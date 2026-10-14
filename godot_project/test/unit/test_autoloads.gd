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
		_eb.reset_telemetry()
	else:
		_eb = autofree(EventBusScript.new())

	if get_node_or_null("/root/DataManager") != null:
		_dm = get_node("/root/DataManager")
		_dm.load_all_data()
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
	if _am != null:
		if _am.has_method("stop_all_sfx"):
			_am.stop_all_sfx()
		if _am.has_method("stop_bgm"):
			_am.stop_bgm(0.0)

func after_all():
	_received_events.clear()
	if _am != null:
		if _am.has_method("stop_all_sfx"):
			_am.stop_all_sfx()
		if _am.has_method("stop_bgm"):
			_am.stop_bgm(0.0)
	_gm = null
	_eb = null
	_dm = null
	_am = null

# ==============================================================================
# SECTION 1: GameManager Tests (14 tests)
# ==============================================================================

func test_game_manager_initial_state_is_menu():
	# Arrange
	_gm.reset_state()
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
	var ok = _gm.change_state(target_state)
	# Assert
	assert_true(ok, "Transition to CERCO_ISECTUM must succeed")
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
	var results: Array[bool] = []
	# Act
	for state in transitions:
		var result = _gm.change_state(state)
		results.append(result)
	# Assert
	for i in range(transitions.size()):
		assert_true(results[i], "Transition to state %s must be valid" % transitions[i])
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Final state must be MENU")

func test_game_manager_is_in_combat_flag():
	# Arrange
	_gm.reset_state()
	var combat_tactical = _gm.GameState.COMBATE_TATICO
	var gameover_state = _gm.GameState.FIM_DE_JOGO
	var combat_cerco = _gm.GameState.CERCO_ISECTUM

	# Act 1: Initial state is MENU
	var in_combat_menu = _gm.is_in_combat()
	# Assert 1
	assert_false(in_combat_menu, "MENU is not combat")

	# Act 2: Valid transition MENU -> COMBATE_TATICO
	var ok_tactical = _gm.change_state(combat_tactical)
	var in_combat_tactical = _gm.is_in_combat()
	# Assert 2
	assert_true(ok_tactical, "Transition MENU -> COMBATE_TATICO must return true")
	assert_true(in_combat_tactical, "COMBATE_TATICO is combat")

	# Act 3: Valid transition COMBATE_TATICO -> FIM_DE_JOGO
	var ok_gameover = _gm.change_state(gameover_state)
	var in_combat_gameover = _gm.is_in_combat()
	# Assert 3
	assert_true(ok_gameover, "Transition COMBATE_TATICO -> FIM_DE_JOGO must return true")
	assert_false(in_combat_gameover, "FIM_DE_JOGO is not combat")

	# Act 4: Valid transition FIM_DE_JOGO -> CERCO_ISECTUM
	var ok_cerco = _gm.change_state(combat_cerco)
	var in_combat_cerco = _gm.is_in_combat()
	# Assert 4
	assert_true(ok_cerco, "Transition FIM_DE_JOGO -> CERCO_ISECTUM must return true")
	assert_true(in_combat_cerco, "CERCO_ISECTUM is combat")

func test_game_manager_get_state_name_mapping():
	# Arrange
	var menu_state = _gm.GameState.MENU
	var tactical_state = _gm.GameState.COMBATE_TATICO
	var cerco_state = _gm.GameState.CERCO_ISECTUM
	var lobby_state = _gm.GameState.MULTIPLAYER_LOBBY
	var game_over_state = _gm.GameState.FIM_DE_JOGO

	# Act
	var name_menu = _gm.get_state_name(menu_state)
	var name_tactical = _gm.get_state_name(tactical_state)
	var name_cerco = _gm.get_state_name(cerco_state)
	var name_lobby = _gm.get_state_name(lobby_state)
	var name_game_over = _gm.get_state_name(game_over_state)

	# Assert
	assert_eq(name_menu, "MENU")
	assert_eq(name_tactical, "COMBATE_TATICO")
	assert_eq(name_cerco, "CERCO_ISECTUM")
	assert_eq(name_lobby, "MULTIPLAYER_LOBBY")
	assert_eq(name_game_over, "FIM_DE_JOGO")

func test_game_manager_transition_to_same_state_is_noop():
	# Arrange
	_gm.reset_state()
	watch_signals(_gm)
	# Act
	var result = _gm.change_state(_gm.GameState.MENU)
	# Assert
	assert_false(result, "Transition to identical state must return false")
	assert_signal_not_emitted(_gm, "state_changed", "No redundant signal when state does not change")

