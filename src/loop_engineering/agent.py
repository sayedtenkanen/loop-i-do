"""Agent — the engine every other building block drives."""

from __future__ import annotations

import os
from typing import Any

from .connectors import ConnectorRegistry

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

ZEN_BASE_URL = "https://opencode.ai/zen/v1"
DEFAULT_MODEL = "nemotron-3-ultra-free"


class Agent:
    def __init__(
        self,
        system_prompt: str,
        model: str = DEFAULT_MODEL,
        connectors: ConnectorRegistry | None = None,
        max_tokens: int = 2048,
        dry_run: bool | None = None,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.connectors = connectors or ConnectorRegistry()
        self.max_tokens = max_tokens
        api_key = os.environ.get("OPENCODE_ZEN_API_KEY")
        self.dry_run = dry_run if dry_run is not None else not api_key
        if self.dry_run or OpenAI is None or not api_key:
            self._client = None
        else:
            self._client = OpenAI(api_key=api_key, base_url=ZEN_BASE_URL)

    def run(self, user_prompt: str, max_turns: int = 6) -> str:
        if self.dry_run:
            return f"[dry-run:{self.model}] would respond to: {user_prompt[:120]}..."

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        tools = self.connectors.tool_specs()
        openai_tools = (
            [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]
            if tools
            else None
        )

        for _ in range(max_turns):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            response = self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
            choice = response.choices[0]

            if choice.message.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": choice.message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in choice.message.tool_calls
                        ],
                    }
                )

                import json

                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = self.connectors.call(tc.function.name, **args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        }
                    )
            else:
                return choice.message.content or ""

        return "stopped: max turns reached without a final answer"
