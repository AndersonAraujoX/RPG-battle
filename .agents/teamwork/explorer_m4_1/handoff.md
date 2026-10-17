# Handoff Report — Milestone M4: Combat Bridge & Controller Hook Design

**Date**: 2026-10-16
**Agent**: Explorer M4 (Read-Only Investigator & Software Architect)
**Target Milestone**: M4 — Tactical Combat Bridge, RunMapScreen Transitions, & CercoGameController Hooks

---

## 1. Observation

### 1.1 Existing Architecture & Code Inspection
1. **`RunSession.gd` (`godot_project/scripts/run/RunSession.gd`)**:
   - Lines 8-14: `DEFAULT_PARTY = {"aquele": 30, "stark": 34, "elden": 26}` and `DEFAULT_DECK` (10 starter cards: 3x movimento, 2x trabalho, 2x escavacao, 2x ataque, 1x defesa).
   - Lines 16-29: Static container `RunSession.current: RunState = null`, `has_active_run() -> bool` returning `current != null and current.is_active()`, `start_new(p_seed, party, deck)`, and `clear()`.
   - Acts as the decoupled cross-scene shared container without requiring a new engine Autoload.

2. **`RunState.gd` (`godot_project/scripts/run/RunState.gd`)**:
   - Lines 30-45: Manages `status` (`NOT_STARTED`, `ACTIVE`, `VICTORY`, `DEFEAT`), `heroes`, `hero_hp`, `hero_max_hp`, `fallen_heroes`, `deck`, `relics`, `gold`, `current_node_id`, `map`, `floors_cleared`, `bosses_defeated`, `enemies_killed`.
   - Lines 111-131: `move_to(node_id)` transitions to an available node and emits `node_entered(node)`. `complete_current_node()` marks node visited, increments `floors_cleared`, and if `node.is_boss()` invokes `_on_boss_defeated()` (advances `act` and heals 25% or triggers `VICTORY`).
   - Lines 157-172: `damage_hero(hero_id, amount)` clamps HP to 0. If HP reaches 0, appends to `fallen_heroes`, emits `hero_died(hero_id)`, and if `get_living_heroes().is_empty()` sets `status = Status.DEFEAT` and emits `run_ended(false)`.
   - Lines 175-181: `heal_hero(hero_id, amount)`: dead heroes in `fallen_heroes` cannot be healed (**Permadeath strictly preserved**).

3. **`RunNode.gd` (`godot_project/scripts/run/RunNode.gd`)**:
   - Lines 8-18: `enum NodeType { COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS }`.
   - Lines 52-57: `is_boss() -> bool` checks `type == NodeType.BOSS`. `is_combat_type() -> bool` returns `type in [NodeType.COMBAT, NodeType.ELITE, NodeType.SIEGE, NodeType.BOSS]`.

4. **`RunMapScreen.gd` (`godot_project/scripts/run/RunMapScreen.gd`)**:
   - Lines 280-302: `_on_node_pressed(node_id: int)`:
     ```gdscript
     var moved: bool = state.move_to(node_id)
     if not moved:
         return
     var target_node: RunNode = state.get_current_node()
     node_selected.emit(target_node)
     # 2. Resolver o nó (Placeholder M1/M2; M4 invocará combate tático no tabuleiro)
     var outcome: Dictionary = resolver.resolve(state, rng)
     ```
   - Currently auto-resolves combats through `resolver.resolve(state, rng)` placeholder.

5. **`CercoGameController.gd` (`godot_project/scripts/main/CercoGameController.gd`)**:
   - Lines 40-60: Hardcoded initialization of 3 units in `_initialize_models()`:
     - `board.place_unit("aquele", Vector2i(9, 10))` (Guerreiro, 48 HP, AC 17, Move 4, Atk 4)
     - `board.place_unit("stark", Vector2i(10, 9))` (Paladino, 52 HP, AC 18, Move 3, Atk 3)
     - `board.place_unit("lysander", Vector2i(10, 11))` (Comandante, 36 HP, AC 14, Move 3, Atk 5)
   - Lines 65-68: Builds standalone starter deck: `deck.build_starter_deck()`, `deck.populate_default_market()`, `deck.draw_cards(5)`.
   - Lines 290-369: `spawn_enemy_wave(wave_num: int)`: generates wave definitions using `threat_deck.generate_wave(wave_num)`.
   - Lines 906-953: `check_game_over_conditions()` checks:
     - Defeat: all team "A" heroes dead.
     - Defeat: 3+ team "B" units in `ZONE_CAMARA_CENTRAL`.
     - Victory: `current_round > max_rounds` and living enemies list is empty.
   - Lines 956-1009: `trigger_game_over(victory: bool, reason: String)`: displays `GameOverModal`, where Restart reloads scene and Menu routes to `res://scenes/main/Menu.tscn`.

