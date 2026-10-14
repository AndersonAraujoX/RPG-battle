## 2026-10-01T01:31:34Z
You are the Implementation Worker for Milestone 5 (UI/UX do Cerco, Tabuleiro da Fortaleza & Áudio) of the RPG-battle Godot Engine 4 migration.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m5_worker_hud_ui_audio

MANDATORY FIRST STEP:
Read these files before writing any code:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Authoritative request)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master architecture & contracts)
- /home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md (Test spec)
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md (Code quality, AAA tests, clean architecture)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m5_spec_miner_cards_ui/handoff.md (Fan card math, dimensions & interaction specs)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_map_zones/handoff.md (17 zones visual overlay, breach indicators & scoreboard)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_architecture_tests/handoff.md (HUD architecture, audio mapping & GUT test design)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- godot_project/scripts/ui/CardFanLayoutCalculator.gd
- godot_project/scripts/ui/CardUI.gd
- godot_project/scripts/ui/CardFanContainer.gd
- godot_project/scripts/ui/ResourceScoreboard.gd
- godot_project/scripts/ui/ZoneOverlay.gd
- godot_project/scripts/ui/FortressBoardView.gd
- godot_project/scripts/ui/CombatLog.gd
- godot_project/scripts/ui/HUD.gd
- godot_project/scenes/ui/HUD.tscn
- godot_project/scripts/autoload/EventBus.gd
- godot_project/test/unit/test_cerco_hud.gd

Objectives:
1. Update `EventBus.gd`:
   - Add Cerco HUD signals:
     * `signal card_played(player_id: String, card_id: String, target_zone: String)`
     * `signal dice_rolled(source_id: String, dice_type: String, results: Array)`
     * `signal damage_dealt(target_id: String, amount: int, current_hp: int)`
     * `signal production_completed(workshop_zone: String, resource_type: String, amount: int)`
     * `signal supreme_synchrony_triggered(crystals_awarded: int)`
     * `signal wall_breached(wall_id: String)`
   - Retain all existing signals and telemetry without regressions.

2. Implement `CardFanLayoutCalculator.gd`:
   - Pure `RefCounted` with 0 UI dependencies, 100% headless testable.
   - Calculates card positions, rotations (clamped to max ±12° or similar smooth parabolic/circular arc), and z-indices for any hand size N.
   - Hover lift (-30px, 0° upright) and selection lift (-45px) calculation methods.

3. Implement `CardUI.gd`:
   - `Control` representing a single card.
   - Binds to `CardData`. Displays name, badge (Marcha, Trabalho, Escavação, Combate, Especial), cost tags (Wood, Leather, Metal, Crystal, AP), description.
   - Procedural/StyleBox drawing with fallback if textures are missing.
   - Signals: `card_selected`, `card_deselected`, `card_played_requested(card_data, target_zone)`, `card_hovered`, `card_unhovered`.

4. Implement `CardFanContainer.gd`:
   - `Control` holding multiple `CardUI` instances.
   - Uses `CardFanLayoutCalculator` to layout children in fan arc.
   - Handles hand updates (cards drawn, played, discarded).

5. Implement `ResourceScoreboard.gd`:
   - `Control` showing Madeira, Couro, Metal, Cristais, AP, current round, current layer.
   - Reactive: connects to `WorkshopEconomy.resources_updated` and `EventBus.resources_updated`.
   - Methods: `update_resources(wood, leather, metal, crystal, ap)`, `set_round(round_num)`, `set_layer(layer_name)`.

6. Implement `ZoneOverlay.gd` & `FortressBoardView.gd`:
   - Visualizes the 17 canonical zones on the 20x20 grid.
   - Delineates elevations (0, 1, 2) and coordinates.
   - Reacts to wall damage and breaches (draws breach warning, changes color/style).
   - Zone highlighting: supports highlighting zones for movement, production, repair, and balestra targeting.

7. Implement `CombatLog.gd`:
   - `RichTextLabel` with BBCode support.
   - Listens to `EventBus.combat_log_entry_added`, `damage_dealt`, `dice_rolled`, `wall_breached`, `synergy_triggered`, `supreme_synchrony_triggered`.
   - Methods: `log_message(bbcode_text)`, `clear_log()`, `get_entries() -> Array[String]`.

8. Implement `HUD.gd` & `HUD.tscn`:
   - `CanvasLayer` root coordinating `ResourceScoreboard`, `FortressBoardView`, `CombatLog`, and `CardFanContainer`.
   - Dual-wiring: automatically connects to `/root/EventBus` and provides dependency injection methods (`bind_board(board)`, `bind_economy(economy)`, `bind_deck(deck)`, `bind_judge(judge)`) for hermetic testing.
   - Plays sound effects via `AudioManager.play_sfx()` / `EventBus.audio_play_sfx_requested` for card hover/play, dice roll, wall breach alarm, synergy bonus, victory/defeat.

9. Implement `test_cerco_hud.gd`:
   - Strict Arrange-Act-Assert (AAA) pattern for all tests.
   - Comprehensive test suite covering:
     * CardFanLayoutCalculator: 1 card, 5 cards, 10 cards, empty hand, hover lift, selection lift.
     * CardUI: data binding, cost checks, signal emissions.
     * ResourceScoreboard: reactive resource updates, layer changes, round changes.
     * FortressBoardView & ZoneOverlay: 17 zones rendering logic, elevation mapping, wall breach state, zone highlight toggling.
     * CombatLog: BBCode message formatting, event subscription.
     * HUD Integration: dependency injection, EventBus wiring, audio requests.
     * Teardown & memory safety: verify 0 ObjectDB leaks when creating and freeing HUD nodes.
   - ZERO tautological assertions (`assert_true(true)` is strictly prohibited).

10. Verification:
    - Run `./godot_project/run_gut_tests.sh` to confirm 100% tests pass across the entire project (all existing 339 tests + new M5 tests).
    - Run `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` to confirm 0 ObjectDB leaks at exit.
    - Write handoff.md in your working directory (.agents/m5_worker_hud_ui_audio/handoff.md) and notify parent.
