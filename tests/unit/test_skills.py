"""Tests for SkillRegistry."""

from loop_engineering.skills import SkillRegistry


class TestSkillRegistry:
    def test_load_skills_from_dir(self, tmp_path):
        skills_dir = tmp_path / "skills" / "flaky-test"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "---\ndescription: flaky test triage\n---\n\nFix flaky tests by seeding random."
        )

        registry = SkillRegistry(str(tmp_path / "skills"))
        assert len(list(registry)) == 1

    def test_match_by_description(self, tmp_path):
        skills_dir = tmp_path / "skills" / "flaky-test"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "---\ndescription: flaky test triage\n---\n\nFix flaky tests."
        )

        registry = SkillRegistry(str(tmp_path / "skills"))
        skill = registry.match("flaky test triage")
        assert skill is not None
        assert skill.name == "flaky-test"

    def test_no_match_returns_none(self, tmp_path):
        skills_dir = tmp_path / "skills" / "flaky-test"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "---\ndescription: flaky test triage\n---\n\nFix flaky tests."
        )

        registry = SkillRegistry(str(tmp_path / "skills"))
        skill = registry.match("deploy to production")
        assert skill is None

    def test_get_by_name(self, tmp_path):
        skills_dir = tmp_path / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("My skill instructions")

        registry = SkillRegistry(str(tmp_path / "skills"))
        skill = registry.get("my-skill")
        assert skill is not None

    def test_empty_dir(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        registry = SkillRegistry(str(skills_dir))
        assert len(list(registry)) == 0
