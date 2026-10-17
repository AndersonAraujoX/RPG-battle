# Handoff Report: Milestone M5 — TorchLighting & ChitinCocoon Design

**Agent**: Explorer 1 (`explorer_m5_1`)  
**Date**: 2026-10-16  
**Scope**: Act II (Túneis Vivos) Mechanics — `TorchLighting.gd` & `ChitinCocoon.gd`  
**Target Path**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1/handoff.md`  

---

## 1. Observation

Direct observations from the codebase, documentation, and existing test infrastructure:

1. **GUT Test Infrastructure & Baseline**:
   - Running `bash godot_project/run_gut_tests.sh` passes 100% cleanly:
     ```
     Test Scripts Executed: 40
     Tests Run:             873
     Tests Passed:          873
     Tests Failed:          0
     Total Assertions:      9554
     Assertions Passed:     9554
     Assertions Failed:     0
     Exit code: 0
     ```
   - Zero test failures, strict AAA structure, deterministic execution without memory leaks.

2. **Tactical Grid Geometry (`godot_project/scripts/tactical/TacticalGrid.gd`)**:
   - Line 45-49: `enum DistanceMetric { CHEBYSHEV, EUCLIDEAN, MANHATTAN }`, default `metric = DistanceMetric.CHEBYSHEV` (D&D 5e standard, diagonal movement cost = 1.0).
   - Line 52-53: Default grid dimensions are `width = 20`, `height = 20` (400 discrete cells).
   - Line 458-460:
     ```gdscript
     func calculate_chebyshev_distance(p1: Vector2i, p2: Vector2i) -> int:
         return maxi(abs(p1.x - p2.x), abs(p1.y - p2.y))
     ```
   - Occupancy grid `_units_grid[y][x]` accepts `Variant` (supports `CharacterBody2D`, `RefCounted`, or `Dictionary`).
   - Line 188-203: `apply_terrain_damage(pos, damage_type)` supports elemental terrain interactions (`"fogo"`, `"gelo"`, etc.).

3. **Canonical Relic Catalog (`godot_project/scripts/run/relics/RelicManager.gd`)**:
   - Line 450-457: Relic `tocha_eterna` ("Tocha Eterna de Sulfeto", rarity `RARITY_RARO`, cost `85`) is registered in catalog.
   - Dispatch requirement specifies: relic synergy `tocha_eterna` increases base torch radius by `+2` (from radius 3 to radius 5).

4. **Tier 2 Insect Castes for Act II (`godot_project/scripts/cerco/IsectumCastes.gd` & `CombatEncounterGenerator.gd`)**:
   - `CombatEncounterGenerator.gd:52-59`:
     ```gdscript
     const ACT_2_COMBAT_POOL: Array[String] = [
         IsectumCastes.ID_VESPA_FURTIVA,        # "vespa_furtiva" (Flyer / Infiltrator)
         IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,  # "louva_deus_ceifador" (Melee DPS / Critical)
         IsectumCastes.ID_CENTOPEIA_VENENOSA,   # "centopeia_venenosa" (Poisoner)
         IsectumCastes.ID_LIBELULA_BOMBARDEIRA, # "libelula_bombardeira" (Ranged Bombardier)
         IsectumCastes.ID_VAGALUME_CEGO,        # "vagalume_cego" (Blinding aura / Flyer)
         IsectumCastes.ID_ARANHA_SALTADORA      # "aranha_saltadora" (Wall leaper / Ambush)
     ]
     ```

5. **Campaign Specification (`CAMPANHA_ROGUELIKE.md` & `ORIGINAL_REQUEST.md`)**:
   - `CAMPANHA_ROGUELIKE.md:64`: *"Escuridão subterrânea (visibilidade reduzida ao redor das tochas dos heróis), paredes bioluminescentes e som abafado de milhares de asas vibrando."*
   - `CAMPANHA_ROGUELIKE.md:73`: *"- Casulos de Quitina: estruturas no tabuleiro que eclodem após 3 rodadas se não forem destruídas."*
   - `PROJECT.md:68-71`: Contract interface:
     ```
     TorchLighting.update_visibility(heroes_positions: Array[Vector2i], grid: TacticalGrid) -> void
     TorchLighting.is_cell_lit(cell: Vector2i) -> bool
     ```

---

## 2. Logic Chain

From the observations above, the following architecture and design decisions are derived:

### Step 1: Subsystem Roles & Memory Model
- **`TorchLighting`**: Should extend `RefCounted`. It represents the mathematical and tactical illumination model of the 20x20 grid. Making it `RefCounted` ensures it can be created, updated, and verified in headless unit tests with zero orphan nodes and minimal allocation overhead.
- **`ChitinCocoon`**: Should extend `RefCounted`. The dispatch specifies `(RefCounted or Node)`. Making the core domain logic `RefCounted` eliminates Godot node lifecycle leaks in headless unit tests (no need for `autofree()`), while emitting standard Godot signals (`damaged`, `destroyed`, `countdown_ticked`, `hatched`, `acid_burst`) that any visual node (e.g., `CharacterBody2D` or `Sprite2D` on the board) can listen to.

### Step 2: Chebyshev Visibility Math & Relic Synergy
- The Chebyshev distance from a hero $H = (h_x, h_y)$ to a cell $C = (x, y)$ is:
  $$d_{\text{Cheb}}(H, C) = \max(|x - h_x|, |y - h_y|)$$
- The illuminated area around hero $H$ with effective radius $R$ is a square of $(2R + 1) \times (2R + 1)$ cells bounded by grid borders:
  $$x \in [\max(0, h_x - R), \min(W - 1, h_x + R)], \quad y \in [\max(0, h_y - R), \min(H - 1, h_y + R)]$$
- Base radius is $R_{\text{base}} = 3$ ($7 \times 7 = 49$ cells when centered in open terrain).
- With relic `tocha_eterna`, bonus radius is $+2$, yielding $R_{\text{effective}} = 5$ ($11 \times 11 = 121$ cells).
- For multiple living heroes, the lit set is the mathematical union:
  $$\mathcal{L} = \bigcup_{i=1}^{N} \text{LitCells}(H_i, R_{\text{effective}})$$
- An internal `Dictionary` (`Vector2i -> bool`) guarantees $O(1)$ lookup for `is_cell_lit(cell)`.

### Step 3: Darkness Tactical Rules
- **Blocks Ranged Targeting into Darkness**:
  If a hero or enemy attempts a ranged attack (`attack_range > 1`) against a target situated in an unlit cell (`not is_cell_lit(target_pos)`), targeting is blocked (`can_target_cell(...) == false`), emitting `darkness_blocked_targeting`.
  Melee attacks (`attack_range <= 1` or adjacent distance $\le 1$) are permitted.
- **Shrouds Enemies in Darkness**:
  An enemy standing in an unlit cell (`not is_cell_lit(enemy_pos)`) is shrouded. Shroud provides:
  1. Complete immunity to incoming ranged attacks / spells (`blocks_ranged: true`).
  2. Tactical obscurement bonus: $+2$ Armor Class (AC) and attack concealment.

### Step 4: ChitinCocoon Lifecycle & Hazard Rules
- Structure Stats: $15\text{ HP}$, $10\text{ AC}$.
- 3-Turn Countdown: Initialized at `hatch_countdown = 3`.
- Round Progression: Each round, `tick_round()` decrements `hatch_countdown` by 1.
- Cancellation: If `apply_damage()` reduces `current_hp <= 0` prior to countdown reaching 0, `is_destroyed` becomes `true`. Subsequent `tick_round()` calls are completely cancelled (`{"status": "cancelled", "reason": "destroyed"}`). No insect spawns, no acid explodes.
- Hatching Execution (at `hatch_countdown == 0`):
  1. `is_hatched` set to `true`.
  2. Spawns a Tier 2 insect (random from `TIER_2_CASTES` or `preferred_caste`) in the first adjacent free walkable cell.
  3. Deals $5\text{ acid damage}$ to all adjacent in-bounds cells (damaging heroes, enemies, and structures occupying those cells).
  4. Emits `hatched` and `acid_burst`.

---

## 3. Specifications & Proposed Implementations

### A. `godot_project/scripts/tactical/TorchLighting.gd`

```gdscript
# res://scripts/tactical/TorchLighting.gd
class_name TorchLighting
extends RefCounted

