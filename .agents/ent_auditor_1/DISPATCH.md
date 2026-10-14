# Task Assignment: ent_auditor_1

## Objective
Perform forensic integrity auditing on the Entities Scene work products (`godot_project/scenes/entities/Character.tscn`, `godot_project/scripts/entities/Character.gd`, and `godot_project/test/unit/test_character_scene.gd`).

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

## Forensic Integrity Checks (NON-NEGOTIABLE)
1. **No Hardcoded Test Bypasses / Facades**:
   - Inspect `Character.gd` and `Character.tscn` to ensure all methods execute real logic, genuine state transitions, real texture searches, and real drawing updates.
   - Verify that there are no conditional branches checking if the environment is a test to return dummy successes.
2. **No Tautological or Empty Assertions**:
   - Inspect `test_character_scene.gd` line-by-line for any `assert_true(true)`, `assert_not_null(1)`, empty test bodies, or bypassed assertions.
   - Every assertion must test genuine side-effects, signal emissions, or state mutations.
3. **Execution Validation & Zero Leak Verification**:
   - Run the test suite directly:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_character_scene.gd`
   - Run full project suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Run verbose leak check:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --verbose --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit`
   - Check stderr/stdout for memory leaks, orphaned nodes, or ObjectDB warnings upon exit.
4. Issue a definitive verdict: `CLEAN` or `INTEGRITY_VIOLATION`.

## Output Requirements
- Write your forensic audit report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1/audit_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T06:16:25Z
<USER_REQUEST>
You are ent_auditor_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

Perform forensic integrity checks:
1. Verify NO hardcoded test results, facade implementations, or dummy bypasses.
2. Verify NO tautological assertions (e.g. assert_true(true)) or empty test bodies.
3. Run GUT test commands (isolated and full suite), check stdout/stderr, and verify strictly 0 ObjectDB memory leaks under verbose headless execution.
Issue a definitive verdict: CLEAN or INTEGRITY_VIOLATION.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1/audit_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_auditor_1/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your verdict and handoff path.
</USER_REQUEST>
