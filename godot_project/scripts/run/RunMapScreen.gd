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
@onready var btn_autoplay: Button = get_node_or_null("Header/HBox/BtnAutoPlay")

var state: RunState = null
var resolver: RunNodeResolver = null
var rng: RandomNumberGenerator = null
var autoplay_active: bool = false

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
	if btn_autoplay != null and not btn_autoplay.pressed.is_connected(toggle_autoplay):
		btn_autoplay.pressed.connect(toggle_autoplay)

	_setup_header_buttons_style()
	_bind_state_signals()
	_apply_background_texture()
	refresh_ui()
	_start_map_bgm()

func _apply_background_texture() -> void:
	var bg: Node = get_node_or_null("Background")
	if bg == null:
		return
	var loaded_tex: Texture2D = null
	var target_jpg: String = "res://assets/images/ui/mapa_biomas_roguelike.jpg"
	var global_path: String = ProjectSettings.globalize_path(target_jpg)
	if FileAccess.file_exists(global_path):
		var img: Image = Image.load_from_file(global_path)
		if img != null and not img.is_empty():
			loaded_tex = ImageTexture.create_from_image(img)
	if loaded_tex == null:
		var bg_paths: Array[String] = [
			"res://assets/images/ui/mapa_biomas_roguelike.jpg",
			"res://assets/images/ui/mapa_biomas_roguelike.png",
			"res://assets/images/ui/mapa_mundo.png"
		]
		for path in bg_paths:
			if ResourceLoader.exists(path):
				loaded_tex = load(path) as Texture2D
				if loaded_tex != null:
					break
	if loaded_tex != null:
		var tex_rect: TextureRect = bg.get_node_or_null("MapTexture") as TextureRect
		if tex_rect == null:
			tex_rect = TextureRect.new()
			tex_rect.name = "MapTexture"
			tex_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
			tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
			tex_rect.modulate = Color(0.95, 0.95, 0.95, 0.92)
			bg.add_child(tex_rect)
		tex_rect.texture = loaded_tex

