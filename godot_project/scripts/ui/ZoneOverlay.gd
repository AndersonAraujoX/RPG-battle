# res://scripts/ui/ZoneOverlay.gd
class_name ZoneOverlay
extends Control

## Visual overlay for the 20x20 fortress grid.
## Renders tactical zone highlights (movement, production, repair, balestra targeting),
## elevation delineations, wall health indicators, and breach warning markers.

# ── Highlight Modes ──────────────────────────────────────────────────────────
const MODE_NONE: String = "NONE"
const MODE_MOVEMENT: String = "MOVEMENT"
const MODE_PRODUCTION: String = "PRODUCTION"
const MODE_REPAIR: String = "REPAIR"
const MODE_BALESTRA: String = "BALESTRA"

# ── Highlight Palette ────────────────────────────────────────────────────────
const COLOR_HIGHLIGHT_MOVEMENT: Color = Color(0.1, 0.85, 0.3, 0.45)
const COLOR_HIGHLIGHT_PRODUCTION: Color = Color(0.2, 0.6, 1.0, 0.45)
const COLOR_HIGHLIGHT_REPAIR: Color = Color(1.0, 0.8, 0.2, 0.5)
const COLOR_HIGHLIGHT_BALESTRA: Color = Color(0.9, 0.2, 0.2, 0.5)
const COLOR_BREACH_ALERT: Color = Color(0.95, 0.1, 0.1, 0.75)
const COLOR_SELECTED_ZONE: Color = Color(0.9, 0.7, 1.0, 0.4)

# ── State ────────────────────────────────────────────────────────────────────
var highlight_mode: String = MODE_NONE
var highlighted_zones: Array[String] = []
var highlighted_cells: Array[Vector2i] = []
var breached_walls: Dictionary = {}
var wall_hps: Dictionary = {}
var hovered_zone: String = ""
var selected_zone: String = ""
var cell_size: Vector2 = Vector2(20.0, 20.0)

# Optional board reference for cell-to-zone resolution
var board_ref: Object = null

func _init() -> void:
	custom_minimum_size = Vector2(400.0, 400.0)
	size = custom_minimum_size
	mouse_filter = MOUSE_FILTER_PASS

func _ready() -> void:
	resized.connect(_on_resized)
	_update_cell_size()

func _on_resized() -> void:
	_update_cell_size()
	queue_redraw()

func _update_cell_size() -> void:
	if size.x > 0.0 and size.y > 0.0:
		cell_size = Vector2(size.x / 20.0, size.y / 20.0)

## Highlights zones for movement
func highlight_movement(zones: Array[String]) -> void:
	highlight_mode = MODE_MOVEMENT
	highlighted_zones.clear()
	for z in zones:
		highlighted_zones.append(z.to_upper())
	queue_redraw()

## Highlights zones for workshop production
func highlight_production(zones: Array[String]) -> void:
	highlight_mode = MODE_PRODUCTION
	highlighted_zones.clear()
	for z in zones:
		highlighted_zones.append(z.to_upper())
	queue_redraw()

## Highlights walls for repair
func highlight_repair(wall_ids: Array[String]) -> void:
	highlight_mode = MODE_REPAIR
	highlighted_zones.clear()
	for w in wall_ids:
		highlighted_zones.append(w.to_upper())
	queue_redraw()

## Highlights target zones for tower balestra ranged attacks
func highlight_balestra_targets(zones: Array[String]) -> void:
	highlight_mode = MODE_BALESTRA
	highlighted_zones.clear()
	for z in zones:
		highlighted_zones.append(z.to_upper())
	queue_redraw()

## Clears all active zone and cell highlights
func clear_highlights() -> void:
	highlight_mode = MODE_NONE
	highlighted_zones.clear()
	highlighted_cells.clear()
	queue_redraw()

## Sets or clears the breached state for a wall
func set_wall_breached(wall_id: String, breached: bool) -> void:
	var norm: String = wall_id.to_upper()
	breached_walls[norm] = breached
	queue_redraw()

## Returns true if the wall is marked as breached
func is_wall_breached(wall_id: String) -> bool:
	var norm: String = wall_id.to_upper()
	return breached_walls.get(norm, false)

## Updates tracked HP for a wall
func set_wall_hp(wall_id: String, hp: int, _max_hp: int = 100) -> void:
	var norm: String = wall_id.to_upper()
	wall_hps[norm] = hp
	if hp <= 0:
		breached_walls[norm] = true
	queue_redraw()

