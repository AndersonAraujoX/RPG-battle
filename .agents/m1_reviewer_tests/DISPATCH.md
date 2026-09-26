# Task Assignment: M1 Tests Reviewer

## Objective
Review Milestone 1 unit tests and GUT framework setup for strict adherence to user guidelines:
1. Strict Arrange-Act-Assert (AAA) pattern.
2. Complete coverage: happy path, edge cases (empty strings, boundaries, nulls), error handling/fallbacks (corrupt JSON, missing file, dummy audio).
3. Test isolation, no cross-test pollution, proper cleanup (`autofree()` / `queue_free()`).
4. Execute `./godot_project/run_gut_tests.sh` and verify all tests pass with exit code 0.

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests`

## Target Files to Review
- `godot_project/test/unit/test_autoloads.gd`
- `godot_project/.gutconfig.json`
- `godot_project/addons/gut/`
- `godot_project/run_gut_tests.sh`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/report.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/handoff.md`

## Deliverables
- Review report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/analysis.md`.
- Handoff report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/handoff.md`.
- Explicit verdict in handoff: `APPROVE` or `REQUEST_CHANGES`.
- Send message to orchestrator with summary and verdict.

## 2026-09-26T13:03:25Z
You are m1_reviewer_tests.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read PROJECT.md, TEST_INFRA.md, and your assignment in /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/DISPATCH.md.

Review the unit test suite in godot_project/test/unit/test_autoloads.gd and GUT setup for strict compliance with Arrange-Act-Assert (AAA) pattern, coverage of happy paths, edge cases, error handling, and test isolation. Execute ./godot_project/run_gut_tests.sh.
Write your analysis to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/analysis.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/handoff.md. Include your explicit verdict: APPROVE or REQUEST_CHANGES.
When finished, send a message to orchestrator with summary and verdict.

