# res://scripts/autoload/AudioManager.gd
extends Node

## Centralized Audio Manager Singleton (AudioManager.gd)
## Manages BGM crossfading, seamless looping, bus volumes, and pooled SFX playback.

const BGM_PATHS: Dictionary = {
	"menu": "res://assets/sounds/menu.ogg",
	"battle1": "res://assets/sounds/battle1.ogg",
	"batalha": "res://assets/sounds/battle1.ogg",
	"batalha1": "res://assets/sounds/battle1.ogg",
	"battle": "res://assets/sounds/battle1.ogg",
	"cerco": "res://assets/sounds/battle1.ogg",
	"combat": "res://assets/sounds/battle1.ogg",
	"intro": "res://assets/sounds/intro.ogg",
	"lobby": "res://assets/sounds/intro.ogg"
}

const SFX_PATHS: Dictionary = {
	"attack": "res://assets/sounds/attack.ogg",
	"ataque": "res://assets/sounds/attack.ogg",
	"button_click": "res://assets/sounds/button_click.ogg",
	"clique": "res://assets/sounds/button_click.ogg",
	"click": "res://assets/sounds/button_click.ogg",
	"critical_hit": "res://assets/sounds/critical_hit.ogg",
	"critico": "res://assets/sounds/critical_hit.ogg",
	"damage": "res://assets/sounds/damage.ogg",
	"dano": "res://assets/sounds/damage.ogg",
	"heal": "res://assets/sounds/heal.ogg",
	"cura": "res://assets/sounds/heal.ogg",
	"hit": "res://assets/sounds/hit.ogg",
	"level_up": "res://assets/sounds/level_up.ogg",
	"subir_nivel": "res://assets/sounds/level_up.ogg",
	"miss": "res://assets/sounds/miss.ogg",
	"erro": "res://assets/sounds/miss.ogg"
}

const SFX_POOL_SIZE: int = 12
const BUS_MASTER: String = "Master"
const BUS_BGM: String = "BGM"
const BUS_SFX: String = "SFX"

signal volume_changed(bus_name: String, new_volume: float, is_muted: bool)

var _bgm_player_a: AudioStreamPlayer
var _bgm_player_b: AudioStreamPlayer
var _active_bgm_player: AudioStreamPlayer
var _current_bgm_key: String = ""
var _bgm_tween: Tween = null

var _sfx_pool: Array[AudioStreamPlayer] = []
var _next_sfx_pool_index: int = 0
var _sfx_streams: Dictionary = {} # Dictionary[String, AudioStream]
var _bgm_streams: Dictionary = {} # Dictionary[String, AudioStream]

var _bus_volumes: Dictionary = {
	"Master": 1.0,
	"BGM": 0.6,
	"SFX": 0.8
}
var _bus_muted: Dictionary = {
	"Master": false,
	"BGM": false,
	"SFX": false
}

func _init() -> void:
	name = "AudioManager"
	process_mode = Node.PROCESS_MODE_ALWAYS
	_init_audio_nodes()

func _ready() -> void:
	_preload_streams()
	_apply_all_bus_settings()
	_connect_event_bus()

func _init_audio_nodes() -> void:
	# BGM Players for crossfade
	_bgm_player_a = AudioStreamPlayer.new()
	_bgm_player_a.process_mode = Node.PROCESS_MODE_ALWAYS
	_bgm_player_a.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_a)

	_bgm_player_b = AudioStreamPlayer.new()
	_bgm_player_b.process_mode = Node.PROCESS_MODE_ALWAYS
	_bgm_player_b.bus = _resolve_bus(BUS_BGM)
	add_child(_bgm_player_b)

	_active_bgm_player = _bgm_player_a

	# SFX Pool
	_sfx_pool.clear()
	for i in range(SFX_POOL_SIZE):
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.bus = _resolve_bus(BUS_SFX)
		p.finished.connect(_on_sfx_finished.bind(p))
		add_child(p)
		_sfx_pool.append(p)

func _on_sfx_finished(p: AudioStreamPlayer) -> void:
	if p != null and not p.playing:
		p.stream = null

func _resolve_bus(bus_name: String) -> String:
	if AudioServer.get_bus_index(bus_name) != -1:
		return bus_name
	return BUS_MASTER

