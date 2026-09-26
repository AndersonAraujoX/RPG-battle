# res://scripts/autoload/AudioManager.gd
extends Node

## Centralized Audio Manager Singleton (AudioManager.gd)
## Manages BGM crossfading, bus volumes, and pooled SFX playback.

const BGM_PATHS: Dictionary = {
	"menu": "res://assets/sounds/menu.ogg",
	"battle1": "res://assets/sounds/battle1.ogg",
	"intro": "res://assets/sounds/intro.ogg"
}

const SFX_PATHS: Dictionary = {
	"attack": "res://assets/sounds/attack.ogg",
	"button_click": "res://assets/sounds/button_click.ogg",
	"critical_hit": "res://assets/sounds/critical_hit.ogg",
	"damage": "res://assets/sounds/damage.ogg",
	"heal": "res://assets/sounds/heal.ogg",
	"hit": "res://assets/sounds/hit.ogg",
	"level_up": "res://assets/sounds/level_up.ogg",
	"miss": "res://assets/sounds/miss.ogg"
}

const SFX_POOL_SIZE: int = 12
const BUS_MASTER: String = "Master"
const BUS_BGM: String = "BGM"
const BUS_SFX: String = "SFX"

var _bgm_player_a: AudioStreamPlayer
var _bgm_player_b: AudioStreamPlayer
var _active_bgm_player: AudioStreamPlayer
var _current_bgm_key: String = ""

var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_streams: Dictionary = {} # Dictionary[String, AudioStream]
var _bgm_streams: Dictionary = {} # Dictionary[String, AudioStream]

var _bus_volumes: Dictionary = {
	"Master": 1.0,
	"BGM": 1.0,
	"SFX": 1.0
}
var _bus_muted: Dictionary = {
	"Master": false,
	"BGM": false,
	"SFX": false
}

func _init() -> void:
	name = "AudioManager"
	_init_audio_nodes()

func _ready() -> void:
	_preload_streams()
	_connect_event_bus()

func _init_audio_nodes() -> void:
	# BGM Players for crossfade
	_bgm_player_a = AudioStreamPlayer.new()
	_bgm_player_a.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_a)

	_bgm_player_b = AudioStreamPlayer.new()
	_bgm_player_b.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_b)

	_active_bgm_player = _bgm_player_a

	# SFX Pool
	_sfx_pool.clear()
	for i in range(SFX_POOL_SIZE):
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.bus = _resolve_bus(BUS_SFX)
		add_child(p)
		_sfx_pool.append(p)

func _resolve_bus(bus_name: String) -> String:
	if AudioServer.get_bus_index(bus_name) != -1:
		return bus_name
	return BUS_MASTER

func _preload_streams() -> void:
	for key in SFX_PATHS.keys():
		var path: String = SFX_PATHS[key]
		if ResourceLoader.exists(path):
			_sfx_streams[key] = load(path)
		else:
			push_warning("[AudioManager] SFX file not found: %s" % path)

	for key in BGM_PATHS.keys():
		var path: String = BGM_PATHS[key]
		if ResourceLoader.exists(path):
			_bgm_streams[key] = load(path)
		else:
			push_warning("[AudioManager] BGM file not found: %s" % path)

func _connect_event_bus() -> void:
	if has_node("/root/EventBus"):
		var eb = get_node("/root/EventBus")
		if eb.has_signal("audio_play_sfx_requested"):
			eb.audio_play_sfx_requested.connect(Callable(self, "_on_play_sfx_requested"))
		if eb.has_signal("audio_play_bgm_requested"):
			eb.audio_play_bgm_requested.connect(Callable(self, "_on_play_bgm_requested"))

func _on_play_sfx_requested(sound_name: String, volume_db: float) -> void:
	play_sfx(sound_name, db_to_linear(volume_db))

func _on_play_bgm_requested(track_name: String, crossfade: bool) -> void:
	play_bgm(track_name, 1.0 if crossfade else 0.0)

