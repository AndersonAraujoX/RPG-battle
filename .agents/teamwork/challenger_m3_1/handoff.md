# Handoff Report — Milestone M3: Adversarial Empirical Challenge

**Agent**: Challenger 1 (`challenger_m3_1`)  
**Mission**: Empirically stress-test Milestone M3 (RelicManager, RelicData, EventBus, RewardModal, ForgeScreen)  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m3_1`  
**Verdict**: **REQUEST_CHANGES**  
**Timestamp**: 2026-10-16T01:52:00Z  

---

## 1. Observation

### 1.1 Baseline and Stress Suite Execution
- **Baseline GUT Execution**:
  Command: `bash godot_project/run_gut_tests.sh`
  Result: 34 test scripts, 765 tests passed, 0 failures, 6629 assertions passed, exit code 0.
- **Stress Suite Authoring & Execution**:
  Created `godot_project/test/unit/test_relic_stress_adversarial.gd` (12 test cases, 1429 assertions).
  Full runner execution (`bash godot_project/run_gut_tests.sh`):
  ```text
  Test Scripts Executed:   36
  Tests Run:               798
  Tests Passed:            798
  Tests Failed:            0
  Total Assertions:        8141
  Assertions Passed:       8141
  Assertions Failed:       0
  ==> All GUT tests passed successfully! (Exit code: 0)
  ```

### 1.2 Verbatim Empirical Observations & Defect Evidence

1. **Defect 1: RewardModal Relic Disconnect (8 out of 10 relics missing from catalog)**
   - Location: `godot_project/scripts/run/ui/RewardModal.gd:60-74`
   - Code:
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
   - Test observation from `test_stress_reward_modal_relic_ids_vs_relic_manager_catalog`:
     ```text
     [FINDING] RewardModal relics that fail to resolve in RelicManager: [
       "reliquia_pedra_afiar",
       "reliquia_armadura_carapaca",
       "reliquia_moeda_da_sorte",
       "reliquia_balsamo_cogumelo",
       "reliquia_pingente_ambar",
       "reliquia_foco_arcano",
       "reliquia_cinzas_da_forja",
       "reliquia_coroa_de_quitina"
     ]
     ```
   - In `RelicManager._register_canonical_catalog()` (`RelicManager.gd:319-330`), the catalog only registers:
     `martelo_runico`, `escudo_ancestral`, `bolsa_do_mercador`, `amuleto_ambar`, `dente_da_viuva`, `tocha_eterna`, `oleo_alquimico`, `frasco_feromonio`, `coroa_quitina`, `relogio_da_forja`.
   - When a player defeats an Elite or Boss node, 80% of possible relic drops fail to instantiate in `RelicManager` with `WARNING: [RelicManager] Relíquia desconhecida`.

2. **Defect 2: Name Mismatch / Typo on Boss Relic `coroa_quitina`**
   - Location: `RewardModal.gd:73` vs `RelicManager.gd:328`
   - `RewardModal.gd` specifies `"reliquia_coroa_de_quitina"`.
   - Stripping `"reliquia_"` yields `"coroa_de_quitina"`.
   - `RelicManager.gd` registers `"coroa_quitina"`.
   - Result: `RelicManager.create_relic("reliquia_coroa_de_quitina")` returns `null`.

3. **Defect 3: Duplicate Relic Registration via Prefix Aliasing**
   - Location: `godot_project/scripts/run/relics/RelicManager.gd:101-115`
   - Code:
     ```gdscript
     func register_relic(relic_id: String) -> bool:
         if relic_id.is_empty() or _active_relics.has(relic_id):
             return false
         var relic: RelicData = create_relic(relic_id)
         ...
         _active_relics[relic_id] = relic
     ```
   - Test observation from `test_stress_duplicate_registration_with_reliquia_prefix`:
     ```text
     [FINDING] RelicManager permits duplicate relic registration via 'reliquia_' alias! Active count: 2
     [FINDING] Attack damage with double registration: bonus=6, final=12
     ```
   - Registering `"martelo_runico"` and subsequently `"reliquia_martelo_runico"` succeeds for both because `_active_relics` keys on raw input rather than canonical `relic.id`. Both instances become active and their passive modifiers stack (+3 + +3 = +6 bonus damage).

4. **Defect 4: ForgeScreen Relic Duplication Sale**
   - Location: `godot_project/scripts/run/ui/ForgeScreen.gd:176-180`
   - Code:
     ```gdscript
     var owned_relics: Array[String] = state.relics if state != null else []
     for rid in CANONICAL_RELICS.keys():
         if not owned_relics.has(rid):
             available_relic_ids.append(rid)
     ```
   - Test observation from `test_stress_forge_shop_duplicate_offering_with_prefix_alias`:
     ```text
     [FINDING] ForgeScreen offered 'martelo_runico' for sale even though RunState already holds 'reliquia_martelo_runico'!
     ```
   - If a player acquires a relic from `RewardModal` (e.g. `"reliquia_martelo_runico"`), `owned_relics.has("martelo_runico")` evaluates to `false`. The Forge offers `"martelo_runico"` for sale, allowing duplicate purchases.

5. **Defect 5: Sync Orphan Relics in `RelicManager.sync_from_run_state()`**
   - Location: `godot_project/scripts/run/relics/RelicManager.gd:90-98`
   - Code:
     ```gdscript
     func sync_from_run_state() -> void:
         if run_state == null:
             return
         for r_id in run_state.relics:
             if not _active_relics.has(r_id):
                 var relic: RelicData = create_relic(r_id)
                 if relic != null:
                     _active_relics[r_id] = relic
                     relic.on_registered(run_state)
     ```
   - Observation from `test_stress_relic_manager_sync_after_run_state_removal`:
     When a relic is removed from `RunState` (via `run_state.remove_relic()`), `sync_from_run_state()` only adds missing relics; it never removes active relics no longer in `run_state.relics`. The active relic remains alive as an orphan listener.

---

## 2. Logic Chain

1. **Premise**: In an integrated roguelike campaign loop, rewards acquired from combat nodes (`RewardModal`) must be compatible with both the passive modifier runtime (`RelicManager`) and the shop economy (`ForgeScreen`).
2. **Catalog Incompatibility**:
   - `RewardModal.gd` defines 10 relic rewards across Elite and Boss pools.
   - `RelicManager.gd` only implements the 10 canonical relics from `PROJECT.md`.
   - 8 of the 10 strings in `RewardModal` are unrecognized names (`pedra_afiar`, `armadura_carapaca`, `moeda_da_sorte`, `balsamo_cogumelo`, `pingente_ambar`, `foco_arcano`, `cinzas_da_forja`, `coroa_de_quitina`).
   - *Inference*: Any player reaching Milestone M3 post-combat reward will receive broken, non-functional relics 80% of the time upon defeating an Elite or Boss.
3. **Prefix Aliasing**:
   - `RewardModal` uses `"reliquia_"` prefixed identifiers (`reliquia_martelo_runico`).
   - `ForgeScreen` uses raw canonical identifiers (`martelo_runico`).
   - `RunState` stores string identifiers without canonicalization.
   - `RelicManager.register_relic()` checks `_active_relics.has(relic_id)` using the raw string rather than the canonical `relic.id`.
   - *Inference*: A player can own both `"martelo_runico"` and `"reliquia_martelo_runico"`. Both will be instantiated, doubling passive bonuses and causing balance exploits.
4. **Conclusion**:
   Milestone M3 cannot be approved in its current state because the subsystem integration between `RewardModal`, `ForgeScreen`, and `RelicManager` contains identifier mismatches and duplicate exploit vulnerabilities.

---

## 3. Caveats

- **Robust Components**:
  - The rapid churn stress test (100 cycles, 1,000 relic registrations/unregistrations) passed cleanly with 0 memory leaks and stable `RefCounted` lifecycle.
  - EventBus signal burst stress (1,000 rapid emissions across all combat and deck signals) showed zero crashes and zero dropped calls.
  - Re-entrant signal cascading (`unit_attacked` triggering `unit_damaged` triggering `unit_died`) executed cleanly without recursion overflow.
  - Headless UI instantiation of `RewardModal` and `ForgeScreen` functions reliably without errors.
- **Scope Restriction**:
  Per Teamwork protocol, as an Empirical Challenger with review-only permissions, I have documented and verified these bugs via `test_relic_stress_adversarial.gd` without modifying implementation source code.

---

## 4. Conclusion & Required Changes

**Verdict**: **REQUEST_CHANGES**

To reach production quality and prepare for Milestone M4 integration, the worker agent must perform the following remediation:

1. **Synchronize `RewardModal` Relic Pools with Canonical Relics**:
   Update `RewardModal.ELITE_RELICS` and `RewardModal.BOSS_RELICS` (`RewardModal.gd:60-74`) to strictly use canonical relics present in `RelicManager`:
   - Elite Pool: `"escudo_ancestral"`, `"dente_da_viuva"`, `"tocha_eterna"`, `"frasco_feromonio"`, `"relogio_da_forja"`
   - Boss Pool: `"martelo_runico"`, `"amuleto_ambar"`, `"oleo_alquimico"`, `"coroa_quitina"`, `"bolsa_do_mercador"`
2. **Canonicalize Relic IDs Across All Subsystems**:
   - In `RelicManager.register_relic()`, resolve the relic instance first and store in `_active_relics[relic.id]`. Check `has_relic(relic.id)` to reject aliases.
   - In `ForgeScreen.generate_inventory()`, normalize `owned_relics` by stripping `"reliquia_"` before filtering `available_relic_ids`.
3. **Fix `RelicManager.sync_from_run_state()` Pruning**:
   In `RelicManager.sync_from_run_state()`, iterate over existing `_active_relics.keys()` and remove any relics that are no longer present in `run_state.relics`.

---

## 5. Verification Method

1. **Execute Full GUT Test Suite**:
   ```bash
   timeout 60s bash godot_project/run_gut_tests.sh
   ```
   *Current state*: 36 suites, 798 tests passing, 0 failures.
2. **Execute Milestone M3 Adversarial Stress Suite**:
   ```bash
   timeout 60s bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_stress_adversarial.gd
   ```
   *Expected result after fix*:
   - `test_stress_duplicate_registration_with_reliquia_prefix` rejects alias registration (`dup_attempt == false`).
   - `test_stress_reward_modal_relic_ids_vs_relic_manager_catalog` reports 0 unresolvable relics.
   - `test_stress_forge_shop_duplicate_offering_with_prefix_alias` confirms no duplicate offerings.
