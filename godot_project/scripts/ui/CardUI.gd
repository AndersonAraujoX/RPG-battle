# res://scripts/ui/CardUI.gd
class_name CardUI
extends Control

## Visual Control node representing an interactive card in the player's hand.
## Renders card name, badge, resource cost badges, description, and stats
## with procedural StyleBox / canvas drawing fallbacks.

signal card_selected(card: CardData, index: int)
signal card_deselected(card: CardData, index: int)
signal card_played_requested(card_data: CardData, target_zone: String)
signal card_hovered(card: CardData, index: int)
signal card_unhovered(card: CardData, index: int)

# ── Badge Palette Constants ──────────────────────────────────────────────────
const COLOR_MARCHA: Color = Color(0.15, 0.55, 0.95)       # Cyan / Azure
const COLOR_TRABALHO: Color = Color(0.20, 0.75, 0.25)     # Emerald Green
const COLOR_ESCAVACAO: Color = Color(0.95, 0.65, 0.15)    # Amber / Gold
const COLOR_COMBATE: Color = Color(0.85, 0.20, 0.20)      # Crimson Red
const COLOR_ESPECIAL: Color = Color(0.65, 0.25, 0.85)     # Arcane Purple

# ── Border Palette Constants ─────────────────────────────────────────────────
const BORDER_NORMAL: Color = Color(0.25, 0.25, 0.35, 1.0)
const BORDER_HOVERED: Color = Color(1.0, 0.85, 0.2, 1.0)
const BORDER_SELECTED: Color = Color(0.80, 0.55, 1.0, 1.0)
const BORDER_DISABLED: Color = Color(0.3, 0.3, 0.3, 0.6)

# ── State Variables ──────────────────────────────────────────────────────────
@export var card_data: CardData = null
var card_index: int = 0
var is_hovered: bool = false
var is_selected: bool = false
var is_disabled: bool = false
var target_zone: String = ""
var _pulse_timer: float = 0.0

# Internal UI subnodes
var _bg_panel: Panel = null
var _name_label: Label = null
var _badge_label: Label = null
var _cost_label: Label = null
var _art_canvas: Control = null
var _desc_label: Label = null
var _stats_label: Label = null
var _btn_play: Button = null

func _init() -> void:
	custom_minimum_size = Vector2(104.0, 146.0)
	size = custom_minimum_size
	mouse_filter = MOUSE_FILTER_STOP
	pivot_offset = custom_minimum_size / 2.0

func _ready() -> void:
	_setup_internal_nodes()
	if card_data != null:
		refresh_display()
	else:
		_update_styling()

func _process(delta: float) -> void:
	if is_hovered or is_selected:
		_pulse_timer += delta
		queue_redraw()
		if _art_canvas != null:
			_art_canvas.queue_redraw()

