# res://scripts/tactical/TacticalGrid.gd
class_name TacticalGrid
extends RefCounted

## Signals
signal terrain_changed(pos: Vector2i, old_type: String, new_type: String)
signal structure_damaged(pos: Vector2i, current_hp: int, max_hp: int)
signal structure_destroyed(pos: Vector2i, new_terrain: String)
signal unit_placed(unit: Variant, pos: Vector2i)
signal unit_removed(unit: Variant, pos: Vector2i)
signal unit_moved(unit: Variant, from_pos: Vector2i, to_pos: Vector2i)
signal hazard_triggered(pos: Vector2i, hazard_type: String, unit: Variant)

## Constants: Terrain Types
const TERRENO_NORMAL: String = "NORMAL"
const TERRENO_FLORESTA: String = "FLORESTA"
const TERRENO_DIFICIL: String = "DIFICIL"
const TERRENO_PAREDE: String = "PAREDE"
const TERRENO_GELO: String = "GELO"
const TERRENO_FOGO: String = "FOGO"
const TERRENO_AGUA: String = "AGUA"
const TERRENO_ROCHA: String = "ROCHA"
const TERRENO_BARRIL: String = "BARRIL"
const TERRENO_VENENO: String = "VENENO"
const TERRENO_POISON: String = "POISON"
const TERRENO_CAMPO: String = "CAMPO"
const TERRENO_EXTERIOR: String = "EXTERIOR"
const TERRENO_CORREDOR: String = "CORREDOR"
const TERRENO_MURALHA_LO: String = "MURALHA_LO"
const TERRENO_SUBSOLO: String = "SUBSOLO"

## Constants: Cover Values
const COVER_NONE: int = 0
const COVER_HALF: int = 2             # Soft creature cover (+2 AC)
const COVER_LIGHT_ADJACENT: int = 3   # Adjacent forest / barrel (+3 AC)
const COVER_THREE_QUARTERS: int = 5   # Adjacent rock / wall (+5 AC)
const COVER_TOTAL: int = 1000         # Wall on LoS / impassable barrier

## Constants: Movement Costs
const COST_NORMAL: float = 1.0
const COST_DIFFICULT: float = 2.0
const COST_IMPASSABLE: float = 9999.0

## Enums
enum DistanceMetric {
	CHEBYSHEV, # D&D 5e standard (diagonal = 1.0)
	EUCLIDEAN, # Real geometric distance (diagonal = sqrt(2) ≈ 1.414)
	MANHATTAN  # 4-way grid distance (|dx| + |dy|)
}

## Grid Configuration
var width: int = 20
var height: int = 20
var metric: DistanceMetric = DistanceMetric.CHEBYSHEV
var allow_corner_cutting: bool = false
var strict_corner_cutting: bool = false

## Internal Grids
var _terrain_grid: Array[Array] = []
var _elevation_grid: Array[Array] = []
var _structure_hp_grid: Array[Array] = []
var _units_grid: Array[Array] = []

## Native Godot AStar2D Instance
var _astar: AStar2D = AStar2D.new()

## Initialization
func _init(p_width: int = 20, p_height: int = 20, p_metric: DistanceMetric = DistanceMetric.CHEBYSHEV) -> void:
	width = p_width
	height = p_height
	metric = p_metric
	_allocate_grids()
	rebuild_astar()

## Grid Allocation & Clearing
func _allocate_grids() -> void:
	_terrain_grid.clear()
	_elevation_grid.clear()
	_structure_hp_grid.clear()
	_units_grid.clear()
	for y in range(height):
		var row_terrain: Array[String] = []
		var row_elev: Array[int] = []
		var row_hp: Array[int] = []
		var row_units: Array[Variant] = []
		for x in range(width):
			row_terrain.append(TERRENO_NORMAL)
			row_elev.append(0)
			row_hp.append(0)
			row_units.append(null)
		_terrain_grid.append(row_terrain)
		_elevation_grid.append(row_elev)
		_structure_hp_grid.append(row_hp)
		_units_grid.append(row_units)

## Coordinate & Bounds Methods
func is_valid_cell(pos: Vector2i) -> bool:
	return pos.x >= 0 and pos.x < width and pos.y >= 0 and pos.y < height

func point_to_id(pos: Vector2i) -> int:
	return pos.y * width + pos.x

func id_to_point(id: int) -> Vector2i:
	return Vector2i(id % width, id / width)

## Terrain & Walkability
func get_cell_type(pos: Vector2i) -> String:
	if not is_valid_cell(pos):
		return TERRENO_PAREDE
	return _terrain_grid[pos.y][pos.x]

