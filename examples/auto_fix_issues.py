"""Example: Auto-fix code issues using Loop Engineering."""

from loop_engineering import Agent, AgentConfig, Loop, LoopState, MemoryLayer, Verifier


def main():
    """Demonstrate auto-fix loop for code issues."""
    print("=" * 60)
    print("LOOP ENGINEERING: Auto-Fix Code Issues Example")
    print("=" * 60)

    # Configure agent
    config = AgentConfig(
        model="gpt-4o-mini",
        temperature=0.2,
    )
    agent = Agent(name="auto-fixer", config=config)
    verifier = Verifier()
    memory = MemoryLayer()

    # Define the task
    task = """
    Fix the following Python code that has syntax and logic errors:

    ```python
    def calculate_average(numbers)
        total = 0
        for num in numbers
            total += num
        return total / len(numbers)

    # Call with empty list
    result = calculate_average([])
    ```

    Requirements:
    1. Fix syntax errors (missing colons)
    2. Handle edge case of empty list
    3. Add proper return type
    """

    # Save initial state
    state = LoopState(loop_id="auto-fix-1", status="idle", task=task.strip())
    memory.save(state)

    # Create and run loop
    loop = Loop(
        name="auto-fix-loop",
        task=task.strip(),
        agent=agent,
        verifier=verifier,
        max_retries=3,
    )

    print("\nRunning auto-fix loop...")
    result = loop.execute()

    # Update memory
    memory.update_status("auto-fix-1", "completed" if result.success else "failed")

    # Display results
    print(f"\nLoop completed: {result.success}")
    print(f"Attempts: {result.attempts}")
    print(f"Tokens used: {result.tokens_used}")

    if result.output:
        print(f"\nAgent response:\n{result.output}")

    # Show memory state
    loaded = memory.load("auto-fix-1")
    print(f"\nMemory status: {loaded.status}")


if __name__ == "__main__":
    main()
