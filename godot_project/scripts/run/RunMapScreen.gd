# res://scripts/run/RunMapScreen.gd
class_name RunMapScreen
extends Control

## Tela de Navegação do Mapa Roguelike (Slay the Spire Style).
## Exibe os nós do Ato atual, conexões entre andares, status do grupo,
## ouro, deck e resolução de eventos com feedback sonoro e visual.

signal node_selected(node: RunNode)
signal run_finished(victory: bool)

@onready var lbl_act: Label = get_node_or_null("Header/HBox/VBoxTitle/LblAct")
@onready var lbl_boss: Label = get_node_or_null("Header/HBox/VBoxTitle/LblBoss")
@onready var lbl_gold: Label = get_node_or_null("Header/HBox/HBoxStats/LblGold")
@onready var lbl_deck: Label = get_node_or_null("Header/HBox/HBoxStats/LblDeck")
@onready var lbl_amber: Label = get_node_or_null("Header/HBox/HBoxStats/LblAmber")
@onready var hero_container: HBoxContainer = get_node_or_null("Header/HBox/HeroesContainer")
@onready var map_canvas: Control = get_node_or_null("Scroll/MapCanvas")
@onready var log_label: RichTextLabel = get_node_or_null("Footer/LogBox/LogLabel")
@onready var btn_back: Button = get_node_or_null("Header/HBox/BtnBack")

var state: RunState = null
var resolver: RunNodeResolver = null
var rng: RandomNumberGenerator = null

var node_buttons: Dictionary = {} # node_id -> Button

func _ready() -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	if resolver == null:
		resolver = RunNodeResolver.new()
	if state == null:
		if RunSession.has_active_run():
			state = RunSession.current
		else:
			# Fallback para desenvolvimento e testes standalone
			state = RunSession.start_new(1234)

	if btn_back != null and not btn_back.pressed.is_connected(_on_btn_back_pressed):
		btn_back.pressed.connect(_on_btn_back_pressed)

	_bind_state_signals()
	refresh_ui()

func setup(p_state: RunState, p_resolver: RunNodeResolver = null, p_rng: RandomNumberGenerator = null) -> void:
	state = p_state
	if p_resolver != null:
		resolver = p_resolver
	if p_rng != null:
		rng = p_rng
	_bind_state_signals()
	if is_inside_tree():
		refresh_ui()

func _bind_state_signals() -> void:
	if state == null:
		return
	if not state.run_ended.is_connected(_on_run_ended):
		state.run_ended.connect(_on_run_ended)
	if not state.act_advanced.is_connected(_on_act_advanced):
		state.act_advanced.connect(_on_act_advanced)

func refresh_ui() -> void:
	if state == null:
		return
	_update_header()
	_rebuild_map_nodes()

func _update_header() -> void:
	if lbl_act != null:
		var act_names: Dictionary = {
			1: "ATO I: O CERCO DA ÚLTIMA FORTALEZA",
			2: "ATO II: OS TÚNEIS VIVOS",
			3: "ATO III: A COLMEIA-MÃE DO REI ISECTUM"
		}
		lbl_act.text = act_names.get(state.act, "ATO %d" % state.act)

	if lbl_boss != null:
		var boss_names: Dictionary = {
			"viuva_canibal": "🕷️ Viúva Canibal (Subsolo)",
			"rainha_do_enxame": "👑 Rainha do Enxame (Ninhada)",
			"rei_isectum": "👑 REI ISECTUM (Mente Colmeia)"
		}
		lbl_boss.text = "Chefe do Ato: %s" % boss_names.get(state.get_current_boss_id(), state.get_current_boss_id())

	if lbl_gold != null:
		lbl_gold.text = "🪙 %d" % state.gold
	if lbl_deck != null:
		lbl_deck.text = "🃏 %d Cartas" % state.deck.size()
	if lbl_amber != null:
		lbl_amber.text = "💎 %d Âmbar" % state.calculate_amber()

	_update_hero_bars()

