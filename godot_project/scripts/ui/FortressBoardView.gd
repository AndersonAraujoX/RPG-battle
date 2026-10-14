# res://scripts/ui/FortressBoardView.gd
class_name FortressBoardView
extends Control

## Interactive visual representation of the 20x20 tactical fortress board and its 17 canonical zones.
## Renders terrain floors, elevation levels (0, 1, 2), wall health & breach warnings,
## and coordinates with ZoneOverlay for tactical highlights.

signal zone_clicked(zone_id: String)
signal zone_hovered(zone_id: String)
signal zone_unhovered(zone_id: String)
signal wall_breach_alert(wall_id: String)
signal unit_selected(unit_id: String, unit_data: Dictionary)
signal unit_deselected(unit_id: String)
signal unit_moved_to_cell(unit_id: String, to_pos: Vector2i)
signal unit_attack_requested(attacker_id: String, target_id: String)
signal item_pickup_requested(unit_id: String, pos: Vector2i, item_data: Dictionary)

# ── Canonical Zone Colors ───────────────────────────────────────────────────
const COLOR_CAMARA: Color = Color(0.75, 0.60, 0.15, 0.9)       # Gold / Amber
const COLOR_CARPINTARIA: Color = Color(0.20, 0.55, 0.20, 0.9)  # Forest Wood Green
const COLOR_CURTUME: Color = Color(0.65, 0.40, 0.20, 0.9)      # Leather Tan
const COLOR_FUNDICAO: Color = Color(0.35, 0.40, 0.55, 0.9)     # Dark Steel
const COLOR_PATIO: Color = Color(0.22, 0.35, 0.65, 0.9)        # Royal Cobblestone
const COLOR_WALL: Color = Color(0.48, 0.50, 0.56, 0.95)        # Fortified Stone
const COLOR_WALL_BREACHED: Color = Color(0.85, 0.15, 0.15, 0.95) # Ruined Red
const COLOR_TOWER: Color = Color(0.35, 0.36, 0.46, 1.0)        # Watchtower Grey
const COLOR_SPAWN: Color = Color(0.16, 0.24, 0.14, 0.85)       # Swarm Perimeter Dark

# ── Geometry & Board State ───────────────────────────────────────────────────
const GRID_SIZE: int = 20
var cell_size: Vector2 = Vector2(20.0, 20.0)
var elevation_offset_px: float = 4.0

var _bound_board: Object = null
var zone_overlay: ZoneOverlay = null

var selected_zone: String = ""
var hovered_zone: String = ""
var breached_walls: Dictionary = {}
var wall_hps: Dictionary = {}

# ── FFT Tactical Character & Item State ──────────────────────────────────────
var selected_unit_id: String = ""
var reachable_cells: Array[Vector2i] = []
var attackable_cells: Array[Vector2i] = []
var hovered_cell: Vector2i = Vector2i(-1, -1)
var _anim_timer: float = 0.0

# ── Combat VFX & Animation Queues ────────────────────────────────────────────
var _unit_visual_positions: Dictionary = {}    # unit_id -> Vector2 (interpolated screen pos)
var _unit_anim_offsets: Dictionary = {}        # unit_id -> Vector2 (lunge recoil offset)
var _unit_anim_flashes: Dictionary = {}        # unit_id -> { "timer": float, "duration": float, "color": Color }
var _active_projectiles: Array[Dictionary] = [] # { "start_pos": Vector2, "end_pos": Vector2, "progress": float, "duration": float, "arc_height": float, "type": String, "color": Color }
var _floating_combat_texts: Array[Dictionary] = [] # { "text": String, "pos": Vector2, "color": Color, "timer": float, "duration": float, "velocity": Vector2, "is_crit": bool }

# ── Screen Shake & Combat Particles (Juice & Feedback) ───────────────────────
var shake_intensity: float = 0.0
var shake_duration: float = 0.0
var shake_timer: float = 0.0
var shake_offset: Vector2 = Vector2.ZERO
var _combat_particles: Array[Dictionary] = [] # { "pos": Vector2, "vel": Vector2, "color": Color, "timer": float, "duration": float, "size": float, "gravity": float }

# ── Sprites & Texture Cache ──────────────────────────────────────────────────
var _unit_texture_cache: Dictionary = {}

# ── Câmera FFT — Pan, Zoom & Rotação 4-Way ─────────────────────────────────────
## Ângulo da câmera isometria FFT: 0 (0° NW), 1 (90° NE), 2 (180° SE), 3 (270° SW)
var camera_angle_idx: int = 0
## Deslocamento do panning (em pixels de tela, antes do zoom)
var cam_pan: Vector2 = Vector2.ZERO
## Nível de zoom da câmera: 1.0 = normal, >1 = aproximado, <1 = afastado
var cam_zoom: float = 1.0
## Estado de drag do mouse para pan
var _is_panning: bool = false
var _pan_start_mouse: Vector2 = Vector2.ZERO
var _pan_start_cam: Vector2 = Vector2.ZERO

const CAM_ZOOM_MIN: float = 0.5
const CAM_ZOOM_MAX: float = 3.0
const CAM_ZOOM_STEP: float = 0.15
const CAM_PAN_KEYBOARD_SPEED: float = 300.0  # px/s ao segurar tecla

## Converte coordenadas centradas (dx, dy) para a rotação de câmera ativa
func get_rotated_dx_dy(dx: float, dy: float) -> Vector2:
	match camera_angle_idx:
		1:
			return Vector2(dy, -dx)
		2:
			return Vector2(-dx, -dy)
		3:
			return Vector2(-dy, dx)
		_:
			return Vector2(dx, dy)

## Rotaciona a câmera FFT 90° para a esquerda (Sentido anti-horário / [Q])
func rotate_camera_left() -> void:
	camera_angle_idx = posmod(camera_angle_idx - 1, 4)
	queue_redraw()

## Rotaciona a câmera FFT 90° para a direita (Sentido horário / [E])
func rotate_camera_right() -> void:
	camera_angle_idx = posmod(camera_angle_idx + 1, 4)
	queue_redraw()

func clear_texture_cache() -> void:
	_unit_texture_cache.clear()

func _init() -> void:
	custom_minimum_size = Vector2(400.0, 400.0)
	size = custom_minimum_size
	mouse_filter = MOUSE_FILTER_PASS

func _ready() -> void:
	_setup_overlay()
	resized.connect(_on_resized)
	_update_cell_size()
	_connect_event_bus()

func _process(delta: float) -> void:
	_anim_timer += delta

	var needs_redraw: bool = false

	# 1. Atualiza flashes de dano das unidades
	if not _unit_anim_flashes.is_empty():
		var finished_flashes: Array = []
		for uid in _unit_anim_flashes.keys():
			var f_info: Dictionary = _unit_anim_flashes[uid]
			f_info["timer"] = float(f_info.get("timer", 0.0)) - delta
			if float(f_info["timer"]) <= 0.0:
				finished_flashes.append(uid)
		for f_id in finished_flashes:
			_unit_anim_flashes.erase(f_id)
		needs_redraw = true

	# 2. Atualiza projéteis ativos
	if not _active_projectiles.is_empty():
		var finished_proj: Array = []
		for i in range(_active_projectiles.size()):
			var p: Dictionary = _active_projectiles[i]
			var dur: float = maxf(0.01, float(p.get("duration", 0.3)))
			p["progress"] = float(p.get("progress", 0.0)) + (delta / dur)
			if float(p["progress"]) >= 1.0:
				finished_proj.append(i)
		for f_idx in range(finished_proj.size() - 1, -1, -1):
			_active_projectiles.remove_at(finished_proj[f_idx])
		needs_redraw = true

	# 3. Atualiza Floating Combat Texts
	if not _floating_combat_texts.is_empty():
		var finished_texts: Array = []
		for i in range(_floating_combat_texts.size()):
			var ft: Dictionary = _floating_combat_texts[i]
			ft["timer"] = float(ft.get("timer", 0.0)) + delta
			var vel: Vector2 = ft.get("velocity", Vector2(0.0, -28.0 * cam_zoom))
			ft["pos"] = Vector2(ft.get("pos", Vector2.ZERO)) + vel * delta
			if float(ft["timer"]) >= float(ft.get("duration", 0.95)):
				finished_texts.append(i)
		for f_t_idx in range(finished_texts.size() - 1, -1, -1):
			_floating_combat_texts.remove_at(finished_texts[f_t_idx])
		needs_redraw = true

	# 4. Atualiza Screen Shake
	if shake_timer > 0.0:
		shake_timer = maxf(0.0, shake_timer - delta)
		if shake_timer > 0.0:
			var p_ratio: float = shake_timer / maxf(0.01, shake_duration)
			shake_offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * shake_intensity * p_ratio
		else:
			shake_offset = Vector2.ZERO
		needs_redraw = true
	else:
		shake_offset = Vector2.ZERO

	# 5. Atualiza Partículas de Combate
	if not _combat_particles.is_empty():
		var dead_p: Array[int] = []
		for p_idx in range(_combat_particles.size()):
			var p: Dictionary = _combat_particles[p_idx]
			p["timer"] = float(p.get("timer", 0.0)) + delta
			var p_grav: float = float(p.get("gravity", 90.0))
			var p_vel: Vector2 = Vector2(p.get("vel", Vector2.ZERO)) + Vector2(0.0, p_grav * delta)
			p["vel"] = p_vel
			p["pos"] = Vector2(p.get("pos", Vector2.ZERO)) + p_vel * delta
			if float(p["timer"]) >= float(p.get("duration", 0.6)):
				dead_p.append(p_idx)
		for d_idx in range(dead_p.size() - 1, -1, -1):
			_combat_particles.remove_at(dead_p[d_idx])
		needs_redraw = true

	# ── Pan com teclado (WASD / Setas) — estilo FFT ──────────────────────────
	if is_visible_in_tree() and has_focus():
		var kpan: Vector2 = Vector2.ZERO
		if Input.is_action_pressed("ui_left")  or Input.is_key_pressed(KEY_A): kpan.x += 1.0
		if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D): kpan.x -= 1.0
		if Input.is_action_pressed("ui_up")    or Input.is_key_pressed(KEY_W): kpan.y += 1.0
		if Input.is_action_pressed("ui_down")  or Input.is_key_pressed(KEY_S): kpan.y -= 1.0
		if Input.is_key_pressed(KEY_R): reset_camera()     # R = Reset câmera
		if kpan != Vector2.ZERO:
			cam_pan += kpan * CAM_PAN_KEYBOARD_SPEED * delta
			cam_pan = _clamp_pan(cam_pan)
			needs_redraw = true

	# Redraw contínuo para animações (itens, auras, seleção, panning, VFX, partículas, tochas)
	if is_visible_in_tree() and (
		needs_redraw
		or _is_panning
		or shake_timer > 0.0
		or not _combat_particles.is_empty()
		or not _unit_visual_positions.is_empty()
		or not _unit_anim_offsets.is_empty()
		or not selected_unit_id.is_empty()
		or not reachable_cells.is_empty()
		or (_bound_board != null and _bound_board.has_method("get_all_items") and not _bound_board.get_all_items().is_empty())
		or true # Tochas dinâmicas piscando a cada frame
	):
		queue_redraw()

## Dispara tremor de tela tático (Screen Shake)
func trigger_screen_shake(intensity: float = 6.0, duration: float = 0.35) -> void:
	shake_intensity = intensity
	shake_duration = maxf(0.01, duration)
	shake_timer = shake_duration
	queue_redraw()

## Spawna partículas de combate procedurais (lascas de pedra, ácido, faíscas, poeira)
func spawn_impact_particles(world_pos: Vector2, p_type: String = "stone", count: int = 8) -> void:
	for _i in range(count):
		var ang: float = randf_range(0.0, TAU)
		var spd: float = randf_range(35.0, 95.0)
		var vel: Vector2 = Vector2(cos(ang), sin(ang) - 0.5) * spd
		var p_col: Color = Color(0.65, 0.60, 0.55, 0.9)
		var p_dur: float = randf_range(0.35, 0.65)
		var p_sz: float = randf_range(2.0, 4.0)
		var p_grav: float = 120.0

		match p_type:
			"acid":
				p_col = Color(0.25, 0.95, 0.35, 0.9)
				p_grav = 80.0
			"spark":
				p_col = Color(1.0, 0.90, 0.25, 0.95)
				spd = randf_range(60.0, 130.0)
				vel = Vector2(cos(ang), sin(ang) - 0.7) * spd
				p_grav = 150.0
			"dust":
				p_col = Color(0.85, 0.85, 0.90, 0.5)
				p_dur = randf_range(0.25, 0.45)
				p_sz = randf_range(2.5, 4.5)
				p_grav = -15.0
			"stone":
				p_col = Color(0.55, 0.52, 0.50, 0.9)

		_combat_particles.append({
			"pos": world_pos,
			"vel": vel,
			"color": p_col,
			"timer": 0.0,
			"duration": p_dur,
			"size": p_sz,
			"gravity": p_grav
		})
	queue_redraw()


func _setup_overlay() -> void:
	if zone_overlay == null:
		zone_overlay = ZoneOverlay.new()
		zone_overlay.name = "ZoneOverlay"
		zone_overlay.set_anchors_preset(PRESET_FULL_RECT)
		zone_overlay.mouse_filter = MOUSE_FILTER_IGNORE
		add_child(zone_overlay)

func _on_resized() -> void:
	_update_cell_size()
	queue_redraw()

func _update_cell_size() -> void:
	if size.x > 0.0 and size.y > 0.0:
		cell_size = Vector2(size.x / float(GRID_SIZE), size.y / float(GRID_SIZE))

func _connect_event_bus() -> void:
	if not Engine.is_editor_hint():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("wall_breached") and not eb.wall_breached.is_connected(_on_eventbus_wall_breached):
				eb.wall_breached.connect(_on_eventbus_wall_breached)

# ── Câmera FFT — Pan & Zoom ───────────────────────────────────────────────────

## Reseta câmera para posição e zoom padrão
func reset_camera() -> void:
	cam_pan = Vector2.ZERO
	cam_zoom = 1.0
	camera_angle_idx = 0
	queue_redraw()

## Centraliza câmera sobre uma unidade específica do tabuleiro
func pan_to_unit(unit_id: String) -> void:
	if _bound_board == null or not _bound_board.has_method("get_unit_position"):
		return
	var upos: Vector2i = _bound_board.get_unit_position(unit_id)
	if upos == Vector2i(-1, -1):
		return
	# Converte a posição da célula para coordenadas de tela sem pan
	var world_pos: Vector2 = get_cell_screen_coords(upos.x, upos.y)
	# Pan para que a unidade fique no centro da view
	cam_pan = (size * 0.5) - world_pos * cam_zoom
	cam_pan = _clamp_pan(cam_pan)
	queue_redraw()

## Limita o pan para não sair demais do tabuleiro
func _clamp_pan(pan: Vector2) -> Vector2:
	var board_w: float = size.x * cam_zoom
	var board_h: float = size.y * cam_zoom
	var margin_x: float = minf(size.x * 0.5, board_w * 0.5)
	var margin_y: float = minf(size.y * 0.5, board_h * 0.5)
	pan.x = clampf(pan.x, -board_w + margin_x, margin_x)
	pan.y = clampf(pan.y, -board_h + margin_y, margin_y)
	return pan

