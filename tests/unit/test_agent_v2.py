"""Tests for Agent class with dry-run and tool-use support."""

from loop_engineering.agent import DEFAULT_MODEL, Agent
from loop_engineering.connectors import ConnectorRegistry


class TestAgentDryRun:
    def test_dry_run_by_default(self):
        agent = Agent(system_prompt="You are a test agent.")
        assert agent.dry_run is True

    def test_dry_run_response(self):
        agent = Agent(system_prompt="You are a test agent.")
        result = agent.run("Do something")
        assert "[dry-run:" in result
        assert DEFAULT_MODEL in result

    def test_explicit_dry_run(self):
        agent = Agent(system_prompt="Test", dry_run=True)
        assert agent.dry_run is True

    def test_explicit_not_dry_run(self):
        agent = Agent(system_prompt="Test", dry_run=False)
        assert agent.dry_run is False

    def test_custom_model(self):
        agent = Agent(system_prompt="Test", model="gpt-5-nano")
        assert agent.model == "gpt-5-nano"


class TestAgentWithConnectors:
    def test_dry_run_with_connectors(self):
        registry = ConnectorRegistry()

        @registry.register("test_tool", "A test", {"type": "object"})
        def test_tool() -> str:
            return "used"

        agent = Agent(
            system_prompt="Test",
            connectors=registry,
            dry_run=True,
        )
        result = agent.run("Use the tool")
        assert "[dry-run:" in result
