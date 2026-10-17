# Handoff Report — Milestone M4 Independent Review (Reviewer 2)

**Agent**: Reviewer 2 (`reviewer_m4_2`)  
**Roles**: Reviewer, Adversarial Critic  
**Milestone**: M4 — Tactical Combat Integration, Persistent Hero HP, and Permadeath  
**Date**: 2026-10-16  
**Final Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

Direct empirical observations from source inspection, tool execution, and adversarial testing:

### Observation 1: Test Suite Runtime Crash & Unexecuted Assertions
- **Location**: `godot_project/test/unit/test_run_combat_integration.gd`, lines 277–284:
```gdscript
func test_cerco_game_controller_ingests_run_session_with_living_heroes_only() -> void:
	# Arrange
	RunSession.start_new(999, {"aquele": 22, "stark": 0, "elden": 18}, ["movimento", "trabalho", "escavacao"])
	var run: RunState = RunSession.current
	# Mata stark antes do combate
	run.damage_hero("stark", 34)
	assert_false(run.is_hero_alive("stark"), "Stark está tombado")
```
- **Execution Command**: `godot --headless --path godot_project -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_run_combat_integration.gd -gexit`
- **Verbatim Output**:
```text
WARNING: [RunState] Herói inválido: stark
     at: push_warning (core/variant/variant_utility.cpp:1033)
     GDScript backtrace (most recent call first):
         [0] start_run (res://scripts/run/RunState.gd:63)
         [1] start_new (res://scripts/run/RunSession.gd:23)
         [2] test_cerco_game_controller_ingests_run_session_with_living_heroes_only (res://test/unit/test_run_combat_integration.gd:279)
SCRIPT ERROR: Invalid call. Nonexistent function 'damage_hero' in base 'Nil'.
          at: test_cerco_game_controller_ingests_run_session_with_living_heroes_only (res://test/unit/test_run_combat_integration.gd:282)
  [PASS] test_cerco_game_controller_ingests_run_session_with_living_heroes_only
Total Assertions: 52
```
- **Analysis**: `RunState.start_run()` line 62 explicitly rejects heroes with `HP <= 0` (`"stark": 0`), causing `RunSession.start_new()` to return `null`. Calling `run.damage_hero()` on `null` throws a fatal script crash. Because GUT only records assertion failures, the test was reported as `[PASS]`, while lines 283–301 (all 8 assertions checking `CercoGameController` permadeath, unit placement, and HP setup) were **never executed**.

### Observation 2: Broken `newly_fallen` Tracking in `RunCombatBridge.sync_combat_result()`
- **Location**: `godot_project/scripts/run/combat/RunCombatBridge.gd`, lines 149–159:
```gdscript
			if target_hp < prev_hp:
				run_state.damage_hero(hid, prev_hp - target_hp)
			elif target_hp > prev_hp:
				run_state.heal_hero(hid, target_hp - prev_hp)

			if target_hp <= 0:
				if not run_state.fallen_heroes.has(hid):
					run_state.fallen_heroes.append(hid)
					run_state.hero_died.emit(hid)
					summary["newly_fallen"].append(hid)
				run_state.hero_hp[hid] = 0
```
- **Context in `RunState.gd`**, lines 165–168:
```gdscript
	hero_hp[hero_id] = maxi(int(hero_hp[hero_id]) - amount, 0)
	if hero_hp[hero_id] == 0:
		fallen_heroes.append(hero_id)
		hero_died.emit(hero_id)
```
- **Analysis**: Line 150 calls `run_state.damage_hero(hid, ...)`, which automatically appends `hid` to `fallen_heroes`. Consequently, at line 155, `run_state.fallen_heroes.has(hid)` is **always true**. The conditional block is never entered, and `summary["newly_fallen"]` is **always empty** `[]` for any hero dying from combat damage.

### Observation 3: Dormant `RelicManager` in `CercoGameController` (Autoload vs Singleton Mismatch)
- **Location**: `godot_project/scripts/main/CercoGameController.gd`, line 175:
```gdscript
	# 7. Sincroniza Relíquias ativas com o EventBus
	relic_manager = RelicManager.new(run_state_ref)
```
- **Context in `RelicManager.gd`**, lines 48–49 & 57–58:
```gdscript
	if event_bus == null and Engine.has_singleton("EventBus"):
		event_bus = Engine.get_singleton("EventBus")

func connect_event_bus() -> void:
	if _connected or event_bus == null:
		return
```
- **Analysis**: `EventBus` is registered in `project.godot` as an **Autoload Node** under `/root/EventBus`, not a native C++ engine singleton (`Engine.has_singleton("EventBus")` returns `false`). When `CercoGameController` instantiates `RelicManager.new(run_state_ref)` without passing the `event_bus` instance, `RelicManager.event_bus` evaluates to `null`. As a result, `connect_event_bus()` silently skips signal registration, leaving all passive relics completely dormant during tactical combat in `CercoGameController`.

### Observation 4: Docstring vs Static Typing Parse Error in `CombatEncounterGenerator`
- **Location**: `godot_project/scripts/run/combat/CombatEncounterGenerator.gd`, lines 81–87:
```gdscript
static func generate_encounter(
	act_or_node: Variant,
	floor_index: int = 0,
	node_type: int = 0,
	p4: Variant = null,
	p5: Variant = null
) -> Dictionary:
```
- **Docstring**: Claims signature supports `(node: RunNode, seed_or_rng: Variant)`.
- **Compiler Error when called as documented**: Calling `CombatEncounterGenerator.generate_encounter(node, rng)` fails at compile-time with:
```text
SCRIPT ERROR: Parse Error: Invalid argument for "generate_encounter()" function: argument 2 should be "int" but is "RandomNumberGenerator".
```
Argument 2 is statically typed as `floor_index: int = 0`, rejecting `RandomNumberGenerator` or `Variant`.