func set_cell_type(pos: Vector2i, type: String) -> void:
	if not is_valid_cell(pos):
		return
	var old: String = _terrain_grid[pos.y][pos.x]
	_terrain_grid[pos.y][pos.x] = type
	if type in [TERRENO_FLORESTA, TERRENO_ROCHA, TERRENO_BARRIL]:
		_structure_hp_grid[pos.y][pos.x] = 20
	else:
		_structure_hp_grid[pos.y][pos.x] = 0
	_update_astar_cell(pos)
	terrain_changed.emit(pos, old, type)

func get_elevation(pos: Vector2i) -> int:
	if not is_valid_cell(pos):
		return 0
	return _elevation_grid[pos.y][pos.x]

func set_elevation(pos: Vector2i, elevation: int) -> void:
	if not is_valid_cell(pos):
		return
	_elevation_grid[pos.y][pos.x] = elevation

func get_structure_hp(pos: Vector2i) -> int:
	if not is_valid_cell(pos):
		return 0
	return _structure_hp_grid[pos.y][pos.x]

func set_structure_hp(pos: Vector2i, hp: int) -> void:
	if not is_valid_cell(pos):
		return
	_structure_hp_grid[pos.y][pos.x] = hp

func is_cell_walkable(pos: Vector2i) -> bool:
	if not is_valid_cell(pos):
		return false
	var t: String = _terrain_grid[pos.y][pos.x]
	return t != TERRENO_PAREDE and t != TERRENO_ROCHA and t != TERRENO_BARRIL

func get_terrain_cost(pos: Vector2i) -> float:
	if not is_valid_cell(pos) or not is_cell_walkable(pos):
		return COST_IMPASSABLE
	var t: String = _terrain_grid[pos.y][pos.x]
	if t == TERRENO_DIFICIL:
		return COST_DIFFICULT
	return COST_NORMAL

## Destructible Structures
func apply_structure_damage(pos: Vector2i, damage: int) -> bool:
	if not is_valid_cell(pos):
		return false
	if _structure_hp_grid[pos.y][pos.x] <= 0:
		return false
	_structure_hp_grid[pos.y][pos.x] = maxi(0, _structure_hp_grid[pos.y][pos.x] - damage)
	var current_hp: int = _structure_hp_grid[pos.y][pos.x]
	structure_damaged.emit(pos, current_hp, 20)
	if current_hp <= 0:
		set_cell_type(pos, TERRENO_DIFICIL)
		structure_destroyed.emit(pos, TERRENO_DIFICIL)
		return true
	return false

## Border Limiters
func add_border_walls() -> void:
	for x in range(width):
		set_cell_type(Vector2i(x, 0), TERRENO_PAREDE)
		set_cell_type(Vector2i(x, height - 1), TERRENO_PAREDE)
		_units_grid[0][x] = null
		_units_grid[height - 1][x] = null
	for y in range(height):
		set_cell_type(Vector2i(0, y), TERRENO_PAREDE)
		set_cell_type(Vector2i(width - 1, y), TERRENO_PAREDE)
		_units_grid[y][0] = null
		_units_grid[y][width - 1] = null
	rebuild_astar()

## Elemental Terrain Reactions
func apply_terrain_damage(pos: Vector2i, damage_type: String) -> void:
	if not is_valid_cell(pos):
		return
	var cur: String = _terrain_grid[pos.y][pos.x]
	var dmg: String = damage_type.to_lower()
	if dmg == "fogo" or dmg == "fire":
		if cur == TERRENO_FLORESTA:
			set_cell_type(pos, TERRENO_FOGO)
		elif cur == TERRENO_GELO:
			set_cell_type(pos, TERRENO_AGUA)
	elif dmg == "gelo" or dmg == "ice":
		if cur == TERRENO_AGUA:
			set_cell_type(pos, TERRENO_GELO)
		elif cur == TERRENO_FOGO:
			set_cell_type(pos, TERRENO_NORMAL)

## Hazard Triggers
func check_hazard(pos: Vector2i, unit: Variant) -> Dictionary:
	if not is_valid_cell(pos):
		return {"type": "none"}
	var t: String = _terrain_grid[pos.y][pos.x]
	if t == TERRENO_GELO:
		hazard_triggered.emit(pos, "ice_slip", unit)
		return {"type": "slip", "chance": 0.5}
	elif t == TERRENO_FOGO:
		hazard_triggered.emit(pos, "fire_damage", unit)
		return {"type": "fire", "damage": 4} # 1d6 avg / hazard
	elif t == TERRENO_VENENO or t == TERRENO_POISON:
		hazard_triggered.emit(pos, "poison_pool", unit)
		return {"type": "poison", "damage": 2}
	return {"type": "none"}

## Unit Occupancy Management
func place_unit(unit: Variant, pos: Vector2i) -> bool:
	if not is_valid_cell(pos) or not is_cell_walkable(pos):
		return false
	if _units_grid[pos.y][pos.x] != null:
		return false
	_units_grid[pos.y][pos.x] = unit
	unit_placed.emit(unit, pos)
	return true