func test_game_manager_reset_state_restores_menu():
	# Arrange: Move to COMBATE_TATICO via legal transition
	var ok = _gm.change_state(_gm.GameState.COMBATE_TATICO)
	assert_true(ok, "Legal transition to COMBATE_TATICO must succeed")
	assert_true(_gm.is_in_combat(), "Must be in combat before reset")
	# Act
	_gm.reset_state()
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "Reset must restore MENU state")
	assert_false(_gm.is_in_combat(), "Reset must clear combat status")

func test_game_manager_rapid_sequential_transitions():
	# Arrange: Sequence of 100% legal transitions
	var valid_cycle = [
		_gm.GameState.COMBATE_TATICO,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU,
		_gm.GameState.CERCO_ISECTUM,
		_gm.GameState.FIM_DE_JOGO,
		_gm.GameState.MENU
	]
	var results: Array[bool] = []
	# Act
	for s in valid_cycle:
		var res = _gm.change_state(s)
		results.append(res)
	# Assert
	for i in range(results.size()):
		assert_true(results[i], "Transition step %d to state %s must succeed" % [i, _gm.get_state_name(valid_cycle[i])])
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

func test_game_manager_payload_deep_copy_isolation():
	# Arrange
	var payload = {"room": "room_123", "meta": {"turn": 1, "crystals": 10}}
	# Act
	var ok = _gm.change_state(_gm.GameState.COMBATE_TATICO, payload)
	payload["meta"]["turn"] = 999 # External mutation of original
	var stored = _gm.get_state_payload()
	stored["meta"]["crystals"] = 999 # Mutation of getter return value
	var stored_again = _gm.get_state_payload()
	# Assert
	assert_true(ok, "State change with payload must succeed")
	assert_eq(stored["room"], "room_123", "Payload room matches")
	assert_eq(stored_again["meta"]["turn"], 1, "Internal payload isolated from external dict mutation")
	assert_eq(stored_again["meta"]["crystals"], 10, "Internal payload isolated from getter mutation")

func test_game_manager_can_transition_to_validation():
	# Arrange
	_gm.reset_state()
	# Act
	var can_combat = _gm.can_transition_to(_gm.GameState.COMBATE_TATICO)
	var can_cerco = _gm.can_transition_to(_gm.GameState.CERCO_ISECTUM)
	var can_gameover = _gm.can_transition_to(_gm.GameState.FIM_DE_JOGO)
	# Assert
	assert_true(can_combat, "MENU -> COMBATE_TATICO is valid")
	assert_true(can_cerco, "MENU -> CERCO_ISECTUM is valid")
	assert_false(can_gameover, "MENU -> FIM_DE_JOGO is invalid")

func test_game_manager_reset_to_menu():
	# Arrange
	var ok = _gm.change_state(_gm.GameState.COMBATE_TATICO)
	assert_true(ok, "Must transition to COMBATE_TATICO")
	# Act
	_gm.reset_to_menu()
	# Assert
	assert_eq(_gm.current_state, _gm.GameState.MENU, "reset_to_menu must restore MENU")
	assert_false(_gm.is_in_combat(), "Must not be in combat after reset_to_menu")

func test_game_manager_change_state_and_scene_headless():
	# Arrange
	_gm.reset_state()
	# Act
	var success = _gm.change_state_and_scene(_gm.GameState.COMBATE_TATICO)
	# Assert
	assert_true(success, "change_state_and_scene must return true in headless test mode")
	assert_eq(_gm.current_state, _gm.GameState.COMBATE_TATICO)

# ==============================================================================
# SECTION 2: EventBus Tests (13 tests)
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
	var attacker = "hero_stark"
	var target = "goblin_1"
	# Act
	_eb.unit_attacked.emit(attacker, target, true, false, 8, "Cortante")
	# Assert
	assert_signal_emitted(_eb, "unit_attacked")
	assert_signal_emitted_with_parameters(_eb, "unit_attacked", [attacker, target, true, false, 8, "Cortante"])

func test_event_bus_unit_damaged_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_damaged.emit("hero_stark", 12, 38, 50)
	# Assert
	assert_signal_emitted(_eb, "unit_damaged")
	assert_signal_emitted_with_parameters(_eb, "unit_damaged", ["hero_stark", 12, 38, 50])

func test_event_bus_unit_died_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.unit_died.emit("goblin_1")
	# Assert
	assert_signal_emitted(_eb, "unit_died")
	assert_signal_emitted_with_parameters(_eb, "unit_died", ["goblin_1"])

func test_event_bus_death_save_rolled_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.death_save_rolled.emit("hero_stark", 15, 2, 1, "Success")
	# Assert
	assert_signal_emitted(_eb, "death_save_rolled")
	assert_signal_emitted_with_parameters(_eb, "death_save_rolled", ["hero_stark", 15, 2, 1, "Success"])

