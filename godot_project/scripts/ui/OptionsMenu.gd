# res://scripts/ui/OptionsMenu.gd
class_name OptionsMenu
extends Control

## OptionsMenu: Painel modal de configurações de áudio e som.
## Permite ajustar volumes de Música (BGM), Efeitos (SFX) e Master,
## com sliders interativos, botões +/- e controle de mute.

signal closed()

@onready var bgm_slider: HSlider = find_child("BgmSlider", true, false) as HSlider
@onready var bgm_label: Label = find_child("BgmValueLabel", true, false) as Label
@onready var btn_bgm_down: Button = find_child("BtnBgmDown", true, false) as Button
@onready var btn_bgm_up: Button = find_child("BtnBgmUp", true, false) as Button
@onready var btn_bgm_mute: Button = find_child("BtnBgmMute", true, false) as Button

@onready var sfx_slider: HSlider = find_child("SfxSlider", true, false) as HSlider
@onready var sfx_label: Label = find_child("SfxValueLabel", true, false) as Label
@onready var btn_sfx_down: Button = find_child("BtnSfxDown", true, false) as Button
@onready var btn_sfx_up: Button = find_child("BtnSfxUp", true, false) as Button
@onready var btn_sfx_mute: Button = find_child("BtnSfxMute", true, false) as Button

@onready var master_slider: HSlider = find_child("MasterSlider", true, false) as HSlider
@onready var master_label: Label = find_child("MasterValueLabel", true, false) as Label
@onready var btn_master_down: Button = find_child("BtnMasterDown", true, false) as Button
@onready var btn_master_up: Button = find_child("BtnMasterUp", true, false) as Button

@onready var btn_close: Button = find_child("BtnClose", true, false) as Button
@onready var backdrop: Control = find_child("Backdrop", true, false) as Control

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_wire_signals()
	refresh_values()
	_connect_audio_manager_signals()

func _wire_signals() -> void:
	if bgm_slider != null and not bgm_slider.value_changed.is_connected(_on_bgm_slider_changed):
		bgm_slider.value_changed.connect(_on_bgm_slider_changed)
	if btn_bgm_down != null and not btn_bgm_down.pressed.is_connected(_on_btn_bgm_down_pressed):
		btn_bgm_down.pressed.connect(_on_btn_bgm_down_pressed)
	if btn_bgm_up != null and not btn_bgm_up.pressed.is_connected(_on_btn_bgm_up_pressed):
		btn_bgm_up.pressed.connect(_on_btn_bgm_up_pressed)
	if btn_bgm_mute != null and not btn_bgm_mute.pressed.is_connected(_on_btn_bgm_mute_pressed):
		btn_bgm_mute.pressed.connect(_on_btn_bgm_mute_pressed)

	if sfx_slider != null and not sfx_slider.value_changed.is_connected(_on_sfx_slider_changed):
		sfx_slider.value_changed.connect(_on_sfx_slider_changed)
	if btn_sfx_down != null and not btn_sfx_down.pressed.is_connected(_on_btn_sfx_down_pressed):
		btn_sfx_down.pressed.connect(_on_btn_sfx_down_pressed)
	if btn_sfx_up != null and not btn_sfx_up.pressed.is_connected(_on_btn_sfx_up_pressed):
		btn_sfx_up.pressed.connect(_on_btn_sfx_up_pressed)
	if btn_sfx_mute != null and not btn_sfx_mute.pressed.is_connected(_on_btn_sfx_mute_pressed):
		btn_sfx_mute.pressed.connect(_on_btn_sfx_mute_pressed)

	if master_slider != null and not master_slider.value_changed.is_connected(_on_master_slider_changed):
		master_slider.value_changed.connect(_on_master_slider_changed)
	if btn_master_down != null and not btn_master_down.pressed.is_connected(_on_btn_master_down_pressed):
		btn_master_down.pressed.connect(_on_btn_master_down_pressed)
	if btn_master_up != null and not btn_master_up.pressed.is_connected(_on_btn_master_up_pressed):
		btn_master_up.pressed.connect(_on_btn_master_up_pressed)

	if btn_close != null and not btn_close.pressed.is_connected(close):
		btn_close.pressed.connect(close)
	if backdrop != null and backdrop.has_signal("gui_input") and not backdrop.gui_input.is_connected(_on_backdrop_gui_input):
		backdrop.gui_input.connect(_on_backdrop_gui_input)

var audio_manager: Node = null

func _connect_audio_manager_signals() -> void:
	var am = _get_audio_manager()
	if am != null and am.has_signal("volume_changed") and not am.volume_changed.is_connected(_on_audio_manager_volume_changed):
		am.volume_changed.connect(_on_audio_manager_volume_changed)

func _on_audio_manager_volume_changed(_bus_name: String, _volume: float, _is_muted: bool) -> void:
	refresh_values()

func _get_audio_manager() -> Node:
	if audio_manager != null and is_instance_valid(audio_manager):
		return audio_manager
	if not is_inside_tree():
		return null
	var tree = get_tree()
	if tree == null:
		return null
	if tree.root.has_node("AudioManager"):
		return tree.root.get_node("AudioManager")
	for child in tree.root.get_children():
		if child.name == "AudioManager":
			return child
		var sub = child.find_child("AudioManager", true, false)
		if sub != null:
			return sub
	return null

