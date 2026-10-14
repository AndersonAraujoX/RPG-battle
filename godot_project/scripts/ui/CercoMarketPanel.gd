# res://scripts/ui/CercoMarketPanel.gd
class_name CercoMarketPanel
extends Control

## CercoMarketPanel: Painel Lateral Direito do Cerco contra Isectum.
## Renderiza os Recursos Depositados ([W] MAD, [L] COU, [I] MET), Barra de Capacidade do Deck,
## o Mercado de 5 Cartas de Upgrades com custos em barras, o Log de Combate e o botão Encerrar Turno.

signal upgrade_purchased(card_id: String)
signal end_turn_requested()

const DEFAULT_MARKET_CARDS: Array[Dictionary] = [
	{
		"id": "plano_tatico",
		"nome": "Plano Tático",
		"stats": "+4TRAB",
		"custo": {"madeira": 1, "couro": 2, "metal": 0},
		"cor": Color(0.85, 0.8, 0.3)
	},
	{
		"id": "mestre_artesao",
		"nome": "Mestre Artesão",
		"stats": "+5TRAB +1carta",
		"custo": {"madeira": 2, "couro": 1, "metal": 0},
		"cor": Color(0.85, 0.8, 0.3)
	},
	{
		"id": "corrida_livre",
		"nome": "Corrida Livre",
		"stats": "+30MOV",
		"custo": {"madeira": 0, "couro": 2, "metal": 1},
		"cor": Color(0.85, 0.8, 0.3)
	},
	{
		"id": "perfurador",
		"nome": "Perfurador",
		"stats": "+5ESC",
		"custo": {"madeira": 1, "couro": 0, "metal": 2},
		"cor": Color(0.85, 0.8, 0.3)
	},
	{
		"id": "explorador",
		"nome": "Explorador",
		"stats": "+25MOV +3TRAB +4ESC",
		"custo": {"madeira": 2, "couro": 2, "metal": 0},
		"cor": Color(0.75, 0.75, 0.85)
	}
]

var wood: int = 0
var leather: int = 0
var metal: int = 0

var deck_current: int = 12
var deck_max: int = 12

var market_cards: Array[Dictionary] = []

# Child Node references
var lbl_mad: Label = null
var lbl_cou: Label = null
var lbl_met: Label = null
var lbl_deck_size: Label = null
var deck_progress_bar: ProgressBar = null
var cards_vbox: VBoxContainer = null
var combat_log: CombatLog = null
var btn_end_turn: Button = null

func _init() -> void:
	custom_minimum_size = Vector2(300.0, 640.0)
	size = custom_minimum_size
	mouse_filter = MOUSE_FILTER_PASS

func _ready() -> void:
	market_cards = DEFAULT_MARKET_CARDS.duplicate(true)
	_setup_ui()
	refresh_display()

