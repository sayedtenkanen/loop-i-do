---
name: agentic-coding-loop
description: Loop where AI agent writes code, tests it, and iterates until bug-free
---

# Agentic Coding Loop

The fastest loop: every few minutes, the coding agent builds and tests a new version.

## When to Use
- Implementing a feature from a spec
- Fixing bugs with tests
- Refactoring code
- Any task where the agent can verify its own work

## How It Works

1. **Start with spec** - Clear description of what to build
2. **Write code** - Agent implements the feature
3. **Run tests** - Agent executes test suite
4. **Check results** - If tests pass, done; if fail, iterate
5. **Repeat** - Up to max_turns until success or give up

## Implementation Pattern

```python
from loop_engineering import Agent, ConnectorRegistry

registry = ConnectorRegistry()

@registry.register("run_tests", "Run pytest and return results", {...})
def run_tests(pattern: str = "tests/") -> str:
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", pattern, "-v"],
        capture_output=True, text=True, timeout=120
    )
    return f"Exit: {result.returncode}\n{result.stdout[-2000:]}"

@registry.register("run_linter", "Run ruff check", {...})
def run_linter() -> str:
    import subprocess
    result = subprocess.run(
        ["ruff", "check", "src/"],
        capture_output=True, text=True
    )
    return f"Exit: {result.returncode}\n{result.stdout}"

agent = Agent(
    system_prompt="""You are a coding agent. Write code, run tests, fix issues.
    Always run tests after changes. Iterate until tests pass.""",
    connectors=registry,
)

result = agent.run("Implement feature X with tests")
```

## Tips
- Always include test-running in your connectors
- Set reasonable max_turns (5-10) to prevent infinite loops
- Use dry_run mode to test without API calls
- Log each iteration for debugging

## Eval Integration
If you have evals (test datasets), measure performance each iteration:
- Track pass/fail rate over time
- Stop when eval score plateaus
- Use evals to guide what to fix next
