# Handoff Report — Milestone M4: Tactical Combat Integration, Persistent Hero HP, and Permadeath

**Date**: 2026-10-16
**Agent**: Worker M4 (`worker_m4_1`)
**Milestone**: M4 — Full Tactical Combat Integration into Run Map Nodes (COMBAT, ELITE, SIEGE, BOSS)
**Status**: COMPLETE (100% GUT Tests Passing: 836/836, 0 failures, exit code 0)

---

## 1. Observation

1. **Procedural Encounter Generation (`CombatEncounterGenerator.gd`)**:
   - Location: `godot_project/scripts/run/combat/CombatEncounterGenerator.gd` (`RefCounted`).
   - Implements `generate_encounter()` with flexible polymorphic signature (accepting `(act: int, node_type: int, rng: RandomNumberGenerator)` or `(node: RunNode, act: int, rng: RandomNumberGenerator)` or `(seed: int, ...)`).
   - Generates procedural tactical squads tailored by node type:
     - `COMBAT`: 2–4 Isectum minions (`batedor`, `soldado`, `zangao_invasor`, `formiga_acida`, `soldado_mandibula`), max 3 rounds.
     - `ELITE`: 4–6 hardened beasts with champions (`escaravelho_couracado`, `besouro_rinoceronte`), webs hazards, max 4 rounds.
     - `SIEGE`: 6–8 horde swarm, multiple waves, max 5 rounds.
     - `BOSS`: Cannibal Spider Queen (`viuva_canibal`, 120 HP, 16 AC, 3 ATK bonus, 2 attack range) with guardian bodyguards and web hazards, max 5 rounds.
   - Deterministic seeding supported via `RandomNumberGenerator.seed`.

2. **Run Combat Bridge (`RunCombatBridge.gd`)**:
   - Location: `godot_project/scripts/run/combat/RunCombatBridge.gd` (`RefCounted`).
   - `setup_combat(run_state: RunState, node: RunNode, rng: RandomNumberGenerator = null) -> Dictionary`:
     - Filters living heroes (`run_state.get_living_heroes()`) and respects permadeath by strictly omitting fallen heroes from party descriptors.
     - Persists living heroes' exact HP into the tactical board (`hp = run_state.hero_hp[hero_id]`).
     - Ingests and converts run card string IDs (`run_state.deck`) into rich `CardData` instances via `convert_deck()`.
     - Caches active encounter payload in `_current_encounter`.
   - `sync_combat_result(run_state: RunState, result: Dictionary) -> Dictionary`:
     - Reads final HP per hero directly from `result.get("hero_hp")` or `result.get("surviving_heroes_hp")`.
     - Employs differential damage application (`run_state.damage_hero(hid, current_hp - final_hp)`).
     - Marks heroes dropping to 0 HP as dead (`run_state.fallen_heroes`), enforcing permadeath.
     - Updates `run_state.enemies_killed`, `run_state.gold`, `run_state.floors_cleared`, and completes node.
     - If all party members are dead, updates `run_state.status = RunState.Status.DEFEAT`.
     - Invokes `clear_encounter()` on completion.

3. **Map Screen Combat Routing (`RunMapScreen.gd`)**:
   - Location: `godot_project/scripts/run/RunMapScreen.gd`.
   - In `_on_node_pressed(node_id: int)`: when target node is a combat type (`target_node.is_combat_type()`), routes to `_transition_to_combat_node(target_node)`.
   - Prepares encounter via `RunCombatBridge.setup_combat(state, target_node, rng)`.
   - In live gameplay: transitions scene to `res://scenes/main/Main.tscn` (or routes via `GameManager.GameState.COMBATE_TATICO`).
   - In headless test runner: guarded via `_is_in_gut_runner()` to prevent tearing down the GUT runner tree.

