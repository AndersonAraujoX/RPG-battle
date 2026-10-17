# res://scripts/ui/HUD.gd
class_name HUD
extends CanvasLayer

## Master HUD Controller for Cerco da Fortaleza contra Isectum.
## Coordinates ResourceScoreboard, FortressBoardView, CombatLog, and CardFanContainer.
## Supports production Autoload EventBus wiring and hermetic dependency injection for testing.

signal card_played(player_id: String, card_id: String, target_zone: String)
signal card_selected(card: CardData, index: int)
signal sync_round_requested()
signal sound_played(sound_name: String)
signal autoplay_toggled(active: bool)

# ── Child Component References ───────────────────────────────────────────────
@export var scoreboard_path: NodePath
@export var board_view_path: NodePath
@export var combat_log_path: NodePath
@export var card_fan_path: NodePath
@export var market_panel_path: NodePath

var scoreboard: ResourceScoreboard = null
var board_view: FortressBoardView = null
var combat_log: CombatLog = null
var card_fan: CardFanContainer = null
var market_panel: CercoMarketPanel = null

var btn_menu: Button = null
var btn_options: Button = null
var btn_autoplay: Button = null
var autoplay_active: bool = false
var btn_move: Button = null
var btn_work: Button = null
var btn_excavate: Button = null
var btn_bribe: Button = null
var btn_attack: Button = null
var btn_shoot: Button = null
var _options_modal: OptionsMenu = null

var lbl_deck_ini_count: Label = null
var lbl_baralho_count: Label = null
var banner_title: Label = null
var banner_subtitle: Label = null
var hero_avatar_icon: TextureRect = null
var avatar_badge: Label = null
var hero_stats: Label = null

# ── Bound Model References (Hermetic Testing) ────────────────────────────────
var _bound_board: Object = null
var _bound_economy: Object = null
var _bound_deck: Object = null
var _bound_judge: Object = null
var _bound_sync_round: Object = null

func _ready() -> void:
	_resolve_subcomponents()
	_wire_subcomponents()
	_connect_event_bus()

## Resolves child components from paths or node searches, creating procedural fallbacks if needed
func _resolve_subcomponents() -> void:
	if scoreboard_path and has_node(scoreboard_path):
		scoreboard = get_node(scoreboard_path) as ResourceScoreboard
	elif find_child("ResourceScoreboard", true, false) != null:
		scoreboard = find_child("ResourceScoreboard", true, false) as ResourceScoreboard
	elif scoreboard == null:
		scoreboard = ResourceScoreboard.new()
		scoreboard.name = "ResourceScoreboard"
		add_child(scoreboard)
	
	if board_view_path and has_node(board_view_path):
		board_view = get_node(board_view_path) as FortressBoardView
	elif find_child("FortressBoardView", true, false) != null:
		board_view = find_child("FortressBoardView", true, false) as FortressBoardView
	elif board_view == null:
		board_view = FortressBoardView.new()
		board_view.name = "FortressBoardView"
		add_child(board_view)
	
	if combat_log_path and has_node(combat_log_path):
		combat_log = get_node(combat_log_path) as CombatLog
	elif find_child("CombatLog", true, false) != null:
		combat_log = find_child("CombatLog", true, false) as CombatLog
	elif combat_log == null:
		combat_log = CombatLog.new()
		combat_log.name = "CombatLog"
		add_child(combat_log)
	
	if card_fan_path and has_node(card_fan_path):
		card_fan = get_node(card_fan_path) as CardFanContainer
	elif find_child("CardFanContainer", true, false) != null:
		card_fan = find_child("CardFanContainer", true, false) as CardFanContainer
	elif card_fan == null:
		card_fan = CardFanContainer.new()
		card_fan.name = "CardFanContainer"
		add_child(card_fan)
	
	if market_panel_path and has_node(market_panel_path):
		market_panel = get_node(market_panel_path) as CercoMarketPanel
	elif find_child("CercoMarketPanel", true, false) != null:
		market_panel = find_child("CercoMarketPanel", true, false) as CercoMarketPanel
	
	btn_menu = find_child("BtnMenu", true, false) as Button
	btn_options = find_child("BtnOptions", true, false) as Button
	btn_autoplay = find_child("BtnAutoPlay", true, false) as Button
	btn_move = find_child("BtnMove", true, false) as Button
	btn_work = find_child("BtnWork", true, false) as Button
	btn_excavate = find_child("BtnExcavate", true, false) as Button
	btn_bribe = find_child("BtnBribe", true, false) as Button
	btn_attack = find_child("BtnAttack", true, false) as Button
	btn_shoot = find_child("BtnShoot", true, false) as Button
	
	lbl_deck_ini_count = find_child("DeckIniCount", true, false) as Label
	lbl_baralho_count = find_child("BaralhoCount", true, false) as Label
	banner_title = find_child("BannerTitle", true, false) as Label
	banner_subtitle = find_child("BannerSubtitle", true, false) as Label
	hero_avatar_icon = find_child("HeroAvatarIcon", true, false) as TextureRect
	avatar_badge = find_child("AvatarBadge", true, false) as Label
	hero_stats = find_child("HeroStats", true, false) as Label

	# Remove a barra roxa/lilás padrão do tema Godot nos containers da área de cartas.
	# O tema global injeta um StyleBox roxo em HBoxContainer/VBoxContainer sem fundo explícito;
	# sobrescrevemos com StyleBoxFlat totalmente transparente.
	_clear_container_background("CardsHBox")
	_clear_container_background("BottomArea")