6. **Milestone M3 Assets (`RewardModal.gd`, `ForgeScreen.gd`, `RelicManager.gd`)**:
   - `RewardModal.gd`: Post-combat modal presenting 3 cards based on Act, gold collection from `NODE_GOLD_TABLE`, guaranteed relics for Elite/Boss from `ELITE_RELICS` and `BOSS_RELICS`, and skip card button. Emits `reward_completed(summary)`.
   - `RelicManager.gd`: Subscribes to `EventBus` (`unit_damaged`, `unit_attacked`, `unit_died`, `card_played`, `turn_changed`) and applies modifiers to `RunState`.

7. **Baseline GUT Test Verification**:
   - Tool command: `bash godot_project/run_gut_tests.sh`
   - Result: 36 test scripts executed, 808 tests run, 808 tests passed, 0 failures, 8203 assertions passed, exit code 0.

---

## 2. Logic Chain

### 2.1 The Need for `RunCombatBridge.gd`
- **Fact**: `RunState` is a pure data model (`RefCounted`) containing expedition-wide persistent stats (party, current HP, deck, relics).
- **Fact**: `CercoGameController` is a `Node2D` game scene controller designed for standalone Cerco matches on a 20x20 grid with `FortressBoard`, `CercoDeck`, and `ThreatDeck`.
- **Deduction**: Directly importing `CercoGameController` into `RunMapScreen` or vice-versa would tightly couple the scenes and introduce circular dependencies. A dedicated mediator (`RunCombatBridge.gd`, `RefCounted`) cleanly bridges the contract:
  1. `setup_combat(run_state: RunState, node: RunNode) -> Dictionary`: Prepares the encounter, maps surviving heroes, filters out dead heroes, converts card strings to `CardData`, sets up wave budgets, and caches the active combat descriptor.
  2. `sync_combat_result(run_state: RunState, result: Dictionary) -> Dictionary`: Extracts final HP from `FortressBoard`, applies delta damages to `RunState.damage_hero`, checks permadeath, records kills and gold, and completes the current node.

### 2.2 Preserving Standalone Cerco Mode (Zero Regressions)
- **Fact**: Existing GUT test suites (`test_all_card_abilities.gd`, `test_board_tactics_items.gd`, `test_cerco_hud.gd`, `test_cerco_screens.gd`, `test_enemy_advance_and_sprites.gd`, `test_game_over_system.gd`) instantiate `CercoGameController.new()` directly without an active run (`RunSession.has_active_run() == false`).
- **Deduction**: `CercoGameController._initialize_models()` must execute a strict branch:
  - If `RunSession.has_active_run()`: execute `_setup_from_run_session()`.
  - Else: execute `_setup_standalone_cerco()`.
- **Result**: All 808 baseline tests will remain 100% green with zero modification to standalone semantics.

### 2.3 Permadeath & Hero Persistence Mechanics
- **Fact**: In a roguelike run, if Stark died in floor 2, he is recorded in `RunState.fallen_heroes` and `RunState.hero_hp["stark"] == 0`.
- **Deduction**: When `_setup_from_run_session()` places units on `FortressBoard`:
  - It iterates only through `run_state.get_living_heroes()`.
  - Fallen heroes are completely excluded from `board.place_unit()` and `board.register_unit()`.
  - Living heroes start with `hp = run_state.hero_hp[hero_id]` and `max_hp = run_state.hero_max_hp[hero_id]`.
  - During battle, whenever an ally takes damage, their final HP at battle conclusion is passed to `sync_combat_result()`. Any hero ending at 0 HP is committed to `fallen_heroes`.

### 2.4 Deck Ingestion
- **Fact**: `RunState.deck` is an `Array[String]` containing card IDs (e.g. `["movimento", "movimento", "trabalho", "escavacao", "ataque", "golpe_pesado"]`), whereas `CercoDeck` expects `Array[CardData]`.
- **Deduction**: `RunCombatBridge` must provide a canonical converter `card_id_to_card_data(card_id: String) -> CardData` supporting:
  - Base starter cards: `movimento` / `marcha`, `trabalho`, `escavacao`, `ataque` / `combate`, `defesa`.
  - Reward & Forge cards: all IDs defined in `RewardModal.CARD_POOLS` and `ForgeScreen.CARD_PRICES`.
  - Fallback generic card for any unrecognized ID.
- In `_setup_from_run_session()`, `deck.draw_pile` is populated with the converted cards and shuffled before drawing the starting hand of 5.

