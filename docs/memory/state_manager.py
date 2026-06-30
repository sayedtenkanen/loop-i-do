# Loop Engineering Architecture - Memory Layer

## Purpose
Persistent state storage between loop runs, maintaining context across sessions.
Key insight from article: "The model forgets everything between runs so the memory 
has to be on disk and not in the context."

## Key Interfaces

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import sqlite3
import asyncio

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskState:
    task_id: str
    loop_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Dict[str, Any] = None
    error: str = None
    retry_count: int = 0

@dataclass
class LoopState:
    loop_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    tasks: List[TaskState]
    metadata: Dict[str, Any] = None
    error: str = None

# Context vs Audit state separation
# ContextState: Small, fits in agent context window
# AuditState: Large, stays on disk for history/debugging
@dataclass
class ContextState:
    """State that fits in agent context window (small)"""
    loop_id: str
    status: str
    current_task_id: Optional[str]
    pending_task_count: int
    completed_task_count: int
    failed_task_count: int
    last_error: Optional[str]
    summary: str  # Brief summary of what's happening
    
    def to_dict(self) -> Dict:
        return {
            "loop_id": self.loop_id,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "pending": self.pending_task_count,
            "completed": self.completed_task_count,
            "failed": self.failed_task_count,
            "last_error": self.last_error,
            "summary": self.summary
        }
    
    def estimate_tokens(self) -> int:
        """Estimate token count for this state"""
        return len(json.dumps(self.to_dict())) // 4

@dataclass
class AuditState:
    """Full state for debugging and history (large)"""
    loop_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    tasks: List[TaskState]
    metadata: Dict[str, Any] = None
    error: str = None
    token_usage: Dict[str, Any] = None
    execution_log: List[Dict] = None

class MemoryLayer:
    def __init__(self, storage_backend: str = "sqlite", 
                 connection_string: str = None):
        self.storage_backend = storage_backend
        self.connection_string = connection_string
        self.storage = self._init_storage()
        
    def _init_storage(self):
        """Initialize storage backend"""
        if self.storage_backend == "sqlite":
            return SQLiteStorage(self.connection_string)
        elif self.storage_backend == "redis":
            return RedisStorage(self.connection_string)
        elif self.storage_backend == "json":
            return JSONStorage(self.connection_string)
        else:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")
    
    async def save_state(self, loop_id: str, state: Dict[str, Any]):
        """Save loop state to persistent storage"""
        await self.storage.save_loop_state(loop_id, state)
    
    async def load_state(self, loop_id: str) -> Dict[str, Any]:
        """Load loop state from storage"""
        return await self.storage.load_loop_state(loop_id)
    
    async def load_state_for_context(self, loop_id: str, 
                                    max_tokens: int = 2000) -> ContextState:
        """Load state truncated to fit in agent context window
        
        This is the key method for "memory as disk, not context":
        - Loads full state from disk
        - Extracts only what agents need
        - Truncates to fit token budget
        """
        full_state = await self.load_state(loop_id)
        
        if not full_state:
            return ContextState(
                loop_id=loop_id,
                status="unknown",
                current_task_id=None,
                pending_task_count=0,
                completed_task_count=0,
                failed_task_count=0,
                last_error=None,
                summary="No state found"
            )
        
        # Extract context-relevant info
        tasks = full_state.get("tasks", {})
        pending = sum(1 for t in tasks.values() if t.get("status") == "pending")
        completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
        failed = sum(1 for t in tasks.values() if t.get("status") == "failed")
        
        # Find current task
        current_task = None
        for task_id, task in tasks.items():
            if task.get("status") == "in_progress":
                current_task = task_id
                break
        
        # Create context state
        context = ContextState(
            loop_id=loop_id,
            status=full_state.get("status", "unknown"),
            current_task_id=current_task,
            pending_task_count=pending,
            completed_task_count=completed,
            failed_task_count=failed,
            last_error=full_state.get("error"),
            summary=self._generate_summary(full_state)
        )
        
        # Truncate if exceeds token budget
        while context.estimate_tokens() > max_tokens and context.summary:
            context.summary = context.summary[:-100] + "..."
        
        return context
    
    def _generate_summary(self, state: Dict) -> str:
        """Generate brief summary of loop state"""
        status = state.get("status", "unknown")
        tasks = state.get("tasks", {})
        
        if not tasks:
            return f"Loop {state.get('loop_id', 'unknown')} is {status} with no tasks"
        
        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
        
        return f"Loop {state.get('loop_id', 'unknown')}: {status}, {completed}/{total} tasks completed"
    
    async def update_progress(self, loop_id: str, task_id: str, 
                            status: str, result: Dict = None):
        """Update task progress within a loop"""
        await self.storage.update_task_status(
            loop_id, task_id, status, result
        )
    
    async def get_pending_tasks(self, loop_id: str) -> List[Dict]:
        """Get tasks that need to be processed"""
        return await self.storage.get_tasks_by_status(
            loop_id, TaskStatus.PENDING.value
        )
    
    async def get_completed_tasks(self, loop_id: str) -> List[Dict]:
        """Get completed tasks"""
        return await self.storage.get_tasks_by_status(
            loop_id, TaskStatus.COMPLETED.value
        )
    
    async def save_automation_state(self, automation):
        """Save automation state"""
        await self.storage.save_automation(automation)
    
    async def load_automation_state(self, automation_id: str) -> Dict:
        """Load automation state"""
        return await self.storage.load_automation(automation_id)