func _setup_ui() -> void:
	for child in get_children():
		child.queue_free()
	
	# Background Panel
	var bg: PanelContainer = PanelContainer.new()
	bg.name = "Background"
	bg.set_anchors_preset(PRESET_FULL_RECT)
	var bg_style: StyleBoxFlat = StyleBoxFlat.new()
	bg_style.bg_color = Color(0.05, 0.06, 0.12, 0.95)
	bg_style.border_width_left = 1
	bg_style.border_width_top = 1
	bg_style.border_width_right = 1
	bg_style.border_width_bottom = 1
	bg_style.border_color = Color(0.18, 0.20, 0.32, 1.0)
	bg_style.set_corner_radius_all(8)
	bg.add_theme_stylebox_override("panel", bg_style)
	add_child(bg)
	
	var main_vbox: VBoxContainer = VBoxContainer.new()
	main_vbox.set_anchors_preset(PRESET_FULL_RECT)
	main_vbox.offset_left = 10
	main_vbox.offset_top = 8
	main_vbox.offset_right = -10
	main_vbox.offset_bottom = -8
	main_vbox.add_theme_constant_override("separation", 8)
	bg.add_child(main_vbox)
	
	# ── 1. Recursos Depositados ─────────────────────────────────────────────
	var res_hbox: HBoxContainer = HBoxContainer.new()
	res_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	res_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(res_hbox)
	
	lbl_mad = _create_resource_box("[W] MAD", Color(0.4, 0.8, 0.35), res_hbox)
	lbl_cou = _create_resource_box("[L] COU", Color(0.85, 0.6, 0.25), res_hbox)
	lbl_met = _create_resource_box("[I] MET", Color(0.65, 0.75, 0.95), res_hbox)
	
	# ── 2. Deck Size Progress ───────────────────────────────────────────────
	var deck_info_box: VBoxContainer = VBoxContainer.new()
	deck_info_box.add_theme_constant_override("separation", 2)
	main_vbox.add_child(deck_info_box)
	
	lbl_deck_size = Label.new()
	lbl_deck_size.text = "Deck: 12/12 cartas"
	lbl_deck_size.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_deck_size.add_theme_font_size_override("font_size", 12)
	lbl_deck_size.add_theme_color_override("font_color", Color(0.3, 0.9, 0.45))
	deck_info_box.add_child(lbl_deck_size)
	
	deck_progress_bar = ProgressBar.new()
	deck_progress_bar.custom_minimum_size = Vector2(0, 6)
	deck_progress_bar.max_value = 12
	deck_progress_bar.value = 12
	deck_progress_bar.show_percentage = false
	var pb_style: StyleBoxFlat = StyleBoxFlat.new()
	pb_style.bg_color = Color(0.2, 0.8, 0.3)
	pb_style.set_corner_radius_all(3)
	deck_progress_bar.add_theme_stylebox_override("fill", pb_style)
	deck_info_box.add_child(deck_progress_bar)
	
	# Separator
	var sep1: HSeparator = HSeparator.new()
	main_vbox.add_child(sep1)
	
	# ── 3. >> MERCADO << ───────────────────────────────────────────────────
	var lbl_market_title: Label = Label.new()
	lbl_market_title.text = ">> MERCADO <<"
	lbl_market_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_market_title.add_theme_font_size_override("font_size", 14)
	lbl_market_title.add_theme_color_override("font_color", Color(0.75, 0.5, 1.0))
	main_vbox.add_child(lbl_market_title)
	
	cards_vbox = VBoxContainer.new()
	cards_vbox.add_theme_constant_override("separation", 6)
	main_vbox.add_child(cards_vbox)
	_build_market_cards()
	
	# ── 4. Log de Combate ──────────────────────────────────────────────────
	combat_log = CombatLog.new()
	combat_log.name = "CombatLog"
	combat_log.bbcode_enabled = true
	combat_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	combat_log.custom_minimum_size = Vector2(0, 90)
	var log_style: StyleBoxFlat = StyleBoxFlat.new()
	log_style.bg_color = Color(0.03, 0.035, 0.06, 0.95)
	log_style.border_width_left = 1
	log_style.border_width_top = 1
	log_style.border_width_right = 1
	log_style.border_width_bottom = 1
	log_style.border_color = Color(0.12, 0.14, 0.22, 1.0)
	log_style.set_corner_radius_all(4)
	combat_log.add_theme_stylebox_override("normal", log_style)
	combat_log.add_theme_font_size_override("normal_font_size", 11)
	main_vbox.add_child(combat_log)
	
	# Linhas iniciais idênticas à ambientação dark fantasy
	combat_log.log_message("[color=#8899aa][o] Round 1 — Defensores: planejem suas cartas![/color]")
	combat_log.log_message("[color=#8899aa][o] Cerco contra Isectum iniciado em Kuar-Tor.[/color]")
	combat_log.log_message("[color=#8899aa][o] Dificuldade: Média (Deck de Ameaça: 24 cartas)[/color]")
	
	# ── 5. Botão Encerrar Turno ───────────────────────────────────────────
	btn_end_turn = Button.new()
	btn_end_turn.name = "BtnEndTurn"
	btn_end_turn.text = "Encerrar Turno  [Ent]"
	btn_end_turn.custom_minimum_size = Vector2(0, 36)
	btn_end_turn.focus_mode = Control.FOCUS_NONE
	var btn_style: StyleBoxFlat = StyleBoxFlat.new()
	btn_style.bg_color = Color(0.35, 0.12, 0.12, 0.95)
	btn_style.border_width_left = 1
	btn_style.border_width_top = 1
	btn_style.border_width_right = 1
	btn_style.border_width_bottom = 1
	btn_style.border_color = Color(0.8, 0.25, 0.25, 1.0)
	btn_style.set_corner_radius_all(6)
	btn_end_turn.add_theme_stylebox_override("normal", btn_style)
	btn_end_turn.add_theme_color_override("font_color", Color(1.0, 0.9, 0.9))
	btn_end_turn.add_theme_font_size_override("font_size", 13)
	btn_end_turn.pressed.connect(_on_end_turn_pressed)
	main_vbox.add_child(btn_end_turn)

func _create_resource_box(label_text: String, border_color: Color, parent: HBoxContainer) -> Label:
	var box: PanelContainer = PanelContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.custom_minimum_size = Vector2(75, 42)
	
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.06, 0.07, 0.14, 0.9)
	style.border_width_left = 1
	style.border_width_top = 1
	style.border_width_right = 1
	style.border_width_bottom = 1
	style.border_color = border_color
	style.set_corner_radius_all(5)
	box.add_theme_stylebox_override("panel", style)
	
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_theme_constant_override("separation", 2)
	box.add_child(vbox)
	
	var lbl_tag: Label = Label.new()
	lbl_tag.text = label_text
	lbl_tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_tag.add_theme_font_size_override("font_size", 10)
	lbl_tag.add_theme_color_override("font_color", border_color)
	vbox.add_child(lbl_tag)
	
	var lbl_val: Label = Label.new()
	lbl_val.text = "0"
	lbl_val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_val.add_theme_font_size_override("font_size", 14)
	lbl_val.add_theme_color_override("font_color", Color(0.9, 0.9, 0.95))
	vbox.add_child(lbl_val)
	
	parent.add_child(box)
	return lbl_val

