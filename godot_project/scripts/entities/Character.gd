# res://scripts/entities/Character.gd
class_name Character
extends CharacterBody2D

## Character Entity Controller (Character.gd)
## Core visual and logical entity representing heroes, monsters, and Isectum castes
## on the tactical fortress grid. Fully decoupled, strictly typed, and zero-leak compliant.

# ── Signals ─────────────────────────────────────────────────────────────────
signal hp_changed(current_hp: int, max_hp: int)
signal died()
signal healed(amount: int, current_hp: int)
signal damaged(amount: int, current_hp: int)
signal selection_changed(is_selected: bool)
signal status_effect_applied(effect_name: String)
signal status_effect_removed(effect_name: String)
signal grid_position_changed(new_pos: Vector2i)

# ── Exported Combat Properties ──────────────────────────────────────────────
@export var character_id: String = ""
@export var character_name: String = "Character"
@export var team: String = "A" # "A" = Allies/Heroes, "B" = Enemies/Isectum
@export var max_hp: int = 10
@export var current_hp: int = 10
@export var ac: int = 10
@export var move_speed: int = 3
@export var attack_range: int = 1
@export var damage_type: String = "Cortante"
@export var grid_position: Vector2i = Vector2i(-1, -1)
@export var elevation: int = 0
@export var is_selected: bool = false
@export var is_alive: bool = true
@export var target_display_size: Vector2 = Vector2(30.0, 30.0)

# ── Node References ─────────────────────────────────────────────────────────
@onready var sprite_2d: Sprite2D = $Sprite2D
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@onready var selection_highlight: Node2D = $SelectionHighlight
@onready var retro_hp_bar: Node2D = $RetroHPBar
@onready var hp_fill: ColorRect = $RetroHPBar/FillRect
@onready var hp_bg: ColorRect = $RetroHPBar/BgRect
@onready var status_container: HBoxContainer = $StatusContainer

# ── Status Colors Mapping ───────────────────────────────────────────────────
const STATUS_COLORS: Dictionary = {
	"poisoned": Color(0.20, 0.80, 0.20),
	"envenenado": Color(0.20, 0.80, 0.20),
	"stunned": Color(0.95, 0.85, 0.15),
	"atordoado": Color(0.95, 0.85, 0.15),
	"bleeding": Color(0.85, 0.15, 0.15),
	"sangrando": Color(0.85, 0.15, 0.15),
	"burning": Color(1.00, 0.45, 0.00),
	"queimando": Color(1.00, 0.45, 0.00),
	"frozen": Color(0.30, 0.75, 1.00),
	"congelado": Color(0.30, 0.75, 1.00),
	"paralyzed": Color(0.70, 0.30, 0.90),
	"paralisado": Color(0.70, 0.30, 0.90),
	"blessed": Color(1.00, 0.90, 0.40),
	"foco": Color(1.00, 0.90, 0.40),
}

# ── Internal State ──────────────────────────────────────────────────────────
var character_data: CharacterData = null
var active_status_effects: Array[String] = []

## Property alias for backward/forward compatibility
var active_statuses: Array[String]:
	get:
		return active_status_effects
	set(value):
		active_status_effects = value

var _highlight_tween: Tween = null

# ── Lifecycle Methods ───────────────────────────────────────────────────────

func _ready() -> void:
	if selection_highlight != null:
		selection_highlight.visible = is_selected
		if is_selected:
			_update_selection_tween()
	update_hp_bar()

func _exit_tree() -> void:
	cleanup()

## Cleanup routine to safely release tweens, dynamic badges, and connections
func cleanup() -> void:
	if _highlight_tween != null and _highlight_tween.is_valid():
		_highlight_tween.kill()
		_highlight_tween = null
	clear_all_status_effects()

# ── Initialization & Data Binding ───────────────────────────────────────────

## Setup method for programmatic instantiation
func setup(p_id: String, p_name: String, p_max_hp: int, texture_path: String = "") -> void:
	character_id = p_id
	set_character_name(p_name, p_max_hp)
	if not texture_path.is_empty():
		if ResourceLoader.exists(texture_path) or FileAccess.file_exists(texture_path):
			var tex: Texture2D = load(texture_path) as Texture2D
			if tex != null and sprite_2d != null:
				sprite_2d.texture = tex
				_apply_sprite_scaling(tex)
	else:
		load_texture_for_character(p_id)

