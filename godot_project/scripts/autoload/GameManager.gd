# res://scripts/autoload/GameManager.gd
extends Node

## Centralized Game State Machine Singleton (GameManager.gd)
## Controls high-level game states, scene routing, and state transitions.

signal state_changed(previous_state: int, new_state: int)

enum GameState {
	MENU = 0,
	COMBATE_TATICO = 1,
	CERCO_ISECTUM = 2,
	FIM_DE_JOGO = 3,
	MULTIPLAYER_LOBBY = 4
}

const STATE_NAMES: Dictionary = {
	GameState.MENU: "MENU",
	GameState.COMBATE_TATICO: "COMBATE_TATICO",
	GameState.CERCO_ISECTUM: "CERCO_ISECTUM",
	GameState.FIM_DE_JOGO: "FIM_DE_JOGO",
	GameState.MULTIPLAYER_LOBBY: "MULTIPLAYER_LOBBY"
}

const VALID_TRANSITIONS: Dictionary = {
	GameState.MENU: [GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM, GameState.MULTIPLAYER_LOBBY],
	GameState.COMBATE_TATICO: [GameState.FIM_DE_JOGO, GameState.MENU],
	GameState.CERCO_ISECTUM: [GameState.FIM_DE_JOGO, GameState.MENU],
	GameState.MULTIPLAYER_LOBBY: [GameState.CERCO_ISECTUM, GameState.COMBATE_TATICO, GameState.MENU],
	GameState.FIM_DE_JOGO: [GameState.MENU, GameState.COMBATE_TATICO, GameState.CERCO_ISECTUM]
}

const SCENE_ROUTES: Dictionary = {
	GameState.MENU: "res://scenes/main/Menu.tscn",
	GameState.COMBATE_TATICO: "res://scenes/main/Main.tscn",
	GameState.CERCO_ISECTUM: "res://scenes/cerco/FortressBoard.tscn",
	GameState.FIM_DE_JOGO: "res://scenes/main/GameOver.tscn",
	GameState.MULTIPLAYER_LOBBY: "res://scenes/main/Lobby.tscn"
}

var current_state: GameState = GameState.MENU
var previous_state: GameState = GameState.MENU
var state_payload: Dictionary = {}
var is_transitioning: bool = false
var headless_test_mode: bool = false # Dynamically set in _init

func _init() -> void:
	name = "GameManager"
	headless_test_mode = (DisplayServer.get_name() == "headless")

## Validates whether a transition from current_state to target_state is legal
func can_transition_to(target_state: int) -> bool:
	if is_transitioning:
		push_warning("[GameManager] Transition rejected: already transitioning")
		return false
	if not STATE_NAMES.has(target_state):
		return false
	if not VALID_TRANSITIONS.has(current_state):
		return false
	return (VALID_TRANSITIONS[current_state] as Array).has(target_state)

## Executes state change with lifecycle hooks and signals
func change_state(new_state: int, payload: Dictionary = {}) -> bool:
	if is_transitioning:
		push_warning("[GameManager] Transition rejected: already transitioning")
		return false

	if not STATE_NAMES.has(new_state):
		push_warning("[GameManager] Invalid state value: %s" % str(new_state))
		return false

	if new_state == current_state:
		return false

	if not can_transition_to(new_state):
		push_warning("[GameManager] Invalid state transition: %s -> %s" % [
			STATE_NAMES.get(current_state, "UNKNOWN"), STATE_NAMES.get(new_state, "UNKNOWN")
		])
		return false

	is_transitioning = true
	var prev: GameState = current_state
	var target_state: GameState = new_state as GameState
	_exit_state(prev)

	previous_state = prev
	current_state = target_state
	state_payload = payload.duplicate(true)

	_enter_state(current_state, state_payload)
	is_transitioning = false

	# Emit EventBus game_state_changed before local state_changed to preserve causal ordering
	if has_node("/root/EventBus"):
		get_node("/root/EventBus").game_state_changed.emit(prev, target_state)

	state_changed.emit(prev, target_state)

	return true

## Executes state change and attempts to load associated scene file
func change_state_and_scene(new_state: int, payload: Dictionary = {}) -> bool:
	var success: bool = change_state(new_state, payload)
	if not success:
		return false

	if headless_test_mode:
		return true

	if SCENE_ROUTES.has(new_state):
		var path: String = SCENE_ROUTES[new_state]
		if ResourceLoader.exists(path):
			var err: Error = get_tree().change_scene_to_file(path)
			if err != OK:
				push_error("[GameManager] Failed to load scene '%s': error %d" % [path, err])
				return false
		else:
			push_warning("[GameManager] Scene file '%s' does not exist yet. State set to %s." % [
				path, STATE_NAMES.get(new_state, "UNKNOWN")
			])

	return true

func is_in_combat() -> bool:
	return current_state == GameState.COMBATE_TATICO or current_state == GameState.CERCO_ISECTUM

func get_state_name(state: int) -> String:
	return STATE_NAMES.get(state, "UNKNOWN")

func get_current_state() -> GameState:
	return current_state

func get_previous_state() -> GameState:
	return previous_state

func get_current_state_name() -> String:
	return STATE_NAMES.get(current_state, "UNKNOWN")

func get_state_payload() -> Dictionary:
	return state_payload.duplicate(true)

## Resets FSM back to MENU
func reset_state() -> void:
	current_state = GameState.MENU
	previous_state = GameState.MENU
	state_payload.clear()
	is_transitioning = false
	if has_node("/root/EventBus"):
		var eb = get_node("/root/EventBus")
		if eb.has_signal("game_reset"):
			eb.game_reset.emit()

func reset_to_menu() -> void:
	if current_state != GameState.MENU:
		change_state(GameState.MENU)
	else:
		reset_state()

# ── Lifecycle Hooks ─────────────────────────────────────────────────────────

func _enter_state(state: GameState, _payload: Dictionary) -> void:
	var track_to_play: String = ""
	match state:
		GameState.MENU:
			track_to_play = "menu"
		GameState.COMBATE_TATICO:
			track_to_play = "battle1"
		GameState.CERCO_ISECTUM:
			track_to_play = "battle1"
		GameState.FIM_DE_JOGO:
			track_to_play = ""
		GameState.MULTIPLAYER_LOBBY:
			track_to_play = "intro"

	if not track_to_play.is_empty():
		if has_node("/root/EventBus"):
			var eb = get_node("/root/EventBus")
			if eb.has_signal("audio_play_bgm_requested"):
				eb.audio_play_bgm_requested.emit(track_to_play, true)
			elif has_node("/root/AudioManager"):
				get_node("/root/AudioManager").play_bgm(track_to_play)
		elif has_node("/root/AudioManager"):
			get_node("/root/AudioManager").play_bgm(track_to_play)

func _exit_state(_state: GameState) -> void:
	pass