## Aplica zoom centrado no ponto de tela dado (geralmente posição do mouse)
func _apply_zoom(new_zoom: float, pivot_screen: Vector2) -> void:
	var old_zoom: float = cam_zoom
	cam_zoom = clampf(new_zoom, CAM_ZOOM_MIN, CAM_ZOOM_MAX)
	# Ajusta pan para manter o ponto do pivot no mesmo lugar
	cam_pan = pivot_screen - (pivot_screen - cam_pan) * (cam_zoom / old_zoom)
	cam_pan = _clamp_pan(cam_pan)
	queue_redraw()

## Converte posição de tela (com câmera) de volta para coordenadas world (sem câmera)
func _screen_to_world(screen_pos: Vector2) -> Vector2:
	return (screen_pos - cam_pan) / cam_zoom

# ── Terrain Textures Cache ────────────────────────────────────────────────────
var _terrain_textures: Dictionary = {}

func clear_terrain_textures() -> void:
	_terrain_textures.clear()

func _load_terrain_texture(key: String, path: String) -> Texture2D:
	if _terrain_textures.has(key):
		return _terrain_textures[key]
	var tex: Texture2D = null
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		tex = load(path) as Texture2D
	_terrain_textures[key] = tex
	return tex

## Returns the high-resolution pixel art texture for a specific tactical board zone
func get_zone_texture(zone_id: String) -> Texture2D:
	var norm: String = zone_id.to_upper()
	if norm.find("TORRE") != -1 or norm.find("MURALHA") != -1:
		return _load_terrain_texture("parede", "res://assets/images/environment/terreno_parede.png")
	elif norm == "CARPINTARIA":
		return _load_terrain_texture("carpintaria", "res://assets/images/environment/terreno_exterior.png")
	elif norm == "CURTUME":
		return _load_terrain_texture("curtume", "res://assets/images/environment/terreno_dificil.png")
	elif norm == "FUNDICAO":
		return _load_terrain_texture("fundicao", "res://assets/images/environment/terreno_rocha.png")
	elif norm == "CAMARA_CENTRAL":
		return _load_terrain_texture("camara", "res://assets/images/environment/terreno_corredor.png")
	elif norm == "PATIO_CENTRAL" or norm == "_PATIO_BAIXO" or norm == "_CORREDOR":
		return _load_terrain_texture("patio", "res://assets/images/environment/terreno_normal.png")
	elif norm == "_CAMPO" or norm == "_EXTERIOR" or norm.find("SPAWN") != -1:
		return _load_terrain_texture("campo", "res://assets/images/environment/terreno_campo.png")
	return null



## Converts grid coordinates (0..19, 0..19) to screen coordinates with elevation offset
func grid_to_screen(grid_pos: Vector2i, elevation: int = 0) -> Vector2:
	var sx: float = float(grid_pos.x) * cell_size.x
	var sy: float = float(grid_pos.y) * cell_size.y - float(elevation) * elevation_offset_px
	return Vector2(sx, sy)

func is_valid_cell(pos: Vector2i) -> bool:
	if _bound_board != null and _bound_board.has_method("is_valid_cell"):
		return _bound_board.is_valid_cell(pos)
	return pos.x >= 0 and pos.x < GRID_SIZE and pos.y >= 0 and pos.y < GRID_SIZE

## Canonical isometric projection from grid cell to screen pixel position
func get_cell_screen_coords(gx: int, gy: int) -> Vector2:
	var r_width: float = size.x if size.x > 0.0 else 400.0
	var r_height: float = size.y if size.y > 0.0 else 400.0
	var zoom: float = clampf(r_width / 680.0, 0.75, 1.25)
	var tw: float = 24.0 * zoom
	var th: float = 12.0 * zoom
	var es: float = 8.0 * zoom
	var cx: float = r_width * 0.5
	var cy: float = r_height * 0.48
	var el: int = get_elevation_at(Vector2i(gx, gy))
	var base_dx: float = float(gx) - 9.5
	var base_dy: float = float(gy) - 9.5
	var rot_d: Vector2 = get_rotated_dx_dy(base_dx, base_dy)
	var dx: float = rot_d.x
	var dy: float = rot_d.y
	var sx: float = (dx - dy) * (tw * 0.5) + cx
	var sy: float = (dx + dy) * (th * 0.5) - float(el) * es + cy
	return Vector2(sx, sy)

## Precise isometric click collision detection (Pygame parity)
func iso_screen_to_grid(screen_pos: Vector2) -> Vector2i:
	if size.x <= 0 or size.y <= 0:
		return Vector2i(-1, -1)

	var r_width: float = size.x
	var r_height: float = size.y
	var zoom: float = clampf(r_width / 680.0, 0.75, 1.25)
	var tw: float = 24.0 * zoom
	var th: float = 12.0 * zoom
	var es: float = 8.0 * zoom
	var cx: float = r_width * 0.5
	var cy: float = r_height * 0.48

	var candidates: Array[Dictionary] = []
	for gy in range(GRID_SIZE):
		for gx in range(GRID_SIZE):
			var el: int = get_elevation_at(Vector2i(gx, gy))
			var base_dx: float = float(gx) - 9.5
			var base_dy: float = float(gy) - 9.5
			var rot_d: Vector2 = get_rotated_dx_dy(base_dx, base_dy)
			var dx: float = rot_d.x
			var dy: float = rot_d.y
			var sx: float = (dx - dy) * (tw * 0.5) + cx
			var sy: float = (dx + dy) * (th * 0.5) - float(el) * es + cy
			var proj_y: float = (dx + dy) * (th * 0.5)
			candidates.append({
				"pos": Vector2i(gx, gy),
				"sx": sx,
				"sy": sy,
				"el": el,
				"proj_y": proj_y
			})

	# Depth sort: higher depth and higher elevation checked first
	candidates.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if a["proj_y"] == b["proj_y"]:
			return a["el"] > b["el"]
		return a["proj_y"] > b["proj_y"]
	)

	for c in candidates:
		var sx: float = c["sx"]
		var sy: float = c["sy"]
		var el: int = c["el"]
		var thick: float = float(el) * es
		# Isometric top diamond collision
		var dx_: float = absf(screen_pos.x - sx) / (tw * 0.5 + 0.0001)
		var dy_: float = absf(screen_pos.y - sy) / (th * 0.5 + 0.0001)
		if dx_ + dy_ <= 1.0:
			return c["pos"]
		# Lateral 3D face collision for elevated tiles (walls and towers)
		if el > 0:
			var sy_bot: float = sy + thick
			if screen_pos.x >= sx - tw * 0.5 and screen_pos.x <= sx + tw * 0.5 and screen_pos.y >= sy and screen_pos.y <= sy_bot + th * 0.5:
				var dy_side: float = absf(screen_pos.y - (sy + sy_bot) * 0.5) / (thick * 0.5 + th * 0.5)
				if dx_ + dy_side <= 1.2:
					return c["pos"]

	return Vector2i(-1, -1)

## Converts screen coordinates to 20x20 grid coordinates
func screen_to_grid(screen_pos: Vector2) -> Vector2i:
	var gx: int = int(screen_pos.x / cell_size.x) if cell_size.x > 0 else 0
	var gy: int = int(screen_pos.y / cell_size.y) if cell_size.y > 0 else 0
	return Vector2i(clampi(gx, 0, GRID_SIZE - 1), clampi(gy, 0, GRID_SIZE - 1))

## Returns the canonical zone ID for a given grid cell coordinate
func get_zone_at(pos: Vector2i) -> String:
	if _bound_board != null and _bound_board.has_method("get_zone_at"):
		return _bound_board.get_zone_at(pos)
	
	# Pure procedural fallback based on canonical 20x20 partitioning
	var x: int = pos.x
	var y: int = pos.y
	if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
		return ""
	
	# Towers (4x4 corners)
	if x < 4 and y < 4: return "TORRE_NOROESTE"
	if x >= 16 and y < 4: return "TORRE_NORDESTE"
	if x < 4 and y >= 16: return "TORRE_SUDOESTE"
	if x >= 16 and y >= 16: return "TORRE_SUDESTE"
	
	# Spawns (outermost 2-cell bands)
	if y < 2: return "SPAWN_NORTE"
	if y >= 18: return "SPAWN_SUL"
	if x < 2: return "SPAWN_OESTE"
	if x >= 18: return "SPAWN_LESTE"
	
	# Walls (2-cell defensive perimeter)
	if y < 4: return "MURALHA_NORTE"
	if y >= 16: return "MURALHA_SUL"
	if x < 4: return "MURALHA_OESTE"
	if x >= 16: return "MURALHA_LESTE"
	
	# Central Core (4x4)
	if x >= 8 and x < 12 and y >= 8 and y < 12:
		return "CAMARA_CENTRAL"
	
	# Interior Quadrants
	var dx: float = float(x) - 9.5
	var dy: float = float(y) - 9.5
	if absf(dy) > absf(dx):
		return "CARPINTARIA" if dy < 0.0 else "CURTUME"
	elif absf(dx) > absf(dy):
		return "FUNDICAO" if dx < 0.0 else "PATIO_CENTRAL"
	else:
		if dy < 0.0 and dx < 0.0: return "FUNDICAO"
		elif dy < 0.0 and dx > 0.0: return "CARPINTARIA"
		elif dy > 0.0 and dx < 0.0: return "CURTUME"
		else: return "PATIO_CENTRAL"

## Returns elevation (0, 1, or 2) for a given zone
func get_elevation(zone_id: String) -> int:
	var norm: String = zone_id.to_upper()
	if norm.find("TORRE") != -1:
		return 2
	elif norm.find("MURALHA") != -1:
		return 1
	return 0

## Returns elevation for a given cell position
func get_elevation_at(pos: Vector2i) -> int:
	return get_elevation(get_zone_at(pos))

## Returns theme color for a given zone
func get_zone_color(zone_id: String) -> Color:
	var norm: String = zone_id.to_upper()
	if norm.find("CAMARA") != -1: return COLOR_CAMARA
	if norm.find("CARPINTARIA") != -1: return COLOR_CARPINTARIA
	if norm.find("CURTUME") != -1: return COLOR_CURTUME
	if norm.find("FUNDICAO") != -1: return COLOR_FUNDICAO
	if norm.find("PATIO") != -1: return COLOR_PATIO
	if norm.find("TORRE") != -1: return COLOR_TOWER
	if norm.find("SPAWN") != -1: return COLOR_SPAWN
	if norm.find("MURALHA") != -1:
		if is_wall_breached(norm):
			return COLOR_WALL_BREACHED
		return COLOR_WALL
	return Color(0.2, 0.2, 0.2, 0.8)

# ── Highlighting & Interaction ───────────────────────────────────────────────
func select_zone(zone_id: String) -> void:
	selected_zone = zone_id.to_upper()
	if zone_overlay != null:
		zone_overlay.set_selected_zone(selected_zone)
	zone_clicked.emit(selected_zone)
	queue_redraw()

func get_selected_zone() -> String:
	return selected_zone

func highlight_movement(zones: Array[String]) -> void:
	if zone_overlay != null:
		zone_overlay.highlight_movement(zones)

func highlight_production(zones: Array[String]) -> void:
	if zone_overlay != null:
		zone_overlay.highlight_production(zones)

func highlight_repair(wall_ids: Array[String]) -> void:
	if zone_overlay != null:
		zone_overlay.highlight_repair(wall_ids)

func highlight_balestra_targets(zones: Array[String]) -> void:
	if zone_overlay != null:
		zone_overlay.highlight_balestra_targets(zones)

func clear_highlights() -> void:
	if zone_overlay != null:
		zone_overlay.clear_highlights()

# ── Breach & Wall State ──────────────────────────────────────────────────────
func set_wall_breached(wall_id: String, breached: bool) -> void:
	var norm: String = wall_id.to_upper()
	breached_walls[norm] = breached
	if zone_overlay != null:
		zone_overlay.set_wall_breached(norm, breached)
	if breached:
		wall_breach_alert.emit(norm)
	queue_redraw()

func is_wall_breached(wall_id: String) -> bool:
	var norm: String = wall_id.to_upper()
	for k in breached_walls:
		if norm.ends_with(k) or norm == k:
			return breached_walls[k]
	return false

func update_wall_hp(wall_id: String, hp: int, max_hp: int = 100) -> void:
	var norm: String = wall_id.to_upper()
	wall_hps[norm] = hp
	if hp <= 0:
		set_wall_breached(norm, true)
	else:
		set_wall_breached(norm, false)
	if zone_overlay != null:
		zone_overlay.set_wall_hp(norm, hp, max_hp)
	queue_redraw()

# ── Model Binding ────────────────────────────────────────────────────────────
func bind_board(board: Object) -> void:
	unbind_board()
	_bound_board = board
	if _bound_board != null:
		if _bound_board.has_signal("wall_damaged"):
			_bound_board.wall_damaged.connect(_on_board_wall_damaged)
		if _bound_board.has_signal("wall_repaired"):
			_bound_board.wall_repaired.connect(_on_board_wall_repaired)
		if _bound_board.has_signal("wall_breached"):
			_bound_board.wall_breached.connect(_on_board_wall_breached)
		if _bound_board.has_signal("item_placed"):
			_bound_board.item_placed.connect(_on_board_item_changed)
		if _bound_board.has_signal("item_collected"):
			_bound_board.item_collected.connect(_on_board_item_collected_signal)
		if _bound_board.has_signal("item_removed"):
			_bound_board.item_removed.connect(_on_board_item_removed_signal)
		if _bound_board.has_signal("unit_moved"):
			_bound_board.unit_moved.connect(_on_board_unit_moved_signal)
		if _bound_board.has_signal("unit_stats_changed"):
			_bound_board.unit_stats_changed.connect(_on_board_unit_stats_changed)
		if zone_overlay != null:
			zone_overlay.board_ref = _bound_board

func unbind_board() -> void:
	if _bound_board != null and is_instance_valid(_bound_board):
		if _bound_board.has_signal("wall_damaged") and _bound_board.wall_damaged.is_connected(_on_board_wall_damaged):
			_bound_board.wall_damaged.disconnect(_on_board_wall_damaged)
		if _bound_board.has_signal("wall_repaired") and _bound_board.wall_repaired.is_connected(_on_board_wall_repaired):
			_bound_board.wall_repaired.disconnect(_on_board_wall_repaired)
		if _bound_board.has_signal("wall_breached") and _bound_board.wall_breached.is_connected(_on_board_wall_breached):
			_bound_board.wall_breached.disconnect(_on_board_wall_breached)
		if _bound_board.has_signal("item_placed") and _bound_board.item_placed.is_connected(_on_board_item_changed):
			_bound_board.item_placed.disconnect(_on_board_item_changed)
		if _bound_board.has_signal("item_collected") and _bound_board.item_collected.is_connected(_on_board_item_collected_signal):
			_bound_board.item_collected.disconnect(_on_board_item_collected_signal)
		if _bound_board.has_signal("item_removed") and _bound_board.item_removed.is_connected(_on_board_item_removed_signal):
			_bound_board.item_removed.disconnect(_on_board_item_removed_signal)
		if _bound_board.has_signal("unit_moved") and _bound_board.unit_moved.is_connected(_on_board_unit_moved_signal):
			_bound_board.unit_moved.disconnect(_on_board_unit_moved_signal)
		if _bound_board.has_signal("unit_stats_changed") and _bound_board.unit_stats_changed.is_connected(_on_board_unit_stats_changed):
			_bound_board.unit_stats_changed.disconnect(_on_board_unit_stats_changed)
	_bound_board = null
	if zone_overlay != null:
		zone_overlay.board_ref = null

func _on_board_wall_damaged(wall_id: String, _amount: int, remaining_hp: int) -> void:
	update_wall_hp(wall_id, remaining_hp)

func _on_board_wall_repaired(wall_id: String, _amount: int, new_hp: int) -> void:
	update_wall_hp(wall_id, new_hp)

