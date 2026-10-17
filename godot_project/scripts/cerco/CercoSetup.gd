# res://scripts/cerco/CercoSetup.gd
class_name CercoSetup
extends Control

## CercoSetup: Tela de Configuração do Cerco contra Isectum.
## Permite selecionar heróis, escolher a dificuldade do combate e ajustar resolução de tela.

signal cerco_iniciado(config: Dictionary)

const HERO_DEFS: Array[Dictionary] = [
	{"id": "Stark", "nome": "Stark", "classe": "Paladino", "sprite": "res://assets/images/characters/portraits/stark_portrait.png", "padrao": true},
	{"id": "Elden", "nome": "Elden", "classe": "Mago", "sprite": "res://assets/images/characters/portraits/elden_portrait.png", "padrao": false},
	{"id": "Doom", "nome": "Doom", "classe": "Ladino", "sprite": "res://assets/images/characters/portraits/doom_portrait.png", "padrao": false},
	{"id": "Gruu", "nome": "Gruu", "classe": "Barbaro", "sprite": "res://assets/images/characters/portraits/gruu_portrait.png", "padrao": false},
	{"id": "Kuro", "nome": "Kuro", "classe": "Ladino", "sprite": "res://assets/images/characters/portraits/kuro_portrait.png", "padrao": false},
	{"id": "Darwin", "nome": "Darwin", "classe": "Druida", "sprite": "res://assets/images/characters/portraits/darwin_portrait.png", "padrao": false},
	{"id": "Lysander", "nome": "Pr. Lysander", "classe": "Filho do Imperador", "sprite": "res://assets/images/characters/portraits/lysander_portrait.png", "padrao": false, "auto": true}
]

const SECRET_HEROES: Array[Dictionary] = [
	{"id": "Aquele", "nome": "?????", "classe": "Guerreiro", "sprite": "res://assets/images/characters/portraits/aquele_portrait.png", "padrao": false, "secreto": true}
]

const DIFFICULTIES: Array[Dictionary] = [
	{"id": "facil", "nome": "Fácil (1/4 Deck)", "desc": "Minas: 5 | Cristais: 30 | Reserva: 8", "fator": 0.25},
	{"id": "media", "nome": "Média (1/2 Deck)", "desc": "Minas: 8 | Cristais: 20 | Reserva: 16", "fator": 0.50},
	{"id": "dificil", "nome": "Difícil (Deck Completo)", "desc": "Minas: 12 | Cristais: 15 | Reserva: 24", "fator": 1.00}
]

const RESOLUTIONS: Array[Vector2i] = [
	Vector2i(800, 600),
	Vector2i(960, 540),
	Vector2i(1024, 768),
	Vector2i(1280, 720),
	Vector2i(1366, 768),
	Vector2i(1600, 900),
	Vector2i(1920, 1080)
]

var selected_heroes: Dictionary = {}
var selected_diff_index: int = 1 # Média por padrão
var selected_res_index: int = 3 # 1280x720 por padrão

@onready var btn_back: Button = get_node_or_null("Header/BtnBack")
@onready var btn_start: Button = get_node_or_null("Footer/ButtonsHBox/BtnStart")
@onready var btn_castes: Button = get_node_or_null("Footer/ButtonsHBox/BtnCastes")
@onready var heroes_container: GridContainer = get_node_or_null("ScrollContainer/MainContent/HeroesSection/VBox/HeroesGrid")
@onready var diff_container: HBoxContainer = get_node_or_null("ScrollContainer/MainContent/DiffSection/VBox/DiffBox")
@onready var res_container: HBoxContainer = get_node_or_null("ScrollContainer/MainContent/ResSection/VBox/ResBox")

func _ready() -> void:
	# Inicializa heróis
	for h in HERO_DEFS:
		selected_heroes[h.id] = h.get("padrao", false)
	
	_build_heroes_ui()
	_build_diff_ui()
	_build_res_ui()
	_update_start_button()
	
	if btn_back != null:
		btn_back.pressed.connect(_on_btn_back_pressed)
	if btn_start != null:
		btn_start.pressed.connect(_on_btn_start_pressed)
	if btn_castes != null:
		btn_castes.pressed.connect(_on_btn_castas_pressed)

