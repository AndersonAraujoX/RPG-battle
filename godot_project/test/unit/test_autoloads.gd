# test/unit/test_autoloads.gd
# Test Suite for Godot 4 Autoload Singletons (GameManager, EventBus, DataManager, AudioManager)
# Adheres strictly to Arrange-Act-Assert (AAA) pattern.
extends GutTest

# ==============================================================================
# Autoload Script References (enables isolated instantiation if needed)
# ==============================================================================
const GameManagerScript = preload("res://scripts/autoload/GameManager.gd")
const EventBusScript = preload("res://scripts/autoload/EventBus.gd")
const DataManagerScript = preload("res://scripts/autoload/DataManager.gd")
const AudioManagerScript = preload("res://scripts/autoload/AudioManager.gd")

var _gm: Node = null
var _eb: Node = null
var _dm: Node = null
var _am: Node = null

# Signal monitoring tracker
var _received_events: Array = []

func _on_event_received(arg1 = null, arg2 = null, arg3 = null, arg4 = null, arg5 = null, arg6 = null):
	_received_events.append([arg1, arg2, arg3, arg4, arg5, arg6])

func before_each():
	_received_events.clear()
	# Resolve either global Autoload singleton or instantiate fresh isolated instance
	if get_node_or_null("/root/GameManager") != null:
		_gm = get_node("/root/GameManager")
		_gm.reset_state()
	else:
		_gm = autofree(GameManagerScript.new())

	if get_node_or_null("/root/EventBus") != null:
		_eb = get_node("/root/EventBus")
	else:
		_eb = autofree(EventBusScript.new())

	if get_node_or_null("/root/DataManager") != null:
		_dm = get_node("/root/DataManager")
	else:
		_dm = autofree(DataManagerScript.new())
		_dm.load_all_data()

	if get_node_or_null("/root/AudioManager") != null:
		_am = get_node("/root/AudioManager")
	else:
		_am = autofree(AudioManagerScript.new())

func after_each():
	_received_events.clear()
	if _gm != null and _gm.has_method("reset_state"):
		_gm.reset_state()
	if _am != null and _am.has_method("stop_bgm"):
		_am.stop_bgm(0.0)

# ==============================================================================
# SECTION 1: GameManager Tests (10 tests)
# ==============================================================================

func test_game_manager_initial_state_is_menu():
	# Arrange: freshly reset GameManager
	# Act
	var current = _gm.current_state
	# Assert
	assert_eq(current, _gm.GameState.MENU, "Initial GameManager state must be MENU")

func test_game_manager_change_state_updates_current_and_previous():
	# Arrange
	var target_state = _gm.GameState.COMBATE_TATICO
	# Act
	var success = _gm.change_state(target_state)
	# Assert
	assert_true(success, "Transition to COMBATE_TATICO must return true")
	assert_eq(_gm.current_state, target_state, "Current state must be COMBATE_TATICO")
	assert_eq(_gm.previous_state, _gm.GameState.MENU, "Previous state must be MENU")

func test_game_manager_emits_state_changed_signal():
	# Arrange
	watch_signals(_gm)
	var target_state = _gm.GameState.CERCO_ISECTUM
	# Act
	_gm.change_state(target_state)
	# Assert
	assert_signal_emitted(_gm, "state_changed", "state_changed signal must be emitted")
	assert_signal_emitted_with_parameters(_gm, "state_changed", [_gm.GameState.MENU, target_state])

func test_game_manager_all_valid_transitions():
	# Arrange
	var transitions = [
		_gm.GameState.MULTIPLAYER_LOBBY,
		_gm.GameState.CERCO_ISECTUM,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU
	]
	# Act & Assert
	for state in transitions:
		var result = _gm.change_state(state)
		assert_true(result, "Transition to state %s must be valid" % state)
		assert_eq(_gm.current_state, state, "Current state must match transition target")