func _update_hero_bars() -> void:
	if hero_container == null:
		return
	for child in hero_container.get_children():
		hero_container.remove_child(child)
		child.queue_free()

	for h in state.heroes:
		var cur: int = int(state.hero_hp.get(h, 0))
		var max_h: int = int(state.hero_max_hp.get(h, 1))
		var is_dead: bool = not state.is_hero_alive(h)

		var card: PanelContainer = PanelContainer.new()
		card.custom_minimum_size = Vector2(140, 48)
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color(0.12, 0.1, 0.14, 0.9) if not is_dead else Color(0.2, 0.05, 0.05, 0.8)
		style.border_color = Color(0.8, 0.65, 0.25) if not is_dead else Color(0.5, 0.2, 0.2)
		style.set_border_width_all(1)
		style.set_corner_radius_all(4)
		card.add_theme_stylebox_override("panel", style)

		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		var lbl_name: Label = Label.new()
		lbl_name.text = h.capitalize() if not is_dead else "💀 %s" % h.capitalize()
		lbl_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_name.add_theme_font_size_override("font_size", 12)

		var pbar: ProgressBar = ProgressBar.new()
		pbar.max_value = max_h
		pbar.value = cur
		pbar.show_percentage = false
		pbar.custom_minimum_size = Vector2(120, 10)

		var pbar_style: StyleBoxFlat = StyleBoxFlat.new()
		var pct: float = float(cur) / float(max_h) if max_h > 0 else 0.0
		if pct > 0.5:
			pbar_style.bg_color = Color(0.2, 0.7, 0.25)
		elif pct > 0.25:
			pbar_style.bg_color = Color(0.85, 0.7, 0.15)
		else:
			pbar_style.bg_color = Color(0.85, 0.2, 0.2)
		pbar_style.set_corner_radius_all(2)
		pbar.add_theme_stylebox_override("fill", pbar_style)

		var lbl_hp: Label = Label.new()
		lbl_hp.text = "%d/%d PV" % [cur, max_h]
		lbl_hp.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_hp.add_theme_font_size_override("font_size", 10)

		vbox.add_child(lbl_name)
		vbox.add_child(pbar)
		vbox.add_child(lbl_hp)
		card.add_child(vbox)
		hero_container.add_child(card)

func _rebuild_map_nodes() -> void:
	if map_canvas == null or state == null or state.map == null:
		return

	# Limpar botões antigos
	for child in map_canvas.get_children():
		map_canvas.remove_child(child)
		child.queue_free()
	node_buttons.clear()

	var map: RunMap = state.map
	var available_nodes: Array[RunNode] = state.get_available_nodes()
	var current_node: RunNode = state.get_current_node()

	# Dimensões de layout
	var total_floors: int = map.floor_count
	var canvas_width: float = 1240.0
	var canvas_height: float = maxf(620.0, float(total_floors) * 68.0)
	map_canvas.custom_minimum_size = Vector2(canvas_width, canvas_height)

	# Instanciar botões dos nós
	for node in map.nodes:
		var btn: Button = Button.new()
		var btn_size: float = 48.0 if not node.is_boss() else 68.0
		btn.custom_minimum_size = Vector2(btn_size, btn_size)
		btn.add_theme_font_size_override("font_size", 20 if not node.is_boss() else 28)

		# Posicionamento centralizado (andar 0 na base, boss no topo)
		var y_pct: float = 1.0 - (float(node.floor_index) / float(maxi(total_floors - 1, 1)))
		var map_span_w: float = 660.0
		var start_x: float = (canvas_width - map_span_w) * 0.5
		var x_pos: float = start_x + float(node.column) * (map_span_w / 3.0)
		if node.is_boss():
			x_pos = canvas_width * 0.5
		var y_pos: float = 48.0 + y_pct * (canvas_height - 110.0)
		btn.position = Vector2(x_pos - btn_size * 0.5, y_pos - btn_size * 0.5)

		# Cores e Ícones
		var icon_str: String = _get_node_icon(node)
		btn.text = icon_str

		var is_available: bool = false
		for av in available_nodes:
			if av.id == node.id:
				is_available = true
				break

		var is_current: bool = (current_node != null and current_node.id == node.id)

		_style_node_button(btn, node, is_available, is_current)

		btn.disabled = not is_available
		var target_id: int = node.id
		btn.pressed.connect(func(): _on_node_pressed(target_id))

		map_canvas.add_child(btn)
		node_buttons[node.id] = btn

	# Força redraw das conexões
	map_canvas.queue_redraw()

func _get_node_icon(node: RunNode) -> String:
	match node.type:
		RunNode.NodeType.COMBAT:
			return "⚔️"
		RunNode.NodeType.ELITE:
			return "💀"
		RunNode.NodeType.SIEGE:
			return "🏰"
		RunNode.NodeType.EVENT:
			return "❓"
		RunNode.NodeType.CAMPFIRE:
			return "🔥"
		RunNode.NodeType.FORGE:
			return "⚒️"
		RunNode.NodeType.BOSS:
			return "👑"
	return "•"

