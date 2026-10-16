# Handoff Report — Milestone M3: Independent Review & Adversarial Challenge

**Agent**: Reviewer 1 (`reviewer_m3_1`)  
**Roles**: Reviewer, Critic  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_1`  
**Verdict**: **REQUEST_CHANGES**  
**Timestamp**: 2026-10-16T01:50:00Z  

---

## 1. Observation

### 1.1 Automated Test Execution
- **Command**: `bash godot_project/run_gut_tests.sh`
- **Output**:
  ```text
  ============================================================
                      TEST SUMMARY                            
  ============================================================
  Test Scripts Executed:   34
  Tests Run:               765
  Tests Passed:            765
  Tests Failed:            0
  Total Assertions:        6622
  Assertions Passed:       6622
  Assertions Failed:       0
  ============================================================
  ==> All GUT tests passed successfully! (Exit code: 0)
  ```
- All 36 new unit tests across `test_relic_system.gd`, `test_reward_modal.gd`, and `test_forge_system.gd` passed with 0 test runner failures.

### 1.2 Integrity Check
No integrity violations detected:
- No hardcoded test outputs or dummy facade methods bypassing logic.
- Real mathematical, stateful, and signal-driven GDScript implementations.
- Independent execution and verification confirmed by running `bash godot_project/run_gut_tests.sh`.

### 1.3 Code Observations & Findings

#### Finding 1: [Critical / Major] Relic Catalog Mismatch Between `RewardModal.gd` and `RelicManager.gd`
- **Location**: `godot_project/scripts/run/ui/RewardModal.gd` lines 60–74:
  ```gdscript
  const ELITE_RELICS: Array[String] = [
  	"reliquia_pedra_afiar",
  	"reliquia_armadura_carapaca",
  	"reliquia_moeda_da_sorte",
  	"reliquia_balsamo_cogumelo",
  	"reliquia_tocha_eterna"
  ]

  const BOSS_RELICS: Array[String] = [
  	"reliquia_pingente_ambar",
  	"reliquia_martelo_runico",
  	"reliquia_foco_arcano",
  	"reliquia_cinzas_da_forja",
  	"reliquia_coroa_de_quitina"
  ]
  ```
- **Comparison with `RelicManager.gd` (lines 319–330)**:
  `RelicManager` registers 10 canonical relics:
  `martelo_runico`, `escudo_ancestral`, `bolsa_do_mercador`, `amuleto_ambar`, `dente_da_viuva`, `tocha_eterna`, `oleo_alquimico`, `frasco_feromonio`, `coroa_quitina`, `relogio_da_forja`.
- **Direct Observation**:
  - `reliquia_pedra_afiar`, `reliquia_armadura_carapaca`, `reliquia_moeda_da_sorte`, `reliquia_balsamo_cogumelo`, `reliquia_pingente_ambar`, `reliquia_foco_arcano`, and `reliquia_cinzas_da_forja` (7 of 10 relics) do NOT exist in `RelicManager._catalog`.
  - `reliquia_coroa_de_quitina` contains a naming mismatch: `RelicManager` registers `coroa_quitina`, not `coroa_de_quitina` (the prefix stripper produces `coroa_de_quitina`, which fails catalog lookup).
  - When granted upon beating an Elite or Boss node, `RelicManager.create_relic()` returns `null` and pushes a warning: `[RelicManager] Relíquia desconhecida: 'reliquia_pedra_afiar'`. The player receives an inert relic with zero gameplay effect.

#### Finding 2: [Major] Dual Gold Crediting in `RelicBolsaDoMercador.on_combat_victory`
- **Location**: `godot_project/scripts/run/relics/RelicManager.gd` lines 358–363:
  ```gdscript
  	func on_combat_victory(rewards: Dictionary, p_run_state: RunState) -> Dictionary:
  		rewards["gold"] = int(rewards.get("gold", 0)) + 10
  		if p_run_state != null:
  			p_run_state.add_gold(10)
  		return rewards
  ```
- **Direct Observation**:
  - `on_combat_victory` modifies the dictionary (`rewards["gold"] += 10`) AND directly calls `p_run_state.add_gold(10)`.
  - In `RewardModal.gd` lines 304–306:
    ```gdscript
    if offered_gold > 0:
    	state.add_gold(offered_gold)
    ```
  - If a combat controller queries `modify_combat_victory_rewards({"gold": 15})`, `RunState.gold` immediately increases by 10 (total +10), and the reward modal receives `offered_gold = 25`. When the player collects rewards in `RewardModal`, `state.add_gold(25)` is executed. Total gold awarded: **+35** (base 15 + 20 bonus, double the intended 10).

#### Finding 3: [Major] `RelicFrascoFeromonio` Protects Enemies and Consumes Charge on Enemy Debuffs
- **Location**: `godot_project/scripts/run/relics/RelicManager.gd` lines 283–286 and 405–409:
  ```gdscript
  func _on_status_applied(unit_id: String, status_id: String, duration: int) -> void:
  	for relic in _active_relics.values():
  		if relic.is_active:
  			relic.on_status_applied(unit_id, status_id, duration, run_state)
  ...
  class RelicFrascoFeromonio extends RelicData:
  	func on_status_applied(_unit_id: String, status_id: String, _duration: int, _run_state: RunState) -> Dictionary:
  		if counter == 0 and status_id in ["poisoned", "stunned", "frightened", "burning", "restrained"]:
  			counter = 1
  			return {"cancel_status": true}
  		return {}
  ```
- **Direct Observation**:
  - The relic's canonical design is: *"Anula a primeira condição negativa recebida pelos heróis em cada combate."*
  - Neither `_on_status_applied` nor `RelicFrascoFeromonio.on_status_applied` checks if `unit_id` belongs to `run_state.heroes`.
  - If a hero inflicts `poisoned`, `stunned`, or `burning` on an enemy insect at the start of combat, the relic returns `cancel_status: true` for the enemy, cancelling the player's attack effect and permanently consuming `counter = 1`. Subsequent debuffs applied by enemies to heroes will no longer be cancelled.

#### Finding 4: [Minor] Progressive Purge Counter Not Persisted in `RunState.gd` Across Forge Nodes
- **Location**: `godot_project/scripts/run/ui/ForgeScreen.gd` lines 123–126 and 316–318:
  ```gdscript
  	if state != null:
  		if "card_purges_count" in state:
  			purges_performed = int(state.get("card_purges_count"))
  ...
  	if state != null and "card_purges_count" in state:
  		state.set("card_purges_count", purges_performed)
  ```
- **Direct Observation**:
  - `RunState.gd` does not declare `card_purges_count`, nor does `to_dict()`/`from_dict()` persist it.
  - As a result, `"card_purges_count" in state` always evaluates to `false`.
  - In a run, if the player purges a card in Forge 1, closes the screen, and later enters Forge 2, `purges_performed` resets to 0 (cost resets from 75 back to 50).

#### Finding 5: [Minor] `RewardModal._ready()` Destroys Packed Nodes from `.tscn`
- **Location**: `godot_project/scripts/run/ui/RewardModal.gd` lines 104–107 and 141–143:
  ```gdscript
  func _ready() -> void:
  	if backdrop == null and modal_panel == null:
  		_build_programmatic_ui()
  ...
  func _build_programmatic_ui() -> void:
  	for c in get_children():
  		c.queue_free()
  ```
- **Direct Observation**:
  - `backdrop` and `modal_panel` are declared as plain variables initialized to `null`.
  - When instantiated via `RewardModal.tscn`, `_ready()` always evaluates `if backdrop == null`, immediately destroying all children loaded from `.tscn` and recreating them procedurally. While functional, this renders `RewardModal.tscn` redundant and differs from `ForgeScreen.gd`'s clean `get_node_or_null` binding.

---

## 2. Logic Chain

1. **Relic Ecosystem Coherence (Observation 1.3.1)**:
   - *Premise*: In roguelike campaign progression, Elite and Boss encounters must grant impactful passive artifacts that activate through `RelicManager`.
   - *Breakdown*: `RewardModal` draws from `ELITE_RELICS` and `BOSS_RELICS` containing legacy placeholder IDs (`reliquia_pedra_afiar`, `reliquia_pingente_ambar`, etc.) and a typo (`coroa_de_quitina` vs `coroa_quitina`).
   - *Deduction*: When players clear Elite or Boss encounters, the rewarded relics are unknown to `RelicManager`, yielding inert artifacts.

2. **Economic Integrity (Observation 1.3.2)**:
   - *Premise*: Modifying reward dictionaries in pipelines should either produce values for display/claiming OR perform direct state mutation, not both.
   - *Breakdown*: `RelicBolsaDoMercador` does both: modifies `rewards["gold"]` to 25 AND adds 10 directly to `RunState.gold`.
   - *Deduction*: In downstream combat-to-reward flow (Milestone M4), `RewardModal` awards 25 gold on top of the 10 already added, generating +35 gold (double the +10 bonus).

3. **Adversarial Combat Logic (Observation 1.3.3)**:
   - *Premise*: Relics intended to protect heroes must filter event participants before applying protective negation.
   - *Breakdown*: `RelicFrascoFeromonio.on_status_applied` does not verify `_run_state.heroes.has(_unit_id)`.
   - *Deduction*: A player opening combat with a fire or poison card against an enemy insect will inadvertently protect the enemy and waste the relic's protection for the remainder of the battle.

4. **Conclusion Support**:
   - Because Findings 1, 2, and 3 break expected runtime interactions between M3 subsystems (`RewardModal` ↔ `RelicManager`), the implementation cannot be approved without targeted adjustments.

---

## 3. Caveats

- **Scope Boundary**: Full runtime integration between the 20x20 combat grid (`Main.tscn` / `FortressBoard.tscn`) and `RewardModal` is scheduled for Milestone M4 (`RunCombatBridge`). This review assessed M3 components autonomously and through their defined interface contracts.
- **Test Suite Pass Rate**: The fact that all 765 tests pass is because the worker's unit tests tested `RelicManager` and `RewardModal` in isolation from each other (e.g., `test_relic_bolsa_do_mercador_awards_extra_gold` asserted the dual mutation, and `test_reward_modal` used an isolated mock). The issues identified above are integration flaws discovered via adversarial static and architectural review.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Worker M3 must address the following required items:
1. **Fix Relic Pools in `RewardModal.gd`**:
   Replace `ELITE_RELICS` and `BOSS_RELICS` with canonical IDs matching `RelicManager.gd` and `ForgeScreen.gd` (e.g. `escudo_ancestral`, `bolsa_do_mercador`, `amuleto_ambar`, `tocha_eterna`, `oleo_alquimico` for Elite; `martelo_runico`, `dente_da_viuva`, `frasco_feromonio`, `coroa_quitina`, `relogio_da_forja` for Boss). Also fix `coroa_de_quitina` -> `coroa_quitina`.
2. **Eliminate Dual Gold Crediting in `RelicBolsaDoMercador`**:
   In `RelicBolsaDoMercador.on_combat_victory`, remove `p_run_state.add_gold(10)` so the method only modifies `rewards["gold"] = int(rewards.get("gold", 0)) + 10`. Update `test_relic_bolsa_do_mercador_awards_extra_gold` accordingly.
3. **Add Hero Verification to `RelicFrascoFeromonio`**:
   In `RelicFrascoFeromonio.on_status_applied`, check that `_run_state != null and _run_state.heroes.has(_unit_id)` before cancelling status and setting `counter = 1`. Add a unit test asserting that enemy debuffs do NOT consume the relic's charge.
4. **Persist `card_purges_count` in `RunState.gd`**:
   Declare `var card_purges_count: int = 0` in `RunState.gd`, include in `to_dict()` and `from_dict()`, ensuring progressive forge costs persist across visits.
5. **Clean `.tscn` Binding in `RewardModal.gd`**:
   Adopt `ForgeScreen.gd`'s pattern using `get_node_or_null` in `_setup_ui_structure()` so packed scene nodes are utilized when loaded via `.tscn`.

---

## 5. Verification Method

To independently verify the changes once applied:
1. **Execute Full GUT Test Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Expected Result*: All tests pass with exit code 0.
2. **Verify Relic Catalog Alignment**:
   In `RewardModal.gd`, inspect `ELITE_RELICS` and `BOSS_RELICS`. Verify that every single ID maps to a valid entry in `RelicManager._catalog` via `RelicManager.create_relic(id) != null`.
3. **Verify Enemy Debuff Resilience**:
   Run a GUT test where an enemy unit (`"larva_carniceira"`) receives status `"poisoned"`. Confirm that `RelicFrascoFeromonio` returns `{}` and preserves `counter == 0`.
4. **Verify Single Gold Crediting**:
   Check that `RelicBolsaDoMercador.on_combat_victory` does not modify `_state.gold` directly.