## TorchLighting: Act II (Túneis Vivos) dynamic illumination and fog of war system.
## Computes Chebyshev distance visibility around living expedition heroes,
## integrates with the 'tocha_eterna' relic (+2 radius synergy), and enforces
## darkness targeting restrictions (blocks ranged attacks into darkness, shrouds enemies).

# ── Signals ──────────────────────────────────────────────────────────────────
signal visibility_updated(lit_cells: Array[Vector2i])
signal darkness_blocked_targeting(attacker_pos: Vector2i, target_pos: Vector2i)
signal enemy_shrouded(enemy_pos: Vector2i)

# ── Constants ────────────────────────────────────────────────────────────────
const DEFAULT_GRID_WIDTH: int = 20
const DEFAULT_GRID_HEIGHT: int = 20
const BASE_TORCH_RADIUS: int = 3
const TOCHA_ETERNA_BONUS_RADIUS: int = 2
const MIN_RADIUS: int = 0

# ── Configuration & State ───────────────────────────────────────────────────
var width: int = DEFAULT_GRID_WIDTH
var height: int = DEFAULT_GRID_HEIGHT
var base_radius: int = BASE_TORCH_RADIUS
var is_enabled: bool = true

var _lit_cells_set: Dictionary = {}
var _lit_cells_list: Array[Vector2i] = []
var _heroes_positions: Array[Vector2i] = []
var _bonus_radius: int = 0
var _static_light_sources: Dictionary = {} # Vector2i -> int (radius)

# ── Initialization ───────────────────────────────────────────────────────────
func _init(p_width: int = DEFAULT_GRID_WIDTH, p_height: int = DEFAULT_GRID_HEIGHT, p_base_radius: int = BASE_TORCH_RADIUS) -> void:
	width = maxi(1, p_width)
	height = maxi(1, p_height)
	base_radius = maxi(0, p_base_radius)
	_lit_cells_set.clear()
	_lit_cells_list.clear()