func test_game_manager_is_in_combat_flag():
	# Arrange & Act & Assert
	_gm.change_state(_gm.GameState.MENU)
	assert_false(_gm.is_in_combat(), "MENU is not combat")

	_gm.change_state(_gm.GameState.COMBATE_TATICO)
	assert_true(_gm.is_in_combat(), "COMBATE_TATICO is combat")

	_gm.change_state(_gm.GameState.CERCO_ISECTUM)
	assert_true(_gm.is_in_combat(), "CERCO_ISECTUM is combat")

	_gm.change_state(_gm.GameState.FIM_DE_JOGO)
	assert_false(_gm.is_in_combat(), "FIM_DE_JOGO is not combat")

func test_game_manager_get_state_name_mapping():
	# Arrange & Act & Assert
	assert_eq(_gm.get_state_name(_gm.GameState.MENU), "MENU")
	assert_eq(_gm.get_state_name(_gm.GameState.COMBATE_TATICO), "COMBATE_TATICO")
	assert_eq(_gm.get_state_name(_gm.GameState.CERCO_ISECTUM), "CERCO_ISECTUM")
	assert_eq(_gm.get_state_name(_gm.GameState.MULTIPLAYER_LOBBY), "MULTIPLAYER_LOBBY")
	assert_eq(_gm.get_state_name(_gm.GameState.FIM_DE_JOGO), "FIM_DE_JOGO")

func test_game_manager_transition_to_same_state_is_noop():
	# Arrange
	_gm.change_state(_gm.GameState.MENU)
	watch_signals(_gm)
	# Act
	var result = _gm.change_state(_gm.GameState.MENU)
	# Assert
	assert_false(result, "Transition to identical state must return false")
	assert_signal_not_emitted(_gm, "state_changed", "No redundant signal when state does not change")

func test_game_manager_reset_state_restores_menu():
	# Arrange
	_gm.change_state(_gm.GameState.FIM_DE_JOGO)
	# Act
	_gm.reset_state()
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Reset must restore MENU state")
	assert_false(_gm.is_in_combat(), "Reset must clear combat status")

func test_game_manager_rapid_sequential_transitions():
	# Arrange
	var states = [
		_gm.GameState.COMBATE_TATICO,
		_gm.GameState.CERCO_ISECTUM,
		_gm.GameState.MULTIPLAYER_LOBBY,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU
	]
	# Act
	for s in states:
		_gm.change_state(s)
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Final state must match last transition")
	assert_eq(_gm.previous_state, _gm.GameState.FIM_DE_JOGO, "Previous state must match N-1 transition")

func test_game_manager_invalid_state_transition_rejected():
	# Arrange
	var invalid_state_val = 999
	# Act
	var success = _gm.change_state(invalid_state_val)
	# Assert
	assert_false(success, "Transitioning to out-of-range integer state must be rejected")
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Current state must remain unchanged")

# ==============================================================================
# SECTION 2: EventBus Tests (11 tests)
# ==============================================================================

func test_event_bus_unit_moved_signal():
	# Arrange
	watch_signals(_eb)
	var unit_id = "hero_stark"
	var from_p = Vector2i(2, 3)
	var to_p = Vector2i(4, 5)
	# Act
	_eb.unit_moved.emit(unit_id, from_p, to_p)
	# Assert
	assert_signal_emitted(_eb, "unit_moved")
	assert_signal_emitted_with_parameters(_eb, "unit_moved", [unit_id, from_p, to_p])

func test_event_bus_unit_attacked_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_attacked.emit("Aquele", "Zangao_01", true, true, 18, "Cortante")
	# Assert
	assert_signal_emitted(_eb, "unit_attacked")
	assert_signal_emitted_with_parameters(_eb, "unit_attacked", ["Aquele", "Zangao_01", true, true, 18, "Cortante"])

func test_event_bus_unit_damaged_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_damaged.emit("hero_elden", 10, 25, 35)
	# Assert
	assert_signal_emitted(_eb, "unit_damaged")
	assert_signal_emitted_with_parameters(_eb, "unit_damaged", ["hero_elden", 10, 25, 35])

