# Handoff Report — Milestone M3: Independent Reviewer 2

**Agent**: Reviewer & Adversarial Critic (`reviewer_m3_2`)  
**Mission**: Milestone M3 Independent Quality & Adversarial Review  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/reviewer_m3_2`  
**Timestamp**: 2026-10-16T01:50:00Z  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

Milestone M3 establishes solid foundational architecture for `RelicData.gd`, `RelicManager.gd`, headless safe UI instantiation, and progressive deck purging. The GUT test runner passes 100% (765/765 tests, 0 errors, exit code 0). However, adversarial inspection revealed critical integration flaws and dummy/orphan artifact references:

1. **CRITICAL (INTEGRITY VIOLATION / DUMMY RELIC IDS)**: `RewardModal.gd` defines `ELITE_RELICS` and `BOSS_RELICS` containing 8 relic IDs that do not exist in `RelicManager.gd`. In real runs, 80% of Elite and Boss relic rewards are completely inert/uninstantiable, and the tests in `test_reward_modal.gd` self-certified this by asserting only against `RewardModal`'s internal array.
2. **CRITICAL (DUAL RELIC STACKING EXPLOIT)**: Inconsistency between prefixed IDs (`reliquia_martelo_runico`) in `RewardModal` and unprefixed IDs (`martelo_runico`) in `ForgeScreen` allows duplicate relic acquisition, bypassing `RunState.has_relic()` and stacking passive effects in `RelicManager._active_relics`.
3. **MAJOR (DOUBLE GOLD ACCUMULATION)**: `RelicBolsaDoMercador.on_combat_victory()` both increments `rewards["gold"]` by 10 and directly invokes `p_run_state.add_gold(10)`. When downstream systems apply the reward dictionary, the bonus gold is credited twice (+20g instead of +10g).
4. **MAJOR (FORGE PURGE COUNT NON-PERSISTENCE)**: `ForgeScreen.gd` attempts to sync `card_purges_count` with `RunState`, but `RunState.gd` neither declares this member variable nor serializes it in `to_dict()`/`from_dict()`. Purge cost resets to 50g across separate Forge visits.

---

## 1. Observation

### 1.1 Automated Test Execution
- Executed `bash godot_project/run_gut_tests.sh` from `/home/anderson/Documents/projeto/RPG-battle`:
  ```text
  ============================================================
                      TEST SUMMARY                            
  ============================================================
  Test Scripts Executed:   34
  Tests Run:               765
  Tests Passed:            765
  Tests Failed:            0
  Total Assertions:        6626
  Assertions Passed:       6626
  Assertions Failed:       0
  ============================================================
  ==> All GUT tests passed successfully! (Exit code: 0)
  ```

### 1.2 Orphan Relic IDs in RewardModal vs. RelicManager
- In `godot_project/scripts/run/ui/RewardModal.gd` (lines 60–74):
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
- In `godot_project/scripts/run/relics/RelicManager.gd` (lines 319–330):
  ```gdscript
  func _register_canonical_catalog() -> void:
  	register_catalog_entry("martelo_runico", func(): return RelicMarteloRunico.new())
  	register_catalog_entry("escudo_ancestral", func(): return RelicEscudoAncestral.new())
  	register_catalog_entry("bolsa_do_mercador", func(): return RelicBolsaDoMercador.new())
  	register_catalog_entry("amuleto_ambar", func(): return RelicAmuletoAmbar.new())
  	register_catalog_entry("dente_da_viuva", func(): return RelicDenteDaViuva.new())
  	register_catalog_entry("tocha_eterna", func(): return RelicTochaEterna.new())
  	register_catalog_entry("oleo_alquimico", func(): return RelicOleoAlquimico.new())
  	register_catalog_entry("frasco_feromonio", func(): return RelicFrascoFeromonio.new())
  	register_catalog_entry("coroa_quitina", func(): return RelicCoroaQuitina.new())
  	register_catalog_entry("relogio_da_forja", func(): return RelicRelogioDaForja.new())
  ```
- `RelicManager.create_relic("reliquia_pedra_afiar")` returns `null` and prints `push_warning("[RelicManager] Relíquia desconhecida: 'reliquia_pedra_afiar'")`.
- Only `tocha_eterna` and `martelo_runico` match.
- Notice also `reliquia_coroa_de_quitina` (has `_de_`) vs `coroa_quitina` (no `_de_`). `replace("reliquia_", "")` leaves `"coroa_de_quitina"`, which is also not in `RelicManager` catalog!

### 1.3 Self-Certifying Test Assertions in `test_reward_modal.gd`
- In `godot_project/test/unit/test_reward_modal.gd` (lines 69–70, 84–85):
  ```gdscript
  assert_false(modal.offered_relic_id.is_empty(), "Elite concede relíquia garantida")
  assert_true(modal.offered_relic_id.begins_with("reliquia_"), "ID de relíquia válido")
  ...
  assert_true(RewardModal.BOSS_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de chefes")
  ```
- The test only verifies that `modal.offered_relic_id` belongs to `RewardModal.BOSS_RELICS`, completely bypassing validation against `RelicManager.create_relic()` or `RelicManager.get_catalog_ids()`.

### 1.4 Double Gold Crediting in `RelicBolsaDoMercador`
- In `godot_project/scripts/run/relics/RelicManager.gd` (lines 358–362):
  ```gdscript
  func on_combat_victory(rewards: Dictionary, p_run_state: RunState) -> Dictionary:
  	rewards["gold"] = int(rewards.get("gold", 0)) + 10
  	if p_run_state != null:
  		p_run_state.add_gold(10)
  	return rewards
  ```
- In `godot_project/scripts/run/ui/RewardModal.gd` (lines 304–306):
  ```gdscript
  if offered_gold > 0:
  	state.add_gold(offered_gold)
  	gold_collected.emit(offered_gold)
  ```
- If a caller calls `modify_combat_victory_rewards({"gold": 15})`:
  `rewards["gold"]` becomes 25, and `p_run_state` receives 10g.
  When `RewardModal` is passed `offered_gold = 25`, it calls `state.add_gold(25)`. Total gold received: +35g instead of +25g.

### 1.5 Missing State Field `card_purges_count` in `RunState.gd`
- In `godot_project/scripts/run/ui/ForgeScreen.gd` (lines 123–126 and 316–318):
  ```gdscript
  if state != null:
  	if "card_purges_count" in state:
  		purges_performed = int(state.get("card_purges_count"))
  	else:
  		purges_performed = 0
  ...
  if state != null and "card_purges_count" in state:
  	state.set("card_purges_count", purges_performed)
  ```
- In `godot_project/scripts/run/RunState.gd`:
  There is no declaration `var card_purges_count: int = 0`.
  In `to_dict()` and `from_dict()`, `card_purges_count` is neither serialized nor deserialized.
- Because `RunState` extends `RefCounted` without dynamic property interception, `"card_purges_count" in state` returns `false`.

---

## 2. Logic Chain

1. **Premise**: Relics earned from Elite and Boss nodes must be functional artifacts that activate in combat and exploration.
   - *Observation*: `RewardModal.gd` defines `ELITE_RELICS` and `BOSS_RELICS` using 8 IDs (`pedra_afiar`, `armadura_carapaca`, `moeda_da_sorte`, `balsamo_cogumelo`, `pingente_ambar`, `foco_arcano`, `cinzas_da_forja`, `coroa_de_quitina`) that have no matching classes or entries in `RelicManager._catalog`.
   - *Deduction*: When an Elite or Boss node awards any of these 8 relics to `RunState.relics`, `RelicManager.sync_from_run_state()` calls `create_relic()`, which returns `null`. The player gains no passive abilities from 80% of Elite and Boss rewards.
   - *Integrity Impact*: The test suite passed because `test_reward_modal.gd` checked `RewardModal.BOSS_RELICS.has(modal.offered_relic_id)` rather than validating integration with `RelicManager`. This constitutes a facade/dummy reference and self-certifying test.

2. **Premise**: Relic ownership must be idempotent: buying a relic in the Forge must prevent duplicate acquisition in RewardModals, and a relic should never stack with itself unless explicitly designed to do so.
   - *Observation*: `ForgeScreen` uses unprefixed IDs (`martelo_runico`), while `RewardModal` uses prefixed IDs (`reliquia_martelo_runico`). `RunState.has_relic()` performs exact string matching.
   - *Deduction*: A player possessing `martelo_runico` will evaluate to `has_relic("reliquia_martelo_runico") == false`. `RewardModal` will offer the duplicate relic. When added to `RunState.relics`, `RelicManager.sync_from_run_state()` registers both keys in `_active_relics` (`_active_relics["martelo_runico"]` and `_active_relics["reliquia_martelo_runico"]`). During `modify_attack_damage()`, both trigger, yielding +6 damage instead of +3.

3. **Premise**: Gold economy calculations must be single-source.
   - *Observation*: `RelicBolsaDoMercador.on_combat_victory()` mutates both `rewards["gold"]` (+10) and `p_run_state.add_gold(10)`.
   - *Deduction*: If downstream systems present the modified reward dictionary to the player via `RewardModal` (which credits `offered_gold` to `state`), the +10 bonus is applied twice, breaking the economy balance.

4. **Premise**: Forge purge costs are specified as progressive ($50, 75, 100\dots) across the expedition.
   - *Observation*: `ForgeScreen.gd` attempts to persist `card_purges_count` on `state`, but `RunState` has no such property and does not serialize it.
   - *Deduction*: Opening a second Forge screen in the run or reloading a run resets `purges_performed` to 0, resetting purge costs to 50g.

---

## 3. Caveats

- **No Regression in Existing Suites**: Baseline GUT suites (729 tests) and new M3 suites (36 tests) all execute and pass cleanly with 0 crashes and exit code 0.
- **UI & Memory Architecture**: `RewardModal.gd` and `ForgeScreen.gd` programmatic fallbacks, `autofree` patterns, and headless safety mechanisms are well-designed and stable.
- **Relic Logic Quality**: For the canonical 10 relics that *are* implemented in `RelicManager.gd`, their virtual hooks, typing, and unit tests are clean and well-structured.

---

## 4. Conclusion & Required Changes

The verdict is **REQUEST_CHANGES**. The following issues must be resolved:

### Action Item 1: Synchronize Relic Catalog between RewardModal, ForgeScreen, and RelicManager
- In `RewardModal.gd`:
  Replace the dummy IDs in `ELITE_RELICS` and `BOSS_RELICS` with canonical relics from `RelicManager`.
  Standardize on unprefixed canonical IDs (matching `ForgeScreen` and `RelicManager`):
  - `ELITE_RELICS`: `["escudo_ancestral", "bolsa_do_mercador", "tocha_eterna", "oleo_alquimico", "frasco_feromonio"]`
  - `BOSS_RELICS`: `["martelo_runico", "amuleto_ambar", "dente_da_viuva", "coroa_quitina", "relogio_da_forja"]`
- In `RewardModal._apply_gold_and_relic()`:
  Ensure `offered_relic_id` matches the exact string stored in `state.relics`.

### Action Item 2: Prevent Dual-Key Stacking in RelicManager
- In `RelicManager.register_relic()` and `sync_from_run_state()`:
  Normalize all incoming IDs (strip any leading `reliquia_`) before inserting into `_active_relics` or querying `has_relic()`, ensuring duplicate registrations are strictly rejected even if legacy prefixed strings are passed.

### Action Item 3: Fix Double Gold Crediting in `RelicBolsaDoMercador`
- In `RelicBolsaDoMercador.on_combat_victory()`:
  Only modify `rewards["gold"] = int(rewards.get("gold", 0)) + 10`. Remove `p_run_state.add_gold(10)` from inside the calculation hook, letting the caller (`RunNodeResolver` or `RewardModal`) apply the resulting gold to the state.
- Update `test_relic_bolsa_do_mercador_awards_extra_gold` in `test_relic_system.gd` accordingly.

### Action Item 4: Persist `card_purges_count` in `RunState.gd`
- In `godot_project/scripts/run/RunState.gd`:
  - Add `var card_purges_count: int = 0`.
  - Include `"card_purges_count": card_purges_count` in `to_dict()`.
  - Restore `card_purges_count = int(data.get("card_purges_count", 0))` in `from_dict()`.
- In `test_forge_system.gd`:
  Add a test verifying that `card_purges_count` persists across separate `ForgeScreen` instances instantiated with the same `RunState`.

### Action Item 5: Strengthen Unit Tests against Self-Certification
- In `test_reward_modal.gd`:
  Assert that any relic generated by `RewardModal` can be successfully resolved via `RelicManager.new().create_relic(modal.offered_relic_id) != null`.

---

## 5. Verification Method

1. **Execute GUT Test Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Expected Result*: 34+ test scripts executed, 765+ tests run, 0 failures, exit code 0.
2. **Verify Relic Catalog Completeness**:
   Ensure `RelicManager.new().create_relic(id) != null` for every ID in `RewardModal.ELITE_RELICS` and `RewardModal.BOSS_RELICS`.
3. **Verify Purge Count Persistence**:
   Instantiate `ForgeScreen` A, purge a card, free `ForgeScreen` A, instantiate `ForgeScreen` B with the same `RunState`, and assert that `_forge_b.get_current_purge_cost() == 75`.