## Helper: aplica StyleBoxFlat transparente para eliminar o fundo roxo padrão do tema Godot.
func _clear_container_background(node_name: String) -> void:
	var node: Control = find_child(node_name, true, false) as Control
	if node == null:
		return
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.0, 0.0, 0.0, 0.0)  # totalmente transparente
	sb.border_width_left   = 0
	sb.border_width_right  = 0
	sb.border_width_top    = 0
	sb.border_width_bottom = 0
	node.add_theme_stylebox_override("panel", sb)
	node.add_theme_stylebox_override("normal", sb)

## Wires internal subcomponent signals
func _wire_subcomponents() -> void:
	if card_fan != null:
		if not card_fan.card_selected.is_connected(_on_fan_card_selected):
			card_fan.card_selected.connect(_on_fan_card_selected)
		if not card_fan.card_played_requested.is_connected(_on_fan_card_played_requested):
			card_fan.card_played_requested.connect(_on_fan_card_played_requested)
		if not card_fan.card_hovered.is_connected(_on_fan_card_hovered):
			card_fan.card_hovered.connect(_on_fan_card_hovered)
	
	if board_view != null:
		if not board_view.zone_clicked.is_connected(_on_board_zone_clicked):
			board_view.zone_clicked.connect(_on_board_zone_clicked)
		if not board_view.wall_breach_alert.is_connected(_on_board_wall_breach_alert):
			board_view.wall_breach_alert.connect(_on_board_wall_breach_alert)
		if board_view.has_signal("unit_selected") and not board_view.unit_selected.is_connected(_on_board_unit_selected):
			board_view.unit_selected.connect(_on_board_unit_selected)
	
	if market_panel != null:
		if not market_panel.end_turn_requested.is_connected(_on_market_end_turn_requested):
			market_panel.end_turn_requested.connect(_on_market_end_turn_requested)
	
	if scoreboard != null:
		if not scoreboard.resource_display_updated.is_connected(_on_scoreboard_resource_updated):
			scoreboard.resource_display_updated.connect(_on_scoreboard_resource_updated)
	
	if btn_menu != null and not btn_menu.pressed.is_connected(_on_btn_menu_pressed):
		btn_menu.pressed.connect(_on_btn_menu_pressed)
	if btn_options != null and not btn_options.pressed.is_connected(_open_options_modal):
		btn_options.pressed.connect(_open_options_modal)
	if btn_autoplay != null and not btn_autoplay.pressed.is_connected(_on_btn_autoplay_pressed):
		btn_autoplay.pressed.connect(_on_btn_autoplay_pressed)
	_setup_autoplay_button_style()
	
	if btn_move != null and not btn_move.pressed.is_connected(_on_btn_move_pressed):
		btn_move.pressed.connect(_on_btn_move_pressed)
	if btn_work != null and not btn_work.pressed.is_connected(_on_btn_work_pressed):
		btn_work.pressed.connect(_on_btn_work_pressed)
	if btn_excavate != null and not btn_excavate.pressed.is_connected(_on_btn_excavate_pressed):
		btn_excavate.pressed.connect(_on_btn_excavate_pressed)
	if btn_bribe != null and not btn_bribe.pressed.is_connected(_on_btn_bribe_pressed):
		btn_bribe.pressed.connect(_on_btn_bribe_pressed)
	if btn_attack != null and not btn_attack.pressed.is_connected(_on_btn_attack_pressed):
		btn_attack.pressed.connect(_on_btn_attack_pressed)
	if btn_shoot != null and not btn_shoot.pressed.is_connected(_on_btn_shoot_pressed):
		btn_shoot.pressed.connect(_on_btn_shoot_pressed)

# ── EventBus Connection (Production Singleton) ──────────────────────────────
func _connect_event_bus() -> void:
	if not Engine.is_editor_hint():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("card_played") and not eb.card_played.is_connected(_on_eb_card_played):
				eb.card_played.connect(_on_eb_card_played)
			if eb.has_signal("dice_rolled") and not eb.dice_rolled.is_connected(_on_eb_dice_rolled):
				eb.dice_rolled.connect(_on_eb_dice_rolled)
			if eb.has_signal("damage_dealt") and not eb.damage_dealt.is_connected(_on_eb_damage_dealt):
				eb.damage_dealt.connect(_on_eb_damage_dealt)
			if eb.has_signal("production_completed") and not eb.production_completed.is_connected(_on_eb_production_completed):
				eb.production_completed.connect(_on_eb_production_completed)
			if eb.has_signal("wall_breached") and not eb.wall_breached.is_connected(_on_eb_wall_breached):
				eb.wall_breached.connect(_on_eb_wall_breached)
			if eb.has_signal("synergy_triggered") and not eb.synergy_triggered.is_connected(_on_eb_synergy_triggered):
				eb.synergy_triggered.connect(_on_eb_synergy_triggered)
			if eb.has_signal("supreme_synchrony_triggered") and not eb.supreme_synchrony_triggered.is_connected(_on_eb_supreme_synchrony_triggered):
				eb.supreme_synchrony_triggered.connect(_on_eb_supreme_synchrony_triggered)

