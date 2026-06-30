"""Tests for TokenTracker - RED phase (failing tests)."""

from loop_engineering.token_tracker import TokenTracker, TokenUsage


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        usage = TokenUsage(
            agent_id="agent-1",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )
        assert usage.agent_id == "agent-1"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_token_usage_cost(self):
        usage = TokenUsage(
            agent_id="agent-1",
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        assert usage.cost > 0


class TestTokenTracker:
    """Tests for TokenTracker class."""

    def test_tracker_creation(self):
        tracker = TokenTracker()
        assert tracker is not None

    def test_tracker_records_usage(self):
        tracker = TokenTracker()
        usage = tracker.record_usage(
            agent_id="agent-1",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )
        assert isinstance(usage, TokenUsage)
        assert tracker.total_tokens == 150

    def test_tracker_budget_check_under(self):
        tracker = TokenTracker(budget=10000)
        result = tracker.check_budget(estimated_tokens=1000)
        assert result["can_proceed"] is True

    def test_tracker_budget_check_over(self):
        tracker = TokenTracker(budget=100)
        result = tracker.check_budget(estimated_tokens=200)
        assert result["can_proceed"] is False
        assert len(result["warnings"]) > 0

    def test_tracker_get_summary(self):
        tracker = TokenTracker()
        tracker.record_usage("a1", "gpt-4o", 100, 50)
        tracker.record_usage("a2", "gpt-4o-mini", 200, 100)
        summary = tracker.get_summary()
        assert summary["total_tokens"] == 450
        assert summary["total_cost"] > 0
        assert summary["usage_count"] == 2