func get_wall_hp(wall_id: String) -> int:
	var norm: String = wall_id.to_upper()
	return wall_hps.get(norm, 100)

## Sets hovered zone
func set_hovered_zone(zone_id: String) -> void:
	hovered_zone = zone_id.to_upper()
	queue_redraw()

## Sets selected zone
func set_selected_zone(zone_id: String) -> void:
	selected_zone = zone_id.to_upper()
	queue_redraw()

## Procedural drawing of highlights and breach alerts
func _draw() -> void:
	# Desativado o desenho de retângulos ortogonais 2D
	# para evitar caixas distorcidas sobre a perspectiva isométrica 2.5D do tabuleiro
	pass

## Draws highlight rectangle for a canonical zone based on its 20x20 cell bounds
func _draw_zone_overlay(zone_id: String, color: Color) -> void:
	var norm: String = zone_id.to_upper()
	var rects: Array[Rect2] = _get_zone_bounding_rects(norm)
	for r in rects:
		draw_rect(r, color, true)
		draw_rect(r, Color(color.r, color.g, color.b, 0.9), false, 2.0)

## Resolves screen rects for each canonical zone
func _get_zone_bounding_rects(norm: String) -> Array[Rect2]:
	var result: Array[Rect2] = []
	var cw: float = cell_size.x
	var ch: float = cell_size.y
	
	match norm:
		"TORRE_NOROESTE":
			result.append(Rect2(0, 0, 4 * cw, 4 * ch))
		"TORRE_NORDESTE":
			result.append(Rect2(16 * cw, 0, 4 * cw, 4 * ch))
		"TORRE_SUDOESTE":
			result.append(Rect2(0, 16 * ch, 4 * cw, 4 * ch))
		"TORRE_SUDESTE":
			result.append(Rect2(16 * cw, 16 * ch, 4 * cw, 4 * ch))
		"SPAWN_NORTE":
			result.append(Rect2(4 * cw, 0, 12 * cw, 2 * ch))
		"SPAWN_SUL":
			result.append(Rect2(4 * cw, 18 * ch, 12 * cw, 2 * ch))
		"SPAWN_OESTE":
			result.append(Rect2(0, 4 * ch, 2 * cw, 12 * ch))
		"SPAWN_LESTE":
			result.append(Rect2(18 * cw, 4 * ch, 2 * cw, 12 * ch))
		"MURALHA_NORTE":
			result.append(Rect2(4 * cw, 2 * ch, 12 * cw, 2 * ch))
		"MURALHA_SUL":
			result.append(Rect2(4 * cw, 16 * ch, 12 * cw, 2 * ch))
		"MURALHA_OESTE":
			result.append(Rect2(2 * cw, 4 * ch, 2 * cw, 12 * ch))
		"MURALHA_LESTE":
			result.append(Rect2(16 * cw, 4 * ch, 2 * cw, 12 * ch))
		"CAMARA_CENTRAL":
			result.append(Rect2(8 * cw, 8 * ch, 4 * cw, 4 * ch))
		"CARPINTARIA":
			result.append(Rect2(4 * cw, 4 * ch, 12 * cw, 4 * ch))
		"CURTUME":
			result.append(Rect2(4 * cw, 12 * ch, 12 * cw, 4 * ch))
		"FUNDICAO":
			result.append(Rect2(4 * cw, 4 * ch, 4 * cw, 12 * ch))
		"PATIO_CENTRAL":
			result.append(Rect2(12 * cw, 4 * ch, 4 * cw, 12 * ch))
		_:
			# If full name e.g. ZONE_MURALHA_NORTE
			for known in ["TORRE_NOROESTE", "TORRE_NORDESTE", "TORRE_SUDOESTE", "TORRE_SUDESTE",
				"SPAWN_NORTE", "SPAWN_SUL", "SPAWN_OESTE", "SPAWN_LESTE",
				"MURALHA_NORTE", "MURALHA_SUL", "MURALHA_OESTE", "MURALHA_LESTE",
				"CAMARA_CENTRAL", "CARPINTARIA", "CURTUME", "FUNDICAO", "PATIO_CENTRAL"]:
				if norm.ends_with(known):
					return _get_zone_bounding_rects(known)
	return result
