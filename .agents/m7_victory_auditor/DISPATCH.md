# Task Assignment: m7_victory_auditor

## Objective
Execute the project-wide Forensic Victory Audit for the RPG-battle Godot Engine 4 migration.
Independently audit all milestones (M1 Foundation, M2 Grid/CombatJudge, M3 24 Castes, M4 Deck/Economy, M5 UI/HUD, M6 WebSocketClient, Entidades Character Scene) for genuine implementation, absence of facades/hardcoding, zero tautological assertions, 100% test pass rate, and strictly zero ObjectDB memory leaks.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/orchestrator_3/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m6_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md

## Forensic Victory Audit Checklist
1. **Authenticity Audit**:
   - Verify that all game logic across all modules (Autoloads, FortressBoard, CercoCombatJudge, IsectumCastes, CercoDeck, WorkshopEconomy, CercoSyncRound, HUD/CardUI, WebSocketClient, Character entity) executes genuine calculations, state machines, and data transformations.
   - Confirm zero hardcoded test bypasses, zero dummy facades, and zero simulated test outputs.
2. **Assertion Integrity Audit**:
   - Confirm zero tautological assertions (e.g. `assert_true(true)`, `assert_eq(1, 1)`) and zero empty test functions across all test files in `godot_project/test/unit/`.
3. **Execution & Leak Audit**:
   - Run `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`.
   - Run `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --verbose --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit`.
   - Verify 100% test pass and strictly 0 ObjectDB memory leaks upon exit.
4. Issue the formal Victory Audit certification: `CLEAN` (Certified 100% Complete) or `INTEGRITY_VIOLATION`.

## Output Requirements
- Write your forensic victory audit report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor/victory_audit_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T06:32:36Z
You are m7_victory_auditor. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/orchestrator_3/handoff.md

Execute the project-wide Forensic Victory Audit:
1. Verify NO hardcoded test results, facade implementations, or dummy bypasses across the entire codebase.
2. Verify NO tautological assertions or empty test bodies across all 17 test files in test/unit/.
3. Execute run_gut_tests.sh and verbose leak check. Confirm 100% pass and strictly 0 ObjectDB memory leaks.
Issue the formal Victory Audit certification: CLEAN (Certified 100% Complete) or INTEGRITY_VIOLATION.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor/victory_audit_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/m7_victory_auditor/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your verdict and handoff path.
