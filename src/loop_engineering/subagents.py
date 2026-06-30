"""Sub-agents — keep the maker away from the checker (building block 5)."""

from __future__ import annotations

from dataclasses import dataclass

from .agent import DEFAULT_MODEL, Agent
from .connectors import ConnectorRegistry
from .debug import log, timer


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
        maker_model: str = DEFAULT_MODEL,
        checker_model: str = DEFAULT_MODEL,
    ):
        self.maker = Agent(maker_system_prompt, model=maker_model, connectors=connectors)
        self.checker = Agent(checker_system_prompt, model=checker_model, connectors=connectors)

    def run(self, task: str) -> tuple[str, ReviewResult]:
        log("MakerChecker.run", task=task[:80])

        with timer("maker"):
            draft = self.maker.run(task)
        log("Maker output", length=len(draft), preview=draft[:100])

        review_prompt = (
            f"Task:\n{task}\n\nProposed solution:\n{draft}\n\n"
            "Reply with APPROVE or REJECT on the first line, "
            "then your reasoning."
        )

        with timer("checker"):
            verdict = self.checker.run(review_prompt)

        approved = verdict.strip().upper().startswith("APPROVE")
        log("Checker verdict", approved=approved)

        return draft, ReviewResult(approved=approved, notes=verdict)