func _start_map_bgm() -> void:
	if not is_inside_tree() or _is_in_gut_runner():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_bgm"):
			am.play_bgm("mapa", 1.2)

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
		card.custom_minimum_size = Vector2(148, 52)
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color(0.10, 0.11, 0.15, 0.95) if not is_dead else Color(0.20, 0.05, 0.05, 0.88)
		style.border_color = Color(0.85, 0.70, 0.25, 0.95) if not is_dead else Color(0.5, 0.2, 0.2)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.set_corner_radius_all(4)
		style.shadow_color = Color(0.0, 0.0, 0.0, 0.7)
		style.shadow_size = 4
		card.add_theme_stylebox_override("panel", style)

		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		var lbl_name: Label = Label.new()
		lbl_name.text = h.capitalize() if not is_dead else "💀 %s" % h.capitalize()
		lbl_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_name.add_theme_font_size_override("font_size", 12)
		lbl_name.add_theme_color_override("font_color", Color(1.0, 0.92, 0.75) if not is_dead else Color(0.8, 0.4, 0.4))

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
		lbl_hp.add_theme_color_override("font_color", Color(0.90, 0.92, 0.96))

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

	# Dimensões de layout para visualização completa 16:9
	var total_floors: int = map.floor_count
	var canvas_width: float = 1240.0
	var canvas_height: float = 540.0
	if total_floors > 7:
		canvas_height = maxf(540.0, float(total_floors) * 75.0 + 80.0)
	map_canvas.custom_minimum_size = Vector2(canvas_width, canvas_height)

	# Instanciar botões dos nós
	for node in map.nodes:
		var btn: Button = Button.new()
		var btn_size: float = 42.0 if not node.is_boss() else 58.0
		btn.custom_minimum_size = Vector2(btn_size, btn_size)
		btn.add_theme_font_size_override("font_size", 19 if not node.is_boss() else 26)

		# Posicionamento com respiro vertical e curvatura orgânica
		var y_top: float = 56.0
		var y_bottom: float = canvas_height - 62.0
		var y_pct: float = 1.0 - (float(node.floor_index) / float(maxi(total_floors - 1, 1)))
		var base_y: float = y_top + y_pct * (y_bottom - y_top)

		var num_cols: int = maxi(map.column_count, 1)
		var col_frac: float = 0.5
		if num_cols > 1:
			col_frac = float(node.column) / float(num_cols - 1)

		# Tapering suave: deserto mais largo na base (680px), floresta mais concentrada no topo (520px)
		var span_w: float = lerpf(680.0, 520.0, 1.0 - y_pct)
		var start_x: float = (canvas_width - span_w) * 0.5
		var base_x: float = start_x + col_frac * span_w

		# Curvatura e respiro orgânico para evitar colunas verticais rígidas (estilo cartografia)
		var organic_x: float = 0.0
		var organic_y: float = 0.0
		if not node.is_boss() and node.floor_index > 0:
			organic_x = sin(float(node.floor_index * 13 + node.column * 37)) * 22.0
			if node.floor_index < total_floors - 1:
				organic_y = cos(float(node.floor_index * 19 + node.column * 11)) * 6.0

		var x_pos: float = base_x + organic_x
		if node.is_boss():
			x_pos = canvas_width * 0.5
			organic_y = 0.0

		btn.position = Vector2(x_pos - btn_size * 0.5, base_y + organic_y - btn_size * 0.5)

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

	# Só posiciona na base (deserto) na primeira inicialização da expedição
	var scroll_node: ScrollContainer = get_node_or_null("Scroll") as ScrollContainer
	if scroll_node != null and canvas_height > 540.0:
		if state.current_node_id < 0:
			scroll_node.scroll_vertical = int(canvas_height)

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
	var radius: int = 21 if not node.is_boss() else 29
	style.set_corner_radius_all(radius)

	if node.visited:
		style.bg_color = Color(0.16, 0.18, 0.22, 0.88)
		style.border_color = Color(0.44, 0.48, 0.54, 0.80)
		style.set_border_width_all(2)
		btn.modulate = Color(0.85, 0.85, 0.9, 0.85)
		btn.add_theme_color_override("font_disabled_color", Color(0.68, 0.70, 0.75, 0.75))
	elif is_current:
		style.bg_color = Color(0.28, 0.18, 0.08, 0.95)
		style.border_color = Color(1.0, 0.92, 0.35, 1.0)
		style.set_border_width_all(3)
		style.shadow_color = Color(1.0, 0.75, 0.2, 0.85)
		style.shadow_size = 14
		btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
		btn.add_theme_color_override("font_color", Color(1.0, 0.95, 0.85, 1.0))
	elif is_available:
		# Nós ativos no deserto brilham intensamente com chamas e brasas douradas
		style.bg_color = Color(0.24, 0.13, 0.06, 0.96)
		style.border_color = Color(1.0, 0.88, 0.35, 1.0)
		style.set_border_width_all(3)
		style.shadow_color = Color(1.0, 0.62, 0.12, 0.95)
		style.shadow_size = 18 if node.floor_index == 0 else 12
		btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
		btn.add_theme_color_override("font_color", Color(1.0, 0.96, 0.85, 1.0))
		btn.add_theme_color_override("font_hover_color", Color(1.0, 1.0, 1.0, 1.0))
	else:
		style.bg_color = Color(0.10, 0.11, 0.15, 0.88)
		style.border_color = Color(0.32, 0.35, 0.42, 0.75)
		style.set_border_width_all(2)
		btn.modulate = Color(0.80, 0.80, 0.85, 0.85)
		btn.add_theme_color_override("font_disabled_color", Color(0.65, 0.68, 0.74, 0.75))

	if node.is_boss() and not node.visited:
		style.border_color = Color(1.0, 0.82, 0.25, 1.0)
		style.set_border_width_all(3)
		style.shadow_color = Color(0.9, 0.2, 0.2, 0.85)
		style.shadow_size = 14

	var style_focus: StyleBoxEmpty = StyleBoxEmpty.new()
	btn.add_theme_stylebox_override("focus", style_focus)
	btn.add_theme_stylebox_override("normal", style)
	var hover_style: StyleBoxFlat = style.duplicate()
	hover_style.border_color = Color(1.0, 1.0, 0.6, 1.0)
	hover_style.shadow_size = style.shadow_size + 4
	btn.add_theme_stylebox_override("hover", hover_style)
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

func _play_click_sound() -> void:
	if not is_inside_tree() or _is_in_gut_runner():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("button_click", 0.9, 1.1)

func _on_node_pressed(node_id: int, from_autoplay: bool = false) -> void:
	if state == null or not state.can_move_to(node_id):
		return

	_play_click_sound()

	if not from_autoplay and autoplay_active:
		autoplay_active = false
		_update_autoplay_button_ui()

	# 1. Mover heróis para o nó
	var moved: bool = state.move_to(node_id)
	if not moved:
		return

	var target_node: RunNode = state.get_current_node()
	node_selected.emit(target_node)

	# 2. Se for nó de combate (COMBAT, ELITE, SIEGE, BOSS), transiciona para Main.tscn
	if target_node.is_combat_type():
		_transition_to_combat_node(target_node)
		return

	# 3. Resolver nó não-combate (Fogueira, Evento, etc.)
	var outcome: Dictionary = resolver.resolve(state, rng)

	# 4. Exibir feedback no log
	if log_label != null:
		var text: String = "\n".join(outcome.get("log", []))
		log_label.text = "[color=#ffd700]▶ %s:[/color]\n%s" % [target_node.get_type_name().to_upper(), text]

	# 5. Atualizar tela
	refresh_ui()

