# res://scripts/cerco/FortressBoard.gd
class_name FortressBoard
extends RefCounted

## FortressBoard: 20x20 discrete board representing the 17 logical zones of the Cerco fortress.
## Manages 400-cell coordinate mapping, elevation layers, adjacency & invasion graphs,
## wall integrity/breaches, and unit positional tracking.

# ── Signals ──────────────────────────────────────────────────────────────────
signal wall_damaged(wall_id: String, amount: int, remaining_hp: int)
signal wall_repaired(wall_id: String, amount: int, new_hp: int)
signal wall_breached(wall_id: String)
signal unit_placed(unit_id: String, pos: Vector2i, zone_id: String)
signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i, from_zone: String, to_zone: String)
signal unit_removed(unit_id: String, last_pos: Vector2i, last_zone: String)
signal unit_stats_changed(unit_id: String, unit_data: Dictionary)
signal item_placed(pos: Vector2i, item_data: Dictionary)
signal item_collected(unit_id: String, pos: Vector2i, item_data: Dictionary)
signal item_removed(pos: Vector2i)

# ── Constants: Item Types ───────────────────────────────────────────────────
const ITEM_CRISTAL: String = "CRISTAL"
const ITEM_CHEST: String = "CHEST"
const ITEM_POTION: String = "POTION"
const ITEM_METAL: String = "METAL"
const ITEM_WOOD: String = "WOOD"
const ITEM_LEATHER: String = "LEATHER"
const ITEM_GOLD: String = "GOLD"

# ── Constants: Grid Dimensions ───────────────────────────────────────────────
const GRID_WIDTH: int = 20
const GRID_HEIGHT: int = 20
const TOTAL_CELLS: int = 400
const DEFAULT_WALL_MAX_HP: int = 100

# ── Constants: 17 Canonical Fortress Zones ──────────────────────────────────
# 1. Central Core
const ZONE_CAMARA_CENTRAL: String = "CAMARA_CENTRAL"

# 2. Workshops & Courtyard (Interior)
const ZONE_CARPINTARIA: String = "CARPINTARIA"
const ZONE_CURTUME: String = "CURTUME"
const ZONE_FUNDICAO: String = "FUNDICAO"
const ZONE_PATIO_CENTRAL: String = "PATIO_CENTRAL"

# 3. Perimeter Walls (Elevation +1)
const ZONE_MURALHA_NORTE: String = "MURALHA_NORTE"
const ZONE_MURALHA_SUL: String = "MURALHA_SUL"
const ZONE_MURALHA_LESTE: String = "MURALHA_LESTE"
const ZONE_MURALHA_OESTE: String = "MURALHA_OESTE"

# 4. Corner Watch Towers (Elevation +2)
const ZONE_TORRE_NOROESTE: String = "TORRE_NOROESTE"
const ZONE_TORRE_NORDESTE: String = "TORRE_NORDESTE"
const ZONE_TORRE_SUDOESTE: String = "TORRE_SUDOESTE"
const ZONE_TORRE_SUDESTE: String = "TORRE_SUDESTE"

# 5. Outer Invasion Spawn Grounds (Elevation 0)
const ZONE_SPAWN_NORTE: String = "SPAWN_NORTE"
const ZONE_SPAWN_SUL: String = "SPAWN_SUL"
const ZONE_SPAWN_LESTE: String = "SPAWN_LESTE"
const ZONE_SPAWN_OESTE: String = "SPAWN_OESTE"

# ── Groupings ────────────────────────────────────────────────────────────────
const ALL_ZONES: Array[String] = [
	ZONE_CAMARA_CENTRAL,
	ZONE_CARPINTARIA,
	ZONE_CURTUME,
	ZONE_FUNDICAO,
	ZONE_PATIO_CENTRAL,
	ZONE_MURALHA_NORTE,
	ZONE_MURALHA_SUL,
	ZONE_MURALHA_LESTE,
	ZONE_MURALHA_OESTE,
	ZONE_TORRE_NOROESTE,
	ZONE_TORRE_NORDESTE,
	ZONE_TORRE_SUDOESTE,
	ZONE_TORRE_SUDESTE,
	ZONE_SPAWN_NORTE,
	ZONE_SPAWN_SUL,
	ZONE_SPAWN_LESTE,
	ZONE_SPAWN_OESTE
]

const ALL_WALLS: Array[String] = [
	ZONE_MURALHA_NORTE,
	ZONE_MURALHA_SUL,
	ZONE_MURALHA_LESTE,
	ZONE_MURALHA_OESTE
]

const ALL_TOWERS: Array[String] = [
	ZONE_TORRE_NOROESTE,
	ZONE_TORRE_NORDESTE,
	ZONE_TORRE_SUDOESTE,
	ZONE_TORRE_SUDESTE
]

const ALL_SPAWNS: Array[String] = [
	ZONE_SPAWN_NORTE,
	ZONE_SPAWN_SUL,
	ZONE_SPAWN_LESTE,
	ZONE_SPAWN_OESTE
]