### 2.5 Encounter Generation by Node Type & Act (`CombatEncounterGenerator.gd`)
- **Fact**: `RunNode.NodeType` differentiates `COMBAT`, `ELITE`, `SIEGE`, `BOSS`, and `RunState.act` ranges from 1 to 3.
- **Deduction**: `ThreatDeck` already has `set_forced_waves(waves: Array[Dictionary])`. By generating structured wave dictionaries with canonical castes from `IsectumCastes.gd`:
  - **Act I**: Tier 1 castes (`zangao_invasor`, `soldado_mandibula`, `formiga_acida`, `besouro_rinoceronte`).
    - `COMBAT`: 3 skirmish waves, max 3 rounds.
    - `ELITE`: 2 heavy waves with `escaravelho_couracado` and `besouro_rinoceronte`.
    - `SIEGE`: 4 defensive waves attacking North, South, East, West.
    - `BOSS`: `viuva_canibal` (`tece_teia`) + necrotic brood.
  - **Act II**: Tier 2 castes (`vespa_furtiva`, `louva_deus_ceifador`, `aranha_saltadora`, `libelula_bombardeira`, `cigarra_ressonante`, `rainha_do_enxame`).
  - **Act III**: Tier 3 castes (`colosso_isectum`, `rei_isectum`, Hive Hearts).

### 2.6 Return Transition & Reward Modal Integration
- **Fact**: M3 implemented `RewardModal.tscn` / `RewardModal.gd` for post-combat drafts.
- **Deduction**: In `CercoGameController.trigger_game_over(victory: bool, reason: String)`:
  - If in run mode and `victory == true`:
    - Synchronize combat result to `RunState`.
    - Instantiate `RewardModal` on top of the HUD.
    - Connect `reward_modal.reward_completed`:
      - If Act 3 Boss defeated (`run_state.status == VICTORY`): routes to `GameOver.tscn` (Epilogue/Victory).
      - Otherwise: routes back to `res://scenes/run/RunMapScreen.tscn`.
  - If in run mode and `victory == false`:
    - Synchronize combat result to `RunState` (marks expedition defeat).
    - Display GameOver overlay with Amber, floors cleared, and enemies defeated.

---

## 3. Caveats

1. **Scene Tree Availability in Headless Unit Tests**:
   - In GUT unit tests, controllers and screens are often tested without an active scene tree (`is_inside_tree() == false`, `get_tree() == null`).
   - All transition methods must guard `get_tree() != null` and allow fallback resolution or programmatic callbacks when running headless.
2. **Boss Multicell Footprint (Marcos M5/M6)**:
   - Act I (`viuva_canibal`) uses a single 1x1 tile (`tece_teia`). Multi-tile 3x3 footprint for `rei_isectum` is scoped for Milestone M6 and must not block M4.
3. **Mid-Combat Save / Resume**:
   - Roguelike state is saved between nodes on the map (`RunState.to_dict()`). Combat matches themselves are self-contained tactical skirmishes that resolve to completion within a single session.

---

## 4. Conclusion & Technical Design

### 4.1 Specification of `godot_project/scripts/run/combat/RunCombatBridge.gd`

