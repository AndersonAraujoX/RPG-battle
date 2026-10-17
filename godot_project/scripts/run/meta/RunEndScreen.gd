# res://scripts/run/meta/RunEndScreen.gd
class_name RunEndScreen
extends Control

## Tela de Fim de Expedição (Vitória Épica ou Derrota) (Marcos M7 & M8)
## Apresenta o resumo estatístico da run, o cálculo final de Âmbar Real,
## o impacto dos 3 Corações e botões de navegação para o Menu Principal e Quartel.

signal return_to_menu_requested()
signal open_barracks_requested()

@onready var title_label: Label = find_child("TitleLabel", true, false) as Label
@onready var subtitle_label: Label = find_child("SubtitleLabel", true, false) as Label
@onready var stats_label: Label = find_child("StatsLabel", true, false) as Label
@onready var amber_summary_label: Label = find_child("AmberSummaryLabel", true, false) as Label
@onready var btn_menu: Button = find_child("BtnMenu", true, false) as Button
@onready var btn_barracks: Button = find_child("BtnBarracks", true, false) as Button

var victory: bool = false
var summary_data: Dictionary = {}

func _ready() -> void:
	if btn_menu != null and not btn_menu.pressed.is_connected(_on_menu_pressed):
		btn_menu.pressed.connect(_on_menu_pressed)
	if btn_barracks != null and not btn_barracks.pressed.is_connected(_on_barracks_pressed):
		btn_barracks.pressed.connect(_on_barracks_pressed)

	refresh_ui()

func setup(p_victory: bool, run_state: RunState, meta: MetaProgression = null) -> void:
	victory = p_victory
	var amber_earned: int = 0
	var floors: int = 0
	var bosses: int = 0
	var kills: int = 0
	var hearts_spared: bool = false

	if run_state != null:
		floors = run_state.floors_cleared
		bosses = run_state.bosses_defeated
		kills = run_state.enemies_killed
		amber_earned = run_state.calculate_amber()
		hearts_spared = run_state.destroyed_hearts.is_empty()

	var total_amber: int = meta.amber_balance if meta != null else amber_earned

	summary_data = {
		"victory": victory,
		"floors": floors,
		"bosses": bosses,
		"kills": kills,
		"amber_earned": amber_earned,
		"total_amber": total_amber,
		"hearts_spared": hearts_spared,
	}

	refresh_ui()
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_bgm"):
			am.play_bgm("vitoria" if victory else "derrota", 1.0)

func refresh_ui() -> void:
	if title_label != null:
		if victory:
			title_label.text = "VITORIA SUPREMA"
			title_label.modulate = Color(1.0, 0.85, 0.2)
		else:
			title_label.text = "EXPEDICAO FRACASSADA"
			title_label.modulate = Color(0.9, 0.2, 0.2)

	if subtitle_label != null:
		if victory:
			if summary_data.get("hearts_spared", false):
				subtitle_label.text = "O Rei Isectum caiu em sua forca total! Conquista lendaria: Ambar em dobro!"
			else:
				subtitle_label.text = "A fortaleza de Karak-Dur esta a salvo do enxame ancestral."
		else:
			subtitle_label.text = "O grupo caiu nos abismos subterraneos. Seu sacrificio rendeu Ambar Real."

	if stats_label != null:
		stats_label.text = "Andares Percorridos: %d  |  Chefes Abatidos: %d  |  Inimigos Derrotados: %d" % [
			int(summary_data.get("floors", 0)),
			int(summary_data.get("bosses", 0)),
			int(summary_data.get("kills", 0)),
		]

	if amber_summary_label != null:
		amber_summary_label.text = "Ambar Recuperado: +%d  (Total no Quartel: %d)" % [
			int(summary_data.get("amber_earned", 0)),
			int(summary_data.get("total_amber", 0)),
		]

func _on_menu_pressed() -> void:
	return_to_menu_requested.emit()

func _on_barracks_pressed() -> void:
	open_barracks_requested.emit()