const ALL_WORKSHOPS: Array[String] = [
	ZONE_CARPINTARIA,
	ZONE_CURTUME,
	ZONE_FUNDICAO
]

# ── Internal State ───────────────────────────────────────────────────────────
var _cell_to_zone: Dictionary = {}        # Vector2i -> String
var _zone_to_cells: Dictionary = {}       # String -> Array[Vector2i]
var _wall_hp: Dictionary = {}             # String -> int
var _wall_max_hp: Dictionary = {}         # String -> int
var _unit_positions: Dictionary = {}      # String -> Vector2i
var _cell_units: Dictionary = {}          # Vector2i -> Array[String]
var _zone_units: Dictionary = {}          # String -> Array[String]
var _unit_data: Dictionary = {}           # String -> Dictionary
var _items: Dictionary = {}               # Vector2i -> Dictionary

# ── Initialization ───────────────────────────────────────────────────────────
func _init() -> void:
	_initialize_zone_mapping()
	_initialize_walls()
	_initialize_unit_tracking()
	_initialize_items()

func _initialize_items() -> void:
	_items.clear()

func _initialize_zone_mapping() -> void:
	_cell_to_zone.clear()
	_zone_to_cells.clear()

	for z in ALL_ZONES:
		var cell_arr: Array[Vector2i] = []
		_zone_to_cells[z] = cell_arr

	for y in range(GRID_HEIGHT):
		for x in range(GRID_WIDTH):
			var cell: Vector2i = Vector2i(x, y)
			var zone_id: String = _calculate_zone_for_cell(x, y)
			_cell_to_zone[cell] = zone_id
			(_zone_to_cells[zone_id] as Array[Vector2i]).append(cell)

func _calculate_zone_for_cell(x: int, y: int) -> String:
	# 1. Four Corner Watch Towers (4x4 cells each = 16 cells per tower)
	if x >= 0 and x < 4 and y >= 0 and y < 4:
		return ZONE_TORRE_NOROESTE
	elif x >= 16 and x < 20 and y >= 0 and y < 4:
		return ZONE_TORRE_NORDESTE
	elif x >= 0 and x < 4 and y >= 16 and y < 20:
		return ZONE_TORRE_SUDOESTE
	elif x >= 16 and x < 20 and y >= 16 and y < 20:
		return ZONE_TORRE_SUDESTE

	# 2. Outer Invasion Spawns (outermost 2-cell perimeter bands)
	elif y >= 0 and y < 2:
		return ZONE_SPAWN_NORTE
	elif y >= 18 and y < 20:
		return ZONE_SPAWN_SUL
	elif x >= 0 and x < 2:
		return ZONE_SPAWN_OESTE
	elif x >= 18 and x < 20:
		return ZONE_SPAWN_LESTE

	# 3. Perimeter Walls (2-cell defensive perimeter bands)
	elif y >= 2 and y < 4:
		return ZONE_MURALHA_NORTE
	elif y >= 16 and y < 18:
		return ZONE_MURALHA_SUL
	elif x >= 2 and x < 4:
		return ZONE_MURALHA_OESTE
	elif x >= 16 and x < 18:
		return ZONE_MURALHA_LESTE

	# 4. Central Core: Câmara Central (4x4 center = 16 cells)
	elif x >= 8 and x < 12 and y >= 8 and y < 12:
		return ZONE_CAMARA_CENTRAL

	# 5. Interior Quadrants: Workshops & Courtyard (32 cells each)
	else:
		var dx: float = float(x) - 9.5
		var dy: float = float(y) - 9.5
		if absf(dy) > absf(dx):
			return ZONE_CARPINTARIA if dy < 0.0 else ZONE_CURTUME
		elif absf(dx) > absf(dy):
			return ZONE_FUNDICAO if dx < 0.0 else ZONE_PATIO_CENTRAL
		else:
			# Diagonal tie-breaker for perfect 32-cell balance
			if dy < 0.0 and dx < 0.0:
				return ZONE_FUNDICAO
			elif dy < 0.0 and dx > 0.0:
				return ZONE_CARPINTARIA
			elif dy > 0.0 and dx < 0.0:
				return ZONE_CURTUME
			else:
				return ZONE_PATIO_CENTRAL

func _initialize_walls() -> void:
	_wall_hp.clear()
	_wall_max_hp.clear()
	for wall_id in ALL_WALLS:
		_wall_hp[wall_id] = DEFAULT_WALL_MAX_HP
		_wall_max_hp[wall_id] = DEFAULT_WALL_MAX_HP

func _initialize_unit_tracking() -> void:
	_unit_positions.clear()
	_cell_units.clear()
	_zone_units.clear()
	for z in ALL_ZONES:
		var arr: Array[String] = []
		_zone_units[z] = arr

