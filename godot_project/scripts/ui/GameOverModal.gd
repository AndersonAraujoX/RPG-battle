# res://scripts/ui/GameOverModal.gd
class_name GameOverModal
extends Control

## GameOverModal: Modal de Vitória ou Derrota do Cerco da Fortaleza.
## Apresenta o resultado tático da batalha, estatísticas consolidadas e opções
## de reiniciar o cerco ou retornar ao Menu Principal.

signal restart_requested()
signal menu_requested()

var is_victory: bool = false
var victory_reason: String = ""
var battle_stats: Dictionary = {}

@onready var backdrop: ColorRect = get_node_or_null("Backdrop")
@onready var modal_panel: PanelContainer = get_node_or_null("CenterContainer/ModalPanel")
@onready var lbl_header: Label = get_node_or_null("CenterContainer/ModalPanel/VBox/HeaderLabel")
@onready var lbl_subtitle: Label = get_node_or_null("CenterContainer/ModalPanel/VBox/SubtitleLabel")
@onready var lbl_stats: RichTextLabel = get_node_or_null("CenterContainer/ModalPanel/VBox/StatsLabel")
@onready var btn_restart: Button = get_node_or_null("CenterContainer/ModalPanel/VBox/ButtonsHBox/BtnRestart")
@onready var btn_menu: Button = get_node_or_null("CenterContainer/ModalPanel/VBox/ButtonsHBox/BtnMenu")

func _ready() -> void:
	if btn_restart != null and not btn_restart.pressed.is_connected(_on_btn_restart_pressed):
		btn_restart.pressed.connect(_on_btn_restart_pressed)
	if btn_menu != null and not btn_menu.pressed.is_connected(_on_btn_menu_pressed):
		btn_menu.pressed.connect(_on_btn_menu_pressed)
	_apply_visuals()

## Configura os dados da tela de fim de jogo e atualiza a interface
func setup(p_is_victory: bool, p_reason: String, p_stats: Dictionary = {}) -> void:
	is_victory = p_is_victory
	victory_reason = p_reason
	battle_stats = p_stats
	_apply_visuals()

func _apply_visuals() -> void:
	if not is_inside_tree():
		return

	if lbl_header != null:
		if is_victory:
			lbl_header.text = "🏆 VITÓRIA TÁTICA!"
			lbl_header.modulate = Color(1.0, 0.85, 0.25)
		else:
			lbl_header.text = "💀 A FORTALEZA CAIU"
			lbl_header.modulate = Color(1.0, 0.25, 0.25)

	if lbl_subtitle != null:
		var default_msg: String = "A Fortaleza de Kuar-Tor resistiu heroicamente ao cerco!" if is_victory else "O Enxame Isectum violou as defesas sagradas da fortaleza."
		lbl_subtitle.text = victory_reason if not victory_reason.is_empty() else default_msg

	if lbl_stats != null:
		var rounds: int = int(battle_stats.get("rounds_survived", 1))
		var kills: int = int(battle_stats.get("enemies_defeated", 0))
		var cards: int = int(battle_stats.get("cards_played", 0))
		var wood: int = int(battle_stats.get("wood", 0))
		var leather: int = int(battle_stats.get("leather", 0))
		var metal: int = int(battle_stats.get("metal", 0))
		var crystals: int = int(battle_stats.get("crystals", 0))

		var bb: String = "[center]"
		bb += "[color=#e0d0b0]⚔️ Rodadas Resistidas:[/color] [b][color=#ffffff]%d[/color][/b]   |   " % rounds
		bb += "[color=#e0d0b0]🐛 Insetos Abatidos:[/color] [b][color=#ffdd66]%d[/color][/b]\n" % kills
		bb += "[color=#e0d0b0]🃏 Cartas Jogadas:[/color] [b][color=#ffffff]%d[/color][/b]   |   " % cards
		bb += "[color=#e0d0b0]💎 Cristais Residuais:[/color] [b][color=#77ddff]%d[/color][/b]\n" % crystals
		bb += "[color=#8899aa]Recursos da Fortaleza:[/color] 🪵 %d  |  🪓 %d  |  ⚔️ %d" % [wood, leather, metal]
		bb += "[/center]"
		lbl_stats.text = bb

	# Estilo visual do painel central
	if modal_panel != null:
		var sb: StyleBoxFlat = StyleBoxFlat.new()
		sb.bg_color = Color(0.06, 0.08, 0.12, 0.96)
		sb.set_border_width_all(2)
		sb.border_color = Color(0.9, 0.75, 0.2, 0.9) if is_victory else Color(0.85, 0.2, 0.2, 0.9)
		sb.set_corner_radius_all(8)
		sb.content_margin_left = 28
		sb.content_margin_right = 28
		sb.content_margin_top = 24
		sb.content_margin_bottom = 24
		modal_panel.add_theme_stylebox_override("panel", sb)

func _on_btn_restart_pressed() -> void:
	_play_click_sfx()
	restart_requested.emit()

func _on_btn_menu_pressed() -> void:
	_play_click_sfx()
	menu_requested.emit()

func _play_click_sfx() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("button_click", 1.0, 1.0)

func _unhandled_input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER or event.keycode == KEY_SPACE:
			_on_btn_restart_pressed()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_ESCAPE:
			_on_btn_menu_pressed()
			get_viewport().set_input_as_handled()
