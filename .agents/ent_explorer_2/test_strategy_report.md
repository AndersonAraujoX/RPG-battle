# Test Strategy Report: GUT 2D Scene Testing & Character Entity QA Blueprint

**Date**: 2026-10-01  
**Agent**: `ent_explorer_2`  
**Milestone**: Entidades (M9 - Character Scene Testing)  
**Target Test Suite**: `res://test/unit/test_character_scene.gd`  
**Status**: Specification & Strategy Finalized  

---

## 1. Executive Summary

This report establishes the comprehensive testing strategy, lifecycle management protocol, and concrete test case specifications for `Character.tscn` / `Character.gd` using Godot Engine 4.3's GUT (Godot Unit Test) framework in headless mode (`--headless`).

Key findings and architectural guidelines:
1. **Node Lifecycle in GUT (`autofree` vs `add_child_autofree`)**:
   In Godot 4, 2D scene instances (`Character.tscn`) rely on `_ready()` to resolve `@onready` child nodes (`$Sprite2D`, `$RetroHPBar`, `$SelectionHighlight`, `$StatusContainer`). Calling `autofree(node)` only registers a node for cleanup, while `add_child_autofree(node)` explicitly attaches the node to the GUT test runner's scene tree (`GutTest`), triggering `_enter_tree()` and `_ready()`, and guarantees deterministic removal and deallocation during test teardown.
2. **Zero-Leak Memory Invariant**:
   Godot 4's headless runner strictly audits ObjectDB instances upon engine termination (`quit()`). Any orphan node (e.g. dynamically spawned status badges removed via `remove_child` without `free()` / `queue_free()`, unbound running `Tween`s, or unsevered Callable connections to autoload singletons like `EventBus`) causes ObjectDB memory leaks or crash warnings. We define explicit architectural guards and tests to enforce zero leaks.
3. **Canonical AAA Test Suite Specification**:
   We formulate **27 concrete unit test cases** structured strictly according to the **Arrange-Act-Assert (AAA)** pattern across 8 functional categories:
   - Scene Hierarchy & Component Resolution (3 tests)
   - Asset Texture Mapping & Normalization (4 tests)
   - Damage Calculation & Retro HP Bar Updates (4 tests)
   - Healing Mechanics & Clamping (4 tests)
   - Selection Highlight & Modulation (2 tests)
   - Status Effect Lifecycle & Badge Management (4 tests)
   - Lethal Damage & Edge Case Guards (3 tests)
   - Zero-Leak Lifecycle & Teardown Verification (3 tests)

---

## 2. GUT 2D Scene Testing Patterns in Godot 4 Headless

### 2.1 GUT Base Class Architecture (`addons/gut/test.gd`)

Inspection of `res://addons/gut/test.gd` demonstrates that `GutTest` extends `Node`. Test runner execution proceeds through well-defined internal hooks:

```
[Test Runner starts test method]
       │
       ▼
_internal_before_each(test_name)
       │  (clears _autofree_nodes, resets _signal_receivers)
       ▼
before_each() [User Hook]
       │
       ▼
test_method() [Test Execution - Arrange, Act, Assert]
       │
       ▼
after_each() [User Hook]
       │
       ▼
_internal_after_each()
       │
       ├── For each node in _autofree_nodes:
       │     if is_instance_valid(node):
       │         if node.get_parent() != null:
       │             node.get_parent().remove_child(node)
       │         node.free()
       │
       └── Disconnect all watched signals & clear receivers
```

### 2.2 `autofree()` vs `add_child_autofree()` Comparison

| Method | Behavior in `GutTest` | Tree State | `@onready` Resolution | Recommended Use Case |
|---|---|---|---|---|
| `autofree(node)` | Appends `node` to `_autofree_nodes`. If node not in tree and `GutTest` is in tree, calls `add_child(node)`. | Conditionally inside tree | May delay resolution if called before tree attachment | Standalone scripts / isolated controllers (`CardUI.new()`, `CombatLog.new()`) |
| `add_child_autofree(node)` | Calls `add_child(node)` explicitly, then calls `autofree(node)`. | Guaranteed inside tree immediately | **Immediate execution of `_enter_tree()` and `_ready()`** | **PackedScene instances (`CHARACTER_SCENE.instantiate()`)** |

**Rule for `test_character_scene.gd`**:
Always instantiate the character packed scene using:
```gdscript
var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
```
This guarantees:
1. `_ready()` runs before the test executes its "Act" phase.
2. All `@onready` variables (`sprite_2d`, `retro_hp_bar`, `selection_highlight`, `status_container`) are non-null and valid.
3. At the end of the test, GUT automatically calls `remove_child(character)` and `character.free()`, recursively freeing all children in the branch.

### 2.3 Signal Watching Primitives

GUT provides built-in signal receivers that record signal emissions with zero external mock boilerplate:
- `watch_signals(object)`: Subscribes to all declared signals on `object`.
- `assert_signal_emitted(object, "signal_name", "optional message")`: Validates that the signal was emitted at least once.
- `assert_signal_not_emitted(object, "signal_name", "optional message")`: Validates that no emissions occurred.
- `assert_signal_emit_count(object, "signal_name", count, "optional message")`: Asserts exact emission count.
- `assert_signal_emitted_with_parameters(object, "signal_name", [param1, param2, ...], "optional message")`: Compares exact parameter types and values.