# ── Grid & Cell Validation ───────────────────────────────────────────────────
func is_valid_cell(pos: Vector2i) -> bool:
	return pos.x >= 0 and pos.x < GRID_WIDTH and pos.y >= 0 and pos.y < GRID_HEIGHT

func get_zone_at(pos: Vector2i) -> String:
	if not is_valid_cell(pos):
		return ""
	return _cell_to_zone.get(pos, "")

func get_cells_in_zone(zone_id: String) -> Array[Vector2i]:
	var norm: String = zone_id.to_upper()
	if _zone_to_cells.has(norm):
		var orig: Array[Vector2i] = _zone_to_cells[norm]
		var copy_arr: Array[Vector2i] = []
		copy_arr.assign(orig)
		return copy_arr
	return []

func get_zone_cell_count(zone_id: String) -> int:
	var norm: String = zone_id.to_upper()
	if _zone_to_cells.has(norm):
		return (_zone_to_cells[norm] as Array[Vector2i]).size()
	return 0

# ── Elevation Levels ─────────────────────────────────────────────────────────
## Elevation: 0 for Spawns, Workshops, Patio, Camara; 1 for Walls; 2 for Towers.
func get_elevation(zone_id: String) -> int:
	var norm: String = zone_id.to_upper()
	if norm in ALL_TOWERS:
		return 2
	elif norm in ALL_WALLS:
		return 1
	return 0

func get_elevation_at(pos: Vector2i) -> int:
	var zone_id: String = get_zone_at(pos)
	if zone_id.is_empty():
		return 0
	return get_elevation(zone_id)

# ── Adjacency & Invasion Graphs ──────────────────────────────────────────────
func get_adjacent_zones(zone_id: String) -> Array[String]:
	var norm: String = zone_id.to_upper()
	var result: Array[String] = []

	match norm:
		ZONE_SPAWN_NORTE:
			result = [ZONE_MURALHA_NORTE, ZONE_TORRE_NOROESTE, ZONE_TORRE_NORDESTE]
		ZONE_SPAWN_SUL:
			result = [ZONE_MURALHA_SUL, ZONE_TORRE_SUDOESTE, ZONE_TORRE_SUDESTE]
		ZONE_SPAWN_OESTE:
			result = [ZONE_MURALHA_OESTE, ZONE_TORRE_NOROESTE, ZONE_TORRE_SUDOESTE]
		ZONE_SPAWN_LESTE:
			result = [ZONE_MURALHA_LESTE, ZONE_TORRE_NORDESTE, ZONE_TORRE_SUDESTE]

		ZONE_TORRE_NOROESTE:
			result = [ZONE_MURALHA_NORTE, ZONE_MURALHA_OESTE, ZONE_SPAWN_NORTE, ZONE_SPAWN_OESTE]
		ZONE_TORRE_NORDESTE:
			result = [ZONE_MURALHA_NORTE, ZONE_MURALHA_LESTE, ZONE_SPAWN_NORTE, ZONE_SPAWN_LESTE]
		ZONE_TORRE_SUDOESTE:
			result = [ZONE_MURALHA_SUL, ZONE_MURALHA_OESTE, ZONE_SPAWN_SUL, ZONE_SPAWN_OESTE]
		ZONE_TORRE_SUDESTE:
			result = [ZONE_MURALHA_SUL, ZONE_MURALHA_LESTE, ZONE_SPAWN_SUL, ZONE_SPAWN_LESTE]

		ZONE_MURALHA_NORTE:
			result = [ZONE_SPAWN_NORTE, ZONE_TORRE_NOROESTE, ZONE_TORRE_NORDESTE, ZONE_CARPINTARIA]
		ZONE_MURALHA_SUL:
			result = [ZONE_SPAWN_SUL, ZONE_TORRE_SUDOESTE, ZONE_TORRE_SUDESTE, ZONE_CURTUME]
		ZONE_MURALHA_OESTE:
			result = [ZONE_SPAWN_OESTE, ZONE_TORRE_NOROESTE, ZONE_TORRE_SUDOESTE, ZONE_FUNDICAO]
		ZONE_MURALHA_LESTE:
			result = [ZONE_SPAWN_LESTE, ZONE_TORRE_NORDESTE, ZONE_TORRE_SUDESTE, ZONE_PATIO_CENTRAL]

		ZONE_CARPINTARIA:
			result = [ZONE_MURALHA_NORTE, ZONE_FUNDICAO, ZONE_PATIO_CENTRAL, ZONE_CAMARA_CENTRAL]
		ZONE_CURTUME:
			result = [ZONE_MURALHA_SUL, ZONE_FUNDICAO, ZONE_PATIO_CENTRAL, ZONE_CAMARA_CENTRAL]
		ZONE_FUNDICAO:
			result = [ZONE_MURALHA_OESTE, ZONE_CARPINTARIA, ZONE_CURTUME, ZONE_CAMARA_CENTRAL]
		ZONE_PATIO_CENTRAL:
			result = [ZONE_MURALHA_LESTE, ZONE_CARPINTARIA, ZONE_CURTUME, ZONE_CAMARA_CENTRAL]

		ZONE_CAMARA_CENTRAL:
			result = [ZONE_CARPINTARIA, ZONE_CURTUME, ZONE_FUNDICAO, ZONE_PATIO_CENTRAL]
		_:
			result = []

	return result