# ── Dependency Injection API (Hermetic Unit Testing) ─────────────────────────
func bind_board(board: Object) -> void:
	if _bound_board != null and is_instance_valid(_bound_board):
		if _bound_board.has_signal("wall_damaged") and _bound_board.wall_damaged.is_connected(_on_model_wall_damaged):
			_bound_board.wall_damaged.disconnect(_on_model_wall_damaged)
		if _bound_board.has_signal("wall_breached") and _bound_board.wall_breached.is_connected(_on_model_wall_breached):
			_bound_board.wall_breached.disconnect(_on_model_wall_breached)
	
	_bound_board = board
	if board_view != null:
		board_view.bind_board(_bound_board)
	
	if _bound_board != null:
		if _bound_board.has_signal("wall_damaged"):
			_bound_board.wall_damaged.connect(_on_model_wall_damaged)
		if _bound_board.has_signal("wall_breached"):
			_bound_board.wall_breached.connect(_on_model_wall_breached)

func bind_economy(economy: Object) -> void:
	if _bound_economy != null and is_instance_valid(_bound_economy):
		if _bound_economy.has_signal("resources_updated") and _bound_economy.resources_updated.is_connected(_on_model_resources_updated):
			_bound_economy.resources_updated.disconnect(_on_model_resources_updated)
	_bound_economy = economy
	if _bound_economy != null:
		if _bound_economy.has_signal("resources_updated"):
			_bound_economy.resources_updated.connect(_on_model_resources_updated)
		var w: int = int(_bound_economy.get("wood")) if "wood" in _bound_economy else 0
		var l: int = int(_bound_economy.get("leather")) if "leather" in _bound_economy else 0
		var m: int = int(_bound_economy.get("metal")) if "metal" in _bound_economy else 0
		if market_panel != null:
			market_panel.update_resources(w, l, m)
	if scoreboard != null:
		if scoreboard.has_method("bind_economy"):
			scoreboard.bind_economy(_bound_economy)

func _on_model_resources_updated(wood: int, leather: int, metal: int, _crystal: int, _ap: int) -> void:
	if market_panel != null:
		market_panel.update_resources(wood, leather, metal)
	if scoreboard != null and scoreboard.has_method("update_resources"):
		scoreboard.update_resources(wood, leather, metal, _crystal, _ap)

func bind_deck(deck: Object) -> void:
	if _bound_deck != null and is_instance_valid(_bound_deck):
		if _bound_deck.has_signal("card_drawn") and _bound_deck.card_drawn.is_connected(_on_deck_card_drawn):
			_bound_deck.card_drawn.disconnect(_on_deck_card_drawn)
		if _bound_deck.has_signal("card_played") and _bound_deck.card_played.is_connected(_on_deck_card_played):
			_bound_deck.card_played.disconnect(_on_deck_card_played)
	
	_bound_deck = deck
	if card_fan == null:
		_resolve_subcomponents()
		_wire_subcomponents()
	
	if _bound_deck != null:
		if _bound_deck.has_signal("card_drawn"):
			_bound_deck.card_drawn.connect(_on_deck_card_drawn)
		if _bound_deck.has_signal("card_played"):
			_bound_deck.card_played.connect(_on_deck_card_played)
		
		var hand_cards: Array = []
		if _bound_deck.has_method("get_hand"):
			hand_cards = _bound_deck.get_hand()
		elif "hand" in _bound_deck:
			hand_cards = _bound_deck.hand
		
		if card_fan != null and not hand_cards.is_empty():
			card_fan.set_hand(hand_cards)
		
		_update_deck_counts()

func _update_deck_counts() -> void:
	if _bound_deck == null:
		return
	var draw_count: int = 0
	if _bound_deck.has_method("get_draw_pile"):
		draw_count = _bound_deck.get_draw_pile().size()
	elif "draw_pile" in _bound_deck:
		draw_count = _bound_deck.draw_pile.size()
	
	var discard_count: int = 0
	if _bound_deck.has_method("get_discard_pile"):
		discard_count = _bound_deck.get_discard_pile().size()
	elif "discard_pile" in _bound_deck:
		discard_count = _bound_deck.discard_pile.size()
	
	var hand_count: int = card_fan.get_card_count() if card_fan != null else 0
	if lbl_baralho_count != null:
		lbl_baralho_count.text = str(draw_count)
	if lbl_deck_ini_count != null:
		lbl_deck_ini_count.text = str(draw_count + discard_count + hand_count)

func update_banner_orders(count: int, last_action_desc: String = "") -> void:
	if banner_title == null:
		banner_title = find_child("BannerTitle", true, false) as Label
	if banner_subtitle == null:
		banner_subtitle = find_child("BannerSubtitle", true, false) as Label
	
	if banner_title != null:
		banner_title.text = "[REAÇÃO] PLANEJAMENTO SIMULTÂNEO CO-OP (14s)  |  Ordens: %d" % count
	if banner_subtitle != null and not last_action_desc.is_empty():
		banner_subtitle.text = "Última ação: %s  [Pressione ESPAÇO para Executar Tática]" % last_action_desc