```gdscript
# res://scripts/run/combat/RunCombatBridge.gd
class_name RunCombatBridge
extends RefCounted

## RunCombatBridge: Mediator connecting RunSession / RunState to CercoGameController.
## Handles combat setup, hero stats mapping, deck conversion, and battle outcome synchronization.

const DEFAULT_HERO_POSITIONS: Array[Vector2i] = [
	Vector2i(9, 10),  # Courtyard West
	Vector2i(10, 9),  # Courtyard North
	Vector2i(10, 11), # Courtyard South
]

static var _current_encounter: Dictionary = {}
static var _last_result: Dictionary = {}

static func has_active_encounter() -> bool:
	return not _current_encounter.is_empty()

static func get_current_encounter() -> Dictionary:
	return _current_encounter.duplicate(true)

static func clear_encounter() -> void:
	_current_encounter.clear()

## 1. Sets up combat encounter parameters from RunState and RunNode
static func setup_combat(run_state: RunState, node: RunNode) -> Dictionary:
	if run_state == null or node == null or not run_state.is_active():
		push_error("[RunCombatBridge] Invalid run state or node for combat setup")
		return {}

	var living: Array[String] = run_state.get_living_heroes()
	if living.is_empty():
		push_error("[RunCombatBridge] No living heroes to enter combat")
		return {}

	var party_data: Array[Dictionary] = []
	for i in range(living.size()):
		var hid: String = living[i]
		var cur_hp: int = int(run_state.hero_hp.get(hid, 1))
		var max_hp: int = int(run_state.hero_max_hp.get(hid, cur_hp))
		var pos: Vector2i = DEFAULT_HERO_POSITIONS[i] if i < DEFAULT_HERO_POSITIONS.size() else Vector2i(9 + i, 10)
		var hero_info: Dictionary = get_hero_battle_stats(hid, cur_hp, max_hp)
		hero_info["spawn_pos"] = pos
		party_data.append(hero_info)

	var waves: Array[Dictionary] = CombatEncounterGenerator.generate_encounter(node, run_state.act)
	var max_rounds: int = 3
	match node.type:
		RunNode.NodeType.COMBAT: max_rounds = 3
		RunNode.NodeType.ELITE: max_rounds = 4
		RunNode.NodeType.SIEGE: max_rounds = 5
		RunNode.NodeType.BOSS: max_rounds = 5

	var encounter: Dictionary = {
		"is_run_combat": true,
		"node_id": node.id,
		"node_type": node.type,
		"act": run_state.act,
		"floor": node.floor_index,
		"is_boss": node.is_boss(),
		"boss_id": run_state.get_current_boss_id() if node.is_boss() else "",
		"party": party_data,
		"living_heroes": living,
		"fallen_heroes": run_state.fallen_heroes.duplicate(),
		"deck_ids": run_state.deck.duplicate(),
		"relics": run_state.relics.duplicate(),
		"max_rounds": max_rounds,
		"forced_waves": waves,
		"gold_reward": RewardModal.NODE_GOLD_TABLE.get(node.type, 15)
	}

	_current_encounter = encounter.duplicate(true)
	return _current_encounter

## 2. Synchronizes combat results back into RunState
static func sync_combat_result(run_state: RunState, result: Dictionary) -> Dictionary:
	if run_state == null or result.is_empty():
		return {}

	var victory: bool = bool(result.get("victory", false))
	var final_hps: Dictionary = result.get("hero_hp", {})
	var kills: int = int(result.get("enemies_killed", 0))
	var gold_loot: int = int(result.get("gold_collected", 0))

	# 1. Synchronize Hero HP & Permadeath
	for hid in run_state.heroes:
		if final_hps.has(hid):
			var final_hp: int = int(final_hps[hid])
			var prev_hp: int = int(run_state.hero_hp.get(hid, 0))
			if final_hp < prev_hp:
				run_state.damage_hero(hid, prev_hp - final_hp)
			elif final_hp > prev_hp:
				run_state.heal_hero(hid, final_hp - prev_hp)

			if final_hp <= 0 and not run_state.fallen_heroes.has(hid):
				run_state.fallen_heroes.append(hid)
				run_state.hero_died.emit(hid)

	# 2. Register Kills and Gold Loot
	if kills > 0:
		run_state.register_kills(kills)
	if gold_loot > 0:
		run_state.add_gold(gold_loot)

	# 3. Handle Victory / Defeat Node Completion
	if victory:
		run_state.complete_current_node()
	else:
		if run_state.is_active():
			run_state.status = RunState.Status.DEFEAT
			run_state.run_ended.emit(false)

	_last_result = result.duplicate(true)
	clear_encounter()

	return {
		"victory": victory,
		"status": run_state.status,
		"living_heroes": run_state.get_living_heroes(),
		"fallen_heroes": run_state.fallen_heroes.duplicate(),
		"hero_hp": run_state.hero_hp.duplicate(),
		"gold": run_state.gold,
		"amber": run_state.calculate_amber(),
		"act": run_state.act
	}

## 3. Converts string card IDs from RunState.deck to CardData instances for CercoDeck
static func convert_deck(card_ids: Array[String]) -> Array[CardData]:
	var cards: Array[CardData] = []
	for cid in card_ids:
		cards.append(card_id_to_card_data(cid))
	return cards

static func card_id_to_card_data(card_id: String) -> CardData:
	var c: CardData = CardData.new()
	c.id = card_id
	var clean: String = card_id.to_lower().strip_edges()

	# Match standard starter types
	if clean.begins_with("movimento") or clean.begins_with("marcha"):
		c.card_name = "Marcha"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_MARCHA
		c.movement = 15
		c.effect_value = 15
		c.description = "+15 Movimento"
		return c

	if clean.begins_with("trabalho"):
		c.card_name = "Trabalho"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_TRABALHO
		c.work = 3
		c.effect_value = 3
		c.description = "+3 Trabalho"
		return c

	if clean.begins_with("escavacao"):
		c.card_name = "Escavação"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_ESCAVACAO
		c.excavation = 4
		c.effect_value = 4
		c.description = "+4 Escavação"
		return c

	if clean.begins_with("ataque") or clean.begins_with("combate") or clean.begins_with("forca_ana"):
		c.card_name = "Força Anã"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_COMBATE
		c.work = 4
		c.movement = 15
		c.effect_value = 4
		c.description = "+15 Mov +4 Trab / Combate"
		return c

	if clean.begins_with("defesa") or clean.begins_with("bloqueio"):
		c.card_name = "Bloqueio"
		c.card_type = CardData.TYPE_DEFESA
		c.badge = CardData.BADGE_COMBATE
		c.effect_value = 5
		c.description = "+5 Defesa / Armadura"
		return c

	# Check Forge & Reward catalog entries
	if ForgeScreen.CARD_PRICES.has(clean):
		var info: Dictionary = ForgeScreen.CARD_PRICES[clean]
		c.card_name = str(info.get("name", clean.capitalize()))
		c.badge = str(info.get("badge", CardData.BADGE_COMBATE))
		c.description = str(info.get("desc", ""))
		c.cost_wood = int(info.get("cost", 50))
		return c

	# Fallback Card
	c.card_name = clean.capitalize()
	c.card_type = CardData.TYPE_ACAO
	c.badge = CardData.BADGE_COMBATE
	c.effect_value = 3
	c.description = "Ação tática de combate"
	return c

## 4. Maps hero IDs to unit registration dictionaries
static func get_hero_battle_stats(hero_id: String, cur_hp: int, max_hp: int) -> Dictionary:
	var clean: String = hero_id.to_lower().strip_edges()
	var base_data: Dictionary = {
		"id": clean,
		"name": clean.capitalize(),
		"team": "A",
		"hp": cur_hp,
		"max_hp": max_hp,
		"ac": 15,
		"move_range": 3,
		"attack_range": 1,
		"attack_bonus": 3,
		"is_alive": cur_hp > 0
	}

	match clean:
		"aquele":
			base_data["name"] = "Aquele"
			base_data["class"] = "Guerreiro"
			base_data["ac"] = 17
			base_data["move_range"] = 4
			base_data["attack_bonus"] = 4
		"stark":
			base_data["name"] = "Stark"
			base_data["class"] = "Paladino"
			base_data["ac"] = 18
			base_data["move_range"] = 3
			base_data["attack_bonus"] = 3
		"elden":
			base_data["name"] = "Elden"
			base_data["class"] = "Clérigo"
			base_data["ac"] = 16
			base_data["move_range"] = 3
			base_data["attack_range"] = 2
			base_data["attack_bonus"] = 4
		"lysander":
			base_data["name"] = "Pr. Lysander"
			base_data["class"] = "Comandante"
			base_data["ac"] = 14
			base_data["move_range"] = 3
			base_data["attack_range"] = 2
			base_data["attack_bonus"] = 5

	return base_data
```

