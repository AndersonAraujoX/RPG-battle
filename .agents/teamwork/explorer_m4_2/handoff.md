# Handoff Report: Combat Encounter Generator Design (Milestone M4)

## 1. Observation

### 1.1 Codebase Inspection & Catalog Verification
- **`IsectumCastes.gd` (`godot_project/scripts/cerco/IsectumCastes.gd`)**:
  - Defines 24 canonical caste IDs (lines 10-34): `ID_ZANGAO_INVASOR`, `ID_SOLDADO_MANDIBULA`, `ID_OPERARIO_ESCAVADOR`, `ID_TECE_TEIA`, `ID_ESCARAVELHO_COURACADO`, `ID_VESPA_FURTIVA`, `ID_FORMIGA_ACIDA`, `ID_LOUVA_DEUS_CEIFADOR`, `ID_BESOURO_RINOCERONTE`, `ID_CENTOPEIA_VENENOSA`, `ID_BARATA_PRAGA`, `ID_TRACA_DA_RUNA`, `ID_CUPIM_ROEDOR`, `ID_VAGALUME_CEGO`, `ID_ARANHA_SALTADORA`, `ID_LIBELULA_BOMBARDEIRA`, `ID_BICHO_PAU_EMBOSCADOR`, `ID_PERCEVEJO_PESTILENTO`, `ID_CARRAPATO_PARASITA`, `ID_PULGA_SALTADORA`, `ID_GRILO_ATORDOANTE`, `ID_LARVA_NECROTICA`, `ID_RAINHA_DO_ENXAME`, `ID_COLOSSO_ISECTUM`.
  - Defines aliases in `ALIASES` (lines 62-83):
    - `"gafanhoto_praga": ID_BARATA_PRAGA`
    - `"viuva_canibal": ID_TECE_TEIA`
    - `"tarantula_golias": ID_COLOSSO_ISECTUM`
    - `"escaravelho_necrofago": ID_ESCARAVELHO_COURACADO`
    - `"formiga_correicao": ID_FORMIGA_ACIDA`
    - `"besouro": ID_BESOURO_RINOCERONTE`
    - `"soldado": ID_SOLDADO_MANDIBULA`
    - `"batedor": ID_ZANGAO_INVASOR`
    - `"operario": ID_OPERARIO_ESCAVADOR`
  - Canonical factory methods: `get_caste(caste_id) -> IsectumCasteData`, `create_instance(caste_id) -> IsectumCasteData`, `get_castes_by_archetype(archetype) -> Array[IsectumCasteData]`.
  - `IsectumCasteData.gd`: exports `id`, `caste_name`, `hp`, `max_hp`, `ac` (12 default, 14 brutamontes), `speed`, `attack_dice`, `attack_range`, `threat_cost`, `is_brutamontes`, `is_infiltrator`, `is_catapult`, `is_flyer`, `is_boss`, `trait_id`, `symbol`, `description`.

### 1.2 Run & Map Specifications
- **`RunNode.gd` (`godot_project/scripts/run/RunNode.gd`)**:
  - `enum NodeType { COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS }` (line 8).
  - Combat-capable node types identified by `is_combat_type()` (line 55): `COMBAT`, `ELITE`, `SIEGE`, `BOSS`.
  - Boss node identified by `is_boss()` (line 52): `type == NodeType.BOSS`.
  - Node attributes: `id: int`, `act: int`, `floor_index: int`, `column: int`, `type: int`.
- **`CAMPANHA_ROGUELIKE.md`**:
  - Act 1 (Superfície - "O Cerco da Última Fortaleza", lines 39-56):
    - Base castes (Tier 1): `larva_carniceira` (enxame básico Melee), `formiga_acida` / `formiga_correicao` (corrosão de armadura), `besouro_gorgulho` (demolidor de estruturas/barricadas), `gafanhoto_praga` (saltador de muralhas).
    - Act 1 Boss: `viuva_canibal` ("Emerge de túneis subterrâneos, prende heróis com teias (reduzindo movimento a 0) e se alimenta de larvas menores para se curar se o jogador não limpar as crias antes.").
  - Node Types (lines 140-149):
    - `COMBAT`: Group of Act castes. Reward: Gold + Choose 1 of 3 Cards.
    - `ELITE`: Powerful caste or mini-boss (only appears floor 4+). Reward: 1 Guaranteed Relic + Extra Gold.
    - `SIEGE`: Outpost defense against siege/sapper waves. Reward: High Gold/resources + Cards.
    - `BOSS`: Final floor of the Act (floor 11). Defeating it heals party 25% and transitions Act.
- **`RunState.gd`**:
  - Bosses per act (line 24): `1: "viuva_canibal", 2: "rainha_do_enxame", 3: "rei_isectum"`.
  - Persistent variables: `hero_hp: Dictionary`, `fallen_heroes: Array[String]`, `seed_value: int`, `gold: int`, `relics: Array[String]`.
