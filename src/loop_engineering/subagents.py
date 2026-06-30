"""Sub-agents — keep the maker away from the checker (building block 5)."""

from __future__ import annotations

from dataclasses import dataclass

from .agent import Agent
from .connectors import ConnectorRegistry


@dataclass
class ReviewResult:
    approved: bool
    notes: str


class MakerChecker:
    def __init__(
        self,
        maker_system_prompt: str,
        checker_system_prompt: str,
        connectors: ConnectorRegistry | None = None,
        maker_model: str = "claude-sonnet-5",
        checker_model: str = "claude-opus-4-8",
    ):
        self.maker = Agent(maker_system_prompt, model=maker_model, connectors=connectors)
        self.checker = Agent(checker_system_prompt, model=checker_model, connectors=connectors)

    def run(self, task: str) -> tuple[str, ReviewResult]:
        draft = self.maker.run(task)
        review_prompt = (
            f"Task:\n{task}\n\nProposed solution:\n{draft}\n\n"
            "Reply with APPROVE or REJECT on the first line, "
            "then your reasoning."
        )
        verdict = self.checker.run(review_prompt)
        approved = verdict.strip().upper().startswith("APPROVE")
        return draft, ReviewResult(approved=approved, notes=verdict)