func bind_judge(judge: Object) -> void:
	if _bound_judge != null and is_instance_valid(_bound_judge):
		if _bound_judge.has_signal("dice_rolled") and _bound_judge.dice_rolled.is_connected(_on_judge_dice_rolled):
			_bound_judge.dice_rolled.disconnect(_on_judge_dice_rolled)
	
	_bound_judge = judge
	if _bound_judge != null and _bound_judge.has_signal("dice_rolled"):
		_bound_judge.dice_rolled.connect(_on_judge_dice_rolled)

func bind_sync_round(sync_round: Object) -> void:
	_bound_sync_round = sync_round

func unbind_all() -> void:
	if board_view != null:
		board_view.unbind_board()
	if scoreboard != null:
		scoreboard.unbind_economy()
	
	if _bound_board != null and is_instance_valid(_bound_board):
		if _bound_board.has_signal("wall_damaged") and _bound_board.wall_damaged.is_connected(_on_model_wall_damaged):
			_bound_board.wall_damaged.disconnect(_on_model_wall_damaged)
		if _bound_board.has_signal("wall_breached") and _bound_board.wall_breached.is_connected(_on_model_wall_breached):
			_bound_board.wall_breached.disconnect(_on_model_wall_breached)
	
	if _bound_deck != null and is_instance_valid(_bound_deck):
		if _bound_deck.has_signal("card_drawn") and _bound_deck.card_drawn.is_connected(_on_deck_card_drawn):
			_bound_deck.card_drawn.disconnect(_on_deck_card_drawn)
		if _bound_deck.has_signal("card_played") and _bound_deck.card_played.is_connected(_on_deck_card_played):
			_bound_deck.card_played.disconnect(_on_deck_card_played)
	
	if _bound_judge != null and is_instance_valid(_bound_judge):
		if _bound_judge.has_signal("dice_rolled") and _bound_judge.dice_rolled.is_connected(_on_judge_dice_rolled):
			_bound_judge.dice_rolled.disconnect(_on_judge_dice_rolled)
	
	_bound_board = null
	_bound_economy = null
	_bound_deck = null
	_bound_judge = null
	_bound_sync_round = null

# ── Audio Triggers ───────────────────────────────────────────────────────────
func play_sfx(sound_name: String, volume_scale: float = 1.0, pitch_scale: float = 1.0) -> void:
	sound_played.emit(sound_name)
	
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx(sound_name, volume_scale, pitch_scale)
	elif tree != null and tree.root.has_node("EventBus"):
		var eb: Node = tree.root.get_node("EventBus")
		if eb.has_signal("audio_play_sfx_requested"):
			eb.audio_play_sfx_requested.emit(sound_name, 0.0)

# ── Subcomponent Signal Handlers ─────────────────────────────────────────────
func _on_fan_card_selected(card: CardData, index: int) -> void:
	card_selected.emit(card, index)
	play_sfx("button_click", 0.7, 1.1)
	if board_view != null:
		board_view.deselect_unit()
	if banner_subtitle != null and card != null:
		var cname: String = card.card_name if not card.card_name.is_empty() else card.id
		banner_subtitle.text = "⚡ Carta Selecionada: %s  [Clique na carta/JOGAR, tecle ESPAÇO ou escolha Oficina/Muralha]" % cname

func _on_fan_card_hovered(_card: CardData, _index: int) -> void:
	play_sfx("button_click", 0.4, 1.4)

func _on_fan_card_played_requested(card_data: CardData, target_zone: String) -> void:
	var cid: String = card_data.id if card_data != null else ""
	var final_zone: String = target_zone
	if final_zone.is_empty() and card_data != null and not card_data.target_zone.is_empty():
		final_zone = card_data.target_zone
	card_played.emit("player_1", cid, final_zone)
	play_sfx("button_click", 0.9, 0.9)
	var cname: String = card_data.card_name if card_data != null else cid
	var zdesc: String = final_zone if not final_zone.is_empty() else "Fortaleza"
	if combat_log != null:
		combat_log.append_entry("CARTA ATIVADA", "⚡ Ativou %s em %s!" % [cname, zdesc])
	show_floating_text("⚡ %s ATIVADA!" % cname, Vector2(460.0, 470.0), Color(0.3, 1.0, 0.5))

