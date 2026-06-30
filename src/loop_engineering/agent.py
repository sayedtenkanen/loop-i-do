"""Agent — the engine every other building block drives."""

from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, Any

from .connectors import ConnectorRegistry
from .debug import log, log_api_call, log_api_response, log_tool_call, timer

if TYPE_CHECKING:
    from .skills import SkillRegistry

try:
    from openai import APIStatusError, APITimeoutError, OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]
    APITimeoutError = Exception  # type: ignore[misc,assignment]
    APIStatusError = Exception  # type: ignore[misc,assignment]

ZEN_BASE_URL = "https://opencode.ai/zen/v1"
DEFAULT_MODEL = "nemotron-3-ultra-free"


class Agent:
    def __init__(
        self,
        system_prompt: str,
        model: str = DEFAULT_MODEL,
        connectors: ConnectorRegistry | None = None,
        skills: SkillRegistry | None = None,
        max_tokens: int = 2048,
        dry_run: bool | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.connectors = connectors or ConnectorRegistry()
        self.skills = skills
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        api_key = os.environ.get("OPENCODE_ZEN_API_KEY")
        self.dry_run = dry_run if dry_run is not None else not api_key
        if self.dry_run or OpenAI is None or not api_key:
            self._client = None
        else:
            self._client = OpenAI(
                api_key=api_key,
                base_url=ZEN_BASE_URL,
                timeout=self.timeout,
                max_retries=0,
            )
        log("Agent init", model=model, dry_run=self.dry_run, skills=bool(skills))

    def _build_system_prompt(self, user_prompt: str) -> str:
        parts = [self.system_prompt]

        if self.skills:
            skill = self.skills.match(user_prompt)
            if skill:
                log("Auto-loaded skill", name=skill.name)
                parts.append(f"\n\n## Relevant Skill: {skill.name}\n\n{skill.instructions}")

        return "".join(parts)

    def run(self, user_prompt: str, max_turns: int = 6) -> str:
        if self.dry_run:
            result = f"[dry-run:{self.model}] would respond to: {user_prompt[:120]}..."
            log("Agent dry-run", result=result[:100])
            return result

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt(user_prompt)},
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

        for attempt in range(self.max_retries):
            try:
                return self._run_loop(messages, openai_tools, max_turns)
            except APITimeoutError:
                log("Agent timeout", attempt=attempt + 1)
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
            except APIStatusError as e:
                if e.status_code >= 500 and attempt < self.max_retries - 1:
                    log("Agent server error", status=e.status_code, attempt=attempt + 1)
                    time.sleep(2**attempt)
                    continue
                raise

        return f"Error: API timeout after {self.max_retries} retries"

    def _run_loop(
        self,
        messages: list[dict[str, Any]],
        openai_tools: list[dict] | None,
        max_turns: int,
    ) -> str:
        for turn in range(max_turns):
            log(f"Turn {turn + 1}/{max_turns}", messages=len(messages))

            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            log_api_call(self.model, messages, openai_tools)

            with timer("API call"):
                response = self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]

            log_api_response(response)

            if not response.choices:
                log("No choices in response")
                return "Error: No response from model"

            choice = response.choices[0]

            if choice.message.tool_calls:
                log("Tool calls detected", count=len(choice.message.tool_calls))

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

                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = self.connectors.call(tc.function.name, **args)
                    log_tool_call(tc.function.name, args, result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        }
                    )
            else:
                content = choice.message.content or ""
                log("Final response", length=len(content))
                return content

        return "stopped: max turns reached without a final answer"