---

### 4.2 Specification of `CombatEncounterGenerator.gd`

```gdscript
# res://scripts/run/combat/CombatEncounterGenerator.gd
class_name CombatEncounterGenerator
extends RefCounted

## Generates structured wave threat lists for ThreatDeck based on Act and RunNode.NodeType.

static func generate_encounter(node: RunNode, act: int) -> Array[Dictionary]:
	var waves: Array[Dictionary] = []
	var ntype: int = node.type if node != null else RunNode.NodeType.COMBAT

	match act:
		1:
			waves = _generate_act_1_encounter(ntype)
		2:
			waves = _generate_act_2_encounter(ntype)
		3:
			waves = _generate_act_3_encounter(ntype)
		_:
			waves = _generate_act_1_encounter(ntype)

	return waves

static func _generate_act_1_encounter(ntype: int) -> Array[Dictionary]:
	var waves: Array[Dictionary] = []
	match ntype:
		RunNode.NodeType.COMBAT:
			waves.append(_threat("wave_1", ThreatDeck.TYPE_SPAWN_WAVE, "Batedores Isectum", IsectumCastes.ID_ZANGAO_INVASOR, 2, FortressBoard.ZONE_SPAWN_NORTE, 1, 4))
			waves.append(_threat("wave_2", ThreatDeck.TYPE_SPAWN_WAVE, "Vanguarda Mandíbula", IsectumCastes.ID_SOLDADO_MANDIBULA, 1, FortressBoard.ZONE_SPAWN_LESTE, 2, 6))
			waves.append(_threat("wave_3", ThreatDeck.TYPE_SPAWN_WAVE, "Sapa de Muralha", IsectumCastes.ID_OPERARIO_ESCAVADOR, 1, FortressBoard.ZONE_SPAWN_SUL, 3, 5))
		RunNode.NodeType.ELITE:
			waves.append(_threat("elite_w1", ThreatDeck.TYPE_SPAWN_WAVE, "Couraçados Isectum", IsectumCastes.ID_ESCARAVELHO_COURACADO, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 6))
			waves.append(_threat("elite_w2", ThreatDeck.TYPE_BOSS_ASSAULT, "Investida Brutamontes", IsectumCastes.ID_BESOURO_RINOCERONTE, 1, FortressBoard.ZONE_SPAWN_SUL, 2, 8))
		RunNode.NodeType.SIEGE:
			waves.append(_threat("siege_w1", ThreatDeck.TYPE_SPAWN_WAVE, "Enxame Norte", IsectumCastes.ID_ZANGAO_INVASOR, 2, FortressBoard.ZONE_SPAWN_NORTE, 1, 4))
			waves.append(_threat("siege_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Sapa Sul", IsectumCastes.ID_OPERARIO_ESCAVADOR, 2, FortressBoard.ZONE_SPAWN_SUL, 2, 6))
			waves.append(_threat("siege_w3", ThreatDeck.TYPE_SPAWN_WAVE, "Flanco Leste", IsectumCastes.ID_FORMIGA_ACIDA, 1, FortressBoard.ZONE_SPAWN_LESTE, 3, 5))
			waves.append(_threat("siege_w4", ThreatDeck.TYPE_SPAWN_WAVE, "Invasão Oeste", IsectumCastes.ID_SOLDADO_MANDIBULA, 2, FortressBoard.ZONE_SPAWN_OESTE, 4, 6))
		RunNode.NodeType.BOSS:
			waves.append(_threat("boss_w1", ThreatDeck.TYPE_BOSS_ASSAULT, "🕷️ A Viúva Canibal Emerge", IsectumCastes.ID_TECE_TEIA, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 10))
			waves.append(_threat("boss_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Crias Necróticas", IsectumCastes.ID_LARVA_NECROTICA, 2, FortressBoard.ZONE_SPAWN_LESTE, 2, 4))
			waves.append(_threat("boss_w3", ThreatDeck.TYPE_SPAWN_WAVE, "Enxame Protetor", IsectumCastes.ID_ZANGAO_INVASOR, 2, FortressBoard.ZONE_SPAWN_SUL, 3, 6))
	return waves

static func _generate_act_2_encounter(ntype: int) -> Array[Dictionary]:
	var waves: Array[Dictionary] = []
	match ntype:
		RunNode.NodeType.BOSS:
			waves.append(_threat("boss_a2", ThreatDeck.TYPE_BOSS_ASSAULT, "👑 A Rainha do Enxame", IsectumCastes.ID_RAINHA_DO_ENXAME, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 12))
			waves.append(_threat("boss_a2_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Ninhada Alada", IsectumCastes.ID_VESPA_FURTIVA, 2, FortressBoard.ZONE_SPAWN_SUL, 2, 6))
		RunNode.NodeType.ELITE:
			waves.append(_threat("elite_a2", ThreatDeck.TYPE_BOSS_ASSAULT, "🦗 Cigarra Ressonante", IsectumCastes.ID_GRILO_ATORDOANTE, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 8))
			waves.append(_threat("elite_a2_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Ceifadores", IsectumCastes.ID_LOUVA_DEUS_CEIFADOR, 1, FortressBoard.ZONE_SPAWN_LESTE, 2, 6))
		_:
			waves.append(_threat("a2_w1", ThreatDeck.TYPE_SPAWN_WAVE, "Predadores Alados", IsectumCastes.ID_VESPA_FURTIVA, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 4))
			waves.append(_threat("a2_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Ceifadores Subterrâneos", IsectumCastes.ID_LOUVA_DEUS_CEIFADOR, 1, FortressBoard.ZONE_SPAWN_SUL, 2, 6))
	return waves

static func _generate_act_3_encounter(ntype: int) -> Array[Dictionary]:
	var waves: Array[Dictionary] = []
	match ntype:
		RunNode.NodeType.BOSS:
			waves.append(_threat("boss_a3", ThreatDeck.TYPE_BOSS_ASSAULT, "👑 REI ISECTUM (Trono de Âmbar)", IsectumCastes.ID_COLOSSO_ISECTUM, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 15))
		RunNode.NodeType.ELITE:
			waves.append(_threat("elite_a3", ThreatDeck.TYPE_BOSS_ASSAULT, "Coração da Colmeia", IsectumCastes.ID_COLOSSO_ISECTUM, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 10))
		_:
			waves.append(_threat("a3_w1", ThreatDeck.TYPE_SPAWN_WAVE, "Guarda Real", IsectumCastes.ID_ESCARAVELHO_COURACADO, 1, FortressBoard.ZONE_SPAWN_NORTE, 1, 6))
			waves.append(_threat("a3_w2", ThreatDeck.TYPE_SPAWN_WAVE, "Colossos Rastejantes", IsectumCastes.ID_CENTOPEIA_VENENOSA, 1, FortressBoard.ZONE_SPAWN_SUL, 2, 7))
	return waves

static func _threat(p_id: String, p_type: String, p_title: String, p_caste_id: String, p_count: int, p_zone: String, p_round: int, p_cost: int) -> Dictionary:
	return {
		"id": p_id,
		"card_type": p_type,
		"title": p_title,
		"caste_id": p_caste_id,
		"count": p_count,
		"target_zone": p_zone,
		"round": p_round,
		"threat_cost": p_cost,
		"status": ThreatDeck.STATUS_ACTIVE,
		"description": "%s: %d unidade(s) atacando %s." % [p_title, p_count, p_zone]
	}
```