# ── Core Visibility Update ───────────────────────────────────────────────────
## Updates the lit area around all living heroes.
## Supports polymorphic parameter signatures:
## - update_visibility(heroes_positions: Array[Vector2i], bonus_radius: int = 0)
## - update_visibility(heroes_positions: Array[Vector2i], grid: TacticalGrid)
## - update_visibility(heroes_positions: Array[Vector2i], bonus_radius: int, grid: TacticalGrid)
func update_visibility(heroes_positions: Array[Vector2i], p2: Variant = 0, p3: Variant = null) -> void:
	var bonus: int = 0
	var grid: TacticalGrid = null

	if p2 is TacticalGrid:
		grid = p2
	elif p2 is int or p2 is float:
		bonus = int(p2)

	if p3 is TacticalGrid:
		grid = p3
	elif p3 is int or p3 is float:
		bonus = int(p3)

	if grid != null:
		width = grid.width
		height = grid.height

	_heroes_positions = heroes_positions.duplicate()
	_bonus_radius = bonus
	_recompute_lit_cells()

func _recompute_lit_cells() -> void:
	_lit_cells_set.clear()
	_lit_cells_list.clear()

	if not is_enabled:
		for y in range(height):
			for x in range(width):
				var p: Vector2i = Vector2i(x, y)
				_lit_cells_set[p] = true
				_lit_cells_list.append(p)
		visibility_updated.emit(_lit_cells_list)
		return

	var effective_radius: int = get_effective_radius(_bonus_radius)

	# 1. Cast light around each hero using Chebyshev distance
	for hero_pos in _heroes_positions:
		if not is_valid_cell(hero_pos):
			continue
		_illuminate_circle(hero_pos, effective_radius)

	# 2. Add static light sources (braziers, stationary lamps)
	for src_pos in _static_light_sources.keys():
		var rad: int = int(_static_light_sources[src_pos])
		_illuminate_circle(src_pos, rad)

	visibility_updated.emit(_lit_cells_list)

func _illuminate_circle(center: Vector2i, radius: int) -> void:
	var min_x: int = maxi(0, center.x - radius)
	var max_x: int = mini(width - 1, center.x + radius)
	var min_y: int = maxi(0, center.y - radius)
	var max_y: int = mini(height - 1, center.y + radius)

	for y in range(min_y, max_y + 1):
		for x in range(min_x, max_x + 1):
			var cell: Vector2i = Vector2i(x, y)
			if not _lit_cells_set.has(cell):
				_lit_cells_set[cell] = true
				_lit_cells_list.append(cell)

# ── Query API ────────────────────────────────────────────────────────────────
func is_cell_lit(cell: Vector2i) -> bool:
	if not is_valid_cell(cell):
		return false
	if not is_enabled:
		return true
	return _lit_cells_set.get(cell, false)

func get_lit_cells() -> Array[Vector2i]:
	return _lit_cells_list.duplicate()

func get_effective_radius(bonus_radius: int = 0) -> int:
	return maxi(MIN_RADIUS, base_radius + bonus_radius)

func is_valid_cell(pos: Vector2i) -> bool:
	return pos.x >= 0 and pos.x < width and pos.y >= 0 and pos.y < height

# ── Relic Integration Helper ────────────────────────────────────────────────
func calculate_bonus_from_relics(relic_ids: Array[String]) -> int:
	for rid in relic_ids:
		var norm: String = rid.to_lower().strip_edges()
		if norm == "tocha_eterna" or norm == "reliquia_tocha_eterna":
			return TOCHA_ETERNA_BONUS_RADIUS
	return 0

# ── Darkness Combat Rules ────────────────────────────────────────────────────
## Checks if targeting from attacker_pos to target_pos is allowed under darkness rules.
## - Melee attacks (attack_range <= 1 or dist <= 1) are permitted.
## - Ranged attacks (attack_range > 1 and dist > 1) are BLOCKED if target_pos is unlit.
func can_target_cell(attacker_pos: Vector2i, target_pos: Vector2i, attack_range: int = 1) -> bool:
	if not is_valid_cell(attacker_pos) or not is_valid_cell(target_pos):
		return false

	var cheb_dist: int = maxi(absi(attacker_pos.x - target_pos.x), absi(attacker_pos.y - target_pos.y))
	if cheb_dist > attack_range:
		return false

	# Melee range rule
	if attack_range <= 1 or cheb_dist <= 1:
		return true

	# Ranged targeting into darkness is blocked!
	if not is_cell_lit(target_pos):
		darkness_blocked_targeting.emit(attacker_pos, target_pos)
		return false

	return true

## Enemies standing in unlit cells are shrouded in darkness.
func is_enemy_shrouded(enemy_pos: Vector2i) -> bool:
	if not is_valid_cell(enemy_pos):
		return false
	if not is_enabled:
		return false
	return not is_cell_lit(enemy_pos)

