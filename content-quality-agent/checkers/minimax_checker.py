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

    async def check_image_vs_text(self, text: str, image_b64: str) -> list[dict]:
        """Multimodal: OCR + cross-check image against caption."""
        try:
            system = load_prompt("image_check")
            user_msg = f"Caption text:\n{text}\n\nĐọc text trong ảnh và so sánh."
            content = await self.client.chat(
                system=system,
                user=user_msg,
                images_b64=[image_b64],
            )
            data = extract_json(content)
            out = []
            for raw in data.get("conflicts", []):
                n = normalize_issue(raw, text, default_category="image_text_conflict")
                if n:
                    # Attach image_text if present
                    if "image_text" in raw:
                        n["image_text"] = raw["image_text"]
                    out.append(n)
            return out
        except Exception as e:
            log.warning("Minimax image check failed: %s", e)
            return []
