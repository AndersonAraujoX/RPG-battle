# Task Assignment: m7_qa_worker

## Objective
Execute Milestone 7: Final Automated GUT Suite Pass & Hardening.
Verify that 100% of all GUT test suites pass and verify strictly 0 ObjectDB memory leaks across the entire Godot Engine 4 project.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/orchestrator_3/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh

## Tasks to Execute
1. Run the master test runner script:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./run_gut_tests.sh
   ```
   Record the exact output: number of test scripts executed, total tests run, tests passed, assertions passed, and exit code.

2. Run the verbose headless memory leak check:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./bin/godot --headless --verbose --path . -s addons/gut/gut_cmdln.gd -gexit
   ```
   Inspect the entire output (including stderr and engine teardown logs) to verify that there are strictly 0 `Leaked X ObjectDB instances at exit` or `Resources still in use at exit` warnings.

3. Compile a comprehensive QA summary table of all test suites across the project (M1 Foundation, M2 Grid/CombatJudge, M3 24 Castes, M4 Deck/Economy, M5 UI/HUD, M6 WebSocketClient, Entidades Character Scene, and Stress/Adversarial suites).

## Output Requirements
- Write your comprehensive QA report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m7_qa_worker/qa_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m7_qa_worker/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T06:32:36Z
Execute:
1. cd /home/anderson/Documents/projeto/RPG-battle/godot_project && ./run_gut_tests.sh
2. cd /home/anderson/Documents/projeto/RPG-battle/godot_project && ./bin/godot --headless --verbose --path . -s addons/gut/gut_cmdln.gd -gexit

Verify that 100% of all tests pass and that strictly 0 ObjectDB memory leaks occur upon exit. Compile a complete QA report of all 17 test suites.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/m7_qa_worker/qa_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/m7_qa_worker/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) when done.
