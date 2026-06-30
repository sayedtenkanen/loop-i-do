"""Skills — written-down project knowledge (building block 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    path: Path


class SkillRegistry:
    def __init__(self, skills_dir: str | Path = "skills"):
        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, Skill] = {}
        self.reload()

    def reload(self) -> None:
        self._skills.clear()
        if not self.skills_dir.exists():
            return
        for folder in sorted(self.skills_dir.iterdir()):
            skill_md = folder / "SKILL.md"
            if folder.is_dir() and skill_md.exists():
                description, instructions = self._parse(skill_md.read_text())
                self._skills[folder.name] = Skill(
                    name=folder.name,
                    description=description,
                    instructions=instructions,
                    path=folder,
                )

    @staticmethod
    def _parse(text: str) -> tuple[str, str]:
        if text.startswith("---"):
            end = text.find("---", 3)
            front_matter, body = text[3:end], text[end + 3 :]
            description = ""
            for line in front_matter.splitlines():
                if line.strip().startswith("description:"):
                    description = line.split(":", 1)[1].strip()
            return description, body.strip()
        paragraphs = text.strip().split("\n\n", 1)
        return paragraphs[0], (paragraphs[1] if len(paragraphs) > 1 else "")

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def match(self, task_description: str) -> Skill | None:
        task_words = set(task_description.lower().split())
        best, best_score = None, 0
        for skill in self._skills.values():
            score = len(task_words & set(skill.description.lower().split()))
            if score > best_score:
                best, best_score = skill, score
        return best

    def __iter__(self):
        return iter(self._skills.values())
