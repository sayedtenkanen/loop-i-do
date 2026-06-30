"""Worktrees — isolation so parallel agents don't collide."""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path


class WorktreeManager:
    def __init__(self, repo_path: str | Path, worktrees_root: str | Path = ".worktrees"):
        self.repo_path = Path(repo_path)
        self.worktrees_root = self.repo_path / worktrees_root
        self.worktrees_root.mkdir(parents=True, exist_ok=True)

    def create(self, branch_prefix: str = "loop") -> Path:
        name = f"{branch_prefix}-{uuid.uuid4().hex[:8]}"
        target = self.worktrees_root / name
        subprocess.run(
            ["git", "worktree", "add", "-b", name, str(target)],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return target

    def remove(self, worktree_path: str | Path) -> None:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )

    def list(self) -> list[str]:
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().splitlines()
