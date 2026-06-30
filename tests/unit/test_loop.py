"""Tests for Loop class - RED phase (failing tests)."""

from loop_engineering.agent import Agent, AgentConfig
from loop_engineering.loop import Loop, LoopResult
from loop_engineering.verifier import Verifier


class TestLoopResult:
    """Tests for LoopResult dataclass."""

    def test_successful_result(self):
        result = LoopResult(
            success=True,
            output={"fixed": True},
            attempts=1,
            tokens_used=500,
        )
        assert result.success is True
        assert result.attempts == 1
        assert result.tokens_used == 500

    def test_failed_result(self):
        result = LoopResult(
            success=False,
            output=None,
            attempts=3,
            tokens_used=1500,
            error="Verification failed",
        )
        assert result.success is False
        assert result.error == "Verification failed"


class TestLoop:
    """Tests for Loop class."""

    def test_loop_creation(self):
        loop = Loop(
            name="test-loop",
            task="Fix bugs in auth.py",
            agent=Agent(name="agent", config=AgentConfig()),
            verifier=Verifier(),
        )
        assert loop.name == "test-loop"
        assert loop.task == "Fix bugs in auth.py"

    def test_loop_execute_returns_result(self):
        loop = Loop(
            name="test-loop",
            task="Fix the bug",
            agent=Agent(name="agent", config=AgentConfig()),
            verifier=Verifier(),
        )
        result = loop.execute()
        assert isinstance(result, LoopResult)

    def test_loop_execute_success(self):
        loop = Loop(
            name="test-loop",
            task="What is 2 + 2?",
            agent=Agent(name="agent", config=AgentConfig()),
            verifier=Verifier(),
        )
        result = loop.execute()
        assert result.success is True
        assert result.attempts == 1

    def test_loop_tracks_tokens(self):
        loop = Loop(
            name="test-loop",
            task="Simple task",
            agent=Agent(name="agent", config=AgentConfig()),
            verifier=Verifier(),
        )
        result = loop.execute()
        assert result.tokens_used > 0

    def test_loop_retries_on_failure(self):
        loop = Loop(
            name="test-loop",
            task="Always fail task",
            agent=Agent(name="agent", config=AgentConfig()),
            verifier=Verifier(),
            max_retries=3,
        )
        result = loop.execute()
        assert result.attempts <= 3
