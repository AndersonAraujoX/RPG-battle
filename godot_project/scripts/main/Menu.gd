# res://scripts/main/Menu.gd
class_name MainMenu
extends Control

## Main Menu Screen Controller for RPG-battle: Cerco contra Isectum.
## Features the stained-glass background, epic title with heavy outlines,
## and the 6-button dark fantasy grid (JOGAR CERCO, NOVA CAMPANHA, CONTINUAR, OPÇÕES, DEV TOOLS, SAIR).

@onready var btn_jogar_cerco: Button = get_node_or_null("UI/GridButtons/BtnJogarCerco")
@onready var btn_nova_campanha: Button = get_node_or_null("UI/GridButtons/BtnNovaCampanha")
@onready var btn_continuar: Button = get_node_or_null("UI/GridButtons/BtnContinuar")
@onready var btn_opcoes: Button = get_node_or_null("UI/GridButtons/BtnOpcoes")
@onready var btn_dev_tools: Button = get_node_or_null("UI/GridButtons/BtnDevTools")
@onready var btn_sair: Button = get_node_or_null("UI/GridButtons/BtnSair")
@onready var btn_quartel: Button = get_node_or_null("UI/GridButtons/BtnQuartel")
@onready var lbl_meta_status: Label = get_node_or_null("UI/MetaBanner/LblMetaStatus")
@onready var lbl_campanha_sub: Label = get_node_or_null("TitleContainer/LblCampanhaSub")

# Compatibilidade para referências legadas
@onready var btn_play: Button = btn_jogar_cerco
@onready var btn_castes: Button = btn_nova_campanha
@onready var btn_multiplayer: Button = btn_opcoes
@onready var btn_quit: Button = btn_sair
@onready var btn_barracks: Button = btn_quartel

func _ready() -> void:
	if btn_jogar_cerco == null:
		btn_jogar_cerco = get_node_or_null("UI/GridButtons/BtnJogarCerco")
	if btn_nova_campanha == null:
		btn_nova_campanha = get_node_or_null("UI/GridButtons/BtnNovaCampanha")
	if btn_continuar == null:
		btn_continuar = get_node_or_null("UI/GridButtons/BtnContinuar")
	if btn_opcoes == null:
		btn_opcoes = get_node_or_null("UI/GridButtons/BtnOpcoes")
	if btn_dev_tools == null:
		btn_dev_tools = get_node_or_null("UI/GridButtons/BtnDevTools")
	if btn_sair == null:
		btn_sair = get_node_or_null("UI/GridButtons/BtnSair")
	if btn_quartel == null:
		btn_quartel = get_node_or_null("UI/GridButtons/BtnQuartel")
	if lbl_meta_status == null:
		lbl_meta_status = get_node_or_null("UI/MetaBanner/LblMetaStatus")
	if lbl_campanha_sub == null:
		lbl_campanha_sub = get_node_or_null("TitleContainer/LblCampanhaSub")

	btn_play = btn_jogar_cerco
	btn_castes = btn_nova_campanha
	btn_multiplayer = btn_opcoes
	btn_quit = btn_sair
	btn_barracks = btn_quartel
	_wire_buttons()
	_update_meta_status()
	_play_menu_music()

func _wire_buttons() -> void:
	if btn_jogar_cerco != null and not btn_jogar_cerco.pressed.is_connected(_on_btn_jogar_cerco_pressed):
		btn_jogar_cerco.pressed.connect(_on_btn_jogar_cerco_pressed)
		btn_jogar_cerco.mouse_entered.connect(_play_hover_sound)
	
	if btn_nova_campanha != null and not btn_nova_campanha.pressed.is_connected(_on_btn_nova_campanha_pressed):
		btn_nova_campanha.pressed.connect(_on_btn_nova_campanha_pressed)
		btn_nova_campanha.mouse_entered.connect(_play_hover_sound)
	
	if btn_continuar != null and not btn_continuar.pressed.is_connected(_on_btn_continuar_pressed):
		btn_continuar.pressed.connect(_on_btn_continuar_pressed)
		btn_continuar.mouse_entered.connect(_play_hover_sound)
	
	if btn_opcoes != null and not btn_opcoes.pressed.is_connected(_on_btn_opcoes_pressed):
		btn_opcoes.pressed.connect(_on_btn_opcoes_pressed)
		btn_opcoes.mouse_entered.connect(_play_hover_sound)
	
	if btn_dev_tools != null and not btn_dev_tools.pressed.is_connected(_on_btn_dev_tools_pressed):
		btn_dev_tools.pressed.connect(_on_btn_dev_tools_pressed)
		btn_dev_tools.mouse_entered.connect(_play_hover_sound)
	
	if btn_sair != null and not btn_sair.pressed.is_connected(_on_btn_sair_pressed):
		btn_sair.pressed.connect(_on_btn_sair_pressed)
		btn_sair.mouse_entered.connect(_play_hover_sound)

	if btn_quartel != null and not btn_quartel.pressed.is_connected(_on_btn_quartel_pressed):
		btn_quartel.pressed.connect(_on_btn_quartel_pressed)
		btn_quartel.mouse_entered.connect(_play_hover_sound)

