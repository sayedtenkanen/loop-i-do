"""Loop Engineering — Automated AI agent orchestration."""

__version__ = "0.1.0"

from .agent import Agent
from .automation import Automation, make_skill_triage
from .connectors import Connector, ConnectorRegistry
from .goal import GoalLoop
from .loop import Loop
from .memory import Memory
from .skills import Skill, SkillRegistry
from .subagents import MakerChecker, ReviewResult
from .worktrees import WorktreeManager

__all__ = [
    "Agent",
    "Automation",
    "make_skill_triage",
    "Connector",
    "ConnectorRegistry",
    "GoalLoop",
    "Loop",
    "Memory",
    "Skill",
    "SkillRegistry",
    "MakerChecker",
    "ReviewResult",
    "WorktreeManager",
]
