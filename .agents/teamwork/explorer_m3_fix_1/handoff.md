# Handoff Report — Milestone M3: Relic ID Normalization & Catalog Synchronization

**Agent**: Remediation Explorer 1 (`explorer_m3_fix_1`)  
**Mission**: Investigate Relic ID normalization and catalog synchronization between RewardModal, ForgeScreen, and RelicManager. Recommend concrete GDScript diffs/replacements.  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_fix_1`  
**Timestamp**: 2026-10-16T02:00:00Z  

---

## 1. Observation

### 1.1 Test Suite & Baseline Execution
- Automated test command: `bash godot_project/run_gut_tests.sh`
- Current status: 36 test scripts executed, 801 tests passed, 0 failures, 8165 assertions passed (Exit code: 0).
- Despite 0 runner failures, diagnostic output from adversarial tests revealed 4 critical defects:
  ```text
  [FINDING] RelicManager permits duplicate relic registration via 'reliquia_' alias! Active count: 2
  [FINDING] Attack damage with double registration: bonus=6, final=12
  [FINDING] RewardModal relics that fail to resolve in RelicManager: ["reliquia_pedra_afiar", "reliquia_armadura_carapaca", "reliquia_moeda_da_sorte", "reliquia_balsamo_cogumelo", "reliquia_pingente_ambar", "reliquia_foco_arcano", "reliquia_cinzas_da_forja", "reliquia_coroa_de_quitina"]
  [FINDING] CRITICAL: 'reliquia_coroa_de_quitina' from RewardModal.BOSS_RELICS cannot be instantiated! (Catalog entry is 'coroa_quitina')
  [FINDING] RelicManager.sync_from_run_state() does not remove relics purged from RunState!
  [FINDING] ForgeScreen offered 'martelo_runico' for sale even though RunState already holds 'reliquia_martelo_runico'!
  ```

### 1.2 Direct Code Observations by Component

#### A. `RewardModal.gd` (lines 60–74)
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
- **Discrepancy 1**: 7 of the 10 strings (`pedra_afiar`, `armadura_carapaca`, `moeda_da_sorte`, `balsamo_cogumelo`, `pingente_ambar`, `foco_arcano`, `cinzas_da_forja`) do not exist in `RelicManager._catalog`.
- **Discrepancy 2**: `reliquia_coroa_de_quitina` contains an inflected preposition typo (`_de_`). `RelicManager` registers `coroa_quitina`. `create_relic("reliquia_coroa_de_quitina")` fails and returns `null`.
- **Discrepancy 3**: In `test_reward_modal.gd:70`, the test previously asserted `assert_true(modal.offered_relic_id.begins_with("reliquia_"))`, masking the fact that the awarded relics were completely unregistered and inert in `RelicManager`.

#### B. `RelicManager.gd` (lines 101–116, 305–330)
```gdscript
func create_relic(relic_id: String) -> RelicData:
	if _catalog.has(relic_id):
		return _catalog[relic_id].call()
	var stripped: String = relic_id.replace("reliquia_", "")
	if _catalog.has(stripped):
		return _catalog[stripped].call()
	return null

func register_relic(relic_id: String) -> bool:
	if relic_id.is_empty() or _active_relics.has(relic_id):
		return false
	var relic: RelicData = create_relic(relic_id)
	...
	_active_relics[relic_id] = relic
```
- In `create_relic`, stripping `"reliquia_"` from `"reliquia_coroa_de_quitina"` yields `"coroa_de_quitina"`, which is not in `_catalog` (registered as `"coroa_quitina"`).
- In `register_relic()`, the key used in `_active_relics[relic_id]` is the unnormalized input string. Calling `register_relic("martelo_runico")` followed by `register_relic("reliquia_martelo_runico")` succeeds twice, activating two instances of `RelicMarteloRunico` and stacking passive bonuses (+6 damage instead of +3).
- In `sync_from_run_state()`, active relics are never pruned when removed from `run_state.relics`.

#### C. `ForgeScreen.gd` (lines 176–181)
```gdscript
var owned_relics: Array[String] = state.relics if state != null else []
var available_relic_ids: Array[String] = []
for rid in CANONICAL_RELICS.keys():
	if not owned_relics.has(rid):
		available_relic_ids.append(rid)
```
- `ForgeScreen` stores canonical IDs without prefix (`"martelo_runico"`).
- If `state.relics` holds `"reliquia_martelo_runico"`, `owned_relics.has("martelo_runico")` evaluates to `false`.
- The Forge shop offers `"martelo_runico"` for sale, allowing duplicate purchase of an already owned relic.

#### D. `RunState.gd` (lines 214–229)
```gdscript
func add_relic(relic_id: String) -> bool:
	if relic_id.is_empty() or relics.has(relic_id):
		return false
	relics.append(relic_id)
	return true