func test_event_bus_status_applied_and_removed_signals():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.status_applied.emit("hero_stark", "Envenenado", 3)
	_eb.status_removed.emit("hero_stark", "Envenenado")
	# Assert
	assert_signal_emitted(_eb, "status_applied")
	assert_signal_emitted_with_parameters(_eb, "status_applied", ["hero_stark", "Envenenado", 3])
	assert_signal_emitted(_eb, "status_removed")
	assert_signal_emitted_with_parameters(_eb, "status_removed", ["hero_stark", "Envenenado"])

func test_event_bus_card_selected_and_round_resolved_signals():
	# Arrange
	watch_signals(_eb)
	var sync_data = {"movement": [Vector2i(1, 1)]}
	# Act
	_eb.card_selected.emit("player_1", "card_ataque_rapido")
	_eb.round_resolved.emit(1, sync_data)
	# Assert
	assert_signal_emitted(_eb, "card_selected")
	assert_signal_emitted_with_parameters(_eb, "card_selected", ["player_1", "card_ataque_rapido"])
	assert_signal_emitted(_eb, "round_resolved")
	assert_signal_emitted_with_parameters(_eb, "round_resolved", [1, sync_data])

func test_event_bus_resources_updated_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_eb.resources_updated.emit(10, 5, 2, 3)
	# Assert
	assert_signal_emitted(_eb, "resources_updated")
	assert_signal_emitted_with_parameters(_eb, "resources_updated", [10, 5, 2, 3])

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
	# Act
	_eb.unit_moved.emit("extreme_unit", Vector2i(-999, -999), extreme_pos)
	_eb.unit_damaged.emit("extreme_unit", extreme_dmg, -500, 100)
	# Assert
	assert_signal_emitted(_eb, "unit_moved")
	assert_signal_emitted(_eb, "unit_damaged")

func test_event_bus_telemetry_recording_and_reset():
	# Arrange
	_eb.reset_telemetry()
	# Act
	_eb.emit_logged("unit_died", ["target_logged"])
	var count_logged = _eb.get_emission_count("unit_died")
	_eb.reset_telemetry()
	var count_after_reset = _eb.get_emission_count("unit_died")
	# Assert
	assert_eq(count_logged, 1, "Emission count must be 1 after emit_logged")
	assert_eq(count_after_reset, 0, "Emission count must be reset to 0")

func test_event_bus_game_reset_signal():
	# Arrange
	watch_signals(_eb)
	# Act
	_gm.reset_state()
	# Assert
	assert_signal_emitted(_eb, "game_reset", "game_reset signal must be emitted upon reset_state")

# ==============================================================================
# SECTION 3: DataManager Tests (16 tests)
# ==============================================================================

func test_data_manager_loads_personagens_json():
	# Arrange
	_dm.clear_cache()
	# Act
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
	# Arrange
	_dm.load_all_data()
	# Act
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
	# Arrange
	var empty_id = ""
	# Act
	var data = _dm.get_hero_data(empty_id)
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
	_dm.load_all_data()
	var loaded_before = _dm.is_data_loaded()
	# Act
	_dm.clear_cache()
	var loaded_after = _dm.is_data_loaded()
	var count_after = _dm.get_all_heroes().size()
	# Assert
	assert_true(loaded_before, "Data was initially loaded")
	assert_false(loaded_after, "is_data_loaded() must be false after clear_cache()")
	assert_eq(count_after, 0, "Heroes collection must be empty after clear")
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

func test_data_manager_heroes_and_enemies_segregation():
	# Arrange
	_dm.load_all_data()
	# Act
	var heroes = _dm.get_all_heroes()
	var enemies = _dm.get_all_enemies()
	var hero_names: Array[String] = []
	for h in heroes:
		hero_names.append(h.id)
	var enemy_names: Array[String] = []
	for e in enemies:
		enemy_names.append(e.id)
	# Assert
	assert_has(hero_names, "Guerreiro", "Playable hero Guerreiro must be in heroes")
	assert_has(hero_names, "Aquele", "Playable hero Aquele must be in heroes")
	assert_false(hero_names.has("ReiGoblin"), "Boss ReiGoblin must NOT be in heroes")
	assert_false(hero_names.has("LordeLich"), "Boss LordeLich must NOT be in heroes")
	assert_has(enemy_names, "ReiGoblin", "Boss ReiGoblin must be in enemies")
	assert_has(enemy_names, "LordeLich", "Boss LordeLich must be in enemies")
	assert_false(enemy_names.has("Guerreiro"), "Playable hero Guerreiro must NOT be in enemies")