---

### 4.3 `RunMapScreen.gd` Integration Specification

In `godot_project/scripts/run/RunMapScreen.gd`:

```gdscript
func _on_node_pressed(node_id: int) -> void:
	if state == null or not state.can_move_to(node_id):
		return

	# 1. Mover heróis para o nó
	var moved: bool = state.move_to(node_id)
	if not moved:
		return

	var target_node: RunNode = state.get_current_node()
	node_selected.emit(target_node)

	# 2. Se for nó de combate (COMBAT, ELITE, SIEGE, BOSS), transiciona para Main.tscn
	if target_node.is_combat_type():
		_transition_to_combat_node(target_node)
		return

	# 3. Resolver nó não-combate (Fogueira, Evento, etc.)
	var outcome: Dictionary = resolver.resolve(state, rng)

	# 4. Exibir feedback no log
	if log_label != null:
		var text: String = "\n".join(outcome.get("log", []))
		log_label.text = "[color=#ffd700]▶ %s:[/color]\n%s" % [target_node.get_type_name().to_upper(), text]

	refresh_ui()

func _transition_to_combat_node(target_node: RunNode) -> void:
	# Prepara dados do combate no bridge
	RunCombatBridge.setup_combat(state, target_node)

	if log_label != null:
		log_label.text = "[color=#ffd700]▶ ENTRANDO EM COMBATE: %s[/color]\nPreparando tabuleiro tático da Fortaleza..." % target_node.get_type_name().to_upper()

	var tree: SceneTree = get_tree()
	if tree != null:
		if tree.root.has_node("GameManager"):
			var gm: Node = tree.root.get_node("GameManager")
			if gm.has_method("change_state_and_scene"):
				gm.change_state_and_scene(GameManager.GameState.COMBATE_TATICO)
				return
		tree.change_scene_to_file("res://scenes/main/Main.tscn")
	else:
		# Fallback headless para testes GUT sem SceneTree
		if resolver != null:
			var outcome: Dictionary = resolver.resolve(state, rng)
			if log_label != null:
				var text: String = "\n".join(outcome.get("log", []))
				log_label.text = "[color=#ffd700]▶ %s:[/color]\n%s" % [target_node.get_type_name().to_upper(), text]
			refresh_ui()
```

