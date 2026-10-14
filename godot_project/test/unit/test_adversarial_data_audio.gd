# test/unit/test_adversarial_data_audio.gd
# Adversarial Stress Test Suite for DataManager and AudioManager
# Tests corrupt JSON, schema edge-cases, CharacterData mutation isolation,
# audio pool exhaustion (>30 concurrent SFX), volume bounds, and headless safety.
# Strictly follows AAA (Arrange-Act-Assert) pattern.
extends GutTest

const DataManagerScript = preload("res://scripts/autoload/DataManager.gd")
const AudioManagerScript = preload("res://scripts/autoload/AudioManager.gd")

var _dm: Node = null
var _am: Node = null

func before_each():
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
	if _am != null and _am.has_method("stop_all_sfx"):
		_am.stop_all_sfx()
	if _am != null and _am.has_method("stop_bgm"):
		_am.stop_bgm(0.0)
	if _dm != null and _dm.has_method("load_all_data"):
		_dm.load_all_data() # restore canonical state

func after_all():
	if _am != null and _am.has_method("stop_all_sfx"):
		_am.stop_all_sfx()
	if _am != null and _am.has_method("stop_bgm"):
		_am.stop_bgm(0.0)
	_dm = null
	_am = null

# ==============================================================================
# SECTION 1: DataManager Adversarial JSON & Schema Stress Tests
# ==============================================================================

func test_dm_stress_empty_string_json():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	# Act
	var result = custom_dm.parse_raw_json("")
	# Assert
	assert_false(result, "Empty JSON string must be rejected gracefully without crash")

func test_dm_stress_whitespace_only_json():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	# Act
	var result = custom_dm.parse_raw_json("   \n\t  \r  ")
	# Assert
	assert_false(result, "Whitespace-only JSON string must be rejected gracefully")

func test_dm_stress_malformed_syntax_json():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var malformed_payloads = [
		"{",
		"{\"key\": }",
		"{\"unclosed_string: 123}",
		"<html><body>Not JSON</body></html>",
		"NaN",
		"{'single_quotes': true}"
	]
	var results: Array[bool] = []

	# Act
	for payload in malformed_payloads:
		results.append(custom_dm.parse_raw_json(payload))

	# Assert
	for i in range(results.size()):
		assert_false(results[i], "Malformed JSON syntax must return false: %s" % malformed_payloads[i])

func test_dm_stress_json_trailing_comma_behavior():
	# Arrange: Godot's JSON parser accepts trailing commas in dictionaries
	var custom_dm = autofree(DataManagerScript.new())
	var trailing_comma_json = "{\"hero\": {\"nome\": \"Hero\",}}"
	# Act
	var result = custom_dm.parse_raw_json(trailing_comma_json)
	# Assert
	assert_true(result, "Godot 4 JSON parser permissively allows trailing commas in dicts")

func test_dm_stress_root_array_instead_of_dict():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var array_json = "[{\"nome\": \"Hero\"}, {\"nome\": \"Enemy\"}]"
	# Act
	var result = custom_dm.parse_raw_json(array_json)
	# Assert
	assert_false(result, "Root JSON as an Array must be rejected (expects Dictionary)")

func test_dm_stress_root_scalar_types():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var scalars = ["123", "true", "\"just a string\"", "null"]
	var results: Array[bool] = []

	# Act
	for s in scalars:
		results.append(custom_dm.parse_raw_json(s))

	# Assert
	for i in range(results.size()):
		assert_false(results[i], "Root scalar '%s' must be rejected" % scalars[i])

func test_dm_stress_parse_raw_json_retains_existing_cache():
	# Arrange: Custom DataManager already loads 28 default characters in _ready()
	var custom_dm = autofree(DataManagerScript.new())
	var initial_count = custom_dm.get_all_heroes().size()
	assert_gte(initial_count, 9, "Initial characters should be loaded")

	# Act: Parse empty dictionary without clear_cache()
	var result = custom_dm.parse_raw_json("{}")

	# Assert: Proves parse_raw_json does NOT clear cache; it retains previous entities
	assert_true(result, "Empty dictionary parses as valid JSON")
	assert_eq(custom_dm.get_all_heroes().size(), initial_count, "parse_raw_json appends/overwrites, does NOT clear existing cache")

func test_dm_stress_parse_raw_json_after_clear_cache():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	custom_dm.clear_cache()
	assert_eq(custom_dm.get_all_heroes().size(), 0)

	# Act
	var result = custom_dm.parse_raw_json("{}")

	# Assert
	assert_true(result)
	assert_eq(custom_dm.get_all_heroes().size(), 0, "No heroes present in a cleared cache parsed with empty dict")

