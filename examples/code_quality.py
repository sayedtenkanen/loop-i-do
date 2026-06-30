"""Example: Code quality review using Loop Engineering."""

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
    """Demonstrate code quality review loop."""
    print("=" * 60)
    print("LOOP ENGINEERING: Code Quality Review Example")
    print("=" * 60)

    # Configure components
    config = AgentConfig(model="gpt-4o-mini", temperature=0.3)
    agent = Agent(name="quality-reviewer", config=config)
    verifier = Verifier()
    tracker = TokenTracker(budget=5000)
    memory = MemoryLayer()

    # Code to review
    code_to_review = """
    def process_data(data):
        result = []
        for i in range(len(data)):
            if data[i] != None:
                result.append(data[i] * 2)
        return result

    def fetch_user(user_id):
        import requests
        response = requests.get(f"https://api.example.com/users/{user_id}")
        return response.json()
    """

    # Save state
    state = LoopState(loop_id="quality-1", status="idle", task="Code quality review")
    memory.save(state)

    # Create loop
    task = f"Review this code for quality issues:\n{code_to_review}"
    loop = Loop(
        name="quality-loop",
        task=task,
        agent=agent,
        verifier=verifier,
        max_retries=2,
    )

    print("\nRunning code quality review loop...")
    result = loop.execute()

    # Track tokens
    tracker.record_usage(
        agent_id="quality-reviewer",
        model="gpt-4o-mini",
        input_tokens=500,
        output_tokens=300,
    )

    # Update memory
    memory.update_status("quality-1", "completed" if result.success else "failed")

    # Display results
    print(f"\nLoop completed: {result.success}")
    print(f"Attempts: {result.attempts}")
    print(f"Tokens used: {result.tokens_used}")

    # Show budget status
    budget = tracker.check_budget(estimated_tokens=200)
    print("\nBudget status:")
    print(f"  Can proceed: {budget['can_proceed']}")
    print(f"  Remaining: {budget['remaining_tokens']} tokens")
    print(f"  Warnings: {len(budget['warnings'])}")

    # Show memory
    loaded = memory.load("quality-1")
    print(f"\nMemory status: {loaded.status}")


if __name__ == "__main__":
    main()
