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
func apply_damage(amount: int, _damage_type: String = "fisico") -> int:
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
func tick_round(grid: Variant = null, rng: RandomNumberGenerator = null) -> Dictionary:
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
func hatch(grid: Variant = null, rng: RandomNumberGenerator = null) -> Dictionary:
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
func get_adjacent_cells(grid: Variant = null) -> Array[Vector2i]:
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
		if grid != null and grid.has_method("is_valid_cell"):
			if grid.is_valid_cell(n):
				result.append(n)
		else:
			if n.x >= 0 and n.x < 20 and n.y >= 0 and n.y < 20:
				result.append(n)

	return result

func find_adjacent_spawn_cell(grid: Variant = null) -> Vector2i:
	var neighbors: Array[Vector2i] = get_adjacent_cells(grid)
	if grid == null:
		return neighbors[0] if not neighbors.is_empty() else Vector2i(-1, -1)

	for cell in neighbors:
		if grid.has_method("is_cell_walkable") and grid.has_method("is_cell_occupied"):
			if grid.is_cell_walkable(cell) and not grid.is_cell_occupied(cell):
				return cell

	# Fallback: search radius 2 if immediate neighbors are blocked
	for dx in range(-2, 3):
		for dy in range(-2, 3):
			if maxi(absi(dx), absi(dy)) == 2:
				var candidate: Vector2i = grid_position + Vector2i(dx, dy)
				if grid.has_method("is_valid_cell") and grid.is_valid_cell(candidate):
					if grid.is_cell_walkable(candidate) and not grid.is_cell_occupied(candidate):
						return candidate

	return Vector2i(-1, -1)

func select_tier_2_caste(rng: RandomNumberGenerator = null) -> String:
	if rng != null:
		var idx: int = rng.randi_range(0, TIER_2_CASTES.size() - 1)
		return TIER_2_CASTES[idx]
	return TIER_2_CASTES[randi_range(0, TIER_2_CASTES.size() - 1)]

func _apply_acid_to_grid(grid: Variant, cells: Array[Vector2i]) -> void:
	for cell in cells:
		if grid.has_method("get_unit_at"):
			var unit: Variant = grid.get_unit_at(cell)
			if unit != null:
				if unit is Object and unit.has_method("take_damage"):
					unit.take_damage(acid_damage)
				elif unit is Dictionary:
					var cur_hp: int = int(unit.get("hp", unit.get("current_hp", 10)))
					unit["hp"] = maxi(0, cur_hp - acid_damage)
					unit["current_hp"] = unit["hp"]

		if grid.has_method("apply_terrain_damage"):
			grid.apply_terrain_damage(cell, "acido")
