"""Agent — the engine every other building block drives."""

from __future__ import annotations

import os
from typing import Any

from .connectors import ConnectorRegistry

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]


class Agent:
    def __init__(
        self,
        system_prompt: str,
        model: str = "claude-sonnet-5",
        connectors: ConnectorRegistry | None = None,
        max_tokens: int = 2048,
        dry_run: bool | None = None,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.connectors = connectors or ConnectorRegistry()
        self.max_tokens = max_tokens
        self.dry_run = dry_run if dry_run is not None else not os.environ.get("ANTHROPIC_API_KEY")
        self._client = None if (self.dry_run or anthropic is None) else anthropic.Anthropic()  # type: ignore[assignment]

    def run(self, user_prompt: str, max_turns: int = 6) -> str:
        if self.dry_run:
            return f"[dry-run:{self.model}] would respond to: {user_prompt[:120]}..."

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
        for _ in range(max_turns):
            response = self._client.messages.create(  # type: ignore[union-attr]
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=self.connectors.tool_specs(),  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if hasattr(b, "text"))

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = self.connectors.call(block.name, **block.input)  # type: ignore[union-attr]
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,  # type: ignore[union-attr]
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})  # type: ignore[dict-item]

        return "stopped: max turns reached without a final answer"
