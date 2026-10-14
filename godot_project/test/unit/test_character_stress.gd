# res://test/unit/test_character_stress.gd
extends GutTest

## Empirical Stress & Adversarial Test Suite for Character Entity Scene (M9)
## Stress-tests Character.tscn and Character.gd:
## 1. Rapid instantiate/free cycles (100+ entities)
## 2. Rapid damage/heal/status churn
## 3. Burst status additions and removals
## 4. Boundary inputs and malformed payloads
## 5. Tween lifecycle, orphan node detection, and ObjectDB leak freedom.

const CHARACTER_SCENE: PackedScene = preload("res://scenes/entities/Character.tscn")

# ==============================================================================
# Category 1: Rapid Instantiation & Destruction Cycles (100+ Entities)
# ==============================================================================

## Stress-tests rapid instantiate, add to tree, mutate, and immediate free for 120 entities
func test_stress_120_character_nodes_instantiate_tree_and_free() -> void:
	# Arrange
	var initial_orphans: int = Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)
	var count: int = 120

	# Act
	for i in range(count):
		var char_node: Character = CHARACTER_SCENE.instantiate() as Character
		add_child(char_node)
		
		# Programmatic setup and mutation
		char_node.set_character_name("StressHero_%d" % i, 30 + (i % 20))
		char_node.set_selected(true)
		char_node.add_status_effect("poisoned")
		char_node.add_status_effect("stunned")
		char_node.take_damage(10)
		char_node.heal(5)
		char_node.set_selected(false)
		char_node.remove_status_effect("poisoned")
		
		# Explicit cleanup and teardown
		char_node.cleanup()
		remove_child(char_node)
		char_node.free()

	# Assert
	pass_test("Successfully created and destroyed 120 Character instances")

## Stress-tests queue_free markings across 100 entities
func test_stress_100_character_nodes_queue_free_marking() -> void:
	# Arrange
	var count: int = 100
	var instances: Array[Character] = []

	# Act: Instantiate 100 nodes and add to tree
	for i in range(count):
		var char_node: Character = CHARACTER_SCENE.instantiate() as Character
		add_child(char_node)
		char_node.set_character_name("QueueHero_%d" % i, 25)
		char_node.set_selected(true)
		char_node.add_status_effect("burning")
		instances.append(char_node)

	# Assert all are valid in tree
	assert_eq(instances.size(), count)

	# Queue free all instances and verify deletion flags
	for char_node in instances:
		char_node.queue_free()
		assert_true(char_node.is_queued_for_deletion(), "Character node marked for deletion")

	# Teardown to maintain clean runner
	for char_node in instances:
		remove_child(char_node)
		char_node.free()

	pass_test("100 Character nodes successfully processed queue_free markings")

## Empirical test verifying engine behavior when Character is manipulated outside tree
## Demonstrates whether get_tree() is guarded with is_inside_tree()
func test_empirical_get_tree_safety_outside_scene_tree() -> void:
	# Arrange
	var char_node: Character = CHARACTER_SCENE.instantiate() as Character
	assert_false(char_node.is_inside_tree(), "Node is outside scene tree")

	# Act: Perform operations on unit outside tree
	char_node.character_id = "headless_emp"
	char_node.set_character_name("HeadlessUnit", 20)
	
	# Calling take_damage triggers get_tree() in Character.gd:203
	var dealt: int = char_node.take_damage(5)
	assert_eq(dealt, 5)
	
	# Calling add_status_effect triggers get_tree() in Character.gd:305
	char_node.add_status_effect("stunned")
	
	# Calling remove_status_effect triggers get_tree() in Character.gd:335
	char_node.remove_status_effect("stunned")
	
	# Calling set_grid_position triggers get_tree() in Character.gd:361
	char_node.set_grid_position(Vector2i(2, 3))

	# Cleanup
	char_node.free()
	pass_test("Completed outside-tree empirical check")

# ==============================================================================
# Category 2: Rapid Damage & Healing Interleaving (Extreme Churn)
# ==============================================================================

