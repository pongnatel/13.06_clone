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


@app.get("/")
async def root():
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

    # ---- Phase 2 & 3: LLM checks (parallel) ----
    if use_llm:
        llm_tasks = []

        if state.gemma:
            llm_tasks.append(state.gemma.check_basic_typos(text))

        if state.minimax:
            llm_tasks.append(state.minimax.check_vietnamese_tone(text))
            llm_tasks.append(state.minimax.check_homophone_and_context(text))

            for img_b64 in req.images:
                llm_tasks.append(state.minimax.check_image_vs_text(text, img_b64))

        if llm_tasks:
            results = await asyncio.gather(*llm_tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    log.error("LLM task failed: %s", r)
                    continue
                if isinstance(r, list):
                    all_issues.extend(r)

        log.info("After LLM checks: %d total issues (+%d from LLM)",
                 len(all_issues), len(all_issues) - deterministic_count)

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
        "metadata": {
            "deterministic_checks": deterministic_count,
            "llm_used": use_llm and (state.gemma is not None or state.minimax is not None),
            "images_checked": len(req.images),
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