---

### 4.4 `CercoGameController.gd` Hooks Specification

In `godot_project/scripts/main/CercoGameController.gd`:

1. **State properties**:
   ```gdscript
   var is_run_mode: bool = false
   var run_state_ref: RunState = null
   var current_node_ref: RunNode = null
   var encounter_config: Dictionary = {}
   ```

2. **Hook in `_initialize_models()`**:
   ```gdscript
   func _initialize_models() -> void:
       board = FortressBoard.new()
       if not board.wall_breached.is_connected(_on_wall_breached_event):
           board.wall_breached.connect(_on_wall_breached_event)

       board.spawn_default_map_items()

       if RunSession.has_active_run():
           _setup_from_run_session()
       else:
           _setup_standalone_cerco()
   ```

3. **`_setup_standalone_cerco()`**:
   - Retains the exact lines 41-88 as currently written (places aquele, stark, lysander, builds starter deck, reads difficulty from `cerco_config`).

4. **`_setup_from_run_session()`**:
   ```gdscript
   func _setup_from_run_session() -> void:
       is_run_mode = true
       run_state_ref = RunSession.current
       current_node_ref = run_state_ref.get_current_node()

       if RunCombatBridge.has_active_encounter():
           encounter_config = RunCombatBridge.get_current_encounter()
       else:
           encounter_config = RunCombatBridge.setup_combat(run_state_ref, current_node_ref)

       # 1. Spawn only LIVING heroes (Permadeath enforcement)
       var party_list: Array = encounter_config.get("party", [])
       for h_info in party_list:
           var hid: String = str(h_info.get("id", ""))
           var pos: Vector2i = h_info.get("spawn_pos", Vector2i(9, 10))
           board.place_unit(hid, pos)
           board.register_unit(hid, h_info)

       # 2. Economy
       economy = WorkshopEconomy.new()
       economy.set_resources(15, 12, 10, 5, 4)

       # 3. Deck Ingestion from RunState.deck
       deck = CercoDeck.new()
       var deck_ids: Array[String] = []
       for cid in encounter_config.get("deck_ids", []):
           deck_ids.append(String(cid))
       var cards: Array[CardData] = RunCombatBridge.convert_deck(deck_ids)
       deck.draw_pile.append_array(cards)
       deck.draw_pile.shuffle()
       deck.populate_default_market()
       deck.draw_cards(5)

       judge = CercoCombatJudge.new()
       sync_round = CercoSyncRound.new()
       threat_deck = ThreatDeck.new()

       # 4. Wave & Round Configuration
       max_rounds = int(encounter_config.get("max_rounds", 3))
       if encounter_config.has("forced_waves"):
           var f_waves: Array[Dictionary] = []
           for w in encounter_config["forced_waves"]:
               f_waves.append(Dictionary(w))
           threat_deck.set_forced_waves(f_waves)
   ```

