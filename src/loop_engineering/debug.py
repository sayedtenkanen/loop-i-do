"""Debug logging for loop_engineering."""

from __future__ import annotations

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

DEBUG = os.environ.get("LOOP_DEBUG", "0") == "1"


def log(msg: str, **kwargs: Any) -> None:
    if not DEBUG:
        return
    parts = [msg]
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    print(f"  [DEBUG] {' '.join(parts)}")


@contextmanager
def timer(label: str) -> Generator[None, None, None]:
    start = time.perf_counter()
    log(f"START {label}")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        log(f"END {label}", elapsed=f"{elapsed:.3f}s")


def log_api_call(
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> None:
    log(
        "API CALL",
        model=model,
        messages=len(messages),
        tools=len(tools) if tools else 0,
    )
    if DEBUG:
        for i, msg in enumerate(messages[-2:]):
            role = msg.get("role", "?")
            content = str(msg.get("content", ""))[:100]
            log(f"  msg[{i}]", role=role, content=content)


def log_api_response(response: Any) -> None:
    if not DEBUG:
        return
    if hasattr(response, "choices") and response.choices:
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = choice.message.tool_calls
        log(
            "API RESPONSE",
            content_len=len(content),
            tool_calls=len(tool_calls) if tool_calls else 0,
        )
        if content:
            log("  content preview", text=content[:150])
    else:
        log("API RESPONSE", error="no choices")


def log_tool_call(name: str, args: dict, result: str) -> None:
    log("TOOL CALL", name=name)
    log("  args", **{k: str(v)[:50] for k, v in args.items()})
    log("  result", text=result[:100])
