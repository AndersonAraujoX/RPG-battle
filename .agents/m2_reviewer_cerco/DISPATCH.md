## 2026-10-01T00:49:43Z

You are the Reviewer for Milestone 2 (Fortress Board & Cerco Combat Judge) of RPG-battle Godot 4.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m2_reviewer_cerco

Read these files first:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m2_worker_fortress_cerco/handoff.md

Your Mission:
Review and verify Milestone 2 implementation:
1. `godot_project/scripts/cerco/FortressBoard.gd`:
   - Verify 17 logical zones correctly partitioned on 20x20 discrete grid (exactly 400 cells total, no overlaps, no unassigned cells).
   - Verify elevation hierarchy: Spawns/Courtyard/Workshops=0, Walls=1, Towers=2.
   - Verify adjacency graph and invasion flow to Camara Central.
   - Verify wall damage, repair, and breach logic.
2. `godot_project/scripts/cerco/CercoCombatJudge.gd`:
   - Verify custom D6 dice mechanics, roll generation, and deterministic forced_rolls.
   - Verify Melee math: 2 impactos = 1 damage, odd impacts discarded, armor deduction.
   - Verify Tower Balestra math: 1 shot = 1 damage, elevation advantage/disadvantage.
   - Verify Brutamontes 3 HP circles, Infiltradores stealth wall scaling, Catapult direct siege damage.
3. Tests & Memory:
   - Run `./godot_project/run_gut_tests.sh` and confirm all 237 tests pass with exit code 0.
   - Run `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` and verify 0 ObjectDB leaks at exit.
4. Deliver your handoff.md in your working directory with an explicit verdict: APPROVE or REQUEST_CHANGES, and notify parent.