func remove_unit(pos: Vector2i) -> Variant:
	if not is_valid_cell(pos):
		return null
	var u: Variant = _units_grid[pos.y][pos.x]
	_units_grid[pos.y][pos.x] = null
	if u != null:
		unit_removed.emit(u, pos)
	return u

func move_unit(from_pos: Vector2i, to_pos: Vector2i) -> bool:
	if not is_valid_cell(from_pos) or not is_valid_cell(to_pos):
		return false
	var u: Variant = _units_grid[from_pos.y][from_pos.x]
	if u == null:
		return false
	if not is_cell_walkable(to_pos) or (_units_grid[to_pos.y][to_pos.x] != null and _units_grid[to_pos.y][to_pos.x] != u):
		return false
	_units_grid[from_pos.y][from_pos.x] = null
	_units_grid[to_pos.y][to_pos.x] = u
	unit_moved.emit(u, from_pos, to_pos)
	return true

func get_unit_at(pos: Vector2i) -> Variant:
	if not is_valid_cell(pos):
		return null
	return _units_grid[pos.y][pos.x]

func is_cell_occupied(pos: Vector2i) -> bool:
	if not is_valid_cell(pos):
		return false
	return _units_grid[pos.y][pos.x] != null

## AStar2D Graph Construction
func rebuild_astar() -> void:
	_astar.clear()
	for y in range(height):
		for x in range(width):
			var pos: Vector2i = Vector2i(x, y)
			var id: int = point_to_id(pos)
			_astar.add_point(id, Vector2(x, y), get_terrain_cost(pos))
			if not is_cell_walkable(pos):
				_astar.set_point_disabled(id, true)

	for y in range(height):
		for x in range(width):
			var pos: Vector2i = Vector2i(x, y)
			if not is_cell_walkable(pos):
				continue
			_connect_neighbors(pos)

func _connect_neighbors(pos: Vector2i) -> void:
	var id: int = point_to_id(pos)
	var dirs: Array[Vector2i] = [
		Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0),
		Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)
	]
	for d in dirs:
		var n_pos: Vector2i = pos + d
		if not is_valid_cell(n_pos) or not is_cell_walkable(n_pos):
			continue
		
		# Corner cutting check on diagonal moves
		if abs(d.x) == 1 and abs(d.y) == 1 and not allow_corner_cutting:
			var ortho1: Vector2i = Vector2i(pos.x + d.x, pos.y)
			var ortho2: Vector2i = Vector2i(pos.x, pos.y + d.y)
			var o1_blocked: bool = not is_cell_walkable(ortho1)
			var o2_blocked: bool = not is_cell_walkable(ortho2)
			if (o1_blocked and o2_blocked) or (strict_corner_cutting and (o1_blocked or o2_blocked)):
				continue

		var n_id: int = point_to_id(n_pos)
		if not _astar.are_points_connected(id, n_id):
			_astar.connect_points(id, n_id, true)

func _update_astar_cell(pos: Vector2i) -> void:
	var id: int = point_to_id(pos)
	_astar.set_point_weight_scale(id, get_terrain_cost(pos))
	_astar.set_point_disabled(id, not is_cell_walkable(pos))
	
	# Disconnect and reconnect to update corner cutting if obstacles changed
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			var check_pos: Vector2i = pos + Vector2i(dx, dy)
			if is_valid_cell(check_pos):
				var check_id: int = point_to_id(check_pos)
				# Disconnect all existing links to recompute cleanly
				for c_id in _astar.get_point_connections(check_id):
					_astar.disconnect_points(check_id, c_id)
				if is_cell_walkable(check_pos):
					_connect_neighbors(check_pos)

## Pathfinding Execution
func find_path(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false, max_movement: float = -1.0) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if from_pos == to_pos or not is_valid_cell(from_pos) or not is_valid_cell(to_pos):
		return result
	if not is_cell_walkable(to_pos):
		return result

	var disabled_ids: Array[int] = []
	if not ignore_units:
		for y in range(height):
			for x in range(width):
				var p: Vector2i = Vector2i(x, y)
				if p == from_pos or p == to_pos:
					continue
				if _units_grid[y][x] != null:
					var uid: int = point_to_id(p)
					if not _astar.is_point_disabled(uid):
						_astar.set_point_disabled(uid, true)
						disabled_ids.append(uid)

	var from_id: int = point_to_id(from_pos)
	var to_id: int = point_to_id(to_pos)
	var raw_path: PackedVector2Array = _astar.get_point_path(from_id, to_id)

	# Restore disabled unit cells
	for uid in disabled_ids:
		_astar.set_point_disabled(uid, false)

	if raw_path.size() <= 1:
		return result

	var accumulated_cost: float = 0.0
	for i in range(1, raw_path.size()):
		var step: Vector2i = Vector2i(int(round(raw_path[i].x)), int(round(raw_path[i].y)))
		var step_cost: float = get_terrain_cost(step)
		if metric == DistanceMetric.EUCLIDEAN:
			var prev_step: Vector2i = Vector2i(int(round(raw_path[i-1].x)), int(round(raw_path[i-1].y)))
			var is_diag: bool = abs(step.x - prev_step.x) == 1 and abs(step.y - prev_step.y) == 1
			if is_diag:
				step_cost *= 1.41421356
		if max_movement > 0.0 and (accumulated_cost + step_cost) > max_movement:
			break
		accumulated_cost += step_cost
		result.append(step)

	return result