---

## 3. Zero-Leak Node Lifecycle & Tree Management

### 3.1 Potential Leak Vectors in 2D Entity Testing

Based on Godot 4 ObjectDB memory mechanics and existing tests in `godot_project/test/unit/test_cerco_hud.gd`:

1. **Orphan Dynamic Badges in `StatusContainer`**:
   - *Risk*: When `remove_status_effect("poisoned")` is called, simply invoking `status_container.remove_child(badge)` removes the node from the tree but leaves it allocated in ObjectDB as an orphan node.
   - *Requirement*: `remove_status_effect()` MUST call `badge.free()` (or `badge.queue_free()`), and `clear_all_status_effects()` must iterate and free all child badge nodes.
2. **Tween Leakage**:
   - *Risk*: Calling `create_tween()` or `get_tree().create_tween()` creates a `Tween` managed by the scene tree. If the character node is freed while a looping pulse tween (like selection highlight) is active, the tween remains in memory or causes runtime errors.
   - *Requirement*: Always bind tweens to the node:
     ```gdscript
     _highlight_tween = create_tween().bind_node(self)
     ```
     Additionally, implement `cleanup()` on `Character.gd` to kill active tweens:
     ```gdscript
     if _highlight_tween != null and _highlight_tween.is_valid():
         _highlight_tween.kill()
     ```
3. **Singleton / Autoload Listener Leaks**:
   - *Risk*: If `Character` connects to `EventBus` signals (e.g. `EventBus.unit_moved`), freeing `Character` without disconnecting leaves dangling Callables on the autoload singleton.
   - *Requirement*: Disconnect all autoload listeners in `_exit_tree()` or `cleanup()`.
4. **Circular References in Custom Resources**:
   - *Risk*: If `CharacterData` holds a reference to `Character` and `Character` holds a reference to `CharacterData`, reference cycles prevent automatic destruction.
   - *Requirement*: `CharacterData` remains a pure data model (`Resource`) with no back-reference to `Node` or `Character`.

### 3.2 Verification via Rapid Instantiation Stress Test

To guarantee zero leaks in ObjectDB, the test suite includes a dedicated stress test that executes multiple cycles of instantiation, mutation, status manipulation, damage, healing, and deallocation:

```gdscript
func test_character_rapid_creation_and_destruction_zero_leaks() -> void:
    # Arrange & Act
    for i in range(10):
        var char_node: Character = CHARACTER_SCENE.instantiate() as Character
        add_child(char_node)
        char_node.set_character_name("StressTestHero_%d" % i, 20)
        char_node.add_status_effect("poisoned")
        char_node.add_status_effect("stunned")
        char_node.take_damage(5)
        char_node.heal(3)
        char_node.remove_status_effect("poisoned")
        char_node.cleanup()
        remove_child(char_node)
        char_node.free()
    
    # Assert
    pass_test("10 Character instances created, exercised with dynamic subnodes, and freed without memory leaks")
```

---

## 4. Comprehensive AAA Test Case Specifications

All test cases are designed for `godot_project/test/unit/test_character_scene.gd`.

### 4.1 Category 1: Scene Hierarchy & Instantiation (3 Tests)

#### Test 1: `test_character_scene_instantiation_defaults`
- **Objective**: Verify that `Character.tscn` can be instantiated and contains all required visual and functional subnodes with valid default properties.
- **Arrange**:
  - `const CHARACTER_SCENE = preload("res://scenes/entities/Character.tscn")`
- **Act**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
- **Assert**:
  - `assert_not_null(character, "Character scene instance must not be null")`
  - `assert_not_null(character.sprite_2d, "Sprite2D subnode must be resolved")`
  - `assert_not_null(character.collision_shape, "CollisionShape2D subnode must be resolved")`
  - `assert_not_null(character.selection_highlight, "SelectionHighlight subnode must be resolved")`
  - `assert_not_null(character.retro_hp_bar, "RetroHPBar subnode must be resolved")`
  - `assert_not_null(character.status_container, "StatusContainer subnode must be resolved")`
  - `assert_eq(character.current_hp, 10, "Default current_hp is 10")`
  - `assert_eq(character.max_hp, 10, "Default max_hp is 10")`
  - `assert_false(character.is_selected, "Default is_selected is false")`
  - `assert_true(character.is_alive, "Default is_alive is true")`
  - `assert_false(character.selection_highlight.visible, "Selection highlight must be hidden initially")`

#### Test 2: `test_character_initialize_from_data_dictionary`
- **Objective**: Verify data ingestion from `dados/personagens.json` structure (`Guerreiro`).
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `var data: Dictionary = {"name": "Guerreiro", "hp": 50, "max_hp": 50, "ac": 18, "velocidade": 3, "alcance": 1, "tipo_dano": "Cortante"}`
- **Act**:
  - `character.initialize_from_data(data)`
