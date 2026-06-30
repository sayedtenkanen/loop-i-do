"""The /goal primitive — worker agent with judge for stop condition."""

from __future__ import annotations

from .agent import DEFAULT_MODEL, Agent
from .connectors import ConnectorRegistry
from .debug import log, timer


class GoalLoop:
    def __init__(
        self,
        worker_system_prompt: str,
        connectors: ConnectorRegistry | None = None,
        worker_model: str = DEFAULT_MODEL,
        judge_model: str = DEFAULT_MODEL,
    ):
        self.worker = Agent(worker_system_prompt, model=worker_model, connectors=connectors)
        self.judge = Agent(
            "You grade whether a stopping condition has been met. "
            "Reply with exactly DONE or NOT_DONE on the first line, "
            "then one sentence of reasoning.",
            model=judge_model,
            connectors=connectors,
        )

    def run(self, goal: str, stop_condition: str, max_iterations: int = 10) -> str:
        log("GoalLoop.run", goal=goal[:80], stop_condition=stop_condition[:80])

        transcript = ""
        for i in range(max_iterations):
            log(f"Iteration {i + 1}/{max_iterations}")

            turn_prompt = (
                f"Goal: {goal}\n\nProgress so far:\n{transcript}\n\nWhat's the next step? Take it."
            )

            with timer("worker"):
                step_output = self.worker.run(turn_prompt)

            transcript += f"\n--- iteration {i + 1} ---\n{step_output}"
            log("Worker output", length=len(step_output), preview=step_output[:100])

            judge_prompt = f"Stop condition: {stop_condition}\n\nWork so far:\n{transcript}"
            with timer("judge"):
                verdict = self.judge.run(judge_prompt)

            log("Judge verdict", verdict=verdict[:50])

            if verdict.strip().upper().startswith("DONE"):
                log("Goal achieved!")
                return transcript

        log("Max iterations reached")
        return transcript + "\n\n[stopped: max iterations reached without DONE]"
