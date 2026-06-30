"""Integration tests for end-to-end loop flow."""

from loop_engineering.agent import Agent, AgentConfig
from loop_engineering.loop import Loop
from loop_engineering.memory import LoopState, MemoryLayer
from loop_engineering.token_tracker import TokenTracker
from loop_engineering.verifier import Verifier


class TestEndToEndFlow:
    """Integration tests for complete loop execution."""

    def test_simple_task_execution(self):
        """Test a simple task goes through the full loop."""
        agent = Agent(name="test-agent", config=AgentConfig())
        verifier = Verifier()

        loop = Loop(
            name="simple-test",
            task="What is 2 + 2?",
            agent=agent,
            verifier=verifier,
        )

        result = loop.execute()

        assert result.success is True
        assert result.attempts == 1
        assert result.tokens_used > 0

    def test_task_with_memory_persistence(self, tmp_path):
        """Test loop state persists to memory."""
        db_path = tmp_path / "test_integration.db"
        memory = MemoryLayer(db_path=str(db_path))

        # Save initial state
        state = LoopState(loop_id="integ-1", status="running", task="Test task")
        memory.save(state)

        # Run loop
        agent = Agent(name="test-agent", config=AgentConfig())
        verifier = Verifier()
        loop = Loop(
            name="integ-loop",
            task="Simple task",
            agent=agent,
            verifier=verifier,
        )
        loop.execute()

        # Update memory with result
        loaded = memory.load("integ-1")
        assert loaded is not None
        assert loaded.status == "running"

        memory.update_status("integ-1", "completed")
        loaded = memory.load("integ-1")
        assert loaded.status == "completed"

    def test_token_tracking_through_loop(self):
        """Test tokens are tracked across loop execution."""
        tracker = TokenTracker(budget=10000)
        agent = Agent(name="tracked-agent", config=AgentConfig())
        verifier = Verifier()

        loop = Loop(
            name="tracked-loop",
            task="Count the tokens",
            agent=agent,
            verifier=verifier,
        )

        loop.execute()

        # Record usage
        tracker.record_usage(
            agent_id="tracked-agent",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
        )

        summary = tracker.get_summary()
        assert summary["total_tokens"] == 150
        assert summary["usage_count"] == 1

    def test_multiple_loops_with_memory(self, tmp_path):
        """Test multiple loops can be tracked."""
        db_path = tmp_path / "multi_loop.db"
        memory = MemoryLayer(db_path=str(db_path))

        # Create and run multiple loops
        for i in range(3):
            state = LoopState(loop_id=f"loop-{i}", status="idle", task=f"Task {i}")
            memory.save(state)

            agent = Agent(name=f"agent-{i}", config=AgentConfig())
            verifier = Verifier()
            loop = Loop(
                name=f"loop-{i}",
                task=f"Task {i}",
                agent=agent,
                verifier=verifier,
            )
            result = loop.execute()

            if result.success:
                memory.update_status(f"loop-{i}", "completed")

        # Verify all loops are tracked
        loops = memory.list_loops()
        assert len(loops) == 3

        completed = [loop for loop in loops if loop.status == "completed"]
        assert len(completed) == 3

    def test_budget_enforcement(self):
        """Test budget limits are enforced."""
        tracker = TokenTracker(budget=100)

        # Record usage that exceeds budget
        tracker.record_usage("agent-1", "gpt-4o", 50, 30)
        tracker.record_usage("agent-2", "gpt-4o", 50, 30)

        result = tracker.check_budget(estimated_tokens=50)
        assert result["can_proceed"] is False
        assert len(result["warnings"]) > 0

    def test_loop_retry_on_verification_failure(self):
        """Test loop retries when verification fails."""
        agent = Agent(name="retry-agent", config=AgentConfig())
        verifier = Verifier()

        loop = Loop(
            name="retry-loop",
            task="This will need retries",
            agent=agent,
            verifier=verifier,
            max_retries=3,
        )

        result = loop.execute()
        assert result.attempts <= 3
