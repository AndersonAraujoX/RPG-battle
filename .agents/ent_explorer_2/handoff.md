# Handoff Report: GUT 2D Scene Testing & Character Entity Test Strategy

**Agent**: `ent_explorer_2`  
**To**: `parent` (Orchestrator) / `ent_implementer_1` (Implementer) / `ent_tester_1` (Tester)  
**Date**: 2026-10-01  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

1. **GUT Node Memory Management Primitives (`godot_project/addons/gut/test.gd:88-97`)**:
   Direct observation of `autofree` and `add_child_autofree` in GUT base class:
   ```gdscript
   func autofree(node: Node) -> Node:
       if node != null and not _autofree_nodes.has(node):
           _autofree_nodes.append(node)
           if not node.is_inside_tree() and is_inside_tree():
               add_child(node)
       return node

   func add_child_autofree(node: Node) -> Node:
       add_child(node)
       return autofree(node)
   ```
   And the automatic cleanup mechanism in `_internal_after_each()` (`lines 65-73`):
   ```gdscript
   for node in _autofree_nodes:
       if is_instance_valid(node):
           if node.get_parent() != null:
               node.get_parent().remove_child(node)
           node.free()
   _autofree_nodes.clear()
   ```

2. **Existing 2D Scene Testing Pattern (`godot_project/test/unit/test_cerco_hud.gd:485-487`)**:
   PackedScene instantiation in canonical test suites:
   ```gdscript
   const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
   var hud: HUD = HUD_SCENE.instantiate() as HUD
   add_child_autofree(hud)
   ```
   And rapid instantiation memory verification (`lines 595-606`):
   ```gdscript
   func test_hud_rapid_creation_and_destruction_zero_leaks() -> void:
       for i in range(5):
           var hud: HUD = HUD.new()
           add_child(hud)
           hud.scoreboard.update_resources(1, 2, 3, 4, 5)
           hud.cleanup()
           remove_child(hud)
           hud.free()
       pass_test("5 HUD instances created, exercised, and destroyed without crash or memory fault")
   ```

3. **Autoload & Node Teardown Mechanics (`godot_project/scripts/ui/HUD.gd:285-309`)**:
   `HUD.gd` implements `cleanup()` called automatically from `_exit_tree()`:
   ```gdscript
   func cleanup() -> void:
       unbind_all()
       if card_fan != null and is_instance_valid(card_fan):
           card_fan.cleanup()
       var tree: SceneTree = get_tree()
       if tree != null and tree.root.has_node("EventBus"):
           # disconnects all signals from EventBus
   func _exit_tree() -> void:
       cleanup()
   ```

4. **Character Architecture Specifications from `ent_explorer_1` (`.agents/ent_explorer_1/exploration_report.md`)**:
   - Scene: `res://scenes/entities/Character.tscn` (Root: `CharacterBody2D`, class_name `Character`).
   - Children: `CollisionShape2D` (CircleShape2D r=14.0), `SelectionHighlight` (Node2D, visible on select), `Sprite2D` (texture filter Nearest), `RetroHPBar` (30x4 px, BgRect, FillRect, 1px black border Line2D), `StatusContainer` (HBoxContainer for 6x6 pixel condition badges).
   - Core API: `initialize_from_data(dict)`, `initialize_from_resource(res)`, `set_character_name(name, max_hp)`, `take_damage(amount) -> int`, `heal(amount) -> int`, `set_selected(bool)`, `add_status_effect(string) -> bool`, `remove_status_effect(string) -> bool`, `has_status_effect(string) -> bool`, `clear_all_status_effects()`, `load_texture_for_character(id) -> bool`, `update_hp_bar()`.
   - Signals: `hp_changed(current_hp, max_hp)`, `died()`, `healed(amount, current_hp)`, `damaged(amount, current_hp)`, `selection_changed(is_selected)`, `status_effect_applied(effect_name)`, `status_effect_removed(effect_name)`.

5. **Headless GUT CLI Test Runner Execution (`godot_project/run_gut_tests.sh`)**:
   Execution command: `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`.
   Result:
   - 15 test scripts executed.
   - 463 tests run, 463 tests passed (100% pass rate, exit code 0).
   - 0 ObjectDB leaks upon termination.

---

## 2. Logic Chain

