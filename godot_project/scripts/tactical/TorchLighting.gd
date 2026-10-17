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

# ── Coordinate Extraction Helper ─────────────────────────────────────────────
func _extract_pos(p: Variant) -> Vector2i:
	if p is Vector2i:
		return p
	elif p is Object and "grid_position" in p:
		return p.grid_position
	elif p is Dictionary:
		if p.has("grid_position") and p["grid_position"] is Vector2i:
			return p["grid_position"]
		elif p.has("pos") and p["pos"] is Vector2i:
			return p["pos"]
		elif p.has("spawn_pos") and p["spawn_pos"] is Vector2i:
			return p["spawn_pos"]
		elif p.has("x") and p.has("y"):
			return Vector2i(int(p["x"]), int(p["y"]))
	return Vector2i(-1, -1)

# ── Core Visibility Update ───────────────────────────────────────────────────
## Updates the lit area around all living heroes.
## Supports polymorphic parameter signatures:
## - update_visibility(heroes_positions: Array, bonus_radius: int = 0, grid = null)
## - update_visibility(heroes_positions: Array, grid: TacticalGrid)
func update_visibility(heroes_positions: Array, p2: Variant = 0, p3: Variant = null) -> void:
	var bonus: int = 0
	var grid: Variant = null

	if p2 != null and (p2 is int or p2 is float):
		bonus = int(p2)
	elif p2 != null and (p2 is TacticalGrid or (p2 is Object and p2.get_class() == "TacticalGrid")):
		grid = p2

	if p3 != null and (p3 is int or p3 is float):
		bonus = int(p3)
	elif p3 != null and (p3 is TacticalGrid or (p3 is Object and p3.get_class() == "TacticalGrid")):
		grid = p3

	if grid != null and "width" in grid and "height" in grid:
		width = grid.width
		height = grid.height

	_heroes_positions.clear()
	for h in heroes_positions:
		var pos: Vector2i = _extract_pos(h)
		if is_valid_cell(pos):
			_heroes_positions.append(pos)

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
func calculate_bonus_from_relics(relic_ids: Array) -> int:
	for rid in relic_ids:
		var norm: String = str(rid).to_lower().strip_edges()
		if norm == "tocha_eterna" or norm == "reliquia_tocha_eterna":
			return TOCHA_ETERNA_BONUS_RADIUS
	return 0

# ── Darkness Combat Rules ────────────────────────────────────────────────────
## Checks if targeting from attacker to target is allowed under darkness rules.
## - Melee attacks (attack_range <= 1 or dist <= 1) are permitted.
## - Ranged attacks (attack_range > 1 and dist > 1) are BLOCKED if target is unlit.
func can_target_cell(attacker: Variant, target: Variant, attack_range: int = 1) -> bool:
	var attacker_pos: Vector2i = _extract_pos(attacker)
	var target_pos: Vector2i = _extract_pos(target)

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
func is_enemy_shrouded(enemy_pos: Variant) -> bool:
	var pos: Vector2i = _extract_pos(enemy_pos)
	if not is_valid_cell(pos):
		return false
	if not is_enabled:
		return false
	return not is_cell_lit(pos)

## Returns combat shroud modifiers for an enemy at given position.
func get_shroud_modifiers(enemy_pos: Variant) -> Dictionary:
	var pos: Vector2i = _extract_pos(enemy_pos)
	var shrouded: bool = is_enemy_shrouded(pos)
	if shrouded:
		enemy_shrouded.emit(pos)
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