class SQLiteStorage:
    def __init__(self, connection_string: str = None):
        self.db_path = connection_string or "loop_state.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Loop states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loop_states (
                loop_id TEXT PRIMARY KEY,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                metadata TEXT,
                error TEXT
            )
        ''')
        
        # Task states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT,
                loop_id TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                PRIMARY KEY (task_id, loop_id),
                FOREIGN KEY (loop_id) REFERENCES loop_states(loop_id)
            )
        ''')
        
        # Automation states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_states (
                automation_id TEXT PRIMARY KEY,
                loop_id TEXT,
                enabled BOOLEAN,
                last_executed TIMESTAMP,
                execution_count INTEGER,
                next_scheduled TIMESTAMP,
                trigger_config TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def save_loop_state(self, loop_id: str, state: Dict):
        """Save loop state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO loop_states 
            (loop_id, status, created_at, updated_at, metadata, error)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            loop_id,
            state.get("status", "idle"),
            state.get("created_at", datetime.now().isoformat()),
            datetime.now().isoformat(),
            json.dumps(state.get("metadata", {})),
            state.get("error")
        ))
        
        conn.commit()
        conn.close()
    
    async def load_loop_state(self, loop_id: str) -> Dict:
        """Load loop state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM loop_states WHERE loop_id = ?', 
            (loop_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {}
        
        return {
            "loop_id": row[0],
            "status": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "metadata": json.loads(row[4]) if row[4] else {},
            "error": row[5]
        }
    
    async def update_task_status(self, loop_id: str, task_id: str,
                               status: str, result: Dict = None):
        """Update task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_states 
            (task_id, loop_id, status, created_at, updated_at, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            loop_id,
            status,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(result) if result else None,
            None
        ))
        
        conn.commit()
        conn.close()
    
    async def get_tasks_by_status(self, loop_id: str, status: str) -> List[Dict]:
        """Get tasks by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM task_states WHERE loop_id = ? AND status = ?',
            (loop_id, status)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "task_id": row[0],
                "loop_id": row[1],
                "status": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "result": json.loads(row[5]) if row[5] else None,
                "error": row[6]
            }
            for row in rows
        ]

class JSONStorage:
    """Simple JSON file storage for development/testing"""
    
    def __init__(self, base_path: str = "./state"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def save_loop_state(self, loop_id: str, state: Dict):
        """Save loop state to JSON file"""
        file_path = os.path.join(self.base_path, f"loop_{loop_id}.json")
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    async def load_loop_state(self, loop_id: str) -> Dict:
        """Load loop state from JSON file"""
        file_path = os.path.join(self.base_path, f"loop_{loop_id}.json")
        if not os.path.exists(file_path):
            return {}
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def update_task_status(self, loop_id: str, task_id: str,
                               status: str, result: Dict = None):
        """Update task status in JSON"""
        # Load current state
        state = await self.load_loop_state(loop_id)
        
        # Initialize tasks if not present
        if "tasks" not in state:
            state["tasks"] = {}
        
        # Update task
        state["tasks"][task_id] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "result": result
        }
        
        # Save updated state
        await self.save_loop_state(loop_id, state)

class RedisStorage:
    """Redis storage for high-performance caching"""
    
    def __init__(self, connection_string: str = "redis://localhost:6379"):
        import redis.asyncio as redis
        self.redis = redis.from_url(connection_string)
    
    async def save_loop_state(self, loop_id: str, state: Dict):
        """Save loop state to Redis"""
        key = f"loop:{loop_id}:state"
        await self.redis.set(key, json.dumps(state, default=str))
    
    async def load_loop_state(self, loop_id: str) -> Dict:
        """Load loop state from Redis"""
        key = f"loop:{loop_id}:state"
        data = await self.redis.get(key)
        if not data:
            return {}
        return json.loads(data)
    
    async def update_task_status(self, loop_id: str, task_id: str,
                               status: str, result: Dict = None):
        """Update task status in Redis"""
        key = f"loop:{loop_id}:task:{task_id}"
        task_data = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "result": result
        }
        await self.redis.set(key, json.dumps(task_data, default=str))
```

## Implementation Notes

1. **Atomic Operations**: Use database transactions for consistency
2. **TTL Support**: Add time-to-live for temporary state data
3. **Compression**: Compress large state objects for storage efficiency
4. **Backup**: Implement regular backups for production use
5. **Migration**: Provide schema migration tools for database updates

## Example Usage

```python
# Initialize memory layer
memory = MemoryLayer(
    storage_backend="sqlite",
    connection_string="loop_state.db"
)

# Save loop state
await memory.save_state("daily-bug-fixes", {
    "status": "running",
    "created_at": "2024-01-01T09:00:00",
    "metadata": {"trigger": "cron", "schedule": "0 9 * * *"}
})

# Update task progress
await memory.update_progress(
    "daily-bug-fixes",
    "task-123",
    "completed",
    {"files_changed": 3, "tests_passed": True}
)

# Get pending tasks
pending = await memory.get_pending_tasks("daily-bug-fixes")
print(f"Pending tasks: {len(pending)}")
```
