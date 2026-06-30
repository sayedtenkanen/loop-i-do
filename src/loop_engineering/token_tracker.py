"""TokenTracker for monitoring AI usage costs."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenUsage:
    """Record of token usage for a single agent call."""

    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost(self) -> float:
        """Calculate cost based on model pricing."""
        # Pricing per 1K tokens (simplified)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
        }
        rates = pricing.get(self.model, {"input": 0.01, "output": 0.03})
        input_cost = (self.input_tokens / 1000) * rates["input"]
        output_cost = (self.output_tokens / 1000) * rates["output"]
        return input_cost + output_cost


class TokenTracker:
    """Tracks token usage and enforces budgets."""

    def __init__(self, budget: int = 100000):
        self.budget = budget
        self.usages: list[TokenUsage] = []

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self.usages)

    @property
    def total_cost(self) -> float:
        return sum(u.cost for u in self.usages)

    def record_usage(
        self, agent_id: str, model: str, input_tokens: int, output_tokens: int
    ) -> TokenUsage:
        """Record token usage for an agent call."""
        usage = TokenUsage(
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self.usages.append(usage)
        return usage

    def check_budget(self, estimated_tokens: int) -> dict:
        """Check if we're within budget."""
        warnings = []
        can_proceed = True

        if self.total_tokens + estimated_tokens > self.budget:
            can_proceed = False
            warnings.append(
                f"Budget exceeded: {self.total_tokens + estimated_tokens}/{self.budget}"
            )

        return {
            "can_proceed": can_proceed,
            "current_tokens": self.total_tokens,
            "estimated_tokens": estimated_tokens,
            "budget": self.budget,
            "warnings": warnings,
        }

    def get_summary(self) -> dict:
        """Get summary of token usage."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "usage_count": len(self.usages),
            "budget": self.budget,
            "budget_remaining": self.budget - self.total_tokens,
        }