## Sets up procedural UI hierarchy
func _setup_internal_nodes() -> void:
	if _bg_panel != null:
		return
	
	_bg_panel = Panel.new()
	_bg_panel.name = "Background"
	_bg_panel.mouse_filter = MOUSE_FILTER_IGNORE
	_bg_panel.set_anchors_preset(PRESET_FULL_RECT)
	add_child(_bg_panel)
	
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.name = "Layout"
	vbox.mouse_filter = MOUSE_FILTER_IGNORE
	vbox.set_anchors_preset(PRESET_FULL_RECT)
	vbox.offset_left = 5.0
	vbox.offset_top = 5.0
	vbox.offset_right = -5.0
	vbox.offset_bottom = -5.0
	vbox.add_theme_constant_override("separation", 2)
	_bg_panel.add_child(vbox)
	
	_badge_label = Label.new()
	_badge_label.name = "BadgeLabel"
	_badge_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_badge_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_badge_label.add_theme_font_size_override("font_size", 9)
	_badge_label.custom_minimum_size = Vector2(0, 16)
	_badge_label.text = "[MARCHA]"
	vbox.add_child(_badge_label)
	
	_name_label = Label.new()
	_name_label.name = "NameLabel"
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_name_label.add_theme_font_size_override("font_size", 10)
	_name_label.add_theme_color_override("font_color", Color(0.96, 0.97, 1.0))
	_name_label.text = "Carta"
	vbox.add_child(_name_label)
	
	_cost_label = Label.new()
	_cost_label.name = "CostLabel"
	_cost_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cost_label.add_theme_font_size_override("font_size", 9)
	_cost_label.add_theme_color_override("font_color", Color(1.0, 0.88, 0.45))
	_cost_label.text = ""
	vbox.add_child(_cost_label)
	
	_art_canvas = Control.new()
	_art_canvas.name = "ArtCanvas"
	_art_canvas.custom_minimum_size = Vector2(0, 24)
	_art_canvas.mouse_filter = MOUSE_FILTER_IGNORE
	_art_canvas.draw.connect(_on_art_canvas_draw)
	vbox.add_child(_art_canvas)
	
	_desc_label = Label.new()
	_desc_label.name = "DescLabel"
	_desc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_desc_label.add_theme_font_size_override("font_size", 8)
	_desc_label.add_theme_color_override("font_color", Color(0.82, 0.86, 0.94))
	_desc_label.size_flags_vertical = SIZE_EXPAND_FILL
	_desc_label.clip_text = true
	_desc_label.text = ""
	vbox.add_child(_desc_label)
	
	_stats_label = Label.new()
	_stats_label.name = "StatsLabel"
	_stats_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_stats_label.add_theme_font_size_override("font_size", 9)
	_stats_label.add_theme_color_override("font_color", Color(0.75, 0.90, 1.0))
	_stats_label.clip_text = true
	_stats_label.text = ""
	vbox.add_child(_stats_label)

	_btn_play = Button.new()
	_btn_play.name = "BtnPlay"
	_btn_play.text = "▶ ATIVAR"
	_btn_play.custom_minimum_size = Vector2(0, 22)
	_btn_play.add_theme_font_size_override("font_size", 9)
	_btn_play.focus_mode = Control.FOCUS_NONE
	_btn_play.mouse_filter = Control.MOUSE_FILTER_STOP
	_btn_play.pressed.connect(func(): request_play())
	vbox.add_child(_btn_play)
	
	_update_styling()

## Binds card data and updates visual representation
func setup(data: CardData, index: int = 0) -> void:
	card_data = data
	card_index = index
	if data != null and not data.target_zone.is_empty():
		target_zone = data.target_zone
	refresh_display()

## Refreshes text and styles from current card_data
func refresh_display() -> void:
	if _bg_panel == null:
		_setup_internal_nodes()
	
	if card_data == null:
		if _name_label != null: _name_label.text = ""
		if _badge_label != null: _badge_label.text = ""
		if _cost_label != null: _cost_label.text = ""
		if _desc_label != null: _desc_label.text = ""
		if _stats_label != null: _stats_label.text = ""
		_update_styling()
		return
	
	var cname: String = card_data.card_name if not card_data.card_name.is_empty() else card_data.id
	if _name_label != null:
		_name_label.text = cname
	
	var badge_str: String = card_data.badge if not card_data.badge.is_empty() else CardData.BADGE_MARCHA
	var glyph: String = ""
	match badge_str.to_upper():
		CardData.BADGE_MARCHA: glyph = "⚡ "
		CardData.BADGE_TRABALHO: glyph = "★ "
		CardData.BADGE_ESCAVACAO: glyph = "✦ "
		CardData.BADGE_COMBATE: glyph = "⚔ "
		CardData.BADGE_ESPECIAL, CardData.TYPE_UPGRADE: glyph = "✦ "
	if _badge_label != null:
		_badge_label.text = "[%s%s]" % [glyph, badge_str.to_upper()]
	
	# Format costs: Wood (MAD), Leather (COU), Metal (MET), Crystal (CRI), AP
	var costs: Array[String] = []
	if card_data.cost_wood > 0: costs.append("MAD:%d" % card_data.cost_wood)
	if card_data.cost_leather > 0: costs.append("COU:%d" % card_data.cost_leather)
	if card_data.cost_metal > 0: costs.append("MET:%d" % card_data.cost_metal)
	if card_data.cost_crystal > 0: costs.append("CRI:%d" % card_data.cost_crystal)
	if card_data.cost_ap > 0: costs.append("AP:%d" % card_data.cost_ap)
	
	if _cost_label != null:
		_cost_label.text = " ".join(costs) if not costs.is_empty() else "GRÁTIS"
	
	if _desc_label != null:
		_desc_label.text = card_data.description
	
	# Stats pills (Movement, Work, Excavation)
	var stats: Array[String] = []
	if card_data.movement > 0: stats.append("+%d MOV" % card_data.movement)
	if card_data.work > 0: stats.append("+%d TRAB" % card_data.work)
	if card_data.excavation > 0: stats.append("+%d ESC" % card_data.excavation)
	
	if _stats_label != null:
		_stats_label.text = " | ".join(stats)
	
	_update_styling()

