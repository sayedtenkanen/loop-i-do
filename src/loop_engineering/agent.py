"""Agent class for loop engineering."""

from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 1000


class Agent:
    """An agent that executes tasks using an LLM."""

    def __init__(self, name: str, config: AgentConfig | None = None):
        self.name = name
        self.config = config or AgentConfig()

    def execute(self, prompt: str) -> dict:
        """Execute a task with the given prompt.

        Args:
            prompt: The task prompt to execute.

        Returns:
            Dictionary with response and metadata.
        """
        # TODO: Replace with actual LLM call in Phase 3
        return {
            "response": f"Agent {self.name} processed: {prompt}",
            "model": self.config.model,
            "tokens_used": len(prompt.split()) * 2,  # Rough estimate
        }