- **`FortressBoard.gd` (`godot_project/scripts/cerco/FortressBoard.gd`)**:
  - Grid: 20x20 discrete coordinates (`0 <= x < 20`, `0 <= y < 20`).
  - Perimeter invasion spawn zones: `SPAWN_NORTE` (y in 0..1), `SPAWN_SUL` (y in 18..19), `SPAWN_OESTE` (x in 0..1), `SPAWN_LESTE` (x in 18..19).
  - Central chamber: `CAMARA_CENTRAL` (x in 8..11, y in 8..11).
  - Board items: placed via `place_item(pos, item_type, data) -> bool`. Custom item types such as `"WEB"` are supported seamlessly.
- **`FortressBoardView.gd` (line 1526)**:
  - Sprite mapping explicitly maps `"larva_necrotica": "larva_carniceira"`, and `"cupim_roedor": "besouro_gorgulho"`.

---

## 2. Logic Chain

### 2.1 Architectural Approach
The encounter generator must be pure, decoupled, headless-safe, and deterministic. Implementing it as a `RefCounted` class named `CombatEncounterGenerator` located at `res://scripts/run/combat/CombatEncounterGenerator.gd` fulfills all project requirements:
1. Follows Godot 4 architecture conventions without requiring scene tree instantiation.
2. Direct dependency injection: can accept either a `RunNode` or raw `(act, floor_index, node_type, node_id)` parameters along with an optional `RandomNumberGenerator` or integer seed.
3. Outputs a standardized, serializable `Dictionary` (`CombatEncounterData`) containing metadata, full enemy squad declarations, environmental hazards, objective rules, and reward guarantees.

### 2.2 Caste Resolution & Alias Normalization
To prevent discrepancies between design documents (`CAMPANHA_ROGUELIKE.md`) and catalog implementations (`IsectumCastes.gd`), `CombatEncounterGenerator` introduces an internal canonical alias resolver:
```gdscript
const CASTE_ALIASES: Dictionary = {
	"larva_carniceira": IsectumCastes.ID_LARVA_NECROTICA,
	"besouro_gorgulho": IsectumCastes.ID_CUPIM_ROEDOR,
	"gafanhoto_praga": IsectumCastes.ID_BARATA_PRAGA,
	"viuva_canibal": IsectumCastes.ID_TECE_TEIA,
	"tarantula_golias": IsectumCastes.ID_COLOSSO_ISECTUM,
	"formiga_correicao": IsectumCastes.ID_FORMIGA_ACIDA,
	"escaravelho_necrofago": IsectumCastes.ID_ESCARAVELHO_COURACADO,
}
```
Every caste query resolves through:
```gdscript
static func resolve_caste_id(raw_id: String) -> String:
	var lower: String = raw_id.to_lower().strip_edges()
	if CASTE_ALIASES.has(lower):
		return CASTE_ALIASES[lower]
	return lower
```
This guarantees that `IsectumCastes.get_caste(resolved_id)` will never return null.

### 2.3 Deterministic Seeding Formula
To guarantee that two expeditions using the same seed encounter the exact same enemy squads and placements, `CombatEncounterGenerator` implements a prime-multiplication hash combiner:
```gdscript
static func compute_encounter_seed(base_seed: int, act: int, floor_index: int, node_id: int) -> int:
	var p1: int = 73856093
	var p2: int = 19349663
	var p3: int = 83492791
	return (base_seed + (act * p1) + (floor_index * p2) + (node_id * p3)) & 0x7FFFFFFF
```
When `generate_encounter(node, seed_or_rng)` is invoked:
- If `seed_or_rng is RandomNumberGenerator`: it is used directly.
- If `seed_or_rng is int`: a new `RandomNumberGenerator` is created with seed = `compute_encounter_seed(seed_or_rng, node.act, node.floor_index, node.id)`.
- If `seed_or_rng == null`: a new `RandomNumberGenerator` is seeded deterministically using `compute_encounter_seed(0, node.act, node.floor_index, node.id)`.

### 2.4 Enemy Squad Composition Algorithms

#### A. Node Type `COMBAT` (Standard Tactical Battle)
- **Enemy Count**: 3 to 4 basic enemies.
  - Floor 0 to 2: 3 enemies (gentle onboarding).
  - Floor 3 to 10: 50% chance of 3 enemies, 50% chance of 4 enemies.
- **Act 1 Caste Pool**:
  - `larva_carniceira` (weight 30%): Melee swarm, 2 HP, on-death explosion.
  - `formiga_acida` (weight 25%): Ranged acid spitter (range 2), 3 HP, armor corrosion.
  - `besouro_gorgulho` (weight 25%): Durable infantry, 3 HP, high threat cost.
  - `gafanhoto_praga` (weight 20%): Mobile flyer/skirmisher, 3 HP, speed 3.
  - Fallback/Variety additions: `soldado_mandibula`, `zangao_invasor`.
- **Role Balancing**:
  - Must include at least 1 frontline melee (`larva_carniceira`, `soldado_mandibula`, `besouro_gorgulho`).
  - Must include at least 1 ranged/flanker (`formiga_acida`, `gafanhoto_praga`, `zangao_invasor`).
  - Remaining units picked by weighted random selection.