func _play_menu_music() -> void:
	if not is_inside_tree():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_bgm"):
			am.play_bgm("menu")

func _on_btn_jogar_cerco_pressed() -> void:
	_play_click_sound()
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.change_scene_to_file("res://scenes/cerco/CercoSetup.tscn")

func _on_btn_nova_campanha_pressed() -> void:
	_play_click_sound()
	RunSession.start_new(int(Time.get_unix_time_from_system()))
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.change_scene_to_file("res://scenes/run/RunMapScreen.tscn")

func _on_btn_continuar_pressed() -> void:
	_play_click_sound()
	if not RunSession.has_active_run():
		RunSession.start_new(int(Time.get_unix_time_from_system()))
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.change_scene_to_file("res://scenes/run/RunMapScreen.tscn")

var _options_modal: OptionsMenu = null

func _on_btn_opcoes_pressed() -> void:
	_play_click_sound()
	_open_options_modal()

func _open_options_modal() -> void:
	if not is_inside_tree():
		return
	if _options_modal == null:
		var scene = load("res://scenes/ui/OptionsMenu.tscn")
		if scene != null:
			_options_modal = scene.instantiate() as OptionsMenu
			add_child(_options_modal)
	if _options_modal != null:
		_options_modal.open()

func _on_btn_dev_tools_pressed() -> void:
	_play_click_sound()
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.change_scene_to_file("res://scenes/main/Main.tscn")

func _on_btn_sair_pressed() -> void:
	_play_click_sound()
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.quit()

var _barracks_modal: BarracksScreen = null

func _on_btn_quartel_pressed() -> void:
	_play_click_sound()
	_open_barracks_modal()

func _open_barracks_modal() -> void:
	if not is_inside_tree():
		return
	if _barracks_modal == null:
		var scene = load("res://scenes/run/meta/BarracksScreen.tscn")
		if scene != null:
			_barracks_modal = scene.instantiate() as BarracksScreen
		else:
			_barracks_modal = BarracksScreen.new()
		if _barracks_modal != null:
			add_child(_barracks_modal)
			if not _barracks_modal.back_requested.is_connected(_on_barracks_back):
				_barracks_modal.back_requested.connect(_on_barracks_back)
	if _barracks_modal != null:
		_barracks_modal.visible = true
		_barracks_modal.refresh_ui()

func _on_barracks_back() -> void:
	if _barracks_modal != null:
		_barracks_modal.visible = false
	_update_meta_status()

func _update_meta_status() -> void:
	if lbl_meta_status == null:
		return
	var meta: MetaProgression = MetaProgression.get_instance()
	if meta != null:
		lbl_meta_status.text = "Ambar Real: %d  |  Ascensao: Nivel %d" % [meta.amber_balance, meta.current_ascension]

# Handlers legados para compatibilidade
func _on_btn_play_pressed() -> void:
	_on_btn_jogar_cerco_pressed()

func _on_btn_castes_pressed() -> void:
	_on_btn_nova_campanha_pressed()

func _on_btn_multiplayer_pressed() -> void:
	_on_btn_opcoes_pressed()

func _on_btn_quit_pressed() -> void:
	_on_btn_sair_pressed()

func _play_hover_sound() -> void:
	if not is_inside_tree():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("button_click", 0.4, 1.4)

func _play_click_sound() -> void:
	if not is_inside_tree():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("button_click", 1.0, 1.0)
