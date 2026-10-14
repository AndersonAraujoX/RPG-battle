# res://test/unit/test_audio_manager_fixes.gd
extends GutTest

## Test suite verifying AudioManager fixes:
## - Seamless looping on all BGM tracks
## - Bug-free crossfading (active stream not nullified after tween)
## - Idempotent re-triggering (no echo/duplicate player)
## - Track & SFX aliases
## - Process mode safety on pause
## - Bus volume and mute propagation

var _am: Node = null

func before_each() -> void:
	var am_script = load("res://scripts/autoload/AudioManager.gd")
	_am = am_script.new()
	add_child_autofree(_am)
	# Allow _ready to process
	if _am.has_method("_ready"):
		_am._ready()

func after_each() -> void:
	if _am != null and is_instance_valid(_am):
		_am.cleanup()

# ==============================================================================
# SECTION 1: BGM Looping & Stream Verification (AAA)
# ==============================================================================

func test_all_bgm_streams_have_loop_enabled() -> void:
	# Arrange: define all canonical BGM keys
	var keys = ["menu", "battle1", "intro", "batalha", "cerco"]
	
	# Act & Assert
	for k in keys:
		var stream = _am._get_or_load_bgm_stream(k)
		assert_not_null(stream, "BGM stream for key '%s' must load successfully" % k)
		if stream is AudioStreamOggVorbis:
			assert_true(stream.loop, "AudioStreamOggVorbis for '%s' must have loop=true" % k)

func test_play_bgm_happy_path() -> void:
	# Arrange
	var track = "menu"
	
	# Act
	_am.play_bgm(track, 0.0)
	
	# Assert
	assert_true(_am.is_bgm_playing(), "BGM must be playing after play_bgm")
	assert_eq(_am.get_current_bgm(), "menu", "Active BGM key must match 'menu'")
	assert_not_null(_am._active_bgm_player.stream, "Active player must have a valid stream assigned")

# ==============================================================================
# SECTION 2: Crossfade Stream Integrity (Regression Fix)
# ==============================================================================

func test_crossfade_preserves_active_player_stream_after_completion() -> void:
	# Arrange: start first track
	_am.play_bgm("menu", 0.0)
	assert_eq(_am.get_current_bgm(), "menu")
	
	# Act: crossfade into battle1 with a duration of 0.1s
	_am.play_bgm("battle1", 0.1)
	
	# Assert immediately: new player active, stream valid
	assert_eq(_am.get_current_bgm(), "battle1", "Current BGM key must immediately update to 'battle1'")
	assert_not_null(_am._active_bgm_player.stream, "Incoming player must have a valid stream immediately")
	assert_not_null(_am._bgm_tween, "Crossfade tween must be instantiated")
	
	# Step tween to completion synchronously via custom_step
	if _am._bgm_tween != null and _am._bgm_tween.is_valid():
		_am._bgm_tween.custom_step(0.2)
	
	# Assert after tween completion: STREAM MUST STILL BE VALID AND NOT NULL!
	assert_not_null(_am._active_bgm_player.stream, "CRITICAL: Active stream must NOT be cleared by tween callback!")
	assert_true(_am.is_bgm_playing(), "BGM must still be playing after crossfade completes")
	assert_eq(_am._active_bgm_player.volume_db, 0.0, "Volume must reach target 0.0 dB after fade in")

func test_stop_bgm_with_fade_stops_and_nulls_cleanly() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	assert_true(_am.is_bgm_playing())
	
	# Act: fade out over 0.1s
	_am.stop_bgm(0.1)
	assert_false(_am.is_bgm_playing(), "is_bgm_playing must report false immediately when stop requested")
	assert_not_null(_am._bgm_tween, "Fade out tween must be created")
	
	# Step fade-out tween to completion
	if _am._bgm_tween != null and _am._bgm_tween.is_valid():
		_am._bgm_tween.custom_step(0.2)
	
	# Assert: player is stopped and stream cleared
	assert_false(_am._active_bgm_player.playing, "Player must be stopped after fade-out")
	assert_null(_am._active_bgm_player.stream, "Stream must be cleared after fade-out")

# ==============================================================================
# SECTION 3: Edge Cases & Race Conditions
# ==============================================================================