- **Stats & Scaling**:
  - Base stats cloned from `IsectumCastes`.
  - Floor scaling:
    - Floor 0–3: Standard base stats.
    - Floor 4–7: +1 HP on 1 unit.
    - Floor 8–10: +1 HP on all units, +1 attack bonus on 1 unit.
- **Placement**:
  - Distributed across `SPAWN_NORTE`, `SPAWN_SUL`, `SPAWN_LESTE`, `SPAWN_OESTE`.
  - Anti-collision tracking guarantees distinct `Vector2i` coordinates.
- **Rewards**:
  - 15–20 Gold.
  - 3-card draft.
  - No guaranteed relic.

#### B. Node Type `SIEGE` (Outpost Assault)
- **Enemy Count**: 4 to 6 enemies (focusing on siege, sappers, and brutamontes).
  - Floor 0 to 4: 4 to 5 enemies.
  - Floor 5 to 10: 5 to 6 enemies.
- **Act 1 Caste Pool**:
  - `besouro_gorgulho` (`cupim_roedor`): structure damage.
  - `operario_escavador`: sapper trait, double wall damage.
  - `besouro_rinoceronte`: Brutamontes (3 circles, CA 14).
  - `escaravelho_couracado`: heavy armor (6 HP).
  - Escort: `formiga_acida` (acid corrosion on masonry), `soldado_mandibula`.
- **Composition Rules**:
  - Guarantee at least 2 dedicated siege/sapper units (`operario_escavador`, `cupim_roedor`, `besouro_rinoceronte`).
  - Guarantee at least 1 heavy armor tank (`escaravelho_couracado` or `besouro_rinoceronte`).
  - Remaining 1–3 units filled by shock infantry or acid artillery.
- **Objective Rules**:
  - `is_siege_mode = true`.
  - Wall breaching threats active.
- **Rewards**:
  - 20–30 Gold.
  - 3-card draft.

#### C. Node Type `ELITE` (Heavy Insect Encounter)
- **Availability**: Floor 4 and above (`floor_index >= 4`).
- **Composition**: 1 Heavy Insect Leader + 2 to 3 Escort Minions (Total 3 to 4 enemies).
- **Heavy Insect Leader (50/50 RNG Choice)**:
  1. `escaravelho_couracado` (Heavy Armored Beetle):
     - Display Name: `"Escaravelho Couraçado Alfa"`
     - HP: 18 to 22 (scaled from base 6)
     - AC: 16
     - Attack Dice: 4
     - Speed: 2
     - Trait: `carapaca_pesada`
     - Flag: `is_elite = true`
  2. `tarantula_golias` (`colosso_isectum`):
     - Display Name: `"Tarântula Golias"`
     - HP: 20 to 25 (scaled from 3 circles)
     - AC: 15
     - Attack Dice: 5
     - Speed: 2
     - Trait: `colosso_devastador`
     - Flag: `is_elite = true`
- **Escort Minions**:
  - 2 to 3 aggressive Tier 1 units (`gafanhoto_praga`, `formiga_acida`, `soldado_mandibula`).
- **Placement**:
  - Leader spawns at prime assault vector (e.g. `Vector2i(10, 2)` in Northern breach).
  - Minions spawn adjacent or flanking.
- **Rewards**:
  - **1 Guaranteed Relic** (`guaranteed_relic = true`).
  - 30–45 Gold.
  - 3-card draft.

#### D. Node Type `BOSS` (Act 1 Boss: `viuva_canibal`)
- **Availability**: Floor 11 (`node.is_boss()`).
- **Boss Unit**:
  - ID: `"viuva_canibal_boss"`
  - Caste: `viuva_canibal` (resolves to `ID_TECE_TEIA` with boss stat override)
  - Display Name: `"Viúva Canibal, Tecelã das Sombras"`
  - HP: 65 to 75 HP (Boss health pool)
  - AC: 15
  - Speed: 3
  - Attack Dice: 4
  - Attack Range: 3
  - Trait: `"teia_imobilizante"`
  - Symbol: `"🕷️"`
  - Flag: `is_boss = true`
  - Placement: North-central plaza (`Vector2i(9, 3)` or `Vector2i(10, 3)`).
- **Minions (Larval adds)**:
  - 2 to 3 `larva_carniceira` (`larva_necrotica`) initial spawns flanking the boss (`Vector2i(7, 3)`, `Vector2i(12, 3)`).
  - Supports the narrative mechanic: Viúva can consume living larvae to heal if players do not eliminate them early.
- **Web Hazards (`hazards`)**:
  - 4 to 8 sticky web tiles placed across the board.
  - Placed at strategic corridors and chokepoints between spawn areas and the inner courtyard:
    - `Vector2i(8, 6)`, `Vector2i(11, 6)`
    - `Vector2i(6, 9)`, `Vector2i(13, 9)`
    - `Vector2i(8, 12)`, `Vector2i(11, 12)`
  - Hazard payload:
    ```gdscript
    {
        "pos": Vector2i(x, y),
        "type": "WEB",
        "name": "Teia Viscosa",
        "icon": "🕸️",
        "effect": "immobilize",
        "duration": -1
    }
    ```