## Sets the character name and initializes HP vitals
func set_character_name(p_name: String, p_max_hp: int) -> void:
	character_name = p_name
	max_hp = maxi(p_max_hp, 1)
	current_hp = max_hp
	is_alive = current_hp > 0
	update_hp_bar()

## Ingests structured dictionary (e.g. from personagens.json or test fixtures) or CharacterData
func initialize_from_data(data: Variant) -> void:
	if data is CharacterData:
		initialize_from_resource(data)
		return
	if not (data is Dictionary):
		return
	
	var d: Dictionary = data
	if d.has("id"):
		character_id = str(d["id"])
	if d.has("name"):
		character_name = str(d["name"])
	elif d.has("nome"):
		character_name = str(d["nome"])
	if d.has("team"):
		team = str(d["team"])
	
	if d.has("max_hp"):
		max_hp = maxi(int(d["max_hp"]), 1)
	elif d.has("hp"):
		max_hp = maxi(int(d["hp"]), 1)
	
	if d.has("hp"):
		current_hp = clampi(int(d["hp"]), 0, max_hp)
	else:
		current_hp = max_hp
	
	is_alive = current_hp > 0
	
	if d.has("ac"):
		ac = int(d["ac"])
	elif d.has("ca"):
		ac = int(d["ca"])
	if d.has("velocidade"):
		move_speed = int(d["velocidade"])
	if d.has("alcance"):
		attack_range = int(d["alcance"])
	if d.has("tipo_dano"):
		damage_type = str(d["tipo_dano"])
	
	update_hp_bar()
	if not character_id.is_empty():
		load_texture_for_character(character_id)
	elif not character_name.is_empty():
		load_texture_for_character(character_name)

## Ingests data from a CharacterData Resource
func initialize_from_resource(res: CharacterData) -> void:
	if res == null:
		return
	character_data = res
	character_id = res.id
	character_name = res.name
	team = res.team
	max_hp = maxi(res.max_hp if res.max_hp > 0 else res.hp, 1)
	current_hp = clampi(res.hp, 0, max_hp)
	is_alive = current_hp > 0
	ac = res.ac
	move_speed = res.velocidade
	attack_range = res.alcance
	damage_type = res.tipo_dano
	update_hp_bar()
	if not character_id.is_empty():
		load_texture_for_character(character_id)
	elif not character_name.is_empty():
		load_texture_for_character(character_name)

# ── Combat Vitals: Damage & Healing ──────────────────────────────────────────

## Applies damage, clamps at zero, updates HP bar, and emits signals.
## Returns actual damage dealt.
func take_damage(amount: int) -> int:
	if amount <= 0:
		return 0
	if not is_alive or current_hp <= 0:
		return 0
	
	var actual_damage: int = mini(amount, current_hp)
	current_hp -= actual_damage
	
	update_hp_bar()
	emit_signal("hp_changed", current_hp, max_hp)
	emit_signal("damaged", actual_damage, current_hp)
	
	# Global EventBus notification
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("unit_damaged"):
				eb.emit_signal("unit_damaged", character_id, actual_damage, current_hp, max_hp)
	
	if current_hp <= 0:
		is_alive = false
		current_hp = 0
		emit_signal("died")
		if is_inside_tree():
			var tree: SceneTree = get_tree()
			if tree != null and tree.root.has_node("EventBus"):
				var eb: Node = tree.root.get_node("EventBus")
				if eb.has_signal("unit_died"):
					eb.emit_signal("unit_died", character_id)
	
	return actual_damage

## Applies healing up to max_hp for living units.
## Returns actual healing amount restored.
func heal(amount: int) -> int:
	if amount <= 0:
		return 0
	if not is_alive or current_hp <= 0:
		return 0
	if current_hp >= max_hp:
		return 0
	
	var actual_heal: int = mini(amount, max_hp - current_hp)
	current_hp += actual_heal
	
	update_hp_bar()
	emit_signal("hp_changed", current_hp, max_hp)
	emit_signal("healed", actual_heal, current_hp)
	
	return actual_heal