func _on_board_wall_breached(wall_id: String) -> void:
	set_wall_breached(wall_id, true)

func _on_eventbus_wall_breached(wall_id: String) -> void:
	set_wall_breached(wall_id, true)

func _on_board_item_changed(_pos: Vector2i, _data: Dictionary) -> void:
	queue_redraw()

func _on_board_item_collected_signal(_unit_id: String, _pos: Vector2i, _data: Dictionary) -> void:
	queue_redraw()

func _on_board_item_removed_signal(_pos: Vector2i) -> void:
	queue_redraw()

func _on_board_unit_moved_signal(_unit_id: String, _from: Vector2i, _to: Vector2i, _fz: String, _tz: String) -> void:
	if _unit_id == selected_unit_id:
		select_unit(selected_unit_id)
	queue_redraw()

func _on_board_unit_stats_changed(_unit_id: String, _data: Dictionary) -> void:
	queue_redraw()

# ── FFT Tactical Unit Control Methods ─────────────────────────────────────────
func select_unit(unit_id: String) -> void:
	if _bound_board == null or not _bound_board.has_method("get_unit_data"):
		return
	var u_data: Dictionary = _bound_board.get_unit_data(unit_id)
	if u_data.is_empty():
		return
	selected_unit_id = unit_id
	var pos: Vector2i = _bound_board.get_unit_position(unit_id)
	var move_range: int = int(u_data.get("move_range", 3))
	var atk_range: int = int(u_data.get("attack_range", 1))
	var team: String = str(u_data.get("team", "A"))

	if _bound_board.has_method("get_reachable_cells"):
		reachable_cells = _bound_board.get_reachable_cells(pos, move_range)
	else:
		reachable_cells.clear()

	if _bound_board.has_method("get_attackable_cells"):
		attackable_cells = _bound_board.get_attackable_cells(pos, atk_range, team)
	else:
		attackable_cells.clear()

	unit_selected.emit(unit_id, u_data)
	queue_redraw()

func deselect_unit() -> void:
	if not selected_unit_id.is_empty():
		var old: String = selected_unit_id
		selected_unit_id = ""
		reachable_cells.clear()
		attackable_cells.clear()
		unit_deselected.emit(old)
		queue_redraw()

func get_selected_unit() -> String:
	return selected_unit_id

func get_reachable_cells() -> Array[Vector2i]:
	return reachable_cells

func get_attackable_cells() -> Array[Vector2i]:
	return attackable_cells

func move_selected_unit_to(dest_pos: Vector2i) -> bool:
	if selected_unit_id.is_empty() or _bound_board == null:
		return false
	if not _bound_board.has_method("move_unit"):
		return false
	var ok: bool = _bound_board.move_unit(selected_unit_id, dest_pos)
	if ok:
		unit_moved_to_cell.emit(selected_unit_id, dest_pos)
		if _bound_board.has_method("has_item_at") and _bound_board.has_item_at(dest_pos):
			var item: Dictionary = _bound_board.collect_item(selected_unit_id, dest_pos)
			item_pickup_requested.emit(selected_unit_id, dest_pos, item)
		select_unit(selected_unit_id)
		queue_redraw()
	return ok

# ── Dynamic Combat VFX & Animation Methods ───────────────────────────────────

## Anima o deslocamento suave de uma unidade de uma célula para outra com arco de salto (bob)
func animate_unit_move(unit_id: String, from_cell: Vector2i, to_cell: Vector2i, duration: float = 0.25) -> Tween:
	var start_coords: Vector2 = get_cell_screen_coords(from_cell.x, from_cell.y)
	var end_coords: Vector2 = get_cell_screen_coords(to_cell.x, to_cell.y)
	_unit_visual_positions[unit_id] = start_coords

	var tween: Tween = create_tween()
	if tween == null:
		# Fallback headless ou sem SceneTree ativo
		_unit_visual_positions.erase(unit_id)
		queue_redraw()
		return null

	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_OUT)

	var step_callback: Callable = func(val: float) -> void:
		# Interpolação linear da posição horizontal isométrica
		var current_xy: Vector2 = start_coords.lerp(end_coords, val)
		# Curva seno vertical simulando passos/salto tático sobre o relevo
		var jump_offset: float = -sin(val * PI) * (8.0 * cam_zoom)
		current_xy.y += jump_offset
		_unit_visual_positions[unit_id] = current_xy
		queue_redraw()

	tween.tween_method(step_callback, 0.0, 1.0, maxf(0.01, duration))
	tween.tween_callback(func() -> void:
		_unit_visual_positions.erase(unit_id)
		queue_redraw()
	)
	return tween

## Executa um avanço físico rápido (lunge) em direção ao alvo e recuo
func animate_melee_attack(attacker_id: String, target_cell: Vector2i, duration: float = 0.28) -> Tween:
	var atk_pos: Vector2i = _bound_board.get_unit_position(attacker_id) if _bound_board != null and _bound_board.has_method("get_unit_position") else Vector2i(-1, -1)
	var atk_coords: Vector2 = get_cell_screen_coords(atk_pos.x, atk_pos.y) if atk_pos != Vector2i(-1, -1) else Vector2.ZERO
	var tgt_coords: Vector2 = get_cell_screen_coords(target_cell.x, target_cell.y)
	var dir_delta: Vector2 = (tgt_coords - atk_coords) * 0.45

	_unit_anim_offsets[attacker_id] = Vector2.ZERO

	var tween: Tween = create_tween()
	if tween == null:
		_unit_anim_offsets.erase(attacker_id)
		queue_redraw()
		return null

	var lunge_time: float = duration * 0.40
	var return_time: float = duration * 0.60

	tween.tween_method(func(val: float) -> void:
		_unit_anim_offsets[attacker_id] = dir_delta * val
		queue_redraw()
	, 0.0, 1.0, maxf(0.01, lunge_time)).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	tween.tween_method(func(val: float) -> void:
		_unit_anim_offsets[attacker_id] = dir_delta * (1.0 - val)
		queue_redraw()
	, 0.0, 1.0, maxf(0.01, return_time)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)

	tween.tween_callback(func() -> void:
		_unit_anim_offsets.erase(attacker_id)
		queue_redraw()
	)
	return tween

## Dispara um projétil com trajetória balística (flecha/balista) ou raio direto (ácido/magia)
func launch_projectile(from_cell: Vector2i, to_cell: Vector2i, proj_type: String = "arrow", color: Color = Color(1.0, 0.85, 0.2), duration: float = 0.35) -> void:
	var start_pos: Vector2 = get_cell_screen_coords(from_cell.x, from_cell.y)
	var end_pos: Vector2 = get_cell_screen_coords(to_cell.x, to_cell.y)
	var dist: float = start_pos.distance_to(end_pos)
	var arc: float = 24.0 if proj_type != "beam" else 0.0

	_active_projectiles.append({
		"start_pos": start_pos,
		"end_pos": end_pos,
		"progress": 0.0,
		"duration": maxf(0.05, duration),
		"arc_height": arc,
		"type": proj_type,
		"color": color
	})
	queue_redraw()

## Dispara um flash de cor na unidade atingida (ex: dano vermelho carmesim)
func trigger_unit_damage_flash(unit_id: String, flash_color: Color = Color(1.0, 0.15, 0.15, 0.85), duration: float = 0.22) -> void:
	_unit_anim_flashes[unit_id] = {
		"timer": duration,
		"duration": duration,
		"color": flash_color
	}
	queue_redraw()

## Cria um número flutuante de dano, crítico ou defesa sobre a célula indicada
func spawn_floating_combat_text(text: String, cell: Vector2i, color: Color = Color.WHITE, is_crit: bool = false) -> void:
	var base_pos: Vector2 = get_cell_screen_coords(cell.x, cell.y) + Vector2(0.0, -18.0)
	# Dispersão horizontal aleatória leve para múltiplos acertos
	base_pos.x += randf_range(-6.0, 6.0)
	_floating_combat_texts.append({
		"text": text,
		"pos": base_pos,
		"color": color,
		"timer": 0.0,
		"duration": 0.95,
		"velocity": Vector2(0.0, -28.0),
		"is_crit": is_crit
	})
	queue_redraw()

# ── Click Handler (câmera-aware) ─────────────────────────────────────────────
## Processa clique do LMB em coordenadas world (já transformadas pela câmera).
## Prioridade: 1. Unidade → seleciona/move; 2. Célula alcançável → move; 3. Zona → emite sinal.
func _handle_left_click(world_pos: Vector2) -> void:
	var grid_pos: Vector2i = iso_screen_to_grid(world_pos)
	if grid_pos == Vector2i(-1, -1):
		deselect_unit()
		return

	# 1. Checa se há uma unidade na célula clicada
	if _bound_board != null and _bound_board.has_method("get_unit_at"):
		var uid_at: String = str(_bound_board.get_unit_at(grid_pos))
		if not uid_at.is_empty() and uid_at != "" and uid_at != "null":
			if uid_at == selected_unit_id:
				# Clique duplo na mesma unidade: cancela seleção
				deselect_unit()
			else:
				# Unidade inimiga selecionada + clique em inimigo → ataque
				if not selected_unit_id.is_empty() and grid_pos in attackable_cells:
					unit_attack_requested.emit(selected_unit_id, uid_at)
				else:
					select_unit(uid_at)
			return

	# 2. Se há unidade selecionada e célula alcançável → move
	if not selected_unit_id.is_empty() and grid_pos in reachable_cells:
		move_selected_unit_to(grid_pos)
		return

	# 3. Cancela seleção e emite sinal de zona clicada
	deselect_unit()
	var zone: String = get_zone_at(grid_pos)
	if not zone.is_empty():
		select_zone(zone)