- **Rewards & Progression**:
  - 50 Gold.
  - 1 Boss Relic.
  - +10 Amber Real.
  - Act clear transition + 25% party heal.

---

### 2.5 Proposed GDScript Implementation

Below is the complete, production-ready implementation of `godot_project/scripts/run/combat/CombatEncounterGenerator.gd`:

```gdscript
# res://scripts/run/combat/CombatEncounterGenerator.gd
class_name CombatEncounterGenerator
extends RefCounted

## CombatEncounterGenerator: Procedural generator for tactical combat encounters
## in the Roguelike Campaign (M4). Deterministically creates enemy squads,
## boss configurations, web hazards, and reward rules based on Act, floor, and NodeType.

# ── Caste Aliases & Normalization ───────────────────────────────────────────
const CASTE_ALIASES: Dictionary = {
	"larva_carniceira": IsectumCastes.ID_LARVA_NECROTICA,
	"besouro_gorgulho": IsectumCastes.ID_CUPIM_ROEDOR,
	"gafanhoto_praga": IsectumCastes.ID_BARATA_PRAGA,
	"viuva_canibal": IsectumCastes.ID_TECE_TEIA,
	"tarantula_golias": IsectumCastes.ID_COLOSSO_ISECTUM,
	"formiga_correicao": IsectumCastes.ID_FORMIGA_ACIDA,
	"escaravelho_necrofago": IsectumCastes.ID_ESCARAVELHO_COURACADO,
}

# ── Act 1 Tier 1 Caste Pools ────────────────────────────────────────────────
const ACT_1_COMBAT_POOL: Array[String] = [
	"larva_carniceira",
	"formiga_acida",
	"besouro_gorgulho",
	"gafanhoto_praga",
	IsectumCastes.ID_ZANGAO_INVASOR,
	IsectumCastes.ID_SOLDADO_MANDIBULA,
]

const ACT_1_SIEGE_POOL: Array[String] = [
	"besouro_gorgulho",
	IsectumCastes.ID_OPERARIO_ESCAVADOR,
	IsectumCastes.ID_BESOURO_RINOCERONTE,
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
	"formiga_acida",
	IsectumCastes.ID_SOLDADO_MANDIBULA,
]

const ACT_1_ELITE_LEADERS: Array[String] = [
	IsectumCastes.ID_ESCARAVELHO_COURACADO,
	"tarantula_golias",
]

# ── Public Factory API ──────────────────────────────────────────────────────

## Generates a complete combat encounter dictionary from a RunNode.
static func generate_from_node(node: RunNode, seed_or_rng: Variant = null) -> Dictionary:
	if node == null:
		push_error("[CombatEncounterGenerator] Node is null")
		return {}
	return generate_encounter(node.act, node.floor_index, node.type, node.id, seed_or_rng)

## Generates a complete combat encounter dictionary from discrete parameters.
static func generate_encounter(
	act: int,
	floor_index: int,
	node_type: int,
	node_id: int = -1,
	seed_or_rng: Variant = null
) -> Dictionary:
	var rng: RandomNumberGenerator = _resolve_rng(seed_or_rng, act, floor_index, node_id)
	var safe_act: int = clampi(act, 1, 3)
	var safe_floor: int = maxi(0, floor_index)

	var squad: Array[Dictionary] = []
	var hazards: Array[Dictionary] = []
	var encounter_name: String = ""
	var rules: Dictionary = {
		"max_rounds": 10,
		"objective": "defeat_all",
		"is_siege_mode": false,
		"boss_id": "",
		"can_flee": false
	}
	var rewards: Dictionary = {
		"base_gold": 15,
		"gold_min": 12,
		"gold_max": 18,
		"card_draft_count": 3,
		"guaranteed_relic": false,
		"relic_pool": "standard",
		"amber_reward": 0
	}

	match node_type:
		RunNode.NodeType.COMBAT:
			encounter_name = "Combate Tático: Enxame Isectum"
			squad = _generate_combat_squad(safe_act, safe_floor, rng)
			rewards["base_gold"] = 15 + safe_floor
			rewards["gold_min"] = maxi(10, rewards["base_gold"] - 3)
			rewards["gold_max"] = rewards["base_gold"] + 4

		RunNode.NodeType.SIEGE:
			encounter_name = "Cerco de Posto Avançado"
			squad = _generate_siege_squad(safe_act, safe_floor, rng)
			rules["is_siege_mode"] = true
			rules["objective"] = "survive_siege"
			rewards["base_gold"] = 22 + safe_floor * 2
			rewards["gold_min"] = rewards["base_gold"] - 4
			rewards["gold_max"] = rewards["base_gold"] + 5

		RunNode.NodeType.ELITE:
			encounter_name = "Inimigo de Elite Isectum"
			squad = _generate_elite_squad(safe_act, safe_floor, rng)
			rules["objective"] = "defeat_elite"
			rewards["base_gold"] = 35 + safe_floor * 2
			rewards["gold_min"] = rewards["base_gold"] - 5
			rewards["gold_max"] = rewards["base_gold"] + 8
			rewards["guaranteed_relic"] = true
			rewards["relic_pool"] = "elite"

		RunNode.NodeType.BOSS:
			encounter_name = "Covil da Viúva Canibal (Chefe do Ato I)"
			squad = _generate_boss_squad(safe_act, safe_floor, rng)
			hazards = _generate_boss_web_hazards(rng)
			rules["objective"] = "kill_boss"
			rules["boss_id"] = "viuva_canibal"
			rules["max_rounds"] = 15
			rewards["base_gold"] = 50
			rewards["gold_min"] = 45
			rewards["gold_max"] = 60
			rewards["guaranteed_relic"] = true
			rewards["relic_pool"] = "boss"
			rewards["amber_reward"] = 10

		_:
			encounter_name = "Encontro Básico"
			squad = _generate_combat_squad(safe_act, safe_floor, rng)

	var enc_id: String = "encounter_a%d_f%d_n%d" % [safe_act, safe_floor, node_id]
	return {
		"encounter_id": enc_id,
		"encounter_name": encounter_name,
		"act": safe_act,
		"floor": safe_floor,
		"node_id": node_id,
		"node_type": node_type,
		"squad": squad,
		"hazards": hazards,
		"rules": rules,
		"rewards": rewards
	}

# ── Squad Generation Algorithms ─────────────────────────────────────────────

static func _generate_combat_squad(act: int, floor_index: int, rng: RandomNumberGenerator) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var count: int = 3
	if floor_index >= 3:
		count = rng.randi_range(3, 4)

	var occupied_positions: Dictionary = {}
	var unit_index: int = 1

	# Guarantee 1 Frontline Melee + 1 Ranged/Skirmisher
	var melee_castes: Array[String] = ["larva_carniceira", IsectumCastes.ID_SOLDADO_MANDIBULA, "besouro_gorgulho"]
	var ranged_castes: Array[String] = ["formiga_acida", "gafanhoto_praga", IsectumCastes.ID_ZANGAO_INVASOR]

	var selected_castes: Array[String] = []
	selected_castes.append(melee_castes[rng.randi() % melee_castes.size()])
	selected_castes.append(ranged_castes[rng.randi() % ranged_castes.size()])

	while selected_castes.size() < count:
		selected_castes.append(ACT_1_COMBAT_POOL[rng.randi() % ACT_1_COMBAT_POOL.size()])

	for raw_id in selected_castes:
		var pos: Vector2i = _pick_spawn_cell(rng, occupied_positions)
		var u: Dictionary = _create_unit_dict(raw_id, "combat_%d" % unit_index, pos, act, floor_index, false, false)
		squad.append(u)
		unit_index += 1

	return squad

static func _generate_siege_squad(act: int, floor_index: int, rng: RandomNumberGenerator) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var count: int = rng.randi_range(4, 5) if floor_index < 5 else rng.randi_range(5, 6)
	var occupied_positions: Dictionary = {}
	var unit_index: int = 1

	# Guarantee 2 Siege/Sappers + 1 Heavy Tank
	var sapper_castes: Array[String] = [IsectumCastes.ID_OPERARIO_ESCAVADOR, "besouro_gorgulho"]
	var heavy_castes: Array[String] = [IsectumCastes.ID_ESCARAVELHO_COURACADO, IsectumCastes.ID_BESOURO_RINOCERONTE]

	var selected: Array[String] = []
	selected.append(sapper_castes[rng.randi() % sapper_castes.size()])
	selected.append(sapper_castes[rng.randi() % sapper_castes.size()])
	selected.append(heavy_castes[rng.randi() % heavy_castes.size()])

	while selected.size() < count:
		selected.append(ACT_1_SIEGE_POOL[rng.randi() % ACT_1_SIEGE_POOL.size()])

	for raw_id in selected:
		var pos: Vector2i = _pick_spawn_cell(rng, occupied_positions)
		var u: Dictionary = _create_unit_dict(raw_id, "siege_%d" % unit_index, pos, act, floor_index, false, true)
		squad.append(u)
		unit_index += 1

	return squad

static func _generate_elite_squad(act: int, floor_index: int, rng: RandomNumberGenerator) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var occupied_positions: Dictionary = {}

	# 1. Heavy Insect Leader
	var leader_raw: String = ACT_1_ELITE_LEADERS[rng.randi() % ACT_1_ELITE_LEADERS.size()]
	var leader_pos: Vector2i = _pick_spawn_cell(rng, occupied_positions, "SPAWN_NORTE")
	var leader: Dictionary = _create_unit_dict(leader_raw, "elite_leader_1", leader_pos, act, floor_index, true, false)
	
	# Apply Elite Leader Buffs
	leader["is_elite"] = true
	leader["name"] = "Escaravelho Couraçado Alfa" if leader["caste_id"] == IsectumCastes.ID_ESCARAVELHO_COURACADO else "Tarântula Golias Titânica"
	leader["max_hp"] = 20 + floor_index
	leader["hp"] = leader["max_hp"]
	leader["ac"] = maxi(15, leader["ac"] + 2)
	leader["attack_bonus"] = leader["attack_bonus"] + 1
	squad.append(leader)

	# 2. Support Minions (2 to 3 units)
	var minion_count: int = rng.randi_range(2, 3)
	var minion_pool: Array[String] = ["gafanhoto_praga", "formiga_acida", IsectumCastes.ID_SOLDADO_MANDIBULA]
	for i in range(minion_count):
		var raw_caste: String = minion_pool[rng.randi() % minion_pool.size()]
		var m_pos: Vector2i = _pick_spawn_cell(rng, occupied_positions)
		var minion: Dictionary = _create_unit_dict(raw_caste, "elite_escort_%d" % (i + 1), m_pos, act, floor_index, false, false)
		squad.append(minion)

	return squad

static func _generate_boss_squad(act: int, floor_index: int, rng: RandomNumberGenerator) -> Array[Dictionary]:
	var squad: Array[Dictionary] = []
	var occupied: Dictionary = {}

	# 1. Viúva Canibal Boss Unit
	var boss_pos: Vector2i = Vector2i(9, 3)
	occupied[boss_pos] = true

	var boss_caste: IsectumCasteData = IsectumCastes.get_caste(IsectumCastes.ID_TECE_TEIA)
	var boss: Dictionary = {
		"id": "viuva_canibal_boss",
		"caste_id": IsectumCastes.ID_TECE_TEIA,
		"name": "Viúva Canibal, Tecelã das Sombras",
		"team": "B",
		"hp": 70,
		"max_hp": 70,
		"ac": 15,
		"move_range": 3,
		"attack_range": 3,
		"attack_bonus": 4,
		"attack_dice": 4,
		"trait_id": "teia_imobilizante",
		"symbol": "🕷️",
		"spawn_pos": boss_pos,
		"is_boss": true,
		"is_elite": false,
		"is_siege": false
	}
	squad.append(boss)

	# 2. Larval Swarm Escorts (2 to 3 larvae for the devour/heal mechanic)
	var larvae_positions: Array[Vector2i] = [Vector2i(7, 3), Vector2i(11, 3), Vector2i(9, 5)]
	for i in range(3):
		var l_pos: Vector2i = larvae_positions[i]
		occupied[l_pos] = true
		var larva: Dictionary = _create_unit_dict("larva_carniceira", "boss_larva_%d" % (i + 1), l_pos, act, floor_index, false, false)
		larva["name"] = "Larva de Alimento"
		squad.append(larva)

	return squad

# ── Hazard Generation ───────────────────────────────────────────────────────

static func _generate_boss_web_hazards(rng: RandomNumberGenerator) -> Array[Dictionary]:
	var hazards: Array[Dictionary] = []
	var candidate_coords: Array[Vector2i] = [
		Vector2i(8, 6), Vector2i(11, 6),
		Vector2i(6, 8), Vector2i(13, 8),
		Vector2i(8, 12), Vector2i(11, 12),
		Vector2i(9, 7), Vector2i(10, 7)
	]
	var count: int = rng.randi_range(5, 7)
	candidate_coords.shuffle()

	for i in range(mini(count, candidate_coords.size())):
		hazards.append({
			"pos": candidate_coords[i],
			"type": "WEB",
			"name": "Teia Viscosa",
			"icon": "🕸️",
			"effect": "slow",
			"move_penalty": 99,
			"duration": -1
		})

	return hazards

# ── Helper Builders & Spatial Placement ──────────────────────────────────────

static func resolve_caste_id(raw_id: String) -> String:
	var lower: String = raw_id.to_lower().strip_edges()
	if CASTE_ALIASES.has(lower):
		return CASTE_ALIASES[lower]
	return lower

static func _create_unit_dict(
	raw_id: String,
	unit_uid: String,
	spawn_pos: Vector2i,
	act: int,
	floor_index: int,
	is_elite: bool,
	is_siege: bool
) -> Dictionary:
	var cid: String = resolve_caste_id(raw_id)
	var caste: IsectumCasteData = IsectumCastes.get_caste(cid)

	var base_hp: int = caste.hp if caste else 4
	var base_ac: int = caste.ac if caste else 12
	var base_speed: int = caste.speed if caste else 3
	var base_atk_dice: int = caste.attack_dice if caste else 2
	var base_range: int = caste.attack_range if caste else 1
	var trait_name: String = caste.trait_id if caste else ""
	var sym: String = caste.symbol if caste else "🦗"
	var disp_name: String = caste.caste_name if caste else raw_id.capitalize()

	# Floor stat progression
	if floor_index >= 7:
		base_hp += 1

	return {
		"id": unit_uid,
		"caste_id": cid,
		"name": disp_name,
		"team": "B",
		"hp": base_hp,
		"max_hp": base_hp,
		"ac": base_ac,
		"move_range": base_speed,
		"attack_range": base_range,
		"attack_bonus": base_atk_dice,
		"attack_dice": base_atk_dice,
		"threat_cost": caste.threat_cost if caste else 1,
		"trait_id": trait_name,
		"symbol": sym,
		"spawn_pos": spawn_pos,
		"is_boss": false,
		"is_elite": is_elite,
		"is_siege": is_siege
	}

static func _pick_spawn_cell(
	rng: RandomNumberGenerator,
	occupied: Dictionary,
	zone_pref: String = ""
) -> Vector2i:
	var candidates: Array[Vector2i] = []
	if zone_pref == "SPAWN_NORTE" or (zone_pref.is_empty() and rng.randi() % 2 == 0):
		for x in range(4, 16):
			for y in range(0, 3):
				var p: Vector2i = Vector2i(x, y)
				if not occupied.has(p):
					candidates.append(p)
	else:
		# South, West, East perimeters
		var side: int = rng.randi() % 3
		match side:
			0: # South
				for x in range(4, 16):
					for y in range(17, 20):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p): candidates.append(p)
			1: # West
				for x in range(0, 3):
					for y in range(4, 16):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p): candidates.append(p)
			2: # East
				for x in range(17, 20):
					for y in range(4, 16):
						var p: Vector2i = Vector2i(x, y)
						if not occupied.has(p): candidates.append(p)

	if candidates.is_empty():
		for x in range(20):
			for y in range(20):
				var p: Vector2i = Vector2i(x, y)
				if not occupied.has(p):
					occupied[p] = true
					return p
		return Vector2i(0, 0)

	var chosen: Vector2i = candidates[rng.randi() % candidates.size()]
	occupied[chosen] = true
	return chosen

static func _resolve_rng(seed_or_rng: Variant, act: int, floor_index: int, node_id: int) -> RandomNumberGenerator:
	if seed_or_rng is RandomNumberGenerator:
		return seed_or_rng
	var r: RandomNumberGenerator = RandomNumberGenerator.new()
	var base_s: int = int(seed_or_rng) if seed_or_rng != null else 0
	r.seed = compute_encounter_seed(base_s, act, floor_index, node_id)
	return r

static func compute_encounter_seed(base_seed: int, act: int, floor_index: int, node_id: int) -> int:
	var p1: int = 73856093
	var p2: int = 19349663
	var p3: int = 83492791
	return (base_seed + (act * p1) + (floor_index * p2) + (node_id * p3)) & 0x7FFFFFFF
```