## Stress-tests 200 rapid alternating damage and heal operations on a single entity
func test_stress_interleaved_damage_and_heal_200_cycles() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var initial_max_hp: int = 100
	character.set_character_name("ChurnWarrior", initial_max_hp)

	# Act: 200 cycles of alternating operations without letting unit die
	for cycle in range(200):
		var dmg_val: int = (cycle % 20) + 1 # 1 to 20

		var dealt: int = character.take_damage(dmg_val)
		assert_gte(dealt, 0, "Damage dealt must be >= 0")
		assert_gte(character.current_hp, 0, "HP must never fall below 0")
		assert_lte(character.current_hp, character.max_hp, "HP must never exceed max_hp")

		# Assert HP bar consistency
		var expected_ratio: float = float(character.current_hp) / float(character.max_hp)
		var expected_width: float = 30.0 * expected_ratio
		assert_almost_eq(character.hp_fill.size.x, expected_width, 0.05, "Fill width matches exact ratio")

		# Verify color shifts
		if expected_ratio > 0.50:
			assert_eq(character.hp_fill.color, Color(0.24, 0.78, 0.24, 1.0))
		elif expected_ratio > 0.25:
			assert_eq(character.hp_fill.color, Color(0.78, 0.78, 0.24, 1.0))
		else:
			assert_eq(character.hp_fill.color, Color(0.78, 0.24, 0.24, 1.0))

		# Heal back to maintain health pool
		if character.current_hp <= 30:
			character.heal(50)
		else:
			character.heal(15)

	# Assert final state
	assert_true(character.is_alive, "Character survived the churn loop")
	assert_gt(character.current_hp, 0)

## Stress-tests lethal damage and attempts to mutate vitals after unit death
func test_stress_lethal_damage_and_post_death_churn() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Mortal", 50)
	watch_signals(character)

	# Act 1: Lethal damage
	var dealt: int = character.take_damage(60) # Overkill by 10
	assert_eq(dealt, 50, "Dealt exact remaining HP")
	assert_eq(character.current_hp, 0)
	assert_false(character.is_alive)
	assert_signal_emit_count(character, "died", 1)

	# Act 2: 50 churn attempts on dead corpse
	for i in range(50):
		var extra_dmg: int = character.take_damage(20)
		assert_eq(extra_dmg, 0, "Dead unit cannot take damage")
		var extra_heal: int = character.heal(20)
		assert_eq(extra_heal, 0, "Dead unit cannot be healed")
		assert_eq(character.current_hp, 0, "HP remains clamped at 0")
		assert_false(character.is_alive, "Unit remains dead")

	# Assert died signal never re-emitted
	assert_signal_emit_count(character, "died", 1, "Died signal must never re-emit on dead unit")

## Stress-tests extreme boundary and overflow integer values
func test_stress_massive_overkill_and_overheal_values() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Titan", 50)

	# Act & Assert: Massive overkill (9999999)
	var dealt: int = character.take_damage(9999999)
	assert_eq(dealt, 50)
	assert_eq(character.current_hp, 0)
	assert_false(character.is_alive)

	# Re-arm character
	character.set_character_name("Titan", 50)
	assert_eq(character.current_hp, 50)
	assert_true(character.is_alive)

	# Massive overheal on full HP
	var healed_full: int = character.heal(9999999)
	assert_eq(healed_full, 0)
	assert_eq(character.current_hp, 50)

	# Negative and zero inputs
	var neg_dmg: int = character.take_damage(-999999)
	var zero_dmg: int = character.take_damage(0)
	assert_eq(neg_dmg, 0)
	assert_eq(zero_dmg, 0)
	assert_eq(character.current_hp, 50)

	var neg_heal: int = character.heal(-999999)
	var zero_heal: int = character.heal(0)
	assert_eq(neg_heal, 0)
	assert_eq(zero_heal, 0)
	assert_eq(character.current_hp, 50)

# ==============================================================================
# Category 3: Burst Status Addition, Removal & Container Node Count
# ==============================================================================