func _preload_streams() -> void:
	for key in SFX_PATHS.keys():
		var path: String = SFX_PATHS[key]
		if not _sfx_streams.has(key) and ResourceLoader.exists(path):
			_sfx_streams[key] = load(path)

	for key in BGM_PATHS.keys():
		var path: String = BGM_PATHS[key]
		if not _bgm_streams.has(key) and ResourceLoader.exists(path):
			var stream: AudioStream = load(path)
			if stream is AudioStreamOggVorbis:
				stream.loop = true
			_bgm_streams[key] = stream

func _get_or_load_bgm_stream(track_key: String) -> AudioStream:
	if _bgm_streams.has(track_key):
		var cached: AudioStream = _bgm_streams[track_key]
		if cached is AudioStreamOggVorbis and not cached.loop:
			cached.loop = true
		return cached

	var path: String = BGM_PATHS.get(track_key, "")
	if path.is_empty() and track_key.begins_with("res://"):
		path = track_key

	if not path.is_empty() and ResourceLoader.exists(path):
		var stream: AudioStream = load(path)
		if stream is AudioStreamOggVorbis:
			stream.loop = true
		_bgm_streams[track_key] = stream
		return stream

	return null

func _connect_event_bus() -> void:
	if has_node("/root/EventBus"):
		var eb = get_node("/root/EventBus")
		if eb.has_signal("audio_play_sfx_requested") and not eb.audio_play_sfx_requested.is_connected(Callable(self, "_on_play_sfx_requested")):
			eb.audio_play_sfx_requested.connect(Callable(self, "_on_play_sfx_requested"))
		if eb.has_signal("audio_play_bgm_requested") and not eb.audio_play_bgm_requested.is_connected(Callable(self, "_on_play_bgm_requested")):
			eb.audio_play_bgm_requested.connect(Callable(self, "_on_play_bgm_requested"))
		if eb.has_signal("audio_stop_bgm_requested") and not eb.audio_stop_bgm_requested.is_connected(Callable(self, "_on_stop_bgm_requested")):
			eb.audio_stop_bgm_requested.connect(Callable(self, "_on_stop_bgm_requested"))
		if eb.has_signal("audio_stop_all_sfx_requested") and not eb.audio_stop_all_sfx_requested.is_connected(Callable(self, "_on_stop_all_sfx_requested")):
			eb.audio_stop_all_sfx_requested.connect(Callable(self, "_on_stop_all_sfx_requested"))

func _on_play_sfx_requested(sound_name: String, volume_db: float) -> void:
	play_sfx(sound_name, db_to_linear(volume_db))

func _on_play_bgm_requested(track_name: String, crossfade: bool) -> void:
	play_bgm(track_name, 1.0 if crossfade else 0.0)

func _on_stop_bgm_requested(fade_duration: float = 0.5) -> void:
	stop_bgm(fade_duration)

func _on_stop_all_sfx_requested() -> void:
	stop_all_sfx()

# ── BGM Playback & Crossfade ────────────────────────────────────────────────

func play_bgm(track_key: String, crossfade_duration: float = 1.0) -> void:
	var key: String = track_key.to_lower().strip_edges()
	if key.is_empty():
		stop_bgm(crossfade_duration)
		return

	if not BGM_PATHS.has(key) and not ResourceLoader.exists(track_key):
		push_warning("[AudioManager] Unknown BGM track '%s'" % track_key)
		return

	# If this track is already playing:
	if _current_bgm_key == key and is_bgm_playing():
		# If it was fading out, cancel the fade and restore volume
		if _bgm_tween != null and _bgm_tween.is_valid():
			_bgm_tween.kill()
			_bgm_tween = null
			if crossfade_duration > 0.0 and is_inside_tree():
				_bgm_tween = create_tween()
				_bgm_tween.tween_property(_active_bgm_player, "volume_db", 0.0, crossfade_duration * 0.5)
			else:
				_active_bgm_player.volume_db = 0.0
		return

	# Kill any ongoing transition tween
	if _bgm_tween != null and _bgm_tween.is_valid():
		_bgm_tween.kill()
		_bgm_tween = null

	var stream: AudioStream = _get_or_load_bgm_stream(key)
	if stream == null and ResourceLoader.exists(track_key):
		stream = _get_or_load_bgm_stream(track_key)

	if stream == null:
		push_warning("[AudioManager] Failed to load BGM stream for '%s'" % track_key)
		return

	var outgoing_player: AudioStreamPlayer = _active_bgm_player
	var incoming_player: AudioStreamPlayer = _bgm_player_b if outgoing_player == _bgm_player_a else _bgm_player_a

	incoming_player.stream = stream

	var should_crossfade: bool = (
		crossfade_duration > 0.0 and
		is_inside_tree() and
		outgoing_player != null and
		outgoing_player.playing and
		outgoing_player.stream != null
	)

	if should_crossfade:
		incoming_player.volume_db = -80.0
		incoming_player.play()
		_active_bgm_player = incoming_player
		_current_bgm_key = key

		_bgm_tween = create_tween().set_parallel(true)
		_bgm_tween.tween_property(outgoing_player, "volume_db", -80.0, crossfade_duration)
		_bgm_tween.tween_property(incoming_player, "volume_db", 0.0, crossfade_duration)
		_bgm_tween.chain().tween_callback(func():
			if outgoing_player != null:
				outgoing_player.stop()
				outgoing_player.stream = null
		)
	else:
		if outgoing_player != null:
			outgoing_player.stop()
			outgoing_player.stream = null

		incoming_player.volume_db = 0.0
		incoming_player.play()
		_active_bgm_player = incoming_player
		_current_bgm_key = key

