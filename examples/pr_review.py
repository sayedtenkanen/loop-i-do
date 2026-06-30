"""Example: PR Review using Loop Engineering."""

from loop_engineering import Agent, AgentConfig, Loop, LoopState, MemoryLayer, Verifier


def main():
    """Demonstrate PR review loop."""
    print("=" * 60)
    print("LOOP ENGINEERING: PR Review Example")
    print("=" * 60)

    # Configure
    config = AgentConfig(model="gpt-4o-mini", temperature=0.2)
    agent = Agent(name="pr-reviewer", config=config)
    verifier = Verifier()
    memory = MemoryLayer()

    # Simulated PR diff
    pr_diff = """
    --- a/src/utils.py
    +++ b/src/utils.py
    @@ -10,6 +10,15 @@
     def format_name(first, last):
         return f"{first} {last}"

    +def validate_email(email):
    +    if "@" in email:
    +        return True
    +    return False
    +
    +def process_user(user):
    +    name = format_name(user['first'], user['last'])
    +    email = user['email']
    +    return {"name": name, "valid": validate_email(email)}
    """

    # Save state
    state = LoopState(loop_id="pr-review-1", status="idle", task="PR review")
    memory.save(state)

    # Create loop
    task = f"Review this PR diff and provide feedback:\n{pr_diff}"
    loop = Loop(
        name="pr-review-loop",
        task=task,
        agent=agent,
        verifier=verifier,
        max_retries=2,
    )

    print("\nRunning PR review loop...")
    result = loop.execute()

    # Update memory
    memory.update_status("pr-review-1", "completed" if result.success else "failed")

    # Display results
    print(f"\nLoop completed: {result.success}")
    print(f"Attempts: {result.attempts}")
    print(f"Tokens used: {result.tokens_used}")

    if result.output:
        print(f"\nReview feedback:\n{result.output}")

    # Show memory
    loaded = memory.load("pr-review-1")
    print(f"\nMemory status: {loaded.status}")


if __name__ == "__main__":
    main()
