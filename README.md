# Loop Engineering System

A Python-based system for orchestrating AI agents through automated loops, implementing the concepts from Addy Osmani's "Loop Engineering" article.

## Overview

This system replaces manual prompting of AI agents with designed systems that automatically discover work, implement solutions, verify results, and manage state across sessions.

## Architecture Components

### 1. Orchestration Layer (`orchestration/`)
Central control system managing workflows, state transitions, and component coordination.

### 2. Automations Scheduler (`automations/`)
Time-based and event-based trigger system for loop execution.

### 3. Memory Layer (`memory/`)
Persistent state storage between loop runs, maintaining context across sessions.

### 4. Skills Engine (`skills/`)
Store and retrieve project-specific knowledge, conventions, and instructions for agents.

### 5. Worktrees Manager (`worktrees/`)
Provide isolated workspaces for parallel agent execution to prevent conflicts.

### 6. Agent Registry (`agents/`)
Manage different agent types with specific roles and capabilities.

### 7. Plugins Manager (`plugins/`)
Integrate with external tools and services via Model Context Protocol (MCP).

## Quick Start

```python
from docs.orchestration import LoopOrchestrator, LoopConfig, LoopDefinition
from docs.memory import MemoryLayer
from docs.automations import AutomationScheduler

# Initialize components
config = LoopConfig()
memory = MemoryLayer(config.memory.backend)
scheduler = AutomationScheduler(memory)
orchestrator = LoopOrchestrator(config)

# Define a loop
loop_def = LoopDefinition(
    id="daily-code-quality",
    description="Automated code quality checks and fixes",
    discovery_task="Analyze codebase for quality issues",
    verification_criteria={"tests_pass": True, "lint_clean": True}
)

# Run the loop
await orchestrator.run_loop(loop_def)
```

## Key Features

- **Automated Discovery**: Agents automatically find and prioritize work
- **Isolated Execution**: Worktrees prevent parallel agent conflicts
- **Persistent State**: Memory layer maintains context across runs
- **Role-Based Agents**: Specialized agents for exploration, implementation, and verification
- **Plugin System**: Extensible integration with external tools
- **Skills System**: Project-specific knowledge for informed decision making

## Configuration

See `docs/config/loop_config.yaml` for configuration options and `docs/config/schema.py` for validation schemas.

## Directory Structure

```
loop-it-do/
├── README.md
└── docs/
    ├── README.md
    ├── orchestration/
    ├── automations/
    ├── memory/
    ├── skills/
    ├── worktrees/
    ├── agents/
    ├── plugins/
    └── config/
```

## Development

Each component is implemented as a Python module with:
- Type hints and dataclasses for type safety
- Async/await for non-blocking operations
- Comprehensive error handling
- Example usage and documentation

## Next Steps

1. Implement production-ready storage backends
2. Add monitoring and metrics collection
3. Create deployment configurations
4. Write comprehensive tests
5. Add integration with popular AI frameworks
