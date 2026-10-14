# Task Assignment: ent_reviewer_2

## Objective
Conduct an independent adversarial and robustness review of `godot_project/scenes/entities/Character.tscn`, `godot_project/scripts/entities/Character.gd`, and `godot_project/test/unit/test_character_scene.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

## Review Criteria
1. Robustness & Fault Tolerance:
   - Clamping behavior for damage and healing.
   - Guard against reviving dead units via heal without resurrection.
   - Status effect lifecycle: duplicate condition guards, non-existent removal.
   - Missing or corrupted texture fallback safety (no crashes).
2. AAA Conformance & Memory Management:
   - Strict Arrange-Act-Assert in all tests.
   - Correct use of `autofree` / `add_child_autofree`.
   - Node-bound tweens (`bind_node(self)`) and explicit freeing of dynamically added status badges.
3. Test Execution & Verification:
   - Run the isolated test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_character_scene.gd`
   - Run the full project test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Confirm 0 ObjectDB memory leaks and 100% pass rate.
4. Issue a definitive verdict: `APPROVE` or `REQUEST_CHANGES`.

## Output Requirements
- Write your review report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2/review_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T06:16:25Z
You are ent_reviewer_2. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

Review robustness, clamping, status effect lifecycles, memory safety, and AAA test conformance. Run GUT tests. Issue a definitive verdict: APPROVE or REQUEST_CHANGES.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2/review_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_reviewer_2/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your verdict and handoff path.
