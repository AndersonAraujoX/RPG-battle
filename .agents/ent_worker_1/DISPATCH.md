# Task Assignment: ent_worker_1

## Objective
Implement `godot_project/scenes/entities/Character.tscn`, `godot_project/scripts/entities/Character.gd`, and the comprehensive unit test suite in `godot_project/test/unit/test_character_scene.gd`.

## Exclusive Write Ownership
You own and may ONLY create/modify:
- `godot_project/scenes/entities/Character.tscn`
- `godot_project/scripts/entities/Character.gd`
- `godot_project/test/unit/test_character_scene.gd`
Do NOT modify files owned by other modules.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/exploration_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/test_strategy_report.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/handoff.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/autoload/EventBus.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/resources/CharacterData.gd

## Implementation Requirements

1. `godot_project/scenes/entities/Character.tscn`:
   - Root: `CharacterBody2D` (or `Node2D`) with script `res://scripts/entities/Character.gd`.
   - Child `CollisionShape2D` with `CircleShape2D` (radius ~14.0).
   - Child `Sprite2D`: centered sprite for character appearance.
   - Child `SelectionHighlight`: `Line2D` or modulated highlight element, hidden by default.
   - Child `RetroHPBar`: `Node2D` with background rect (30x4 px, dark grey #1e1e1e), black 1px border, foreground fill rect (green > 50%, yellow 25-50%, red <= 25%), positioned above sprite.
   - Child `StatusContainer`: `HBoxContainer` or `Node2D` displaying active status effect badges/icons.

2. `godot_project/scripts/entities/Character.gd`:
   - `class_name Character extends CharacterBody2D` (or `Node2D`).
   - Statically typed GDScript with `@export` and clear variables:
     * `character_id: String`
     * `character_name: String`
     * `current_hp: int`, `max_hp: int`
     * `is_selected: bool`
     * `active_statuses: Array[String]`
   - Public methods:
     * `initialize_from_data(data: CharacterData or Dictionary)`
     * `setup(id: String, name: String, max_hp: int, texture_path: String = "")`
     * `take_damage(amount: int) -> int` (clamps HP >= 0, updates HP bar, emits damaged/died)
     * `heal(amount: int) -> int` (clamps HP <= max_hp, updates HP bar, emits healed)
     * `set_selected(selected: bool)` (toggles highlight visibility, emits selection_changed)
     * `add_status_effect(effect: String) -> bool` (prevents duplicates, adds badge, emits status_effect_applied)
     * `remove_status_effect(effect: String) -> bool` (removes badge, emits status_effect_removed)
     * `has_status_effect(effect: String) -> bool`
     * `load_texture_for_character(char_id: String) -> Texture2D` (supports paths in `assets/images/characters/`, with safe fallback)
   - Signals: `hp_changed(current, max)`, `damaged(amount)`, `healed(amount)`, `died()`, `selection_changed(is_selected)`, `status_effect_applied(effect)`, `status_effect_removed(effect)`.
   - Headless safety: clean tree cleanup, bound tweens, 0 leaks.

3. `godot_project/test/unit/test_character_scene.gd`:
   - Extends `GutTest`.
   - Uses `autofree()` / `add_child_autofree()` on character instances.
   - Implements tests matching the specifications from `ent_explorer_2/test_strategy_report.md`:
     * Scene loading and node hierarchy integrity.
     * Sprite loading with valid vs fallback paths.
     * Damage calculation (normal and overkill clamping).
     * Healing calculation (normal and overhealing cap).
     * Retro HP bar color threshold transitions (green > 50%, yellow 25-50%, red <= 25%).
     * Selection highlight toggles.
     * Status effect lifecycle (add, query, remove, duplicate guard, non-existent removal).
     * Death sequence and signal emissions.
     * Zero-leak verification on tree exit.

4. Testing & Verification:
   - Run the isolated character test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_character_scene.gd`
   - Run the full project test suite:
     `/home/anderson/Documents/projeto/RPG-battle/godot_project/run_gut_tests.sh`
   - Confirm 100% pass across all test suites and 0 ObjectDB memory leaks.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Output Requirements
- Write your implementation and tests.
- Run tests and confirm results.
- Write your completion handoff report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T06:10:18Z
Invoking request received from parent/user:
- Implement Character.tscn, Character.gd, and test_character_scene.gd.
- Run GUT tests in headless mode, confirm 100% pass and 0 leaks.
- Write handoff to /home/anderson/Documents/projeto/RPG-battle/.agents/ent_worker_1/handoff.md.
- Send message back to parent.