4. **Cerco Tactical Controller Ingestion (`CercoGameController.gd`)**:
   - Location: `godot_project/scripts/main/CercoGameController.gd`.
   - Decoupled initialization via `_should_setup_from_run_session()`:
     - Detects active run session (`RunSession.has_active_run()`) with an active encounter (`RunCombatBridge.has_active_encounter()`) or combat node (`current_node.is_combat_type()`).
     - If true, calls `_setup_from_run_session()`: spawns surviving heroes at designated courtyard coordinates with persistent HP, builds battle deck from `run_state.deck`, registers encounter squads and environmental hazards (`hazards`), and hooks `RelicManager(run_state)`.
     - If false, executes legacy `_setup_standalone_cerco()` preserving 100% backwards compatibility for standalone Cerco matches.
   - Victory/Defeat Hooks:
     - On victory in run mode: presents `RewardModal.tscn` (configured with `run_state_ref` and `current_node_ref`), seamlessly connecting post-combat loot and card drafting back to `RunMapScreen.tscn`.
     - On defeat in run mode: triggers `GameOverModal` with expedition statistics.

5. **GUT Test Suites**:
   - `godot_project/test/unit/test_combat_encounter_generator.gd`: 13 comprehensive unit tests validating deterministic generation, enemy caste distributions, squad sizes, and boss specs.
   - `godot_project/test/unit/test_run_combat_integration.gd`: 15 comprehensive integration tests validating headless safety, bridge contracts, HP delta synchronization, permadeath enforcement, deck conversion, and controller ingestion.
   - Both suites follow strict Arrange-Act-Assert (AAA) pattern with zero memory leaks (`autofree`).

---

## 2. Logic Chain

1. **Separation of Concerns & Decoupled Architecture**:
   - `RunState` is an abstract campaign data structure, while `CercoGameController` is a tactical isometric board coordinator.
   - `RunCombatBridge` acts as a pure, stateless mediator (`RefCounted`) between the two systems without introducing scene coupling or circular references.

2. **Permadeath & Persistent HP Enforcement**:
   - Any damage suffered by heroes on the tactical `FortressBoard` is mapped at combat conclusion to `RunCombatBridge.sync_combat_result()`.
   - If hero HP reaches 0, `RunState.damage_hero()` marks them in `run_state.fallen_heroes`.
   - During subsequent encounters, `_setup_from_run_session()` inspects `run_state.get_living_heroes()`; fallen heroes are never placed or registered on the board.

3. **Zero-Regression Standalone Cerco Compatibility**:
   - Prior existing tests in `test_cerco_screens.gd` instantiate `CercoGameController` for standalone testing without a running expedition.
   - By creating `_should_setup_from_run_session()`, the controller accurately differentiates between a live campaign battle and standalone execution, ensuring 100% of all legacy tests pass without interference.

---

## 3. Caveats

- In headless test runner environments, `SceneTree.change_scene_to_file()` must be bypassed to avoid terminating the GUT runner process; this is safely guarded via `_is_in_gut_runner()`.
- Future milestone expansions adding multi-act boss encounters should register additional caste entries in `CombatEncounterGenerator.ACT_CASTES` for Act 2 and Act 3.
- No other caveats.

---

## 4. Conclusion

Milestone M4 is completely implemented, verified, and adheres strictly to the Integrity Mandate. Tactical combat encounters (Combat, Elite, Siege, and Cannibal Queen Boss) seamlessly launch from run map nodes with persistent HP and permadeath, returning rewards via `RewardModal` upon victory. All 836 project tests pass with 0 failures, 0 errors, and exit code 0.

---

## 5. Verification Method

To independently reproduce and verify this implementation:

```bash
cd /home/anderson/Documents/projeto/RPG-battle
bash godot_project/run_gut_tests.sh
```

Expected output:
```text
============================================================
                    TEST SUMMARY                            
============================================================
Test Scripts Executed:   38
Tests Run:               836
Tests Passed:            836
Tests Failed:            0
Total Assertions:        8330
Assertions Passed:       8330
Assertions Failed:       0
============================================================

==> All GUT tests passed successfully! (Exit code: 0)
```