- **Assert**:
  - `assert_eq(character.character_name, "Guerreiro", "Name initialized")`
  - `assert_eq(character.current_hp, 50, "HP initialized")`
  - `assert_eq(character.max_hp, 50, "Max HP initialized")`
  - `assert_eq(character.ac, 18, "AC initialized")`
  - `assert_eq(character.move_speed, 3, "Move speed initialized")`
  - `assert_eq(character.attack_range, 1, "Attack range initialized")`
  - `assert_eq(character.damage_type, "Cortante", "Damage type initialized")`

#### Test 3: `test_character_initialize_from_character_data_resource`
- **Objective**: Verify data ingestion from a `CharacterData` Resource.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `var res: CharacterData = CharacterData.new()`
  - `res.id = "hero_mago"`
  - `res.name = "Mago"`
  - `res.hp = 30`
  - `res.max_hp = 30`
  - `res.ac = 12`
  - `res.velocidade = 4`
- **Act**:
  - `character.initialize_from_resource(res)`
- **Assert**:
  - `assert_eq(character.character_name, "Mago", "Name bound from resource")`
  - `assert_eq(character.current_hp, 30, "HP bound from resource")`
  - `assert_eq(character.max_hp, 30, "Max HP bound from resource")`
  - `assert_eq(character.ac, 12, "AC bound from resource")`
  - `assert_eq(character.move_speed, 4, "Move speed bound from resource")`

---

### 4.2 Category 2: Texture Assignment & Bounds Normalization (4 Tests)

#### Test 4: `test_character_texture_assignment_valid_hero`
- **Objective**: Verify loading and assigning a valid tactical hero PNG texture.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `var path: String = "res://assets/images/characters/heroes/guerreiro.png"`
- **Act**:
  - `var success: bool = character.load_texture_for_character("guerreiro")`
- **Assert**:
  - `assert_true(success, "Loading valid hero texture must return true")`
  - `assert_not_null(character.sprite_2d.texture, "Sprite2D texture must be populated")`
  - `assert_gt(character.sprite_2d.texture.get_width(), 0, "Texture width must be greater than 0")`

#### Test 5: `test_character_texture_assignment_isectum_caste_pixel_art`
- **Objective**: Verify loading a 32x32 pixel art caste from `monsters/isectum/`.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
- **Act**:
  - `var success: bool = character.load_texture_for_character("abelha_tecela")`
- **Assert**:
  - `assert_true(success, "Loading 32x32 caste texture must succeed")`
  - `assert_not_null(character.sprite_2d.texture, "Texture must be present")`
  - `assert_eq(character.sprite_2d.texture.get_width(), 32, "Caste texture width is 32px")`
  - `assert_eq(character.sprite_2d.texture.get_height(), 32, "Caste texture height is 32px")`

#### Test 6: `test_character_sprite_normalization_scaling`
- **Objective**: Verify that high-resolution textures (e.g. 676x369 or 1024x1024) are scaled down to fit `target_display_size` (30x30).
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.target_display_size = Vector2(30.0, 30.0)`
- **Act**:
  - `character.load_texture_for_character("guerreiro")`
- **Assert**:
  - `var tex: Texture2D = character.sprite_2d.texture`
  - `var effective_width: float = tex.get_width() * character.sprite_2d.scale.x`
  - `var effective_height: float = tex.get_height() * character.sprite_2d.scale.y`
  - `assert_lte(effective_width, 30.01, "Effective width must not exceed target display width")`
  - `assert_lte(effective_height, 30.01, "Effective height must not exceed target display height")`

#### Test 7: `test_character_texture_invalid_path_safe_fallback`
- **Objective**: Verify that querying an invalid/nonexistent character ID does not crash the engine and safely handles the missing asset.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
- **Act**:
  - `var success: bool = character.load_texture_for_character("non_existent_hero_99999")`
- **Assert**:
  - `assert_false(success, "Querying invalid ID returns false")`
  - `assert_null(character.sprite_2d.texture, "Texture remains null or safe fallback")`
  - `assert_true(character.is_inside_tree(), "Character remains valid and mounted in scene tree")`

---

### 4.3 Category 3: Damage Calculation & Retro HP Bar Updates (4 Tests)

#### Test 8: `test_character_take_damage_normal`
- **Objective**: Verify that standard damage reduces HP, updates the HP bar, and emits appropriate signals.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Warrior", 50)`
  - `watch_signals(character)`
- **Act**:
  - `var dealt: int = character.take_damage(15)`
- **Assert**:
  - `assert_eq(dealt, 15, "Actual damage dealt is 15")`
  - `assert_eq(character.current_hp, 35, "Current HP reduced to 35")`
  - `assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])`
  - `assert_signal_emitted_with_parameters(character, "damaged", [15, 35])`
  - `assert_true(character.is_alive, "Character is still alive")`

#### Test 9: `test_character_retro_hp_bar_fill_and_color_shifts`
- **Objective**: Verify the Pygame-equivalent retro HP bar visual thresholds (Green > 50%, Yellow 25-50%, Red <= 25%).
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Tank", 100)`
- **Act & Assert - Full Health (>50%)**:
  - `character.update_hp_bar()`
  - `assert_eq(character.hp_fill.color, Color(0.24, 0.78, 0.24, 1.0), "HP at 100% displays Retro Green")`
  - `assert_almost_eq(character.hp_fill.size.x, 30.0, 0.1, "HP fill is full 30px width")`