# ── Rendering ────────────────────────────────────────────────────────────────
func _draw() -> void:

	_update_cell_size()
	
	if size.x <= 0 or size.y <= 0:
		return
	
	var r_width: float = size.x
	var r_height: float = size.y
	
	# Fundo do céu noturno escuro com estrelas sutis
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.035, 0.04, 0.08), true)
	
	# Estrelas distantes no quadrante superior
	for i in range(30):
		var star_x: float = fposmod(float(i * 97 + 13), r_width - 20.0) + 10.0
		var star_y: float = fposmod(float(i * 53 + 7), r_height * 0.45) + 8.0
		var star_alpha: float = 0.4 + 0.5 * sin(float(i) * 1.7)
		draw_circle(Vector2(star_x, star_y), 1.0, Color(0.7, 0.75, 0.9, star_alpha))
	
	# Névoa atmosférica de chão
	draw_circle(Vector2(r_width * 0.5, r_height * 0.88), r_width * 0.45, Color(0.08, 0.10, 0.18, 0.12))

	# ── Aplica Transform da Câmera FFT (Com Screen Shake Direcional Tático) ───
	# Todo o conteúdo do tabuleiro abaixo será deslocado e escalado conforme cam_pan, shake_offset e cam_zoom.
	# O fundo e a borda ficam fora do transform (fixos na tela).
	draw_set_transform(cam_pan + shake_offset, 0.0, Vector2(cam_zoom, cam_zoom))
	
	# Parâmetros de Projeção Isométrica Canônica

	var zoom: float = clampf(r_width / 680.0, 0.75, 1.25)
	var tw: float = 24.0 * zoom
	var th: float = 12.0 * zoom
	var es: float = 8.0 * zoom
	var cx: float = r_width * 0.5
	var cy: float = r_height * 0.48
	
	# Definição de zonas e elevações para a grade estendida (-2 até 21)
	var RENDER_MIN: int = -2
	var RENDER_MAX: int = 21
	
	# Coleta itens e unidades antecipadamente para intercalar no Y-Sort por célula
	var items_by_cell: Dictionary = {}
	if _bound_board != null and _bound_board.has_method("get_all_items"):
		var raw_items: Dictionary = _bound_board.get_all_items()
		for ip in raw_items.keys():
			items_by_cell[ip] = raw_items[ip]
	
	var units_by_cell: Dictionary = {}
	if _bound_board != null and _bound_board.has_method("get_all_units"):
		for uid in _bound_board.get_all_units():
			var upos: Vector2i = _bound_board.get_unit_position(uid)
			if upos != Vector2i(-1, -1):
				if not units_by_cell.has(upos):
					units_by_cell[upos] = []
				units_by_cell[upos].append(uid)

	# Foco de oclusão inteligente estilo FFT (unidade selecionada ou hover)
	var focus_cell: Vector2i = Vector2i(-1, -1)
	if not selected_unit_id.is_empty() and _bound_board != null and _bound_board.has_method("get_unit_position"):
		focus_cell = _bound_board.get_unit_position(selected_unit_id)
	elif hovered_cell != Vector2i(-1, -1):
		focus_cell = hovered_cell

	var focus_rot_depth: float = -9999.0
	var focus_rot_x: float = 0.0
	if focus_cell != Vector2i(-1, -1):
		var f_rot: Vector2 = get_rotated_dx_dy(float(focus_cell.x) - 9.5, float(focus_cell.y) - 9.5)
		focus_rot_depth = f_rot.x + f_rot.y
		focus_rot_x = f_rot.x - f_rot.y

	var cells_to_draw: Array[Dictionary] = []
	
	for gy in range(RENDER_MIN, RENDER_MAX + 1):
		for gx in range(RENDER_MIN, RENDER_MAX + 1):
			var el: int = 0
			var zone_k: String = "_exterior"
			
			if gx >= 0 and gx < GRID_SIZE and gy >= 0 and gy < GRID_SIZE:
				var z_id: String = get_zone_at(Vector2i(gx, gy))
				zone_k = z_id
				
				# Elevações canônicas de Kuar-Tor
				if z_id.find("TORRE") != -1:
					el = 6
				elif z_id.find("MURALHA") != -1:
					el = 4
				elif z_id == "CAMARA_CENTRAL":
					el = 3
				elif z_id in ["CARPINTARIA", "CURTUME", "FUNDICAO", "PATIO_CENTRAL"]:
					el = 2
				elif gx >= 4 and gx <= 15 and gy >= 4 and gy <= 15:
					el = 1
					zone_k = "_corredor"
				else:
					el = 0
					zone_k = "_patio_baixo"
			elif gx >= -1 and gx <= 20 and gy >= -1 and gy <= 20:
				el = 0
				zone_k = "_campo"
			else:
				el = 0
				zone_k = "_exterior"
			
			var base_dx: float = float(gx) - 9.5
			var base_dy: float = float(gy) - 9.5
			var rot_d: Vector2 = get_rotated_dx_dy(base_dx, base_dy)
			var dx: float = rot_d.x
			var dy: float = rot_d.y
			var ground_depth: float = dx + dy
			
			cells_to_draw.append({
				"gx": gx,
				"gy": gy,
				"el": el,
				"zone": zone_k,
				"depth": ground_depth,
				"dx": dx,
				"dy": dy
			})
	
	# Ordena pelo depth rotacionado de trás para frente (Y-Sort canônico isométrico)
	cells_to_draw.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a["depth"] < b["depth"]
	)
	
	# Cores base por zona
	var color_map: Dictionary = {
		"CAMARA_CENTRAL": Color(0.41, 0.32, 0.07),
		"CARPINTARIA": Color(0.12, 0.35, 0.11),
		"CURTUME": Color(0.47, 0.28, 0.11),
		"FUNDICAO": Color(0.27, 0.27, 0.35),
		"PATIO_CENTRAL": Color(0.11, 0.24, 0.47),
		"TORRE_NOROESTE": Color(0.27, 0.28, 0.36),
		"TORRE_NORDESTE": Color(0.27, 0.28, 0.36),
		"TORRE_SUDOESTE": Color(0.27, 0.28, 0.36),
		"TORRE_SUDESTE": Color(0.27, 0.28, 0.36),
		"MURALHA_NORTE": Color(0.35, 0.36, 0.42),
		"MURALHA_SUL": Color(0.35, 0.36, 0.42),
		"MURALHA_LESTE": Color(0.35, 0.36, 0.42),
		"MURALHA_OESTE": Color(0.35, 0.36, 0.42),
		"_corredor": Color(0.14, 0.13, 0.11),
		"_patio_baixo": Color(0.12, 0.15, 0.20),
		"_campo": Color(0.12, 0.20, 0.09),
		"_exterior": Color(0.07, 0.11, 0.05)
	}
	
	var has_units_drawn: bool = false
	
	# ── 1. Névoa Rastejante & Miasma no Perímetro ─────────────────────────────
	_draw_creeping_miasma(cx, cy, tw, th, zoom)

	# ── 2. Sombras Projetadas das Muralhas e Torres no Chão do Pátio ─────────
	_draw_projected_shadows(cells_to_draw, tw, th, cx, cy, zoom)

	# Renderiza cada célula e intercala chão -> itens/movimento -> faces elevadas -> unidades
	for c in cells_to_draw:
		var gx: int = c["gx"]
		var gy: int = c["gy"]
		var el: int = c["el"]
		var zk: String = c["zone"]
		var dx: float = c["dx"]
		var dy: float = c["dy"]
		var cell_vec: Vector2i = Vector2i(gx, gy)
		
		var sx: float = (dx - dy) * (tw * 0.5) + cx
		var sy: float = (dx + dy) * (th * 0.5) - float(el) * es + cy
		
		# Vértices do topo (losango isométrico)
		var p0: Vector2 = Vector2(sx, sy - th * 0.5)
		var p1: Vector2 = Vector2(sx + tw * 0.5, sy)
		var p2: Vector2 = Vector2(sx, sy + th * 0.5)
		var p3: Vector2 = Vector2(sx - tw * 0.5, sy)
		
		var base_col: Color = color_map.get(zk, Color(0.15, 0.15, 0.18))
		
		# Coordenadas UV normalizadas e divididas em 4 quadrantes para variação natural
		var u_min: float = float(posmod(gx, 4)) * 0.25
		var v_min: float = float(posmod(gy, 4)) * 0.25
		var u_max: float = u_min + 0.25
		var v_max: float = v_min + 0.25
		var u_mid: float = (u_min + u_max) * 0.5
		var v_mid: float = (v_min + v_max) * 0.5

		# Textura específica para a zona atual
		var top_tex: Texture2D = get_zone_texture(zk)

		# Oclusão inteligente estilo Final Fantasy Tactics:
		# Se a muralha/torre estiver na frente do foco (depth maior) e alinhada na coluna visual,
		# aplica transparência (X-Ray / Fade suave) para permitir ver o herói e os itens atrás da muralha!
		var wall_alpha: float = 1.0
		if el >= 4 and focus_rot_depth > -9000.0:
			var c_depth: float = dx + dy
			var c_rot_x: float = dx - dy
			if c_depth > focus_rot_depth and c_depth <= focus_rot_depth + 6.0 and absf(c_rot_x - focus_rot_x) <= 3.5:
				wall_alpha = 0.38

		# Faces laterais 3D quando há elevação
		if el > 0:
			var sy_bot: float = (dx + dy) * (th * 0.5) + cy
			var p2_bot: Vector2 = Vector2(sx, sy_bot + th * 0.5)
			var p3_bot: Vector2 = Vector2(sx - tw * 0.5, sy_bot)
			var p1_bot: Vector2 = Vector2(sx + tw * 0.5, sy_bot)
			
			var wall_tex: Texture2D = _load_terrain_texture("parede", "res://assets/images/environment/terreno_parede.png")
			var v_h: float = clampf(float(el) * 0.20, 0.15, 1.0)
			
			# Face esquerda (em sombra mais escura - lado sudoeste)
			var pts_left: PackedVector2Array = PackedVector2Array([p3, p2, p2_bot, p3_bot])
			if wall_tex != null:
				var uvs_l: PackedVector2Array = PackedVector2Array([
					Vector2(u_min, 0.0), Vector2(u_max, 0.0),
					Vector2(u_max, v_h), Vector2(u_min, v_h)
				])
				draw_colored_polygon(pts_left, Color(0.55, 0.55, 0.60, wall_alpha), uvs_l, wall_tex)
			else:
				var c_left: Color = base_col.darkened(0.45)
				c_left.a = wall_alpha
				draw_colored_polygon(pts_left, c_left)
			
			# Face direita (sombra intermediária / meia luz - lado sudeste)
			var pts_right: PackedVector2Array = PackedVector2Array([p2, p1, p1_bot, p2_bot])
			if wall_tex != null:
				var uvs_r: PackedVector2Array = PackedVector2Array([
					Vector2(u_min, 0.0), Vector2(u_max, 0.0),
					Vector2(u_max, v_h), Vector2(u_min, v_h)
				])
				draw_colored_polygon(pts_right, Color(0.75, 0.75, 0.80, wall_alpha), uvs_r, wall_tex)
			else:
				var c_right: Color = base_col.darkened(0.3)
				c_right.a = wall_alpha
				draw_colored_polygon(pts_right, c_right)
			
			# Linhas de alvenaria e profundidade 3D
			draw_line(p2, p2_bot, Color(0.06, 0.06, 0.10, 0.9 * wall_alpha), 1.5)
			draw_line(p3, p2, Color(1.0, 1.0, 1.0, 0.15 * wall_alpha), 1.0)
			draw_line(p2, p1, Color(1.0, 1.0, 1.0, 0.12 * wall_alpha), 1.0)
			
			# Fissuras e rachaduras dinâmicas nas muralhas (100% -> 50% -> Brecha)
			_draw_wall_fissures(pts_left, pts_right, zk, wall_alpha, zoom)
		
		# Face superior texturizada (losango isométrico)
		var pts_top: PackedVector2Array = PackedVector2Array([p0, p1, p2, p3])
		if top_tex != null:
			var uvs_top: PackedVector2Array = PackedVector2Array([
				Vector2(u_mid, v_min),
				Vector2(u_max, v_mid),
				Vector2(u_mid, v_max),
				Vector2(u_min, v_mid)
			])
			# Modular com tom da zona para harmonização rica de cores
			var mod_col: Color = Color.WHITE
			if zk.find("MURALHA") != -1 or zk.find("TORRE") != -1:
				mod_col = Color(0.92, 0.92, 0.96)
			elif zk == "CARPINTARIA":
				mod_col = Color(0.95, 0.90, 0.82)
			elif zk == "CURTUME":
				mod_col = Color(0.92, 0.85, 0.75)
			elif zk == "FUNDICAO":
				mod_col = Color(0.88, 0.85, 0.90)
			elif zk == "CAMARA_CENTRAL":
				mod_col = Color(1.0, 0.96, 0.88)
			elif zk == "PATIO_CENTRAL" or zk == "_patio_baixo" or zk == "_corredor":
				mod_col = Color(0.85, 0.90, 0.98)
			elif zk == "_campo" or zk == "_exterior" or zk.find("SPAWN") != -1:
				mod_col = Color(0.90, 0.98, 0.88)
			
			mod_col.a = wall_alpha
			draw_colored_polygon(pts_top, mod_col, uvs_top, top_tex)
		else:
			var top_c: Color = base_col
			top_c.a = wall_alpha
			draw_colored_polygon(pts_top, top_c)
		
		# Chanfro e iluminação das arestas superiores do tile
		draw_polyline(PackedVector2Array([p3, p0, p1]), Color(1.0, 1.0, 1.0, 0.20 * wall_alpha), 1.0)
		draw_polyline(PackedVector2Array([p1, p2, p3]), Color(0.0, 0.0, 0.0, 0.28 * wall_alpha), 1.0)

		# Contornos temáticos das Oficinas e Pátio
		var outline_col: Color = Color(0.08, 0.09, 0.14, 0.5)
		var outline_w: float = 1.0
		
		if zk == "CARPINTARIA":
			outline_col = Color(0.25, 0.85, 0.25, 0.8)
			outline_w = 1.5
		elif zk == "CURTUME":
			outline_col = Color(0.9, 0.55, 0.2, 0.8)
			outline_w = 1.5
		elif zk == "FUNDICAO":
			outline_col = Color(0.45, 0.7, 0.95, 0.8)
			outline_w = 1.5
		elif zk == "PATIO_CENTRAL":
			outline_col = Color(0.3, 0.65, 1.0, 0.8)
			outline_w = 1.5
		elif zk == "CAMARA_CENTRAL":
			outline_col = Color(1.0, 0.8, 0.2, 0.9)
			outline_w = 2.0
		
		outline_col.a *= wall_alpha
		draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), outline_col, outline_w)
		
		# Entalhes orgânicos de pedra na lajota
		if gx >= 8 and gx <= 11 and gy >= 8 and gy <= 11:
			draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), Color(1.0, 0.7, 0.15, 0.35 * wall_alpha), 1.0)

		# ── FFT Reachable Movement Range (Tile Azul desenhado no topo da célula) ─
		if cell_vec in reachable_cells:
			var rp_pts: PackedVector2Array = PackedVector2Array([p0, p1, p2, p3])
			var p_alpha: float = (0.35 + 0.15 * sin(_anim_timer * 4.0)) * wall_alpha
			draw_colored_polygon(rp_pts, Color(0.15, 0.55, 1.0, p_alpha))
			draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), Color(0.40, 0.85, 1.0, 0.9 * wall_alpha), 1.5)
			draw_circle(Vector2(sx, sy), 2.5 * zoom, Color(0.7, 0.9, 1.0, 0.8 * wall_alpha))

		# ── FFT Attackable Enemy Range (Tile Vermelho desenhado no topo da célula) ─
		if cell_vec in attackable_cells:
			var ap_pts: PackedVector2Array = PackedVector2Array([p0, p1, p2, p3])
			var r_alpha: float = (0.40 + 0.20 * sin(_anim_timer * 6.0)) * wall_alpha
			draw_colored_polygon(ap_pts, Color(0.95, 0.15, 0.15, r_alpha))
			draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), Color(1.0, 0.35, 0.35, 0.95 * wall_alpha), 2.0)
			draw_line(Vector2(sx - 5.0 * zoom, sy), Vector2(sx + 5.0 * zoom, sy), Color(1.0, 0.95, 0.95, wall_alpha), 1.5)
			draw_line(Vector2(sx, sy - 5.0 * zoom), Vector2(sx, sy + 5.0 * zoom), Color(1.0, 0.95, 0.95, wall_alpha), 1.5)

		# ── Hovered Cell Diamond Highlight ──────────────────────────────────────
		if cell_vec == hovered_cell and is_valid_cell(hovered_cell):
			draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), Color(1.0, 0.95, 0.4, 0.85 * wall_alpha), 1.5)

		# ── Item no chão desta célula (Unified Y-Sorting) ──────────────────────
		if items_by_cell.has(cell_vec):
			var it_data: Dictionary = items_by_cell[cell_vec]
			_draw_board_item(it_data, Vector2(sx, sy), zoom)

		# ── Unidades no chão desta célula (Unified Y-Sorting) ──────────────────
		if units_by_cell.has(cell_vec):
			var u_ids_here: Array = units_by_cell[cell_vec]
			for uid in u_ids_here:
				var udata: Dictionary = _bound_board.get_unit_data(uid)
				var anim_offset: Vector2 = _unit_anim_offsets.get(uid, Vector2.ZERO)
				var ucoords: Vector2 = Vector2(sx, sy) + anim_offset
				var is_sel: bool = (uid == selected_unit_id)
				_draw_unit_entity(uid, udata, ucoords, zoom, is_sel)
				has_units_drawn = true
		
		# Árvores de Pinheiro perimetrais nas margens
		if (zk == "_campo" or zk == "_exterior") and ((gx * 37 + gy * 79) % 10 < 3):
			_draw_pine_tree(Vector2(sx, sy), zoom)
	
	# ── Trono Norte do Comandante Pr. Lysander ──────────────────────────────
	_draw_commander_throne(cx, cy - 130.0 * zoom, zoom)

	if not has_units_drawn:
		# Herói Posicionado no Centro do Pátio (Fallback)
		var center_coords: Vector2 = get_cell_screen_coords(10, 10)
		_draw_hero_on_board(center_coords.x, center_coords.y, zoom)

	# ── Tochas Vivas nas 4 Torres e Portão Norte (Luz Âmbar & Brasas) ────────
	_draw_torches_and_lights(cx, cy, tw, th, es, zoom)

	# ── Linha Parabólica de Trajetória e Mira com % de Acerto ────────────────
	_draw_targeting_trajectory(cx, cy, tw, th, es, zoom)

	# ── Partículas de Combate Procedurais (Lascas, Ácido, Faíscas, Poeira) ──
	_draw_combat_particles(zoom)

	# ── Projéteis Ativos em Voo (Flechas, Balistas, Magias) ────────────────
	_draw_active_projectiles(zoom)

	# ── Números Flutuantes de Dano / Crítico / Defesa (Combat Text) ────────
	_draw_floating_combat_texts(zoom)

	# ── Reseta Transform — elementos de UI abaixo ficam na tela, não no mundo ──
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# Borda decorativa do tabuleiro (fixo na tela)
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.18, 0.20, 0.32, 0.8), false, 1.5)

	# ── Card Flutuante de Informação Tática Rápida (Tooltip estilo FFT) ──────
	_draw_tactical_tooltip(r_width, r_height)

	# ── FFT Tactical Camera HUD (Controles no estilo Final Fantasy Tactics) ─
	var font: Font = ThemeDB.fallback_font
	var angles_str: Array[String] = ["0° (NW)", "90° (NE)", "180° (SE)", "270° (SW)"]
	var cur_angle_txt: String = angles_str[posmod(camera_angle_idx, 4)]
	
	# Indicador de Ângulo e Zoom no canto inferior esquerdo
	var cam_hud_txt: String = "CÂMERA FFT: %s  |  Zoom: x%.1f  |  [Q ↺] [E ↻]  [WASD]=Pan  [R]=Reset" % [cur_angle_txt, cam_zoom]
	draw_string(font, Vector2(16.0, r_height - 12.0), cam_hud_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.75, 0.85, 1.0, 0.85))

	# Botões Táteis no topo direito para rotação de câmera
	var btn_y: float = 12.0
	var btn_w: float = 52.0
	var btn_h: float = 24.0
	var q_btn_rect: Rect2 = Rect2(r_width - 120.0, btn_y, btn_w, btn_h)
	var e_btn_rect: Rect2 = Rect2(r_width - 60.0, btn_y, btn_w, btn_h)

	draw_rect(q_btn_rect, Color(0.08, 0.12, 0.22, 0.85), true)
	draw_rect(q_btn_rect, Color(0.35, 0.60, 0.90, 0.8), false, 1.0)
	draw_string(font, Vector2(q_btn_rect.position.x + 8.0, q_btn_rect.position.y + 16.0), "Q ↺", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.9, 0.95, 1.0))

	draw_rect(e_btn_rect, Color(0.08, 0.12, 0.22, 0.85), true)
	draw_rect(e_btn_rect, Color(0.35, 0.60, 0.90, 0.8), false, 1.0)
	draw_string(font, Vector2(e_btn_rect.position.x + 8.0, e_btn_rect.position.y + 16.0), "E ↻", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.9, 0.95, 1.0))

