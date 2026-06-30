"""Tests for Memory class (JSON-backed, thread-safe)."""

import json
import threading

from loop_engineering.memory import Memory


class TestMemory:
    def test_creates_file_on_init(self, tmp_path):
        path = tmp_path / "test.json"
        Memory(str(path))
        assert path.exists()
        data = json.loads(path.read_text())
        assert "findings" in data
        assert "log" in data

    def test_add_finding(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))
        finding_id = mem.add_finding({"title": "flaky test"})
        assert finding_id.startswith("f-")

        findings = mem.all_findings()
        assert len(findings) == 1
        assert findings[0]["title"] == "flaky test"
        assert findings[0]["status"] == "open"

    def test_update_finding(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))
        finding_id = mem.add_finding({"title": "test"})
        mem.update_finding(finding_id, status="shipped")

        finding = mem.all_findings()[0]
        assert finding["status"] == "shipped"
        assert "updated_at" in finding

    def test_open_findings(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))
        mem.add_finding({"title": "open1"})
        finding_id = mem.add_finding({"title": "open2"})
        mem.add_finding({"title": "closed"})
        mem.update_finding(finding_id, status="shipped")

        open_findings = mem.open_findings()
        assert len(open_findings) == 2
        assert all(f["status"] == "open" for f in open_findings)

    def test_log(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))
        mem.log("test message")

        data = json.loads((tmp_path / "test.json").read_text())
        assert len(data["log"]) == 1
        assert data["log"][0]["message"] == "test message"
        assert "ts" in data["log"][0]

    def test_concurrent_adds(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))

        def add_findings():
            for i in range(5):
                mem.add_finding({"title": f"test-{i}"})

        threads = [threading.Thread(target=add_findings) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        findings = mem.all_findings()
        assert len(findings) == 15
