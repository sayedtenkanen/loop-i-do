# Loop Engineering Architecture - Python Implementation

"""
A Python-based system for orchestrating AI agents through automated loops,
implementing the concepts from Addy Osmani's "Loop Engineering" article.

Components:
- orchestration: Central control system
- automations: Scheduling system
- memory: State management
- skills: Knowledge storage
- worktrees: Isolation layer
- agents: Agent registry
- plugins: External integrations
- config: Configuration management
- token_tracker: Token usage tracking
- production_hardening: Circuit breaker, rate limiting, etc.
- errors: Structured error types
- metrics: Prometheus metrics
"""

__version__ = "1.0.0"
__author__ = "Loop Engineering Team"