## Returns combat shroud modifiers for an enemy at given position.
func get_shroud_modifiers(enemy_pos: Vector2i) -> Dictionary:
	var shrouded: bool = is_enemy_shrouded(enemy_pos)
	if shrouded:
		enemy_shrouded.emit(enemy_pos)
	return {
		"is_shrouded": shrouded,
		"blocks_ranged": shrouded,
		"ac_bonus": 2 if shrouded else 0,
		"has_concealment": shrouded
	}

# ── Static Light Sources ─────────────────────────────────────────────────────
func add_static_light(pos: Vector2i, radius: int = 2) -> void:
	if is_valid_cell(pos):
		_static_light_sources[pos] = maxi(1, radius)
		_recompute_lit_cells()

func remove_static_light(pos: Vector2i) -> void:
	if _static_light_sources.has(pos):
		_static_light_sources.erase(pos)
		_recompute_lit_cells()

func clear_static_lights() -> void:
	_static_light_sources.clear()
	_recompute_lit_cells()
```

---

### B. `godot_project/scripts/entities/ChitinCocoon.gd`

```gdscript
# res://scripts/entities/ChitinCocoon.gd
class_name ChitinCocoon
extends RefCounted

## ChitinCocoon: Destructible Act II obstacle with 15 HP and 3-turn hatch countdown.
## If not destroyed by heroes within 3 rounds, it hatches into a Tier 2 Isectum caste
## in an adjacent free cell and releases an explosive 5-damage acid burst to all adjacent cells.
## If reduced to 0 HP prior to hatching, the countdown is permanently cancelled.

# ── Signals ──────────────────────────────────────────────────────────────────
signal damaged(amount: int, current_hp: int, max_hp: int)
signal destroyed(cocoon: ChitinCocoon)
signal countdown_ticked(remaining_turns: int)
signal hatched(spawn_caste_id: String, spawn_pos: Vector2i, acid_cells: Array[Vector2i])
signal acid_burst(affected_cells: Array[Vector2i], damage: int)

# ── Constants ────────────────────────────────────────────────────────────────
const DEFAULT_MAX_HP: int = 15
const DEFAULT_HATCH_COUNTDOWN: int = 3
const DEFAULT_ACID_DAMAGE: int = 5
const DEFAULT_AC: int = 10

const TIER_2_CASTES: Array[String] = [
	IsectumCastes.ID_VESPA_FURTIVA,
	IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
	IsectumCastes.ID_CENTOPEIA_VENENOSA,
	IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
	IsectumCastes.ID_VAGALUME_CEGO,
	IsectumCastes.ID_ARANHA_SALTADORA
]

# ── Properties ───────────────────────────────────────────────────────────────
var id: String = ""
var entity_name: String = "Casulo de Quitina"
var grid_position: Vector2i = Vector2i(-1, -1)
var max_hp: int = DEFAULT_MAX_HP
var current_hp: int = DEFAULT_MAX_HP
var ac: int = DEFAULT_AC
var hatch_countdown: int = DEFAULT_HATCH_COUNTDOWN
var initial_countdown: int = DEFAULT_HATCH_COUNTDOWN
var acid_damage: int = DEFAULT_ACID_DAMAGE
var preferred_caste: String = ""
var is_destroyed: bool = false
var is_hatched: bool = false

# ── Initialization ───────────────────────────────────────────────────────────
func _init(
	p_id: String = "cocoon_1",
	p_pos: Vector2i = Vector2i(-1, -1),
	p_max_hp: int = DEFAULT_MAX_HP,
	p_countdown: int = DEFAULT_HATCH_COUNTDOWN,
	p_preferred_caste: String = ""
) -> void:
	id = p_id
	grid_position = p_pos
	max_hp = maxi(1, p_max_hp)
	current_hp = max_hp
	hatch_countdown = maxi(1, p_countdown)
	initial_countdown = hatch_countdown
	preferred_caste = p_preferred_caste

# ── Combat & Damage ──────────────────────────────────────────────────────────
## Applies incoming damage to the cocoon.
## Returns actual damage taken.
func apply_damage(amount: int, damage_type: String = "fisico") -> int:
	if is_destroyed or is_hatched:
		return 0

	var actual_damage: int = maxi(0, amount)
	current_hp = maxi(0, current_hp - actual_damage)
	damaged.emit(actual_damage, current_hp, max_hp)

	if current_hp <= 0:
		is_destroyed = true
		destroyed.emit(self)

	return actual_damage

# ── Round Progression & Countdown ────────────────────────────────────────────
## Decrements the hatch countdown by 1.
## If countdown reaches 0, executes hatching sequence.
func tick_round(grid: TacticalGrid = null, rng: RandomNumberGenerator = null) -> Dictionary:
	if is_destroyed:
		return {"status": "cancelled", "reason": "destroyed", "remaining": 0}
	if is_hatched:
		return {"status": "already_hatched", "remaining": 0}

	hatch_countdown = maxi(0, hatch_countdown - 1)
	countdown_ticked.emit(hatch_countdown)

	if hatch_countdown == 0:
		return hatch(grid, rng)

	return {"status": "counting_down", "remaining": hatch_countdown}