func get_next_invasion_zones(zone_id: String) -> Array[String]:
	var norm: String = zone_id.to_upper()
	var result: Array[String] = []

	match norm:
		ZONE_SPAWN_NORTE:
			result = [ZONE_MURALHA_NORTE]
		ZONE_SPAWN_SUL:
			result = [ZONE_MURALHA_SUL]
		ZONE_SPAWN_OESTE:
			result = [ZONE_MURALHA_OESTE]
		ZONE_SPAWN_LESTE:
			result = [ZONE_MURALHA_LESTE]

		ZONE_MURALHA_NORTE:
			result = [ZONE_CARPINTARIA]
		ZONE_MURALHA_SUL:
			result = [ZONE_CURTUME]
		ZONE_MURALHA_OESTE:
			result = [ZONE_FUNDICAO]
		ZONE_MURALHA_LESTE:
			result = [ZONE_PATIO_CENTRAL]

		ZONE_CARPINTARIA:
			result = [ZONE_CAMARA_CENTRAL]
		ZONE_CURTUME:
			result = [ZONE_CAMARA_CENTRAL]
		ZONE_FUNDICAO:
			result = [ZONE_CAMARA_CENTRAL]
		ZONE_PATIO_CENTRAL:
			result = [ZONE_CAMARA_CENTRAL]

		ZONE_CAMARA_CENTRAL:
			# Final objective reached: invasion complete
			result = []
		_:
			result = []

	return result

# ── Wall Integrity System ────────────────────────────────────────────────────
func get_wall_hp(wall_id: String) -> int:
	var norm: String = wall_id.to_upper()
	return _wall_hp.get(norm, 0)

func get_wall_max_hp(wall_id: String) -> int:
	var norm: String = wall_id.to_upper()
	return _wall_max_hp.get(norm, DEFAULT_WALL_MAX_HP)

func set_wall_hp(wall_id: String, hp: int) -> void:
	var norm: String = wall_id.to_upper()
	if not _wall_hp.has(norm):
		return
	var max_hp: int = get_wall_max_hp(norm)
	var clamped: int = clampi(hp, 0, max_hp)
	var was_breached: bool = is_wall_breached(norm)
	_wall_hp[norm] = clamped

	if not was_breached and clamped == 0:
		wall_breached.emit(norm)

func damage_wall(wall_id: String, amount: int) -> int:
	var norm: String = wall_id.to_upper()
	if not _wall_hp.has(norm):
		return 0
	if amount <= 0:
		return _wall_hp[norm]

	var current_hp: int = _wall_hp[norm]
	var was_breached: bool = current_hp <= 0
	var new_hp: int = maxi(0, current_hp - amount)
	_wall_hp[norm] = new_hp

	wall_damaged.emit(norm, amount, new_hp)

	if not was_breached and new_hp == 0:
		wall_breached.emit(norm)

	return new_hp

func repair_wall(wall_id: String, amount: int) -> int:
	var norm: String = wall_id.to_upper()
	if not _wall_hp.has(norm):
		return 0
	if amount <= 0:
		return _wall_hp[norm]

	var current_hp: int = _wall_hp[norm]
	var max_hp: int = get_wall_max_hp(norm)
	var new_hp: int = mini(max_hp, current_hp + amount)
	_wall_hp[norm] = new_hp

	wall_repaired.emit(norm, amount, new_hp)
	return new_hp

func is_wall_breached(wall_id: String) -> bool:
	var norm: String = wall_id.to_upper()
	if not _wall_hp.has(norm):
		return false
	return _wall_hp[norm] <= 0

# ── Unit Tracking System ─────────────────────────────────────────────────────
func place_unit(unit_id: String, pos: Vector2i) -> bool:
	if unit_id.is_empty() or not is_valid_cell(pos):
		return false

	# If already on board, remove from previous cell/zone first
	if _unit_positions.has(unit_id):
		remove_unit(unit_id)

	var zone_id: String = get_zone_at(pos)
	_unit_positions[unit_id] = pos

	if not _cell_units.has(pos):
		var arr: Array[String] = []
		_cell_units[pos] = arr
	(_cell_units[pos] as Array[String]).append(unit_id)

	if not _zone_units.has(zone_id):
		var zarr: Array[String] = []
		_zone_units[zone_id] = zarr
	(_zone_units[zone_id] as Array[String]).append(unit_id)

	unit_placed.emit(unit_id, pos, zone_id)
	return true

