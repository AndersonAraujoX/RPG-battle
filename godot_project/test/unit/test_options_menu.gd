# res://test/unit/test_options_menu.gd
extends GutTest

## Test suite verifying OptionsMenu functionality:
## - Sliders and labels synchronization with AudioManager
## - BGM volume step buttons ([-] and [+])
## - BGM mute toggle
## - SFX & Master volume controls
## - Boundary clamping (0.0 to 1.0)
## - Modal open/close lifecycle and input handling

var _am: Node = null
var _options: OptionsMenu = null

func before_each() -> void:
	var am_script = load("res://scripts/autoload/AudioManager.gd")
	_am = am_script.new()
	_am.name = "AudioManager"
	add_child_autofree(_am)
	if _am.has_method("_ready"):
		_am._ready()

	var options_scene = load("res://scenes/ui/OptionsMenu.tscn")
	_options = options_scene.instantiate() as OptionsMenu
	_options.audio_manager = _am
	add_child_autofree(_options)
	_options._connect_audio_manager_signals()
	_options.refresh_values()

func after_each() -> void:
	if _am != null and is_instance_valid(_am):
		_am.cleanup()

# ==============================================================================
# SECTION 1: Initialization & Synchronization (AAA)
# ==============================================================================

func test_options_menu_initializes_with_audiomanager_values() -> void:
	# Arrange
	_am.set_bus_volume("BGM", 0.6)
	_am.set_bus_volume("SFX", 0.8)
	_am.set_bus_volume("Master", 1.0)
	
	# Act
	_options.refresh_values()
	
	# Assert
	assert_between(_options.bgm_slider.value, 0.59, 0.61, "BGM slider must reflect 0.6 volume")
	assert_eq(_options.bgm_label.text, "60%", "BGM label must read '60%'")
	assert_between(_options.sfx_slider.value, 0.79, 0.81, "SFX slider must reflect 0.8 volume")
	assert_eq(_options.sfx_label.text, "80%", "SFX label must read '80%'")
	assert_between(_options.master_slider.value, 0.99, 1.01, "Master slider must reflect 1.0 volume")
	assert_eq(_options.master_label.text, "100%", "Master label must read '100%'")

func test_options_menu_open_and_close_lifecycle() -> void:
	# Arrange
	watch_signals(_options)
	_options.visible = false
	
	# Act 1: open
	_options.open()
	
	# Assert 1
	assert_true(_options.visible, "OptionsMenu must become visible on open()")
	
	# Act 2: close
	_options.close()
	
	# Assert 2
	assert_false(_options.visible, "OptionsMenu must become hidden on close()")
	assert_signal_emitted(_options, "closed", "closed signal must be emitted on close()")

# ==============================================================================
# SECTION 2: BGM Volume Controls (Decrease, Increase, Mute)
# ==============================================================================

func test_bgm_down_button_decreases_volume_by_ten_percent() -> void:
	# Arrange
	_am.set_bus_volume("BGM", 0.6)
	_options.refresh_values()
	
	# Act: press [-] button
	_options._on_btn_bgm_down_pressed()
	
	# Assert: volume reduced to ~0.5
	var new_vol: float = _am.get_bus_volume("BGM")
	assert_between(new_vol, 0.49, 0.51, "BGM volume must decrease by 0.1 to 0.5")
	assert_between(_options.bgm_slider.value, 0.49, 0.51, "BGM slider must update to 0.5")
	assert_eq(_options.bgm_label.text, "50%", "BGM label must display '50%'")

func test_bgm_up_button_increases_volume_by_ten_percent() -> void:
	# Arrange
	_am.set_bus_volume("BGM", 0.6)
	_options.refresh_values()
	
	# Act: press [+] button
	_options._on_btn_bgm_up_pressed()
	
	# Assert: volume increased to ~0.7
	var new_vol: float = _am.get_bus_volume("BGM")
	assert_between(new_vol, 0.69, 0.71, "BGM volume must increase by 0.1 to 0.7")
	assert_between(_options.bgm_slider.value, 0.69, 0.71, "BGM slider must update to 0.7")
	assert_eq(_options.bgm_label.text, "70%", "BGM label must display '70%'")