func test_data_manager_hero_duplicate_mutation_isolation():
	# Arrange
	var original = _dm.get_hero_data("Guerreiro")
	var orig_hp = original.hp
	# Act
	var dup = _dm.get_hero_duplicate("Guerreiro")
	dup.hp = 9999
	# Assert
	assert_not_null(dup, "Duplicate must be non-null")
	assert_ne(dup, original, "Duplicate must be a distinct object reference")
	assert_eq(original.hp, orig_hp, "Original character HP must not be modified by copy mutation")

func test_data_manager_isectum_castes_helper_methods():
	# Arrange
	var target_caste = "vespa_cacadora"
	# Act
	var caste_data = _dm.get_isectum_caste(target_caste)
	var all_castes = _dm.get_all_isectum_castes()
	var exists_true = _dm.has_caste(target_caste)
	var exists_false = _dm.has_caste("non_existent_caste_xyz")
	# Assert
	assert_not_null(caste_data, "Vespa Caçadora must exist in castes")
	assert_gte(all_castes.size(), 24, "All 24 Isectum castes must be loaded")
	assert_true(exists_true, "has_caste must return true for valid caste")
	assert_false(exists_false, "has_caste must return false for unknown caste")

func test_data_manager_cards_helper_methods():
	# Arrange
	var target_card = "trabalho_1"
	# Act
	var card_data = _dm.get_card_data(target_card)
	var all_cards = _dm.get_all_cards()
	var exists_true = _dm.has_card(target_card)
	var exists_false = _dm.has_card("non_existent_card_xyz")
	# Assert
	assert_not_null(card_data, "trabalho_1 must exist in cards")
	assert_gt(all_cards.size(), 0, "Cards list must not be empty")
	assert_true(exists_true, "has_card must return true for valid card")
	assert_false(exists_false, "has_card must return false for unknown card")

# ==============================================================================
# SECTION 4: AudioManager Tests (14 tests)
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
	# Arrange
	var high_vol = 2.5
	# Act
	_am.set_bus_volume("Master", high_vol)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_lte(vol, 1.0, "Volume must be clamped to max 1.0")

func test_audio_manager_volume_clamping_lower():
	# Arrange
	var low_vol = -1.0
	# Act
	_am.set_bus_volume("Master", low_vol)
	var vol = _am.get_bus_volume("Master")
	# Assert
	assert_gte(vol, 0.0, "Volume must be clamped to min 0.0")

func test_audio_manager_sfx_pool_rapid_fire():
	# Arrange
	var sfx = "attack"
	var allocated_players = []
	# Act: rapidly play 16 sound effects (exceeding pool size of 12)
	for i in range(16):
		var p = _am.play_sfx(sfx)
		if p != null:
			allocated_players.append(p)
	# Assert: pool handled allocation without crashing
	assert_gt(allocated_players.size(), 0, "Pool must allocate and cycle players safely")

func test_audio_manager_headless_safety():
	# Arrange
	var bgm_track = "intro"
	var sfx_track = "miss"
	# Act
	_am.play_bgm(bgm_track, 0.0)
	var player = _am.play_sfx(sfx_track)
	_am.stop_bgm(0.0)
	# Assert
	assert_not_null(player, "SFX player successfully allocated in headless mode")
	assert_false(_am.is_bgm_playing(), "BGM stopped cleanly in headless mode")

func test_audio_manager_bus_mute_controls():
	# Arrange
	var bus_name = "Master"
	# Act
	_am.set_bus_muted(bus_name, true)
	var is_muted = _am.is_bus_muted(bus_name)
	_am.set_bus_muted(bus_name, false)
	var is_unmuted = _am.is_bus_muted(bus_name)
	# Assert
	assert_true(is_muted, "Bus Master must report muted")
	assert_false(is_unmuted, "Bus Master must report unmuted")

func test_audio_manager_stop_all_sfx():
	# Arrange
	_am.play_sfx("button_click")
	_am.play_sfx("hit")
	# Act
	_am.stop_all_sfx()
	var any_playing = false
	var any_stream_assigned = false
	for p in _am._sfx_pool:
		if p.playing:
			any_playing = true
		if p.stream != null:
			any_stream_assigned = true
	# Assert
	assert_false(any_playing, "All SFX players must be stopped")
	assert_false(any_stream_assigned, "All SFX streams must be cleared to null")

func test_audio_manager_pitch_scale_setting():
	# Arrange
	var target_pitch = 1.5
	# Act
	var player = _am.play_sfx("attack", 1.0, target_pitch)
	# Assert
	assert_not_null(player, "Player must be returned")
	assert_almost_eq(player.pitch_scale, target_pitch, 0.01, "Player pitch scale must match requested pitch")