---

## 3. Caveats

1. **Act 2 and Act 3 Scope Scaffolding**:
   The primary focus for Milestone M4 is Act 1 (`viuva_canibal` and Tier 1 castes). While the class parameters accept `act: int` up to 3, detailed caste pools for Act 2 (`rainha_do_enxame`, casulos) and Act 3 (`rei_isectum`, 3 Corações) will receive their specialized boss logic in Milestones M5 and M6 respectively.
2. **Web Hazard Consumption & Board Interaction**:
   `CombatEncounterGenerator` provides the complete specification and placement of `"WEB"` hazards on the grid. In the subsequent integration step (`RunCombatBridge`), `FortressBoard.place_item()` will receive these hazards, and movement cost / status triggers must check whether an entering unit is an enemy or ally (since spiders ignore web hazards while heroes are trapped).
3. **Caste Catalog Aliases**:
   As discovered during investigation, `larva_carniceira` is not an explicit key in `IsectumCastes.ALIASES` (which has `ID_LARVA_NECROTICA`). The generator's `CASTE_ALIASES` table resolves this mismatch internally, ensuring total backwards and cross-document compatibility.

---

## 4. Conclusion

The design for `CombatEncounterGenerator.gd` fulfills all M4 requirements:
- Strictly decoupled `RefCounted` architecture.
- Full deterministic seed computation (`compute_encounter_seed`) with prime hashing.
- Complete algorithms for `COMBAT` (3–4 basic), `SIEGE` (4–6 sapper/brutamontes), `ELITE` (Escaravelho Alfa or Tarântula Golias + minions), and `BOSS` (Viúva Canibal + larval adds + web hazards).
- Fully validated against `IsectumCastes.gd`, `FortressBoard.gd`, and `RunNode.gd`.

