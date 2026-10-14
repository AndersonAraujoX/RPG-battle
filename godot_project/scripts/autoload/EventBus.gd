# res://scripts/autoload/EventBus.gd
@warning_ignore("unused_signal")
extends Node

## Centralized Event Bus Singleton (EventBus.gd)
## Decouples subsystems through type-safe global signals.

# ── Combat & Tactical Grid Signals ──────────────────────────────────────────
@warning_ignore("unused_signal")
signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i)
@warning_ignore("unused_signal")
signal unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String)
@warning_ignore("unused_signal")
signal unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int)
@warning_ignore("unused_signal")
signal unit_died(unit_id: String)
@warning_ignore("unused_signal")
signal death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String)
@warning_ignore("unused_signal")
signal status_applied(unit_id: String, status_id: String, duration: int)
@warning_ignore("unused_signal")
signal status_removed(unit_id: String, status_id: String)
@warning_ignore("unused_signal")
signal turn_changed(turn_number: int, active_unit_id: String)

# ── Cerco & Deckbuilder Signals ─────────────────────────────────────────────
@warning_ignore("unused_signal")
signal card_selected(player_id: String, card_id: String)
@warning_ignore("unused_signal")
signal card_played(player_id: String, card_id: String, target_zone: String)
@warning_ignore("unused_signal")
signal dice_rolled(source_id: String, dice_type: String, results: Array)
@warning_ignore("unused_signal")
signal damage_dealt(target_id: String, amount: int, current_hp: int)
@warning_ignore("unused_signal")
signal production_completed(workshop_zone: String, resource_type: String, amount: int)
@warning_ignore("unused_signal")
signal supreme_synchrony_triggered(crystals_awarded: int)
@warning_ignore("unused_signal")
signal wall_breached(wall_id: String)
@warning_ignore("unused_signal")
signal round_resolved(round_number: int, sync_results: Dictionary)
@warning_ignore("unused_signal")
signal synergy_triggered(synergy_type: String, bonus_description: String)
@warning_ignore("unused_signal")
signal resources_updated(wood: int, metal: int, crystal: int, ap: int)

# ── Network Signals ─────────────────────────────────────────────────────────
@warning_ignore("unused_signal")
signal network_message_received(message_type: String, payload: Dictionary)
@warning_ignore("unused_signal")
signal network_connection_status_changed(connected: bool, room_id: String)

# ── System, State & Audio Signals ───────────────────────────────────────────
@warning_ignore("unused_signal")
signal game_state_changed(previous_state: int, new_state: int)
@warning_ignore("unused_signal")
signal game_reset()
@warning_ignore("unused_signal")
signal audio_play_sfx_requested(sound_name: String, volume_db: float)
@warning_ignore("unused_signal")
signal audio_play_bgm_requested(track_name: String, crossfade: bool)
@warning_ignore("unused_signal")
signal audio_stop_bgm_requested(fade_duration: float)
@warning_ignore("unused_signal")
signal audio_stop_all_sfx_requested()
@warning_ignore("unused_signal")
signal floating_text_requested(text: String, position: Vector2, color: Color)
@warning_ignore("unused_signal")
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
	_event_history.append({"signal": sig_name, "args": args.duplicate(true), "timestamp": Time.get_ticks_msec()})
	
	if debug_logging:
		print("[EventBus] %s args: %s" % [sig_name, str(args)])
	
	# Actually emit the underlying signal if it exists
	if has_signal(sig_name):
		Callable(self, sig_name).callv(args)
	else:
		push_warning("[EventBus] Signal '%s' does not exist." % sig_name)