func _draw_board_item(item: Dictionary, pos: Vector2, zoom: float) -> void:
	var bob: float = sin(_anim_timer * 3.0 + float(pos.x + pos.y)) * 2.5 * zoom
	var ipos: Vector2 = pos + Vector2(0.0, -4.0 * zoom + bob)
	var itype: String = str(item.get("type", "CRISTAL")).to_upper()

	match itype:
		"CRISTAL":
			# Sombra do cristal
			draw_circle(pos + Vector2(0, 2.0 * zoom), 6.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))
			# Aura mágica pulsante
			var glow_r: float = (8.0 + 2.0 * sin(_anim_timer * 4.0)) * zoom
			draw_circle(ipos, glow_r, Color(0.75, 0.3, 1.0, 0.3))
			# Losango facetado do cristal de mana
			var top_pt: Vector2 = ipos + Vector2(0, -9.0 * zoom)
			var mid_l: Vector2 = ipos + Vector2(-6.0 * zoom, -2.0 * zoom)
			var mid_r: Vector2 = ipos + Vector2(6.0 * zoom, -2.0 * zoom)
			var bot_pt: Vector2 = ipos + Vector2(0, 6.0 * zoom)
			# Faceta superior
			draw_colored_polygon(PackedVector2Array([top_pt, mid_r, ipos, mid_l]), Color(0.85, 0.50, 1.0))
			# Faceta inferior esquerda
			draw_colored_polygon(PackedVector2Array([mid_l, ipos, bot_pt]), Color(0.65, 0.25, 0.90))
			# Faceta inferior direita
			draw_colored_polygon(PackedVector2Array([ipos, mid_r, bot_pt]), Color(0.45, 0.12, 0.75))
			# Contorno fino do cristal
			draw_polyline(PackedVector2Array([top_pt, mid_r, bot_pt, mid_l, top_pt]), Color(1.0, 0.85, 1.0, 0.9), 1.0)
			# Ponto de brilho / reflexo
			draw_circle(ipos + Vector2(-2.0 * zoom, -4.0 * zoom), 1.5 * zoom, Color(1.0, 1.0, 1.0, 0.9))

		"CHEST", "BAU":
			var chest_path: String = "res://assets/images/material/bau_ouro.png"
			if not _unit_texture_cache.has("item_chest"):
				_unit_texture_cache["item_chest"] = load(chest_path) if (ResourceLoader.exists(chest_path) or FileAccess.file_exists(chest_path)) else null
			var c_tex: Texture2D = _unit_texture_cache.get("item_chest", null)
			
			# Sombra do baú no chão
			draw_circle(pos + Vector2(0, 3.0 * zoom), 9.0 * zoom, Color(0.0, 0.0, 0.0, 0.45))
			
			# Brilho dourado cintilante sutil
			var sparkle: float = sin(_anim_timer * 4.5 + float(pos.x)) * 0.5 + 0.5
			draw_circle(ipos + Vector2(0, 1.0 * zoom), (10.0 + 2.0 * sparkle) * zoom, Color(1.0, 0.85, 0.2, 0.18))
			
			if c_tex != null:
				var c_size: float = 22.0 * zoom
				var c_rect: Rect2 = Rect2(ipos.x - c_size * 0.5, ipos.y - c_size * 0.65, c_size, c_size)
				draw_texture_rect(c_tex, c_rect, false)
			else:
				# Fallback isométrico 3D detalhado do Baú
				var bw: float = 16.0 * zoom
				var bh: float = 11.0 * zoom
				# Caixa base
				draw_rect(Rect2(ipos.x - bw * 0.5, ipos.y - bh * 0.5, bw, bh), Color(0.42, 0.24, 0.12))
				# Tampa arqueada
				draw_colored_polygon(PackedVector2Array([
					Vector2(ipos.x - bw * 0.5, ipos.y - bh * 0.5),
					Vector2(ipos.x, ipos.y - bh * 0.5 - 3.5 * zoom),
					Vector2(ipos.x + bw * 0.5, ipos.y - bh * 0.5)
				]), Color(0.55, 0.32, 0.15))
				# Fitas de reforço douradas
				draw_rect(Rect2(ipos.x - bw * 0.5, ipos.y - bh * 0.5, bw, bh), Color(0.95, 0.80, 0.25), false, 1.5)
				draw_line(Vector2(ipos.x - bw * 0.25, ipos.y - bh * 0.5), Vector2(ipos.x - bw * 0.25, ipos.y + bh * 0.5), Color(0.95, 0.80, 0.25), 1.2)
				draw_line(Vector2(ipos.x + bw * 0.25, ipos.y - bh * 0.5), Vector2(ipos.x + bw * 0.25, ipos.y + bh * 0.5), Color(0.95, 0.80, 0.25), 1.2)
				# Fechadura dourada com orifício
				draw_circle(ipos + Vector2(0, 0.5 * zoom), 2.2 * zoom, Color(1.0, 0.88, 0.25))
				draw_circle(ipos + Vector2(0, 0.5 * zoom), 0.8 * zoom, Color(0.15, 0.1, 0.05))

		"OURO", "GOLD", "COINS", "MOEDAS":
			var gold_path: String = "res://assets/images/material/moedas_ouro.png"
			if not _unit_texture_cache.has("item_gold"):
				_unit_texture_cache["item_gold"] = load(gold_path) if (ResourceLoader.exists(gold_path) or FileAccess.file_exists(gold_path)) else null
			var g_tex: Texture2D = _unit_texture_cache.get("item_gold", null)
			
			draw_circle(pos + Vector2(0, 2.0 * zoom), 8.0 * zoom, Color(0.0, 0.0, 0.0, 0.40))
			var sparkle_g: float = sin(_anim_timer * 5.0 + float(pos.y)) * 0.5 + 0.5
			draw_circle(ipos, (9.0 + 2.5 * sparkle_g) * zoom, Color(1.0, 0.88, 0.2, 0.22))
			
			if g_tex != null:
				var g_size: float = 20.0 * zoom
				var g_rect: Rect2 = Rect2(ipos.x - g_size * 0.5, ipos.y - g_size * 0.6, g_size, g_size)
				draw_texture_rect(g_tex, g_rect, false)
			else:
				# Pilha de moedas douradas (Fallback)
				for i in range(3):
					var cx_i: float = ipos.x + float(i - 1) * 3.5 * zoom
					var cy_i: float = ipos.y + float(1 - i % 2) * 2.0 * zoom
					draw_circle(Vector2(cx_i, cy_i), 3.5 * zoom, Color(0.95, 0.78, 0.18))
					draw_circle(Vector2(cx_i, cy_i), 3.5 * zoom, Color(1.0, 0.92, 0.4), false, 1.0)


		"POTION":
			# Sombra do frasco
			draw_circle(pos + Vector2(0, 2.0 * zoom), 5.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))
			# Corpo da poção (esfera verde esmeralda ou carmesim)
			draw_circle(ipos, 5.0 * zoom, Color(0.2, 0.9, 0.4, 0.85))
			draw_circle(ipos, 5.0 * zoom, Color(0.6, 1.0, 0.7, 0.95), false, 1.0)
			# Gargalo e rolha de cortiça
			draw_rect(Rect2(ipos.x - 2.0 * zoom, ipos.y - 8.0 * zoom, 4.0 * zoom, 3.5 * zoom), Color(0.55, 0.35, 0.15))
			# Brilho interno
			draw_circle(ipos + Vector2(-1.5 * zoom, -1.5 * zoom), 1.2 * zoom, Color(1.0, 1.0, 1.0, 0.8))

		"METAL":
			var metal_path: String = "res://assets/images/material/stone/Rock Pile - BEIGE -/Rock Pile 1 - BEIGE - small.PNG"
			if not _unit_texture_cache.has("item_metal"):
				_unit_texture_cache["item_metal"] = load(metal_path) if (ResourceLoader.exists(metal_path) or FileAccess.file_exists(metal_path)) else null
			var m_tex: Texture2D = _unit_texture_cache.get("item_metal", null)
			if m_tex != null:
				draw_circle(pos + Vector2(0, 3.0 * zoom), 8.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))
				draw_texture_rect(m_tex, Rect2(ipos.x - 9.0 * zoom, ipos.y - 9.0 * zoom, 18.0 * zoom, 18.0 * zoom), false)
			else:
				# Lingotes de Metal (Fallback)
				draw_rect(Rect2(ipos.x - 7.0 * zoom, ipos.y - 3.0 * zoom, 14.0 * zoom, 5.0 * zoom), Color(0.6, 0.65, 0.75))
				draw_rect(Rect2(ipos.x - 7.0 * zoom, ipos.y - 3.0 * zoom, 14.0 * zoom, 5.0 * zoom), Color(0.9, 0.95, 1.0), false, 1.0)

		"WOOD":
			var wood_path: String = "res://assets/images/material/wood/wood_1.png"
			if not _unit_texture_cache.has("item_wood"):
				_unit_texture_cache["item_wood"] = load(wood_path) if (ResourceLoader.exists(wood_path) or FileAccess.file_exists(wood_path)) else null
			var w_tex: Texture2D = _unit_texture_cache.get("item_wood", null)
			if w_tex != null:
				draw_circle(pos + Vector2(0, 3.0 * zoom), 8.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))
				draw_texture_rect(w_tex, Rect2(ipos.x - 9.0 * zoom, ipos.y - 9.0 * zoom, 18.0 * zoom, 18.0 * zoom), false)
			else:
				# Pilha de Madeira (Fallback)
				draw_rect(Rect2(ipos.x - 6.0 * zoom, ipos.y - 4.0 * zoom, 12.0 * zoom, 4.0 * zoom), Color(0.45, 0.25, 0.12))
				draw_rect(Rect2(ipos.x - 5.0 * zoom, ipos.y - 1.0 * zoom, 10.0 * zoom, 4.0 * zoom), Color(0.55, 0.32, 0.15))

		"LEATHER", "COURO":
			# Sombra do fardo de couro
			draw_circle(pos + Vector2(0, 2.5 * zoom), 7.5 * zoom, Color(0.0, 0.0, 0.0, 0.38))
			# Rolo de couro dobrado / fardo
			var lw: float = 14.0 * zoom
			var lh: float = 9.0 * zoom
			# Camada base marrom escuro curtido
			draw_rect(Rect2(ipos.x - lw * 0.5, ipos.y - lh * 0.5, lw, lh), Color(0.38, 0.22, 0.12))
			# Camada superior couro caramelo
			draw_rect(Rect2(ipos.x - lw * 0.45, ipos.y - lh * 0.4, lw * 0.9, lh * 0.8), Color(0.58, 0.36, 0.20))
			# Correias de amarração do fardo
			draw_line(Vector2(ipos.x - lw * 0.22, ipos.y - lh * 0.5), Vector2(ipos.x - lw * 0.22, ipos.y + lh * 0.5), Color(0.85, 0.72, 0.3), 1.2 * zoom)
			draw_line(Vector2(ipos.x + lw * 0.22, ipos.y - lh * 0.5), Vector2(ipos.x + lw * 0.22, ipos.y + lh * 0.5), Color(0.85, 0.72, 0.3), 1.2 * zoom)
			# Fivela central dourada
			draw_circle(ipos + Vector2(-lw * 0.22, 0.0), 1.4 * zoom, Color(1.0, 0.88, 0.35))
			draw_circle(ipos + Vector2(lw * 0.22, 0.0), 1.4 * zoom, Color(1.0, 0.88, 0.35))

		_:
			draw_circle(ipos, 4.0 * zoom, Color(0.9, 0.8, 0.2))

	# Badge numérico de acúmulo de recursos (Stacking Badge)
	var stack_qty: int = int(item.get("amount", 1))
	if item.has("wood") and int(item["wood"]) > stack_qty: stack_qty = int(item["wood"])
	if item.has("leather") and int(item["leather"]) > stack_qty: stack_qty = int(item["leather"])
	if item.has("metal") and int(item["metal"]) > stack_qty: stack_qty = int(item["metal"])
	if item.has("gold") and int(item["gold"]) > stack_qty: stack_qty = int(item["gold"])
	if item.has("crystal") and int(item["crystal"]) > stack_qty: stack_qty = int(item["crystal"])

	if stack_qty > 1:
		var font: Font = ThemeDB.fallback_font
		var qty_txt: String = "x%d" % stack_qty
		var font_sz: int = int(7 * zoom)
		var str_w: float = font.get_string_size(qty_txt, HORIZONTAL_ALIGNMENT_CENTER, -1, font_sz).x
		var b_w: float = maxf(str_w + 4.0 * zoom, 12.0 * zoom)
		var b_h: float = 8.0 * zoom
		var badge_origin: Vector2 = Vector2(ipos.x - b_w * 0.5, ipos.y - 7.5 * zoom)
		draw_rect(Rect2(badge_origin.x, badge_origin.y, b_w, b_h), Color(0.06, 0.06, 0.12, 0.90))
		draw_rect(Rect2(badge_origin.x, badge_origin.y, b_w, b_h), Color(1.0, 0.85, 0.25, 0.85), false, 1.0)
		draw_string(font, Vector2(badge_origin.x + (b_w - str_w) * 0.5, badge_origin.y + 6.5 * zoom), qty_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, font_sz, Color(1.0, 0.95, 0.6))