func _transition_to_combat_node(target_node: RunNode) -> void:
	RunCombatBridge.setup_combat(state, target_node, rng)

	if log_label != null:
		log_label.text = "[color=#ffd700]▶ ENTRANDO EM COMBATE: %s[/color]\nPreparando tabuleiro tático da Fortaleza..." % target_node.get_type_name().to_upper()

	var tree: SceneTree = get_tree()
	var in_test_runner: bool = _is_in_gut_runner()

	if tree != null and not in_test_runner:
		if tree.root.has_node("GameManager"):
			var gm: Node = tree.root.get_node("GameManager")
			if gm.has_method("change_state_and_scene"):
				var target_state: int = gm.GameState.COMBATE_TATICO if "GameState" in gm else 1
				gm.change_state_and_scene(target_state)
				return
		tree.change_scene_to_file("res://scenes/main/Main.tscn")
	else:
		# Fallback para ambiente de testes GUT (evita descarregar o runner e resolve nó)
		if resolver != null:
			var outcome: Dictionary = resolver.resolve(state, rng)
			if log_label != null:
				var text: String = "\n".join(outcome.get("log", []))
				log_label.text = "[color=#ffd700]▶ %s:[/color]\n%s" % [target_node.get_type_name().to_upper(), text]
			refresh_ui()

func _is_in_gut_runner() -> bool:
	for arg in OS.get_cmdline_args():
		if "gut" in arg.to_lower():
			return true
	for arg in OS.get_cmdline_user_args():
		if "gut" in arg.to_lower():
			return true
	var tree: SceneTree = get_tree()
	if tree == null:
		return true
	if tree.root.find_child("*gut*", true, false) != null:
		return true
	return false

func _on_act_advanced(new_act: int) -> void:
	if log_label != null:
		log_label.text = "[color=#00ff88]★ ATO CONCLUÍDO! O grupo desce para o Ato %d. (+25%% PV recuperado)[/color]" % new_act
	refresh_ui()

func _on_run_ended(victory: bool) -> void:
	run_finished.emit(victory)
	# Grava permanentemente estatísticas e Âmbar Real no MetaProgression
	var meta: MetaProgression = MetaProgression.get_instance()
	if meta != null:
		meta.record_run_finished(state, victory)

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
			var gm: Node = tree.root.get_node("GameManager")
			var target_state: int = gm.GameState.MENU if "GameState" in gm else 0
			gm.change_state_and_scene(target_state)
		else:
			tree.change_scene_to_file("res://scenes/main/Menu.tscn")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F5:
			toggle_autoplay()

# ── Sistema de Auto-Play no Mapa ─────────────────────────────────────────────

## Alterna o estado do Auto-Play no mapa da run.
func toggle_autoplay() -> bool:
	autoplay_active = not autoplay_active
	_update_autoplay_button_ui()
	if autoplay_active:
		if log_label != null:
			log_label.text = "[color=#00e5ff]🤖 AUTO-PLAY: Modo automático ativado! Explorando rotas automaticamente...[/color]"
		_execute_map_autoplay_step()
	else:
		if log_label != null:
			log_label.text = "[color=#ffd700]⏸ AUTO-PLAY: Modo automático pausado. Escolha uma rota manualmente.[/color]"
	return autoplay_active

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

func _setup_header_buttons_style() -> void:
	if btn_back != null:
		btn_back.custom_minimum_size = Vector2(95, 38)
		btn_back.add_theme_stylebox_override("normal", _create_fantasy_stylebox(Color(0.10, 0.09, 0.14, 0.95), Color(0.65, 0.55, 0.40, 0.9)))
		btn_back.add_theme_stylebox_override("hover", _create_fantasy_stylebox(Color(0.18, 0.14, 0.24, 0.98), Color(0.95, 0.80, 0.45, 1.0)))
		btn_back.add_theme_stylebox_override("pressed", _create_fantasy_stylebox(Color(0.06, 0.05, 0.09, 1.0), Color(0.50, 0.40, 0.30, 1.0)))
		btn_back.add_theme_color_override("font_color", Color(0.92, 0.92, 0.92))
		btn_back.add_theme_color_override("font_hover_color", Color(1.0, 0.94, 0.75))

	if btn_autoplay != null:
		btn_autoplay.custom_minimum_size = Vector2(135, 38)
		btn_autoplay.tooltip_text = "Auto-Play [F5]: A IA avança estrategicamente pelos nós do mapa da expedição."
		_update_autoplay_button_ui()

