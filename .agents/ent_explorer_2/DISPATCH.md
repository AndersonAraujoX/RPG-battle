# Task Assignment: ent_explorer_2

## Objective
Investigate GUT testing patterns for 2D Node/Scene testing (`Character.tscn`), headless lifecycle management, 0-leak tree management, and formulate concrete AAA test case specifications for `godot_project/test/unit/test_character_scene.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_card_ui.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_zone_overlay.gd

## Detailed Scope
1. Inspect 2D Scene Testing in GUT:
   - Check how other scene tests in `godot_project/test/unit/` (e.g. `test_card_ui.gd`, `test_zone_overlay.gd`, `test_hud.gd`) instantiate packed scenes using `autofree()` / `add_child_autofree()`.
   - Ensure clean teardown so no nodes remain orphaned in ObjectDB.
2. Formulate Comprehensive AAA Test Cases:
   - Happy paths:
     * Character instantiation from `Character.tscn` with valid default values.
     * Texture assignment and sprite bounds.
     * Damage calculation and retro HP bar update.
     * Healing calculation (capping at max_hp).
     * Selection highlight toggling (visibility and modulation).
     * Status effect icon addition, querying, and removal.
     * Death sequence and signal emission when HP reaches 0.
   - Edge cases:
     * Overkill damage (HP <= 0, clamping to 0).
     * Overhealing (HP cannot exceed max_hp).
     * Duplicate status effects.
     * Removing non-existent status effect.
     * Zero max HP or negative values handling.
     * Missing or invalid sprite path fallback (no crash, fallback icon or safe default).
3. Zero-Leak Verification:
   - Outline test structure guaranteeing 0 ObjectDB leaks upon test suite exit.

## Output Requirements
- Write your test strategy report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/test_strategy_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T06:03:00Z
You are ent_explorer_2. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_card_ui.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/test/unit/test_zone_overlay.gd

Investigate GUT 2D scene testing patterns, zero-leak node lifecycle (autofree/add_child_autofree), and formulate concrete AAA test case specifications for test_character_scene.gd.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/test_strategy_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your summary and handoff path.