```
- `relics.has(relic_id)` performs exact string matching without alias normalization, allowing `"martelo_runico"` and `"reliquia_martelo_runico"` to coexist in `relics`.

---

## 2. Logic Chain

1. **Premise 1 (Catalog Integrity)**: Post-combat rewards (Elite and Boss nodes) and Forge items must map exclusively to active relics implemented in the project engine.
   - *Evidence (1.2.A, 1.2.B)*: 8 of 10 relics in `RewardModal.gd` fail lookup in `RelicManager._catalog`.
   - *Deduction*: Elite and Boss encounters grant non-functional relics 80% of the time. The 10 canonical relics registered in `RelicManager._register_canonical_catalog()` must be partitioned into the Elite and Boss pools.

2. **Premise 2 (Idempotence & Anti-Stacking)**: A relic's passive benefits must activate exactly once per expedition, regardless of whether it is referred to by canonical ID or prefixed alias.
   - *Evidence (1.2.B, 1.2.C, 1.2.D)*: RelicManager keys on raw input; ForgeScreen checks raw `owned_relics.has()`; RunState adds raw strings.
   - *Deduction*: By introducing a centralized `RelicManager.normalize_id(relic_id: String) -> String` method and calling it in `RelicManager`, `ForgeScreen`, `RewardModal`, and `RunState`, all subsystems operate on canonical identifiers. Aliases (such as `"reliquia_..."` or `"coroa_de_quitina"`) normalize transparently to their canonical form.

3. **Premise 3 (Pool Partitioning)**: The 10 canonical relics have distinct tiers and mechanical impacts:
   - Utility / Defense / Status: `escudo_ancestral` (Broquel), `bolsa_do_mercador` (Moedas), `tocha_eterna` (Sulfeto), `oleo_alquimico` (Incineração), `frasco_feromonio` (Feromônio).
   - High-Tier / Boss / Legendary: `martelo_runico` (Karak-Dur), `amuleto_ambar` (Resinoso), `dente_da_viuva` (Canibal), `coroa_quitina` (Quitina Cristalizada), `relogio_da_forja` (Engrenagem Mestra).
   - *Deduction*: Assigning the first group to `ELITE_RELICS` and the second group to `BOSS_RELICS` ensures 100% catalog coverage, perfect thematic alignment, and zero missing items.

---

## 3. Caveats

- **Explorer Scope Division**: Explorer 2 is responsible for `RelicBolsaDoMercador` single-gold award and `RelicFrascoFeromonio` friendly-unit filtering. Explorer 3 is responsible for `card_purges_count` persistence in `RunState` and typed array safety in `ForgeScreen:176`. This report focuses strictly on Relic ID normalization, catalog synchronization, and anti-duplication mechanisms.
- **Backwards Compatibility**: Tests and save files containing legacy `"reliquia_..."` strings must continue to function without error. The `normalize_id()` function preserves full backwards compatibility while converting storage and runtime maps to canonical identifiers.

---

## 4. Conclusion & Concrete Code Recommendations

### 4.1 Recommended GDScript Changes

#### File 1: `godot_project/scripts/run/relics/RelicManager.gd`

```gdscript
# ── Add Static Normalization Function ─────────────────────────────────────────
## Normalizes relic identifiers: removes leading "reliquia_", handles aliases/typos, and trims whitespace.
static func normalize_id(relic_id: String) -> String:
	var clean: String = relic_id.strip_edges().to_lower()
	if clean.begins_with("reliquia_"):
		clean = clean.substr(9)
	match clean:
		"coroa_de_quitina":
			return "coroa_quitina"
		"pingente_ambar":
			return "amuleto_ambar"
		_:
			return clean

# ── Update create_relic ───────────────────────────────────────────────────────
func create_relic(relic_id: String) -> RelicData:
	var norm: String = normalize_id(relic_id)
	if _catalog.has(norm):
		return _catalog[norm].call()
	if _catalog.has(relic_id):
		return _catalog[relic_id].call()
	return null

# ── Update register_relic ─────────────────────────────────────────────────────
func register_relic(relic_id: String) -> bool:
	var norm_id: String = normalize_id(relic_id)
	if norm_id.is_empty() or _active_relics.has(norm_id):
		return false
	
	var relic: RelicData = create_relic(norm_id)
	if relic == null:
		push_warning("[RelicManager] Relíquia desconhecida: '%s'" % relic_id)
		return false
	
	_active_relics[norm_id] = relic
	if run_state != null:
		if not run_state.has_relic(norm_id):
			run_state.add_relic(norm_id)
		relic.on_registered(run_state)
	
	return true

