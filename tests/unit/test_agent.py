"""Tests for Agent class - RED phase (failing tests)."""

from loop_engineering.agent import Agent, AgentConfig


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_config(self):
        config = AgentConfig()
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000

    def test_custom_config(self):
        config = AgentConfig(model="gpt-4o", temperature=0.1, max_tokens=2000)
        assert config.model == "gpt-4o"
        assert config.temperature == 0.1
        assert config.max_tokens == 2000


class TestAgent:
    """Tests for Agent class."""

    def test_agent_creation(self):
        agent = Agent(name="test-agent", config=AgentConfig())
        assert agent.name == "test-agent"
        assert agent.config.model == "gpt-4o-mini"

    def test_agent_execute_returns_dict(self):
        agent = Agent(name="test-agent", config=AgentConfig())
        result = agent.execute("Fix the bug in auth.py")
        assert isinstance(result, dict)
        assert "response" in result

    def test_agent_execute_with_prompt(self):
        agent = Agent(name="test-agent", config=AgentConfig())
        result = agent.execute("What is 2 + 2?")
        assert isinstance(result, dict)
        assert "response" in result
        assert len(result["response"]) > 0
