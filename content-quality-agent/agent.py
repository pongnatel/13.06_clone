"""Content Quality Checker Agent.

FastAPI orchestrator that:
1. Loads the content-quality-checker skill at startup.
2. Exposes POST /check — runs the full pipeline:
   - Deterministic checks (regex)
   - Gemma 4 quick pass (typos, diacritics)
   - Minimax 2.5 deep pass (homophones, context, image OCR)
3. Returns scored JSON with issues + corrected_text.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from skill_loader import SkillLoader
from checkers.deterministic import (
    check_spacing,
    check_punctuation,
    check_capitalization_basic,
    check_forbidden_words,
)
from checkers.gemma_checker import GemmaChecker
from checkers.minimax_checker import MinimaxChecker
from scorer import (
    compute_score,
    build_corrected_text,
    deduplicate_issues,
    sort_issues_for_display,
)


load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("agent")


# ---- Configuration ----------------------------------------------------------

SKILL_PATH = Path(os.environ.get(
    "SKILL_PATH",
    str(Path(__file__).parent.parent / "content-quality-checker"),
))

MINIMAX_ENDPOINT = os.environ.get(
    "MINIMAX_ENDPOINT",
    "https://api.minimax.chat/v1/chat/completions",
)
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "minimax-2.5")

GEMMA_ENDPOINT = os.environ.get(
    "GEMMA_ENDPOINT",
    "https://api.example-gemma.ai/v1/chat/completions",
)
GEMMA_API_KEY = os.environ.get("GEMMA_API_KEY", "")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma-4")

ENABLE_LLM = os.environ.get("ENABLE_LLM", "true").lower() == "true"


# ---- Singletons (loaded at startup) -----------------------------------------

class AgentState:
    skill: Optional[SkillLoader] = None
    gemma: Optional[GemmaChecker] = None
    minimax: Optional[MinimaxChecker] = None


state = AgentState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Loading skill from %s", SKILL_PATH)
    state.skill = SkillLoader(SKILL_PATH)
    log.info("Skill loaded. Categories: %s", state.skill.list_categories())

    if ENABLE_LLM:
        if GEMMA_API_KEY:
            state.gemma = GemmaChecker(GEMMA_ENDPOINT, GEMMA_API_KEY, GEMMA_MODEL)
            log.info("Gemma checker initialized (model=%s)", GEMMA_MODEL)
        else:
            log.warning("GEMMA_API_KEY not set — Gemma checks disabled")

        if MINIMAX_API_KEY:
            state.minimax = MinimaxChecker(MINIMAX_ENDPOINT, MINIMAX_API_KEY, MINIMAX_MODEL)
            log.info("Minimax checker initialized (model=%s)", MINIMAX_MODEL)
        else:
            log.warning("MINIMAX_API_KEY not set — Minimax checks disabled")
    else:
        log.info("ENABLE_LLM=false — running deterministic checks only")

    yield
    log.info("Shutting down")


# ---- Schema -----------------------------------------------------------------

class ProjectInfo(BaseModel):
    """Project-level context that customizes the check."""
    brand_name: str = ""
    brand_exclusions: list[str] = Field(
        default_factory=list,
        description="Brand names that should NOT be flagged as SP-08 CamelCase errors",
    )
    tone: str = Field("casual", description="formal | casual | playful")
    forbidden_words: list[str] = Field(default_factory=list)
    preferred_terms: dict[str, str] = Field(
        default_factory=dict,
        description="Map of preferred terms: { 'users': 'customers' }",
    )
    is_social_media: bool = True


class CheckRequest(BaseModel):
    text: str = Field(..., description="The post body to check")
    images: list[str] = Field(
        default_factory=list,
        description="Optional list of base64-encoded images (without data URI prefix)",
    )
    project: ProjectInfo = Field(default_factory=ProjectInfo)
    enable_llm: bool = Field(True, description="Set to false for fast deterministic-only check")


class IssueResponse(BaseModel):
    rule_id: str
    severity: str
    category: str
    position: str
    position_index: int
    found: str
    suggestion: str
    message: str
    confidence: Optional[str] = None
    source: Optional[str] = None


# ---- App --------------------------------------------------------------------

app = FastAPI(
    title="Content Quality Checker Agent",
    version="1.0.0",
    description="Proofreads and scores social media posts using a Claude skill + LLMs.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _check_image_full(
    minimax,
    caption_text: str,
    image_b64: str,
    image_index: int,
    project,
    exclusions: set,
) -> tuple[list[dict], list[dict], dict]:
    """Run the full image pipeline for ONE image.

    Steps:
      1. OCR extract text from image (Minimax multimodal)
      2. Run extracted text through deterministic + tone checkers
         → tag each issue with source="image_<idx>" and category="image_text_quality"
      3. Cross-check caption vs extracted text for conflicts
         → category="image_text_conflict"

    Returns (image_quality_issues, image_conflict_issues, ocr_info_dict)
    """
    img_tag = f"image_{image_index}"

    # Step 1: OCR
    ocr_result = await minimax.extract_image_text(image_b64)
    extracted_text = ocr_result.get("extracted_text", "")
    ocr_info = {
        "image_index": image_index,
        "extracted_text": extracted_text,
        "text_blocks": ocr_result.get("text_blocks", []),
        "has_text": ocr_result.get("has_text", False),
    }

    quality_issues: list[dict] = []
    conflict_issues: list[dict] = []

    if not extracted_text.strip():
        return quality_issues, conflict_issues, ocr_info

    # Step 2: Run extracted text through quality pipeline
    # Deterministic checks (re-use same regex rules)
    det_issues = []
    det_issues.extend(check_spacing(extracted_text, exclusions))
    det_issues.extend(check_punctuation(extracted_text))
    det_issues.extend(check_capitalization_basic(
        extracted_text,
        brand_names=[project.brand_name] if project.brand_name else None,
    ))

    # Tone check via LLM
    tone_issues = await minimax.check_vietnamese_tone(extracted_text)

    # Re-tag everything as image_text_quality
    for issue in det_issues + tone_issues:
        issue["category"] = "image_text_quality"
        issue["source"] = img_tag
        # Keep original rule_id (SP-08, VT-02, etc.) so user knows what's wrong
        # Add prefix in message so the UI knows where the issue is
        original_msg = issue.get("message", "")
        issue["message"] = f"[Image {image_index}] {original_msg}"
        # Position context changes: prefix with image tag
        issue["position"] = f"image {image_index} · {issue.get('position', '?')}"
        quality_issues.append(issue)

    # Step 3: Caption vs extracted text — conflict check
    conflict_raw = await minimax.check_image_conflicts(caption_text, extracted_text)
    for issue in conflict_raw:
        issue["source"] = img_tag
        conflict_issues.append(issue)

    return quality_issues, conflict_issues, ocr_info



    return {
        "name": "Content Quality Checker Agent",
        "version": "1.0.0",
        "skill_loaded": state.skill is not None,
        "gemma_enabled": state.gemma is not None,
        "minimax_enabled": state.minimax is not None,
        "endpoints": ["/check", "/health", "/skill/info"],
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "skill_loaded": state.skill is not None,
        "llm_ready": state.minimax is not None or state.gemma is not None,
    }


@app.get("/skill/info")
async def skill_info():
    if not state.skill:
        raise HTTPException(503, "Skill not loaded")
    return {
        "skill_path": str(state.skill.skill_path),
        "categories": state.skill.list_categories(),
    }


@app.post("/check")
async def check_content(req: CheckRequest):
    if not state.skill:
        raise HTTPException(503, "Skill not loaded")

    if not req.text or not req.text.strip():
        return {
            "score": None,
            "grade": None,
            "issues": [{
                "rule_id": "EMPTY_INPUT",
                "severity": "critical",
                "category": "input",
                "message": "No text provided",
                "found": "",
                "suggestion": "",
                "position": "n/a",
                "position_index": -1,
            }],
            "original_text": req.text,
            "corrected_text": req.text,
        }

    text = req.text
    project = req.project
    use_llm = req.enable_llm and ENABLE_LLM

    log.info("Checking text (len=%d, images=%d, llm=%s)",
             len(text), len(req.images), use_llm)

    all_issues: list[dict] = []

    # ---- Phase 1: Deterministic (always) ----
    exclusions = set(project.brand_exclusions)
    if project.brand_name:
        exclusions.add(project.brand_name)

    all_issues.extend(check_spacing(text, exclusions))
    all_issues.extend(check_punctuation(text))
    all_issues.extend(check_capitalization_basic(
        text,
        brand_names=[project.brand_name] if project.brand_name else None,
    ))
    all_issues.extend(check_forbidden_words(text, project.forbidden_words))

    deterministic_count = len(all_issues)
    log.info("Deterministic checks found %d issues", deterministic_count)

    image_quality_issues: list[dict] = []
    image_conflict_issues: list[dict] = []
    extracted_image_texts: list[dict] = []  # always present in response

    # ---- Phase 2 & 3: LLM checks (parallel) ----
    if use_llm:
        llm_tasks = []

        if state.gemma:
            llm_tasks.append(state.gemma.check_basic_typos(text))

        if state.minimax:
            llm_tasks.append(state.minimax.check_vietnamese_tone(text))
            llm_tasks.append(state.minimax.check_homophone_and_context(text))

        if llm_tasks:
            results = await asyncio.gather(*llm_tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    log.error("LLM task failed: %s", r)
                    continue
                if isinstance(r, list):
                    all_issues.extend(r)

        # ---- Phase 3b: Image pipeline (sequential per-image, parallel across images) ----
        if state.minimax and req.images:
            image_results = await asyncio.gather(
                *[_check_image_full(state.minimax, text, img, idx, project, exclusions)
                  for idx, img in enumerate(req.images)],
                return_exceptions=True,
            )
            for r in image_results:
                if isinstance(r, Exception):
                    log.error("Image pipeline failed: %s", r)
                    continue
                quality_issues, conflict_issues, ocr_info = r
                image_quality_issues.extend(quality_issues)
                image_conflict_issues.extend(conflict_issues)
                extracted_image_texts.append(ocr_info)

            all_issues.extend(image_quality_issues)
            all_issues.extend(image_conflict_issues)

        log.info("After LLM checks: %d total issues (+%d from LLM, +%d image quality, +%d image conflicts)",
                 len(all_issues),
                 len(all_issues) - deterministic_count - len(image_quality_issues) - len(image_conflict_issues),
                 len(image_quality_issues),
                 len(image_conflict_issues))

    # ---- Phase 4: Deduplicate + sort + score ----
    all_issues = deduplicate_issues(all_issues)
    all_issues = sort_issues_for_display(all_issues)

    score_result = compute_score(all_issues)
    corrected = build_corrected_text(text, all_issues)

    # ---- Build response ----
    response = {
        "score": score_result["score"],
        "grade": score_result["grade"],
        "total_issues": score_result["total_issues"],
        "issues_by_severity": score_result["issues_by_severity"],
        "categories": score_result["categories"],
        "issues": all_issues,
        "original_text": text,
        "corrected_text": corrected,
        "image_analysis": extracted_image_texts,
        "metadata": {
            "deterministic_checks": deterministic_count,
            "llm_used": use_llm and (state.gemma is not None or state.minimax is not None),
            "images_checked": len(req.images),
            "image_quality_issues": len(image_quality_issues),
            "image_conflict_issues": len(image_conflict_issues),
        },
    }
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
    )