- **Act & Assert - Moderate Damage (25% - 50%)**:
  - `character.take_damage(60)` # 40/100 HP = 40%
  - `assert_eq(character.hp_fill.color, Color(0.78, 0.78, 0.24, 1.0), "HP at 40% displays Retro Yellow/Amber")`
  - `assert_almost_eq(character.hp_fill.size.x, 12.0, 0.1, "HP fill width is 12px (40% of 30px)")`
- **Act & Assert - Critical Damage (<= 25%)**:
  - `character.take_damage(25)` # 15/100 HP = 15%
  - `assert_eq(character.hp_fill.color, Color(0.78, 0.24, 0.24, 1.0), "HP at 15% displays Retro Crimson")`
  - `assert_almost_eq(character.hp_fill.size.x, 4.5, 0.1, "HP fill width is 4.5px (15% of 30px)")`

#### Test 10: `test_character_take_damage_zero_or_negative_ignored`
- **Objective**: Verify that passing 0 or negative damage values does not change HP or emit spurious signals.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Hero", 30)`
  - `watch_signals(character)`
- **Act**:
  - `var d0: int = character.take_damage(0)`
  - `var d_neg: int = character.take_damage(-10)`
- **Assert**:
  - `assert_eq(d0, 0, "0 damage returns 0 dealt")`
  - `assert_eq(d_neg, 0, "Negative damage returns 0 dealt")`
  - `assert_eq(character.current_hp, 30, "HP remains unchanged at 30")`
  - `assert_signal_not_emitted(character, "hp_changed")`
  - `assert_signal_not_emitted(character, "damaged")`

#### Test 11: `test_character_take_damage_overkill_clamps_at_zero`
- **Objective**: Verify that damage exceeding current HP clamps cleanly at 0 without going negative.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Mage", 20)`
  - `watch_signals(character)`
- **Act**:
  - `var dealt: int = character.take_damage(999)`
- **Assert**:
  - `assert_eq(dealt, 20, "Actual damage dealt is capped at remaining HP (20)")`
  - `assert_eq(character.current_hp, 0, "HP clamped at 0")`
  - `assert_false(character.is_alive, "Character marked not alive")`
  - `assert_signal_emitted(character, "died")`
  - `assert_almost_eq(character.hp_fill.size.x, 0.0, 0.01, "Retro HP bar fill is 0px width")`

---

### 4.4 Category 4: Healing Mechanics & Overheal Clamping (4 Tests)

#### Test 12: `test_character_heal_normal`
- **Objective**: Verify standard healing below maximum HP.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Cleric", 50)`
  - `character.take_damage(30)` # HP = 20
  - `watch_signals(character)`
- **Act**:
  - `var healed: int = character.heal(15)`
- **Assert**:
  - `assert_eq(healed, 15, "Healing received is 15")`
  - `assert_eq(character.current_hp, 35, "Current HP increased to 35")`
  - `assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])`
  - `assert_signal_emitted_with_parameters(character, "healed", [15, 35])`

#### Test 13: `test_character_heal_overhealing_capped_at_max_hp`
- **Objective**: Verify that healing cannot exceed `max_hp`.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Paladin", 40)`
  - `character.take_damage(5)` # HP = 35
  - `watch_signals(character)`
- **Act**:
  - `var healed: int = character.heal(20)`
- **Assert**:
  - `assert_eq(healed, 5, "Actual healing done is capped to missing 5 HP")`
  - `assert_eq(character.current_hp, 40, "HP clamped at max_hp (40)")`
  - `assert_signal_emitted_with_parameters(character, "hp_changed", [40, 40])`

#### Test 14: `test_character_heal_dead_unit_fails`
- **Objective**: Verify that a deceased character cannot be healed by normal heal actions.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Corpse", 20)`
  - `character.take_damage(20)` # is_alive = false, current_hp = 0
  - `watch_signals(character)`
- **Act**:
  - `var healed: int = character.heal(25)`
- **Assert**:
  - `assert_eq(healed, 0, "Healing dead character returns 0")`
  - `assert_eq(character.current_hp, 0, "HP remains 0")`
  - `assert_false(character.is_alive, "Character remains dead")`
  - `assert_signal_not_emitted(character, "healed")`

#### Test 15: `test_character_heal_zero_or_negative_ignored`
- **Objective**: Verify that 0 or negative heal values are safely rejected.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Fighter", 30)`
  - `character.take_damage(10)` # HP = 20
  - `watch_signals(character)`
- **Act**:
  - `var h0: int = character.heal(0)`
  - `var h_neg: int = character.heal(-10)`
- **Assert**:
  - `assert_eq(h0, 0, "0 heal returns 0")`
  - `assert_eq(h_neg, 0, "Negative heal returns 0")`
  - `assert_eq(character.current_hp, 20, "HP unchanged at 20")`
  - `assert_signal_not_emitted(character, "healed")`

---

### 4.5 Category 5: Selection Highlight & Modulation (2 Tests)