func _update_autoplay_button_ui() -> void:
	if btn_autoplay == null:
		return
	if autoplay_active:
		btn_autoplay.text = "⏸ AUTO [ON]"
		btn_autoplay.add_theme_color_override("font_color", Color(1.0, 0.88, 0.25))
		btn_autoplay.add_theme_color_override("font_hover_color", Color(1.0, 0.96, 0.60))
		btn_autoplay.add_theme_stylebox_override("normal", _create_fantasy_stylebox(Color(0.14, 0.12, 0.04, 0.95), Color(1.0, 0.84, 0.20, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("hover", _create_fantasy_stylebox(Color(0.22, 0.18, 0.06, 0.98), Color(1.0, 0.94, 0.45, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("pressed", _create_fantasy_stylebox(Color(0.09, 0.07, 0.02, 1.0), Color(0.85, 0.70, 0.15, 1.0), 2, 4))
	else:
		btn_autoplay.text = "▶ AUTO [F5]"
		btn_autoplay.add_theme_color_override("font_color", Color(0.70, 0.95, 0.70))
		btn_autoplay.add_theme_color_override("font_hover_color", Color(0.85, 1.0, 0.85))
		btn_autoplay.add_theme_stylebox_override("normal", _create_fantasy_stylebox(Color(0.10, 0.09, 0.14, 0.95), Color(0.85, 0.70, 0.25, 0.9), 2, 4))
		btn_autoplay.add_theme_stylebox_override("hover", _create_fantasy_stylebox(Color(0.18, 0.14, 0.24, 0.98), Color(1.0, 0.88, 0.35, 1.0), 2, 4))
		btn_autoplay.add_theme_stylebox_override("pressed", _create_fantasy_stylebox(Color(0.06, 0.05, 0.09, 1.0), Color(0.75, 0.60, 0.20, 1.0), 2, 4))

## Escolhe inteligentemente o melhor nó disponível para navegação automática
func pick_best_autoplay_node(available: Array[RunNode]) -> RunNode:
	if available.is_empty():
		return null

	# Checa se algum herói está gravemente ferido (< 50% HP)
	var needs_healing: bool = false
	if state != null:
		for h in state.heroes:
			var cur: int = int(state.hero_hp.get(h, 0))
			var max_h: int = int(state.hero_max_hp.get(h, 1))
			if max_h > 0 and float(cur) / float(max_h) < 0.50:
				needs_healing = true
				break

	# 1. Se precisa de cura, prioriza Fogueira (CAMPFIRE)
	if needs_healing:
		for n in available:
			if n.type == RunNode.NodeType.CAMPFIRE:
				return n

	# 2. Se o grupo está saudável, prioriza Elite para recompensas ou Forja
	if not needs_healing:
		for n in available:
			if n.type == RunNode.NodeType.ELITE:
				return n
		for n in available:
			if n.type == RunNode.NodeType.FORGE:
				return n

	# 3. Padrão: primeiro nó disponível
	return available[0]

## Executa um passo de avanço automático no mapa
func _execute_map_autoplay_step() -> void:
	if not autoplay_active or state == null:
		return

	var available: Array[RunNode] = state.get_available_nodes()
	if available.is_empty():
		autoplay_active = false
		_update_autoplay_button_ui()
		return

	var chosen: RunNode = pick_best_autoplay_node(available)
	if chosen == null:
		autoplay_active = false
		_update_autoplay_button_ui()
		return

	if log_label != null:
		log_label.text = "[color=#00e5ff]🤖 AUTO-PLAY: Avançando para %s (Andar %d)...[/color]" % [chosen.get_type_name().to_upper(), chosen.floor_index]

	# Dispara o clique no nó
	_on_node_pressed(chosen.id, true)

	# Se for nó que resolve sem mudar de cena (Fogueira, Evento, etc.), agenda o próximo nó
	if autoplay_active and not chosen.is_combat_type():
		var tree: SceneTree = get_tree()
		if tree != null:
			var timer: SceneTreeTimer = tree.create_timer(1.2)
			timer.timeout.connect(func():
				if autoplay_active:
					_execute_map_autoplay_step()
			)