func move_unit(unit_id: String, to_pos: Vector2i) -> bool:
	if not _unit_positions.has(unit_id) or not is_valid_cell(to_pos):
		return false

	var from_pos: Vector2i = _unit_positions[unit_id]
	if from_pos == to_pos:
		return true

	var from_zone: String = get_zone_at(from_pos)
	var to_zone: String = get_zone_at(to_pos)

	# Remove from old cell
	if _cell_units.has(from_pos):
		(_cell_units[from_pos] as Array[String]).erase(unit_id)
		if (_cell_units[from_pos] as Array[String]).is_empty():
			_cell_units.erase(from_pos)

	# Remove from old zone
	if _zone_units.has(from_zone):
		(_zone_units[from_zone] as Array[String]).erase(unit_id)

	# Add to new cell & zone
	_unit_positions[unit_id] = to_pos

	if not _cell_units.has(to_pos):
		var arr: Array[String] = []
		_cell_units[to_pos] = arr
	(_cell_units[to_pos] as Array[String]).append(unit_id)

	if not _zone_units.has(to_zone):
		var zarr: Array[String] = []
		_zone_units[to_zone] = zarr
	(_zone_units[to_zone] as Array[String]).append(unit_id)

	unit_moved.emit(unit_id, from_pos, to_pos, from_zone, to_zone)
	return true

func remove_unit(unit_id: String) -> bool:
	if not _unit_positions.has(unit_id):
		return false

	var last_pos: Vector2i = _unit_positions[unit_id]
	var last_zone: String = get_zone_at(last_pos)

	_unit_positions.erase(unit_id)

	if _cell_units.has(last_pos):
		(_cell_units[last_pos] as Array[String]).erase(unit_id)
		if (_cell_units[last_pos] as Array[String]).is_empty():
			_cell_units.erase(last_pos)

	if _zone_units.has(last_zone):
		(_zone_units[last_zone] as Array[String]).erase(unit_id)

	unit_removed.emit(unit_id, last_pos, last_zone)
	return true

func get_units_in_zone(zone_id: String) -> Array[String]:
	var norm: String = zone_id.to_upper()
	if _zone_units.has(norm):
		var orig: Array[String] = _zone_units[norm]
		var copy_arr: Array[String] = []
		copy_arr.assign(orig)
		return copy_arr
	return []

func get_units_at_cell(pos: Vector2i) -> Array[String]:
	if _cell_units.has(pos):
		var orig: Array[String] = _cell_units[pos]
		var copy_arr: Array[String] = []
		copy_arr.assign(orig)
		return copy_arr
	return []

func get_unit_at(pos: Vector2i) -> String:
	if _cell_units.has(pos):
		var arr: Array[String] = _cell_units[pos]
		if not arr.is_empty():
			return arr[0]
	return ""

func get_unit_position(unit_id: String) -> Vector2i:
	return _unit_positions.get(unit_id, Vector2i(-1, -1))

func get_unit_zone(unit_id: String) -> String:
	var pos: Vector2i = get_unit_position(unit_id)
	if pos == Vector2i(-1, -1):
		return ""
	return get_zone_at(pos)

func has_unit(unit_id: String) -> bool:
	return _unit_positions.has(unit_id)

func get_all_units() -> Array[String]:
	var keys: Array = _unit_positions.keys()
	var arr: Array[String] = []
	for k in keys:
		arr.append(str(k))
	return arr

func clear_all_units() -> void:
	var all_u: Array[String] = get_all_units()
	for u in all_u:
		remove_unit(u)
	_unit_data.clear()

func clear_all() -> void:
	clear_all_units()
	_initialize_items()

