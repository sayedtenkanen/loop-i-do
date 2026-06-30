"""Memory — the loop's spine (article's 6th building block)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class Memory:
    def __init__(self, path: str | Path = "loop_state.json"):
        self.path = Path(path)
        self._lock = threading.Lock()
        if not self.path.exists():
            self._write({"findings": [], "log": []})

    def _read(self) -> dict[str, list[dict[str, str]]]:
        return json.loads(self.path.read_text())

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2, default=str))

    def add_finding(self, finding: dict) -> str:
        with self._lock:
            data = self._read()
            finding = {
                "id": f"f-{len(data['findings']) + 1}",
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat(),
                **finding,
            }
            data["findings"].append(finding)
            self._write(data)
            return finding["id"]

    def update_finding(self, finding_id: str, **updates) -> None:
        with self._lock:
            data = self._read()
            for f in data["findings"]:
                if f["id"] == finding_id:
                    f.update(updates)
                    f["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write(data)

    def open_findings(self) -> list[dict]:
        return [f for f in self._read()["findings"] if f["status"] == "open"]

    def all_findings(self) -> list[dict]:
        return self._read()["findings"]

    def log(self, message: str) -> None:
        with self._lock:
            data = self._read()
            data["log"].append({"ts": datetime.now(timezone.utc).isoformat(), "message": message})
            self._write(data)