# ── Hatching Execution ───────────────────────────────────────────────────────
func hatch(grid: TacticalGrid = null, rng: RandomNumberGenerator = null) -> Dictionary:
	if is_destroyed:
		return {"status": "cancelled", "reason": "destroyed"}
	if is_hatched:
		return {"status": "already_hatched"}

	is_hatched = true

	# 1. Determine caste to spawn
	var caste_to_spawn: String = preferred_caste
	if caste_to_spawn.is_empty() or not IsectumCastes.has_caste(caste_to_spawn):
		caste_to_spawn = select_tier_2_caste(rng)

	# 2. Determine spawn cell (adjacent free walkable cell)
	var spawn_pos: Vector2i = find_adjacent_spawn_cell(grid)

	# 3. Calculate all adjacent cells for acid splash
	var affected_cells: Array[Vector2i] = get_adjacent_cells(grid)

	# 4. Apply acid damage to grid/units if grid is provided
	if grid != null:
		_apply_acid_to_grid(grid, affected_cells)

	acid_burst.emit(affected_cells, acid_damage)
	hatched.emit(caste_to_spawn, spawn_pos, affected_cells)

	return {
		"status": "hatched",
		"caste_id": caste_to_spawn,
		"spawn_pos": spawn_pos,
		"spawn_success": spawn_pos != Vector2i(-1, -1),
		"acid_damage": acid_damage,
		"acid_cells": affected_cells
	}

# ── Adjacent Geometry Helpers ────────────────────────────────────────────────
func get_adjacent_cells(grid: TacticalGrid = null) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if grid_position == Vector2i(-1, -1):
		return result

	var dirs: Array[Vector2i] = [
		Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1),
		Vector2i(-1, 0),                   Vector2i(1, 0),
		Vector2i(-1, 1),  Vector2i(0, 1),  Vector2i(1, 1)
	]

	for d in dirs:
		var n: Vector2i = grid_position + d
		if grid != null:
			if grid.is_valid_cell(n):
				result.append(n)
		else:
			if n.x >= 0 and n.x < 20 and n.y >= 0 and n.y < 20:
				result.append(n)

	return result

func find_adjacent_spawn_cell(grid: TacticalGrid) -> Vector2i:
	if grid == null:
		var neighbors: Array[Vector2i] = get_adjacent_cells(null)
		return neighbors[0] if not neighbors.is_empty() else Vector2i(-1, -1)

	for cell in get_adjacent_cells(grid):
		if grid.is_cell_walkable(cell) and not grid.is_cell_occupied(cell):
			return cell

	# Fallback: search radius 2 if immediate neighbors are blocked
	for dx in range(-2, 3):
		for dy in range(-2, 3):
			if maxi(absi(dx), absi(dy)) == 2:
				var candidate: Vector2i = grid_position + Vector2i(dx, dy)
				if grid.is_valid_cell(candidate) and grid.is_cell_walkable(candidate) and not grid.is_cell_occupied(candidate):
					return candidate

	return Vector2i(-1, -1)

func select_tier_2_caste(rng: RandomNumberGenerator = null) -> String:
	if rng != null:
		var idx: int = rng.randi_range(0, TIER_2_CASTES.size() - 1)
		return TIER_2_CASTES[idx]
	return TIER_2_CASTES[randi_range(0, TIER_2_CASTES.size() - 1)]

func _apply_acid_to_grid(grid: TacticalGrid, cells: Array[Vector2i]) -> void:
	for cell in cells:
		var unit: Variant = grid.get_unit_at(cell)
		if unit != null:
			if unit is Object and unit.has_method("take_damage"):
				unit.take_damage(acid_damage, "acido")
			elif unit is Dictionary:
				var cur_hp: int = int(unit.get("hp", unit.get("current_hp", 10)))
				unit["hp"] = maxi(0, cur_hp - acid_damage)
				unit["current_hp"] = unit["hp"]

		grid.apply_terrain_damage(cell, "acido")
