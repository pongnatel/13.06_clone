"""Skill loader — reads the content-quality-checker skill files into memory."""

from pathlib import Path
from typing import Optional


class SkillLoader:
    """Loads SKILL.md and reference files at agent startup.

    The agent uses skill content as authoritative rules — injecting relevant
    sections into LLM prompts and using rule IDs to tag issues.
    """

    def __init__(self, skill_path: Path):
        self.skill_path = Path(skill_path)
        if not self.skill_path.exists():
            raise FileNotFoundError(f"Skill path not found: {self.skill_path}")

        skill_md_path = self.skill_path / "SKILL.md"
        if not skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found in {self.skill_path}")

        self.skill_md = skill_md_path.read_text(encoding="utf-8")
        self.refs: dict[str, str] = {}

        refs_dir = self.skill_path / "references"
        if refs_dir.exists():
            for ref_file in refs_dir.glob("*.md"):
                self.refs[ref_file.stem] = ref_file.read_text(encoding="utf-8")

    def get_rules(self, category: str) -> str:
        """Get rules content for a category.

        Category keys match reference filename without extension:
        - spacing-rules, punctuation-rules, typo-rules
        - vietnamese-tone-rules, capitalization-rules
        - brand-style-rules, output-format
        """
        return self.refs.get(category, "")

    def get_output_schema(self) -> str:
        return self.refs.get("output-format", "")

    def list_categories(self) -> list[str]:
        return list(self.refs.keys())
