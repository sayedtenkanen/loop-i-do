"""Tests for Automation."""

from loop_engineering.automation import Automation, make_skill_triage
from loop_engineering.memory import Memory
from loop_engineering.skills import SkillRegistry


class TestAutomation:
    def test_run_once_finds_issues(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))

        def triage_fn():
            return [{"title": "flaky test"}, {"title": "lint error"}]

        auto = Automation("test-auto", triage_fn, mem)
        ids = auto.run_once()

        assert len(ids) == 2
        assert len(mem.open_findings()) == 2

    def test_run_once_empty_archives(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))

        def triage_fn():
            return []

        auto = Automation("test-auto", triage_fn, mem)
        ids = auto.run_once()

        assert len(ids) == 0
        assert len(mem.open_findings()) == 0

    def test_run_once_logs(self, tmp_path):
        mem = Memory(str(tmp_path / "test.json"))

        def triage_fn():
            return [{"title": "issue"}]

        auto = Automation("test-auto", triage_fn, mem)
        auto.run_once()

        log = mem._read()["log"]
        assert len(log) == 1
        assert "1 finding(s)" in log[0]["message"]


class TestMakeSkillTriage:
    def test_creates_triage_fn(self, tmp_path):
        skills_dir = tmp_path / "skills" / "flaky"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "---\ndescription: flaky test\n---\n\n- Fix test_login.py\n- Fix test_auth.py"
        )
        skills = SkillRegistry(str(tmp_path / "skills"))

        def agent_run(instructions):
            return "- Fix test_login.py\n- Fix test_auth.py"

        triage_fn = make_skill_triage(skills, "flaky", agent_run)
        findings = triage_fn()

        assert len(findings) == 2
        assert findings[0]["title"] == "Fix test_login.py"

    def test_returns_empty_if_no_skill(self, tmp_path):
        skills = SkillRegistry(str(tmp_path / "nonexistent"))
        triage_fn = make_skill_triage(skills, "nonexistent", lambda x: "")
        findings = triage_fn()
        assert findings == []
