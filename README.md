# loop_engineering

A Python implementation of the pattern from Addy Osmani's
["Loop Engineering"](https://addyo.substack.com/p/loop-engineering):
stop prompting the agent yourself, build the system that prompts it
instead. Each module maps to one of the six building blocks.

| Article block        | Module                  | What it does |
|-----------------------|--------------------------|--------------|
| 1. Automations         | `automation.py`         | Scheduled triage that writes findings to Memory; runs that find nothing archive themselves. |
| 2. Worktrees            | `worktrees.py`           | `git worktree` wrapper so parallel agents never touch the same checkout. |
| 3. Skills               | `skills.py`              | Loads `SKILL.md` folders, matches one to a task by keyword overlap. |
| 4. Plugins / connectors | `connectors.py`          | Registry of Python callables exposed as OpenAI-compatible tool-use tools. |
| 5. Sub-agents            | `subagents.py`, `goal.py`| Maker/checker split — a separate model reviews the draft (`MakerChecker`), or judges whether a goal's stop condition holds (`GoalLoop`, the `/goal` primitive). |
| 6. Memory (the spine)   | `memory.py`              | JSON-backed state that survives between runs — swap for a markdown file or a Linear board. |
| engine                  | `agent.py`               | Tool-use loop wrapper around the OpenAI-compatible API (OpenCode Zen). |
| orchestrator            | `loop.py`                | Wires all six together into the "what one loop looks like" shape from the article. |

## Quick start

```bash
pip install loop-engineering
export OPENCODE_ZEN_API_KEY=your_key   # omit this to run everything in dry-run mode
python examples/demo.py
```

`examples/demo.py` runs the whole flow — memory, skill matching, maker/checker
review, and a `/goal` loop — against dry-run agents by default, so you
can see the wiring before spending a single token.

## Going live on a real repo

```python
from loop_engineering import Loop, ConnectorRegistry

registry = ConnectorRegistry()

@registry.register("open_pull_request", "Open a PR", {
    "type": "object",
    "properties": {"branch": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}},
    "required": ["branch", "title", "body"],
})
def open_pull_request(branch, title, body):
    # call your real git host's API here
    ...

loop = Loop(repo_path="/path/to/your/repo", connectors=registry)
loop.memory.add_finding({"title": "flaky test in test/auth/test_login.py"})
loop.tick()  # opens a worktree, runs maker -> checker, ships or escalates, cleans up
```

Wire `Loop.tick()` to an `Automation` on a schedule (cron, GitHub
Actions, APScheduler — `automation.py` gives you the shape, swap the
scheduler for whatever you already run) and you have the loop the
article describes: an automation finds work, each finding gets its
own worktree, a maker drafts a fix, a checker reviews it against your
skills, and a connector ships the result. Memory is what lets
tomorrow's run pick up where today's left off.

## What this does *not* automate

As the article is careful to point out: the loop changes the work, it
doesn't remove you from it. Verification, your own understanding of
what shipped, and your judgment about *when* to design a loop versus
just prompting directly are still on you — `MakerChecker` and
`GoalLoop` make "it's done" mean something more than a model marking
its own homework, but "done" is still a claim, not a proof.
