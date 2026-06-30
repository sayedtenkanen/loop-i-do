"""Verifier class for loop engineering."""

from dataclasses import dataclass, field


@dataclass
class VerificationResult:
    """Result of a verification check."""

    passed: bool
    score: float
    issues: list[str] = field(default_factory=list)


class Verifier:
    """Verifies code changes against criteria."""

    def verify(self, code: str, criteria: dict | None = None) -> VerificationResult:
        """Verify code against criteria.

        Args:
            code: The code to verify.
            criteria: Verification criteria (e.g., {"tests_pass": True}).

        Returns:
            VerificationResult with pass/fail status and details.
        """
        criteria = criteria or {}
        issues = []

        # Basic verification logic
        # TODO: Replace with actual test/lint execution in Phase 3
        if not code or len(code.strip()) == 0:
            return VerificationResult(passed=False, score=0.0, issues=["Empty code"])

        # Check for obvious issues
        if "return a - b" in code and "add" in code.lower():
            issues.append("Suspicious implementation: subtraction in add function")

        # Calculate score based on criteria
        score = 1.0
        if criteria.get("tests_pass") and issues:
            score -= 0.5 * len(issues)
        if criteria.get("lint_clean") and issues:
            score -= 0.3 * len(issues)

        passed = score >= 0.8 and len(issues) == 0

        return VerificationResult(
            passed=passed,
            score=max(0.0, score),
            issues=issues,
        )
