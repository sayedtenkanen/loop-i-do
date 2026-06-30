# MVP Scope: 30-Day Plan

## Goal

Get 10 users who run at least one loop and give feedback.

## What We're Building

### Core Loop (Week 1-2)

```python
from loop_engineering import Loop, Agent, ConnectorRegistry

# Define a simple loop
loop = Loop(
    name="fix-github-issues",
    agent=Agent(model="nemotron-3-ultra-free"),
    connectors=ConnectorRegistry(),
    task="Find and fix open GitHub issues",
)

# Run it
loop.tick()
```

### What's Included

| Feature | Status | Module |
|---------|--------|--------|
| Agent with tool-use loop | ✅ Built | `agent.py` |
| Automations (scheduled triage) | ✅ Built | `automation.py` |
| Worktrees (git isolation) | ✅ Built | `worktrees.py` |
| Skills (SKILL.md matching) | ✅ Built | `skills.py` |
| Connectors (plugin/tool registry) | ✅ Built | `connectors.py` |
| Sub-agents (MakerChecker) | ✅ Built | `subagents.py` |
| GoalLoop (/goal primitive) | ✅ Built | `goal.py` |
| Memory (JSON-backed state) | ✅ Built | `memory.py` |
| Debug logging | ✅ Built | `debug.py` |
| Auto skill loading | ✅ Built | `agent.py` |

### What's NOT Included (Cut These)

| Feature | Reason | When |
|---------|--------|------|
| Dashboard | Not needed | V2 |
| SSO | Enterprise only | V2 |
| K8s deployment | Too early | V2 |
| Notification system | Nice to have | V1 |

---

## 30-Day Sprint Plan

### Week 1: Validate & Simplify

**Goal:** Confirm people want this

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Interview 2 dev leads | Notes on pain points |
| Tue | Interview 2 more dev leads | Notes on pain points |
| Wed | Interview 1 CTO | Notes on CTO needs |
| Thu | Analyze interviews | Key insights |
| Fri | Cut MVP scope | Simplified feature list |

**Success:** 5 interviews completed, pain points validated

### Week 2: Ship MVP

**Goal:** Get something running

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Clean up code | Working package |
| Tue | Write README | Documentation |
| Wed | Create example | Basic usage example |
| Thu | Test end-to-end | Working loop |
| Fri | Push to PyPI | `pip install loop-engineering` |

**Success:** Package installable, example runs

### Week 3: Get Users

**Goal:** 10 users trying it

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Post on Twitter | Announcement tweet |
| Tue | Post on Hacker News | Show HN post |
| Wed | Post on Reddit | r/Python, r/MachineLearning |
| Thu | Email 5 contacts | Personal outreach |
| Fri | Set up Discord | Community channel |

**Success:** 10+ signups, 3+ conversations

### Week 4: Learn & Iterate

**Goal:** Understand what to build next

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Talk to 3 users | Feedback notes |
| Tue | Talk to 2 more users | Feedback notes |
| Wed | Analyze feedback | Key themes |
| Thu | Prioritize fixes | Updated backlog |
| Fri | Ship V0.1.1 | Fixes + learnings |

**Success:** 5 user conversations, clear next steps

---

## Success Metrics

### Week 1-2 (Build)

| Metric | Target | Actual |
|--------|--------|--------|
| Interviews | 5 | |
| Pain points validated | 3+ | |
| MVP scope cut | 50% | |

### Week 3-4 (Launch)

| Metric | Target | Actual |
|--------|--------|--------|
| GitHub stars | 20 | |
| PyPI installs | 10 | |
| Discord members | 5 | |
| User conversations | 5 | |
| NPS | > 30 | |

---

## User Interview Script

### Opening (2 min)

> "Hi, I'm building a tool to automate AI agent workflows. I'd love to learn about how you use AI agents today. No sales pitch - just trying to understand your problems."

### Questions (20 min)

1. **Current state:** "Walk me through how you use AI agents for coding tasks."
2. **Pain points:** "What's the most frustrating part?"
3. **Cost:** "How much are you spending on AI tokens? Is that a problem?"
4. **Quality:** "How often does AI output need rework?"
5. **Time:** "How much time do you spend prompting AI per day?"
6. **Solution:** "What would your ideal AI workflow look like?"
7. **Willingness:** "If this saved you 10 hours/week, what would you pay?"

### Closing (3 min)

> "Would you be willing to try an early version and give feedback? I'll give you free access for life."

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **No one signs up** | Personal outreach to 20 contacts |
| **Users try but churn** | Daily check-ins, fast fixes |
| **Too complex** | Simplify further, better docs |
| **No feedback** | Offer incentives (free access, swag) |

---

## Definition of Done

### MVP is Done When:

- [ ] 5 user interviews completed
- [ ] Pain points validated (3+ people confirm)
- [ ] Package installable via pip
- [ ] Example runs end-to-end
- [ ] 10 people have tried it
- [ ] 5 people have given feedback
- [ ] Clear next steps defined

### NOT Done When:

- [ ] All features are built
- [ ] Documentation is perfect
- [ ] Tests are 100%
- [ ] Dashboard is ready
- [ ] Enterprise features exist

---

*Plan created: 2026-06-30*
*Review after Week 2*
