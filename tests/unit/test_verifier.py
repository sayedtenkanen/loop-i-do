"""Tests for Verifier class - RED phase (failing tests)."""

from loop_engineering.verifier import VerificationResult, Verifier


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_passed_result(self):
        result = VerificationResult(passed=True, score=1.0, issues=[])
        assert result.passed is True
        assert result.score == 1.0
        assert result.issues == []

    def test_failed_result(self):
        result = VerificationResult(passed=False, score=0.3, issues=["Tests failed", "Lint errors"])
        assert result.passed is False
        assert result.score == 0.3
        assert len(result.issues) == 2


class TestVerifier:
    """Tests for Verifier class."""

    def test_verifier_creation(self):
        verifier = Verifier()
        assert verifier is not None

    def test_verify_returns_result(self):
        verifier = Verifier()
        result = verifier.verify("code change", criteria={"tests_pass": True})
        assert isinstance(result, VerificationResult)

    def test_verify_with_passing_code(self):
        verifier = Verifier()
        result = verifier.verify(
            "def add(a, b): return a + b",
            criteria={"tests_pass": True, "lint_clean": True},
        )
        assert result.passed is True
        assert result.score > 0.8

    def test_verify_with_failing_code(self):
        verifier = Verifier()
        result = verifier.verify(
            "def add(a, b): return a - b",  # Wrong implementation
            criteria={"tests_pass": True},
        )
        assert result.passed is False
        assert len(result.issues) > 0
