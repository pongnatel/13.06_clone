"""Base class + utilities for LLM-based checkers."""

import json
import re
from pathlib import Path
from typing import Optional

import httpx


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from prompts/."""
    p = PROMPTS_DIR / f"{name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"Prompt not found: {p}")
    return p.read_text(encoding="utf-8")


def extract_json(content: str) -> dict:
    """Extract JSON from LLM response, tolerating markdown fences and extra text."""
    if not content:
        return {}

    # Strip markdown code fences
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Find the first { ... } balanced block
    start = content.find("{")
    if start == -1:
        return {}

    depth = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(content[start:i+1])
                except json.JSONDecodeError:
                    break
    return {}


def find_position_in_text(text: str, found: str) -> Optional[int]:
    """Find character index of `found` in `text`. Returns None if not found."""
    if not found:
        return None
    idx = text.find(found)
    return idx if idx >= 0 else None


def normalize_issue(raw: dict, original_text: str, default_category: str) -> Optional[dict]:
    """Normalize an LLM-returned issue into the agent's standard format.

    - Validates required fields
    - Computes position_index by searching original_text
    - Filters out low-confidence issues
    """
    if not isinstance(raw, dict):
        return None

    found = raw.get("found", "").strip()
    if not found:
        return None

    confidence = raw.get("confidence", "high").lower()
    if confidence == "low":
        return None  # drop unreliable

    severity = raw.get("severity", "minor").lower()
    if severity not in {"critical", "major", "minor", "suggestion"}:
        severity = "minor"

    pos_idx = find_position_in_text(original_text, found)

    return {
        "rule_id": raw.get("rule_id", "UNKNOWN"),
        "severity": severity,
        "category": raw.get("category", default_category),
        "position": raw.get("position", f"char {pos_idx}" if pos_idx is not None else "?"),
        "position_index": pos_idx if pos_idx is not None else -1,
        "found": found,
        "suggestion": raw.get("suggestion", ""),
        "message": raw.get("message", ""),
        "confidence": confidence,
        "source": "llm",
    }


class LLMClient:
    """Generic OpenAI-compatible chat completion client.

    Both Minimax and Gemma APIs are accessed through this. Pass the
    appropriate endpoint, model name, and API key.
    """

    def __init__(self, endpoint: str, api_key: str, model: str, timeout: float = 60.0):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def chat(self, system: str, user: str,
                   images_b64: Optional[list[str]] = None,
                   force_json: bool = True,
                   temperature: float = 0.1) -> str:
        """Send a chat completion request. Returns the assistant's text content."""
        messages = [{"role": "system", "content": system}]

        if images_b64:
            # Build multimodal user message (OpenAI-style)
            content_blocks = [{"type": "text", "text": user}]
            for img in images_b64:
                # Assume base64 with no data URI prefix; normalize
                if img.startswith("data:"):
                    img_url = img
                else:
                    img_url = f"data:image/jpeg;base64,{img}"
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": img_url}
                })
            messages.append({"role": "user", "content": content_blocks})
        else:
            messages.append({"role": "user", "content": user})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if force_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # OpenAI-compatible response shape
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected LLM response shape: {data}") from e