## Line of Sight & Bresenham Raycasting
func get_bresenham_line(from_pos: Vector2i, to_pos: Vector2i) -> Array[Vector2i]:
	var points: Array[Vector2i] = []
	var x0: int = from_pos.x
	var y0: int = from_pos.y
	var x1: int = to_pos.x
	var y1: int = to_pos.y
	var dx: int = abs(x1 - x0)
	var dy: int = abs(y1 - y0)
	var sx: int = 1 if x0 < x1 else -1
	var sy: int = 1 if y0 < y1 else -1
	var err: int = dx - dy
	var cx: int = x0
	var cy: int = y0

	while true:
		if not (cx == x0 and cy == y0):
			points.append(Vector2i(cx, cy))
		if cx == x1 and cy == y1:
			break
		var e2: int = 2 * err
		if e2 > -dy:
			err -= dy
			cx += sx
		if e2 < dx:
			err += dx
			cy += sy
	return points

func has_line_of_sight(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false) -> bool:
	if from_pos == to_pos:
		return true
	if not is_valid_cell(from_pos) or not is_valid_cell(to_pos):
		return false
	var line: Array[Vector2i] = get_bresenham_line(from_pos, to_pos)
	for i in range(line.size()):
		var pt: Vector2i = line[i]
		if _terrain_grid[pt.y][pt.x] == TERRENO_PAREDE or _terrain_grid[pt.y][pt.x] == TERRENO_ROCHA:
			return false
		if not ignore_units and i < (line.size() - 1):
			if _units_grid[pt.y][pt.x] != null:
				return false
	return true

## Cover Calculations
func get_raycast_cover(attacker_pos: Vector2i, target_pos: Vector2i) -> int:
	if attacker_pos == target_pos:
		return COVER_NONE
	if not is_valid_cell(attacker_pos) or not is_valid_cell(target_pos):
		return COVER_NONE
	var line: Array[Vector2i] = get_bresenham_line(attacker_pos, target_pos)
	var has_creature_soft_cover: bool = false

	for i in range(line.size()):
		var pt: Vector2i = line[i]
		if _terrain_grid[pt.y][pt.x] == TERRENO_PAREDE or _terrain_grid[pt.y][pt.x] == TERRENO_ROCHA:
			return COVER_TOTAL
		if i < (line.size() - 1): # Exclude target cell itself
			if _units_grid[pt.y][pt.x] != null:
				has_creature_soft_cover = true

	if has_creature_soft_cover:
		return COVER_HALF
	return COVER_NONE

func get_adjacent_cover_bonus(pos: Vector2i) -> int:
	if not is_valid_cell(pos):
		return COVER_NONE
	var max_bonus: int = 0
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			if dx == 0 and dy == 0:
				continue
			var n: Vector2i = pos + Vector2i(dx, dy)
			if is_valid_cell(n):
				var t: String = _terrain_grid[n.y][n.x]
				if t == TERRENO_FLORESTA or t == TERRENO_BARRIL:
					max_bonus = maxi(max_bonus, COVER_LIGHT_ADJACENT)
				elif t == TERRENO_ROCHA or t == TERRENO_PAREDE:
					max_bonus = maxi(max_bonus, COVER_THREE_QUARTERS)
	return max_bonus

func get_total_cover_bonus(attacker_pos: Vector2i, target_pos: Vector2i) -> int:
	var ray_cover: int = get_raycast_cover(attacker_pos, target_pos)
	if ray_cover >= COVER_TOTAL:
		return COVER_TOTAL
	return maxi(ray_cover, get_adjacent_cover_bonus(target_pos))

## Distance Helpers
func calculate_chebyshev_distance(p1: Vector2i, p2: Vector2i) -> int:
	return maxi(abs(p1.x - p2.x), abs(p1.y - p2.y))

func calculate_manhattan_distance(p1: Vector2i, p2: Vector2i) -> int:
	return abs(p1.x - p2.x) + abs(p1.y - p2.y)

func calculate_euclidean_distance(p1: Vector2i, p2: Vector2i) -> float:
	return Vector2(p1).distance_to(Vector2(p2))
