# Loop Engineering - Blueprint Documentation

This directory contains early architecture blueprints and design documents.
The actual implementation is in `src/loop_engineering/`.

## Actual Implementation

```
src/loop_engineering/
├── __init__.py          # Package exports
├── agent.py             # Tool-use loop wrapper (OpenAI SDK, OpenCode Zen)
├── automation.py        # Scheduled triage with skill-based routing
├── connectors.py        # Plugin/tool registry (OpenAI function calling)
├── debug.py             # Debug logging module
├── goal.py              # GoalLoop - /goal primitive (worker + judge)
├── loop.py              # Orchestrator wiring all components
├── memory.py            # JSON-backed state (thread-safe)
├── skills.py            # SKILL.md folder matching
├── subagents.py         # MakerChecker + ReviewResult
└── worktrees.py         # Git worktree isolation
```

## Skills

```
skills/
├── agentic-coding-loop/SKILL.md    # Fast loop for iterative coding
├── developer-feedback-loop/SKILL.md # Human review and steering
├── external-feedback-loop/SKILL.md  # User feedback and A/B testing
├── flaky-test/SKILL.md             # Flaky test triage
└── glm-agentic-coding/SKILL.md     # GLM-5.2 model usage
```

## For the actual package documentation, see the root `README.md`.
