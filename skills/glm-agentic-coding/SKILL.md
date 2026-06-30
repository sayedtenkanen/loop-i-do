---
name: glm-agentic-coding
description: Using GLM-5.2 for high-performance agentic coding tasks
---

# GLM-5.2 for Agentic Coding

GLM-5.2 is an open-weights model (753B params, 40B active) optimized for long-running agentic coding tasks.

## Key Features
- 1M token context window
- Function calling and structured output
- Context caching for repeated prompt parts
- MIT license (commercial use OK)
- Cost: ~25% of Claude Opus/GPT-5.5

## Performance
- PostTrainBench: 34.3% (top for agentic coding)
- Arena.ai WebDev: 1,593 Elo (2nd place)
- Artificial Analysis Intelligence: 51 (top open model)

## When to Use
- Long-running coding tasks
- Budget-conscious projects
- When you need open weights
- Web development tasks

## Integration

```python
from loop_engineering import Agent

# GLM-5.2 via Z.ai API
agent = Agent(
    system_prompt="You are an expert Python developer.",
    model="glm-5.2",  # or specific variant
)

# Or via OpenCode Zen
agent = Agent(
    system_prompt="You are an expert Python developer.",
    model="nemotron-3-ultra-free",  # similar capabilities
)
```

## Tips
- Use context caching for repeated prompts
- Set max_tokens appropriately (up to 128K output)
- Leverage function calling for tool use
- Monitor token usage for cost optimization
