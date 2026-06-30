# Loop Engineering

A Python package for automated AI agent orchestration with task loops, verification, and memory.

## Installation

```bash
pip install loop-engineering
```

## Quick Start

```python
from loop_engineering import Agent, AgentConfig, Loop, Verifier

# Configure agent
config = AgentConfig(model="gpt-4o-mini", temperature=0.3)
agent = Agent(name="my-agent", config=config)
verifier = Verifier()

# Create and run loop
loop = Loop(
    name="my-loop",
    task="Write a Python function to calculate factorial",
    agent=agent,
    verifier=verifier,
)

result = loop.execute()
print(f"Success: {result.success}")
print(f"Attempts: {result.attempts}")
```

## Features

- **Agent**: Configurable AI agent with LLM integration
- **Loop**: Orchestrates multiple attempts with retries
- **Verifier**: Validates agent outputs
- **TokenTracker**: Monitors token usage and budgets
- **MemoryLayer**: Persists loop state to SQLite

## Examples

See the `examples/` directory for complete examples:

- `auto_fix_issues.py` - Auto-fix code errors
- `code_quality.py` - Code quality review
- `pr_review.py` - PR review automation

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/ tests/
ruff format --check src/ tests/

# Run type checking
mypy src/
```

## License

MIT