## Spawns temporary floating text message for feedback
func show_floating_text(msg: String, pos: Vector2 = Vector2(-1, -1), col: Color = Color.WHITE) -> void:
	if not is_inside_tree():
		return
	var lbl: Label = Label.new()
	lbl.text = msg
	lbl.add_theme_color_override("font_color", col)
	lbl.add_theme_font_size_override("font_size", 16)
	lbl.z_index = 100
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	var actual_pos: Vector2 = pos
	if actual_pos == Vector2(-1, -1):
		actual_pos = Vector2(460.0, 470.0)
	lbl.position = actual_pos
	
	add_child(lbl)
	var tw: Tween = create_tween()
	if tw != null:
		tw.set_parallel(true)
		tw.tween_property(lbl, "position:y", actual_pos.y - 35.0, 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(lbl, "modulate:a", 0.0, 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.chain().tween_callback(lbl.queue_free)
	else:
		lbl.queue_free()

func _on_board_zone_clicked(zone_id: String) -> void:
	play_sfx("button_click", 0.6, 1.0)
	if card_fan != null and card_fan.selected_index >= 0:
		var selected_card: CardData = card_fan.get_selected_card()
		if selected_card != null:
			card_fan.play_selected_card(zone_id)
			return

func _on_board_wall_breach_alert(wall_id: String) -> void:
	play_sfx("critical_hit", 1.0, 0.7)
	if combat_log != null:
		combat_log.append_entry("BRECHA!", "Alerta de Brecha Crítica em %s!" % wall_id)

func _on_board_unit_selected(_unit_id: String, unit_data: Dictionary) -> void:
	if card_fan != null:
		card_fan.deselect_card()
	update_active_hero(unit_data)

func update_active_hero(hero_data: Dictionary) -> void:
	if hero_avatar_icon != null:
		var hero_id: String = str(hero_data.get("id", hero_data.get("name", "aquele"))).to_lower().strip_edges()
		var h_slug: String = hero_id
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
			hero_avatar_icon.texture = load(p_path) as Texture2D
	if avatar_badge != null:
		var h_class: String = str(hero_data.get("class", hero_data.get("classe", "HERÓI"))).to_upper()
		avatar_badge.text = "[ %s ]" % h_class
	if hero_stats != null:
		var h_name: String = str(hero_data.get("name", hero_data.get("nome", "Herói")))
		var cur_hp: int = int(hero_data.get("hp", hero_data.get("hp_atual", 48)))
		var max_hp: int = int(hero_data.get("max_hp", hero_data.get("hp_max", 48)))
		var atk: int = int(hero_data.get("attack_bonus", hero_data.get("ataque", 3)))
		var def: int = int(hero_data.get("ac", hero_data.get("defesa", 17)))
		var pm: int = int(hero_data.get("remaining_pm", hero_data.get("move_range", hero_data.get("pm", 3))))
		hero_stats.text = "%s   %d/%d   [ATK] +%d   [DEF] %d   [PM] %d" % [h_name, cur_hp, max_hp, atk, def, pm]
	_update_action_buttons_state(hero_data)

func _update_action_buttons_state(hero_data: Dictionary) -> void:
	var pm: int = int(hero_data.get("remaining_pm", hero_data.get("move_range", 3)))
	if btn_move != null:
		btn_move.text = "Mover [%d PM]" % pm
		if pm > 0:
			btn_move.add_theme_color_override("font_color", Color(0.45, 0.95, 1.0))
			btn_move.tooltip_text = "Mover [M]: Clique em uma célula azul no tabuleiro para mover o herói (%d PM restantes)." % pm
		else:
			btn_move.add_theme_color_override("font_color", Color(0.65, 0.65, 0.65))
			btn_move.tooltip_text = "Mover [M]: Sem PM nesta rodada. Jogue uma carta de Marcha para mover-se mais."

	if btn_attack != null:
		var atk_bonus: int = int(hero_data.get("attack_bonus", 3))
		btn_attack.text = "Atacar [+%d]" % atk_bonus
		btn_attack.tooltip_text = "Atacar [A]: Ataque um inimigo em alcance corpo a corpo (células vermelhas no tabuleiro)."

func _on_market_end_turn_requested() -> void:
	trigger_sync_round()

func _on_scoreboard_resource_updated(_type: String, _val: int) -> void:
	if market_panel != null and scoreboard != null:
		market_panel.update_resources(scoreboard.wood, scoreboard.leather, scoreboard.metal)

func _on_btn_menu_pressed() -> void:
	play_sfx("button_click", 1.0, 1.0)
	get_tree().change_scene_to_file("res://scenes/main/Menu.tscn")

func _on_btn_move_pressed() -> void:
	play_sfx("button_click", 0.8, 1.0)
	# 1. Se uma carta da mão estiver selecionada, joga a carta
	if card_fan != null and card_fan.selected_index >= 0:
		card_fan.play_selected_card()
		return

	# 2. Se houver um herói ativo/selecionado, ativa o modo de movimento tático
	var target_hero: String = ""
	if board_view != null and not board_view.selected_unit_id.is_empty():
		target_hero = board_view.selected_unit_id
	elif _bound_board != null:
		var allies: Array[String] = _bound_board.get_units_by_team("A")
		if not allies.is_empty():
			target_hero = allies[0]
			if board_view != null:
				board_view.select_unit(target_hero)

	if not target_hero.is_empty() and _bound_board != null:
		var udata: Dictionary = _bound_board.get_unit_data(target_hero)
		var pm: int = int(udata.get("remaining_pm", udata.get("move_range", 3)))
		var hname: String = str(udata.get("name", target_hero))
		if board_view != null:
			board_view.select_unit(target_hero)
		if pm > 0:
			if combat_log != null:
				combat_log.append_entry("MOVIMENTO", "🚶 %s selecionado! Clique em uma célula azul no tabuleiro para mover (%d PM)." % [hname, pm])
			return
		else:
			# Sem PM direto: tenta jogar carta de Marcha se houver
			if card_fan != null:
				var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_MARCHA)
				if played != null:
					return
			if combat_log != null:
				combat_log.append_entry("AVISO", "⚠️ %s não possui mais PM nesta rodada! Jogue uma carta de Marcha para mover-se." % hname)
			return

	# 3. Fallback: tentar carta de marcha na mão
	if card_fan != null:
		var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_MARCHA)
		if played == null and combat_log != null:
			combat_log.append_entry("AVISO", "Nenhuma carta de Marcha disponível na mão!")