```

---

## 4. Edge Case Matrix

| ID | Component | Scenario / Edge Case | Expected System Behavior |
|----|-----------|----------------------|--------------------------|
| EC-01 | `TorchLighting` | `heroes_positions` is empty (`[]`). | Grid has 0 lit cells. `is_cell_lit` returns `false` for all cells. No errors. |
| EC-02 | `TorchLighting` | Hero at corner `(0, 0)`. | Radius 3 generates cells only in `[0, 3] x [0, 3]` (16 cells). No negative coordinates. |
| EC-03 | `TorchLighting` | Hero at corner `(19, 19)`. | Radius 3 generates cells only in `[16, 19] x [16, 19]` (16 cells). No out-of-bounds coordinates. |
| EC-04 | `TorchLighting` | Overlapping heroes at `(5, 5)` and `(5, 6)`. | Mathematical union of lit cells without duplicates in `get_lit_cells()`. |
| EC-05 | `TorchLighting` | Relic `tocha_eterna` active (+2 bonus). | Visibility radius expands to 5 cells ($11 \times 11 = 121$ tiles centered). |
| EC-06 | `TorchLighting` | Ranged targeting (`range > 1`) into darkness. | Returns `false` from `can_target_cell`, emits `darkness_blocked_targeting`. |
| EC-07 | `TorchLighting` | Melee targeting (`range == 1`) in darkness. | Returns `true` from `can_target_cell` if within 1 Chebyshev step. |
| EC-08 | `TorchLighting` | Enemy situated in unlit cell. | `is_enemy_shrouded` is `true`, `ac_bonus = 2`, `blocks_ranged = true`. |
| EC-09 | `TorchLighting` | Lighting disabled (`is_enabled = false`). | Acts as daylight: all in-bounds cells lit, ranged targeting unblocked. |
| EC-10 | `ChitinCocoon` | Overkill damage (e.g. 30 damage on 15 HP). | HP clamped to 0. `is_destroyed` set to `true`, emits `destroyed`. |
| EC-11 | `ChitinCocoon` | Cocoon destroyed at turn 1 of 3. | `tick_round` halts, returns `{"status": "cancelled"}`, no hatch, no acid damage. |
| EC-12 | `ChitinCocoon` | Round ticks reaching exactly 0. | Spawns Tier 2 insect in adjacent cell, deals 5 acid damage to adjacent cells. |
| EC-13 | `ChitinCocoon` | Adjacent cells all blocked by walls/units. | Fallback searches radius 2; if fully blocked, returns `Vector2i(-1, -1)` without crash while still applying acid blast. |
| EC-14 | `ChitinCocoon` | Cocoon at corner `(0, 0)` hatches. | Only valid in-bounds adjacent cells `[(1,0), (0,1), (1,1)]` receive acid damage. |
| EC-15 | `ChitinCocoon` | Call `tick_round` after already hatched. | Idempotent guard: returns `{"status": "already_hatched"}`. |

---

## 5. GUT Test Design

The test suites will be written under `godot_project/test/unit/`:
- `test_torch_lighting.gd`
- `test_chitin_cocoon.gd`

### A. Test Suite: `test_torch_lighting.gd`
```gdscript
# res://test/unit/test_torch_lighting.gd
extends GutTest

var _torch: TorchLighting

func before_each() -> void:
	_torch = TorchLighting.new(20, 20, 3)

func after_each() -> void:
	_torch = null

# ── 1. Initialization & Defaults ─────────────────────────────────────────────
func test_initialization_defaults() -> void:
	# Arrange & Act
	var t: TorchLighting = TorchLighting.new()
	# Assert
	assert_eq(t.width, 20)
	assert_eq(t.height, 20)
	assert_eq(t.base_radius, 3)
	assert_eq(t.get_lit_cells().size(), 0)

# ── 2. Visibility & Chebyshev Math ───────────────────────────────────────────
func test_visibility_single_hero_center() -> void:
	# Arrange
	var hero_pos: Vector2i = Vector2i(10, 10)
	# Act
	_torch.update_visibility([hero_pos], 0)
	# Assert: (2*3 + 1)^2 = 49 cells
	assert_eq(_torch.get_lit_cells().size(), 49)
	assert_true(_torch.is_cell_lit(Vector2i(10, 10)))
	assert_true(_torch.is_cell_lit(Vector2i(7, 7)))   # Corner at Chebyshev dist 3
	assert_true(_torch.is_cell_lit(Vector2i(13, 13))) # Corner at Chebyshev dist 3
	assert_false(_torch.is_cell_lit(Vector2i(6, 10))) # Dist 4
	assert_false(_torch.is_cell_lit(Vector2i(10, 14))) # Dist 4

func test_visibility_corner_boundaries() -> void:
	# Arrange: Hero at top-left (0, 0)
	_torch.update_visibility([Vector2i(0, 0)], 0)
	# Act & Assert: [0..3] x [0..3] = 16 cells
	assert_eq(_torch.get_lit_cells().size(), 16)
	assert_true(_torch.is_cell_lit(Vector2i(0, 0)))
	assert_true(_torch.is_cell_lit(Vector2i(3, 3)))
	assert_false(_torch.is_cell_lit(Vector2i(4, 0)))

func test_empty_heroes_array_leaves_grid_dark() -> void:
	# Arrange & Act
	_torch.update_visibility([])
	# Assert
	assert_eq(_torch.get_lit_cells().size(), 0)
	assert_false(_torch.is_cell_lit(Vector2i(10, 10)))

func test_multiple_heroes_union_deduplicated() -> void:
	# Arrange: Two adjacent heroes at (5, 5) and (5, 6)
	_torch.update_visibility([Vector2i(5, 5), Vector2i(5, 6)], 0)
	var lit: Array[Vector2i] = _torch.get_lit_cells()
	# Assert: Total unique cells is 7 * 8 = 56 cells
	assert_eq(lit.size(), 56)
	assert_true(_torch.is_cell_lit(Vector2i(5, 5)))
	assert_true(_torch.is_cell_lit(Vector2i(5, 6)))

