---
name: external-feedback-loop
description: Gather feedback from users, testers, and production data
---

# External Feedback Loop

The slowest loop: hours to days for user feedback, A/B tests, and production data.

## When to Use
- After initial release
- Validating product direction
- Measuring user satisfaction
- Optimizing conversion
- Identifying bugs in production

## Feedback Channels

### 1. Quick Feedback (hours)
- Ask a few friends
- Post on social media
- Internal dogfooding

### 2. Alpha Testing (days)
- Invite beta users
- Collect structured feedback
- Monitor usage patterns

### 3. Production Data (days-weeks)
- A/B testing
- Analytics dashboards
- Support tickets
- Usage metrics

## Implementation Pattern

```python
from loop_engineering import Agent, Memory

memory = Memory("feedback_state.json")
agent = Agent(system_prompt="You analyze user feedback and suggest improvements.")

# Simulate feedback collection
feedback_data = {
    "support_tickets": ["login fails on mobile", "slow page load"],
    "analytics": {"bounce_rate": 0.45, "avg_session": "2m30s"},
    "feature_requests": ["dark mode", "export to CSV"],
}

# Agent analyzes and prioritizes
result = agent.run(f"""
Analyze this feedback and suggest top 3 improvements:

Support tickets: {feedback_data['support_tickets']}
Analytics: {feedback_data['analytics']}
Feature requests: {feedback_data['feature_requests']}

Prioritize by impact and effort.
""")

# Create findings from analysis
memory.add_finding({"title": "Fix mobile login", "priority": "high"})
memory.add_finding({"title": "Optimize page load", "priority": "high"})
memory.add_finding({"title": "Add dark mode", "priority": "medium"})
```

## Metrics to Track

### Engagement
- Session duration
- Pages per session
- Return visit rate

### Satisfaction
- NPS score
- Support ticket volume
- Feature request frequency

### Conversion
- Sign-up rate
- Activation rate
- Retention rate

## Tips
- Start small: 5 users > 0 users
- Use structured feedback forms
- Combine quantitative (metrics) with qualitative (interviews)
- Close the loop: tell users what you built based on their feedback
- Don't over-index on vocal minorities