func test_dm_stress_non_dict_entries_in_root():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var mixed_json = "{\"hero_valid\": {\"nome\": \"Valid\"}, \"invalid_int\": 42, \"invalid_str\": \"foo\", \"invalid_arr\": [1,2]}"
	# Act
	var result = custom_dm.parse_raw_json(mixed_json)
	# Assert
	assert_true(result, "Valid root dict should parse successfully")
	assert_not_null(custom_dm.get_hero_data("hero_valid"), "Valid entry must be parsed")
	assert_null(custom_dm.get_hero_data("invalid_int"), "Non-dict entries must be skipped without crashing")
	assert_null(custom_dm.get_hero_data("invalid_str"), "Non-dict entries must be skipped without crashing")

func test_dm_stress_character_empty_data_dictionary():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var empty_char_json = "{\"EmptyHero\": {}}"
	# Act
	var result = custom_dm.parse_raw_json(empty_char_json)
	var hero = custom_dm.get_hero_data("EmptyHero")
	# Assert
	assert_true(result, "Empty hero dict should be parsed with defaults")
	assert_not_null(hero, "Hero object must be created")
	assert_eq(hero.id, "EmptyHero")
	assert_eq(hero.name, "EmptyHero")
	assert_eq(hero.ac, 10, "Default AC should be 10")
	# In DataManager.gd: max_hp = max(1, dice[1] + con_mod) where dice defaults to [1, 8] and con_mod is 0 -> 8
	assert_eq(hero.hp, 8, "Default HP with 1d8 (8) + ConMod(0) = 8")
	assert_eq(hero.forca, 10, "Default Strength should be 10")

func test_dm_stress_character_missing_stats_block():
	# Arrange
	var custom_dm = autofree(DataManagerScript.new())
	var json_str = "{\"NoStatsHero\": {\"nome\": \"Nameless\", \"hp\": 30, \"ac\": 15}}"
	# Act
	var result = custom_dm.parse_raw_json(json_str)
	var hero = custom_dm.get_hero_data("NoStatsHero")
	# Assert
	assert_true(result)
	assert_not_null(hero)
	assert_eq(hero.hp, 30)
	assert_eq(hero.ac, 15)
	assert_eq(hero.forca, 10, "Missing stats should fall back to 10")
	assert_eq(hero.stats.forca, 10, "Stats dictionary should be populated with defaults")

func test_dm_stress_large_scale_character_payload():
	# Arrange: generate 200 characters in raw JSON
	var custom_dm = autofree(DataManagerScript.new())
	custom_dm.clear_cache()
	var dict: Dictionary = {}
	for i in range(200):
		dict["Char_%d" % i] = {
			"nome": "Character %d" % i,
			"hp": 20 + (i % 50),
			"ac": 10 + (i % 10),
			"stats": {"forca": 12, "destreza": 14}
		}
	var json_str = JSON.stringify(dict)

	# Act
	var result = custom_dm.parse_raw_json(json_str)

	# Assert
	assert_true(result, "Bulk character parsing should succeed")
	assert_eq(custom_dm.get_all_heroes().size(), 200, "All 200 characters must be cached")
	var sample = custom_dm.get_hero_data("Char_199")
	assert_not_null(sample)
	assert_eq(sample.name, "Character 199")

# ==============================================================================
# SECTION 2: CharacterData Mutation Isolation Stress Tests
# ==============================================================================

func test_dm_isolation_primitive_field_mutation():
	# Arrange
	var hero1 = _dm.get_hero_data("Guerreiro")
	assert_not_null(hero1, "Precondition: Guerreiro must exist")
	var original_hp = hero1.hp
	var original_ac = hero1.ac

	# Act: Mutate hero1 primitive fields directly
	hero1.hp = 1
	hero1.ac = 99

	# Query hero again from DataManager
	var hero2 = _dm.get_hero_data("Guerreiro")

	# Assert: EMPIRICAL PROOF OF SHARED MUTABLE REFERENCE
	var is_shared = (hero2.hp == 1 and hero2.ac == 99)
	# Cleanup cache immediately to avoid test pollution
	hero1.hp = original_hp
	hero1.ac = original_ac

	assert_true(is_shared, "CRITICAL FINDING: get_hero_data returns shared mutable reference, violating mutation isolation")

