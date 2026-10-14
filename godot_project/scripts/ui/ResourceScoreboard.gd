# res://scripts/ui/ResourceScoreboard.gd
class_name ResourceScoreboard
extends Control

## Displays fortress resources (Madeira, Couro, Metal, Cristais, AP),
## current round number, synchrony layer, and wall integrity metrics.
## Reacts to WorkshopEconomy and EventBus signals.

signal resource_display_updated(resource_type: String, value: int)

# ── Current Values ───────────────────────────────────────────────────────────
var wood: int = 0
var leather: int = 0
var metal: int = 0
var crystal: int = 0
var ap: int = 0
var current_round: int = 1
var current_layer: String = "Marcha"
var wall_hps: Dictionary = {
	"MURALHA_NORTE": 100,
	"MURALHA_SUL": 100,
	"MURALHA_LESTE": 100,
	"MURALHA_OESTE": 100
}

# ── References ───────────────────────────────────────────────────────────────
var _bound_economy: Object = null

# Child UI Nodes
var _round_label: Label = null
var _layer_label: Label = null
var _wood_label: Label = null
var _leather_label: Label = null
var _metal_label: Label = null
var _crystal_label: Label = null
var _ap_label: Label = null
var _wall_labels: Dictionary = {}

func _init() -> void:
	custom_minimum_size = Vector2(800.0, 48.0)
	size = custom_minimum_size
	mouse_filter = MOUSE_FILTER_PASS

func _ready() -> void:
	_setup_ui()
	_connect_event_bus()
	refresh_display()

func _setup_ui() -> void:
	if _round_label != null:
		return
	
	var panel: PanelContainer = PanelContainer.new()
	panel.name = "Panel"
	panel.set_anchors_preset(PRESET_FULL_RECT)
	panel.mouse_filter = MOUSE_FILTER_PASS
	add_child(panel)
	
	var hbox: HBoxContainer = HBoxContainer.new()
	hbox.name = "HBox"
	hbox.mouse_filter = MOUSE_FILTER_PASS
	hbox.set_anchors_preset(PRESET_FULL_RECT)
	hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	hbox.add_theme_constant_override("separation", 14)
	panel.add_child(hbox)
	
	# Round & Layer
	_round_label = Label.new()
	_round_label.name = "RoundLabel"
	_round_label.text = "Rodada: 1"
	hbox.add_child(_round_label)
	
	_layer_label = Label.new()
	_layer_label.name = "LayerLabel"
	_layer_label.text = "Fase: Marcha"
	hbox.add_child(_layer_label)
	
	# Separator
	var sep1: VSeparator = VSeparator.new()
	hbox.add_child(sep1)
	
	# Resource Counters
	_wood_label = Label.new()
	_wood_label.name = "WoodLabel"
	_wood_label.text = "Madeira: 0"
	_wood_label.add_theme_color_override("font_color", Color(0.4, 0.8, 0.35))
	hbox.add_child(_wood_label)
	
	_leather_label = Label.new()
	_leather_label.name = "LeatherLabel"
	_leather_label.text = "Couro: 0"
	_leather_label.add_theme_color_override("font_color", Color(0.85, 0.6, 0.25))
	hbox.add_child(_leather_label)
	
	_metal_label = Label.new()
	_metal_label.name = "MetalLabel"
	_metal_label.text = "Metal: 0"
	_metal_label.add_theme_color_override("font_color", Color(0.65, 0.75, 0.95))
	hbox.add_child(_metal_label)
	
	_crystal_label = Label.new()
	_crystal_label.name = "CrystalLabel"
	_crystal_label.text = "Cristal: 0"
	_crystal_label.add_theme_color_override("font_color", Color(0.85, 0.55, 1.0))
	hbox.add_child(_crystal_label)
	
	_ap_label = Label.new()
	_ap_label.name = "APLabel"
	_ap_label.text = "AP: 0"
	_ap_label.add_theme_color_override("font_color", Color(1.0, 0.85, 0.2))
	hbox.add_child(_ap_label)
	
	# Separator
	var sep2: VSeparator = VSeparator.new()
	hbox.add_child(sep2)
	
	# Wall Mini Integrities
	for wkey in ["MURALHA_NORTE", "MURALHA_SUL", "MURALHA_LESTE", "MURALHA_OESTE"]:
		var wlbl: Label = Label.new()
		wlbl.name = wkey + "Label"
		var short_name: String = wkey.replace("MURALHA_", "")[0]
		wlbl.text = "M.%s: 100" % short_name
		hbox.add_child(wlbl)
		_wall_labels[wkey] = wlbl

func _connect_event_bus() -> void:
	if not Engine.is_editor_hint():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("resources_updated") and not eb.resources_updated.is_connected(_on_eventbus_resources_updated):
				eb.resources_updated.connect(_on_eventbus_resources_updated)