## Updates the retro health bar (30x4 px) with Pygame-equivalent color shifts:
## Green (> 50%), Yellow (25-50%), Red (<= 25%).
func update_hp_bar() -> void:
	if hp_fill == null:
		return
	var safe_max: float = maxf(float(max_hp), 1.0)
	var ratio: float = clampf(float(current_hp) / safe_max, 0.0, 1.0)
	var fill_width: float = 30.0 * ratio
	hp_fill.size = Vector2(fill_width, 4.0)
	
	if ratio > 0.50:
		hp_fill.color = Color(0.24, 0.78, 0.24, 1.0) # Retro Green
	elif ratio > 0.25:
		hp_fill.color = Color(0.78, 0.78, 0.24, 1.0) # Retro Yellow/Amber
	else:
		hp_fill.color = Color(0.78, 0.24, 0.24, 1.0) # Retro Red

# ── Selection & Highlight ───────────────────────────────────────────────────

## Sets the selection state and toggles the highlight ring.
func set_selected(selected: bool) -> void:
	if is_selected == selected:
		return
	is_selected = selected
	if selection_highlight != null:
		selection_highlight.visible = is_selected
		_update_selection_tween()
	emit_signal("selection_changed", is_selected)

func _update_selection_tween() -> void:
	if _highlight_tween != null and _highlight_tween.is_valid():
		_highlight_tween.kill()
		_highlight_tween = null
	
	if is_selected and selection_highlight != null and is_inside_tree():
		_highlight_tween = create_tween().bind_node(self).set_loops()
		_highlight_tween.tween_property(selection_highlight, "modulate:a", 0.5, 0.6).from(1.0)
		_highlight_tween.tween_property(selection_highlight, "modulate:a", 1.0, 0.6).from(0.5)
	elif selection_highlight != null:
		selection_highlight.modulate.a = 1.0

# ── Status Effects Management ───────────────────────────────────────────────

## Checks if a condition is currently active.
func has_status_effect(effect: String) -> bool:
	return active_status_effects.has(effect)

## Adds a condition, prevents duplicates, spawns a visual badge, and emits signals.
func add_status_effect(effect: String) -> bool:
	if effect.is_empty():
		return false
	if active_status_effects.has(effect):
		return false
	
	active_status_effects.append(effect)
	
	if status_container != null:
		var badge: ColorRect = ColorRect.new()
		badge.name = "StatusBadge_%s" % effect
		badge.custom_minimum_size = Vector2(6.0, 6.0)
		badge.size = Vector2(6.0, 6.0)
		badge.color = STATUS_COLORS.get(effect.to_lower(), Color(0.8, 0.8, 0.8, 1.0))
		status_container.add_child(badge)
	
	emit_signal("status_effect_applied", effect)
	
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("status_applied"):
				eb.emit_signal("status_applied", character_id, effect, 1)
	
	return true

## Removes a condition, destroys the visual badge, and emits signals.
func remove_status_effect(effect: String) -> bool:
	if not active_status_effects.has(effect):
		return false
	
	active_status_effects.erase(effect)
	
	if status_container != null:
		var badge_name: String = "StatusBadge_%s" % effect
		var badge: Node = status_container.get_node_or_null(badge_name)
		if badge != null:
			status_container.remove_child(badge)
			badge.queue_free()
		else:
			for child in status_container.get_children():
				if child.name == badge_name or child.name.ends_with(effect):
					status_container.remove_child(child)
					child.queue_free()
					break
	
	emit_signal("status_effect_removed", effect)
	
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("status_removed"):
				eb.emit_signal("status_removed", character_id, effect)
	
	return true

## Clears all active status conditions and frees all badge nodes.
func clear_all_status_effects() -> void:
	active_status_effects.clear()
	if status_container != null:
		for child in status_container.get_children():
			status_container.remove_child(child)
			child.queue_free()

# ── Tactical Grid Integration ───────────────────────────────────────────────

## Sets the tactical grid coordinate and emits signals
func set_grid_position(new_pos: Vector2i) -> void:
	if grid_position == new_pos:
		return
	var old_pos: Vector2i = grid_position
	grid_position = new_pos
	emit_signal("grid_position_changed", new_pos)
	
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("unit_moved"):
				eb.emit_signal("unit_moved", character_id, old_pos, new_pos)

func get_grid_position() -> Vector2i:
	return grid_position

# ── Texture Discovery & Scaling ─────────────────────────────────────────────