func test_event_bus_unit_died_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_died.emit("enemy_goblin_04")
	# Assert
	assert_signal_emitted(_eb, "unit_died")
	assert_signal_emitted_with_parameters(_eb, "unit_died", ["enemy_goblin_04"])

func test_event_bus_death_save_rolled_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.death_save_rolled.emit("hero_novak", 20, 1, 0, "REVIVED")
	# Assert
	assert_signal_emitted(_eb, "death_save_rolled")
	assert_signal_emitted_with_parameters(_eb, "death_save_rolled", ["hero_novak", 20, 1, 0, "REVIVED"])

func test_event_bus_status_applied_and_removed_signals():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.status_applied.emit("hero_darwin", "Envenenado", 3)
	_eb.status_removed.emit("hero_darwin", "Envenenado")
	# Assert
	assert_signal_emit_count(_eb, "status_applied", 1)
	assert_signal_emit_count(_eb, "status_removed", 1)

func test_event_bus_card_selected_and_round_resolved_signals():
	# Arrange
	watch_signals(_eb)
	var sync_data = {"round": 1, "synergy": "SUPREMA", "bonus_crystals": 2}
	# Act
	_eb.card_selected.emit("player_1", "card_escavacao_01")
	_eb.round_resolved.emit(1, sync_data)
	# Assert
	assert_signal_emitted_with_parameters(_eb, "card_selected", ["player_1", "card_escavacao_01"])
	assert_signal_emitted_with_parameters(_eb, "round_resolved", [1, sync_data])

func test_event_bus_resources_updated_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.resources_updated.emit(12, 8, 4, 3)
	# Assert
	assert_signal_emitted_with_parameters(_eb, "resources_updated", [12, 8, 4, 3])

func test_event_bus_multiple_subscribers_receive_event():
	# Arrange
	var count = {"calls_a": 0, "calls_b": 0, "calls_c": 0}
	var cb_a = func(id): count["calls_a"] += 1
	var cb_b = func(id): count["calls_b"] += 1
	var cb_c = func(id): count["calls_c"] += 1
	_eb.unit_died.connect(cb_a)
	_eb.unit_died.connect(cb_b)
	_eb.unit_died.connect(cb_c)
	# Act
	_eb.unit_died.emit("target_boss")
	# Assert
	assert_eq(count["calls_a"], 1, "Listener A must receive signal")
	assert_eq(count["calls_b"], 1, "Listener B must receive signal")
	assert_eq(count["calls_c"], 1, "Listener C must receive signal")
	# Teardown
	_eb.unit_died.disconnect(cb_a)
	_eb.unit_died.disconnect(cb_b)
	_eb.unit_died.disconnect(cb_c)

func test_event_bus_disconnected_subscriber_ignored():
	# Arrange
	var received = {"active": 0, "removed": 0}
	var cb_active = func(id): received["active"] += 1
	var cb_removed = func(id): received["removed"] += 1
	_eb.unit_died.connect(cb_active)
	_eb.unit_died.connect(cb_removed)
	_eb.unit_died.disconnect(cb_removed)
	# Act
	_eb.unit_died.emit("target_unit")
	# Assert
	assert_eq(received["active"], 1, "Connected listener must receive signal")
	assert_eq(received["removed"], 0, "Disconnected listener must not receive signal")
	# Teardown
	_eb.unit_died.disconnect(cb_active)

func test_event_bus_extreme_values_safe():
	# Arrange
	watch_signals(_eb)
	var extreme_pos = Vector2i(9999, 9999)
	var extreme_dmg = 999999
	# Act & Assert
	_eb.unit_moved.emit("extreme_unit", Vector2i(-999, -999), extreme_pos)
	_eb.unit_damaged.emit("extreme_unit", extreme_dmg, -500, 100)
	assert_signal_emitted(_eb, "unit_moved")
	assert_signal_emitted(_eb, "unit_damaged")

# ==============================================================================
# SECTION 3: DataManager Tests (12 tests)
# ==============================================================================