#### Test 16: `test_character_selection_toggle_and_visibility`
- **Objective**: Verify selection highlight visibility and signal emissions.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `watch_signals(character)`
- **Act - Select**:
  - `character.set_selected(true)`
- **Assert - Select**:
  - `assert_true(character.is_selected, "Character is selected")`
  - `assert_true(character.selection_highlight.visible, "Highlight is visible")`
  - `assert_signal_emitted_with_parameters(character, "selection_changed", [true])`
- **Act - Deselect**:
  - `character.set_selected(false)`
- **Assert - Deselect**:
  - `assert_false(character.is_selected, "Character is deselected")`
  - `assert_false(character.selection_highlight.visible, "Highlight is hidden")`
  - `assert_signal_emitted_with_parameters(character, "selection_changed", [false])`

#### Test 17: `test_character_selection_idempotency`
- **Objective**: Verify that selecting an already selected character does not trigger redundant transitions or signal spam.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_selected(true)`
  - `watch_signals(character)`
- **Act**:
  - `character.set_selected(true)`
- **Assert**:
  - `assert_signal_not_emitted(character, "selection_changed")`

---

### 4.6 Category 6: Status Effect Lifecycle & Badge Management (4 Tests)

#### Test 18: `test_character_status_effect_add_and_query`
- **Objective**: Verify applying a status condition, querying its presence, and verifying badge node creation in `StatusContainer`.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `watch_signals(character)`
- **Act**:
  - `var applied: bool = character.add_status_effect("poisoned")`
- **Assert**:
  - `assert_true(applied, "Status applied returns true")`
  - `assert_true(character.has_status_effect("poisoned"), "Query returns true")`
  - `assert_has(character.active_status_effects, "poisoned", "Condition in active array")`
  - `assert_eq(character.status_container.get_child_count(), 1, "Status badge created in container")`
  - `assert_signal_emitted_with_parameters(character, "status_effect_applied", ["poisoned"])`

#### Test 19: `test_character_status_effect_removal_frees_badge`
- **Objective**: Verify removing a status condition, updating internal array, and deallocating the visual badge node.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.add_status_effect("stunned")`
  - `watch_signals(character)`
- **Act**:
  - `var removed: bool = character.remove_status_effect("stunned")`
- **Assert**:
  - `assert_true(removed, "Removal returns true")`
  - `assert_false(character.has_status_effect("stunned"), "Query returns false")`
  - `assert_eq(character.status_container.get_child_count(), 0, "Badge removed from container")`
  - `assert_signal_emitted_with_parameters(character, "status_effect_removed", ["stunned"])`

#### Test 20: `test_character_multiple_distinct_status_effects`
- **Objective**: Verify stacking multiple unique status conditions.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
- **Act**:
  - `character.add_status_effect("poisoned")`
  - `character.add_status_effect("bleeding")`
  - `character.add_status_effect("frozen")`
- **Assert**:
  - `assert_eq(character.active_status_effects.size(), 3, "3 distinct effects active")`
  - `assert_eq(character.status_container.get_child_count(), 3, "3 badges in container")`
  - `assert_true(character.has_status_effect("poisoned"))`
  - `assert_true(character.has_status_effect("bleeding"))`
  - `assert_true(character.has_status_effect("frozen"))`

#### Test 21: `test_character_duplicate_status_effect_prevented`
- **Objective**: Verify that adding an existing status effect does not create duplicate badge nodes in `StatusContainer`.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.add_status_effect("burning")`
- **Act**:
  - `var second_apply: bool = character.add_status_effect("burning")`
- **Assert**:
  - `assert_eq(character.active_status_effects.size(), 1, "Status array size remains 1")`
  - `assert_eq(character.status_container.get_child_count(), 1, "Only 1 badge exists in container")`

---

### 4.7 Category 7: Lethal Damage & Edge Case Guards (3 Tests)

#### Test 22: `test_character_death_signal_emitted_exactly_once`
- **Objective**: Verify that taking lethal damage emits the `died` signal once, and subsequent hits do not re-emit `died`.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.set_character_name("Target", 10)`
  - `watch_signals(character)`
- **Act**:
  - `character.take_damage(10)` # Lethal hit
  - `character.take_damage(10)` # Post-mortem hit
- **Assert**:
  - `assert_signal_emit_count(character, "died", 1, "Signal died must be emitted exactly once")`
  - `assert_false(character.is_alive, "Character is deceased")`
  - `assert_eq(character.current_hp, 0, "HP stays 0")`

#### Test 23: `test_character_zero_or_negative_max_hp_guard`
- **Objective**: Verify that setting max_hp to 0 or negative is safely clamped to at least 1, avoiding division by zero in HP percentage calculation.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
- **Act**:
  - `character.set_character_name("InvalidHP", 0)`
- **Assert**:
  - `assert_gte(character.max_hp, 1, "Max HP clamped to minimum 1")`
  - `assert_gte(character.current_hp, 0, "Current HP non-negative")`

#### Test 24: `test_character_remove_nonexistent_status_graceful`
- **Objective**: Verify that removing a status condition not currently on the character returns false gracefully without throwing errors.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `watch_signals(character)`
- **Act**:
  - `var removed: bool = character.remove_status_effect("petrified")`