func test_bgm_slider_change_updates_audiomanager() -> void:
	# Arrange
	_am.set_bus_volume("BGM", 0.6)
	
	# Act
	_options._on_bgm_slider_changed(0.35)
	
	# Assert
	var new_vol: float = _am.get_bus_volume("BGM")
	assert_between(new_vol, 0.34, 0.36, "AudioManager BGM volume must update from slider")
	assert_eq(_options.bgm_label.text, "35%", "BGM label must display '35%'")

func test_bgm_mute_button_toggles_mute_state() -> void:
	# Arrange
	_am.set_bus_muted("BGM", false)
	_options.refresh_values()
	assert_false(_am.is_bus_muted("BGM"))
	assert_eq(_options.btn_bgm_mute.text, "🔊 Mute")
	
	# Act 1: toggle mute
	_options._on_btn_bgm_mute_pressed()
	
	# Assert 1
	assert_true(_am.is_bus_muted("BGM"), "BGM must be muted")
	assert_eq(_options.btn_bgm_mute.text, "🔇 Desmutar", "Button text must update to '🔇 Desmutar'")
	assert_eq(_options.bgm_label.text, "MUTADO", "BGM label must display 'MUTADO'")
	
	# Act 2: toggle unmute
	_options._on_btn_bgm_mute_pressed()
	
	# Assert 2
	assert_false(_am.is_bus_muted("BGM"), "BGM must be unmuted")
	assert_eq(_options.btn_bgm_mute.text, "🔊 Mute", "Button text must revert to '🔊 Mute'")

# ==============================================================================
# SECTION 3: Edge Cases & Volume Clamping
# ==============================================================================

func test_bgm_volume_clamping_minimum_at_zero() -> void:
	# Arrange: set volume to 0.05
	_am.set_bus_volume("BGM", 0.05)
	_options.refresh_values()
	
	# Act: decrease twice
	_options._on_btn_bgm_down_pressed()
	_options._on_btn_bgm_down_pressed()
	
	# Assert: volume clamped to 0.0
	assert_eq(_am.get_bus_volume("BGM"), 0.0, "Volume must clamp at 0.0")
	assert_eq(_options.bgm_slider.value, 0.0, "Slider must clamp at 0.0")
	assert_eq(_options.bgm_label.text, "0%", "Label must display '0%'")

func test_bgm_volume_clamping_maximum_at_one() -> void:
	# Arrange: set volume to 0.95
	_am.set_bus_volume("BGM", 0.95)
	_options.refresh_values()
	
	# Act: increase twice
	_options._on_btn_bgm_up_pressed()
	_options._on_btn_bgm_up_pressed()
	
	# Assert: volume clamped to 1.0
	assert_eq(_am.get_bus_volume("BGM"), 1.0, "Volume must clamp at 1.0")
	assert_eq(_options.bgm_slider.value, 1.0, "Slider must clamp at 1.0")
	assert_eq(_options.bgm_label.text, "100%", "Label must display '100%'")

func test_sfx_controls_work_cleanly() -> void:
	# Arrange
	_am.set_bus_volume("SFX", 0.8)
	_options.refresh_values()
	
	# Act: step down then mute
	_options._on_btn_sfx_down_pressed()
	assert_between(_am.get_bus_volume("SFX"), 0.69, 0.71)
	
	_options._on_btn_sfx_mute_pressed()
	assert_true(_am.is_bus_muted("SFX"))
	assert_eq(_options.sfx_label.text, "MUTADO")

func test_options_menu_bare_node_without_tree_safe() -> void:
	# Arrange: bare node not inside any scene tree
	var bare_options: OptionsMenu = OptionsMenu.new()
	
	# Act & Assert: should not crash on any call
	bare_options.refresh_values()
	bare_options._on_bgm_slider_changed(0.5)
	bare_options._on_btn_bgm_down_pressed()
	bare_options._on_btn_bgm_up_pressed()
	bare_options._on_btn_bgm_mute_pressed()
	bare_options.close()
	bare_options.free()
	pass