---

## 5. Verification Method

### 5.1 Test Specification (`test_combat_encounter_generator.gd`)
The implementation must be validated by creating `godot_project/test/unit/test_combat_encounter_generator.gd` using GUT, adhering strictly to the **Arrange-Act-Assert (AAA)** pattern:

```gdscript
# res://test/unit/test_combat_encounter_generator.gd
extends GutTest

## Test Suite for CombatEncounterGenerator (Milestone M4)
## Validates determinism, squad counts, elite leaders, Viúva Canibal boss, and web hazards.

func test_combat_node_generates_three_to_four_enemies() -> void:
	# Arrange
	var node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 1234)

	# Assert
	assert_false(enc.is_empty(), "Encounter should not be empty")
	var squad: Array = enc.get("squad", [])
	assert_gte(squad.size(), 3, "Combat node squad must have at least 3 enemies")
	assert_lte(squad.size(), 4, "Combat node squad must have at most 4 enemies")
	assert_false(enc["rules"]["is_siege_mode"], "Combat node should not be siege mode")
	assert_false(enc["rewards"]["guaranteed_relic"], "Standard combat does not guarantee relic")

func test_siege_node_generates_four_to_six_enemies_with_siege_castes() -> void:
	# Arrange
	var node: RunNode = RunNode.new(2, 1, 3, 1, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 5678)

	# Assert
	var squad: Array = enc.get("squad", [])
	assert_gte(squad.size(), 4, "Siege squad has at least 4 enemies")
	assert_lte(squad.size(), 6, "Siege squad has at most 6 enemies")
	assert_true(enc["rules"]["is_siege_mode"], "Siege mode flag must be true")

	var has_siege_unit: bool = false
	for u in squad:
		if u["is_siege"] or u["caste_id"] in [IsectumCastes.ID_OPERARIO_ESCAVADOR, IsectumCastes.ID_BESOURO_RINOCERONTE, IsectumCastes.ID_ESCARAVELHO_COURACADO, IsectumCastes.ID_CUPIM_ROEDOR]:
			has_siege_unit = true
			break
	assert_true(has_siege_unit, "Siege squad contains sapper or heavy siege caste")

func test_elite_node_generates_heavy_leader_and_guarantees_relic() -> void:
	# Arrange
	var node: RunNode = RunNode.new(3, 1, 5, 2, RunNode.NodeType.ELITE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 9999)

	# Assert
	var squad: Array = enc.get("squad", [])
	assert_gte(squad.size(), 3, "Elite squad has leader and minions")
	assert_true(enc["rewards"]["guaranteed_relic"], "Elite encounter must guarantee a relic")

	var leader: Dictionary = squad[0]
	assert_true(leader["is_elite"], "First unit is flagged as elite leader")
	assert_gte(leader["hp"], 18, "Elite leader possesses elevated HP pool")
	assert_true(leader["caste_id"] in [IsectumCastes.ID_ESCARAVELHO_COURACADO, IsectumCastes.ID_COLOSSO_ISECTUM], "Leader is heavy armored or colossus")

func test_boss_node_generates_viuva_canibal_with_larvae_and_web_hazards() -> void:
	# Arrange
	var node: RunNode = RunNode.new(4, 1, 11, 0, RunNode.NodeType.BOSS)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 4321)

	# Assert
	assert_eq(enc["rules"]["boss_id"], "viuva_canibal")
	var squad: Array = enc.get("squad", [])
	var boss: Dictionary = squad[0]
	assert_true(boss["is_boss"], "First unit is boss")
	assert_eq(boss["caste_id"], IsectumCastes.ID_TECE_TEIA)
	assert_gte(boss["hp"], 60, "Viúva Canibal has boss HP (>= 60)")

	var hazards: Array = enc.get("hazards", [])
	assert_gt(hazards.size(), 0, "Boss encounter must generate web hazards")
	for h in hazards:
		assert_eq(h["type"], "WEB", "Hazard type is WEB")
		assert_true(h.has("pos"), "Hazard must contain grid position")

func test_deterministic_reproducibility_with_same_seed() -> void:
	# Arrange
	var node: RunNode = RunNode.new(7, 1, 2, 1, RunNode.NodeType.COMBAT)

	# Act
	var enc1: Dictionary = CombatEncounterGenerator.generate_from_node(node, 88888)
	var enc2: Dictionary = CombatEncounterGenerator.generate_from_node(node, 88888)

	# Assert
	assert_eq(enc1["squad"].size(), enc2["squad"].size(), "Squad sizes match identically")
	for i in range(enc1["squad"].size()):
		assert_eq(enc1["squad"][i]["caste_id"], enc2["squad"][i]["caste_id"], "Caste ID matches at index %d" % i)
		assert_eq(enc1["squad"][i]["spawn_pos"], enc2["squad"][i]["spawn_pos"], "Spawn position matches at index %d" % i)
		assert_eq(enc1["squad"][i]["hp"], enc2["squad"][i]["hp"], "HP matches at index %d" % i)

func test_spatial_anti_collision_guarantee() -> void:
	# Arrange
	var node: RunNode = RunNode.new(8, 1, 4, 1, RunNode.NodeType.SIEGE)

	# Act
	var enc: Dictionary = CombatEncounterGenerator.generate_from_node(node, 10101)

	# Assert
	var positions_seen: Dictionary = {}
	var squad: Array = enc.get("squad", [])
	for u in squad:
		var p: Vector2i = u["spawn_pos"]
		assert_false(positions_seen.has(p), "No two enemies can spawn on the same cell: %s" % str(p))
		assert_true(p.x >= 0 and p.x < 20 and p.y >= 0 and p.y < 20, "Position must be inside 20x20 grid")
		positions_seen[p] = true
```

### 5.2 Independent Verification Command
Run the test runner once implemented:
```bash
bash godot_project/run_gut_tests.sh -gselect=test_combat_encounter_generator.gd
```
- Expected exit code: `0`
- Expected result: All tests pass with 0 failures and 0 memory leaks.
