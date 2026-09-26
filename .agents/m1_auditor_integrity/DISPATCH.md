# Task Assignment: M1 Forensic Integrity Auditor

## Objective
Perform independent forensic integrity audit on Milestone 1 code in `godot_project/`:
1. Static and code-level verification: Ensure no test outcomes are hardcoded, no fake/dummy implementations exist, and no tautological assertions are used.
2. Runtime validation: Verify that `DataManager` genuinely opens and parses `dados/personagens.json`, that `GameManager` genuinely tracks state transitions and enforces validation, that `EventBus` genuinely emits signals across subscribers, and that `AudioManager` genuinely manages players and buses.
3. Verify that `godot_project/run_gut_tests.sh` runs real tests against real implementations.

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity`

## Target Files to Audit
- All files in `godot_project/scripts/`
- All files in `godot_project/test/`
- `godot_project/project.godot`
- `godot_project/run_gut_tests.sh`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/report.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/handoff.md`

## Deliverables
- Audit report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/analysis.md`.
- Handoff report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/handoff.md`.
- Binary verdict in handoff: `CLEAN` or `INTEGRITY VIOLATION`.
- Send message to orchestrator with summary and verdict.

## 2026-09-26T13:03:25Z
You are m1_auditor_integrity.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read PROJECT.md and your assignment in /home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/DISPATCH.md.

Perform a forensic integrity audit on all files in godot_project/. Verify that implementations are genuine, not hardcoded to pass tests, contain no facade/dummy code, and that run_gut_tests.sh executes real tests.
Write your analysis to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/analysis.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_auditor_integrity/handoff.md. Include your binary verdict: CLEAN or INTEGRITY VIOLATION.
When finished, send a message to orchestrator with summary and verdict.

