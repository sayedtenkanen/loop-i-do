"""Tests for Sub-agents (MakerChecker and GoalLoop)."""

from loop_engineering.agent import Agent
from loop_engineering.goal import GoalLoop
from loop_engineering.subagents import MakerChecker


class TestMakerChecker:
    def test_approve_when_checker_says_approve(self):
        class MockAgent(Agent):
            def __init__(self, response: str):
                self.response = response
                self.system_prompt = ""
                self.model = "mock"
                self.dry_run = True

            def run(self, prompt, max_turns=6):
                return self.response

        mc = MakerChecker.__new__(MakerChecker)
        mc.maker = MockAgent("I fixed the code")
        mc.checker = MockAgent("APPROVE\nLooks good")

        draft, review = mc.run("Fix the bug")
        assert draft == "I fixed the code"
        assert review.approved is True

    def test_reject_when_checker_says_reject(self):
        class MockAgent(Agent):
            def __init__(self, response: str):
                self.response = response
                self.system_prompt = ""
                self.model = "mock"
                self.dry_run = True

            def run(self, prompt, max_turns=6):
                return self.response

        mc = MakerChecker.__new__(MakerChecker)
        mc.maker = MockAgent("I fixed the code")
        mc.checker = MockAgent("REJECT\nMissing tests")

        draft, review = mc.run("Fix the bug")
        assert review.approved is False
        assert "Missing tests" in review.notes

    def test_dry_run_independently(self):
        mc = MakerChecker(
            maker_system_prompt="You fix things",
            checker_system_prompt="You review things",
        )
        draft, review = mc.run("Fix something")
        assert "[dry-run:" in draft
        assert review.approved is False  # dry-run verdict doesn't start with APPROVE


class TestGoalLoop:
    def test_stops_when_judge_says_done(self):
        class MockAgent(Agent):
            def __init__(self, response: str):
                self.response = response
                self.system_prompt = ""
                self.model = "mock"
                self.dry_run = True

            def run(self, prompt, max_turns=6):
                return self.response

        goal = GoalLoop.__new__(GoalLoop)
        goal.worker = MockAgent("I did the work")
        goal.judge = MockAgent("DONE\nCondition met")

        result = goal.run(goal="Fix tests", stop_condition="All tests pass")
        assert "I did the work" in result
        assert "[stopped:" not in result

    def test_stops_at_max_iterations(self):
        class MockAgent(Agent):
            def __init__(self, response: str):
                self.response = response
                self.system_prompt = ""
                self.model = "mock"
                self.dry_run = True

            def run(self, prompt, max_turns=6):
                return self.response

        goal = GoalLoop.__new__(GoalLoop)
        goal.worker = MockAgent("Working...")
        goal.judge = MockAgent("NOT_DONE\nStill not done")

        result = goal.run(goal="Fix tests", stop_condition="All pass", max_iterations=3)
        assert "[stopped: max iterations reached without DONE]" in result
        assert result.count("--- iteration") == 3

    def test_dry_run(self):
        goal = GoalLoop(worker_system_prompt="You work")
        result = goal.run(goal="Fix tests", stop_condition="Tests pass")
        assert "[dry-run:" in result
