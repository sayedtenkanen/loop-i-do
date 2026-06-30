"""Loop — wires the six building blocks together."""

from __future__ import annotations

from pathlib import Path

from .connectors import ConnectorRegistry
from .memory import Memory
from .skills import SkillRegistry
from .subagents import MakerChecker
from .worktrees import WorktreeManager


class Loop:
    def __init__(
        self,
        repo_path: str,
        memory_path: str = "loop_state.json",
        skills_dir: str = "skills",
        connectors: ConnectorRegistry | None = None,
    ):
        self.repo_path = Path(repo_path)
        self.memory = Memory(memory_path)
        self.skills = SkillRegistry(skills_dir)
        self.worktrees = WorktreeManager(repo_path)
        self.connectors = connectors or ConnectorRegistry()

    def handle_finding(self, finding: dict) -> None:
        skill = self.skills.match(finding.get("title", ""))
        guidance = skill.instructions if skill else ""

        worktree_path = self.worktrees.create(branch_prefix="loop")
        try:
            maker_checker = MakerChecker(
                maker_system_prompt=(
                    f"You are working inside {worktree_path}. Project conventions:\n{guidance}"
                ),
                checker_system_prompt=(
                    "You are a strict reviewer. Check the proposed change "
                    f"against these project conventions:\n{guidance}"
                ),
                connectors=self.connectors,
            )
            task = f"Fix: {finding['title']}"
            draft, review = maker_checker.run(task)

            if review.approved:
                self.connectors.call(
                    "open_pull_request",
                    branch=worktree_path.name,
                    title=finding["title"],
                    body=draft,
                )
                self.memory.update_finding(finding["id"], status="shipped", notes=review.notes)
            else:
                self.memory.update_finding(finding["id"], status="needs_human", notes=review.notes)
        finally:
            self.worktrees.remove(worktree_path)

    def tick(self) -> None:
        for finding in self.memory.open_findings():
            self.handle_finding(finding)