func test_dm_isolation_nested_dictionary_mutation():
	# Arrange
	var hero1 = _dm.get_hero_data("Mago")
	assert_not_null(hero1)
	var original_forca = hero1.stats.get("forca", 10)

	# Act: mutate nested dictionary
	hero1.stats["forca"] = 999
	var hero2 = _dm.get_hero_data("Mago")

	# Assert: EMPIRICAL PROOF OF SHARED NESTED DICT
	var dict_is_shared = (hero2.stats["forca"] == 999)
	hero1.stats["forca"] = original_forca # Cleanup

	assert_true(dict_is_shared, "CRITICAL FINDING: Nested stats dictionary is shared across get_hero_data callers")

func test_dm_isolation_array_mutation():
	# Arrange
	var hero1 = _dm.get_hero_data("Ladino")
	assert_not_null(hero1)
	var orig_dice_size = hero1.dado_vida.size()

	# Act: mutate array
	hero1.dado_vida.append(9999)
	var hero2 = _dm.get_hero_data("Ladino")

	# Assert: EMPIRICAL PROOF OF SHARED ARRAY
	var array_is_shared = (hero2.dado_vida.size() == orig_dice_size + 1)
	hero1.dado_vida.pop_back() # Cleanup

	assert_true(array_is_shared, "CRITICAL FINDING: Array dado_vida is shared across get_hero_data callers")

func test_dm_isolation_duplicate_data_provides_deep_isolation():
	# Arrange
	var hero = _dm.get_hero_data("Guerreiro")
	assert_not_null(hero)

	# Act: deep clone via duplicate_data()
	var clone = hero.duplicate_data()
	clone.hp = 999
	clone.stats["forca"] = 777
	clone.dado_vida.append(100)
	clone.resistencias["Fogo"] = 0.0

	# Assert: verify duplicate_data() itself works properly
	assert_ne(hero.hp, clone.hp, "Primitive hp must be isolated in duplicate_data")
	assert_ne(hero.stats["forca"], clone.stats["forca"], "Stats dictionary must be isolated in duplicate_data")
	assert_ne(hero.dado_vida.size(), clone.dado_vida.size(), "dado_vida array must be isolated in duplicate_data")
	assert_false(hero.resistencias.has("Fogo"), "resistencias dictionary must be isolated in duplicate_data")

func test_dm_isolation_get_hero_duplicate_isolates_cache():
	# Arrange
	var original_hp = _dm.get_hero_data("Stark").hp
	# Act
	var hero_dup = _dm.get_hero_duplicate("Stark")
	assert_not_null(hero_dup)
	hero_dup.hp = -50

	# Assert
	var fresh_query = _dm.get_hero_data("Stark")
	assert_eq(fresh_query.hp, original_hp, "get_hero_duplicate() properly prevents cache mutation")

func test_dm_isolation_get_all_heroes_returns_shared_references():
	# Arrange
	var list1 = _dm.get_all_heroes()
	assert_gt(list1.size(), 0)
	var first_hero = list1[0]
	var orig_hp = first_hero.hp

	# Act
	first_hero.hp = -99
	var list2 = _dm.get_all_heroes()

	# Assert: EMPIRICAL PROOF OF SHARED REFERENCES IN get_all_heroes()
	var list_is_shared = (list2[0].hp == -99)
	first_hero.hp = orig_hp # Cleanup
	assert_true(list_is_shared, "CRITICAL FINDING: get_all_heroes returns shared references from cache")

func test_dm_isolation_isectum_and_cards_lack_duplicate_api():
	# Arrange
	var caste_id = "vespa_cacadora"
	var card_id = "trabalho_1"

	# Act
	var caste = _dm.get_isectum_caste(caste_id)
	var card = _dm.get_card_data(card_id)

	# Assert
	assert_not_null(caste)
	assert_not_null(card)
	assert_false(caste.has_method("duplicate_data"), "IsectumCasteData lacks duplicate_data() method")
	assert_false(card.has_method("duplicate_data"), "CardData lacks duplicate_data() method")
	assert_false(_dm.has_method("get_isectum_caste_duplicate"), "DataManager lacks get_isectum_caste_duplicate()")
	assert_false(_dm.has_method("get_card_duplicate"), "DataManager lacks get_card_duplicate()")

# ==============================================================================
# SECTION 3: AudioManager Pool Exhaustion (>30 Concurrent SFX)
# ==============================================================================