## Directly updates all 5 resource counters
func update_resources(p_wood: int, p_leather: int, p_metal: int, p_crystal: int, p_ap: int) -> void:
	wood = p_wood
	leather = p_leather
	metal = p_metal
	crystal = p_crystal
	ap = p_ap
	refresh_display()
	resource_display_updated.emit("wood", wood)
	resource_display_updated.emit("leather", leather)
	resource_display_updated.emit("metal", metal)
	resource_display_updated.emit("crystal", crystal)
	resource_display_updated.emit("ap", ap)

## Sets the current round number
func set_round(round_num: int) -> void:
	current_round = round_num
	if _round_label != null:
		_round_label.text = "Rodada: %d" % current_round

## Sets the active layer/phase name
func set_layer(layer_name: String) -> void:
	current_layer = layer_name
	if _layer_label != null:
		_layer_label.text = "Fase: %s" % current_layer

## Updates wall HP display
func update_wall_hp(wall_id: String, hp: int, _max_hp: int = 100) -> void:
	var norm_id: String = wall_id.to_upper()
	wall_hps[norm_id] = hp
	
	# Also find matching short key
	for k in _wall_labels:
		if norm_id.ends_with(k) or norm_id == k:
			var lbl: Label = _wall_labels[k]
			var short_name: String = k.replace("MURALHA_", "")[0]
			lbl.text = "M.%s: %d" % [short_name, hp]
			if hp <= 0:
				lbl.add_theme_color_override("font_color", Color(0.9, 0.2, 0.2))
			elif hp <= 30:
				lbl.add_theme_color_override("font_color", Color(0.9, 0.6, 0.2))
			else:
				lbl.add_theme_color_override("font_color", Color(0.8, 0.8, 0.8))

## Returns tracked value for given resource
func get_resource_value(res_name: String) -> int:
	match res_name.to_lower():
		"wood", "madeira": return wood
		"leather", "couro": return leather
		"metal", "ferro": return metal
		"crystal", "cristais", "cristal": return crystal
		"ap", "pontos_acao": return ap
		_: return 0

func get_round() -> int:
	return current_round

func get_layer() -> String:
	return current_layer

func get_wall_hp(wall_id: String) -> int:
	var norm: String = wall_id.to_upper()
	for k in wall_hps:
		if norm.ends_with(k) or norm == k:
			return wall_hps[k]
	return 100

## Binds to WorkshopEconomy instance
func bind_economy(economy: Object) -> void:
	unbind_economy()
	_bound_economy = economy
	if _bound_economy != null and _bound_economy.has_signal("resources_updated"):
		if not _bound_economy.resources_updated.is_connected(_on_economy_resources_updated):
			_bound_economy.resources_updated.connect(_on_economy_resources_updated)
		# Initialize immediately if methods exist
		if _bound_economy.has_method("get_resource"):
			update_resources(
				_bound_economy.get_resource("wood"),
				_bound_economy.get_resource("leather"),
				_bound_economy.get_resource("metal"),
				_bound_economy.get_resource("crystal"),
				_bound_economy.get_resource("ap")
			)

func unbind_economy() -> void:
	if _bound_economy != null and is_instance_valid(_bound_economy):
		if _bound_economy.has_signal("resources_updated") and _bound_economy.resources_updated.is_connected(_on_economy_resources_updated):
			_bound_economy.resources_updated.disconnect(_on_economy_resources_updated)
	_bound_economy = null

func _on_economy_resources_updated(p_wood: int, p_leather: int, p_metal: int, p_crystal: int, p_ap: int) -> void:
	update_resources(p_wood, p_leather, p_metal, p_crystal, p_ap)

func _on_eventbus_resources_updated(p_wood: int, p_metal: int, p_crystal: int, p_ap: int) -> void:
	update_resources(p_wood, leather, p_metal, p_crystal, p_ap)

func refresh_display() -> void:
	if _round_label != null: _round_label.text = "Rodada: %d" % current_round
	if _layer_label != null: _layer_label.text = "Fase: %s" % current_layer
	if _wood_label != null: _wood_label.text = "Madeira: %d" % wood
	if _leather_label != null: _leather_label.text = "Couro: %d" % leather
	if _metal_label != null: _metal_label.text = "Metal: %d" % metal
	if _crystal_label != null: _crystal_label.text = "Cristal: %d" % crystal
	if _ap_label != null: _ap_label.text = "AP: %d" % ap

func _exit_tree() -> void:
	unbind_economy()
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("EventBus"):
		var eb: Node = tree.root.get_node("EventBus")
		if eb.has_signal("resources_updated") and eb.resources_updated.is_connected(_on_eventbus_resources_updated):
			eb.resources_updated.disconnect(_on_eventbus_resources_updated)