# ── Update unregister_relic ───────────────────────────────────────────────────
func unregister_relic(relic_id: String) -> bool:
	var norm_id: String = normalize_id(relic_id)
	var target_key: String = norm_id if _active_relics.has(norm_id) else (relic_id if _active_relics.has(relic_id) else "")
	if target_key.is_empty():
		return false
	var relic: RelicData = _active_relics[target_key]
	if run_state != null:
		relic.on_unregistered(run_state)
		run_state.remove_relic(target_key)
		if target_key != norm_id:
			run_state.remove_relic(norm_id)
		if target_key != relic_id:
			run_state.remove_relic(relic_id)
	_active_relics.erase(target_key)
	return true

# ── Update has_relic and get_relic ───────────────────────────────────────────
func get_relic(relic_id: String) -> RelicData:
	var norm_id: String = normalize_id(relic_id)
	if _active_relics.has(norm_id):
		return _active_relics[norm_id]
	return _active_relics.get(relic_id, null)

func has_relic(relic_id: String) -> bool:
	var norm_id: String = normalize_id(relic_id)
	return _active_relics.has(norm_id) or _active_relics.has(relic_id)

# ── Update sync_from_run_state ───────────────────────────────────────────────
func sync_from_run_state() -> void:
	if run_state == null:
		return
	
	# 1. Prune active relics that are no longer present in RunState
	var active_keys: Array = _active_relics.keys()
	for act_key in active_keys:
		var found: bool = false
		for r_id in run_state.relics:
			if normalize_id(r_id) == act_key or r_id == act_key:
				found = true
				break
		if not found:
			var relic: RelicData = _active_relics[act_key]
			relic.on_unregistered(run_state)
			_active_relics.erase(act_key)

	# 2. Register newly acquired relics from RunState
	for r_id in run_state.relics:
		var norm_id: String = normalize_id(r_id)
		if not _active_relics.has(norm_id):
			var relic: RelicData = create_relic(norm_id)
			if relic != null:
				_active_relics[norm_id] = relic
				relic.on_registered(run_state)
```

---

#### File 2: `godot_project/scripts/run/ui/RewardModal.gd`

```gdscript
# ── Replace Dummy Pools with Canonical Relics ────────────────────────────────
const ELITE_RELICS: Array[String] = [
	"escudo_ancestral",
	"bolsa_do_mercador",
	"tocha_eterna",
	"oleo_alquimico",
	"frasco_feromonio"
]

const BOSS_RELICS: Array[String] = [
	"martelo_runico",
	"amuleto_ambar",
	"dente_da_viuva",
	"coroa_quitina",
	"relogio_da_forja"
]

# ── Update setup() Relic ID Selection ────────────────────────────────────────
	# 2. Determinar Relíquia (Garantida em Elite e Boss)
	if p_options.has("relic_id"):
		offered_relic_id = RelicManager.normalize_id(String(p_options["relic_id"]))
	elif ntype == RunNode.NodeType.BOSS:
		offered_relic_id = _select_available_relic(BOSS_RELICS)
	elif ntype == RunNode.NodeType.ELITE:
		offered_relic_id = _select_available_relic(ELITE_RELICS)
	else:
		offered_relic_id = ""

# ── Update refresh_display() Relic Label ─────────────────────────────────────
	if lbl_relic_info != null:
		if not offered_relic_id.is_empty():
			var display_name: String = offered_relic_id.capitalize()
			if ForgeScreen.CANONICAL_RELICS.has(offered_relic_id):
				display_name = String(ForgeScreen.CANONICAL_RELICS[offered_relic_id]["name"])
			lbl_relic_info.text = "💎 Relíquia: %s" % display_name
			lbl_relic_info.visible = true
		else:
			lbl_relic_info.text = ""
			lbl_relic_info.visible = false

# ── Update _apply_gold_and_relic() ───────────────────────────────────────────
		if not offered_relic_id.is_empty():
			var norm_id: String = RelicManager.normalize_id(offered_relic_id)
			var added: bool = state.add_relic(norm_id)
			if added:
				relic_collected.emit(norm_id)
			else:
				# Se já possuía a relíquia, compensa com bônus monetário
				state.add_gold(50)
				gold_collected.emit(50)

# ── Update _select_available_relic() ─────────────────────────────────────────
func _select_available_relic(relic_list: Array[String]) -> String:
	var pool: Array[String] = []
	for r in relic_list:
		var norm_r: String = RelicManager.normalize_id(r)
		if state == null or not state.has_relic(norm_r):
			pool.append(norm_r)

	if pool.is_empty():
		return ""
	var idx: int = rng.randi_range(0, pool.size() - 1) if rng != null else 0
	return pool[idx]
