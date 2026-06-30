"""Automations — the heartbeat of a loop (building block 1)."""

from __future__ import annotations

import time
from collections.abc import Callable

from .memory import Memory
from .skills import SkillRegistry


class Automation:
    def __init__(
        self,
        name: str,
        triage_fn: Callable[[], list[dict]],
        memory: Memory,
        interval_seconds: int = 3600,
    ):
        self.name = name
        self.triage_fn = triage_fn
        self.memory = memory
        self.interval_seconds = interval_seconds

    def run_once(self) -> list[str]:
        findings = self.triage_fn()
        ids = [self.memory.add_finding(f) for f in findings]
        self.memory.log(f"automation '{self.name}' ran, {len(ids)} finding(s)")
        return ids

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.interval_seconds)


def make_skill_triage(
    skills: SkillRegistry,
    skill_name: str,
    agent_run_fn: Callable[[str], str],
) -> Callable[[], list[dict]]:
    def triage_fn() -> list[dict]:
        skill = skills.get(skill_name)
        if skill is None:
            return []
        output = agent_run_fn(skill.instructions)
        return [
            {"title": line.strip("- ").strip(), "source": skill_name}
            for line in output.splitlines()
            if line.strip().startswith("-")
        ]

    return triage_fn