func test_play_same_bgm_track_is_idempotent() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	var active_player = _am._active_bgm_player
	var active_stream = active_player.stream
	
	# Act: call play_bgm with the exact same track
	_am.play_bgm("menu", 0.5)
	
	# Assert: active player and stream remain identical, no duplicate trigger
	assert_eq(_am._active_bgm_player, active_player, "Calling same BGM must not swap players")
	assert_eq(_am._active_bgm_player.stream, active_stream, "Stream must remain unchanged")
	assert_true(_am.is_bgm_playing(), "BGM must continue playing")

func test_play_bgm_track_aliases() -> void:
	# Arrange & Act: test aliases for battle1
	var aliases = ["batalha", "cerco", "combat", "battle", "battle1"]
	for a in aliases:
		_am.play_bgm(a, 0.0)
		assert_true(_am.is_bgm_playing(), "Alias '%s' must start playing BGM" % a)
		assert_not_null(_am._active_bgm_player.stream, "Alias '%s' must load valid stream" % a)
		_am.stop_bgm(0.0)

func test_play_bgm_empty_or_whitespace_stops_bgm() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	assert_true(_am.is_bgm_playing())
	
	# Act
	_am.play_bgm("", 0.0)
	
	# Assert
	assert_false(_am.is_bgm_playing(), "Empty track key must stop BGM")
	
	# Act with spaces
	_am.play_bgm("menu", 0.0)
	_am.play_bgm("   ", 0.0)
	assert_false(_am.is_bgm_playing(), "Whitespace track key must stop BGM")

func test_play_bgm_nonexistent_track_graceful() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	
	# Act
	_am.play_bgm("totally_fake_track_12345", 0.0)
	
	# Assert: should keep playing existing track or safely ignore
	assert_true(_am.is_bgm_playing(), "Invalid track should not crash BGM playback")
	assert_eq(_am.get_current_bgm(), "menu", "BGM should remain on 'menu'")

func test_rapid_bgm_swapping_cancels_previous_tweens() -> void:
	# Arrange & Act: rapidly swap tracks with tweens
	_am.play_bgm("menu", 0.5)
	_am.play_bgm("battle1", 0.5)
	_am.play_bgm("intro", 0.5)
	_am.play_bgm("menu", 0.1)
	
	# Step final tween to completion
	if _am._bgm_tween != null and _am._bgm_tween.is_valid():
		_am._bgm_tween.custom_step(0.2)
	
	# Assert: final state is 'menu', valid stream, playing
	assert_eq(_am.get_current_bgm(), "menu", "Final track must be 'menu'")
	assert_not_null(_am._active_bgm_player.stream, "Stream must be valid and playing")
	assert_true(_am.is_bgm_playing(), "BGM must be playing cleanly")

# ==============================================================================
# SECTION 4: SFX Aliases & Pool Safety
# ==============================================================================

func test_sfx_portuguese_aliases_resolve_correctly() -> void:
	# Arrange
	var sfx_keys = ["ataque", "dano", "cura", "clique", "critico", "erro", "subir_nivel"]
	
	# Act & Assert
	for k in sfx_keys:
		var p = _am.play_sfx(k)
		assert_not_null(p, "SFX player must be allocated for alias '%s'" % k)
		assert_not_null(p.stream, "Stream must be loaded for alias '%s'" % k)

# ==============================================================================
# SECTION 5: Pause Immunity & Bus Settings
# ==============================================================================

func test_audio_manager_process_mode_is_always() -> void:
	# Assert: process mode must be PROCESS_MODE_ALWAYS so pausing tree doesn't silence music
	assert_eq(_am.process_mode, Node.PROCESS_MODE_ALWAYS, "AudioManager must have process_mode ALWAYS")
	assert_eq(_am._bgm_player_a.process_mode, Node.PROCESS_MODE_ALWAYS, "BGM Player A must have process_mode ALWAYS")
	assert_eq(_am._bgm_player_b.process_mode, Node.PROCESS_MODE_ALWAYS, "BGM Player B must have process_mode ALWAYS")

func test_bus_volume_and_mute_propagation() -> void:
	# Arrange
	_am.set_bus_volume("BGM", 0.6)
	_am.set_bus_muted("BGM", true)
	
	# Assert
	assert_between(_am.get_bus_volume("BGM"), 0.59, 0.61, "BGM volume must be 0.6")
	assert_true(_am.is_bus_muted("BGM"), "BGM must be muted")
	
	# Restore
	_am.set_bus_muted("BGM", false)
	_am.set_bus_volume("BGM", 1.0)
	assert_false(_am.is_bus_muted("BGM"), "BGM must be unmuted")
