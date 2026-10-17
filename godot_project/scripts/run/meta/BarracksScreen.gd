# res://scripts/run/meta/BarracksScreen.gd
class_name BarracksScreen
extends Control

## Quartel dos Heróis & Painel de Ascensão (Marcos M7 & M8)
## Permite ao jogador desbloquear novos heróis com Âmbar Real acumulado
## e selecionar o Nível de Ascensão desejado (1 a 10) para as próximas expedições.

signal back_requested()
signal hero_unlocked_ui(hero_id: String)
signal ascension_selected_ui(level: int)

@onready var title_label: Label = find_child("TitleLabel", true, false) as Label
@onready var amber_label: Label = find_child("AmberLabel", true, false) as Label
@onready var heroes_container: VBoxContainer = find_child("HeroesContainer", true, false) as VBoxContainer
@onready var ascension_label: Label = find_child("AscensionLabel", true, false) as Label
@onready var btn_ascension_down: Button = find_child("BtnDown", true, false) as Button
@onready var btn_ascension_up: Button = find_child("BtnUp", true, false) as Button
@onready var btn_back: Button = find_child("BtnBack", true, false) as Button

var meta: MetaProgression = null

func _ready() -> void:
	if meta == null:
		meta = MetaProgression.get_instance()
	if btn_back != null and not btn_back.pressed.is_connected(_on_back_pressed):
		btn_back.pressed.connect(_on_back_pressed)
	if btn_ascension_down != null and not btn_ascension_down.pressed.is_connected(_on_ascension_down):
		btn_ascension_down.pressed.connect(_on_ascension_down)
	if btn_ascension_up != null and not btn_ascension_up.pressed.is_connected(_on_ascension_up):
		btn_ascension_up.pressed.connect(_on_ascension_up)

	refresh_ui()
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_bgm"):
			am.play_bgm("quartel", 1.0)

func setup(p_meta: MetaProgression) -> void:
	meta = p_meta
	refresh_ui()

func refresh_ui() -> void:
	if meta == null:
		return

	if amber_label != null:
		amber_label.text = "Ambar Real: %d" % meta.amber_balance

	_refresh_heroes_list()
	_refresh_ascension_controls()

func _refresh_heroes_list() -> void:
	if heroes_container == null:
		return

	for child in heroes_container.get_children():
		child.queue_free()

	for hid in MetaProgression.HERO_UNLOCK_COSTS:
		var row: HBoxContainer = HBoxContainer.new()
		row.name = "Row_%s" % hid

		var name_lbl: Label = Label.new()
		name_lbl.name = "NameLabel"
		name_lbl.text = hid.capitalize()
		name_lbl.custom_minimum_size = Vector2(150, 0)
		row.add_child(name_lbl)

		var status_lbl: Label = Label.new()
		status_lbl.name = "StatusLabel"
		row.add_child(status_lbl)

		if meta.is_hero_unlocked(hid):
			status_lbl.text = "[Desbloqueado]"
			status_lbl.modulate = Color(0.3, 0.9, 0.3)
		else:
			var cost: int = MetaProgression.HERO_UNLOCK_COSTS[hid]
			status_lbl.text = "Custo: %d Ambar" % cost
			status_lbl.modulate = Color(0.8, 0.8, 0.8)

			var unlock_btn: Button = Button.new()
			unlock_btn.name = "BtnUnlock_%s" % hid
			unlock_btn.text = "Desbloquear"
			unlock_btn.disabled = not meta.can_unlock_hero(hid)
			unlock_btn.pressed.connect(func(): _on_unlock_hero_clicked(hid))
			row.add_child(unlock_btn)

		heroes_container.add_child(row)

func _refresh_ascension_controls() -> void:
	if ascension_label == null:
		return

	if not meta.is_ascension_unlocked():
		ascension_label.text = "Ascensao: Bloqueada (Venca o Rei Isectum para liberar)"
		if btn_ascension_down != null: btn_ascension_down.disabled = true
		if btn_ascension_up != null: btn_ascension_up.disabled = true
	else:
		ascension_label.text = "Ascensao: Nivel %d (Max: %d)" % [meta.current_ascension, meta.max_unlocked_ascension]
		if btn_ascension_down != null:
			btn_ascension_down.disabled = (meta.current_ascension <= 0)
		if btn_ascension_up != null:
			btn_ascension_up.disabled = (meta.current_ascension >= meta.max_unlocked_ascension)

func _on_unlock_hero_clicked(hid: String) -> void:
	if meta != null and meta.unlock_hero(hid):
		hero_unlocked_ui.emit(hid)
		refresh_ui()

func _on_ascension_down() -> void:
	if meta != null and meta.current_ascension > 0:
		meta.set_ascension_level(meta.current_ascension - 1)
		ascension_selected_ui.emit(meta.current_ascension)
		refresh_ui()

func _on_ascension_up() -> void:
	if meta != null and meta.current_ascension < meta.max_unlocked_ascension:
		meta.set_ascension_level(meta.current_ascension + 1)
		ascension_selected_ui.emit(meta.current_ascension)
		refresh_ui()

func _on_back_pressed() -> void:
	back_requested.emit()
