---
description: flaky test triage failing intermittent CI test pytest
---

Flaky tests in this repo almost always come from two places: a
`time.sleep`-based race in `tests/auth/` or an unseeded `random`
call in `tests/data/`. When triaging a flaky test failure:

- Check if the failing test imports `random` without a fixed seed.
- Check if the failing test or its fixtures use `time.sleep` instead
  of a polling/`wait_for` helper.
- Prefer fixing the root cause (seed, wait condition) over adding
  `@pytest.mark.flaky` or increasing retries.
- Always re-run the suite 3x locally before calling it fixed.
