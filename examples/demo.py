"""Demo wiring for the loop_engineering package."""

import os
import sys

from loop_engineering import (
    Agent,
    ConnectorRegistry,
    GoalLoop,
    MakerChecker,
    Memory,
    SkillRegistry,
)

registry = ConnectorRegistry()


@registry.register(
    "open_pull_request",
    "Open a pull request for a given branch",
    {
        "type": "object",
        "properties": {
            "branch": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["branch", "title", "body"],
    },
)
def open_pull_request(branch: str, title: str, body: str) -> str:
    return f"opened PR for {branch}: {title}"


def demo_memory():
    print("=" * 60)
    print("DEMO 1: Memory - Finding Management")
    print("=" * 60)

    memory = Memory("demo_state.json")

    finding_id = memory.add_finding({"title": "flaky test in test/auth/test_login.py"})
    print(f"Created finding: {finding_id}")

    finding_id2 = memory.add_finding({"title": "lint error in src/utils.py"})
    print(f"Created finding: {finding_id2}")

    print(f"\nOpen findings: {len(memory.open_findings())}")
    memory.update_finding(finding_id, status="shipped")
    print(f"After shipping one: {len(memory.open_findings())} open")


def demo_skills():
    print("\n" + "=" * 60)
    print("DEMO 2: Skills - Project Knowledge")
    print("=" * 60)

    skills = SkillRegistry("skills")

    print("\nAvailable skills:")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description[:60]}...")

    print("\nMatching examples:")
    test_queries = [
        "flaky test triage",
        "write code and test it iteratively",
        "user feedback on my app",
        "GLM-5.2 performance",
    ]
    for query in test_queries:
        matched = skills.match(query)
        print(f"  '{query}' -> {matched.name if matched else 'None'}")


def demo_auto_skill_loading():
    print("\n" + "=" * 60)
    print("DEMO 3: Auto Skill Loading - Agent + Skills")
    print("=" * 60)

    skills = SkillRegistry("skills")

    agent = Agent(
        system_prompt="You are a helpful coding assistant. Be concise.",
        skills=skills,
    )

    tasks = [
        "Write a function and test it iteratively until it passes",
        "Check if the login button is blue",
        "What is 2 + 2?",
    ]

    for task in tasks:
        print(f"\nTask: {task}")
        response = agent.run(task)
        print(f"Response: {response[:100]}...")


def demo_single_agent():
    print("\n" + "=" * 60)
    print("DEMO 4: Single Agent - Direct Execution")
    print("=" * 60)

    agent = Agent(
        system_prompt="You are a helpful coding assistant. Be concise.",
    )

    response = agent.run("What is 2 + 2? Reply with just the number.")
    print(f"Agent response: {response}")


def demo_maker_checker():
    print("\n" + "=" * 60)
    print("DEMO 5: MakerChecker - Dual Agent Review")
    print("=" * 60)

    mc = MakerChecker(
        maker_system_prompt="You write Python code. Be concise.",
        checker_system_prompt="You review code. Reply APPROVE if code looks good, REJECT if not.",
    )

    task = "Write a function that returns the square of a number"
    print(f"Task: {task}")
    draft, review = mc.run(task)
    print(f"\nMaker output: {draft[:150]}...")
    print(f"Checker approved: {review.approved}")


def demo_goal_loop():
    print("\n" + "=" * 60)
    print("DEMO 6: GoalLoop - Iterative Problem Solving")
    print("=" * 60)

    goal = GoalLoop(
        worker_system_prompt="You solve coding problems step by step.",
    )

    result = goal.run(
        goal="Write a Python function to check if a number is prime",
        stop_condition="function is complete and handles edge cases",
        max_iterations=3,
    )
    print(f"Goal result: {result[:300]}...")


def main():
    debug = "--debug" in sys.argv
    if debug:
        os.environ["LOOP_DEBUG"] = "1"
        print("DEBUG MODE ENABLED\n")

    api_key = os.environ.get("OPENCODE_ZEN_API_KEY")
    print(f"API key: {'Set' if api_key else 'Not set (dry-run mode)'}\n")

    demo_memory()
    demo_skills()
    demo_auto_skill_loading()
    demo_single_agent()
    demo_maker_checker()
    demo_goal_loop()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
