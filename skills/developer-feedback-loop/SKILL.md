---
name: developer-feedback-loop
description: Human reviews agent output and provides steering feedback
---

# Developer Feedback Loop

The middle loop: developer examines the current product and steers the coding agent.

## When to Use
- After initial implementation is working
- UI/UX improvements
- Feature prioritization
- Architecture decisions
- When you have context the AI lacks

## How It Works

1. **Agent produces output** - Code, UI, or design
2. **Developer reviews** - Examine what was built
3. **Developer provides feedback** - Specific, actionable instructions
4. **Agent implements changes** - Based on feedback
5. **Repeat** - Until satisfied

## Key Insight: Humans Have Context Advantage

Andrew Ng notes: "Humans know a lot more than the AI system about the users and the context the product has to operate in."

This is why human-in-the-loop is needed:
- User needs and preferences
- Business requirements
- Domain expertise
- Product vision
- Technical constraints

## Implementation Pattern

```python
from loop_engineering import Agent, Memory

memory = Memory("product_state.json")
agent = Agent(system_prompt="You implement product changes based on feedback.")

# Developer reviews and provides feedback
feedback = "The login button should be blue, not green. Also, add remember-me checkbox."

# Agent implements
result = agent.run(f"""
Current state: {memory.open_findings()}
Developer feedback: {feedback}
Implement these changes.
""")

# Log for next iteration
memory.log(f"Implemented: {feedback[:100]}")
```

## Feedback Types

### UI Feedback
- "Make the header larger"
- "Change color scheme to dark mode"
- "Move navigation to the left"

### Feature Feedback
- "Add export to PDF"
- "Users need a search function"
- "Support multiple languages"

### Architecture Feedback
- "This should use a database, not JSON files"
- "Add caching for performance"
- "Split this into microservices"

## Tips
- Be specific: "Add X" not "improve it"
- One change at a time when possible
- Reference existing code/designs
- Explain the "why" when helpful