## Multi-tier search algorithm to locate and load character visual assets.
## Searches: 1. Isectum pixel art, 2. Heroes, 3. Animation portraits, 4. Monsters, 5. Bosses.
func load_texture_for_character(id_to_find: String) -> bool:
	if id_to_find.is_empty():
		return false
	
	var raw_name: String = id_to_find.strip_edges()
	var lower_name: String = raw_name.to_lower()
	var snake_name: String = raw_name.to_snake_case()
	var capitalized_name: String = raw_name.capitalize().replace(" ", "")
	
	var candidate_paths: Array[String] = [
		# 0. Hero Portraits (128x128 RGBA)
		"res://assets/images/characters/portraits/%s_portrait.png" % lower_name,
		"res://assets/images/characters/portraits/%s_portrait.png" % snake_name,
		"res://assets/images/characters/portraits/%s.png" % lower_name,
		# 1. Monsters / Isectum pixel art (32x32)
		"res://assets/images/characters/monsters/isectum/%s.png" % snake_name,
		"res://assets/images/characters/monsters/isectum/%s.png" % lower_name,
		"res://assets/images/characters/monsters/isectum/%s.png" % raw_name,
		# 2. Heroes
		"res://assets/images/characters/heroes/%s.png" % raw_name,
		"res://assets/images/characters/heroes/%s.png" % lower_name,
		"res://assets/images/characters/heroes/%s.png" % capitalized_name,
		# 3. Animation Processed
		"res://assets/images/characters/animation/processed/%s.png" % lower_name,
		"res://assets/images/characters/animation/processed/%s.png" % raw_name,
		# 4. Monsters
		"res://assets/images/characters/monsters/%s.png" % snake_name,
		"res://assets/images/characters/monsters/%s.png" % lower_name,
		"res://assets/images/characters/monsters/%s.png" % raw_name,
		# 5. Bosses
		"res://assets/images/characters/bosses/%s.png" % raw_name,
		"res://assets/images/characters/bosses/%s.png" % lower_name,
		"res://assets/images/characters/bosses/%s.png" % snake_name
	]
	
	for path in candidate_paths:
		if ResourceLoader.exists(path) or FileAccess.file_exists(path):
			var tex: Texture2D = load(path) as Texture2D
			if tex != null:
				if sprite_2d != null:
					sprite_2d.texture = tex
					_apply_sprite_scaling(tex)
				return true
	
	return false

## Normalizes texture scale so that it fits within target_display_size without distortion
func _apply_sprite_scaling(tex: Texture2D) -> void:
	if tex == null or sprite_2d == null:
		return
	var tex_size: Vector2 = tex.get_size()
	if tex_size.x <= 0.0 or tex_size.y <= 0.0:
		return
	if target_display_size.x <= 0.0 or target_display_size.y <= 0.0:
		sprite_2d.scale = Vector2.ONE
		return
	var scale_factor: float = minf(target_display_size.x / tex_size.x, target_display_size.y / tex_size.y)
	sprite_2d.scale = Vector2(scale_factor, scale_factor)

## Isolates a single frame from a multi-frame spritesheet (e.g. 4x2 or 4x4) and scales it to fit target_display_size
func slice_spritesheet_frame(col: int = 0, row: int = 0, cols: int = 4, rows: int = 2) -> bool:
	if sprite_2d == null or sprite_2d.texture == null or cols <= 0 or rows <= 0:
		return false
	var tex_sz: Vector2 = sprite_2d.texture.get_size()
	var frame_w: float = tex_sz.x / float(cols)
	var frame_h: float = tex_sz.y / float(rows)
	sprite_2d.region_enabled = true
	sprite_2d.region_rect = Rect2(float(col) * frame_w, float(row) * frame_h, frame_w, frame_h)
	if target_display_size.x > 0.0 and target_display_size.y > 0.0:
		var scale_f: float = minf(target_display_size.x / frame_w, target_display_size.y / frame_h)
		sprite_2d.scale = Vector2(scale_f, scale_f)
	return true

## Auto-detects whether the loaded texture is a known multi-frame spritesheet and isolates frame 0
func auto_slice_multiframe() -> bool:
	if sprite_2d == null or sprite_2d.texture == null:
		return false
	var tex_sz: Vector2 = sprite_2d.texture.get_size()
	if int(tex_sz.x) == 676 and int(tex_sz.y) == 369:
		return slice_spritesheet_frame(0, 0, 4, 2)
	elif int(tex_sz.x) == 1024 and int(tex_sz.y) == 1024:
		return slice_spritesheet_frame(0, 0, 4, 4)
	return false