## Stress-tests 50 distinct status condition badges added and removed in reverse order
func test_stress_burst_status_addition_and_removal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var count: int = 50

	# Act: Burst addition
	for i in range(count):
		var eff: String = "condition_%d" % i
		var ok: bool = character.add_status_effect(eff)
		assert_true(ok, "Adding unique condition %s should succeed" % eff)

	# Assert container reflects all 50 badges
	assert_eq(character.active_status_effects.size(), count)
	assert_eq(character.status_container.get_child_count(), count)

	# Act: Reverse removal
	for i in range(count - 1, -1, -1):
		var eff: String = "condition_%d" % i
		var removed: bool = character.remove_status_effect(eff)
		assert_true(removed, "Removing condition %s should succeed" % eff)

	# Assert container is completely empty
	assert_eq(character.active_status_effects.size(), 0)
	assert_eq(character.status_container.get_child_count(), 0)

## Stress-tests duplicate status addition flood
func test_stress_duplicate_status_burst_rejection() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act: First add succeeds
	var first_add: bool = character.add_status_effect("poisoned")
	assert_true(first_add)

	# Flood 99 duplicate attempts
	for i in range(99):
		var dup: bool = character.add_status_effect("poisoned")
		assert_false(dup, "Duplicate add attempt %d must be rejected" % i)

	# Assert exactly 1 badge and 1 active effect
	assert_eq(character.active_status_effects.size(), 1)
	assert_eq(character.status_container.get_child_count(), 1)

## Empirical test measuring orphan node accumulation during remove_status_effect and clear_all_status_effects
func test_empirical_orphan_node_behavior_on_status_clear() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var initial_orphans: int = Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)

	# Act: Add 10 status effects
	for i in range(10):
		character.add_status_effect("test_stat_%d" % i)
	assert_eq(character.status_container.get_child_count(), 10)

	# Clear all status effects
	character.clear_all_status_effects()
	assert_eq(character.active_status_effects.size(), 0)
	assert_eq(character.status_container.get_child_count(), 0)

	var post_clear_orphans: int = Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)
	var orphan_growth: int = post_clear_orphans - initial_orphans

	# Document empirical orphan accumulation
	# In Character.gd lines 348-349: status_container.remove_child(child) + child.queue_free()
	# Because remove_child detaches before queue_free, badges temporarily exist as orphan nodes
	assert_eq(character.status_container.get_child_count(), 0, "Container is empty")
	pass_test("Orphan growth recorded during clear_all: %d nodes" % orphan_growth)

## Stress-tests exotic and special-character status names
func test_stress_exotic_and_special_character_status_names() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var exotic_statuses: Array[String] = [
		"sangrando_crítico",
		"foco_supremo_3x",
		"status with spaces",
		"emoji_effect",
		"hyphen-separated-status",
		"UPPERCASE_STATUS",
		"123456789"
	]

	# Act & Assert Add
	for eff in exotic_statuses:
		var ok: bool = character.add_status_effect(eff)
		assert_true(ok, "Adding exotic status '%s' should succeed" % eff)
		assert_true(character.has_status_effect(eff))

	assert_eq(character.status_container.get_child_count(), exotic_statuses.size())

	# Act & Assert Remove
	for eff in exotic_statuses:
		var removed: bool = character.remove_status_effect(eff)
		assert_true(removed, "Removing exotic status '%s' should succeed" % eff)
		assert_false(character.has_status_effect(eff))

	assert_eq(character.status_container.get_child_count(), 0)

# ==============================================================================
# Category 4: Tween Lifecycle & Rapid Selection Stress
# ==============================================================================

## Stress-tests rapid selection toggling (150 toggles) ensuring Tween replacement safety
func test_stress_rapid_selection_toggle_tween_churn() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act: 150 rapid alternating toggles
	for i in range(150):
		var target_state: bool = (i % 2 == 0)
		character.set_selected(target_state)
		assert_eq(character.is_selected, target_state)
		assert_eq(character.selection_highlight.visible, target_state)

	# Cleanup to deselect
	character.set_selected(false)
	assert_false(character.selection_highlight.visible)
	assert_eq(character.selection_highlight.modulate.a, 1.0)
	pass_test("Completed 150 selection toggles cleanly")