func _on_btn_work_pressed() -> void:
	play_sfx("button_click", 0.8, 1.0)
	if card_fan != null and card_fan.selected_index >= 0:
		card_fan.play_selected_card("CARPINTARIA")
		return

	# Verifica se o herói está em uma oficina válida
	var current_zone: String = ""
	if board_view != null and not board_view.selected_unit_id.is_empty() and _bound_board != null:
		current_zone = _bound_board.get_unit_zone(board_view.selected_unit_id)
	if current_zone in [FortressBoard.ZONE_CARPINTARIA, FortressBoard.ZONE_FUNDICAO, FortressBoard.ZONE_CURTUME]:
		if card_fan != null:
			var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_TRABALHO, current_zone)
			if played != null:
				return
		if _bound_economy != null:
			if current_zone == FortressBoard.ZONE_CARPINTARIA:
				_bound_economy.add_resource("wood", 2)
				if combat_log != null: combat_log.append_entry("TRABALHO", "🪓 Trabalho na Carpintaria! (+2 Madeira)")
			elif current_zone == FortressBoard.ZONE_FUNDICAO:
				_bound_economy.add_resource("metal", 2)
				if combat_log != null: combat_log.append_entry("TRABALHO", "⚒️ Trabalho na Fundição! (+2 Metal)")
			elif current_zone == FortressBoard.ZONE_CURTUME:
				_bound_economy.add_resource("leather", 2)
				if combat_log != null: combat_log.append_entry("TRABALHO", "🛡️ Trabalho no Curtume! (+2 Couro)")
			return

	if card_fan != null:
		var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_TRABALHO, "CARPINTARIA")
		if played == null and combat_log != null:
			combat_log.append_entry("AVISO", "Nenhuma carta de Trabalho disponível na mão!")

func _on_btn_excavate_pressed() -> void:
	play_sfx("button_click", 0.8, 1.0)
	if card_fan != null and card_fan.selected_index >= 0:
		card_fan.play_selected_card("PATIO_CENTRAL")
		return

	var current_zone: String = ""
	if board_view != null and not board_view.selected_unit_id.is_empty() and _bound_board != null:
		current_zone = _bound_board.get_unit_zone(board_view.selected_unit_id)
	if current_zone in [FortressBoard.ZONE_PATIO_CENTRAL, FortressBoard.ZONE_CAMARA_CENTRAL]:
		if card_fan != null:
			var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_ESCAVACAO, current_zone)
			if played != null:
				return
		if _bound_economy != null:
			_bound_economy.add_resource("crystal", 1)
			if combat_log != null: combat_log.append_entry("ESCAVAÇÃO", "⛏️ Escavação bem-sucedida no Pátio! (+1 Cristal)")
			return

	if card_fan != null:
		var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_ESCAVACAO, "PATIO_CENTRAL")
		if played == null and combat_log != null:
			combat_log.append_entry("AVISO", "Nenhuma carta de Escavação disponível na mão!")

func _on_btn_attack_pressed() -> void:
	play_sfx("button_click", 0.8, 1.0)
	if card_fan != null and card_fan.selected_index >= 0:
		card_fan.play_selected_card()
		return

	var target_hero: String = ""
	if board_view != null and not board_view.selected_unit_id.is_empty():
		target_hero = board_view.selected_unit_id
	elif _bound_board != null:
		var allies: Array[String] = _bound_board.get_units_by_team("A")
		if not allies.is_empty():
			target_hero = allies[0]
			if board_view != null:
				board_view.select_unit(target_hero)

	if not target_hero.is_empty() and _bound_board != null:
		var udata: Dictionary = _bound_board.get_unit_data(target_hero)
		var hname: String = str(udata.get("name", target_hero))
		if board_view != null:
			board_view.select_unit(target_hero)
			if not board_view.attackable_cells.is_empty():
				if combat_log != null:
					combat_log.append_entry("ATAQUE", "⚔️ %s em posição de ataque! Clique em um inimigo dentro das células vermelhas." % hname)
				return
			else:
				if card_fan != null:
					var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_COMBATE)
					if played != null:
						return
				if combat_log != null:
					combat_log.append_entry("AVISO", "⚠️ Nenhum inimigo no alcance de ataque de %s! Mova-se mais perto primeiro." % hname)
				return

	if card_fan != null:
		var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_COMBATE)
		if played == null and combat_log != null:
			combat_log.append_entry("AVISO", "Nenhuma carta de Combate disponível na mão!")

