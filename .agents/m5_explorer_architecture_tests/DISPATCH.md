## 2026-10-01T01:25:39Z

You are the Architecture & Testing Explorer for Milestone 5 (HUD, Audio Integration & GUT Test Design) of RPG-battle.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_architecture_tests

MANDATORY FIRST STEP:
Read these files before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Authoritative request)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master architecture & contracts)
- /home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md (Test spec)
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoload/AudioManager.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoload/EventBus.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/CercoSyncRound.gd

Your Mission:
Design the overall Milestone 5 HUD architecture, Audio integration, and comprehensive GUT test strategy:
1. Overall HUD Architecture (`godot_project/scenes/ui/HUD.tscn` & `godot_project/scripts/ui/HUD.gd`):
   - Integration of Fan Cards, Board View, Resource Scoreboard, and Combat Log (RichTextLabel with BBCode).
   - EventBus wiring: connecting to `card_played`, `dice_rolled`, `damage_dealt`, `production_completed`, `synergy_triggered`, `supreme_synchrony_triggered`, `round_resolved`.
2. Audio Integration:
   - Safe audio trigger mappings through `AudioManager.gd` (card draw/play sfx, dice roll sfx, wall breach warning sfx, victory/defeat jingles).
   - Headless audio safety: ensure zero leaks and no dependency on active audio hardware in `--headless` CI/CLI mode.
3. Test Suite Design (`godot_project/test/unit/test_cerco_hud.gd`):
   - Enumerate all test cases for:
     * Card fan math (angles, positions, hover lift, card count changes).
     * Resource scoreboard updates and signal responsiveness.
     * Zone overlay highlighting and breach state changes.
     * Combat log appending and BBCode formatting.
     * Signal emissions and user input event handling.
     * Teardown & memory safety: 0 ObjectDB leaks when freeing HUD nodes in tests.
   - Strict AAA pattern with `# Arrange`, `# Act`, `# Assert`.

Deliverables:
- Write your comprehensive findings to /home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_architecture_tests/handoff.md.
- Send a completion message to parent.
