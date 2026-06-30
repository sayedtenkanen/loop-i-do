#!/usr/bin/env python3
"""Run loop-engineering on this repo to demonstrate the tool."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loop_engineering import (
    Agent,
    AgentConfig,
    Loop,
    LoopState,
    MemoryLayer,
    TokenTracker,
    Verifier,
)


def main():
    """Run loop-engineering demo on this repo."""
    print("=" * 70)
    print("LOOP ENGINEERING - Repository Analysis Demo")
    print("=" * 70)

    # Configure components
    config = AgentConfig(model="gpt-4o-mini", temperature=0.3)
    agent = Agent(name="repo-analyzer", config=config)
    verifier = Verifier()
    tracker = TokenTracker(budget=50000)
    memory = MemoryLayer(db_path="repo_analysis.db")

    # Gather repo info
    repo_root = Path(__file__).parent.parent
    src_files = list(repo_root.glob("src/**/*.py"))
    test_files = list(repo_root.glob("tests/**/*.py"))

    print(f"\nRepository: {repo_root.name}")
    print(f"Source files: {len(src_files)}")
    print(f"Test files: {len(test_files)}")

    # Task 1: Code Quality Review
    print("\n" + "-" * 70)
    print("TASK 1: Code Quality Review")
    print("-" * 70)

    code_content = ""
    for f in src_files[:3]:
        code_content += f"\n--- {f.name} ---\n"
        code_content += f.read_text()[:500] + "\n..."

    task1 = f"""Analyze the following Python code for quality issues:

{code_content}

Provide a brief summary of:
1. Code style issues
2. Potential bugs
3. Suggested improvements
"""

    state1 = LoopState(loop_id="repo-1", status="idle", task="Code quality review")
    memory.save(state1)

    loop1 = Loop(
        name="quality-review",
        task=task1,
        agent=agent,
        verifier=verifier,
        max_retries=2,
    )

    result1 = loop1.execute()
    tracker.record_usage("repo-analyzer", "gpt-4o-mini", 800, 400)
    memory.update_status("repo-1", "completed" if result1.success else "failed")

    print(f"Status: {'SUCCESS' if result1.success else 'FAILED'}")
    print(f"Attempts: {result1.attempts}")
    print(f"Tokens: {result1.tokens_used}")

    # Task 2: Test Coverage Analysis
    print("\n" + "-" * 70)
    print("TASK 2: Test Coverage Analysis")
    print("-" * 70)

    test_content = ""
    for f in test_files[:2]:
        test_content += f"\n--- {f.name} ---\n"
        test_content += f.read_text()[:300] + "\n..."

    task2 = f"""Analyze test coverage for this project:

Source files: {[f.name for f in src_files]}
Test files: {[f.name for f in test_files]}

Sample test code:
{test_content}

Identify any gaps in test coverage.
"""

    state2 = LoopState(loop_id="repo-2", status="idle", task="Test coverage analysis")
    memory.save(state2)

    loop2 = Loop(
        name="coverage-analysis",
        task=task2,
        agent=agent,
        verifier=verifier,
        max_retries=2,
    )

    result2 = loop2.execute()
    tracker.record_usage("repo-analyzer", "gpt-4o-mini", 600, 300)
    memory.update_status("repo-2", "completed" if result2.success else "failed")

    print(f"Status: {'SUCCESS' if result2.success else 'FAILED'}")
    print(f"Attempts: {result2.attempts}")
    print(f"Tokens: {result2.tokens_used}")

    # Task 3: Documentation Review
    print("\n" + "-" * 70)
    print("TASK 3: Documentation Review")
    print("-" * 70)

    readme = (repo_root / "README.md").read_text()[:500]

    task3 = f"""Review this README for completeness and clarity:

{readme}

Suggest improvements for:
1. Getting started section
2. API documentation
3. Examples
"""

    state3 = LoopState(loop_id="repo-3", status="idle", task="Documentation review")
    memory.save(state3)

    loop3 = Loop(
        name="doc-review",
        task=task3,
        agent=agent,
        verifier=verifier,
        max_retries=2,
    )

    result3 = loop3.execute()
    tracker.record_usage("repo-analyzer", "gpt-4o-mini", 500, 250)
    memory.update_status("repo-3", "completed" if result3.success else "failed")

    print(f"Status: {'SUCCESS' if result3.success else 'FAILED'}")
    print(f"Attempts: {result3.attempts}")
    print(f"Tokens: {result3.tokens_used}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    budget = tracker.check_budget(estimated_tokens=100)
    summary = tracker.get_summary()
    print(f"\nTotal tokens used: {summary['total_tokens']}")
    print(f"Budget: {budget['budget']}")
    print(f"Can proceed: {budget['can_proceed']}")
    if budget["warnings"]:
        print(f"Warnings: {budget['warnings']}")

    loops = memory.list_loops()
    print(f"\nLoops executed: {len(loops)}")
    for loop in loops:
        print(f"  - {loop.loop_id}: {loop.status}")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
