"""Minimax 2.5 checker — deep semantic + multimodal."""

import logging
from typing import Optional

from checkers.llm_base import LLMClient, load_prompt, extract_json, normalize_issue


log = logging.getLogger(__name__)


class MinimaxChecker:
    def __init__(self, endpoint: str, api_key: str, model: str = "minimax-2.5"):
        self.client = LLMClient(endpoint=endpoint, api_key=api_key, model=model)

    async def check_vietnamese_tone(self, text: str) -> list[dict]:
        """VT-02..VT-06 — needs context to disambiguate."""
        try:
            system = load_prompt("vietnamese_tone")
            content = await self.client.chat(system=system, user=text)
            data = extract_json(content)
            out = []
            for raw in data.get("issues", []):
                n = normalize_issue(raw, text, default_category="vietnamese_tone")
                if n:
                    out.append(n)
            return out
        except Exception as e:
            log.warning("Minimax tone check failed: %s", e)
            return []

    async def check_homophone_and_context(self, text: str) -> list[dict]:
        """TY-06 homophones, missing words, wrong acronyms — semantic only."""
        try:
            system = load_prompt("homophone_context")
            content = await self.client.chat(system=system, user=text)
            data = extract_json(content)
            out = []
            for raw in data.get("issues", []):
                n = normalize_issue(raw, text, default_category="typo")
                if n:
                    out.append(n)
            return out
        except Exception as e:
            log.warning("Minimax homophone check failed: %s", e)
            return []

    async def extract_image_text(self, image_b64: str) -> dict:
        """Pure OCR — extract text from image without judgment.

        Returns:
            {
              "extracted_text": str,
              "text_blocks": [{text, region, confidence}],
              "has_text": bool,
            }
        Returns empty dict on failure.
        """
        try:
            system = load_prompt("image_ocr")
            content = await self.client.chat(
                system=system,
                user="Trích xuất tất cả text từ ảnh này.",
                images_b64=[image_b64],
            )
            data = extract_json(content)
            return {
                "extracted_text": data.get("extracted_text", ""),
                "text_blocks": data.get("text_blocks", []),
                "has_text": data.get("has_text", False),
            }
        except Exception as e:
            log.warning("Minimax OCR failed: %s", e)
            return {"extracted_text": "", "text_blocks": [], "has_text": False}

    async def check_image_conflicts(self, caption: str, image_text: str) -> list[dict]:
        """Cross-check caption vs already-extracted image text for conflicts.

        Both inputs are plain text — no image is passed. This keeps the
        check cheap (text-only) and lets us pair it with multiple
        analyses on the same OCR'd content.
        """
        if not image_text.strip():
            return []
        try:
            system = load_prompt("image_conflict")
            user_msg = f"CAPTION:\n{caption}\n\n---\n\nIMAGE_TEXT:\n{image_text}"
            content = await self.client.chat(system=system, user=user_msg)
            data = extract_json(content)
            out = []
            for raw in data.get("conflicts", []):
                n = normalize_issue(raw, caption, default_category="image_text_conflict")
                if n:
                    if "image_text" in raw:
                        n["image_text"] = raw["image_text"]
                    out.append(n)
            return out
        except Exception as e:
            log.warning("Minimax image conflict check failed: %s", e)
            return []