## Updates procedural StyleBox colors based on badge, hover, selection and disabled states
func _update_styling() -> void:
	if _bg_panel == null:
		return
	
	var badge_col: Color = get_badge_color()
	var border_col: Color = BORDER_NORMAL
	
	if is_disabled:
		border_col = BORDER_DISABLED
		modulate = Color(0.65, 0.65, 0.65, 1.0)
	elif is_selected:
		border_col = BORDER_SELECTED
		modulate = Color(1.0, 1.0, 1.0, 1.0)
	elif is_hovered:
		border_col = BORDER_HOVERED
		modulate = Color(1.06, 1.06, 1.06, 1.0)
	else:
		border_col = BORDER_NORMAL
		modulate = Color(1.0, 1.0, 1.0, 1.0)
	
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.09, 0.10, 0.15, 0.98)
	style.border_color = border_col
	style.set_border_width_all(2 if (is_hovered or is_selected) else 1)
	style.set_corner_radius_all(7)
	style.shadow_size = 6 if is_selected else (4 if is_hovered else 2)
	style.shadow_color = Color(0.0, 0.0, 0.0, 0.55)
	style.shadow_offset = Vector2(0, 2)
	_bg_panel.add_theme_stylebox_override("panel", style)
	
	if _badge_label != null:
		var b_box: StyleBoxFlat = StyleBoxFlat.new()
		b_box.bg_color = Color(badge_col.r * 0.35, badge_col.g * 0.35, badge_col.b * 0.35, 0.85)
		b_box.border_color = badge_col
		b_box.set_border_width_all(1)
		b_box.set_corner_radius_all(4)
		_badge_label.add_theme_stylebox_override("normal", b_box)
		_badge_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))

	if _desc_label != null:
		var d_box: StyleBoxFlat = StyleBoxFlat.new()
		d_box.bg_color = Color(0.05, 0.06, 0.09, 0.65)
		d_box.border_color = Color(0.22, 0.26, 0.36, 0.5)
		d_box.set_border_width_all(1)
		d_box.set_corner_radius_all(3)
		d_box.content_margin_left = 3.0
		d_box.content_margin_right = 3.0
		d_box.content_margin_top = 2.0
		d_box.content_margin_bottom = 2.0
		_desc_label.add_theme_stylebox_override("normal", d_box)

	if _btn_play != null:
		var pstyle: StyleBoxFlat = StyleBoxFlat.new()
		pstyle.set_corner_radius_all(4)
		if is_disabled:
			pstyle.bg_color = Color(0.12, 0.13, 0.16, 0.6)
			pstyle.border_color = Color(0.25, 0.25, 0.3, 0.4)
			pstyle.set_border_width_all(1)
			_btn_play.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
			_btn_play.text = "▶ BLOQUEADA"
		elif is_selected:
			pstyle.bg_color = Color(0.18, 0.72, 0.38, 0.95)
			pstyle.border_color = Color(0.7, 1.0, 0.8, 1.0)
			pstyle.set_border_width_all(1)
			_btn_play.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
			_btn_play.text = "▶ ATIVAR AGORA"
		elif is_hovered:
			pstyle.bg_color = Color(0.22, 0.52, 0.95, 0.95)
			pstyle.border_color = Color(1.0, 0.88, 0.35, 1.0)
			pstyle.set_border_width_all(1)
			_btn_play.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
			_btn_play.text = "▶ ATIVAR"
		else:
			pstyle.bg_color = Color(0.16, 0.22, 0.34, 0.95)
			pstyle.border_color = Color(0.32, 0.45, 0.68, 0.8)
			pstyle.set_border_width_all(1)
			_btn_play.add_theme_color_override("font_color", Color(0.92, 0.96, 1.0))
			_btn_play.text = "▶ ATIVAR"
		_btn_play.add_theme_stylebox_override("normal", pstyle)
		_btn_play.add_theme_stylebox_override("hover", pstyle)
		_btn_play.add_theme_stylebox_override("pressed", pstyle)

## Returns the theme color mapped to current card badge
func get_badge_color() -> Color:
	if card_data == null:
		return COLOR_MARCHA
	match card_data.badge.to_upper():
		CardData.BADGE_MARCHA:
			return COLOR_MARCHA
		CardData.BADGE_TRABALHO:
			return COLOR_TRABALHO
		CardData.BADGE_ESCAVACAO:
			return COLOR_ESCAVACAO
		CardData.BADGE_COMBATE:
			return COLOR_COMBATE
		CardData.BADGE_ESPECIAL, CardData.TYPE_UPGRADE:
			return COLOR_ESPECIAL
		_:
			return COLOR_MARCHA