```

---

#### File 3: `godot_project/scripts/run/ui/ForgeScreen.gd`

```gdscript
# ── Update generate_inventory() (Anti-Duplicate Check) ────────────────────────
	# 2. Gerar 2 Relíquias (excluindo relíquias já possuídas pelo jogador)
	var available_relic_ids: Array[String] = []
	for rid in CANONICAL_RELICS.keys():
		var norm_rid: String = RelicManager.normalize_id(rid)
		var already_owned: bool = false
		if state != null:
			for owned in state.relics:
				if RelicManager.normalize_id(owned) == norm_rid:
					already_owned = true
					break
		if not already_owned:
			available_relic_ids.append(rid)

# ── Update buy_relic() (Canonical Storage) ───────────────────────────────────
	var norm_relic_id: String = RelicManager.normalize_id(slot["id"])
	state.spend_gold(cost)
	state.add_relic(norm_relic_id)
	if relic_manager != null and relic_manager.has_method("register_relic"):
		relic_manager.register_relic(norm_relic_id)
	slot["sold"] = true
```

---

#### File 4: `godot_project/scripts/run/RunState.gd`

```gdscript
# ── Update Relic Storage Methods ─────────────────────────────────────────────
func add_relic(relic_id: String) -> bool:
	if relic_id.is_empty() or has_relic(relic_id):
		return false
	var norm: String = RelicManager.normalize_id(relic_id)
	relics.append(norm)
	return true

func has_relic(relic_id: String) -> bool:
	if relics.has(relic_id):
		return true
	var norm: String = RelicManager.normalize_id(relic_id)
	for r in relics:
		if RelicManager.normalize_id(r) == norm:
			return true
	return false

func remove_relic(relic_id: String) -> bool:
	var idx: int = relics.find(relic_id)
	if idx >= 0:
		relics.remove_at(idx)
		return true
	var norm: String = RelicManager.normalize_id(relic_id)
	for i in range(relics.size()):
		if RelicManager.normalize_id(relics[i]) == norm:
			relics.remove_at(i)
			return true
	return false
```

---

#### File 5: Unit Tests Updates

1. **`godot_project/test/unit/test_reward_modal.gd`**:
   - Replace line 70:
     ```gdscript
     assert_true(RewardModal.ELITE_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de elite")
     assert_not_null(RelicManager.new().create_relic(modal.offered_relic_id), "Relíquia pertence ao catálogo canônico de RelicManager")
     ```
   - Update line 85:
     ```gdscript
     assert_true(RewardModal.BOSS_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de chefes")
     assert_not_null(RelicManager.new().create_relic(modal.offered_relic_id), "Relíquia de boss pertence ao catálogo canônico de RelicManager")
     ```

2. **`godot_project/test/unit/test_relic_stress_adversarial.gd`**:
   - In `test_stress_duplicate_registration_with_reliquia_prefix()`:
     ```gdscript
     assert_false(dup_attempt, "Tentativa de registro duplicado com prefixo deve ser rejeitada")
     assert_eq(_manager.get_relic_count(), 1, "Apenas 1 relíquia ativa")
     ```
   - In `test_stress_reward_modal_relic_ids_vs_relic_manager_catalog()`:
     ```gdscript
     assert_eq(unresolvable_relics.size(), 0, "Todas as relíquias de RewardModal devem ser resolvíveis no catálogo")
     ```
   - In `test_stress_coroa_de_quitina_typo_in_reward_modal()`:
     ```gdscript
     assert_not_null(relic, "RelicManager deve resolver 'reliquia_coroa_de_quitina' via normalize_id()")
     assert_eq(relic.id, "coroa_quitina", "ID normalizado é coroa_quitina")
     ```
   - In `test_stress_forge_shop_duplicate_offering_with_prefix_alias()`:
     ```gdscript
     assert_false(offered_martelo, "ForgeScreen não deve ofertar martelo_runico se o jogador já possui reliquia_martelo_runico")
     ```
   - In `test_stress_relic_manager_sync_after_run_state_removal()`:
     ```gdscript
     assert_false(_manager.has_relic("martelo_runico"), "RelicManager deve purgar relíquias removidas do RunState")
     ```

---

## 5. Verification Method

Once the implementer applies the diffs, verify via:

1. **Full GUT Test Suite Execution**:
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Expected Result*: 36 test scripts executed, 801+ tests run, 0 errors, 0 failures, exit code 0.

2. **Specific Adversarial Stress Suite**:
   ```bash
   bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_relic_stress_adversarial.gd
   ```
   *Expected Result*: All 12 stress tests pass with 0 warnings of unresolvable relics or duplicate registration.

3. **Standalone Catalog Consistency Check**:
   Inspect `RewardModal.ELITE_RELICS` and `RewardModal.BOSS_RELICS`. Confirm:
   - Total items across both pools = 10.
   - All 10 items match `CANONICAL_RELICS.keys()` in `ForgeScreen.gd` and `RelicManager._register_canonical_catalog()`.
   - `RelicManager.new().create_relic(id) != null` for every ID in both pools.
