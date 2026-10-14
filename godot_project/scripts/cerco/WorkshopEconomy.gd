# res://scripts/cerco/WorkshopEconomy.gd
class_name WorkshopEconomy
extends RefCounted

## WorkshopEconomy: Manages fortress resource tracking, workshop production,
## costs deduction, and wall reinforcement for Cerco da Fortaleza contra Isectum.

# ── Signals ──────────────────────────────────────────────────────────────────
signal resources_updated(wood: int, leather: int, metal: int, crystal: int, ap: int)
signal resource_added(type: String, amount: int, new_total: int)
signal resource_spent(type: String, amount: int, remaining: int)
signal production_completed(workshop_zone: String, produced: Dictionary)
signal wall_repaired_with_resources(wall_id: String, wood_spent: int, metal_spent: int, new_hp: int)

# ── Production Constants ─────────────────────────────────────────────────────
const CARPINTARIA_WOOD_PER_WORKER: int = 2
const CURTUME_LEATHER_PER_WORKER: int = 2
const FUNDICAO_METAL_PER_WORKER: int = 1
const FUNDICAO_CRYSTAL_PER_WORKER: int = 1
const PATIO_CRYSTAL_PER_WORKER: int = 1

# Wall repair efficiency
const HP_PER_WOOD: int = 10
const HP_PER_METAL: int = 15

# ── Tracked Fortress Resources ───────────────────────────────────────────────
var wood: int = 0
var leather: int = 0
var metal: int = 0
var crystal: int = 0
var ap: int = 0

# ── Portuguese Nomenclature Properties ───────────────────────────────────────
var madeira: int:
	get:
		return wood
	set(v):
		wood = maxi(0, v)

var couro: int:
	get:
		return leather
	set(v):
		leather = maxi(0, v)

var ferro: int:
	get:
		return metal
	set(v):
		metal = maxi(0, v)

var cristal: int:
	get:
		return crystal
	set(v):
		crystal = maxi(0, v)

var cristais: int:
	get:
		return crystal
	set(v):
		crystal = maxi(0, v)

# ── Lifecycle / Initialization ───────────────────────────────────────────────
func _init(init_wood: int = 0, init_leather: int = 0, init_metal: int = 0, init_crystal: int = 0, init_ap: int = 0) -> void:
	wood = maxi(0, init_wood)
	leather = maxi(0, init_leather)
	metal = maxi(0, init_metal)
	crystal = maxi(0, init_crystal)
	ap = maxi(0, init_ap)

func reset() -> void:
	wood = 0
	leather = 0
	metal = 0
	crystal = 0
	ap = 0
	_emit_resources_updated()

func set_resources(new_wood: int, new_leather: int, new_metal: int, new_crystal: int, new_ap: int) -> void:
	wood = maxi(0, new_wood)
	leather = maxi(0, new_leather)
	metal = maxi(0, new_metal)
	crystal = maxi(0, new_crystal)
	ap = maxi(0, new_ap)
	_emit_resources_updated()

# ── Resource Management ──────────────────────────────────────────────────────

## Normalizes resource type names across English and Portuguese variants.
func normalize_resource_type(type: String) -> String:
	match type.strip_edges().to_lower():
		"wood", "madeira", "w":
			return "wood"
		"leather", "couro", "l":
			return "leather"
		"metal", "ferro", "m":
			return "metal"
		"crystal", "cristal", "cristais", "c":
			return "crystal"
		"ap", "pa", "action_points", "pontos_acao":
			return "ap"
		_:
			return type.strip_edges().to_lower()

## Gets the current value of a resource by normalized name.
func get_resource(type: String) -> int:
	match normalize_resource_type(type):
		"wood":
			return wood
		"leather":
			return leather
		"metal":
			return metal
		"crystal":
			return crystal
		"ap":
			return ap
		_:
			return 0

## Sets the value of a single resource.
func set_resource(type: String, amount: int) -> void:
	var norm: String = normalize_resource_type(type)
	var val: int = maxi(0, amount)
	match norm:
		"wood":
			wood = val
		"leather":
			leather = val
		"metal":
			metal = val
		"crystal":
			crystal = val
		"ap":
			ap = val
	_emit_resources_updated()

## Adds an amount of resource to the fortress storage.
func add_resource(type: String, amount: int) -> int:
	if amount <= 0:
		return get_resource(type)

	var norm: String = normalize_resource_type(type)
	var new_total: int = 0
	match norm:
		"wood":
			wood += amount
			new_total = wood
		"leather":
			leather += amount
			new_total = leather
		"metal":
			metal += amount
			new_total = metal
		"crystal":
			crystal += amount
			new_total = crystal
		"ap":
			ap += amount
			new_total = ap

	resource_added.emit(norm, amount, new_total)
	_emit_resources_updated()
	return new_total

## Spends an amount of resource if sufficient balance is available.
func spend_resource(type: String, amount: int) -> bool:
	if amount <= 0:
		return true

	var norm: String = normalize_resource_type(type)
	var current: int = get_resource(norm)
	if current < amount:
		return false

	var remaining: int = 0
	match norm:
		"wood":
			wood -= amount
			remaining = wood
		"leather":
			leather -= amount
			remaining = leather
		"metal":
			metal -= amount
			remaining = metal
		"crystal":
			crystal -= amount
			remaining = crystal
		"ap":
			ap -= amount
			remaining = ap

	resource_spent.emit(norm, amount, remaining)
	_emit_resources_updated()
	return true