## Sets hovered state and updates visuals
func set_hovered(hovered: bool) -> void:
	if is_hovered == hovered:
		return
	is_hovered = hovered
	_update_styling()
	if is_hovered:
		card_hovered.emit(card_data, card_index)
	else:
		card_unhovered.emit(card_data, card_index)

## Sets selected state and updates visuals
func set_selected(selected: bool) -> void:
	if is_selected == selected:
		return
	is_selected = selected
	_update_styling()
	if is_selected:
		card_selected.emit(card_data, card_index)
	else:
		card_deselected.emit(card_data, card_index)

## Sets disabled state (e.g. unaffordable card)
func set_disabled(disabled: bool) -> void:
	is_disabled = disabled
	_update_styling()

## Requests playing this card
func request_play(tz: String = "") -> void:
	if is_disabled:
		return
	var final_zone: String = tz if not tz.is_empty() else target_zone
	card_played_requested.emit(card_data, final_zone)
	if is_inside_tree():
		var tw: Tween = create_tween()
		if tw != null:
			tw.tween_property(self, "scale", Vector2(1.15, 1.15), 0.08)
			tw.tween_property(self, "modulate", Color(1.3, 1.3, 1.1, 0.4), 0.08)
			tw.tween_callback(func():
				modulate = Color.WHITE
				scale = Vector2.ONE
			)

## Direct convenience trigger to play this card immediately
func play_now(tz: String = "") -> void:
	request_play(tz)

## Input handling for mouse clicks and hover
func _gui_input(event: InputEvent) -> void:
	if is_disabled:
		return
	
	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			if mb.double_click or is_selected:
				# Double click OR click on an already-selected card activates it immediately!
				request_play()
			else:
				# First click selects the card in hand
				set_selected(true)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			if is_selected:
				set_selected(false)
				accept_event()

func _notification(what: int) -> void:
	match what:
		NOTIFICATION_MOUSE_ENTER:
			set_hovered(true)
		NOTIFICATION_MOUSE_EXIT:
			set_hovered(false)