func test_am_stress_pool_exhaustion_35_requests():
	# Arrange
	var sfx_key = "attack"
	var request_count = 35
	var allocated_players: Array[AudioStreamPlayer] = []

	# Act: rapidly request 35 SFX (pool size is 12)
	for i in range(request_count):
		var p = _am.play_sfx(sfx_key)
		assert_not_null(p, "Player allocation %d must not return null" % i)
		allocated_players.append(p)

	# Assert
	assert_eq(allocated_players.size(), 35, "All 35 requests must be processed without rejection or null")

	# Check pool distribution
	var unique_players: Dictionary = {}
	for p in allocated_players:
		var ptr_id = p.get_instance_id()
		unique_players[ptr_id] = unique_players.get(ptr_id, 0) + 1

	assert_lte(unique_players.size(), 12, "Allocated players must belong to the 12-player pool")
	assert_gt(unique_players.size(), 0, "At least one player must be used")

func test_am_stress_pool_exhaustion_100_concurrent_requests():
	# Arrange: extreme burst of 100 requests
	var sfx_keys = ["attack", "damage", "heal", "hit", "button_click"]
	var total_requests = 100
	var success_count = 0

	# Act
	for i in range(total_requests):
		var key = sfx_keys[i % sfx_keys.size()]
		var player = _am.play_sfx(key)
		if player != null:
			success_count += 1

	# Assert
	assert_eq(success_count, total_requests, "Pool must absorb 100 consecutive requests without crash")

func test_am_stress_pool_exhaustion_allocation_policy_bias():
	# Arrange
	var pool = _am.get("_sfx_pool")
	assert_not_null(pool)
	assert_eq(pool.size(), 12, "SFX pool size is 12")

	# Act: trigger multiple sound effects
	var p1 = _am.play_sfx("attack")
	var p2 = _am.play_sfx("damage")
	var p3 = _am.play_sfx("heal")

	# Assert: Round-robin allocation ensures successive calls cycle through distinct players
	assert_ne(p1, p2, "Round-robin allocation ensures p1 and p2 use distinct players")
	assert_ne(p2, p3, "Round-robin allocation ensures p2 and p3 use distinct players")
	assert_ne(p1, p3, "Round-robin allocation ensures p1 and p3 use distinct players")

# ==============================================================================
# SECTION 4: AudioManager Volume Bounds & Extreme Values
# ==============================================================================

func test_am_stress_bus_volume_extreme_upper():
	# Arrange
	var high_vol = 100.0

	# Act
	_am.set_bus_volume("SFX", high_vol)
	var vol = _am.get_bus_volume("SFX")

	# Assert
	assert_eq(vol, 1.0, "Bus volume above 1.0 must be clamped to 1.0")

func test_am_stress_bus_volume_extreme_lower():
	# Arrange
	var low_vol = -50.0

	# Act
	_am.set_bus_volume("SFX", low_vol)
	var vol = _am.get_bus_volume("SFX")

	# Assert
	assert_eq(vol, 0.0, "Bus volume below 0.0 must be clamped to 0.0")

func test_am_stress_bus_volume_zero_db_conversion():
	# Arrange
	var zero_vol = 0.0

	# Act
	_am.set_bus_volume("SFX", zero_vol)
	var vol = _am.get_bus_volume("SFX")
	var idx = AudioServer.get_bus_index("SFX")
	var db = AudioServer.get_bus_volume_db(idx) if idx != -1 else -80.0

	# Assert
	assert_eq(vol, 0.0)
	if idx != -1:
		assert_lte(db, -79.0, "Volume 0.0 should map to <= -79 dB (near silent), preventing -inf crash")

func test_am_stress_bus_volume_nonexistent_bus():
	# Arrange
	var fake_bus = "HyperDrive_Bus_99"

	# Act
	_am.set_bus_volume(fake_bus, 0.5)
	var vol = _am.get_bus_volume(fake_bus)

	# Assert
	assert_eq(vol, 0.5, "Non-existent bus volume stored in cache safely")

func test_am_stress_sfx_volume_scale_bounds():
	# Arrange
	var high_scale = 50.0
	var neg_scale = -10.0
	var zero_scale = 0.0

	# Act
	var p_high = _am.play_sfx("attack", high_scale)
	var p_high_vol = p_high.volume_db if p_high != null else -999.0

	var p_neg = _am.play_sfx("attack", neg_scale)
	var p_neg_vol = p_neg.volume_db if p_neg != null else -999.0

	var p_zero = _am.play_sfx("attack", zero_scale)
	var p_zero_vol = p_zero.volume_db if p_zero != null else -999.0

	# Assert
	assert_not_null(p_high)
	assert_between(p_high_vol, -0.1, 0.1, "50.0 volume scale clamped to 1.0 (0 dB)")
	assert_not_null(p_neg)
	assert_lte(p_neg_vol, -79.0, "Negative volume scale clamped to 0.0001 (~ -80 dB)")
	assert_not_null(p_zero)
	assert_lte(p_zero_vol, -79.0, "Zero volume scale clamped to 0.0001 (~ -80 dB)")