## Resolves and caches textures for heroes and Isectum monsters on the tactical board
func get_unit_texture(unit_id: String, unit_data: Dictionary = {}) -> Texture2D:
	var cache_key: String = unit_id.to_lower().strip_edges()
	if _unit_texture_cache.has(cache_key):
		return _unit_texture_cache[cache_key]

	# 1. Checa explicitamente a propriedade "sprite" ou "icon" nos dados da unidade
	var explicit_sprite: String = str(unit_data.get("sprite", unit_data.get("icon", "")))
	if not explicit_sprite.is_empty():
		if ResourceLoader.exists(explicit_sprite) or FileAccess.file_exists(explicit_sprite):
			var tex: Texture2D = load(explicit_sprite) as Texture2D
			if tex != null:
				_unit_texture_cache[cache_key] = tex
				return tex

	var uid_clean: String = unit_id.strip_edges().to_lower()
	var uname_clean: String = str(unit_data.get("name", "")).strip_edges().to_lower()
	var uclass_clean: String = str(unit_data.get("class", unit_data.get("classe", ""))).strip_edges().to_lower()

	# 2. Retratos canônicos de heróis (128x128 RGBA)
	var hero_keys: Array[String] = [uid_clean, uname_clean, uclass_clean]
	for hkey in hero_keys:
		if hkey.is_empty():
			continue
		var h_slug: String = hkey
		if h_slug in ["aquele", "guerreiro", "?????"]:
			h_slug = "aquele"
		elif h_slug in ["stark", "paladino"]:
			h_slug = "stark"
		elif h_slug in ["elden", "mago"]:
			h_slug = "elden"
		elif h_slug in ["doom"]:
			h_slug = "doom"
		elif h_slug in ["gruu", "barbaro"]:
			h_slug = "gruu"
		elif h_slug in ["kuro"]:
			h_slug = "kuro"
		elif h_slug in ["darwin", "druida"]:
			h_slug = "darwin"
		elif h_slug in ["lysander", "pr. lysander", "comandante"]:
			h_slug = "lysander"
		
		var p_path: String = "res://assets/images/characters/portraits/%s_portrait.png" % h_slug
		if ResourceLoader.exists(p_path) or FileAccess.file_exists(p_path):
			var tex: Texture2D = load(p_path) as Texture2D
			if tex != null:
				_unit_texture_cache[cache_key] = tex
				return tex

	# 3. Castas do Enxame Isectum (32x32 pixel art)
	var isectum_map: Dictionary = {
		# Mapeamento canônico das 24 castas Isectum
		"zangao_invasor": "vespa_cacadora",
		"soldado_mandibula": "formiga_correicao",
		"operario_escavador": "escaravelho_necrofago",
		"tece_teia": "aranha_clepto",
		"escaravelho_couracado": "besouro_rinoceronte",
		"vespa_furtiva": "vespa_joia",
		"formiga_acida": "formiga_correicao",
		"louva_deus_ceifador": "louva_deus",
		"besouro_rinoceronte": "besouro_rinoceronte",
		"centopeia_venenosa": "centopeia_olhos",
		"barata_praga": "infiltrador",
		"traca_da_runa": "mariposa_esfinge",
		"cupim_roedor": "besouro_gorgulho",
		"vagalume_cego": "vagalume_sombras",
		"aranha_saltadora": "viuva_canibal",
		"libelula_bombardeira": "libelula_blindada",
		"bicho_pau_emboscador": "infiltrador",
		"percevejo_pestilento": "carrapato_vampiro",
		"carrapato_parasita": "carrapato_vampiro",
		"pulga_saltadora": "viuva_negra",
		"grilo_atordoante": "cigarra_ressonante",
		"larva_necrotica": "larva_carniceira",
		"rainha_do_enxame": "enxame_rainha",
		"colosso_isectum": "brutamonte",

		# Prefixos e apelidos táticos
		"zangao": "vespa_cacadora",
		"operario": "escaravelho_necrofago",
		"barata": "infiltrador",
		"traca": "mariposa_esfinge",
		"cupim": "besouro_gorgulho",
		"bicho_pau": "infiltrador",
		"bicho": "infiltrador",
		"percevejo": "carrapato_vampiro",
		"pulga": "viuva_negra",
		"grilo": "cigarra_ressonante",
		"colosso": "brutamonte",
		"batedor": "infiltrador",
		"infiltrador": "infiltrador",
		"soldado": "formiga_correicao",
		"formiga": "formiga_correicao",
		"vespa": "vespa_cacadora",
		"vespa_cacadora": "vespa_cacadora",
		"vespa_joia": "vespa_joia",
		"besouro": "besouro_rinoceronte",
		"besouro_unicornio": "besouro_unicornio",
		"besouro_gorgulho": "besouro_gorgulho",
		"brutamonte": "brutamonte",
		"aranha": "aranha_clepto",
		"aranha_clepto": "aranha_clepto",
		"centopeia": "centopeia_olhos",
		"centopeia_olhos": "centopeia_olhos",
		"cigarra": "cigarra_ressonante",
		"cigarra_ressonante": "cigarra_ressonante",
		"efemera": "efemera_mimetica",
		"efemera_mimetica": "efemera_mimetica",
		"enxame": "enxame_rainha",
		"rainha": "enxame_rainha",
		"enxame_rainha": "enxame_rainha",
		"escaravelho": "escaravelho_necrofago",
		"gafanhoto": "gafanhoto_praga",
		"gafanhoto_praga": "gafanhoto_praga",
		"larva": "larva_carniceira",
		"libelula": "libelula_blindada",
		"louva_deus": "louva_deus",
		"mariposa": "mariposa_esfinge",
		"mosca": "mosca_tse_tse",
		"mosca_tse_tse": "mosca_tse_tse",
		"tarantula": "tarantula_golias",
		"tarantula_golias": "tarantula_golias",
		"vagalume": "vagalume_sombras",
		"viuva": "viuva_negra",
		"viuva_negra": "viuva_negra",
		"viuva_canibal": "viuva_canibal",
		"abelha": "abelha_tecela",
		"abelha_tecela": "abelha_tecela",
		"carrapato": "carrapato_vampiro"
	}

	# Limpa sufixos de wave (_w1_1) e prefixos de nome ("horda: ", "chegada do chefe: ")
	var regex_clean_uid: String = uid_clean
	var wave_sep_pos: int = uid_clean.find("_w")
	if wave_sep_pos > 0:
		regex_clean_uid = uid_clean.substr(0, wave_sep_pos)

	var clean_uname_no_prefix: String = uname_clean
	if clean_uname_no_prefix.begins_with("horda:"):
		clean_uname_no_prefix = clean_uname_no_prefix.substr(6).strip_edges()
	elif clean_uname_no_prefix.begins_with("chegada do chefe:"):
		clean_uname_no_prefix = clean_uname_no_prefix.substr(17).strip_edges()

	var normalized_uname: String = clean_uname_no_prefix \
		.replace("ã", "a").replace("á", "a").replace("à", "a") \
		.replace("é", "e").replace("ê", "e") \
		.replace("í", "i") \
		.replace("ó", "o").replace("ô", "o").replace("õ", "o") \
		.replace("ú", "u").replace("ç", "c") \
		.replace(" ", "_")

	var search_tokens: Array[String] = [
		regex_clean_uid,
		uid_clean,
		uid_clean.split("_")[0],
		normalized_uname,
		normalized_uname.split("_")[0],
		clean_uname_no_prefix,
		uname_clean,
		uclass_clean
	]

	for token in search_tokens:
		if token.is_empty():
			continue
		var caste_file: String = isectum_map.get(token, token)
		var caste_path: String = "res://assets/images/characters/monsters/isectum/%s.png" % caste_file
		if ResourceLoader.exists(caste_path) or FileAccess.file_exists(caste_path):
			var tex: Texture2D = load(caste_path) as Texture2D
			if tex != null:
				_unit_texture_cache[cache_key] = tex
				return tex

	# 4. Heróis secundários e sprites diretos em heroes/
	var hero_candidates: Array[String] = [
		"res://assets/images/characters/heroes/%s.png" % uid_clean.capitalize(),
		"res://assets/images/characters/heroes/%s.png" % uid_clean,
		"res://assets/images/characters/heroes/%s.png" % uclass_clean,
		"res://assets/images/characters/heroes/%s.png" % uclass_clean.capitalize()
	]
	for h_path in hero_candidates:
		if ResourceLoader.exists(h_path) or FileAccess.file_exists(h_path):
			var tex: Texture2D = load(h_path) as Texture2D
			if tex != null:
				_unit_texture_cache[cache_key] = tex
				return tex

	# 5. Monstros gerais em monsters/ e bosses/
	var monster_candidates: Array[String] = [
		"res://assets/images/characters/monsters/%s.png" % uid_clean,
		"res://assets/images/characters/monsters/%s.png" % uclass_clean,
		"res://assets/images/characters/bosses/%s.png" % uid_clean,
		"res://assets/images/characters/bosses/%s.png" % uid_clean.capitalize()
	]
	for m_path in monster_candidates:
		if ResourceLoader.exists(m_path) or FileAccess.file_exists(m_path):
			var tex: Texture2D = load(m_path) as Texture2D
			if tex != null:
				_unit_texture_cache[cache_key] = tex
				return tex

	_unit_texture_cache[cache_key] = null
	return null

func _draw_unit_entity(unit_id: String, data: Dictionary, pos: Vector2, zoom: float, is_selected: bool) -> void:
	var hx: float = pos.x
	var hy: float = pos.y
	var team: String = str(data.get("team", "A")).to_upper()
	var uname: String = str(data.get("name", unit_id))
	var cur_hp: int = int(data.get("hp", 10))
	var max_hp: int = maxi(1, int(data.get("max_hp", cur_hp)))
	var ac: int = int(data.get("ac", 14))
	var atk: int = int(data.get("attack_bonus", 3))

	# Unidades inimigas derrotadas não devem ser renderizadas no tabuleiro
	if team != "A" and (cur_hp <= 0 or not bool(data.get("is_alive", true))):
		return

	# 1. Sombra sutil de ancoragem no solo sob os pés do personagem
	draw_circle(Vector2(hx, hy + 2.0 * zoom), 6.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))

	# 2. Destaque de Seleção FFT (Seta suspensa e marcação sutil nos pés)
	if is_selected:
		draw_circle(Vector2(hx, hy + 2.0 * zoom), 8.0 * zoom, Color(1.0, 0.85, 0.2, 0.6), false, 1.5)
		# Cursor FFT clássico em formato de seta triangular suspensa sobre o personagem
		var arrow_bob: float = sin(_anim_timer * 8.0) * 3.0 * zoom
		var arrow_y: float = hy - 36.0 * zoom + arrow_bob
		var arrow_pts: PackedVector2Array = PackedVector2Array([
			Vector2(hx - 5.0 * zoom, arrow_y - 8.0 * zoom),
			Vector2(hx + 5.0 * zoom, arrow_y - 8.0 * zoom),
			Vector2(hx, arrow_y)
		])
		draw_colored_polygon(arrow_pts, Color(1.0, 0.85, 0.15))
		draw_polyline(PackedVector2Array([arrow_pts[0], arrow_pts[1], arrow_pts[2], arrow_pts[0]]), Color(0.3, 0.2, 0.0), 1.0)

	# 3. Sprite Limpo do Personagem (Sem bolinhas/anéis em volta)
	var spr_size: float = 30.0 * zoom if team != "A" else 28.0 * zoom
	var spr_rect: Rect2 = Rect2(hx - spr_size * 0.5, hy - spr_size + 4.0 * zoom, spr_size, spr_size)

	var tex: Texture2D = get_unit_texture(unit_id, data)
	if tex != null:
		draw_texture_rect(tex, spr_rect, false)
	else:
		# Fallback discreto sem poluição circular
		var fb_col: Color = Color(0.2, 0.45, 0.8, 0.85) if team == "A" else Color(0.8, 0.2, 0.2, 0.85)
		var fb_rect: Rect2 = Rect2(hx - 9.0 * zoom, hy - 18.0 * zoom, 18.0 * zoom, 18.0 * zoom)
		draw_rect(fb_rect, fb_col, true)
		draw_rect(fb_rect, Color(1.0, 1.0, 1.0, 0.8), false, 1.0)
		var clean_fallback_name: String = uname.strip_edges()
		if clean_fallback_name.begins_with("Horda:"):
			clean_fallback_name = clean_fallback_name.substr(6).strip_edges()
		elif clean_fallback_name.begins_with("Chegada do Chefe:"):
			clean_fallback_name = clean_fallback_name.substr(17).strip_edges()
		var initial: String = clean_fallback_name.substr(0, 1).to_upper() if not clean_fallback_name.is_empty() else "?"
		var font: Font = ThemeDB.fallback_font
		var font_sz: int = int(10 * zoom)
		draw_string(font, Vector2(hx - 3.5 * zoom, hy - 5.0 * zoom), initial, HORIZONTAL_ALIGNMENT_CENTER, -1, font_sz, Color.WHITE)

	# Efeito de Flash de Dano (Overlay avermelhado/branco ao sofrer dano)
	if _unit_anim_flashes.has(unit_id):
		var f_data: Dictionary = _unit_anim_flashes[unit_id]
		var f_color: Color = f_data.get("color", Color(1.0, 0.2, 0.2, 0.8))
		var f_timer: float = float(f_data.get("timer", 0.1))
		var f_dur: float = maxf(0.01, float(f_data.get("duration", 0.22)))
		var flash_alpha: float = clampf(f_timer / f_dur, 0.0, 1.0) * f_color.a
		var flash_col_effective: Color = Color(f_color.r, f_color.g, f_color.b, flash_alpha)
		draw_rect(spr_rect, flash_col_effective, true)

	# 4. Barra de Vida (HP) com Borda Retrô posicionada acima da cabeça do personagem
	if cur_hp > 0:
		var pct: float = clampf(float(cur_hp) / float(max_hp), 0.0, 1.0)
		var bar_w: float = clampf(20.0 * zoom, 12.0, 24.0)
		var bar_h: float = clampf(3.5 * zoom, 2.0, 4.0)
		var bar_x: float = hx - bar_w * 0.5
		var bar_y: float = hy - spr_size - 1.0 * zoom

		draw_rect(Rect2(bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), Color(0.05, 0.05, 0.08, 0.9))
		var hp_col: Color = Color(0.25, 0.85, 0.3) if pct > 0.5 else (Color(0.95, 0.8, 0.2) if pct > 0.25 else Color(0.9, 0.2, 0.2))
		if pct > 0.0:
			draw_rect(Rect2(bar_x, bar_y, bar_w * pct, bar_h), hp_col)
		draw_rect(Rect2(bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), Color(0.35, 0.4, 0.5), false, 1.0)

	# 5. Placa de Status Retrô Compacta (ao selecionar ou passar o mouse)
	var upos: Vector2i = _bound_board.get_unit_position(unit_id) if _bound_board != null else Vector2i(-1, -1)
	if is_selected or upos == hovered_cell:
		var font: Font = ThemeDB.fallback_font
		var t_info: String = "%s  %d/%d" % [uname, cur_hp, max_hp]
		var font_p_sz: int = int(7 * zoom)
		var t_sz: Vector2 = font.get_string_size(t_info, HORIZONTAL_ALIGNMENT_CENTER, -1, font_p_sz)
		var plate_w: float = maxf(t_sz.x + 8.0 * zoom, 46.0 * zoom)
		var plate_h: float = 11.0 * zoom
		var plate_rect: Rect2 = Rect2(hx - plate_w * 0.5, hy - spr_size - 12.0 * zoom, plate_w, plate_h)

		draw_rect(plate_rect, Color(0.04, 0.05, 0.10, 0.92), true)
		draw_rect(plate_rect, Color(1.0, 0.8, 0.2) if is_selected else Color(0.4, 0.6, 0.9), false, 1.0)
		draw_string(font, Vector2(hx - t_sz.x * 0.5, plate_rect.position.y + 8.0 * zoom), t_info, HORIZONTAL_ALIGNMENT_CENTER, -1, font_p_sz, Color(1.0, 0.92, 0.5) if is_selected else Color(0.9, 0.95, 1.0))

func _draw_active_projectiles(zoom: float) -> void:
	for p in _active_projectiles:
		var p_start: Vector2 = p.get("start_pos", Vector2.ZERO)
		var p_end: Vector2 = p.get("end_pos", Vector2.ZERO)
		var progress: float = clampf(float(p.get("progress", 0.0)), 0.0, 1.0)
		var arc_h: float = float(p.get("arc_height", 24.0)) * zoom
		var p_type: String = str(p.get("type", "arrow"))
		var p_color: Color = p.get("color", Color(1.0, 0.85, 0.2))

		# Posição interpolada com arco parabólico vertical: y_offset = -4 * h * p * (1 - p)
		var cur_pos: Vector2 = p_start.lerp(p_end, progress)
		var arc_offset: float = -4.0 * arc_h * progress * (1.0 - progress)
		cur_pos.y += arc_offset

		if p_type == "beam":
			# Trajetória direta de feixe de energia / ácido
			draw_line(p_start, cur_pos, p_color, 2.5 * zoom)
			draw_circle(cur_pos, 4.0 * zoom, Color(1.0, 1.0, 1.0, 0.9))
		else:
			# Flecha balística / dardo de balista com rastro
			var prev_prog: float = maxf(0.0, progress - 0.08)
			var prev_pos: Vector2 = p_start.lerp(p_end, prev_prog)
			prev_pos.y += -4.0 * arc_h * prev_prog * (1.0 - prev_prog)

			# Rastro luminoso
			draw_line(prev_pos, cur_pos, Color(p_color.r, p_color.g, p_color.b, 0.45), 1.5 * zoom)

			# Cabeça da flecha e corpo
			var dir: Vector2 = (cur_pos - prev_pos).normalized()
			if dir == Vector2.ZERO:
				dir = (p_end - p_start).normalized()
			var tip: Vector2 = cur_pos + dir * (4.0 * zoom)
			draw_line(prev_pos, tip, p_color, 2.0 * zoom)
			draw_circle(tip, 2.2 * zoom, Color(1.0, 0.95, 0.8))

