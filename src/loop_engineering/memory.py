"""MemoryLayer for persisting loop state."""

import json
import sqlite3
from dataclasses import dataclass


@dataclass
class LoopState:
    """State of a loop execution."""

    loop_id: str
    status: str
    task: str
    attempts: int = 0
    result: dict | None = None
    error: str | None = None


class MemoryLayer:
    """SQLite-backed memory for loop state."""

    def __init__(self, db_path: str = "loop_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS loop_states (
                loop_id TEXT PRIMARY KEY,
                status TEXT,
                task TEXT,
                attempts INTEGER,
                result TEXT,
                error TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def save(self, state: LoopState):
        """Save loop state."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO loop_states
            (loop_id, status, task, attempts, result, error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                state.loop_id,
                state.status,
                state.task,
                state.attempts,
                json.dumps(state.result) if state.result else None,
                state.error,
            ),
        )
        conn.commit()
        conn.close()

    def load(self, loop_id: str) -> LoopState | None:
        """Load loop state by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM loop_states WHERE loop_id = ?", (loop_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return LoopState(
            loop_id=row[0],
            status=row[1],
            task=row[2],
            attempts=row[3],
            result=json.loads(row[4]) if row[4] else None,
            error=row[5],
        )

    def update_status(self, loop_id: str, status: str):
        """Update loop status."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE loop_states SET status = ? WHERE loop_id = ?",
            (status, loop_id),
        )
        conn.commit()
        conn.close()

    def list_loops(self) -> list[LoopState]:
        """List all loops."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM loop_states")
        rows = cursor.fetchall()
        conn.close()

        return [
            LoopState(
                loop_id=row[0],
                status=row[1],
                task=row[2],
                attempts=row[3],
                result=json.loads(row[4]) if row[4] else None,
                error=row[5],
            )
            for row in rows
        ]