func _on_btn_shoot_pressed() -> void:
	play_sfx("button_click", 0.8, 1.2)
	if card_fan != null and card_fan.selected_index >= 0:
		card_fan.play_selected_card()
	elif card_fan != null:
		var played: CardData = card_fan.play_card_by_badge(CardData.BADGE_COMBATE)
		if played == null and combat_log != null:
			combat_log.append_entry("AVISO", "Nenhuma carta de Balestra/Combate disponível na mão!")

func _on_btn_bribe_pressed() -> void:
	play_sfx("button_click", 0.8, 1.0)
	if combat_log != null:
		combat_log.append_entry("SUBORNO", "Você ofereceu néctar aos batedores Isectum.")

func _select_or_play_hand_card(idx: int) -> void:
	if card_fan == null or idx < 0 or idx >= card_fan.get_card_count():
		return
	if card_fan.selected_index == idx:
		card_fan.play_selected_card()
	else:
		card_fan.select_card(idx)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_ESCAPE:
				_on_btn_menu_pressed()
			KEY_SPACE:
				if card_fan != null and card_fan.selected_index >= 0:
					card_fan.play_selected_card()
				else:
					trigger_sync_round()
			KEY_ENTER, KEY_KP_ENTER:
				if card_fan != null and card_fan.selected_index >= 0:
					card_fan.play_selected_card()
				else:
					trigger_sync_round()
			KEY_1:
				_select_or_play_hand_card(0)
			KEY_2:
				_select_or_play_hand_card(1)
			KEY_3:
				_select_or_play_hand_card(2)
			KEY_4:
				_select_or_play_hand_card(3)
			KEY_5:
				_select_or_play_hand_card(4)
			KEY_M:
				_on_btn_move_pressed()
			KEY_T:
				_on_btn_work_pressed()
			KEY_X:
				_on_btn_excavate_pressed()
			KEY_A:
				_on_btn_attack_pressed()
			KEY_F:
				_on_btn_shoot_pressed()
			KEY_S:
				_on_btn_bribe_pressed()
			KEY_Q:
				if board_view != null:
					board_view.rotate_camera_left()
			KEY_E:
				if board_view != null:
					board_view.rotate_camera_right()
			KEY_R:
				if board_view != null:
					board_view.reset_camera()
			KEY_O:
				_open_options_modal()
			KEY_F5:
				_on_btn_autoplay_pressed()
			KEY_K:
				# Comando de desenvolvedor desativado: sem movimento infinito
				if combat_log != null:
					combat_log.append_entry("AVISO", "🛡️ Comando de desenvolvedor 'k' desativado. Movimentação consome PM normalmente.")

func _on_btn_autoplay_pressed() -> void:
	play_sfx("button_click", 0.8, 1.1)
	autoplay_active = not autoplay_active
	set_autoplay_active(autoplay_active)
	autoplay_toggled.emit(autoplay_active)

func _create_fantasy_stylebox(bg: Color, border: Color, border_w: int = 2, radius: int = 4) -> StyleBoxFlat:
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.border_width_left = border_w
	sb.border_width_top = border_w
	sb.border_width_right = border_w
	sb.border_width_bottom = border_w
	sb.corner_radius_top_left = radius
	sb.corner_radius_top_right = radius
	sb.corner_radius_bottom_right = radius
	sb.corner_radius_bottom_left = radius
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 3
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	return sb

func _setup_autoplay_button_style() -> void:
	if btn_autoplay != null:
		btn_autoplay.custom_minimum_size = Vector2(130, 32)
		btn_autoplay.tooltip_text = "Auto-Play [F5]: A IA joga cartas, ataca e movimenta seus heróis automaticamente no combate."
		set_autoplay_active(autoplay_active)