func test_am_stress_sfx_pitch_scale_bounds():
	# Arrange
	var high_pitch = 99.0
	var low_pitch = -5.0
	var zero_pitch = 0.0

	# Act
	var p_high = _am.play_sfx("attack", 1.0, high_pitch)
	var p_high_val = p_high.pitch_scale if p_high != null else 0.0

	var p_low = _am.play_sfx("attack", 1.0, low_pitch)
	var p_low_val = p_low.pitch_scale if p_low != null else 0.0

	var p_zero = _am.play_sfx("attack", 1.0, zero_pitch)
	var p_zero_val = p_zero.pitch_scale if p_zero != null else 0.0

	# Assert
	assert_not_null(p_high)
	assert_eq(p_high_val, 2.0, "Pitch above 2.0 must be clamped to 2.0")
	assert_not_null(p_low)
	assert_eq(p_low_val, 0.5, "Pitch below 0.5 must be clamped to 0.5")
	assert_not_null(p_zero)
	assert_eq(p_zero_val, 0.5, "Pitch 0.0 must be clamped to 0.5")

# ==============================================================================
# SECTION 5: Mute Toggle Cycles Stress Tests
# ==============================================================================

func test_am_stress_rapid_mute_toggle_100_cycles():
	# Arrange
	var bus_name = "Master"
	# Act: rapidly toggle mute 100 times
	for i in range(100):
		var state = (i % 2 == 0)
		_am.set_bus_muted(bus_name, state)
		assert_eq(_am.is_bus_muted(bus_name), state, "is_bus_muted must match state on cycle %d" % i)

	# Final check with AudioServer
	_am.set_bus_muted(bus_name, false)
	assert_false(_am.is_bus_muted(bus_name))
	var idx = AudioServer.get_bus_index(bus_name)
	if idx != -1:
		assert_false(AudioServer.is_bus_mute(idx))

func test_am_stress_concurrent_bus_mute_toggle():
	# Arrange
	var buses = ["Master", "BGM", "SFX"]
	# Act: toggle all buses 30 times
	for i in range(30):
		for b in buses:
			_am.set_bus_muted(b, i % 2 == 1)

	# Assert
	for b in buses:
		assert_true(_am.is_bus_muted(b), "All buses should be muted at cycle 29")
		_am.set_bus_muted(b, false) # restore

# ==============================================================================
# SECTION 6: Headless Safety & BGM Stress Tests
# ==============================================================================

func test_am_stress_headless_bgm_rapid_track_swapping():
	# Arrange
	var tracks = ["menu", "battle1", "intro", "menu", "battle1"]
	var recorded_bgms: Array[String] = []
	var recorded_playing: Array[bool] = []

	# Act
	for t in tracks:
		_am.play_bgm(t, 0.0)
		recorded_bgms.append(_am.get_current_bgm())
		recorded_playing.append(_am.is_bgm_playing())

	_am.stop_bgm(0.0)
	var stopped_playing = _am.is_bgm_playing()

	# Assert
	for i in range(tracks.size()):
		assert_eq(recorded_bgms[i], tracks[i], "BGM track should update immediately to %s" % tracks[i])
		assert_true(recorded_playing[i], "BGM should be active for %s" % tracks[i])
	assert_false(stopped_playing, "BGM should stop cleanly")

func test_am_stress_stop_bgm_when_already_stopped():
	# Arrange
	_am.stop_bgm(0.0)
	var initial_playing = _am.is_bgm_playing()

	# Act
	_am.stop_bgm(0.0)
	_am.stop_bgm(0.5)
	var after_repeat_playing = _am.is_bgm_playing()

	# Assert
	assert_false(initial_playing, "BGM initially stopped")
	assert_false(after_repeat_playing, "Repeated stop_bgm is safe no-op")

func test_am_stress_bgm_crossfade_duration_zero_and_negative():
	# Arrange
	var track1 = "menu"
	var track2 = "battle1"

	# Act
	_am.play_bgm(track1, -1.0)
	var playing_after_negative = _am.is_bgm_playing()
	_am.play_bgm(track2, 0.0)
	var playing_after_zero = _am.is_bgm_playing()
	_am.stop_bgm(-0.5)
	var playing_after_stop = _am.is_bgm_playing()

	# Assert
	assert_true(playing_after_negative, "BGM must be playing after negative crossfade")
	assert_true(playing_after_zero, "BGM must be playing after zero crossfade")
	assert_false(playing_after_stop, "BGM must stop cleanly with negative fade duration")
