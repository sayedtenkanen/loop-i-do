# Loop Engineering Architecture - Worktrees Manager

## Purpose
Provide isolated workspaces for parallel agent execution to prevent conflicts.

## Key Interfaces

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import shutil
from datetime import datetime
import asyncio
import fcntl
import os

@dataclass
class Worktree:
    task_id: str
    path: str
    branch: str
    created_at: datetime
    base_repo_path: str
    is_active: bool = True
    lock_fd: int = None  # File descriptor for lock

class WorktreeManager:
    def __init__(self, base_repo_path: str = ".", max_concurrent: int = 10,
                 subprocess_timeout: int = 60):
        self.base_path = Path(base_repo_path).resolve()
        self.worktrees: Dict[str, Worktree] = {}
        self.worktree_dir = self.base_path.parent / "worktrees"
        self.worktree_dir.mkdir(exist_ok=True)
        self.max_concurrent = max_concurrent
        self.subprocess_timeout = subprocess_timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._locks_dir = self.worktree_dir / ".locks"
        self._locks_dir.mkdir(exist_ok=True)
    
    def _get_lock_path(self, task_id: str) -> Path:
        """Get lock file path for a task"""
        return self._locks_dir / f"{task_id}.lock"
    
    def _acquire_lock(self, task_id: str) -> int:
        """Acquire file lock for a task (non-blocking)"""
        lock_path = self._get_lock_path(task_id)
        lock_fd = open(lock_path, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_fd.write(f"{os.getpid()}\n")
            lock_fd.flush()
            return lock_fd.fileno()
        except IOError:
            lock_fd.close()
            return None
    
    def _release_lock(self, task_id: str, lock_fd: int):
        """Release file lock"""
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except:
                pass
            lock_path = self._get_lock_path(task_id)
            if lock_path.exists():
                lock_path.unlink()
    
    async def create_worktree(self, task_id: str) -> Worktree:
        """Create an isolated worktree for a task with concurrency control"""
        # Acquire lock to prevent duplicate worktrees for same task
        lock_fd = self._acquire_lock(task_id)
        if lock_fd is None:
            raise RuntimeError(f"Could not acquire lock for task {task_id}")
        
        try:
            # Use semaphore to limit concurrent worktrees
            async with self._semaphore:
                # Generate unique branch name
                branch_name = f"worktree-{task_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                worktree_path = self.worktree_dir / f"worktree-{task_id}"
                
                # Check if worktree already exists
                if worktree_path.exists():
                    await self._delete_worktree_files(worktree_path)
                
                # Create git worktree with timeout
                try:
                    subprocess.run(
                        ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                        cwd=str(self.base_path),
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=self.subprocess_timeout
                    )
                except subprocess.TimeoutExpired:
                    raise RuntimeError(f"Git worktree creation timed out for task {task_id}")
                except subprocess.CalledProcessError:
                    # Fallback to copy if git worktree fails
                    await self._create_copy_worktree(task_id, worktree_path)
                    branch_name = f"copy-{task_id}"
                
                # Create worktree object
                worktree = Worktree(
                    task_id=task_id,
                    path=str(worktree_path),
                    branch=branch_name,
                    created_at=datetime.now(),
                    base_repo_path=str(self.base_path),
                    is_active=True,
                    lock_fd=lock_fd
                )
                
                self.worktrees[task_id] = worktree
                return worktree
        except Exception:
            self._release_lock(task_id, lock_fd)
            raise
    
    async def _create_copy_worktree(self, task_id: str, worktree_path: Path):
        """Create worktree by copying repository"""
        # Use git clone --local for faster copy that preserves history
        try:
            subprocess.run(
                ["git", "clone", "--local", "--no-checkout", 
                 str(self.base_path), str(worktree_path)],
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            # Fallback to shutil.copytree
            shutil.copytree(
                str(self.base_path),
                str(worktree_path),
                ignore=shutil.ignore_patterns('.git', '__pycache__', 'node_modules')
            )
            
            # Initialize git in copy
            subprocess.run(
                ["git", "init"],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            
            # Add remote to original repo
            subprocess.run(
                ["git", "remote", "add", "origin", str(self.base_path)],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
    
    async def _delete_worktree_files(self, worktree_path: Path):
        """Delete worktree files"""
        if worktree_path.exists():
            shutil.rmtree(worktree_path)
    
    async def delete_worktree(self, task_id: str):
        """Clean up worktree after task completion"""
        worktree = self.worktrees.get(task_id)
        if not worktree:
            return
        
        worktree_path = Path(worktree.path)
        
        # Try git worktree removal first with timeout
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            # Fallback to directory removal
            await self._delete_worktree_files(worktree_path)
        
        # Remove branch if it exists with timeout
        try:
            subprocess.run(
                ["git", "branch", "-D", worktree.branch],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass  # Branch might not exist
        
        # Release lock
        self._release_lock(task_id, worktree.lock_fd)
        
        # Update worktree status
        worktree.is_active = False
        del self.worktrees[task_id]
    
    async def get_worktree_path(self, task_id: str) -> Optional[str]:
        """Get filesystem path for a worktree"""
        worktree = self.worktrees.get(task_id)
        if worktree and worktree.is_active:
            return worktree.path
        return None
    
    async def merge_changes(self, task_id: str, strategy: str = "merge"):
        """Merge worktree changes back to main"""
        worktree = self.worktrees.get(task_id)
        if not worktree:
            raise ValueError(f"Worktree for task {task_id} not found")
        
        worktree_path = Path(worktree.path)
        
        if strategy == "merge":
            # Merge branch into main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            subprocess.run(
                ["git", "merge", worktree.branch],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        
        elif strategy == "rebase":
            # Rebase onto main
            subprocess.run(
                ["git", "checkout", worktree.branch],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            subprocess.run(
                ["git", "rebase", "main"],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            
            # Switch back to main and merge
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            subprocess.run(
                ["git", "merge", worktree.branch],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        
        elif strategy == "squash":
            # Squash commits and merge
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            subprocess.run(
                ["git", "merge", "--squash", worktree.branch],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
            subprocess.run(
                ["git", "commit", "-m", f"Squashed changes from task {task_id}"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                timeout=self.subprocess_timeout
            )
        
        # Clean up worktree after merge
        await self.delete_worktree(task_id)
    
    async def get_changed_files(self, task_id: str) -> List[str]:
        """Get list of changed files in worktree"""
        worktree = self.worktrees.get(task_id)
        if not worktree:
            return []
        
        worktree_path = Path(worktree.path)
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=self.subprocess_timeout
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []
    
    async def create_commit(self, task_id: str, message: str):
        """Create a commit in the worktree"""
        worktree = self.worktrees.get(task_id)
        if not worktree:
            raise ValueError(f"Worktree for task {task_id} not found")
        
        worktree_path = Path(worktree.path)
        
        # Stage all changes
        subprocess.run(
            ["git", "add", "."],
            cwd=str(worktree_path),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout
        )
        
        # Create commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(worktree_path),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout
        )
    
    async def list_active_worktrees(self) -> List[Dict]:
        """List all active worktrees"""
        return [
            {
                "task_id": wt.task_id,
                "path": wt.path,
                "branch": wt.branch,
                "created_at": wt.created_at.isoformat(),
                "is_active": wt.is_active
            }
            for wt in self.worktrees.values()
            if wt.is_active
        ]
    
    async def cleanup_old_worktrees(self, max_age_hours: int = 24):
        """Clean up worktrees older than specified hours"""
        current_time = datetime.now()
        
        for task_id, worktree in list(self.worktrees.items()):
            age_hours = (current_time - worktree.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                await self.delete_worktree(task_id)

# Alternative: Docker-based isolation
class DockerWorktreeManager:
    """Docker-based worktree isolation for complete environment isolation"""
    
    def __init__(self, base_image: str = "python:3.9-slim"):
        self.base_image = base_image
        self.containers: Dict[str, str] = {}
    
    async def create_worktree(self, task_id: str) -> Dict:
        """Create Docker container for isolation"""
        container_name = f"worktree-{task_id}"
        
        # Create and start container
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", container_name,
                "-v", f"{os.getcwd()}:/app",
                "-w", "/app",
                self.base_image,
                "sleep", "infinity"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        
        self.containers[task_id] = container_name
        
        return {
            "task_id": task_id,
            "container": container_name,
            "path": "/app"
        }
    
    async def execute_in_worktree(self, task_id: str, command: str) -> str:
        """Execute command in worktree container"""
        container_name = self.containers.get(task_id)
        if not container_name:
            raise ValueError(f"No container for task {task_id}")
        
        result = subprocess.run(
            ["docker", "exec", container_name, "sh", "-c", command],
            check=True,
            capture_output=True,
            text=True
        )
        
        return result.stdout
    
    async def delete_worktree(self, task_id: str):
        """Delete worktree container"""
        container_name = self.containers.get(task_id)
        if container_name:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                check=True,
                capture_output=True
            )
            del self.containers[task_id]
```

## Implementation Notes

1. **Git Worktrees**: Preferred for git repositories, provides true isolation
2. **Copy Fallback**: When git worktrees aren't available, copy the repository
3. **Docker Isolation**: Complete environment isolation for complex scenarios
4. **Cleanup**: Automatic cleanup of old worktrees to prevent disk bloat
5. **Merge Strategies**: Support for merge, rebase, and squash strategies

## Example Usage

```python
# Initialize worktree manager
wt_manager = WorktreeManager("/path/to/repo")

# Create worktree for a task
worktree = await wt_manager.create_worktree("bug-fix-123")
print(f"Worktree created at: {worktree.path}")

# Work in the worktree...
# ...

# Get changed files
changed_files = await wt_manager.get_changed_files("bug-fix-123")

# Create commit
await wt_manager.create_commit("bug-fix-123", "Fix: resolve authentication issue")

# Merge changes back
await wt_manager.merge_changes("bug-fix-123", strategy="squash")

# Clean up
await wt_manager.delete_worktree("bug-fix-123")
```