# ── Item Management System ───────────────────────────────────────────────────
func place_item(pos: Vector2i, item_type: String, data: Dictionary = {}) -> bool:
	if not is_valid_cell(pos) or item_type.is_empty():
		return false
	var item_dict: Dictionary = data.duplicate(true)
	item_dict["type"] = item_type
	item_dict["pos"] = pos
	if not item_dict.has("name"):
		match item_type:
			ITEM_CRISTAL: item_dict["name"] = "Cristal de Mana"
			ITEM_CHEST: item_dict["name"] = "Baú de Suprimentos"
			ITEM_POTION: item_dict["name"] = "Poção de Vida"
			ITEM_METAL: item_dict["name"] = "Lingotes de Metal"
			ITEM_WOOD: item_dict["name"] = "Pilha de Madeira"
			ITEM_LEATHER: item_dict["name"] = "Fardo de Couro"
			ITEM_GOLD: item_dict["name"] = "Pilha de Ouro"
			_: item_dict["name"] = "Item"
	if not item_dict.has("amount"):
		item_dict["amount"] = 1
	var base_n: String = str(item_dict.get("base_name", item_dict.get("name", "Item")))
	item_dict["base_name"] = base_n

	# Se a célula já possui um item no chão, acumula os recursos (Stacking System)
	if _items.has(pos):
		var existing: Dictionary = _items[pos]
		var total_amt: int = int(existing.get("amount", 1)) + int(item_dict.get("amount", 1))
		existing["amount"] = total_amt
		
		# Somar recursos acumulados na mesma célula
		if item_dict.has("wood") or existing.has("wood"):
			existing["wood"] = int(existing.get("wood", 0)) + int(item_dict.get("wood", 0))
		if item_dict.has("leather") or existing.has("leather"):
			existing["leather"] = int(existing.get("leather", 0)) + int(item_dict.get("leather", 0))
		if item_dict.has("metal") or existing.has("metal"):
			existing["metal"] = int(existing.get("metal", 0)) + int(item_dict.get("metal", 0))
		if item_dict.has("crystal") or existing.has("crystal"):
			existing["crystal"] = int(existing.get("crystal", 0)) + int(item_dict.get("crystal", 0))
		if item_dict.has("gold") or existing.has("gold"):
			existing["gold"] = int(existing.get("gold", 0)) + int(item_dict.get("gold", 0))
		if item_dict.has("heal") or existing.has("heal"):
			existing["heal"] = int(existing.get("heal", 0)) + int(item_dict.get("heal", 0))
		
		var existing_base: String = str(existing.get("base_name", existing.get("name", "Item")))
		existing["base_name"] = existing_base
		existing["name"] = "%s (x%d)" % [existing_base, total_amt]
		_items[pos] = existing
		item_placed.emit(pos, existing)
		return true

	_items[pos] = item_dict
	item_placed.emit(pos, item_dict)
	return true

func get_item_at(pos: Vector2i) -> Dictionary:
	if not _items.has(pos):
		return {}
	return (_items[pos] as Dictionary).duplicate(true)

func has_item_at(pos: Vector2i) -> bool:
	return _items.has(pos)

func remove_item(pos: Vector2i) -> bool:
	if not _items.has(pos):
		return false
	_items.erase(pos)
	item_removed.emit(pos)
	return true

func collect_item(unit_id: String, pos: Vector2i) -> Dictionary:
	if not _items.has(pos):
		return {}
	var item_dict: Dictionary = (_items[pos] as Dictionary).duplicate(true)
	_items.erase(pos)
	item_collected.emit(unit_id, pos, item_dict)
	return item_dict

func get_all_items() -> Dictionary:
	return _items.duplicate(true)

func clear_all_items() -> void:
	_items.clear()

func spawn_default_map_items() -> void:
	clear_all_items()
	# 💎 Cristais Roxos de Mana na Câmara Central (longe dos heróis em (9,10), (10,9) e (10,11))
	place_item(Vector2i(9, 8), ITEM_CRISTAL, {"name": "Cristal de Mana", "amount": 1, "icon": "💎"})
	place_item(Vector2i(11, 8), ITEM_CRISTAL, {"name": "Grande Cristal", "amount": 2, "icon": "💎"})
	place_item(Vector2i(8, 11), ITEM_CRISTAL, {"name": "Cristal Roxo", "amount": 2, "icon": "💎"})
	place_item(Vector2i(11, 11), ITEM_CRISTAL, {"name": "Cristal de Mana", "amount": 1, "icon": "💎"})

	# 🪵 Carpintaria (Norte interior): Madeira e Baú bem espaçados
	place_item(Vector2i(7, 5), ITEM_WOOD, {"name": "Estoque de Madeira", "wood": 10, "amount": 10, "icon": "🪵"})
	place_item(Vector2i(10, 5), ITEM_CHEST, {"name": "Baú da Carpintaria", "wood": 6, "leather": 2, "metal": 2, "icon": "📦"})

	# 👞 Curtume (Sul interior): Couro e Baú bem espaçados
	place_item(Vector2i(8, 14), ITEM_LEATHER, {"name": "Estoque de Couro", "leather": 10, "amount": 10, "icon": "👞"})
	place_item(Vector2i(11, 14), ITEM_CHEST, {"name": "Baú do Curtume", "wood": 2, "leather": 6, "metal": 2, "icon": "📦"})

	# 🪙 Fundição (Oeste) e Pátio (Leste): Ouro e Baú em células amplas
	place_item(Vector2i(5, 8), ITEM_GOLD, {"name": "Reserva de Ouro", "gold": 10, "amount": 10, "crystal": 10, "icon": "🪙"})
	place_item(Vector2i(5, 11), ITEM_CHEST, {"name": "Baú da Fundição", "wood": 2, "leather": 2, "metal": 6, "icon": "📦"})
	place_item(Vector2i(14, 9), ITEM_GOLD, {"name": "Tesouro do Pátio", "gold": 10, "amount": 10, "crystal": 10, "icon": "🪙"})

	# 🧪 Poções de Cura nas Torres de Vigia dos Cantos
	place_item(Vector2i(2, 2), ITEM_POTION, {"name": "Elixir da Torre NW", "heal": 15, "icon": "🧪"})
	place_item(Vector2i(17, 2), ITEM_POTION, {"name": "Elixir da Torre NE", "heal": 15, "icon": "🧪"})
	place_item(Vector2i(2, 17), ITEM_POTION, {"name": "Elixir da Torre SW", "heal": 15, "icon": "🧪"})
	place_item(Vector2i(17, 17), ITEM_POTION, {"name": "Elixir da Torre SE", "heal": 15, "icon": "🧪"})

	# ⚙️ / 🪵 Materiais nos Corredores e Pátio
	place_item(Vector2i(14, 11), ITEM_WOOD, {"name": "Pilha de Vigas", "wood": 5, "icon": "🪵"})
	place_item(Vector2i(6, 6), ITEM_METAL, {"name": "Lingotes de Ferro", "metal": 5, "icon": "⚙️"})
	place_item(Vector2i(13, 13), ITEM_METAL, {"name": "Lingotes de Aço", "metal": 5, "icon": "⚙️"})