func stop_bgm(fade_duration: float = 0.5) -> void:
	if _bgm_tween != null and _bgm_tween.is_valid():
		_bgm_tween.kill()
		_bgm_tween = null

	var player_to_stop: AudioStreamPlayer = _active_bgm_player
	_current_bgm_key = ""

	if player_to_stop == null or not player_to_stop.playing:
		if player_to_stop != null:
			player_to_stop.stop()
			player_to_stop.stream = null
		return

	if fade_duration > 0.0 and is_inside_tree():
		_bgm_tween = create_tween()
		_bgm_tween.tween_property(player_to_stop, "volume_db", -80.0, fade_duration)
		_bgm_tween.tween_callback(func():
			if player_to_stop != null:
				player_to_stop.stop()
				player_to_stop.stream = null
		)
	else:
		player_to_stop.stop()
		player_to_stop.stream = null

func stop_all_sfx() -> void:
	for p in _sfx_pool:
		if p != null:
			p.stop()
			p.stream = null
	_next_sfx_pool_index = 0

func cleanup() -> void:
	if _bgm_tween != null and _bgm_tween.is_valid():
		_bgm_tween.kill()
		_bgm_tween = null
	stop_bgm(0.0)
	stop_all_sfx()
	if _bgm_player_a != null:
		_bgm_player_a.stop()
		_bgm_player_a.stream = null
	if _bgm_player_b != null:
		_bgm_player_b.stop()
		_bgm_player_b.stream = null
	_sfx_streams.clear()
	_bgm_streams.clear()
	_current_bgm_key = ""
	_next_sfx_pool_index = 0

func _exit_tree() -> void:
	cleanup()

func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE or what == NOTIFICATION_WM_CLOSE_REQUEST:
		cleanup()

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
	var key: String = sound_key.to_lower().strip_edges()
	if not SFX_PATHS.has(key) and not ResourceLoader.exists(sound_key):
		push_warning("[AudioManager] Unknown SFX '%s'" % sound_key)
		return null

	if not _sfx_streams.has(key):
		var path: String = SFX_PATHS.get(key, sound_key)
		if ResourceLoader.exists(path):
			_sfx_streams[key] = load(path)

	var player: AudioStreamPlayer = _get_available_sfx_player()
	if player == null:
		return null

	player.stop()
	player.stream = _sfx_streams.get(key, null)
	player.volume_db = linear_to_db(clamp(volume_scale, 0.0001, 1.0))
	player.pitch_scale = clamp(pitch_scale, 0.5, 2.0)
	player.play()
	return player

func _get_available_sfx_player() -> AudioStreamPlayer:
	if _sfx_pool.is_empty():
		return null
	var pool_size: int = _sfx_pool.size()
	for i in range(pool_size):
		var idx: int = (_next_sfx_pool_index + i) % pool_size
		var p: AudioStreamPlayer = _sfx_pool[idx]
		if not p.playing:
			_next_sfx_pool_index = (idx + 1) % pool_size
			return p
	# Pool exhausted: borrow next player in round-robin sequence
	var player: AudioStreamPlayer = _sfx_pool[_next_sfx_pool_index]
	_next_sfx_pool_index = (_next_sfx_pool_index + 1) % pool_size
	return player