func _build_market_cards() -> void:
	if cards_vbox == null:
		return
	for child in cards_vbox.get_children():
		child.queue_free()
	
	for card in market_cards:
		var panel: PanelContainer = PanelContainer.new()
		panel.custom_minimum_size = Vector2(0, 52)
		
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color(0.06, 0.07, 0.13, 0.9)
		style.border_width_left = 1
		style.border_width_top = 1
		style.border_width_right = 1
		style.border_width_bottom = 1
		style.border_color = card.get("cor", Color(0.8, 0.75, 0.3))
		style.set_corner_radius_all(6)
		panel.add_theme_stylebox_override("panel", style)
		
		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.offset_left = 6
		vbox.offset_top = 4
		vbox.offset_right = -6
		vbox.offset_bottom = -4
		vbox.add_theme_constant_override("separation", 2)
		panel.add_child(vbox)
		
		var lbl_name: Label = Label.new()
		lbl_name.text = card.get("nome", "")
		lbl_name.add_theme_font_size_override("font_size", 12)
		lbl_name.add_theme_color_override("font_color", Color(0.95, 0.95, 1.0))
		vbox.add_child(lbl_name)
		
		var lbl_stats: Label = Label.new()
		lbl_stats.text = card.get("stats", "")
		lbl_stats.add_theme_font_size_override("font_size", 10)
		lbl_stats.add_theme_color_override("font_color", Color(0.55, 0.95, 0.6))
		vbox.add_child(lbl_stats)
		
		# Custo em linha com tags [W], [L], [I]
		var hbox_cost: HBoxContainer = HBoxContainer.new()
		hbox_cost.add_theme_constant_override("separation", 8)
		vbox.add_child(hbox_cost)
		
		var custo: Dictionary = card.get("custo", {})
		if custo.get("madeira", 0) > 0:
			var req_w: int = int(custo["madeira"])
			var cur_w: int = mini(wood, req_w)
			var l_w: Label = Label.new()
			l_w.text = "[W] %d/%d" % [cur_w, req_w]
			l_w.add_theme_font_size_override("font_size", 9)
			l_w.add_theme_color_override("font_color", Color(0.4, 0.8, 0.35) if cur_w >= req_w else Color(0.7, 0.7, 0.7))
			hbox_cost.add_child(l_w)
		
		if custo.get("couro", 0) > 0:
			var req_l: int = int(custo["couro"])
			var cur_l: int = mini(leather, req_l)
			var l_l: Label = Label.new()
			l_l.text = "[L] %d/%d" % [cur_l, req_l]
			l_l.add_theme_font_size_override("font_size", 9)
			l_l.add_theme_color_override("font_color", Color(0.85, 0.6, 0.25) if cur_l >= req_l else Color(0.7, 0.7, 0.7))
			hbox_cost.add_child(l_l)
		
		if custo.get("metal", 0) > 0:
			var req_m: int = int(custo["metal"])
			var cur_m: int = mini(metal, req_m)
			var l_m: Label = Label.new()
			l_m.text = "[I] %d/%d" % [cur_m, req_m]
			l_m.add_theme_font_size_override("font_size", 9)
			l_m.add_theme_color_override("font_color", Color(0.65, 0.75, 0.95) if cur_m >= req_m else Color(0.7, 0.7, 0.7))
			hbox_cost.add_child(l_m)
		
		var btn: Button = Button.new()
		btn.flat = true
		btn.set_anchors_preset(PRESET_FULL_RECT)
		var cid: String = card.get("id", "")
		btn.pressed.connect(_on_card_clicked.bind(cid))
		panel.add_child(btn)
		
		cards_vbox.add_child(panel)

func update_resources(p_wood: int, p_leather: int, p_metal: int) -> void:
	wood = p_wood
	leather = p_leather
	metal = p_metal
	refresh_display()
	_build_market_cards()

func set_deck_capacity(current: int, max_c: int) -> void:
	deck_current = current
	deck_max = max(1, max_c)
	refresh_display()

func refresh_display() -> void:
	if lbl_mad != null:
		lbl_mad.text = str(wood)
	if lbl_cou != null:
		lbl_cou.text = str(leather)
	if lbl_met != null:
		lbl_met.text = str(metal)
	if lbl_deck_size != null:
		lbl_deck_size.text = "Deck: %d/%d cartas" % [deck_current, deck_max]
	if deck_progress_bar != null:
		deck_progress_bar.max_value = deck_max
		deck_progress_bar.value = deck_current

func _on_card_clicked(card_id: String) -> void:
	upgrade_purchased.emit(card_id)

func _on_end_turn_pressed() -> void:
	end_turn_requested.emit()