# ── 3. Relic Synergy (tocha_eterna) ──────────────────────────────────────────
func test_relic_tocha_eterna_bonus_radius_5() -> void:
	# Arrange: Hero at center with +2 bonus
	_torch.update_visibility([Vector2i(10, 10)], TorchLighting.TOCHA_ETERNA_BONUS_RADIUS)
	# Act & Assert: (2*5 + 1)^2 = 121 cells
	assert_eq(_torch.get_lit_cells().size(), 121)
	assert_true(_torch.is_cell_lit(Vector2i(5, 5)))   # Chebyshev dist 5
	assert_true(_torch.is_cell_lit(Vector2i(15, 15))) # Chebyshev dist 5
	assert_false(_torch.is_cell_lit(Vector2i(4, 10))) # Dist 6

func test_relic_calculation_helper() -> void:
	# Arrange & Act
	var bonus_1: int = _torch.calculate_bonus_from_relics(["tocha_eterna"])
	var bonus_2: int = _torch.calculate_bonus_from_relics(["reliquia_tocha_eterna"])
	var bonus_3: int = _torch.calculate_bonus_from_relics(["martelo_runico"])
	# Assert
	assert_eq(bonus_1, 2)
	assert_eq(bonus_2, 2)
	assert_eq(bonus_3, 0)

# ── 4. Darkness Targeting & Shroud Rules ─────────────────────────────────────
func test_can_target_cell_melee_allowed_in_darkness() -> void:
	# Arrange: Both cells unlit
	_torch.update_visibility([])
	# Act & Assert: Melee (range 1) between adjacent cells is allowed
	assert_true(_torch.can_target_cell(Vector2i(1, 1), Vector2i(1, 2), 1))

func test_can_target_cell_ranged_blocked_into_darkness() -> void:
	# Arrange: Attacker at (10, 10) lit; target at (0, 0) unlit
	_torch.update_visibility([Vector2i(10, 10)], 0)
	watch_signals(_torch)
	# Act
	var can_target: bool = _torch.can_target_cell(Vector2i(10, 10), Vector2i(0, 0), 15)
	# Assert
	assert_false(can_target, "Ranged targeting into darkness must be blocked")
	assert_signal_emitted(_torch, "darkness_blocked_targeting")

func test_can_target_cell_ranged_allowed_into_light() -> void:
	# Arrange: Both attacker and target inside light
	_torch.update_visibility([Vector2i(10, 10)], 0)
	# Act & Assert: Target at (8, 8) is lit
	assert_true(_torch.can_target_cell(Vector2i(10, 10), Vector2i(8, 8), 3))

func test_enemy_shroud_modifiers() -> void:
	# Arrange
	_torch.update_visibility([Vector2i(10, 10)], 0)
	# Act
	var dark_mod: Dictionary = _torch.get_shroud_modifiers(Vector2i(0, 0))
	var lit_mod: Dictionary = _torch.get_shroud_modifiers(Vector2i(10, 10))
	# Assert
	assert_true(dark_mod["is_shrouded"])
	assert_true(dark_mod["blocks_ranged"])
	assert_eq(dark_mod["ac_bonus"], 2)
	assert_false(lit_mod["is_shrouded"])
	assert_false(lit_mod["blocks_ranged"])
	assert_eq(lit_mod["ac_bonus"], 0)
```

### B. Test Suite: `test_chitin_cocoon.gd`
```gdscript
# res://test/unit/test_chitin_cocoon.gd
extends GutTest

var _cocoon: ChitinCocoon
var _grid: TacticalGrid

func before_each() -> void:
	_grid = TacticalGrid.new(20, 20)
	_cocoon = ChitinCocoon.new("cocoon_test", Vector2i(5, 5), 15, 3)

func after_each() -> void:
	_cocoon = null
	_grid = null

# ── 1. Initialization ────────────────────────────────────────────────────────
func test_cocoon_initialization() -> void:
	assert_eq(_cocoon.id, "cocoon_test")
	assert_eq(_cocoon.grid_position, Vector2i(5, 5))
	assert_eq(_cocoon.current_hp, 15)
	assert_eq(_cocoon.max_hp, 15)
	assert_eq(_cocoon.hatch_countdown, 3)
	assert_false(_cocoon.is_destroyed)
	assert_false(_cocoon.is_hatched)

# ── 2. Damage & Early Destruction (Cancellation) ─────────────────────────────
func test_apply_damage_partial() -> void:
	watch_signals(_cocoon)
	var taken: int = _cocoon.apply_damage(6)
	assert_eq(taken, 6)
	assert_eq(_cocoon.current_hp, 9)
	assert_false(_cocoon.is_destroyed)
	assert_signal_emitted(_cocoon, "damaged")

func test_destruction_cancels_hatching() -> void:
	watch_signals(_cocoon)
	# Destroy cocoon with 15 damage
	_cocoon.apply_damage(15)
	assert_true(_cocoon.is_destroyed)
	assert_signal_emitted(_cocoon, "destroyed")

	# Subsequent round ticks must be cancelled
	var res: Dictionary = _cocoon.tick_round(_grid)
	assert_eq(res["status"], "cancelled")
	assert_false(_cocoon.is_hatched)