func test_data_manager_loads_personagens_json():
	# Arrange & Act
	var loaded = _dm.load_all_data()
	# Assert
	assert_true(loaded, "load_all_data() must return true")
	assert_true(_dm.is_data_loaded(), "is_data_loaded() must be true")

func test_data_manager_get_hero_data_guerreiro():
	# Arrange
	var hero_id = "Guerreiro"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Guerreiro data must not be null")
	assert_eq(data.ac, 18, "Guerreiro AC must be 18")
	assert_eq(data.stats.forca, 16, "Guerreiro Força must be 16")
	assert_eq(data.stats.constituicao, 14, "Guerreiro Constituicao must be 14")
	assert_eq(data.stats.destreza, 12, "Guerreiro Destreza must be 12")
	assert_eq(data.dado_vida, [1, 10], "Guerreiro dado_vida must be [1, 10]")
	assert_eq(data.tipo_dano, "Cortante", "Guerreiro tipo_dano must be Cortante")

func test_data_manager_get_hero_data_mago():
	# Arrange
	var hero_id = "Mago"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Mago data must not be null")
	assert_eq(data.ac, 10, "Mago AC must be 10")
	assert_eq(data.stats.inteligencia, 16, "Mago Inteligência must be 16")
	assert_eq(data.alcance, 6, "Mago alcance must be 6")
	assert_eq(data.tipo_dano, "Magico", "Mago tipo_dano must be Magico")

func test_data_manager_get_hero_data_ladino():
	# Arrange
	var hero_id = "Ladino"
	# Act
	var data = _dm.get_hero_data(hero_id)
	# Assert
	assert_not_null(data, "Ladino data must not be null")
	assert_eq(data.ac, 12, "Ladino AC must be 12")
	assert_eq(data.stats.destreza, 16, "Ladino Destreza must be 16")
	assert_eq(data.velocidade, 4, "Ladino velocidade must be 4")
	assert_eq(data.tipo_dano, "Perfurante", "Ladino tipo_dano must be Perfurante")

func test_data_manager_get_all_heroes_count():
	# Arrange & Act
	var all_heroes = _dm.get_all_heroes()
	# Assert
	assert_gte(all_heroes.size(), 9, "Must contain at least 9 playable hero classes")

func test_data_manager_boss_stats_rei_goblin():
	# Arrange
	var boss_id = "ReiGoblin"
	# Act
	var data = _dm.get_hero_data(boss_id)
	# Assert
	assert_not_null(data, "ReiGoblin data must not be null")
	assert_eq(data.hp, 250, "ReiGoblin HP must be 250")
	assert_eq(data.ac, 18, "ReiGoblin AC must be 18")
	assert_eq(data.dado_dano, [2, 6], "ReiGoblin damage dice must be [2, 6]")

func test_data_manager_query_nonexistent_hero_returns_null():
	# Arrange
	var fake_id = "BatmanSuperHero"
	# Act
	var data = _dm.get_hero_data(fake_id)
	# Assert
	assert_null(data, "Querying non-existent hero must return null without crashing")

func test_data_manager_query_empty_string_returns_null():
	# Arrange & Act
	var data = _dm.get_hero_data("")
	# Assert
	assert_null(data, "Querying empty string must return null")

func test_data_manager_cache_persistence():
	# Arrange
	var id = "Guerreiro"
	# Act
	var ref1 = _dm.get_hero_data(id)
	var ref2 = _dm.get_hero_data(id)
	# Assert
	assert_eq(ref1, ref2, "Subsequent queries for same hero must return cached reference")

func test_data_manager_clear_cache():
	# Arrange
	assert_true(_dm.is_data_loaded())
	# Act
	_dm.clear_cache()
	# Assert
	assert_false(_dm.is_data_loaded(), "is_data_loaded() must be false after clear_cache()")
	assert_eq(_dm.get_all_heroes().size(), 0, "Heroes collection must be empty after clear")
	# Re-arm
	_dm.load_all_data()