func _draw_floating_combat_texts(zoom: float) -> void:
	if _floating_combat_texts.is_empty():
		return
	var font: Font = ThemeDB.fallback_font
	for ft in _floating_combat_texts:
		var text: String = str(ft.get("text", ""))
		var pos: Vector2 = ft.get("pos", Vector2.ZERO)
		var base_col: Color = ft.get("color", Color.WHITE)
		var timer: float = float(ft.get("timer", 0.0))
		var dur: float = maxf(0.1, float(ft.get("duration", 0.95)))
		var is_crit: bool = bool(ft.get("is_crit", false))

		# Efeito de fade-out suave nos últimos 35% da duração
		var alpha: float = 1.0
		if timer > dur * 0.65:
			alpha = clampf(1.0 - (timer - dur * 0.65) / (dur * 0.35), 0.0, 1.0)

		var col: Color = Color(base_col.r, base_col.g, base_col.b, alpha)
		var font_sz: int = int((14 if is_crit else 10) * zoom)
		var t_size: Vector2 = font.get_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, -1, font_sz)
		var t_draw_pos: Vector2 = pos - Vector2(t_size.x * 0.5, 0.0)

		# Sombra/contorno escuro para máxima legibilidade retrô
		var outline_col: Color = Color(0.0, 0.0, 0.0, alpha * 0.9)
		for ox in [-1.0, 1.0]:
			for oy in [-1.0, 1.0]:
				draw_string(font, t_draw_pos + Vector2(ox, oy), text, HORIZONTAL_ALIGNMENT_CENTER, -1, font_sz, outline_col)

		draw_string(font, t_draw_pos, text, HORIZONTAL_ALIGNMENT_CENTER, -1, font_sz, col)

func _draw_pine_tree(pos: Vector2, zoom: float) -> void:
	var tree_tex: Texture2D = _load_terrain_texture("arvore", "res://assets/images/environment/arvore_pinheiro.png")
	
	# Sombra suave sob a árvore
	draw_circle(pos + Vector2(0, 3.0 * zoom), 10.0 * zoom, Color(0.0, 0.0, 0.0, 0.45))
	
	if tree_tex != null:
		var tw: float = 34.0 * zoom
		var th: float = 44.0 * zoom
		var tree_rect: Rect2 = Rect2(pos.x - tw * 0.5, pos.y - th + 4.0 * zoom, tw, th)
		draw_texture_rect(tree_tex, tree_rect, false)
	else:
		var trunk_w: float = max(2.0, 5.0 * zoom)
		var trunk_h: float = max(4.0, 14.0 * zoom)
		draw_rect(Rect2(pos.x - trunk_w * 0.5, pos.y - trunk_h, trunk_w, trunk_h), Color(0.35, 0.22, 0.12))
		var r1: float = max(4.0, 11.0 * zoom)
		var r2: float = max(3.0, 8.5 * zoom)
		var r3: float = max(2.0, 6.0 * zoom)
		var y1: float = pos.y - trunk_h
		var y2: float = y1 - 6.0 * zoom
		var y3: float = y2 - 6.0 * zoom
		draw_circle(Vector2(pos.x, y1), r1, Color(0.11, 0.38, 0.17))
		draw_circle(Vector2(pos.x, y1), r1, Color(0.07, 0.26, 0.11), false, 1.0)
		draw_circle(Vector2(pos.x, y2), r2, Color(0.15, 0.50, 0.21))
		draw_circle(Vector2(pos.x, y2), r2, Color(0.09, 0.34, 0.13), false, 1.0)
		draw_circle(Vector2(pos.x, y3), r3, Color(0.19, 0.62, 0.25))
		draw_circle(Vector2(pos.x, y3), r3, Color(0.11, 0.42, 0.16), false, 1.0)

func _draw_commander_throne(px: float, py: float, zoom: float) -> void:
	# ── 1. Sombra projetada na base do pedestal (solo) ─────────────────────────
	draw_circle(Vector2(px, py + 2.0 * zoom), 14.0 * zoom, Color(0.0, 0.0, 0.0, 0.35))
	
	# ── 2. Base e Plinto do Pedestal (Cantaria de Pedra) ──────────────────────
	var base_w1: float = 28.0 * zoom
	var base_h1: float = 4.0 * zoom
	var base_rect1: Rect2 = Rect2(px - base_w1 * 0.5, py - base_h1 * 0.5, base_w1, base_h1)
	draw_rect(base_rect1, Color(0.18, 0.20, 0.26))
	draw_rect(base_rect1, Color(0.30, 0.35, 0.44), false, 1.0 * zoom)

	var base_w2: float = 22.0 * zoom
	var base_h2: float = 3.0 * zoom
	var base_rect2: Rect2 = Rect2(px - base_w2 * 0.5, py - base_h1 - base_h2 * 0.5, base_w2, base_h2)
	draw_rect(base_rect2, Color(0.24, 0.27, 0.34))
	draw_rect(base_rect2, Color(0.85, 0.72, 0.22), false, 1.0 * zoom)

	# ── 3. Fuste Compacto do Pilar (Cantaria) ───────────────────────────────
	var pillar_w: float = 16.0 * zoom
	var pillar_h: float = 16.0 * zoom
	var shaft_top_y: float = py - base_h1 - base_h2 - pillar_h
	var shaft_rect: Rect2 = Rect2(px - pillar_w * 0.5, shaft_top_y, pillar_w, pillar_h)

	draw_rect(shaft_rect, Color(0.22, 0.25, 0.32))
	var hl_w: float = 4.0 * zoom
	var sh_w: float = 4.0 * zoom
	draw_rect(Rect2(px - pillar_w * 0.5, shaft_top_y, hl_w, pillar_h), Color(0.35, 0.40, 0.50))
	draw_rect(Rect2(px + pillar_w * 0.5 - sh_w, shaft_top_y, sh_w, pillar_h), Color(0.13, 0.15, 0.20))
	draw_rect(shaft_rect, Color(0.10, 0.12, 0.16), false, 1.0 * zoom)

	# ── 4. Capitel e Platô Superior ──────────────────────────────────────────
	var cap_w1: float = 20.0 * zoom
	var cap_h1: float = 3.0 * zoom
	var cap_rect1: Rect2 = Rect2(px - cap_w1 * 0.5, shaft_top_y - cap_h1, cap_w1, cap_h1)
	draw_rect(cap_rect1, Color(0.28, 0.32, 0.40))

	var cap_w2: float = 26.0 * zoom
	var cap_h2: float = 4.0 * zoom
	var plat_y: float = shaft_top_y - cap_h1 - cap_h2
	var plat_rect: Rect2 = Rect2(px - cap_w2 * 0.5, plat_y, cap_w2, cap_h2)
	draw_rect(plat_rect, Color(0.20, 0.22, 0.28))
	draw_rect(plat_rect, Color(1.0, 0.85, 0.30), false, 1.2 * zoom)
	
	draw_circle(Vector2(px, plat_y + cap_h2 * 0.5), 6.0 * zoom, Color(0.0, 0.0, 0.0, 0.30))

	# ── 5. Estandarte e Mastro Imperial Contido ──────────────────────────────
	var mast_x: float = px + cap_w2 * 0.5 + 1.0 * zoom
	var mast_y: float = py - 2.0 * zoom
	var mast_top_y: float = plat_y - 14.0 * zoom
	draw_line(Vector2(mast_x, mast_y), Vector2(mast_x, mast_top_y), Color(0.70, 0.55, 0.22), 2.0 * zoom)
	draw_circle(Vector2(mast_x, mast_top_y), 2.0 * zoom, Color(1.0, 0.88, 0.30))

	# Bandeira Imperial Pequena Ondulante
	var flag_w: float = 14.0 * zoom
	var flag_wave: float = sin(_anim_timer * 5.0) * 1.5 * zoom
	var flag_pts: PackedVector2Array = PackedVector2Array([
		Vector2(mast_x, mast_top_y + 1.0 * zoom),
		Vector2(mast_x + flag_w, mast_top_y + 5.0 * zoom + flag_wave),
		Vector2(mast_x + flag_w * 0.65, mast_top_y + 10.0 * zoom),
		Vector2(mast_x + flag_w, mast_top_y + 14.0 * zoom - flag_wave),
		Vector2(mast_x, mast_top_y + 16.0 * zoom)
	])
	draw_colored_polygon(flag_pts, Color(0.78, 0.12, 0.12))
	draw_polyline(flag_pts, Color(1.0, 0.85, 0.25), 1.0 * zoom)

func _draw_hero_on_board(hx: float, hy: float, zoom: float) -> void:
	# Fallback com token do herói
	var fallback_data: Dictionary = {
		"name": "Aquele", "class": "Guerreiro", "team": "A",
		"hp": 48, "max_hp": 48, "ac": 17, "attack_bonus": 3
	}
	_draw_unit_entity("aquele", fallback_data, Vector2(hx, hy), zoom, true)

# ── Input Handling (Final Fantasy Tactics Tactical Controls & Camera) ─────────
func _unhandled_input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_Q:
			rotate_camera_left()
			accept_event()
			return
		elif event.keycode == KEY_E:
			rotate_camera_right()
			accept_event()
			return
		elif event.keycode == KEY_R:
			reset_camera()
			accept_event()
			return

func _gui_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_Q:
			rotate_camera_left()
			accept_event()
			return
		elif event.keycode == KEY_E:
			rotate_camera_right()
			accept_event()
			return
		elif event.keycode == KEY_R:
			reset_camera()
			accept_event()
			return

	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.pressed:
			# ── Botões Táteis do HUD de Câmera FFT (Topo Direito) ─────────────
			var r_w: float = size.x
			var btn_y: float = 12.0
			var btn_w: float = 52.0
			var btn_h: float = 24.0
			var q_btn_rect: Rect2 = Rect2(r_w - 120.0, btn_y, btn_w, btn_h)
			var e_btn_rect: Rect2 = Rect2(r_w - 60.0, btn_y, btn_w, btn_h)

			if mb.button_index == MOUSE_BUTTON_LEFT:
				if q_btn_rect.has_point(mb.position):
					rotate_camera_left()
					accept_event()
					return
				elif e_btn_rect.has_point(mb.position):
					rotate_camera_right()
					accept_event()
					return

			# ── Câmera: Zoom via Scroll ───────────────────────────────────────
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_apply_zoom(cam_zoom + CAM_ZOOM_STEP, mb.position)
				accept_event()
				return
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_apply_zoom(cam_zoom - CAM_ZOOM_STEP, mb.position)
				accept_event()
				return
			# ── Câmera: Pan via Botão do Meio ────────────────────────────────
			elif mb.button_index == MOUSE_BUTTON_MIDDLE:
				_is_panning = true
				_pan_start_mouse = mb.position
				_pan_start_cam = cam_pan
				accept_event()
				return
			# ── Câmera: Pan via Botão Direito / Deselecionar FFT ─────────────
			elif mb.button_index == MOUSE_BUTTON_RIGHT:
				_is_panning = true
				_pan_start_mouse = mb.position
				_pan_start_cam = cam_pan
				deselect_unit()
				accept_event()
				return
			# ── Botão Esquerdo: Seleção / Movimento / Ataque / Zona ───────────
			elif mb.button_index == MOUSE_BUTTON_LEFT and not _is_panning:
				var world_pos: Vector2 = _screen_to_world(mb.position)
				var grid_pos: Vector2i = iso_screen_to_grid(world_pos)
				if grid_pos == Vector2i(-1, -1):
					grid_pos = screen_to_grid(world_pos)

				# 1. Verifica se clicou diretamente em uma unidade no tabuleiro
				if _bound_board != null and _bound_board.has_method("get_units_at_cell"):
					var units_clicked: Array[String] = _bound_board.get_units_at_cell(grid_pos)
					if not units_clicked.is_empty():
						var target_uid: String = units_clicked[0]
						var target_data: Dictionary = _bound_board.get_unit_data(target_uid)
						var target_team: String = str(target_data.get("team", "A"))

						# Clicou em um herói aliado -> Seleciona-o no estilo FFT!
						if target_team == "A":
							select_unit(target_uid)
							accept_event()
							return
						# Clicou em um inimigo ao alcance enquanto tem herói selecionado -> Ataca!
						elif not selected_unit_id.is_empty() and grid_pos in attackable_cells:
							unit_attack_requested.emit(selected_unit_id, target_uid)
							accept_event()
							return

				# 2. Se um herói estiver selecionado e o jogador clicar em um tile azul de movimento
				if not selected_unit_id.is_empty() and grid_pos in reachable_cells:
					move_selected_unit_to(grid_pos)
					accept_event()
					return

				# 3. Clique em uma zona do tabuleiro (fallback ou foco de zona)
				var zid: String = get_zone_at(grid_pos)
				if not zid.is_empty():
					select_zone(zid)
					accept_event()
		else:
			# Soltou botão do mouse
			if mb.button_index == MOUSE_BUTTON_MIDDLE or mb.button_index == MOUSE_BUTTON_RIGHT:
				_is_panning = false

	elif event is InputEventMouseMotion:
		var mm: InputEventMouseMotion = event as InputEventMouseMotion
		if _is_panning:
			cam_pan = _pan_start_cam + (mm.position - _pan_start_mouse)
			cam_pan = _clamp_pan(cam_pan)
			queue_redraw()
			accept_event()
			return

		var world_pos: Vector2 = _screen_to_world(mm.position)
		var grid_pos: Vector2i = iso_screen_to_grid(world_pos)
		if grid_pos == Vector2i(-1, -1):
			grid_pos = screen_to_grid(world_pos)
		if grid_pos != hovered_cell:
			hovered_cell = grid_pos
			queue_redraw()

		var zid: String = get_zone_at(grid_pos)
		if zid != hovered_zone:
			if not hovered_zone.is_empty():
				zone_unhovered.emit(hovered_zone)
			hovered_zone = zid
			if not hovered_zone.is_empty():
				zone_hovered.emit(hovered_zone)
			if zone_overlay != null:
				zone_overlay.set_hovered_zone(hovered_zone)

# ── 1. Névoa Rastejante & Miasma no Perímetro ─────────────────────────────────
func _draw_creeping_miasma(cx: float, cy: float, _tw: float, _th: float, zoom: float) -> void:
	for m_i in range(8):
		var m_angle: float = float(m_i) * (TAU / 8.0) + _anim_timer * 0.08
		var m_dist: float = 230.0 * zoom + sin(_anim_timer * 0.6 + float(m_i * 2)) * 25.0 * zoom
		var mx: float = cx + cos(m_angle) * m_dist
		var my: float = cy + sin(m_angle) * (m_dist * 0.52)
		var m_pulse: float = 0.5 + 0.3 * sin(_anim_timer * 1.3 + float(m_i))
		draw_circle(Vector2(mx, my), 52.0 * zoom, Color(0.04, 0.18, 0.08, 0.08 * m_pulse))
		draw_circle(Vector2(mx, my), 28.0 * zoom, Color(0.02, 0.12, 0.05, 0.11 * m_pulse))