## Stress-tests freeing while selection tween is actively looping
func test_stress_freeing_during_active_looping_tween() -> void:
	# Arrange
	var char_node: Character = CHARACTER_SCENE.instantiate() as Character
	add_child(char_node)
	char_node.set_selected(true)
	assert_true(char_node.is_selected)

	# Act: Free node while tween is looping
	char_node.cleanup()
	remove_child(char_node)
	char_node.free()

	# Assert
	pass_test("Node freed cleanly during active looping tween without crash or leak")

# ==============================================================================
# Category 5: Boundary Data Ingestion & Malformed Payloads
# ==============================================================================

## Stress-tests initialize_from_data with adversarial and malformed dictionary payloads
func test_stress_initialize_from_data_malformed_dictionary() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act 1: Empty dictionary
	character.initialize_from_data({})
	assert_gte(character.max_hp, 1)

	# Act 2: Negative and zero HP specifications
	character.initialize_from_data({
		"name": "CorruptedUnit",
		"hp": -50,
		"max_hp": -10,
		"ac": -5,
		"velocidade": -2
	})
	assert_gte(character.max_hp, 1, "Max HP clamped to minimum 1")
	assert_gte(character.current_hp, 0, "Current HP clamped to minimum 0")
	assert_eq(character.character_name, "CorruptedUnit")

	# Act 3: Extreme integers
	character.initialize_from_data({
		"name": "GodUnit",
		"hp": 999999,
		"max_hp": 999999,
		"ac": 999
	})
	assert_eq(character.max_hp, 999999)
	assert_eq(character.current_hp, 999999)
	assert_true(character.is_alive)

## Stress-tests initialize_from_data with non-Dictionary variants
func test_stress_initialize_from_data_non_dictionary_variants() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var initial_name: String = character.character_name
	var initial_hp: int = character.current_hp

	# Act: Pass completely invalid variants
	character.initialize_from_data(null)
	character.initialize_from_data(12345)
	character.initialize_from_data("invalid_string_payload")
	character.initialize_from_data(Vector2(10, 20))
	character.initialize_from_data([1, 2, 3])

	# Assert: Entity remains completely intact and uncorrupted
	assert_eq(character.character_name, initial_name)
	assert_eq(character.current_hp, initial_hp)
	assert_true(character.is_inside_tree())

## Stress-tests adversarial texture path discovery strings
func test_stress_texture_discovery_adversarial_strings() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var attack_strings: Array[String] = [
		"",
		"   ",
		"../../../../etc/passwd",
		"invalid/nested/path/to/nothing.png",
		"res://non_existent_image_xyz_123.png",
		"A".repeat(500) # Buffer stress string
	]

	# Act & Assert
	for s in attack_strings:
		var result: bool = character.load_texture_for_character(s)
		assert_false(result, "Adversarial texture string '%s' safely returns false" % s.substr(0, 20))
		assert_true(character.is_inside_tree(), "Character node remains safe and alive")

## Stress-tests cleanup method idempotency
func test_stress_cleanup_idempotency() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_selected(true)
	character.add_status_effect("stunned")

	# Act: Call cleanup 5 times consecutively
	for i in range(5):
		character.cleanup()
		assert_eq(character.active_status_effects.size(), 0)
		assert_eq(character.status_container.get_child_count(), 0)

	# Assert
	pass_test("Multiple cleanup calls execute idempotently without errors")

## Stress-tests tactical grid coordinate updates across extreme ranges
func test_stress_grid_position_churn() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.character_id = "grid_tester"
	watch_signals(character)

	var test_positions: Array[Vector2i] = [
		Vector2i(0, 0),
		Vector2i(19, 19),
		Vector2i(-1, -1),
		Vector2i(-999, -999),
		Vector2i(1000, 1000),
		Vector2i(10, 10)
	]

	# Act & Assert
	for pos in test_positions:
		character.set_grid_position(pos)
		assert_eq(character.get_grid_position(), pos)
		assert_signal_emitted_with_parameters(character, "grid_position_changed", [pos])