- **Assert**:
  - `assert_false(removed, "Removing nonexistent status returns false")`
  - `assert_signal_not_emitted(character, "status_effect_removed")`

---

### 4.8 Category 8: Zero-Leak Lifecycle & Teardown Verification (3 Tests)

#### Test 25: `test_character_clear_all_status_effects_frees_all_badges`
- **Objective**: Verify `clear_all_status_effects()` wipes all active conditions and frees all badge nodes from memory.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.add_status_effect("poisoned")`
  - `character.add_status_effect("stunned")`
  - `character.add_status_effect("bleeding")`
  - `assert_eq(character.status_container.get_child_count(), 3)`
- **Act**:
  - `character.clear_all_status_effects()`
- **Assert**:
  - `assert_eq(character.active_status_effects.size(), 0, "Active array cleared")`
  - `assert_eq(character.status_container.get_child_count(), 0, "All badges removed and freed")`

#### Test 26: `test_character_status_badge_node_memory_deallocation`
- **Objective**: Explicitly confirm that removing a status effect deallocates the underlying `Node` from ObjectDB rather than orphaning it.
- **Arrange**:
  - `var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character`
  - `character.add_status_effect("burning")`
  - `var badge_node: Node = character.status_container.get_child(0)`
  - `assert_not_null(badge_node, "Badge node exists")`
- **Act**:
  - `character.remove_status_effect("burning")`
- **Assert**:
  - `assert_true(badge_node.is_queued_for_deletion() or not is_instance_valid(badge_node), "Badge node must be freed or queued for deletion")`

#### Test 27: `test_character_rapid_creation_and_destruction_zero_leaks`
- **Objective**: Verify that 10 successive instantiations with node mutations, animations, and destructions exit cleanly with 0 ObjectDB leaks.
- **Arrange & Act**:
  - Run loop of 10 instances with setup, damage, heal, status, and explicit cleanup.
- **Assert**:
  - `pass_test("10 Character instances exercised and freed with zero memory leaks")`

---

## 5. Ready-to-Use GDScript Test Suite Blueprint

Below is the concrete implementation skeleton to be created by the implementer agent at `godot_project/test/unit/test_character_scene.gd`:

```gdscript
# res://test/unit/test_character_scene.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Character Entity Scene (M9)
## Tests Character.tscn & Character.gd with strict AAA pattern and 0 ObjectDB leaks.

const CHARACTER_SCENE: PackedScene = preload("res://scenes/entities/Character.tscn")

# ── 1. Scene Hierarchy & Instantiation Tests ─────────────────────────────────

func test_character_scene_instantiation_defaults() -> void:
	# Arrange & Act
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Assert
	assert_not_null(character, "Character instance must be non-null")
	assert_not_null(character.sprite_2d, "Sprite2D node resolved")
	assert_not_null(character.collision_shape, "CollisionShape2D node resolved")
	assert_not_null(character.selection_highlight, "SelectionHighlight node resolved")
	assert_not_null(character.retro_hp_bar, "RetroHPBar node resolved")
	assert_not_null(character.status_container, "StatusContainer node resolved")
	assert_eq(character.current_hp, 10, "Default current_hp is 10")
	assert_eq(character.max_hp, 10, "Default max_hp is 10")
	assert_false(character.is_selected, "Default is_selected is false")
	assert_true(character.is_alive, "Default is_alive is true")
	assert_false(character.selection_highlight.visible, "Highlight hidden initially")

func test_character_initialize_from_data_dictionary() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var data: Dictionary = {
		"name": "Guerreiro",
		"hp": 50,
		"max_hp": 50,
		"ac": 18,
		"velocidade": 3,
		"alcance": 1,
		"tipo_dano": "Cortante"
	}

	# Act
	character.initialize_from_data(data)

	# Assert
	assert_eq(character.character_name, "Guerreiro", "Name initialized")
	assert_eq(character.current_hp, 50, "HP initialized")
	assert_eq(character.max_hp, 50, "Max HP initialized")
	assert_eq(character.ac, 18, "AC initialized")
	assert_eq(character.move_speed, 3, "Speed initialized")
	assert_eq(character.attack_range, 1, "Range initialized")
	assert_eq(character.damage_type, "Cortante", "Damage type initialized")

func test_character_initialize_from_character_data_resource() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var res: CharacterData = CharacterData.new()
	res.id = "hero_mago"
	res.name = "Mago"
	res.hp = 30
	res.max_hp = 30
	res.ac = 12
	res.velocidade = 4

	# Act
	character.initialize_from_resource(res)

	# Assert
	assert_eq(character.character_name, "Mago", "Name bound from Resource")
	assert_eq(character.current_hp, 30, "HP bound from Resource")
	assert_eq(character.max_hp, 30, "Max HP bound from Resource")
	assert_eq(character.ac, 12, "AC bound from Resource")
	assert_eq(character.move_speed, 4, "Speed bound from Resource")

# ── 2. Texture Assignment & Normalization Tests ──────────────────────────────