1. **`add_child_autofree()` is Mandatory for 2D Scenes**:
   From Observation 1 and 2, when `CHARACTER_SCENE.instantiate()` is called, the node tree is constructed in memory but `_enter_tree()` and `_ready()` are not invoked until the instance enters the scene tree. In `Character.tscn`, all subnode references (`@onready var sprite_2d = $Sprite2D`, `@onready var retro_hp_bar = $RetroHPBar`, etc.) depend on `_ready()`. Calling `add_child_autofree(character)` attaches the node to `GutTest`, triggers `_ready()`, and guarantees deterministic removal and `free()` when the test finishes.
2. **Preventing Dynamic Child Node Leaks in `StatusContainer`**:
   From Observation 1 and 4, `StatusContainer` dynamically instantiates badge nodes (`ColorRect`) when `add_status_effect()` is called. If `remove_status_effect()` or `clear_all_status_effects()` only calls `status_container.remove_child(badge)` without calling `badge.free()`, the node remains orphaned in Godot's ObjectDB, violating the 0-leak acceptance criterion. Therefore, `Character.gd` must explicitly call `badge.free()` on removal, and the test suite must assert that removed badge nodes are deallocated.
3. **Tween Lifecycle Safety**:
   From Observation 1 and 3, any looping tween (such as the pulsating selection highlight ring) must be bound to the node via `tween.bind_node(self)`. When the node is freed by GUT, Godot automatically terminates and frees the bound tween, avoiding orphan tween tasks in the scene tree.
4. **Comprehensive Test Specification Matrix (27 AAA Tests)**:
   Synthesizing the requirements from `DISPATCH.md` and `ent_explorer_1`'s architectural blueprint, 27 concrete test specifications were designed in `test_strategy_report.md`:
   - 3 tests for Scene Hierarchy & Initialization (defaults, dictionary ingestion, resource binding).
   - 4 tests for Texture Assignment & Normalization (tactical heroes, 32x32 caste pixel art, scaling normalization, invalid path fallback).
   - 4 tests for Damage Calculation & Retro HP Bar Updates (normal damage, color transitions Green->Yellow->Red, non-positive damage rejection, overkill clamping to 0).
   - 4 tests for Healing & Overheal Clamping (normal heal, capping at max_hp, dead unit heal rejection, non-positive heal rejection).
   - 2 tests for Selection Highlight (visibility & signal emission, idempotency).
   - 4 tests for Status Effects (addition & query, removal & badge free, multi-status stacking, duplicate prevention).
   - 3 tests for Lethal Damage & Edge Cases (death signal emitted exactly once, zero/negative max_hp safe clamping, nonexistent status removal graceful handling).
   - 3 tests for Zero-Leak Lifecycle (clear all statuses frees all badges, status badge deallocation verification, 10-iteration rapid creation/destruction stress test).

---

## 3. Caveats

1. **Read-Only Explorer Persona**: In accordance with system instructions, no files were modified or created under `godot_project/scenes/`, `godot_project/scripts/`, or `godot_project/test/`. The deliverables are delivered in `.agents/ent_explorer_2/`.
2. **Sub-pixel Layout in Headless Mode**: Headless mode does not run a physical display server, but Control / Node2D dimensions, color rects, and line coordinates evaluate accurately in memory. Tests rely on exact numerical assertions (`assert_eq`, `assert_almost_eq`) without requiring rendering backends.
3. **EventBus Connection Teardown**: If `Character.gd` connects to singletons (`EventBus`), it must implement `_exit_tree()` to disconnect them, ensuring isolated test executions do not pollute global state.

---

## 4. Conclusion

The testing strategy and concrete specifications for `godot_project/test/unit/test_character_scene.gd` are completely defined.
- Complete 27-test GDScript specification is documented in `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/test_strategy_report.md`.
- Zero-leak lifecycle patterns (`add_child_autofree`, dynamic badge freeing, tween node binding, rapid creation/destruction verification) are validated against GUT's codebase and existing test suites.
- The project is ready for immediate handoff to the implementer agent (`ent_implementer_1`) to write `Character.tscn`, `Character.gd`, and `test_character_scene.gd`.

---

## 5. Verification Method

To independently verify all observations and test patterns:

1. **Inspect GUT Base Class & Test Runner**:
   ```bash
   view_file: godot_project/addons/gut/test.gd
   view_file: godot_project/addons/gut/gut_cmdln.gd
   ```

2. **Verify Current Headless Suite Pass Rate**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./run_gut_tests.sh
   ```
   *Expected outcome*: 463 tests run, 463 tests passed, exit code 0, 0 ObjectDB leaks.

3. **Verify Generated Reports**:
   - Inspect `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/test_strategy_report.md`
   - Inspect `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_2/handoff.md`
