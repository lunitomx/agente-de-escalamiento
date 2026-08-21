# S51.1: Welcome Engine Cleanup

## Problem
GitHub issue #1 reported that `escala-welcome` invoked the core with `company_name` while `coaching/welcome/engine.py` required `name`, blocking onboarding. The main onboarding path (`coaching/welcome/__init__.py::run`) was fixed and now accepts `company_name`, but the orphaned `coaching/welcome/engine.py` still declares `REQUIRED_FIELDS = ["name", ...]` and is never invoked. This dead code confuses maintainers and can resurrect the original defect if someone imports it.

## Root Cause
Two overlapping welcome implementations exist: the original form-based engine (`engine.py`) and the conversational E49 state machine (`conversation.py`). The form-based path lives in `__init__.py::run` and uses `company_name`, while `engine.py` was left behind with the old `name` contract.

## Goal
Eliminate the contract ambiguity. Either remove `engine.py` if it is truly unused, or align it with `__init__.py::run` and cover it with tests.

## Acceptance Criteria
- [ ] `coaching/welcome/engine.py` contract matches `__init__.py::run` (`company_name`) or the file is removed.
- [ ] All imports of welcome use a single canonical entry point.
- [ ] Regression test proves onboarding with `company_name` succeeds.
- [ ] All existing tests pass.

## Tasks
1. Verify every consumer of `coaching.welcome` and `coaching.welcome.engine`.
2. Decide: align `engine.py` or delete it and move logic to `__init__.py`.
3. Implement the decision.
4. Add/update tests.
5. Run gates.

## Related
- GitHub issue #1