# ── 3. Round Countdown & Hatching Sequence ────────────────────────────────────
func test_tick_round_countdown_decrement() -> void:
	watch_signals(_cocoon)
	var res1: Dictionary = _cocoon.tick_round(_grid)
	assert_eq(res1["status"], "counting_down")
	assert_eq(_cocoon.hatch_countdown, 2)

	var res2: Dictionary = _cocoon.tick_round(_grid)
	assert_eq(res2["status"], "counting_down")
	assert_eq(_cocoon.hatch_countdown, 1)
	assert_signal_emit_count(_cocoon, "countdown_ticked", 2)

func test_hatching_at_countdown_zero_spawns_and_bursts_acid() -> void:
	watch_signals(_cocoon)
	# Set a target dummy unit at adjacent cell (5, 6)
	var target_dummy: Dictionary = {"id": "hero_1", "hp": 20, "current_hp": 20}
	_grid.place_unit(target_dummy, Vector2i(5, 6))

	# Advance 3 rounds
	_cocoon.tick_round(_grid) # to 2
	_cocoon.tick_round(_grid) # to 1
	var hatch_res: Dictionary = _cocoon.tick_round(_grid) # to 0 -> hatches!

	assert_eq(hatch_res["status"], "hatched")
	assert_true(_cocoon.is_hatched)
	assert_signal_emitted(_cocoon, "hatched")
	assert_signal_emitted(_cocoon, "acid_burst")

	# Check acid damage (5 damage to adjacent unit)
	assert_eq(target_dummy["current_hp"], 15)

	# Verify spawned caste is canonical Tier 2
	assert_true(ChitinCocoon.TIER_2_CASTES.has(hatch_res["caste_id"]))
	assert_true(_grid.is_valid_cell(hatch_res["spawn_pos"]))

func test_cannot_hatch_twice() -> void:
	_cocoon.hatch_countdown = 1
	_cocoon.tick_round(_grid)
	assert_true(_cocoon.is_hatched)

	var second_try: Dictionary = _cocoon.tick_round(_grid)
	assert_eq(second_try["status"], "already_hatched")

func test_boundary_acid_burst_at_corner() -> void:
	var corner_cocoon: ChitinCocoon = ChitinCocoon.new("c_corner", Vector2i(0, 0), 15, 1)
	var res: Dictionary = corner_cocoon.tick_round(_grid)
	assert_eq(res["status"], "hatched")
	# Only 3 adjacent in-bounds cells: (1,0), (0,1), (1,1)
	assert_eq(res["acid_cells"].size(), 3)
	for cell in res["acid_cells"]:
		assert_true(_grid.is_valid_cell(cell))
```

---

## 6. Caveats

1. **Visual Rendering vs Domain Logic**:
   - `TorchLighting.gd` and `ChitinCocoon.gd` are pure RefCounted domain models.
   - The visual presentation layer (darkness canvas modulators, tile shaders, sprite flicker in `FortressBoardView.gd`) can listen to `TorchLighting.visibility_updated` and `ChitinCocoon.damaged`/`hatched` without domain logic coupling.
2. **Relic Registration**:
   - Relic `"tocha_eterna"` is already in `RelicManager.gd`. The helper `calculate_bonus_from_relics` or `update_visibility(heroes, bonus_radius)` provides direct integration.
3. **Line of Sight Obstacles**:
   - `TorchLighting` uses Chebyshev distance for ambient torch radius. If dense stone walls (`TERRENO_PAREDE`) should cast raycast shadow penumbras, `TacticalGrid.has_line_of_sight` can be queried in addition to `is_cell_lit`.

---

## 7. Conclusion

The design for Milestone M5 components (`TorchLighting.gd` and `ChitinCocoon.gd`) is complete, robust, strictly typed, zero-leak compliant, and fully specified:
- **`TorchLighting.gd`**:
  - Chebyshev radius 3 illumination around living heroes.
  - Relic synergy with `tocha_eterna` (+2 bonus radius, total 5).
  - Darkness rules: blocks ranged targeting into darkness (`darkness_blocked_targeting`); grants shrouded status to unlit enemies (+2 AC, ranged attack immunity).
- **`ChitinCocoon.gd`**:
  - 15 HP structure with 3-round hatch countdown.
  - Decrements each round; cancelled completely if destroyed before countdown reaches 0.
  - Hatches into a Tier 2 Isectum caste in an adjacent free cell and unleashes 5 acid damage in an adjacent burst.
- **GUT Test Suites**:
  - Full AAA test specifications covering happy paths, edge cases, boundary conditions, and signal verification.

Ready for immediate implementation by the assigned builder agent.

---

## 8. Verification Method

To independently verify the architecture and test design:
1. **File Locations**:
   - Confirm design file exists at: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1/handoff.md`.
2. **Baseline Test Execution**:
   - Run: `bash godot_project/run_gut_tests.sh`
   - Verify exit code 0 and all 873 tests pass.
3. **Implementation Verification (Downstream Builder)**:
   - Create `godot_project/scripts/tactical/TorchLighting.gd` and `godot_project/scripts/entities/ChitinCocoon.gd`.
   - Create test files `godot_project/test/unit/test_torch_lighting.gd` and `godot_project/test/unit/test_chitin_cocoon.gd`.
   - Run `bash godot_project/run_gut_tests.sh` to confirm 100% green tests.
