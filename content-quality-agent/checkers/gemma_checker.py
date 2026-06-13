"""Gemma 4 checker — fast/cheap pass for diacritics & basic typos."""

import logging
from typing import Optional

from checkers.llm_base import LLMClient, load_prompt, extract_json, normalize_issue


log = logging.getLogger(__name__)


class GemmaChecker:
    def __init__(self, endpoint: str, api_key: str, model: str = "gemma-4"):
        self.client = LLMClient(endpoint=endpoint, api_key=api_key, model=model)

    async def check_basic_typos(self, text: str) -> list[dict]:
        """Quick pass for English typos, brand name spelling, missing diacritics."""
        try:
            system = load_prompt("basic_typo")
            content = await self.client.chat(system=system, user=text)
            data = extract_json(content)
            raw_issues = data.get("issues", [])
            normalized = []
            for raw in raw_issues:
                n = normalize_issue(raw, text, default_category="typo")
                if n:
                    normalized.append(n)
            return normalized
        except Exception as e:
            log.warning("Gemma basic_typo check failed: %s", e)
            return []
