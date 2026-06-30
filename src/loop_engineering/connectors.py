"""Connectors / plugins — how the loop touches your real tools."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Connector:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., str]

    def to_tool_spec(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, Connector] = {}

    def register(self, name: str, description: str, input_schema: dict):
        def decorator(fn: Callable[..., str]):
            self._connectors[name] = Connector(name, description, input_schema, fn)
            return fn

        return decorator

    def tool_specs(self) -> list[dict]:
        return [c.to_tool_spec() for c in self._connectors.values()]

    def call(self, connector_name: str, **kwargs) -> str:
        if connector_name not in self._connectors:
            return f"error: unknown connector '{connector_name}'"
        return self._connectors[connector_name].fn(**kwargs)