# ── 2. Sombras Projetadas das Muralhas e Torres no Chão do Pátio ─────────────
func _draw_projected_shadows(cells: Array[Dictionary], tw: float, th: float, cx: float, cy: float, zoom: float) -> void:
	for c in cells:
		var el: int = int(c.get("el", 0))
		if el >= 4:
			var dx: float = float(c.get("dx", 0.0))
			var dy: float = float(c.get("dy", 0.0))
			var sx_floor: float = (dx - dy) * (tw * 0.5) + cx
			var sy_floor: float = (dx + dy) * (th * 0.5) + cy
			var s_off_x: float = float(el) * 3.5 * zoom
			var s_off_y: float = float(el) * 2.2 * zoom
			var sh_p0: Vector2 = Vector2(sx_floor, sy_floor - th * 0.5) + Vector2(s_off_x, s_off_y)
			var sh_p1: Vector2 = Vector2(sx_floor + tw * 0.5, sy_floor) + Vector2(s_off_x, s_off_y)
			var sh_p2: Vector2 = Vector2(sx_floor, sy_floor + th * 0.5) + Vector2(s_off_x, s_off_y)
			var sh_p3: Vector2 = Vector2(sx_floor - tw * 0.5, sy_floor) + Vector2(s_off_x, s_off_y)
			draw_colored_polygon(PackedVector2Array([sh_p0, sh_p1, sh_p2, sh_p3]), Color(0.02, 0.02, 0.05, 0.16))

# ── 3. Fissuras e Rachaduras Dinâmicas nas Muralhas ───────────────────────────
func _draw_wall_fissures(pts_l: PackedVector2Array, pts_r: PackedVector2Array, zk: String, wall_alpha: float, zoom: float) -> void:
	var norm: String = zk.to_upper()
	var hp: int = wall_hps.get(norm, 100)
	if is_wall_breached(norm) or hp <= 0:
		var pulse: float = sin(_anim_timer * 6.0) * 0.35 + 0.65
		if pts_l.size() >= 4:
			draw_line(pts_l[0], pts_l[2], Color(1.0, 0.25, 0.25, pulse * wall_alpha), 2.5 * zoom)
			draw_line(pts_l[1], pts_l[3], Color(0.9, 0.15, 0.15, pulse * wall_alpha), 2.0 * zoom)
			draw_circle(pts_l[2] + Vector2(2 * zoom, 1 * zoom), 3.0 * zoom, Color(0.18, 0.18, 0.22, wall_alpha))
			draw_circle(pts_l[2] + Vector2(-4 * zoom, 3 * zoom), 2.2 * zoom, Color(0.12, 0.12, 0.16, wall_alpha))
		if pts_r.size() >= 4:
			draw_line(pts_r[0], pts_r[2], Color(1.0, 0.25, 0.25, pulse * wall_alpha), 2.5 * zoom)
	elif hp < 50:
		if pts_l.size() >= 4:
			var mid_l: Vector2 = pts_l[0].lerp(pts_l[2], 0.5) + Vector2(3.0 * zoom, 0.0)
			draw_line(pts_l[0], mid_l, Color(0.08, 0.08, 0.12, 0.85 * wall_alpha), 1.8 * zoom)
			draw_line(mid_l, pts_l[2], Color(0.08, 0.08, 0.12, 0.85 * wall_alpha), 1.8 * zoom)
			draw_line(mid_l, pts_l[1], Color(0.15, 0.15, 0.20, 0.65 * wall_alpha), 1.2 * zoom)
		if pts_r.size() >= 4:
			var mid_r: Vector2 = pts_r[0].lerp(pts_r[2], 0.45) - Vector2(2.5 * zoom, 0.0)
			draw_line(pts_r[0], mid_r, Color(0.08, 0.08, 0.12, 0.85 * wall_alpha), 1.8 * zoom)
			draw_line(mid_r, pts_r[2], Color(0.08, 0.08, 0.12, 0.85 * wall_alpha), 1.8 * zoom)
	elif hp < 100:
		if pts_l.size() >= 4:
			draw_line(pts_l[0], pts_l[0].lerp(pts_l[2], 0.6), Color(0.14, 0.14, 0.18, 0.7 * wall_alpha), 1.2 * zoom)

# ── 4. Tochas Vivas com Flicker e Fagulhas Subindo (4 Torres & Portão Norte) ──
func _draw_torches_and_lights(cx: float, cy: float, tw: float, th: float, es: float, zoom: float) -> void:
	var torch_locs: Array[Dictionary] = [
		{"gx": 3.5, "gy": 3.5, "el": 6.2},
		{"gx": 15.5, "gy": 3.5, "el": 6.2},
		{"gx": 3.5, "gy": 15.5, "el": 6.2},
		{"gx": 15.5, "gy": 15.5, "el": 6.2},
		{"gx": 8.5, "gy": 2.2, "el": 4.2},
		{"gx": 11.5, "gy": 2.2, "el": 4.2}
	]
	for idx in range(torch_locs.size()):
		var t: Dictionary = torch_locs[idx]
		var r_coord: Vector2 = get_rotated_dx_dy(float(t["gx"]) - 9.5, float(t["gy"]) - 9.5)
		var tx: float = (r_coord.x - r_coord.y) * (tw * 0.5) + cx
		var ty: float = (r_coord.x + r_coord.y) * (th * 0.5) - float(t["el"]) * es + cy

		var flicker: float = 1.0 + 0.12 * sin(_anim_timer * 13.7 + float(idx) * 2.1) + 0.08 * cos(_anim_timer * 19.3 + float(idx) * 3.7)

		# Luz âmbar atmosférica suave (PointLight2D)
		draw_circle(Vector2(tx, ty), 36.0 * zoom * flicker, Color(1.0, 0.60, 0.12, 0.09))
		draw_circle(Vector2(tx, ty), 18.0 * zoom * flicker, Color(1.0, 0.78, 0.25, 0.16))
		draw_circle(Vector2(tx, ty), 7.0 * zoom * flicker, Color(1.0, 0.92, 0.45, 0.35))

		# Suporte de ferro escuro da tocha
		draw_line(Vector2(tx, ty + 2.0 * zoom), Vector2(tx, ty + 7.0 * zoom), Color(0.20, 0.18, 0.16), 2.0 * zoom)
		draw_circle(Vector2(tx, ty + 1.0 * zoom), 2.0 * zoom, Color(0.40, 0.25, 0.12))

		# Chama viva com núcleo brilhante
		draw_circle(Vector2(tx, ty - 1.0 * zoom), 3.0 * zoom * flicker, Color(1.0, 0.45, 0.08, 0.95))
		draw_circle(Vector2(tx, ty - 2.0 * zoom), 1.8 * zoom * flicker, Color(1.0, 0.95, 0.35, 1.0))

		# Partículas de fagulhas e brasas subindo no ar (CPUParticles procedural)
		for s_i in range(3):
			var s_prog: float = fmod(_anim_timer * 1.8 + float(idx * 7 + s_i * 13) * 0.33, 1.0)
			var s_y: float = ty - 3.0 * zoom - s_prog * 22.0 * zoom
			var s_x: float = tx + sin(_anim_timer * 6.0 + float(s_i * 4)) * 3.5 * zoom
			var s_alpha: float = (1.0 - s_prog) * 0.85
			draw_circle(Vector2(s_x, s_y), 1.0 * zoom, Color(1.0, 0.82, 0.25, s_alpha))

# ── 5. Linha Parabólica de Trajetória e Perigo com % de Acerto ───────────────
func _draw_targeting_trajectory(_cx: float, _cy: float, _tw: float, _th: float, _es: float, zoom: float) -> void:
	if selected_unit_id.is_empty() or hovered_cell == Vector2i(-1, -1):
		return
	if not (hovered_cell in attackable_cells):
		return
	if _bound_board == null or not _bound_board.has_method("get_unit_position"):
		return

	var src_pos: Vector2i = _bound_board.get_unit_position(selected_unit_id)
	if src_pos == Vector2i(-1, -1):
		return

	var src_coords: Vector2 = get_cell_screen_coords(src_pos.x, src_pos.y)
	var tgt_coords: Vector2 = get_cell_screen_coords(hovered_cell.x, hovered_cell.y)

	var atk_data: Dictionary = _bound_board.get_unit_data(selected_unit_id) if _bound_board.has_method("get_unit_data") else {}
	var atk_bonus: int = int(atk_data.get("attack_bonus", 3))

	var tgt_ac: int = 13
	if _bound_board.has_method("get_units_at_cell"):
		var u_here: Array = _bound_board.get_units_at_cell(hovered_cell)
		if not u_here.is_empty():
			var tdata: Dictionary = _bound_board.get_unit_data(u_here[0])
			tgt_ac = int(tdata.get("ac", 13))

	var req_roll: int = clamp(tgt_ac - atk_bonus, 2, 20)
	var hit_pct: int = int(round(float(21 - req_roll) / 20.0 * 100.0))

	var segments: int = 14
	var arc_h: float = 38.0 * zoom
	var prev_pt: Vector2 = src_coords + Vector2(0, -10.0 * zoom)

	for s in range(1, segments + 1):
		var prog: float = float(s) / float(segments)
		var pt: Vector2 = (src_coords + Vector2(0, -10.0 * zoom)).lerp(tgt_coords + Vector2(0, -6.0 * zoom), prog)
		pt.y += -4.0 * arc_h * prog * (1.0 - prog)

		if s % 2 == 1:
			draw_line(prev_pt, pt, Color(1.0, 0.35, 0.25, 0.85), 2.0 * zoom)
			draw_circle(pt, 1.8 * zoom, Color(1.0, 0.85, 0.3, 0.9))
		prev_pt = pt

	var apex_prog: float = 0.5
	var apex_pt: Vector2 = (src_coords + Vector2(0, -10.0 * zoom)).lerp(tgt_coords + Vector2(0, -6.0 * zoom), apex_prog)
	apex_pt.y += -arc_h

	var font: Font = ThemeDB.fallback_font
	var badge_txt: String = "🎯 %d%% ACERTO (CA %d)" % [hit_pct, tgt_ac]
	var b_sz: Vector2 = font.get_string_size(badge_txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 10)
	var b_rect: Rect2 = Rect2(apex_pt.x - (b_sz.x + 12.0) * 0.5, apex_pt.y - 18.0, b_sz.x + 12.0, 18.0)

	draw_rect(b_rect, Color(0.08, 0.09, 0.15, 0.92), true)
	draw_rect(b_rect, Color(1.0, 0.45, 0.2, 0.95), false, 1.2)
	draw_string(font, Vector2(b_rect.position.x + 6.0, b_rect.position.y + 13.0), badge_txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 10, Color(1.0, 0.95, 0.75))

# ── 6. Partículas de Combate Procedurais ──────────────────────────────────────
func _draw_combat_particles(zoom: float) -> void:
	for p in _combat_particles:
		var p_timer: float = float(p.get("timer", 0.0))
		var p_dur: float = maxf(0.01, float(p.get("duration", 0.5)))
		var p_alpha: float = clampf(1.0 - (p_timer / p_dur), 0.0, 1.0)
		var base_c: Color = p.get("color", Color.WHITE)
		var p_col: Color = Color(base_c.r, base_c.g, base_c.b, base_c.a * p_alpha)
		var p_sz: float = float(p.get("size", 3.0)) * zoom
		var pos: Vector2 = p.get("pos", Vector2.ZERO)
		draw_circle(pos, p_sz, p_col)

# ── 7. Card Flutuante de Informação Tática Rápida (Tooltip estilo FFT) ───────
func _draw_tactical_tooltip(r_width: float, _r_height: float) -> void:
	if hovered_cell == Vector2i(-1, -1) or _bound_board == null:
		return
	if not _bound_board.has_method("get_units_at_cell"):
		return
	var u_list: Array = _bound_board.get_units_at_cell(hovered_cell)
	if u_list.is_empty():
		return

	var uid: String = str(u_list[0])
	var udata: Dictionary = _bound_board.get_unit_data(uid)
	if udata.is_empty():
		return

	var uname: String = str(udata.get("name", uid))
	var team: String = str(udata.get("team", "A"))
	var cur_hp: int = int(udata.get("hp", 10))
	var max_hp: int = int(udata.get("max_hp", 10))
	var ac: int = int(udata.get("ac", 13))
	var pm: int = int(udata.get("move_range", 3))
	var atk_r: int = int(udata.get("attack_range", 1))
	var atk_b: int = int(udata.get("attack_bonus", 3))
	var is_hero: bool = (team == "A")

	var font: Font = ThemeDB.fallback_font
	var card_w: float = 190.0
	var card_h: float = 84.0
	var card_x: float = r_width - card_w - 14.0
	var card_y: float = 46.0
	var card_rect: Rect2 = Rect2(card_x, card_y, card_w, card_h)

	draw_rect(card_rect, Color(0.06, 0.07, 0.12, 0.95), true)
	var border_c: Color = Color(0.85, 0.70, 0.25, 0.95) if is_hero else Color(0.95, 0.30, 0.25, 0.95)
	draw_rect(card_rect, border_c, false, 1.5)

	for cx_o in [card_rect.position.x, card_rect.position.x + card_rect.size.x]:
		for cy_o in [card_rect.position.y, card_rect.position.y + card_rect.size.y]:
			draw_circle(Vector2(cx_o, cy_o), 2.5, border_c)

	var team_tag: String = "🛡️ HERÓI" if is_hero else "👾 INVASOR"
	var title_txt: String = "%s: %s" % [team_tag, uname]
	draw_string(font, Vector2(card_x + 8.0, card_y + 15.0), title_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(1.0, 0.95, 0.8))

	var bar_x: float = card_x + 8.0
	var bar_y: float = card_y + 22.0
	var bar_w: float = card_w - 16.0
	var bar_h: float = 5.0
	draw_rect(Rect2(bar_x, bar_y, bar_w, bar_h), Color(0.12, 0.12, 0.16, 0.9), true)
	var hp_pct: float = clampf(float(cur_hp) / float(maxi(1, max_hp)), 0.0, 1.0)
	var hp_col: Color = Color(0.25, 0.85, 0.3) if hp_pct > 0.5 else (Color(0.95, 0.8, 0.2) if hp_pct > 0.25 else Color(0.9, 0.2, 0.2))
	if hp_pct > 0.0:
		draw_rect(Rect2(bar_x, bar_y, bar_w * hp_pct, bar_h), hp_col, true)
	draw_rect(Rect2(bar_x, bar_y, bar_w, bar_h), Color(0.3, 0.35, 0.45), false, 1.0)

	var hp_str: String = "HP: %d/%d" % [cur_hp, max_hp]
	draw_string(font, Vector2(card_x + 8.0, card_y + 39.0), hp_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.9, 0.92, 0.95))

	var stats_str: String = "CA: %d  |  PM: %d  |  ATK: +%d" % [ac, pm, atk_b]
	draw_string(font, Vector2(card_x + 8.0, card_y + 54.0), stats_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.75, 0.85, 1.0))

	var tags_str: String = "Alcance: %d casa(s)" % atk_r
	if not is_hero:
		if uname.to_lower().find("voador") != -1 or uname.to_lower().find("vespa") != -1:
			tags_str += " • [Voador]"
		elif uname.to_lower().find("besouro") != -1 or uname.to_lower().find("brutamontes") != -1:
			tags_str += " • [Perfurador Cerco]"
		else:
			tags_str += " • [Enxame]"
	else:
		tags_str += " • [Guardião de Kuar-Tor]"
	draw_string(font, Vector2(card_x + 8.0, card_y + 70.0), tags_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.7, 0.75, 0.85))



func _exit_tree() -> void:
	unbind_board()
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("EventBus"):
		var eb: Node = tree.root.get_node("EventBus")
		if eb.has_signal("wall_breached") and eb.wall_breached.is_connected(_on_eventbus_wall_breached):
			eb.wall_breached.disconnect(_on_eventbus_wall_breached)