func _build_heroes_ui() -> void:
	if heroes_container == null:
		return
	for child in heroes_container.get_children():
		child.queue_free()
	
	for hero in HERO_DEFS:
		var is_sel: bool = selected_heroes.get(hero.id, false)
		var is_auto: bool = hero.get("auto", false)

		var card: PanelContainer = PanelContainer.new()
		card.custom_minimum_size = Vector2(246, 84)
		
		var style: StyleBoxFlat = StyleBoxFlat.new()
		if is_auto:
			style.bg_color = Color(0.12, 0.06, 0.22, 0.95)
			style.border_color = Color(0.85, 0.45, 1.0, 1.0)
		elif is_sel:
			style.bg_color = Color(0.10, 0.08, 0.20, 0.95)
			style.border_color = Color(0.95, 0.8, 0.25, 1.0)
		else:
			style.bg_color = Color(0.06, 0.05, 0.12, 0.9)
			style.border_color = Color(0.22, 0.20, 0.35, 0.8)

		style.set_corner_radius_all(8)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		card.add_theme_stylebox_override("panel", style)
		
		var card_inner: Control = Control.new()
		card_inner.custom_minimum_size = Vector2(246, 84)
		card.add_child(card_inner)
		
		var hbox: HBoxContainer = HBoxContainer.new()
		hbox.set_anchors_preset(Control.PRESET_FULL_RECT)
		hbox.offset_left = 10
		hbox.offset_right = -10
		hbox.offset_top = 8
		hbox.offset_bottom = -8
		hbox.add_theme_constant_override("separation", 12)
		card_inner.add_child(hbox)
		
		# Caixa do Retrato com borda
		var avatar_box: PanelContainer = PanelContainer.new()
		avatar_box.custom_minimum_size = Vector2(64, 64)
		var av_style: StyleBoxFlat = StyleBoxFlat.new()
		av_style.bg_color = Color(0.04, 0.03, 0.08, 0.9)
		av_style.set_corner_radius_all(6)
		av_style.border_width_left = 1
		av_style.border_width_top = 1
		av_style.border_width_right = 1
		av_style.border_width_bottom = 1
		av_style.border_color = Color(0.7, 0.45, 1.0, 0.8) if is_auto else (Color(0.9, 0.75, 0.2, 0.8) if is_sel else Color(0.3, 0.3, 0.45, 0.6))
		avatar_box.add_theme_stylebox_override("panel", av_style)
		hbox.add_child(avatar_box)

		var icon_rect: TextureRect = TextureRect.new()
		icon_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
		icon_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		var sprite_path: String = hero.get("sprite", "")
		if sprite_path != "" and ResourceLoader.exists(sprite_path):
			icon_rect.texture = load(sprite_path)
		else:
			icon_rect.texture = _create_placeholder_texture()
		avatar_box.add_child(icon_rect)
		
		# Detalhes do Herói
		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hbox.add_child(vbox)
		
		var lbl_nome: Label = Label.new()
		lbl_nome.text = hero.nome
		lbl_nome.add_theme_font_size_override("font_size", 15)
		lbl_nome.add_theme_color_override("font_color", Color(1.0, 0.88, 0.35) if (is_sel or is_auto) else Color(0.92, 0.94, 1.0))
		vbox.add_child(lbl_nome)
		
		var lbl_classe: Label = Label.new()
		lbl_classe.text = hero.classe
		lbl_classe.add_theme_font_size_override("font_size", 12)
		lbl_classe.add_theme_color_override("font_color", Color(0.7, 0.6, 0.9) if is_auto else Color(0.6, 0.65, 0.8))
		vbox.add_child(lbl_classe)
		
		if is_auto:
			var lbl_auto_tag: Label = Label.new()
			lbl_auto_tag.text = "⚙ CONTROLADO POR IA"
			lbl_auto_tag.add_theme_font_size_override("font_size", 9)
			lbl_auto_tag.add_theme_color_override("font_color", Color(0.85, 0.55, 1.0))
			vbox.add_child(lbl_auto_tag)
		
		# Badges de Seleção e AUTO
		if is_sel:
			var dot: ColorRect = ColorRect.new()
			dot.custom_minimum_size = Vector2(10, 10)
			dot.color = Color(0.2, 0.95, 0.45, 1.0)
			dot.set_anchors_preset(Control.PRESET_TOP_RIGHT)
			dot.position = Vector2(226, 8)
			card_inner.add_child(dot)
		elif is_auto:
			var badge_lbl: Label = Label.new()
			badge_lbl.text = "● AUTO"
			badge_lbl.add_theme_font_size_override("font_size", 10)
			badge_lbl.add_theme_color_override("font_color", Color(0.9, 0.65, 1.0))
			badge_lbl.position = Vector2(195, 6)
			card_inner.add_child(badge_lbl)
		
		# Botão invisível clicável
		var btn: Button = Button.new()
		btn.flat = true
		btn.set_anchors_preset(Control.PRESET_FULL_RECT)
		if not is_auto:
			btn.pressed.connect(_on_hero_clicked.bind(hero.id))
		card.add_child(btn)
		
		heroes_container.add_child(card)

func _create_placeholder_texture() -> ImageTexture:
	var img: Image = Image.create(32, 32, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.2, 0.15, 0.3, 0.5))
	return ImageTexture.create_from_image(img)