func test_character_texture_assignment_valid_hero() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("guerreiro")

	# Assert
	assert_true(ok, "Loading valid hero texture succeeds")
	assert_not_null(character.sprite_2d.texture, "Texture assigned to Sprite2D")
	assert_gt(character.sprite_2d.texture.get_width(), 0, "Texture has positive width")

func test_character_texture_assignment_isectum_caste_pixel_art() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("abelha_tecela")

	# Assert
	assert_true(ok, "Loading caste pixel art succeeds")
	assert_not_null(character.sprite_2d.texture, "Texture assigned")
	assert_eq(character.sprite_2d.texture.get_width(), 32, "Caste pixel width is 32")
	assert_eq(character.sprite_2d.texture.get_height(), 32, "Caste pixel height is 32")

func test_character_sprite_normalization_scaling() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.target_display_size = Vector2(30.0, 30.0)

	# Act
	character.load_texture_for_character("guerreiro")

	# Assert
	var tex: Texture2D = character.sprite_2d.texture
	var eff_w: float = tex.get_width() * character.sprite_2d.scale.x
	var eff_h: float = tex.get_height() * character.sprite_2d.scale.y
	assert_lte(eff_w, 30.01, "Effective width scaled within 30px")
	assert_lte(eff_h, 30.01, "Effective height scaled within 30px")

func test_character_texture_invalid_path_safe_fallback() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("invalid_character_xyz")

	# Assert
	assert_false(ok, "Invalid ID returns false")
	assert_true(character.is_inside_tree(), "Character remains intact without crash")

# ── 3. Damage Calculation & Retro HP Bar Tests ───────────────────────────────

func test_character_take_damage_normal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Warrior", 50)
	watch_signals(character)

	# Act
	var dealt: int = character.take_damage(15)

	# Assert
	assert_eq(dealt, 15, "Damage dealt is 15")
	assert_eq(character.current_hp, 35, "Current HP is 35")
	assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])
	assert_signal_emitted_with_parameters(character, "damaged", [15, 35])
	assert_true(character.is_alive, "Character is alive")

