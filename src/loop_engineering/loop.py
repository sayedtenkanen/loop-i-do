"""Loop class for orchestrating agent tasks."""

from dataclasses import dataclass

from loop_engineering.agent import Agent
from loop_engineering.verifier import Verifier


@dataclass
class LoopResult:
    """Result of a loop execution."""

    success: bool
    output: dict | None
    attempts: int
    tokens_used: int
    error: str | None = None


class Loop:
    """Orchestrates an agent to complete a task with verification."""

    def __init__(
        self,
        name: str,
        task: str,
        agent: Agent,
        verifier: Verifier,
        max_retries: int = 3,
        criteria: dict | None = None,
    ):
        self.name = name
        self.task = task
        self.agent = agent
        self.verifier = verifier
        self.max_retries = max_retries
        self.criteria = criteria or {"tests_pass": True}

    def execute(self) -> LoopResult:
        """Execute the loop with retries.

        Returns:
            LoopResult with success status and output.
        """
        total_tokens = 0
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            # Execute the task
            agent_result = self.agent.execute(self.task)
            total_tokens += agent_result.get("tokens_used", 0)

            # Verify the result
            verification = self.verifier.verify(
                agent_result.get("response", ""),
                criteria=self.criteria,
            )

            if verification.passed:
                return LoopResult(
                    success=True,
                    output=agent_result,
                    attempts=attempt,
                    tokens_used=total_tokens,
                )

            last_error = f"Verification failed: {', '.join(verification.issues)}"

        return LoopResult(
            success=False,
            output=None,
            attempts=self.max_retries,
            tokens_used=total_tokens,
            error=last_error,
        )