# ── Unit Stats & Combat Registry ─────────────────────────────────────────────
func register_unit(unit_id: String, data: Dictionary) -> void:
	if unit_id.is_empty():
		return
	var u_dict: Dictionary = data.duplicate(true)
	if not u_dict.has("id"):
		u_dict["id"] = unit_id
	if not u_dict.has("name"):
		u_dict["name"] = unit_id
	if not u_dict.has("team"):
		u_dict["team"] = "A"
	if not u_dict.has("hp"):
		u_dict["hp"] = 10
	if not u_dict.has("max_hp"):
		u_dict["max_hp"] = u_dict["hp"]
	if not u_dict.has("ac"):
		u_dict["ac"] = 10
	if not u_dict.has("move_range"):
		u_dict["move_range"] = 3
	if not u_dict.has("remaining_pm"):
		u_dict["remaining_pm"] = int(u_dict["move_range"])
	if not u_dict.has("attack_range"):
		u_dict["attack_range"] = 1
	if not u_dict.has("attack_bonus"):
		u_dict["attack_bonus"] = 3
	u_dict["is_alive"] = int(u_dict["hp"]) > 0
	_unit_data[unit_id] = u_dict
	unit_stats_changed.emit(unit_id, u_dict)

func get_unit_remaining_pm(unit_id: String) -> int:
	if not _unit_data.has(unit_id):
		return 0
	return int(_unit_data[unit_id].get("remaining_pm", _unit_data[unit_id].get("move_range", 3)))

func consume_unit_pm(unit_id: String, amount: int) -> int:
	if not _unit_data.has(unit_id):
		return 0
	var cur_pm: int = get_unit_remaining_pm(unit_id)
	var new_pm: int = maxi(0, cur_pm - amount)
	_unit_data[unit_id]["remaining_pm"] = new_pm
	unit_stats_changed.emit(unit_id, _unit_data[unit_id].duplicate(true))
	return new_pm

func restore_units_pm(team: String = "A") -> void:
	for u_id in get_units_by_team(team):
		if is_unit_alive(u_id):
			var max_pm: int = int(_unit_data[u_id].get("move_range", 3))
			_unit_data[u_id]["remaining_pm"] = max_pm
			unit_stats_changed.emit(u_id, _unit_data[u_id].duplicate(true))

func get_unit_data(unit_id: String) -> Dictionary:
	return _unit_data.get(unit_id, {}).duplicate(true)

func set_unit_data(unit_id: String, data: Dictionary) -> void:
	if not _unit_data.has(unit_id):
		register_unit(unit_id, data)
	else:
		for k in data.keys():
			_unit_data[unit_id][k] = data[k]
		_unit_data[unit_id]["is_alive"] = int(_unit_data[unit_id].get("hp", 0)) > 0
		unit_stats_changed.emit(unit_id, _unit_data[unit_id].duplicate(true))

func damage_unit(unit_id: String, amount: int) -> int:
	if not _unit_data.has(unit_id):
		return 0
	var cur_hp: int = int(_unit_data[unit_id].get("hp", 0))
	var new_hp: int = maxi(0, cur_hp - amount)
	_unit_data[unit_id]["hp"] = new_hp
	if new_hp <= 0:
		_unit_data[unit_id]["is_alive"] = false
	unit_stats_changed.emit(unit_id, _unit_data[unit_id].duplicate(true))
	return new_hp

func heal_unit(unit_id: String, amount: int) -> int:
	if not _unit_data.has(unit_id):
		return 0
	var cur_hp: int = int(_unit_data[unit_id].get("hp", 0))
	var max_hp: int = int(_unit_data[unit_id].get("max_hp", cur_hp))
	var new_hp: int = mini(max_hp, cur_hp + amount)
	_unit_data[unit_id]["hp"] = new_hp
	if new_hp > 0:
		_unit_data[unit_id]["is_alive"] = true
	unit_stats_changed.emit(unit_id, _unit_data[unit_id].duplicate(true))
	return new_hp