## Checks if the economy has enough resources to satisfy the provided cost dictionary.
func can_afford(cost_dict: Dictionary) -> bool:
	if cost_dict.is_empty():
		return true

	# Aggregate normalized costs
	var aggregated: Dictionary = {}
	for k in cost_dict:
		var norm_k: String = normalize_resource_type(String(k))
		var amt: int = int(cost_dict[k])
		if amt > 0:
			aggregated[norm_k] = aggregated.get(norm_k, 0) + amt

	for norm_res in aggregated:
		if get_resource(norm_res) < aggregated[norm_res]:
			return false

	return true

## Atomically spends the costs defined in cost_dict if affordable.
func spend_costs(cost_dict: Dictionary) -> bool:
	if not can_afford(cost_dict):
		return false

	var aggregated: Dictionary = {}
	for k in cost_dict:
		var norm_k: String = normalize_resource_type(String(k))
		var amt: int = int(cost_dict[k])
		if amt > 0:
			aggregated[norm_k] = aggregated.get(norm_k, 0) + amt

	for norm_res in aggregated:
		var amt: int = aggregated[norm_res]
		match norm_res:
			"wood":
				wood -= amt
			"leather":
				leather -= amt
			"metal":
				metal -= amt
			"crystal":
				crystal -= amt
			"ap":
				ap -= amt
		resource_spent.emit(norm_res, amt, get_resource(norm_res))

	_emit_resources_updated()
	return true

# ── Workshop Production ──────────────────────────────────────────────────────

## Alias for produce_at_workshop to ensure polymorphic caller compatibility
func produce(workshop_zone: String, worker_count: int = 1) -> Dictionary:
	return produce_at_workshop(workshop_zone, worker_count)

## Executes production at a workshop zone based on worker count.
## Carpintaria produces wood; Curtume produces leather; Fundição produces metal & crystal;
## Pátio Central produces crystals.
func produce_at_workshop(workshop_zone: String, worker_count: int) -> Dictionary:
	if worker_count <= 0:
		return {}

	var norm_zone: String = workshop_zone.strip_edges().to_upper()
	var produced: Dictionary = {}

	match norm_zone:
		"CARPINTARIA":
			var wood_gain: int = worker_count * CARPINTARIA_WOOD_PER_WORKER
			produced["wood"] = wood_gain
			wood += wood_gain
			resource_added.emit("wood", wood_gain, wood)
		"CURTUME":
			var leather_gain: int = worker_count * CURTUME_LEATHER_PER_WORKER
			produced["leather"] = leather_gain
			leather += leather_gain
			resource_added.emit("leather", leather_gain, leather)
		"FUNDICAO":
			var metal_gain: int = worker_count * FUNDICAO_METAL_PER_WORKER
			var crystal_gain: int = worker_count * FUNDICAO_CRYSTAL_PER_WORKER
			produced["metal"] = metal_gain
			produced["crystal"] = crystal_gain
			metal += metal_gain
			crystal += crystal_gain
			resource_added.emit("metal", metal_gain, metal)
			resource_added.emit("crystal", crystal_gain, crystal)
		"PATIO_CENTRAL", "PATIO":
			var crystal_gain: int = worker_count * PATIO_CRYSTAL_PER_WORKER
			produced["crystal"] = crystal_gain
			crystal += crystal_gain
			resource_added.emit("crystal", crystal_gain, crystal)
		_:
			# Unknown workshop: no production
			return {}

	_emit_resources_updated()
	production_completed.emit(norm_zone, produced)
	return produced

# ── Wall Repairs ─────────────────────────────────────────────────────────────

## Alias for repair_wall_with_resources
func repair_wall(wall_id: String, board: FortressBoard, wood_spent: int, metal_spent: int = 0) -> int:
	return repair_wall_with_resources(wall_id, board, wood_spent, metal_spent)

## Repairs a fortress wall on the board by spending wood and metal.
## Returns the new wall HP after repair, or 0 on failure.
func repair_wall_with_resources(
	wall_id: String,
	board: FortressBoard,
	wood_spent: int,
	metal_spent: int
) -> int:
	if board == null:
		return 0
	if wood_spent < 0 or metal_spent < 0:
		return 0

	# Check affordability
	if wood < wood_spent or metal < metal_spent:
		return 0

	# If zero resources spent, return current HP without changes
	if wood_spent == 0 and metal_spent == 0:
		return board.get_wall_hp(wall_id)

	# Deduct resources
	if wood_spent > 0:
		wood -= wood_spent
		resource_spent.emit("wood", wood_spent, wood)
	if metal_spent > 0:
		metal -= metal_spent
		resource_spent.emit("metal", metal_spent, metal)

	_emit_resources_updated()

	var repair_amount: int = (wood_spent * HP_PER_WOOD) + (metal_spent * HP_PER_METAL)
	var new_hp: int = board.repair_wall(wall_id, repair_amount)

	wall_repaired_with_resources.emit(wall_id, wood_spent, metal_spent, new_hp)
	return new_hp

# ── Helper Export ────────────────────────────────────────────────────────────

func to_dict() -> Dictionary:
	return {
		"wood": wood,
		"leather": leather,
		"metal": metal,
		"crystal": crystal,
		"ap": ap
	}

func _emit_resources_updated() -> void:
	resources_updated.emit(wood, leather, metal, crystal, ap)

	# Safely notify global EventBus if available
	var main_loop = Engine.get_main_loop()
	if main_loop is SceneTree and main_loop.root != null:
		var eb = main_loop.root.get_node_or_null("EventBus")
		if eb != null and eb.has_signal("resources_updated"):
			eb.resources_updated.emit(wood, metal, crystal, ap)