func set_autoplay_active(active: bool) -> void:
	autoplay_active = active
	if btn_autoplay == null:
		return
	if active:
		btn_autoplay.text = "⏸ AUTO [ON]"
		btn_autoplay.add_theme_color_override("font_color", Color(1.0, 0.88, 0.25))
		btn_autoplay.add_theme_color_override("font_hover_color", Color(1.0, 0.96, 0.60))
		btn_autoplay.add_theme_stylebox_override("normal", _create_fantasy_stylebox(Color(0.14, 0.12, 0.04, 0.95), Color(1.0, 0.84, 0.20, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("hover", _create_fantasy_stylebox(Color(0.22, 0.18, 0.06, 0.98), Color(1.0, 0.94, 0.45, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("pressed", _create_fantasy_stylebox(Color(0.09, 0.07, 0.02, 1.0), Color(0.85, 0.70, 0.15, 1.0), 2, 4))
	else:
		btn_autoplay.text = "AutoPlay [F5]"
		btn_autoplay.add_theme_color_override("font_color", Color(0.70, 0.95, 0.70))
		btn_autoplay.add_theme_color_override("font_hover_color", Color(0.85, 1.0, 0.85))
		btn_autoplay.add_theme_stylebox_override("normal", _create_fantasy_stylebox(Color(0.10, 0.09, 0.14, 0.95), Color(0.85, 0.70, 0.25, 0.9), 2, 4))
		btn_autoplay.add_theme_stylebox_override("hover", _create_fantasy_stylebox(Color(0.18, 0.14, 0.24, 0.98), Color(1.0, 0.88, 0.35, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("pressed", _create_fantasy_stylebox(Color(0.06, 0.05, 0.09, 1.0), Color(0.75, 0.60, 0.20, 1.0), 2, 4))

func _open_options_modal() -> void:
	play_sfx("button_click", 0.8, 1.0)
	if not is_inside_tree():
		return
	if _options_modal == null:
		var scene = load("res://scenes/ui/OptionsMenu.tscn")
		if scene != null:
			_options_modal = scene.instantiate() as OptionsMenu
			add_child(_options_modal)
	if _options_modal != null:
		_options_modal.open()

# ── Model Signal Handlers ────────────────────────────────────────────────────
func _on_model_wall_damaged(wall_id: String, _amount: int, remaining_hp: int) -> void:
	if scoreboard != null:
		scoreboard.update_wall_hp(wall_id, remaining_hp)
	play_sfx("damage", 0.9, 1.0)

func _on_model_wall_breached(wall_id: String) -> void:
	if scoreboard != null:
		scoreboard.update_wall_hp(wall_id, 0)
	play_sfx("critical_hit", 1.0, 0.7)

func _on_deck_card_drawn(card: CardData) -> void:
	if card_fan != null and card != null:
		card_fan.add_card(card)
	_update_deck_counts()
	play_sfx("button_click", 0.7, 1.3)

func _on_deck_card_played(card: CardData) -> void:
	if card_fan != null and card != null:
		card_fan.remove_card_by_id(card.id)
	_update_deck_counts()
	play_sfx("button_click", 0.9, 0.9)

func _on_judge_dice_rolled(_rolls: Array, total_impacts: int, total_shots: int, total_crits: int) -> void:
	play_sfx("hit", 0.9, 1.4)
	if combat_log != null:
		combat_log.append_entry("DADOS", "Rolagem: %d Impactos, %d Balestras, %d Críticos" % [total_impacts, total_shots, total_crits])

# ── EventBus Handlers ────────────────────────────────────────────────────────
func _on_eb_card_played(_player_id: String, _card_id: String, _target_zone: String) -> void:
	play_sfx("button_click", 0.8, 1.0)

func _on_eb_dice_rolled(_source_id: String, _dice_type: String, _results: Array) -> void:
	play_sfx("hit", 0.9, 1.4)

func _on_eb_damage_dealt(_target_id: String, _amount: int, _current_hp: int) -> void:
	play_sfx("damage", 1.0, 1.0)

func _on_eb_production_completed(workshop_zone: String, resource_type: String, amount: int) -> void:
	play_sfx("button_click", 0.8, 1.2)
	if combat_log != null:
		combat_log.append_entry("PRODUÇÃO", "%s produziu %d de %s!" % [workshop_zone, amount, resource_type])

func _on_eb_wall_breached(_wall_id: String) -> void:
	play_sfx("critical_hit", 1.0, 0.7)

func _on_eb_synergy_triggered(_synergy_type: String, _bonus_description: String) -> void:
	play_sfx("heal", 0.9, 1.2)

func _on_eb_supreme_synchrony_triggered(_crystals_awarded: int) -> void:
	play_sfx("level_up", 1.0, 1.1)

# ── Public Action Trigger ────────────────────────────────────────────────────
func trigger_sync_round() -> void:
	sync_round_requested.emit()
	play_sfx("button_click", 1.0, 1.0)

# ── Lifecycle & Memory Safety ────────────────────────────────────────────────
func cleanup() -> void:
	unbind_all()
	if card_fan != null and is_instance_valid(card_fan):
		card_fan.cleanup()
	
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("EventBus"):
		var eb: Node = tree.root.get_node("EventBus")
		if eb.has_signal("card_played") and eb.card_played.is_connected(_on_eb_card_played):
			eb.card_played.disconnect(_on_eb_card_played)
		if eb.has_signal("dice_rolled") and eb.dice_rolled.is_connected(_on_eb_dice_rolled):
			eb.dice_rolled.disconnect(_on_eb_dice_rolled)
		if eb.has_signal("damage_dealt") and eb.damage_dealt.is_connected(_on_eb_damage_dealt):
			eb.damage_dealt.disconnect(_on_eb_damage_dealt)
		if eb.has_signal("production_completed") and eb.production_completed.is_connected(_on_eb_production_completed):
			eb.production_completed.disconnect(_on_eb_production_completed)
		if eb.has_signal("wall_breached") and eb.wall_breached.is_connected(_on_eb_wall_breached):
			eb.wall_breached.disconnect(_on_eb_wall_breached)
		if eb.has_signal("synergy_triggered") and eb.synergy_triggered.is_connected(_on_eb_synergy_triggered):
			eb.synergy_triggered.disconnect(_on_eb_synergy_triggered)
		if eb.has_signal("supreme_synchrony_triggered") and eb.supreme_synchrony_triggered.is_connected(_on_eb_supreme_synchrony_triggered):
			eb.supreme_synchrony_triggered.disconnect(_on_eb_supreme_synchrony_triggered)

func _exit_tree() -> void:
	cleanup()