func is_unit_alive(unit_id: String) -> bool:
	if not _unit_data.has(unit_id):
		return has_unit(unit_id)
	return int(_unit_data[unit_id].get("hp", 1)) > 0 and bool(_unit_data[unit_id].get("is_alive", true))

func get_units_by_team(team: String) -> Array[String]:
	var result: Array[String] = []
	for u_id in get_all_units():
		var u_team: String = _unit_data.get(u_id, {}).get("team", "A")
		if u_team == team:
			result.append(u_id)
	return result

# ── Tactical FFT Range Calculations ──────────────────────────────────────────
func is_cell_walkable(cell: Vector2i) -> bool:
	if not is_valid_cell(cell):
		return false
	var z_id: String = get_zone_at(cell)
	# Torres de vigia perimetrais são elevadas e intransponíveis a pé
	if z_id in ALL_TOWERS:
		return false
	# Muralhas intactas bloqueiam passagem até serem derrubadas (breached)
	if z_id in ALL_WALLS:
		if not is_wall_breached(z_id):
			return false
	return true

func get_reachable_cells(pos: Vector2i, move_range: int) -> Array[Vector2i]:
	var reachable: Array[Vector2i] = []
	if not is_valid_cell(pos) or move_range <= 0:
		return reachable

	var queue: Array[Dictionary] = [{"pos": pos, "dist": 0}]
	var visited: Dictionary = {pos: 0}

	var dirs: Array[Vector2i] = [
		Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0),
		Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)
	]

	while not queue.is_empty():
		var current: Dictionary = queue.pop_front()
		var curr_pos: Vector2i = current["pos"]
		var curr_dist: int = current["dist"]

		if curr_dist >= move_range:
			continue

		for d in dirs:
			var nxt: Vector2i = curr_pos + d
			if not is_valid_cell(nxt):
				continue

			# Muralhas intactas não podem ser atravessadas
			if not is_cell_walkable(nxt):
				continue

			var nxt_dist: int = curr_dist + 1
			if not visited.has(nxt) or visited[nxt] > nxt_dist:
				visited[nxt] = nxt_dist
				# Cell is reachable if empty or has items (units don't block friendly path in simple tactical mode)
				if not _cell_units.has(nxt) or (_cell_units[nxt] as Array[String]).is_empty():
					if not reachable.has(nxt):
						reachable.append(nxt)
				queue.append({"pos": nxt, "dist": nxt_dist})

	return reachable

func get_attackable_cells(pos: Vector2i, attack_range: int, attacker_team: String = "A") -> Array[Vector2i]:
	var targets: Array[Vector2i] = []
	if not is_valid_cell(pos) or attack_range <= 0:
		return targets

	for u_id in get_all_units():
		var u_pos: Vector2i = get_unit_position(u_id)
		if u_pos == Vector2i(-1, -1) or u_pos == pos:
			continue
		var u_data: Dictionary = get_unit_data(u_id)
		var u_team: String = u_data.get("team", "B" if attacker_team == "A" else "A")
		if u_team != attacker_team and is_unit_alive(u_id):
			var dist: int = maxi(absi(pos.x - u_pos.x), absi(pos.y - u_pos.y))
			if dist <= attack_range:
				if not targets.has(u_pos):
					targets.append(u_pos)

	return targets

## Encontra o caminho mais curto entre from_pos e to_pos usando BFS tático com suporte a evasão de obstáculos e muralhas
func find_path(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false, max_steps: int = -1) -> Array[Vector2i]:
	var path: Array[Vector2i] = []
	if from_pos == to_pos or not is_valid_cell(from_pos) or not is_valid_cell(to_pos):
		return path

	var dirs: Array[Vector2i] = [
		Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0),
		Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)
	]

	var queue: Array[Dictionary] = [{"pos": from_pos, "path": []}]
	var visited: Dictionary = {from_pos: true}

	while not queue.is_empty():
		var curr: Dictionary = queue.pop_front()
		var curr_pos: Vector2i = curr["pos"]
		var curr_path: Array = curr["path"]

		if curr_pos == to_pos:
			path.assign(curr_path)
			return path

		if max_steps > 0 and curr_path.size() >= max_steps:
			continue

		for d in dirs:
			var nxt: Vector2i = curr_pos + d
			if not is_valid_cell(nxt) or visited.has(nxt):
				continue

			# Checa se célula está bloqueada por outra unidade
			if not ignore_units and nxt != to_pos:
				if _cell_units.has(nxt) and not (_cell_units[nxt] as Array[String]).is_empty():
					continue

			visited[nxt] = true
			var nxt_path: Array = curr_path.duplicate()
			nxt_path.append(nxt)
			queue.append({"pos": nxt, "path": nxt_path})

	return path

func reset_board() -> void:
	clear_all_units()
	clear_all_items()
	_initialize_walls()