# ── Bus Volume & Mute Controls ──────────────────────────────────────────────

func _apply_all_bus_settings() -> void:
	for bus_name in _bus_volumes.keys():
		_apply_bus_volume(bus_name, _bus_volumes[bus_name])
	for bus_name in _bus_muted.keys():
		_apply_bus_mute(bus_name, _bus_muted[bus_name])

func _apply_bus_volume(bus_name: String, vol: float) -> void:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		var db = linear_to_db(max(0.0001, vol))
		AudioServer.set_bus_volume_db(idx, db)

func _apply_bus_mute(bus_name: String, muted: bool) -> void:
	var idx: int = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		AudioServer.set_bus_mute(idx, muted)

func set_bus_volume(bus_name: String, linear_volume: float) -> void:
	var vol_clamped: float = clamp(linear_volume, 0.0, 1.0)
	_bus_volumes[bus_name] = vol_clamped
	_apply_bus_volume(bus_name, vol_clamped)
	volume_changed.emit(bus_name, vol_clamped, is_bus_muted(bus_name))

func get_bus_volume(bus_name: String) -> float:
	return _bus_volumes.get(bus_name, 1.0)

func set_bus_muted(bus_name: String, muted: bool) -> void:
	_bus_muted[bus_name] = muted
	_apply_bus_mute(bus_name, muted)
	volume_changed.emit(bus_name, get_bus_volume(bus_name), muted)

func is_bus_muted(bus_name: String) -> bool:
	return _bus_muted.get(bus_name, false)

func change_bus_volume(bus_name: String, delta: float) -> float:
	var current: float = get_bus_volume(bus_name)
	var new_vol: float = clamp(current + delta, 0.0, 1.0)
	set_bus_volume(bus_name, new_vol)
	return new_vol

func toggle_bus_mute(bus_name: String) -> bool:
	var new_muted: bool = not is_bus_muted(bus_name)
	set_bus_muted(bus_name, new_muted)
	return new_muted

func change_bgm_volume(delta: float) -> float:
	return change_bus_volume(BUS_BGM, delta)

func toggle_bgm_mute() -> bool:
	return toggle_bus_mute(BUS_BGM)

func change_sfx_volume(delta: float) -> float:
	return change_bus_volume(BUS_SFX, delta)

func toggle_sfx_mute() -> bool:
	return toggle_bus_mute(BUS_SFX)

func set_player_pitch_scale(player: AudioStreamPlayer, pitch_scale: float) -> void:
	if player != null:
		player.pitch_scale = clamp(pitch_scale, 0.5, 2.0)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F9 or event.keycode == KEY_MINUS:
			var v = change_bgm_volume(-0.1)
			_notify_volume_feedback("Música", v, is_bus_muted(BUS_BGM))
		elif event.keycode == KEY_F10 or event.keycode == KEY_EQUAL:
			var v = change_bgm_volume(+0.1)
			_notify_volume_feedback("Música", v, is_bus_muted(BUS_BGM))
		elif event.keycode == KEY_F8:
			var m = toggle_bgm_mute()
			_notify_volume_feedback("Música", get_bus_volume(BUS_BGM), m)

func _notify_volume_feedback(channel_name: String, vol: float, muted: bool) -> void:
	if has_node("/root/EventBus"):
		var eb = get_node("/root/EventBus")
		if eb.has_signal("combat_log_entry_added"):
			var pct = int(round(vol * 100))
			var state_str = "[MUTADO]" if muted else "%d%%" % pct
			eb.combat_log_entry_added.emit("[color=#38bdf8][ÁUDIO][/color] 🔊 %s: %s (F9/F10 para ajustar)" % [channel_name, state_str])

## Toca a trompa de guerra anã / alarme de invasão (emitido ao romper a muralha)
func play_war_horn_alarm() -> void:
	# Som grave, pesado e ressonante de trompa anã
	play_sfx("critical_hit", 0.58)

## Toca som ambiente de cerco da fortaleza (loop contínuo adaptativo)
func play_ambient_fortress_loop() -> void:
	if _current_bgm_key.is_empty():
		play_bgm("cerco", 1.5)

