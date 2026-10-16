# Handoff Report — Milestone M3: Adversarial Empirical Challenge 2 (Economy, Modals & Edge Cases)

**Agent**: Challenger 2 (`challenger_m3_2`)  
**Mission**: Empirically stress-test RewardModal, ForgeScreen, economy, 5-card minimum deck safety, and edge cases.  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/challenger_m3_2`  
**Verdict**: **REQUEST_CHANGES**  
**Timestamp**: 2026-10-16T01:53:00Z  

---

## 1. Observation

### 1.1 Test Runner Execution and Baseline
- **Baseline Execution**:
  Command: `bash godot_project/run_gut_tests.sh`
  Result: 34 test scripts, 765 tests passed, 0 failures, 6616 assertions passed, exit code 0.
- **Adversarial Suite Created**:
  File: `godot_project/test/unit/test_adversarial_m3.gd`
  Coverage: 24 tests, 106 assertions covering 0 gold, exact gold, negative gold, 5-card deck safety limits, reentrancy, unoffered card injection, duplicate purges, pool exhaustion, and null safety.
- **Combined Runner Execution**:
  Command: `bash godot_project/run_gut_tests.sh`
  Result:
  ```text
  Test Scripts Executed:   36
  Tests Run:               801
  Tests Passed:            801
  Tests Failed:            0
  Total Assertions:        8157
  Assertions Passed:       8157
  Assertions Failed:       0
  ==> All GUT tests passed successfully! (Exit code: 0)
  ```

---

### 1.2 Verbatim Empirical Observations & Defect Evidence

#### Defect 1: Runtime Engine SCRIPT ERROR in `ForgeScreen.gd:176` (Untyped Array Assignment)
- **File**: `godot_project/scripts/run/ui/ForgeScreen.gd:176`
- **Verbatim Code**:
  ```gdscript
  var owned_relics: Array[String] = state.relics if state != null else []
  ```
- **Observed Error in Godot Runner**:
  ```text
  SCRIPT ERROR: Trying to assign an array of type "Array" to a variable of type "Array[String]".
            at: ForgeScreen.generate_inventory (res://scripts/run/ui/ForgeScreen.gd:176)
            GDScript backtrace (most recent call first):
                [0] generate_inventory (res://scripts/run/ui/ForgeScreen.gd:176)
                [1] setup (res://scripts/run/ui/ForgeScreen.gd:129)
                [2] test_forge_screen_null_dependencies_safe (res://test/unit/test_adversarial_m3.gd:480)
  ```
- **Analysis**: In GDScript 4, the literal `[]` creates an untyped `Array`. When `state == null` (e.g. bare instantiation, headless tests, or isolated scene preview), assigning `[]` to statically typed `Array[String]` causes a runtime engine type-mismatch error.

#### Defect 2: Broken Cross-Visit Purge Cost Escalation due to Missing `card_purges_count` on `RunState`
- **Files**: `godot_project/scripts/run/ui/ForgeScreen.gd:123-126, 316-318` vs `godot_project/scripts/run/RunState.gd:30-45`
- **Verbatim Code in `ForgeScreen.gd`**:
  ```gdscript
  # Lines 123-126:
  if state != null:
      if "card_purges_count" in state:
          purges_performed = int(state.get("card_purges_count"))
      else:
          purges_performed = 0

  # Lines 316-318:
  purges_performed += 1
  if state != null and "card_purges_count" in state:
      state.set("card_purges_count", purges_performed)
  ```
- **Observation in `RunState.gd`**:
  `RunState` (a `RefCounted`) does NOT declare `var card_purges_count: int = 0`.
  In GDScript 4, `"card_purges_count" in state` evaluates to `false`.
- **Empirical Failure**: When a player visits Forge 1 and purges a card, `purges_performed` increases to 1. But `state.set("card_purges_count", 1)` is never executed because `"card_purges_count" in state` is false. When the player visits a second Forge node (`ForgeScreen` instance 2), `purges_performed` resets to 0. The purge cost resets back to 50g instead of properly escalating (50g -> 75g -> 100g...) across the campaign as designed.

#### Defect 3: Double Bonus Gold Grant Bug in `RelicBolsaDoMercador`
- **File**: `godot_project/scripts/run/relics/RelicManager.gd:358-363`
- **Verbatim Code**:
  ```gdscript
  func on_combat_victory(rewards: Dictionary, p_run_state: RunState) -> Dictionary:
      rewards["gold"] = int(rewards.get("gold", 0)) + 10
      if p_run_state != null:
          p_run_state.add_gold(10)
      return rewards
  ```
- **Analysis**: `on_combat_victory` increments `rewards["gold"]` by +10 AND directly calls `p_run_state.add_gold(10)`. When `rewards` is passed into `RewardModal.setup(state, node, rng, rewards)`, `RewardModal._apply_gold_and_relic()` executes:
  ```gdscript
  if offered_gold > 0:
      state.add_gold(offered_gold)
  ```
  This adds the 10 bonus gold TWICE to `RunState.gold` (e.g. 15 base + 10 = 25 offered -> +10 added by relic + 25 added by modal = 35 total instead of 25).

---

### 1.3 Verified Positive Invariants
1. **5-Card Minimum Deck Safety Limit**:
   - `ForgeScreen.MINIMUM_SAFE_DECK_LIMIT = 5` is strictly enforced.
   - Tested in `test_purge_when_deck_has_exactly_5_cards_is_strictly_blocked`, `test_purge_duplicate_cards_removes_single_instance_and_respects_limit`, and `test_deck_minimum_holds_across_multiple_forge_visits`.
   - Purges with 5 or fewer cards are strictly rejected with user message `"Deck mínimo atingido (5 cartas). Segurança da expedição!"`. No gold is spent.
2. **Exact Gold Purchases**:
   - Tested with cards (45g), relics (50g/70g), and purges (50g).
   - In all cases, `state.gold` drops to exactly 0 without negative underflow.
   - Subsequent purchases with 0 gold are cleanly blocked (`0 < cost`).
3. **Negative Gold Protection**:
   - `RunState.spend_gold(-10)` returns `false`.
   - `RunState.add_gold(-10)` returns `false`.
   - `ForgeScreen` with negative gold fails all purchase and purge checks cleanly.
4. **Re-entrancy and Double-Click Protection**:
   - `RewardModal.select_card` and `skip_card` are locked by `is_claimed = true` on the first call. Rapid successive clicks return `false` without duplicate card or gold grants.
   - `RewardModal` rejects injection of unoffered card IDs without locking the modal.
   - `ForgeScreen.buy_card` and `buy_relic` are locked by `slot["sold"] = true`. Rapid double-clicks deduct gold only once.
   - `ForgeScreen.purge_card` is single-use per visit via `purge_used_this_visit = true`.
5. **Catalog & Pool Exhaustion**:
   - When all Elite/Boss relics are owned, `RewardModal` sets `offered_relic_id = ""` without error.
   - When all 10 canonical relics are owned, `ForgeScreen` generates 0 relic slots safely. `buy_relic(0)` returns `false` without out-of-bounds exceptions.
   - Out-of-bounds slot calls (`buy_card(-1)`, `buy_card(99)`) return `false` safely.

---

## 2. Logic Chain

1. **Observation 1.2 (Defect 1)**: Godot emits a `SCRIPT ERROR` at runtime whenever `ForgeScreen.generate_inventory()` executes with `state == null`, due to assigning untyped `[]` to `Array[String]`.
   - *Inference*: Untyped array assignment violates GDScript 2.0 static typing rules and causes noisy engine errors during testing and UI previews.
2. **Observation 1.2 (Defect 2)**: `ForgeScreen` relies on `"card_purges_count" in state` to track cumulative purges across visits, but `RunState` has no such variable declared, causing `"card_purges_count" in state` to always return `false`.
   - *Inference*: The economy anti-abuse mechanic ($50\text{g} + 25\text{g} \times n$) fails to persist across nodes. Every new Forge resets the purge cost to 50g, allowing players to cheaply thin decks at every Forge encounter.
3. **Observation 1.2 (Defect 3)**: `RelicBolsaDoMercador.on_combat_victory` adds 10 gold directly to `run_state.gold` AND adds 10 gold to the `rewards` dictionary which `RewardModal` later awards again.
   - *Inference*: The player receives double bonus gold (20 bonus gold instead of 10) in the integrated post-combat loop.
4. **Challenger 1 Cross-Verification**: Challenger 1 confirmed that 8 of 10 relic strings in `RewardModal.ELITE_RELICS` and `RewardModal.BOSS_RELICS` do not exist in `RelicManager._catalog` (e.g. `pedra_afiar`, `coroa_de_quitina`), preventing players from receiving actual relic instances upon defeating Elite and Boss encounters.
5. **Conclusion**: While core invariants (5-card deck safety, 0 gold handling, double-claim locking) are robust, Milestone M3 exhibits 3 internal economic/runtime bugs plus the critical catalog disconnect identified by Challenger 1. Therefore, Milestone M3 must be revised before proceeding to Milestone M4.

---

## 3. Caveats

- **Tactical Combat Integration**: Tests in this suite focused on `RewardModal`, `ForgeScreen`, `RunState`, and `RelicManager`. Actual tactical grid combat execution belongs to Milestone M4 (`RunCombatBridge`).
- **No Implementation Edits**: Per role constraints as an Empirical Challenger, no production implementation files in `godot_project/scripts/` were modified. All defects were identified and validated through empirical tests in `godot_project/test/unit/test_adversarial_m3.gd`.

---

## 4. Conclusion & Required Changes

**Verdict**: **REQUEST_CHANGES**

The worker must implement the following fixes:

1. **Fix Type Error in `ForgeScreen.gd:176`**:
   Change:
   ```gdscript
   var owned_relics: Array = state.relics if state != null else []
   ```
   Or explicitly type the fallback:
   ```gdscript
   var owned_relics: Array[String] = state.relics if state != null else ([] as Array[String])
   ```
2. **Persist `card_purges_count` on `RunState.gd`**:
   Add `var card_purges_count: int = 0` to `RunState.gd` (around line 45), include it in `to_dict()`, `from_dict()`, and `_reset()`.
3. **Fix Double Gold in `RelicBolsaDoMercador` (`RelicManager.gd:358-363`)**:
   Do NOT call `p_run_state.add_gold(10)` inside `on_combat_victory` if `rewards["gold"]` is also incremented, or clarify that `RewardModal` only receives base gold.
4. **Synchronize `RewardModal` Relics with `RelicManager` Catalog** (concurring with Challenger 1):
   Update `RewardModal.ELITE_RELICS` and `RewardModal.BOSS_RELICS` to use canonical catalog IDs:
   - Elite: `"escudo_ancestral"`, `"dente_da_viuva"`, `"tocha_eterna"`, `"frasco_feromonio"`, `"relogio_da_forja"`
   - Boss: `"martelo_runico"`, `"amuleto_ambar"`, `"oleo_alquimico"`, `"coroa_quitina"`, `"bolsa_do_mercador"`

---

## 5. Verification Method

1. **Run Full Test Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Current state*: 36 scripts, 801 tests passed, 0 failures.
2. **Run Adversarial Suite (Challenger 2)**:
   ```bash
   bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_adversarial_m3.gd
   ```
   *Expected*: 24 tests passed, 0 errors, 0 warnings.
3. **Run Adversarial Suite (Challenger 1)**:
   ```bash
   bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_stress_adversarial.gd
   ```