func _style_node_button(btn: Button, node: RunNode, is_available: bool, is_current: bool) -> void:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.set_corner_radius_all(10 if not node.is_boss() else 16)

	if node.visited:
		style.bg_color = Color(0.22, 0.25, 0.28, 0.85)
		style.border_color = Color(0.5, 0.58, 0.65)
		style.set_border_width_all(2)
		btn.modulate = Color(0.85, 0.85, 0.9, 0.9)
	elif is_current:
		style.bg_color = Color(0.85, 0.55, 0.12, 0.95)
		style.border_color = Color(1.0, 0.92, 0.35)
		style.set_border_width_all(3)
		btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
	elif is_available:
		style.bg_color = _get_node_base_color(node.type)
		style.border_color = Color(1.0, 0.88, 0.32)
		style.set_border_width_all(3)
		btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
	else:
		style.bg_color = _get_node_base_color(node.type).darkened(0.45)
		style.border_color = Color(0.42, 0.44, 0.52, 0.85)
		style.set_border_width_all(2)
		btn.modulate = Color(0.85, 0.85, 0.9, 0.85)

	btn.add_theme_stylebox_override("normal", style)
	btn.add_theme_stylebox_override("hover", style)
	btn.add_theme_stylebox_override("pressed", style)
	btn.add_theme_stylebox_override("disabled", style)

func _get_node_base_color(type: int) -> Color:
	match type:
		RunNode.NodeType.COMBAT:
			return Color(0.6, 0.18, 0.18, 0.9)
		RunNode.NodeType.ELITE:
			return Color(0.5, 0.15, 0.65, 0.9)
		RunNode.NodeType.SIEGE:
			return Color(0.2, 0.35, 0.65, 0.9)
		RunNode.NodeType.EVENT:
			return Color(0.65, 0.5, 0.15, 0.9)
		RunNode.NodeType.CAMPFIRE:
			return Color(0.75, 0.35, 0.1, 0.9)
		RunNode.NodeType.FORGE:
			return Color(0.4, 0.4, 0.45, 0.9)
		RunNode.NodeType.BOSS:
			return Color(0.8, 0.1, 0.15, 0.95)
	return Color(0.2, 0.2, 0.2)

func _on_node_pressed(node_id: int) -> void:
	if state == null or not state.can_move_to(node_id):
		return

	# 1. Mover heróis para o nó
	var moved: bool = state.move_to(node_id)
	if not moved:
		return

	var target_node: RunNode = state.get_current_node()
	node_selected.emit(target_node)

	# 2. Resolver o nó (Placeholder M1/M2; M4 invocará combate tático no tabuleiro)
	var outcome: Dictionary = resolver.resolve(state, rng)

	# 3. Exibir feedback no log
	if log_label != null:
		var text: String = "\n".join(outcome.get("log", []))
		log_label.text = "[color=#ffd700]▶ %s:[/color]\n%s" % [target_node.get_type_name().to_upper(), text]

	# 4. Atualizar tela
	refresh_ui()

func _on_act_advanced(new_act: int) -> void:
	if log_label != null:
		log_label.text = "[color=#00ff88]★ ATO CONCLUÍDO! O grupo desce para o Ato %d. (+25%% PV recuperado)[/color]" % new_act
	refresh_ui()

func _on_run_ended(victory: bool) -> void:
	run_finished.emit(victory)
	if log_label != null:
		if victory:
			log_label.text = "[color=#ffd700]🏆 VITÓRIA SUPREMA! O Rei Isectum foi destruído e a Colmeia colapsou![/color]"
		else:
			log_label.text = "[color=#ff4444]💀 DERROTA: Todos os heróis caíram nas profundezas do enxame.[/color]"

	# Transição para tela de Game Over ou Menu
	var tree: SceneTree = get_tree()
	if tree != null:
		var timer: SceneTreeTimer = tree.create_timer(1.8)
		timer.timeout.connect(func():
			if tree.root.has_node("GameManager"):
				var gm = tree.root.get_node("GameManager")
				gm.change_state_and_scene(gm.GameState.FIM_DE_JOGO, {
					"victory": victory,
					"score": state.calculate_amber(),
					"floors": state.floors_cleared,
					"enemies": state.enemies_killed
				})
			else:
				tree.change_scene_to_file("res://scenes/main/GameOver.tscn")
		)

func _on_btn_back_pressed() -> void:
	var tree: SceneTree = get_tree()
	if tree != null:
		if tree.root.has_node("GameManager"):
			tree.root.get_node("GameManager").change_state_and_scene(GameManager.GameState.MENU)
		else:
			tree.change_scene_to_file("res://scenes/main/Menu.tscn")
