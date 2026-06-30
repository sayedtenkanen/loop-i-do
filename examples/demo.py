"""Demo wiring for the loop_engineering package."""

from loop_engineering import (
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


def main() -> None:
    memory = Memory("demo_state.json")
    finding_id = memory.add_finding({"title": "flaky test in test/auth/test_login.py"})
    print("open findings:", memory.open_findings())

    skills = SkillRegistry("skills")
    matched = skills.match("flaky test triage")
    print("\nmatched skill:", matched.name if matched else None)

    mc = MakerChecker(
        maker_system_prompt=(
            "You fix flaky tests.\nProject conventions:\n"
            f"{matched.instructions if matched else ''}"
        ),
        checker_system_prompt="You review test fixes for correctness.",
        connectors=registry,
    )
    draft, review = mc.run("Fix the flaky test in test/auth/test_login.py")
    print("\nmaker draft:", draft)
    print("checker verdict approved:", review.approved)
    print("checker notes:", review.notes)

    goal = GoalLoop(worker_system_prompt="You write code to satisfy a goal.", connectors=registry)
    result = goal.run(
        goal="Make all tests in test/auth pass and lint clean",
        stop_condition="all tests in test/auth pass and lint is clean",
        max_iterations=3,
    )
    print("\ngoal loop transcript:", result)

    memory.update_finding(finding_id, status="shipped" if review.approved else "needs_human")
    print("\nfinal memory state:", memory.all_findings())


if __name__ == "__main__":
    main()