func _build_diff_ui() -> void:
	if diff_container == null:
		return
	for child in diff_container.get_children():
		child.queue_free()
	
	for i in range(DIFFICULTIES.size()):
		var d: Dictionary = DIFFICULTIES[i]
		var is_sel: bool = (i == selected_diff_index)
		
		var panel: PanelContainer = PanelContainer.new()
		panel.custom_minimum_size = Vector2(230, 60)
		
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color(0.08, 0.07, 0.15, 0.9)
		style.set_corner_radius_all(6)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(1.0, 0.8, 0.2, 1.0) if is_sel else Color(0.2, 0.2, 0.35, 0.8)
		panel.add_theme_stylebox_override("panel", style)
		
		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		panel.add_child(vbox)
		
		var lbl_t: Label = Label.new()
		lbl_t.text = d.nome
		lbl_t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_t.add_theme_font_size_override("font_size", 14)
		lbl_t.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3) if is_sel else Color(0.85, 0.85, 0.95))
		vbox.add_child(lbl_t)
		
		var lbl_d: Label = Label.new()
		lbl_d.text = d.desc
		lbl_d.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_d.add_theme_font_size_override("font_size", 11)
		lbl_d.add_theme_color_override("font_color", Color(0.5, 0.5, 0.7))
		vbox.add_child(lbl_d)
		
		var btn: Button = Button.new()
		btn.flat = true
		btn.set_anchors_preset(Control.PRESET_FULL_RECT)
		btn.pressed.connect(_on_diff_clicked.bind(i))
		panel.add_child(btn)
		
		diff_container.add_child(panel)

func _build_res_ui() -> void:
	if res_container == null:
		return
	for child in res_container.get_children():
		child.queue_free()
	
	for i in range(RESOLUTIONS.size()):
		var r: Vector2i = RESOLUTIONS[i]
		var is_sel: bool = (i == selected_res_index)
		
		var btn: Button = Button.new()
		btn.custom_minimum_size = Vector2(95, 36)
		btn.text = "%dx%d" % [r.x, r.y]
		btn.focus_mode = Control.FOCUS_NONE
		
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color(0.12, 0.1, 0.22, 0.9) if is_sel else Color(0.06, 0.05, 0.12, 0.8)
		style.set_corner_radius_all(5)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(0.4, 0.75, 1.0, 1.0) if is_sel else Color(0.2, 0.18, 0.3, 0.8)
		btn.add_theme_stylebox_override("normal", style)
		
		btn.pressed.connect(_on_res_clicked.bind(i))
		res_container.add_child(btn)

func _on_hero_clicked(hero_id: String) -> void:
	selected_heroes[hero_id] = not selected_heroes.get(hero_id, false)
	_play_click_sfx()
	_build_heroes_ui()
	_update_start_button()

func _on_diff_clicked(idx: int) -> void:
	selected_diff_index = idx
	_play_click_sfx()
	_build_diff_ui()

func _on_res_clicked(idx: int) -> void:
	selected_res_index = idx
	_play_click_sfx()
	_build_res_ui()
	var res: Vector2i = RESOLUTIONS[idx]
	DisplayServer.window_set_size(res)

func _update_start_button() -> void:
	var count: int = 0
	for k in selected_heroes:
		if selected_heroes[k]:
			count += 1
	if btn_start != null:
		btn_start.text = "INICIAR CERCO (%d herói%s)" % [count, "s" if count != 1 else ""]
		btn_start.disabled = (count == 0)

func _on_btn_back_pressed() -> void:
	_play_click_sfx()
	get_tree().change_scene_to_file("res://scenes/main/Menu.tscn")

func _on_btn_castas_pressed() -> void:
	_play_click_sfx()
	# Transiciona para a batalha do Cerco ou visualizador
	_on_btn_start_pressed()

func _on_btn_start_pressed() -> void:
	_play_click_sfx()
	var config: Dictionary = {
		"herois": selected_heroes,
		"dificuldade": DIFFICULTIES[selected_diff_index],
		"resolucao": RESOLUTIONS[selected_res_index]
	}
	cerco_iniciado.emit(config)
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		gm.set_meta("cerco_config", config)
	get_tree().change_scene_to_file("res://scenes/main/Main.tscn")

func _play_click_sfx() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("button_click", 1.0, 1.0)

var _options_modal: OptionsMenu = null

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			_on_btn_back_pressed()
		elif event.keycode == KEY_O:
			_open_options_modal()

func _open_options_modal() -> void:
	_play_click_sfx()
	if not is_inside_tree():
		return
	if _options_modal == null:
		var scene = load("res://scenes/ui/OptionsMenu.tscn")
		if scene != null:
			_options_modal = scene.instantiate() as OptionsMenu
			add_child(_options_modal)
	if _options_modal != null:
		_options_modal.open()