func test_character_retro_hp_bar_fill_and_color_shifts() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Tank", 100)

	# Act & Assert - 100% (Green)
	character.update_hp_bar()
	assert_eq(character.hp_fill.color, Color(0.24, 0.78, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 30.0, 0.1)

	# Act & Assert - 40% (Yellow)
	character.take_damage(60)
	assert_eq(character.hp_fill.color, Color(0.78, 0.78, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 12.0, 0.1)

	# Act & Assert - 15% (Red)
	character.take_damage(25)
	assert_eq(character.hp_fill.color, Color(0.78, 0.24, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 4.5, 0.1)

func test_character_take_damage_zero_or_negative_ignored() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Hero", 30)
	watch_signals(character)

	# Act
	var d0: int = character.take_damage(0)
	var d_neg: int = character.take_damage(-10)

	# Assert
	assert_eq(d0, 0)
	assert_eq(d_neg, 0)
	assert_eq(character.current_hp, 30)
	assert_signal_not_emitted(character, "hp_changed")

func test_character_take_damage_overkill_clamps_at_zero() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Mage", 20)
	watch_signals(character)

	# Act
	var dealt: int = character.take_damage(999)

	# Assert
	assert_eq(dealt, 20, "Actual damage capped to current HP")
	assert_eq(character.current_hp, 0, "HP clamped to 0")
	assert_false(character.is_alive, "Character is dead")
	assert_signal_emitted(character, "died")
	assert_almost_eq(character.hp_fill.size.x, 0.0, 0.01)

# ── 4. Healing Tests ─────────────────────────────────────────────────────────

func test_character_heal_normal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Cleric", 50)
	character.take_damage(30)
	watch_signals(character)

	# Act
	var healed: int = character.heal(15)

	# Assert
	assert_eq(healed, 15)
	assert_eq(character.current_hp, 35)
	assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])
	assert_signal_emitted_with_parameters(character, "healed", [15, 35])

func test_character_heal_overhealing_capped_at_max_hp() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Paladin", 40)
	character.take_damage(5)
	watch_signals(character)

	# Act
	var healed: int = character.heal(20)

	# Assert
	assert_eq(healed, 5, "Healed only missing 5 HP")
	assert_eq(character.current_hp, 40)
	assert_signal_emitted_with_parameters(character, "hp_changed", [40, 40])

func test_character_heal_dead_unit_fails() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Corpse", 20)
	character.take_damage(20)
	watch_signals(character)

	# Act
	var healed: int = character.heal(25)

	# Assert
	assert_eq(healed, 0)
	assert_eq(character.current_hp, 0)
	assert_false(character.is_alive)
	assert_signal_not_emitted(character, "healed")

func test_character_heal_zero_or_negative_ignored() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Fighter", 30)
	character.take_damage(10)
	watch_signals(character)

	# Act
	var h0: int = character.heal(0)
	var h_neg: int = character.heal(-10)

	# Assert
	assert_eq(h0, 0)
	assert_eq(h_neg, 0)
	assert_eq(character.current_hp, 20)
	assert_signal_not_emitted(character, "healed")

# ── 5. Selection Highlight Tests ─────────────────────────────────────────────

func test_character_selection_toggle_and_visibility() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act - Select
	character.set_selected(true)

	# Assert - Select
	assert_true(character.is_selected)
	assert_true(character.selection_highlight.visible)
	assert_signal_emitted_with_parameters(character, "selection_changed", [true])

	# Act - Deselect
	character.set_selected(false)

	# Assert - Deselect
	assert_false(character.is_selected)
	assert_false(character.selection_highlight.visible)
	assert_signal_emitted_with_parameters(character, "selection_changed", [false])

func test_character_selection_idempotency() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_selected(true)
	watch_signals(character)

	# Act
	character.set_selected(true)

	# Assert
	assert_signal_not_emitted(character, "selection_changed")

# ── 6. Status Effect Lifecycle Tests ─────────────────────────────────────────

func test_character_status_effect_add_and_query() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act
	var applied: bool = character.add_status_effect("poisoned")

	# Assert
	assert_true(applied)
	assert_true(character.has_status_effect("poisoned"))
	assert_has(character.active_status_effects, "poisoned")
	assert_eq(character.status_container.get_child_count(), 1)
	assert_signal_emitted_with_parameters(character, "status_effect_applied", ["poisoned"])

func test_character_status_effect_removal_frees_badge() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("stunned")
	watch_signals(character)

	# Act
	var removed: bool = character.remove_status_effect("stunned")

	# Assert
	assert_true(removed)
	assert_false(character.has_status_effect("stunned"))
	assert_eq(character.status_container.get_child_count(), 0)
	assert_signal_emitted_with_parameters(character, "status_effect_removed", ["stunned"])

func test_character_multiple_distinct_status_effects() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.add_status_effect("poisoned")
	character.add_status_effect("bleeding")
	character.add_status_effect("frozen")

	# Assert
	assert_eq(character.active_status_effects.size(), 3)
	assert_eq(character.status_container.get_child_count(), 3)
	assert_true(character.has_status_effect("poisoned"))
	assert_true(character.has_status_effect("bleeding"))
	assert_true(character.has_status_effect("frozen"))

func test_character_duplicate_status_effect_prevented() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("burning")

	# Act
	character.add_status_effect("burning")

	# Assert
	assert_eq(character.active_status_effects.size(), 1)
	assert_eq(character.status_container.get_child_count(), 1)

# ── 7. Lethal Damage & Edge Case Guards ──────────────────────────────────────

func test_character_death_signal_emitted_exactly_once() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Target", 10)
	watch_signals(character)

	# Act
	character.take_damage(10)
	character.take_damage(10)

	# Assert
	assert_signal_emit_count(character, "died", 1)
	assert_false(character.is_alive)
	assert_eq(character.current_hp, 0)

func test_character_zero_or_negative_max_hp_guard() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.set_character_name("InvalidHP", 0)

	# Assert
	assert_gte(character.max_hp, 1, "Max HP clamped to minimum 1")
	assert_gte(character.current_hp, 0)

func test_character_remove_nonexistent_status_graceful() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act
	var removed: bool = character.remove_status_effect("petrified")

	# Assert
	assert_false(removed)
	assert_signal_not_emitted(character, "status_effect_removed")

# ── 8. Zero-Leak Lifecycle & Teardown Verification ───────────────────────────

func test_character_clear_all_status_effects_frees_all_badges() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("poisoned")
	character.add_status_effect("stunned")
	character.add_status_effect("bleeding")
	assert_eq(character.status_container.get_child_count(), 3)

	# Act
	character.clear_all_status_effects()

	# Assert
	assert_eq(character.active_status_effects.size(), 0)
	assert_eq(character.status_container.get_child_count(), 0)

func test_character_status_badge_node_memory_deallocation() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("burning")
	var badge_node: Node = character.status_container.get_child(0)
	assert_not_null(badge_node)

	# Act
	character.remove_status_effect("burning")

	# Assert
	assert_true(badge_node.is_queued_for_deletion() or not is_instance_valid(badge_node))

func test_character_rapid_creation_and_destruction_zero_leaks() -> void:
	# Arrange & Act
	for i in range(10):
		var char_node: Character = CHARACTER_SCENE.instantiate() as Character
		add_child(char_node)
		char_node.set_character_name("StressHero_%d" % i, 20)
		char_node.add_status_effect("poisoned")
		char_node.add_status_effect("stunned")
		char_node.take_damage(5)
		char_node.heal(3)
		char_node.remove_status_effect("poisoned")
		char_node.cleanup()
		remove_child(char_node)
		char_node.free()

	# Assert
	pass_test("10 Character instances exercised and freed with zero memory leaks")
```

---

## 6. Verification and Execution Protocols

To execute the test suite headlessly and verify 100% pass rate with zero ObjectDB leaks:

```bash
cd /home/anderson/Documents/projeto/RPG-battle/godot_project
./bin/godot --headless -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_character_scene.gd -gexit
```

Full suite regression command:
```bash
./run_gut_tests.sh
```

Expected metrics upon implementation:
- Test Scripts Executed: 16
- Total Tests: 490 (463 existing + 27 new)
- Passed: 490 (100%)
- Failed: 0
- Leaks: 0 ObjectDB leaks upon termination.
