# Loop Engineering Architecture Blueprint

A Python-based system for orchestrating AI agents through automated loops, replacing manual prompting with designed systems.

## Overview

This architecture implements the five building blocks from Addy Osmani's "Loop Engineering" article:

1. **Automations** - Time-based and event-based trigger system
2. **Worktrees** - Isolated workspaces for parallel agent execution
3. **Skills** - Project-specific knowledge storage for agents
4. **Plugins/Connectors** - Integration with external tools via MCP
5. **Sub-agents** - Role-based agent orchestration
6. **Memory** - Persistent state management between runs

## Directory Structure

```
docs/
├── README.md                    # This file
├── orchestration/               # Central control system
├── automations/                 # Scheduling system
├── memory/                      # State management
├── skills/                      # Knowledge storage
├── worktrees/                   # Isolation layer
├── agents/                      # Agent registry and types
├── plugins/                     # External integrations
└── config/                      # Configuration management
```

## Implementation Approach

- **Framework**: Uses existing Python frameworks (LangChain, CrewAI, APScheduler)
- **Architecture**: Modular design with clear interfaces between components
- **State Management**: Persistent storage with SQLite/Redis/PostgreSQL backends
- **Isolation**: Git worktrees or temporary directories for parallel execution
- **Monitoring**: Structured logging and metrics collection

## Key Interfaces

Each component exposes clean interfaces for integration:

```python
# Example usage
orchestrator = LoopOrchestrator(config)
await orchestrator.run_loop(loop_definition)
```

## Next Steps

1. Review component-specific documentation in each directory
2. Implement core orchestration layer
3. Add memory and automation systems
4. Integrate agent types and skills engine
5. Add monitoring and production hardening