5. **Hook in `trigger_game_over(victory: bool, reason: String)`**:
   ```gdscript
   func trigger_game_over(victory: bool, reason: String) -> void:
       if is_game_over:
           return
       is_game_over = true

       # Collect final HP of heroes on board
       var final_hero_hp: Dictionary = {}
       for hid in board.get_units_by_team("A"):
           var udata: Dictionary = board.get_unit_data(hid)
           final_hero_hp[hid] = int(udata.get("hp", 0))

       var combat_result: Dictionary = {
           "victory": victory,
           "reason": reason,
           "hero_hp": final_hero_hp,
           "enemies_killed": enemies_defeated_count,
           "rounds_survived": mini(current_round, max_rounds),
           "gold_collected": economy.crystal if economy != null else 0
       }

       if is_run_mode and run_state_ref != null:
           RunCombatBridge.sync_combat_result(run_state_ref, combat_result)
           _handle_run_game_over(victory, reason, combat_result)
       else:
           _handle_standalone_game_over(victory, reason)
   ```

6. **`_handle_run_game_over(victory: bool, reason: String, combat_result: Dictionary)`**:
   ```gdscript
   func _handle_run_game_over(victory: bool, reason: String, _result: Dictionary) -> void:
       if not victory:
           # Defeat: Present Game Over with Amber / Run Stats
           _show_game_over_modal(false, reason)
           return

       # Victory: Present M3 RewardModal
       var reward_scene: PackedScene = load("res://scenes/run/RewardModal.tscn")
       var reward_modal: RewardModal = null
       if reward_scene != null:
           reward_modal = reward_scene.instantiate() as RewardModal
       else:
           reward_modal = RewardModal.new()

       reward_modal.setup(run_state_ref, current_node_ref)
       reward_modal.reward_completed.connect(func(_summary):
           var tree: SceneTree = get_tree()
           if tree != null:
               if run_state_ref.status == RunState.Status.VICTORY:
                   # Defeated Act 3 Final Boss
                   tree.change_scene_to_file("res://scenes/main/GameOver.tscn")
               else:
                   tree.change_scene_to_file("res://scenes/run/RunMapScreen.tscn")
       )

       if hud_instance != null:
           hud_instance.add_child(reward_modal)
       else:
           add_child(reward_modal)
   ```

---

## 5. Verification Method

### 5.1 Independent Test Suite Verification (Arrange-Act-Assert)
Create `godot_project/test/unit/test_run_combat_bridge.gd` covering:
1. `test_setup_combat_extracts_party_hp_deck_and_waves()`:
   - **Arrange**: Initialize `RunState` with party `{"aquele": 30, "stark": 20}`, deck `["marcha", "trabalho"]`.
   - **Act**: Call `RunCombatBridge.setup_combat(state, combat_node)`.
   - **Assert**: Verify party count is 2, HP matches `RunState`, rounds equal 3, and forced waves are non-empty.
2. `test_setup_combat_enforces_permadeath()`:
   - **Arrange**: Damage `stark` to 0 HP (`state.damage_hero("stark", 20)`).
   - **Act**: Call `RunCombatBridge.setup_combat(state, combat_node)`.
   - **Assert**: Verify `stark` is NOT in `encounter["living_heroes"]` and NOT in `encounter["party"]`.
3. `test_sync_combat_result_updates_hp_and_records_death()`:
   - **Arrange**: Hero `aquele` starts with 30 HP.
   - **Act**: Call `RunCombatBridge.sync_combat_result(state, {"victory": true, "hero_hp": {"aquele": 12}, "enemies_killed": 4})`.
   - **Assert**: `state.hero_hp["aquele"] == 12`, `state.enemies_killed == 4`, node marked `visited`.
4. `test_cerco_game_controller_standalone_when_no_run()`:
   - **Arrange**: `RunSession.clear()`.
   - **Act**: `var controller = autofree(CercoGameController.new())`.
   - **Assert**: `controller.is_run_mode == false`, default heroes `aquele`, `stark`, `lysander` are registered.
5. `test_cerco_game_controller_ingests_run_session()`:
   - **Arrange**: `RunSession.start_new(999, {"aquele": 25}, ["movimento", "trabalho"])`.
   - **Act**: `var controller = autofree(CercoGameController.new())`.
   - **Assert**: `controller.is_run_mode == true`, only `aquele` is registered with 25 HP, and `deck` draw pile has 2 cards.

### 5.2 Command-Line Automated Test Execution
Run the complete GUT suite to verify zero regressions across all 808 existing tests and new bridge tests:
```bash
timeout 45s bash godot_project/run_gut_tests.sh
```
**Expected Exit Code**: `0`.

### 5.3 Invalidation Conditions
- If any existing test in `test_game_over_system.gd` or `test_all_card_abilities.gd` fails, standalone mode was altered.
- If a hero at 0 HP enters combat, permadeath was violated.
- If final combat HP does not match `RunState.hero_hp` after `sync_combat_result`, HP persistence was broken.