# ── BGM Playback & Crossfade ────────────────────────────────────────────────

func play_bgm(track_key: String, crossfade_duration: float = 1.0) -> void:
	if not BGM_PATHS.has(track_key):
		push_warning("[AudioManager] Unknown BGM track '%s'" % track_key)
		return

	if not _bgm_streams.has(track_key):
		var path = BGM_PATHS[track_key]
		if ResourceLoader.exists(path):
			_bgm_streams[track_key] = load(path)

	var next_player: AudioStreamPlayer = _bgm_player_b if _active_bgm_player == _bgm_player_a else _bgm_player_a
	var stream: AudioStream = _bgm_streams.get(track_key, null)

	next_player.stream = stream
	next_player.volume_db = 0.0
	next_player.play()

	if crossfade_duration > 0.0 and is_inside_tree():
		var tween: Tween = create_tween().set_parallel(true)
		tween.tween_property(_active_bgm_player, "volume_db", -80.0, crossfade_duration)
		tween.tween_property(next_player, "volume_db", 0.0, crossfade_duration)
		tween.chain().tween_callback(Callable(_active_bgm_player, "stop"))
	else:
		_active_bgm_player.stop()

	_active_bgm_player = next_player
	_current_bgm_key = track_key

func stop_bgm(fade_duration: float = 0.5) -> void:
	if not is_bgm_playing():
		_current_bgm_key = ""
		return

	if fade_duration > 0.0 and is_inside_tree():
		var tween: Tween = create_tween()
		tween.tween_property(_active_bgm_player, "volume_db", -80.0, fade_duration)
		tween.tween_callback(Callable(_active_bgm_player, "stop"))
	else:
		_active_bgm_player.stop()

	_current_bgm_key = ""

func is_bgm_playing() -> bool:
	if _current_bgm_key.is_empty():
		return false
	return _active_bgm_player != null and _active_bgm_player.playing

func get_current_bgm() -> String:
	return _current_bgm_key

func get_current_bgm_key() -> String:
	return _current_bgm_key

# ── SFX Pooled Playback ─────────────────────────────────────────────────────

func play_sfx(sound_key: String, volume_scale: float = 1.0, pitch_scale: float = 1.0) -> AudioStreamPlayer:
	if not SFX_PATHS.has(sound_key):
		push_warning("[AudioManager] Unknown SFX '%s'" % sound_key)
		return null

	if not _sfx_streams.has(sound_key):
		var path = SFX_PATHS[sound_key]
		if ResourceLoader.exists(path):
			_sfx_streams[sound_key] = load(path)

	var player: AudioStreamPlayer = _get_available_sfx_player()
	player.stream = _sfx_streams.get(sound_key, null)
	player.volume_db = linear_to_db(clamp(volume_scale, 0.0001, 1.0))
	player.pitch_scale = clamp(pitch_scale, 0.5, 2.0)
	player.play()
	return player

func _get_available_sfx_player() -> AudioStreamPlayer:
	for p in _sfx_pool:
		if not p.playing:
			return p
	# Pool exhausted: borrow first player (oldest)
	return _sfx_pool[0]

# ── Bus Volume & Mute Controls ──────────────────────────────────────────────

func set_bus_volume(bus_name: String, linear_volume: float) -> void:
	var vol_clamped: float = clamp(linear_volume, 0.0, 1.0)
	_bus_volumes[bus_name] = vol_clamped

	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		var db = linear_to_db(max(0.0001, vol_clamped))
		AudioServer.set_bus_volume_db(idx, db)

func get_bus_volume(bus_name: String) -> float:
	return _bus_volumes.get(bus_name, 1.0)

func set_bus_muted(bus_name: String, muted: bool) -> void:
	_bus_muted[bus_name] = muted
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		AudioServer.set_bus_mute(idx, muted)

func is_bus_muted(bus_name: String) -> bool:
	return _bus_muted.get(bus_name, false)