# ── 1. Ilustração do Arquétipo no Centro da Carta ────────────────────────────
func _on_art_canvas_draw() -> void:
	if _art_canvas == null:
		return
	var c_sz: Vector2 = _art_canvas.size
	if c_sz.x <= 0 or c_sz.y <= 0:
		return

	var art_rect: Rect2 = Rect2(0, 0, c_sz.x, c_sz.y)
	_art_canvas.draw_rect(art_rect, Color(0.06, 0.07, 0.11, 0.95), true)
	var badge_col: Color = get_badge_color()
	_art_canvas.draw_rect(art_rect, Color(badge_col.r * 0.5, badge_col.g * 0.5, badge_col.b * 0.5, 0.7), false, 1.0)

	var cx: float = c_sz.x * 0.5
	var cy: float = c_sz.y * 0.5
	var b_str: String = card_data.badge.to_upper() if card_data != null else "MARCHA"

	match b_str:
		CardData.BADGE_ESCAVACAO:
			# Picareta de Mineração Anã com cabo de madeira e lâmina de aço/ouro
			var pick_col: Color = Color(1.0, 0.82, 0.25)
			_art_canvas.draw_line(Vector2(cx - 9, cy + 7), Vector2(cx + 7, cy - 7), Color(0.48, 0.28, 0.14), 2.0)
			_art_canvas.draw_polyline(PackedVector2Array([
				Vector2(cx + 1, cy - 10),
				Vector2(cx + 7, cy - 7),
				Vector2(cx + 11, cy - 1)
			]), Color(0.85, 0.88, 0.95), 2.5)
			_art_canvas.draw_circle(Vector2(cx + 11, cy - 1), 1.5, pick_col)
			_art_canvas.draw_circle(Vector2(cx - 7, cy + 6), 2.0, Color(0.85, 0.45, 1.0, 0.9))

		CardData.BADGE_TRABALHO:
			# Bigorna de Forja de Kuar-Tor com martelo e faíscas
			var iron_col: Color = Color(0.55, 0.60, 0.70)
			_art_canvas.draw_rect(Rect2(cx - 7, cy + 2, 14, 5), Color(0.25, 0.28, 0.35), true)
			_art_canvas.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 10, cy - 4),
				Vector2(cx + 8, cy - 4),
				Vector2(cx + 5, cy + 2),
				Vector2(cx - 5, cy + 2)
			]), iron_col)
			_art_canvas.draw_line(Vector2(cx - 10, cy - 4), Vector2(cx - 13, cy - 2), iron_col, 2.0)
			_art_canvas.draw_circle(Vector2(cx + 2, cy - 6), 1.5, Color(1.0, 0.85, 0.2))

		CardData.BADGE_COMBATE:
			# Espada Anã Flamejante com labaredas ardentes
			var blade_col: Color = Color(0.95, 0.95, 1.0)
			_art_canvas.draw_line(Vector2(cx - 8, cy + 6), Vector2(cx + 8, cy - 6), blade_col, 2.0)
			_art_canvas.draw_line(Vector2(cx - 11, cy + 3), Vector2(cx - 5, cy + 9), Color(0.85, 0.70, 0.2), 2.0)
			var flame_flicker: float = sin(_pulse_timer * 8.0) * 1.5
			_art_canvas.draw_circle(Vector2(cx, cy - 1 + flame_flicker), 3.0, Color(1.0, 0.35, 0.15, 0.8))
			_art_canvas.draw_circle(Vector2(cx + 4, cy - 4), 2.0, Color(1.0, 0.85, 0.25, 0.9))

		CardData.BADGE_MARCHA:
			# Bota Alada / Asas Velozes
			var wing_col: Color = Color(0.35, 0.75, 1.0)
			_art_canvas.draw_polyline(PackedVector2Array([
				Vector2(cx - 11, cy - 3),
				Vector2(cx - 4, cy - 7),
				Vector2(cx, cy)
			]), wing_col, 2.0)
			_art_canvas.draw_polyline(PackedVector2Array([
				Vector2(cx + 11, cy - 3),
				Vector2(cx + 4, cy - 7),
				Vector2(cx, cy)
			]), wing_col, 2.0)
			_art_canvas.draw_circle(Vector2(cx, cy), 2.5, Color(1.0, 0.88, 0.35))
			_art_canvas.draw_line(Vector2(cx - 7, cy + 5), Vector2(cx + 7, cy + 5), Color(0.7, 0.9, 1.0, 0.6), 1.0)

		_:
			# Orbe Místico Rúnico com anéis de energia giratórios
			var rune_pulse: float = 1.0 + 0.2 * sin(_pulse_timer * 5.0)
			_art_canvas.draw_circle(Vector2(cx, cy), 6.0 * rune_pulse, Color(0.65, 0.25, 0.95, 0.35))
			_art_canvas.draw_circle(Vector2(cx, cy), 4.0, Color(0.85, 0.45, 1.0, 0.95))
			_art_canvas.draw_circle(Vector2(cx, cy), 1.5, Color(1.0, 1.0, 1.0))

# ── 2. Moldura Dark Fantasy com Rebites e Brilho Rúnico ao Jogar ─────────────
func _draw() -> void:
	var c_w: float = size.x
	var c_h: float = size.y
	if c_w <= 0 or c_h <= 0:
		return

	var rivet_col: Color = Color(0.75, 0.65, 0.45, 0.95)
	if is_selected:
		rivet_col = Color(1.0, 0.88, 0.35, 1.0)
	elif is_hovered:
		rivet_col = Color(0.95, 0.82, 0.40, 0.95)

	# Rebites metálicos nos 4 cantos
	var r_margin: float = 4.0
	var rivets: Array[Vector2] = [
		Vector2(r_margin, r_margin),
		Vector2(c_w - r_margin, r_margin),
		Vector2(r_margin, c_h - r_margin),
		Vector2(c_w - r_margin, c_h - r_margin)
	]
	for rv in rivets:
		draw_circle(rv, 1.8, Color(0.12, 0.12, 0.15, 0.9))
		draw_circle(rv + Vector2(-0.4, -0.4), 1.2, rivet_col)

	# Brilho rúnico dourado / arcano ao selecionar ou hover
	if is_selected or is_hovered:
		var p_alpha: float = 0.45 + 0.35 * sin(_pulse_timer * 6.0)
		var glow_col: Color = Color(1.0, 0.85, 0.25, p_alpha) if is_selected else Color(0.4, 0.8, 1.0, p_alpha * 0.7)
		draw_rect(Rect2(1, 1, c_w - 2, c_h - 2), glow_col, false, 1.5)
