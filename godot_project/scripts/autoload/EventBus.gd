# res://scripts/autoload/EventBus.gd
extends Node

## Centralized Event Bus Singleton (EventBus.gd)
## Decouples subsystems through type-safe global signals.

# ── Combat & Tactical Grid Signals ──────────────────────────────────────────
signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i)
signal unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String)
signal unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int)
signal unit_died(unit_id: String)
signal death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String)
signal status_applied(unit_id: String, status_id: String, duration: int)
signal status_removed(unit_id: String, status_id: String)
signal turn_changed(turn_number: int, active_unit_id: String)

# ── Cerco & Deckbuilder Signals ─────────────────────────────────────────────
signal card_selected(player_id: String, card_id: String)
signal round_resolved(round_number: int, sync_results: Dictionary)
signal synergy_triggered(synergy_type: String, bonus_description: String)
signal resources_updated(wood: int, metal: int, crystal: int, ap: int)

# ── Network Signals ─────────────────────────────────────────────────────────
signal network_message_received(message_type: String, payload: Dictionary)
signal network_connection_status_changed(connected: bool, room_id: String)

# ── System, State & Audio Signals ───────────────────────────────────────────
signal game_state_changed(previous_state: int, new_state: int)
signal audio_play_sfx_requested(sound_name: String, volume_db: float)
signal audio_play_bgm_requested(track_name: String, crossfade: bool)
signal floating_text_requested(text: String, position: Vector2, color: Color)
signal combat_log_entry_added(bbcode_text: String)

# ── Telemetry & Test Support ────────────────────────────────────────────────
@export var debug_logging: bool = false
var _emission_counts: Dictionary = {}
var _event_history: Array[Dictionary] = []
const MAX_HISTORY: int = 100

func _init() -> void:
	name = "EventBus"

## Resets telemetry metrics (useful between unit test runs)
func reset_telemetry() -> void:
	_emission_counts.clear()
	_event_history.clear()

## Returns the number of times a specific signal was emitted via emit_logged
func get_emission_count(signal_name: String) -> int:
	return _emission_counts.get(signal_name, 0)

## Emits a signal while recording telemetry for test validation
func emit_logged(sig_name: String, args: Array = []) -> void:
	_emission_counts[sig_name] = _emission_counts.get(sig_name, 0) + 1
	if _event_history.size() >= MAX_HISTORY:
		_event_history.pop_front()
	_event_history.append({"signal": sig_name, "args": args, "timestamp": Time.get_ticks_msec()})
	
	if debug_logging:
		print("[EventBus] %s args: %s" % [sig_name, str(args)])
	
	# Actually emit the underlying signal if it exists
	if has_signal(sig_name):
		match args.size():
			0:
				emit_signal(sig_name)
			1:
				emit_signal(sig_name, args[0])
			2:
				emit_signal(sig_name, args[0], args[1])
			3:
				emit_signal(sig_name, args[0], args[1], args[2])
			4:
				emit_signal(sig_name, args[0], args[1], args[2], args[3])
			5:
				emit_signal(sig_name, args[0], args[1], args[2], args[3], args[4])
			6:
				emit_signal(sig_name, args[0], args[1], args[2], args[3], args[4], args[5])