### Observation 5: Worker Handoff Documentation Discrepancy
- In `worker_m4_1/handoff.md`, line 19 claims:
  `"BOSS: Cannibal Spider Queen (viuva_canibal, 120 HP, 16 AC, 3 ATK bonus, 2 attack range)"`
- In `CombatEncounterGenerator.gd`, lines 342–348, the implemented stats for Viúva Canibal are:
  `hp: 70, max_hp: 70, ac: 15, move_range: 3, attack_range: 3, attack_bonus: 4, attack_dice: 4`.

---

## 2. Logic Chain

1. **Test Integrity & False Positive Passing**:
   - `test_run_combat_integration.gd` contains a test `test_cerco_game_controller_ingests_run_session_with_living_heroes_only`.
   - The test attempts to create a run with `{"stark": 0}`, which causes `RunSession.start_new` to return `null`.
   - The test then calls `run.damage_hero()`, crashing the test runner with a `Nil` dereference.
   - GUT prints `[PASS]` because zero assertions were recorded before the crash. The 8 assertions intended to verify the core M4 milestone deliverable (permadeath filtering in the tactical board) never ran in the test suite.
   - While empirical testing in an isolated script confirms that `CercoGameController._setup_from_run_session()` does function when provided valid inputs, having a crashed, self-aborting test in the primary test suite compromises test integrity.

2. **Causal Chain for `newly_fallen` Bug**:
   - Upstream caller of `sync_combat_result()` expects `summary["newly_fallen"]` to identify which heroes died during the combat encounter.
   - Because `RunCombatBridge` calls `run_state.damage_hero()` first, `RunState` immediately mutates `fallen_heroes`.
   - The guard `if not run_state.fallen_heroes.has(hid):` immediately evaluates to `false`.
   - Any UI or downstream caller depending on `summary["newly_fallen"]` receives an empty list.

3. **Causal Chain for `RelicManager` Inactivity**:
   - Milestone M3 implemented relics listening to `EventBus` signals.
   - Milestone M4 tasked `CercoGameController` with connecting run relics into tactical combat.
   - `CercoGameController` relied on `RelicManager.new(run_state_ref)` without providing the `EventBus` node.
   - `RelicManager` looked up `Engine.has_singleton("EventBus")`, which is false for Autoloads.
   - Thus, combat encounters run with 0 active relic listeners on `EventBus`.

---

## 3. Caveats

- In headless test runs (`run_gut_tests.sh`), the overall test runner passes (836/836) only because GUT does not fail a test on an unhandled GDScript runtime error if no assertion failed beforehand.
- The procedural encounter generation logic in `CombatEncounterGenerator.gd` is mathematically sound, deterministic, and free of spatial collisions across 100+ simulated runs.
- `RunMapScreen.gd` properly encapsulates scene transitions and protects the GUT test runner tree via `_is_in_gut_runner()`.

---

## 4. Conclusion & Required Changes

The Milestone M4 implementation demonstrates strong procedural design and clean architectural decoupling, but requires immediate remediation for two functional defects and one test suite integrity flaw:

### Required Changes:
1. **Fix Test Setup in `test_run_combat_integration.gd` (Line 279)**:
   Initialize Stark with positive HP (e.g. `{"aquele": 22, "stark": 34, "elden": 18}`) before calling `run.damage_hero("stark", 34)`. This prevents the `Nil` crash and allows all 8 assertions to execute properly.
2. **Fix `summary["newly_fallen"]` in `RunCombatBridge.gd` (Line 144)**:
   Record `var was_alive: bool = run_state.is_hero_alive(hid)` before applying damage. If `was_alive` and `target_hp <= 0`, append `hid` to `summary["newly_fallen"]`. Avoid redundant `hero_died.emit()` calls.
3. **Pass `EventBus` to `RelicManager` in `CercoGameController.gd` (Line 175)**:
   Obtain the autoload `EventBus` from `/root/EventBus` or `get_tree().root.get_node_or_null("EventBus")` and pass it to `RelicManager.new(run_state_ref, eb)`. Alternatively, add a fallback in `RelicManager.gd` to inspect `Engine.get_main_loop().root.get_node_or_null("EventBus")`.
4. **Relax Parameter Typing in `CombatEncounterGenerator.gd` (Line 83)**:
   Change `floor_index: int = 0` to `floor_index: Variant = 0` in `generate_encounter` to match the documented polymorphic signature.

---

## 5. Verification Method

To verify the fixes once implemented:

1. **Verify Test Execution Without Script Errors**:
   ```bash
   godot --headless --path godot_project -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_run_combat_integration.gd -gexit
   ```
   **Expected**: 15 tests run, 0 warnings about `Herói inválido: stark`, 0 `SCRIPT ERROR: Invalid call. Nonexistent function 'damage_hero'`, and total assertion count increases from 52 to 60.

2. **Verify Full GUT Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   **Expected**: Exit code 0, all 836+ tests passing with zero script errors in the logs.

3. **Verify Relic Connection**:
   In `CercoGameController`, verify `relic_manager.event_bus != null` when `_setup_from_run_session()` executes.
