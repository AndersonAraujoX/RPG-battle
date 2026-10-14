# Task Assignment: ent_challenger_1

## Objective
Empirically stress-test and challenge `godot_project/scenes/entities/Character.tscn` and `godot_project/scripts/entities/Character.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

## Challenger Mission
1. Empirical Stress Testing:
   - Rapid instantiation and freeing of 50-100 `Character` nodes.
   - Rapid damage/heal/status churn (e.g. 50 alternating damage/heal/status cycles on single entity).
   - Boundary inputs: massive damage numbers (`99999`), negative healing, null strings, weird characters.
   - Verify that no lingering tweens, status badges, or signal connections cause crashes or ObjectDB leaks.
2. Execute the verification commands:
   - Run isolated Character test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_character_scene.gd`
   - Run the full suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Verify 0 ObjectDB leaks under `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit`.
3. Issue a definitive verdict: `APPROVE` or `REQUEST_CHANGES`.

## Output Requirements
- Write your challenger report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1/challenger_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`) with your explicit verdict.

## 2026-10-01T06:16:25Z
You are ent_challenger_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scenes/entities/Character.tscn
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/entities/Character.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_character_scene.gd

Stress-test Character scene: rapid instantiate/free cycles (100+ entities), rapid damage/heal interleaving, burst status additions, and verify 0 ObjectDB leaks under verbose mode. Issue a definitive verdict: APPROVE or REQUEST_CHANGES.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1/challenger_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_challenger_1/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your verdict and handoff path.