func refresh_values() -> void:
	var am = _get_audio_manager()
	if am == null:
		return

	# BGM
	var bgm_vol: float = am.get_bus_volume("BGM") if am.has_method("get_bus_volume") else 0.6
	var bgm_muted: bool = am.is_bus_muted("BGM") if am.has_method("is_bus_muted") else false
	if bgm_slider != null:
		bgm_slider.set_value_no_signal(bgm_vol)
	if bgm_label != null:
		bgm_label.text = "MUTADO" if bgm_muted else "%d%%" % int(round(bgm_vol * 100))
	if btn_bgm_mute != null:
		btn_bgm_mute.text = "🔇 Desmutar" if bgm_muted else "🔊 Mute"

	# SFX
	var sfx_vol: float = am.get_bus_volume("SFX") if am.has_method("get_bus_volume") else 0.8
	var sfx_muted: bool = am.is_bus_muted("SFX") if am.has_method("is_bus_muted") else false
	if sfx_slider != null:
		sfx_slider.set_value_no_signal(sfx_vol)
	if sfx_label != null:
		sfx_label.text = "MUTADO" if sfx_muted else "%d%%" % int(round(sfx_vol * 100))
	if btn_sfx_mute != null:
		btn_sfx_mute.text = "🔇 Desmutar" if sfx_muted else "🔊 Mute"

	# Master
	var master_vol: float = am.get_bus_volume("Master") if am.has_method("get_bus_volume") else 1.0
	if master_slider != null:
		master_slider.set_value_no_signal(master_vol)
	if master_label != null:
		master_label.text = "%d%%" % int(round(master_vol * 100))

# ── Handlers BGM ───────────────────────────────────────────────────────────

func _on_bgm_slider_changed(value: float) -> void:
	var am = _get_audio_manager()
	if am != null and am.has_method("set_bus_volume"):
		am.set_bus_volume("BGM", value)
	refresh_values()

func _on_btn_bgm_down_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("change_bgm_volume"):
			am.change_bgm_volume(-0.1)
		elif am.has_method("set_bus_volume"):
			var cur = am.get_bus_volume("BGM")
			am.set_bus_volume("BGM", max(0.0, cur - 0.1))
	refresh_values()

func _on_btn_bgm_up_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("change_bgm_volume"):
			am.change_bgm_volume(+0.1)
		elif am.has_method("set_bus_volume"):
			var cur = am.get_bus_volume("BGM")
			am.set_bus_volume("BGM", min(1.0, cur + 0.1))
	refresh_values()

func _on_btn_bgm_mute_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("toggle_bgm_mute"):
			am.toggle_bgm_mute()
		elif am.has_method("set_bus_muted"):
			var cur = am.is_bus_muted("BGM")
			am.set_bus_muted("BGM", not cur)
	refresh_values()

# ── Handlers SFX ───────────────────────────────────────────────────────────

func _on_sfx_slider_changed(value: float) -> void:
	var am = _get_audio_manager()
	if am != null and am.has_method("set_bus_volume"):
		am.set_bus_volume("SFX", value)
	refresh_values()

func _on_btn_sfx_down_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("change_sfx_volume"):
			am.change_sfx_volume(-0.1)
		elif am.has_method("set_bus_volume"):
			var cur = am.get_bus_volume("SFX")
			am.set_bus_volume("SFX", max(0.0, cur - 0.1))
	refresh_values()

func _on_btn_sfx_up_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("change_sfx_volume"):
			am.change_sfx_volume(+0.1)
		elif am.has_method("set_bus_volume"):
			var cur = am.get_bus_volume("SFX")
			am.set_bus_volume("SFX", min(1.0, cur + 0.1))
	refresh_values()

func _on_btn_sfx_mute_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null:
		if am.has_method("toggle_sfx_mute"):
			am.toggle_sfx_mute()
		elif am.has_method("set_bus_muted"):
			var cur = am.is_bus_muted("SFX")
			am.set_bus_muted("SFX", not cur)
	refresh_values()

# ── Handlers Master ────────────────────────────────────────────────────────

func _on_master_slider_changed(value: float) -> void:
	var am = _get_audio_manager()
	if am != null and am.has_method("set_bus_volume"):
		am.set_bus_volume("Master", value)
	refresh_values()

func _on_btn_master_down_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null and am.has_method("set_bus_volume"):
		var cur = am.get_bus_volume("Master")
		am.set_bus_volume("Master", max(0.0, cur - 0.1))
	refresh_values()

func _on_btn_master_up_pressed() -> void:
	_play_click_sfx()
	var am = _get_audio_manager()
	if am != null and am.has_method("set_bus_volume"):
		var cur = am.get_bus_volume("Master")
		am.set_bus_volume("Master", min(1.0, cur + 0.1))
	refresh_values()

# ── Modal Control & Input ──────────────────────────────────────────────────

func open() -> void:
	refresh_values()
	visible = true
	# Capture focus on close button
	if btn_close != null:
		btn_close.grab_focus()

func close() -> void:
	_play_click_sfx()
	visible = false
	closed.emit()

func _on_backdrop_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		close()

func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE or event.keycode == KEY_O:
			close()
			get_viewport().set_input_as_handled()

func _play_click_sfx() -> void:
	var am = _get_audio_manager()
	if am != null and am.has_method("play_sfx"):
		am.play_sfx("button_click", 0.6, 1.0)