func test_data_manager_missing_file_graceful_handling():
	# Arrange: isolated DataManager instance pointing to invalid path
	var custom_dm = autofree(DataManagerScript.new())
	# Act
	var success = custom_dm.load_from_file("res://dados/non_existent_file.json")
	# Assert
	assert_false(success, "Loading from missing file must return false gracefully")

func test_data_manager_corrupted_json_handling():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var malformed_content = "{ 'Guerreiro': { unclosed json ... "
	# Act
	var success = custom_dm.parse_raw_json(malformed_content)
	# Assert
	assert_false(success, "Parsing corrupt JSON string must return false and log error")

# ==============================================================================
# SECTION 4: AudioManager Tests (11 tests)
# ==============================================================================

func test_audio_manager_play_bgm():
	# Arrange
	var track = "menu"
	# Act
	_am.play_bgm(track, 0.0)
	# Assert
	assert_true(_am.is_bgm_playing(), "BGM must be marked playing")
	assert_eq(_am.get_current_bgm(), track, "Current BGM must match 'menu'")

func test_audio_manager_stop_bgm():
	# Arrange
	_am.play_bgm("menu", 0.0)
	# Act
	_am.stop_bgm(0.0)
	# Assert
	assert_false(_am.is_bgm_playing(), "BGM must not be playing after stop")

func test_audio_manager_switch_bgm_track():
	# Arrange
	_am.play_bgm("menu", 0.0)
	# Act
	_am.play_bgm("battle1", 0.0)
	# Assert
	assert_eq(_am.get_current_bgm(), "battle1", "Active BGM track must update to 'battle1'")

func test_audio_manager_play_sfx_pool_allocation():
	# Arrange
	var sfx_name = "button_click"
	# Act
	var player = _am.play_sfx(sfx_name)
	# Assert
	assert_not_null(player, "SFX player must be allocated from pool")

func test_audio_manager_set_and_get_bus_volume():
	# Arrange
	var target_vol = 0.75
	# Act
	_am.set_bus_volume("Master", target_vol)
	var actual_vol = _am.get_bus_volume("Master")
	# Assert
	assert_between(actual_vol, 0.74, 0.76, "Bus volume must match set value within 0.01 tolerance")

func test_audio_manager_play_nonexistent_sfx_graceful():
	# Arrange
	var fake_sfx = "laser_cannon_9000"
	# Act
	var player = _am.play_sfx(fake_sfx)
	# Assert
	assert_null(player, "Playing nonexistent SFX must return null and not crash")

func test_audio_manager_play_nonexistent_bgm_graceful():
	# Arrange
	var fake_bgm = "nonexistent_orchestra"
	# Act
	_am.play_bgm(fake_bgm, 0.0)
	# Assert
	assert_false(_am.is_bgm_playing(), "Invalid BGM track must not start playing")

func test_audio_manager_volume_clamping_upper():
	# Arrange & Act
	_am.set_bus_volume("Master", 2.5)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_lte(vol, 1.0, "Volume must be clamped to max 1.0")

func test_audio_manager_volume_clamping_lower():
	# Arrange & Act
	_am.set_bus_volume("Master", -1.0)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_gte(vol, 0.0, "Volume must be clamped to min 0.0")

func test_audio_manager_sfx_pool_rapid_fire():
	# Arrange
	var sfx = "attack"
	var allocated_players = []
	# Act: rapidly play 16 sound effects (exceeding typical pool default of 8)
	for i in range(16):
		var p = _am.play_sfx(sfx)
		if p != null:
			allocated_players.append(p)
	# Assert: pool handled allocation without crashing or leaking
	assert_gt(allocated_players.size(), 0, "Pool must allocate and cycle players safely")

func test_audio_manager_headless_safety():
	# Arrange & Act
	_am.play_bgm("intro", 0.0)
	_am.play_sfx("miss")
	_am.stop_bgm(0.0)
	# Assert: headless dummy driver executes commands smoothly
	pass_test("AudioManager runs safely in headless execution mode")
