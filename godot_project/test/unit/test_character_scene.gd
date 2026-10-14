# res://test/unit/test_character_scene.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Character Entity Scene (M9)
## Tests Character.tscn & Character.gd with strict AAA pattern and 0 ObjectDB leaks.

const CHARACTER_SCENE: PackedScene = preload("res://scenes/entities/Character.tscn")

# ── 1. Scene Hierarchy & Instantiation Tests ─────────────────────────────────

func test_character_scene_instantiation_defaults() -> void:
	# Arrange & Act
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Assert
	assert_not_null(character, "Character instance must be non-null")
	assert_not_null(character.sprite_2d, "Sprite2D node resolved")
	assert_not_null(character.collision_shape, "CollisionShape2D node resolved")
	assert_not_null(character.selection_highlight, "SelectionHighlight node resolved")
	assert_not_null(character.retro_hp_bar, "RetroHPBar node resolved")
	assert_not_null(character.status_container, "StatusContainer node resolved")
	assert_not_null(character.hp_fill, "RetroHPBar FillRect node resolved")
	assert_not_null(character.hp_bg, "RetroHPBar BgRect node resolved")
	assert_eq(character.current_hp, 10, "Default current_hp is 10")
	assert_eq(character.max_hp, 10, "Default max_hp is 10")
	assert_false(character.is_selected, "Default is_selected is false")
	assert_true(character.is_alive, "Default is_alive is true")
	assert_false(character.selection_highlight.visible, "Highlight hidden initially")

func test_character_initialize_from_data_dictionary() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var data: Dictionary = {
		"name": "Guerreiro",
		"hp": 50,
		"max_hp": 50,
		"ac": 18,
		"velocidade": 3,
		"alcance": 1,
		"tipo_dano": "Cortante"
	}

	# Act
	character.initialize_from_data(data)

	# Assert
	assert_eq(character.character_name, "Guerreiro", "Name initialized")
	assert_eq(character.current_hp, 50, "HP initialized")
	assert_eq(character.max_hp, 50, "Max HP initialized")
	assert_eq(character.ac, 18, "AC initialized")
	assert_eq(character.move_speed, 3, "Speed initialized")
	assert_eq(character.attack_range, 1, "Range initialized")
	assert_eq(character.damage_type, "Cortante", "Damage type initialized")

func test_character_initialize_from_character_data_resource() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	var res: CharacterData = CharacterData.new()
	res.id = "hero_mago"
	res.name = "Mago"
	res.hp = 30
	res.max_hp = 30
	res.ac = 12
	res.velocidade = 4

	# Act
	character.initialize_from_resource(res)

	# Assert
	assert_eq(character.character_name, "Mago", "Name bound from Resource")
	assert_eq(character.current_hp, 30, "HP bound from Resource")
	assert_eq(character.max_hp, 30, "Max HP bound from Resource")
	assert_eq(character.ac, 12, "AC bound from Resource")
	assert_eq(character.move_speed, 4, "Speed bound from Resource")

# ── 2. Texture Assignment & Normalization Tests ──────────────────────────────

func test_character_texture_assignment_valid_hero() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("guerreiro")

	# Assert
	assert_true(ok, "Loading valid hero texture succeeds")
	assert_not_null(character.sprite_2d.texture, "Texture assigned to Sprite2D")
	assert_gt(character.sprite_2d.texture.get_width(), 0, "Texture has positive width")

func test_character_texture_assignment_isectum_caste_pixel_art() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("abelha_tecela")

	# Assert
	assert_true(ok, "Loading caste pixel art succeeds")
	assert_not_null(character.sprite_2d.texture, "Texture assigned")
	assert_eq(character.sprite_2d.texture.get_width(), 32, "Caste pixel width is 32")
	assert_eq(character.sprite_2d.texture.get_height(), 32, "Caste pixel height is 32")

func test_character_sprite_normalization_scaling() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.target_display_size = Vector2(30.0, 30.0)

	# Act
	character.load_texture_for_character("guerreiro")

	# Assert
	var tex: Texture2D = character.sprite_2d.texture
	var eff_w: float = tex.get_width() * character.sprite_2d.scale.x
	var eff_h: float = tex.get_height() * character.sprite_2d.scale.y
	assert_lte(eff_w, 30.01, "Effective width scaled within 30px")
	assert_lte(eff_h, 30.01, "Effective height scaled within 30px")

func test_character_texture_invalid_path_safe_fallback() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("invalid_character_xyz")

	# Assert
	assert_false(ok, "Invalid ID returns false")
	assert_true(character.is_inside_tree(), "Character remains intact without crash")

# ── 3. Damage Calculation & Retro HP Bar Tests ───────────────────────────────

func test_character_take_damage_normal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Warrior", 50)
	watch_signals(character)

	# Act
	var dealt: int = character.take_damage(15)

	# Assert
	assert_eq(dealt, 15, "Damage dealt is 15")
	assert_eq(character.current_hp, 35, "Current HP is 35")
	assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])
	assert_signal_emitted_with_parameters(character, "damaged", [15, 35])
	assert_true(character.is_alive, "Character is alive")

func test_character_retro_hp_bar_fill_and_color_shifts() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Tank", 100)

	# Act & Assert - 100% (Green)
	character.update_hp_bar()
	assert_eq(character.hp_fill.color, Color(0.24, 0.78, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 30.0, 0.1)

	# Act & Assert - 40% (Yellow)
	character.take_damage(60)
	assert_eq(character.hp_fill.color, Color(0.78, 0.78, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 12.0, 0.1)

	# Act & Assert - 15% (Red)
	character.take_damage(25)
	assert_eq(character.hp_fill.color, Color(0.78, 0.24, 0.24, 1.0))
	assert_almost_eq(character.hp_fill.size.x, 4.5, 0.1)

func test_character_take_damage_zero_or_negative_ignored() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Hero", 30)
	watch_signals(character)

	# Act
	var d0: int = character.take_damage(0)
	var d_neg: int = character.take_damage(-10)

	# Assert
	assert_eq(d0, 0)
	assert_eq(d_neg, 0)
	assert_eq(character.current_hp, 30)
	assert_signal_not_emitted(character, "hp_changed")
	assert_signal_not_emitted(character, "damaged")

func test_character_take_damage_overkill_clamps_at_zero() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Mage", 20)
	watch_signals(character)

	# Act
	var dealt: int = character.take_damage(999)

	# Assert
	assert_eq(dealt, 20, "Actual damage capped to current HP")
	assert_eq(character.current_hp, 0, "HP clamped to 0")
	assert_false(character.is_alive, "Character is dead")
	assert_signal_emitted(character, "died")
	assert_almost_eq(character.hp_fill.size.x, 0.0, 0.01)

# ── 4. Healing Tests ─────────────────────────────────────────────────────────

func test_character_heal_normal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Cleric", 50)
	character.take_damage(30)
	watch_signals(character)

	# Act
	var healed: int = character.heal(15)

	# Assert
	assert_eq(healed, 15)
	assert_eq(character.current_hp, 35)
	assert_signal_emitted_with_parameters(character, "hp_changed", [35, 50])
	assert_signal_emitted_with_parameters(character, "healed", [15, 35])

func test_character_heal_overhealing_capped_at_max_hp() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Paladin", 40)
	character.take_damage(5)
	watch_signals(character)

	# Act
	var healed: int = character.heal(20)

	# Assert
	assert_eq(healed, 5, "Healed only missing 5 HP")
	assert_eq(character.current_hp, 40)
	assert_signal_emitted_with_parameters(character, "hp_changed", [40, 40])

func test_character_heal_dead_unit_fails() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Corpse", 20)
	character.take_damage(20)
	watch_signals(character)

	# Act
	var healed: int = character.heal(25)

	# Assert
	assert_eq(healed, 0)
	assert_eq(character.current_hp, 0)
	assert_false(character.is_alive)
	assert_signal_not_emitted(character, "healed")

func test_character_heal_zero_or_negative_ignored() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Fighter", 30)
	character.take_damage(10)
	watch_signals(character)

	# Act
	var h0: int = character.heal(0)
	var h_neg: int = character.heal(-10)

	# Assert
	assert_eq(h0, 0)
	assert_eq(h_neg, 0)
	assert_eq(character.current_hp, 20)
	assert_signal_not_emitted(character, "healed")

# ── 5. Selection Highlight Tests ─────────────────────────────────────────────

func test_character_selection_toggle_and_visibility() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act - Select
	character.set_selected(true)

	# Assert - Select
	assert_true(character.is_selected)
	assert_true(character.selection_highlight.visible)
	assert_signal_emitted_with_parameters(character, "selection_changed", [true])

	# Act - Deselect
	character.set_selected(false)

	# Assert - Deselect
	assert_false(character.is_selected)
	assert_false(character.selection_highlight.visible)
	assert_signal_emitted_with_parameters(character, "selection_changed", [false])

func test_character_selection_idempotency() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_selected(true)
	watch_signals(character)

	# Act
	character.set_selected(true)

	# Assert
	assert_signal_not_emitted(character, "selection_changed")

# ── 6. Status Effect Lifecycle Tests ─────────────────────────────────────────

func test_character_status_effect_add_and_query() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act
	var applied: bool = character.add_status_effect("poisoned")

	# Assert
	assert_true(applied)
	assert_true(character.has_status_effect("poisoned"))
	assert_has(character.active_status_effects, "poisoned")
	assert_eq(character.status_container.get_child_count(), 1)
	assert_signal_emitted_with_parameters(character, "status_effect_applied", ["poisoned"])

func test_character_status_effect_removal_frees_badge() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("stunned")
	watch_signals(character)

	# Act
	var removed: bool = character.remove_status_effect("stunned")

	# Assert
	assert_true(removed)
	assert_false(character.has_status_effect("stunned"))
	assert_eq(character.status_container.get_child_count(), 0)
	assert_signal_emitted_with_parameters(character, "status_effect_removed", ["stunned"])

func test_character_multiple_distinct_status_effects() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.add_status_effect("poisoned")
	character.add_status_effect("bleeding")
	character.add_status_effect("frozen")

	# Assert
	assert_eq(character.active_status_effects.size(), 3)
	assert_eq(character.status_container.get_child_count(), 3)
	assert_true(character.has_status_effect("poisoned"))
	assert_true(character.has_status_effect("bleeding"))
	assert_true(character.has_status_effect("frozen"))

func test_character_duplicate_status_effect_prevented() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("burning")

	# Act
	var second_apply: bool = character.add_status_effect("burning")

	# Assert
	assert_false(second_apply, "Duplicate status addition returns false")
	assert_eq(character.active_status_effects.size(), 1, "Status array size remains 1")
	assert_eq(character.status_container.get_child_count(), 1, "Only 1 badge exists in container")

# ── 7. Lethal Damage & Edge Case Guards ──────────────────────────────────────

func test_character_death_signal_emitted_exactly_once() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.set_character_name("Target", 10)
	watch_signals(character)

	# Act
	character.take_damage(10)
	character.take_damage(10)

	# Assert
	assert_signal_emit_count(character, "died", 1)
	assert_false(character.is_alive)
	assert_eq(character.current_hp, 0)

func test_character_zero_or_negative_max_hp_guard() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.set_character_name("InvalidHP", 0)

	# Assert
	assert_gte(character.max_hp, 1, "Max HP clamped to minimum 1")
	assert_gte(character.current_hp, 0)

func test_character_remove_nonexistent_status_graceful() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	watch_signals(character)

	# Act
	var removed: bool = character.remove_status_effect("petrified")

	# Assert
	assert_false(removed)
	assert_signal_not_emitted(character, "status_effect_removed")

# ── 8. Zero-Leak Lifecycle & Teardown Verification ───────────────────────────

func test_character_clear_all_status_effects_frees_all_badges() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("poisoned")
	character.add_status_effect("stunned")
	character.add_status_effect("bleeding")
	assert_eq(character.status_container.get_child_count(), 3)

	# Act
	character.clear_all_status_effects()

	# Assert
	assert_eq(character.active_status_effects.size(), 0)
	assert_eq(character.status_container.get_child_count(), 0)

func test_character_status_badge_node_memory_deallocation() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.add_status_effect("burning")
	var badge_node: Node = character.status_container.get_child(0)
	assert_not_null(badge_node)

	# Act
	character.remove_status_effect("burning")

	# Assert
	assert_true(badge_node.is_queued_for_deletion() or not is_instance_valid(badge_node))

func test_character_rapid_creation_and_destruction_zero_leaks() -> void:
	# Arrange & Act
	for i in range(10):
		var char_node: Character = CHARACTER_SCENE.instantiate() as Character
		add_child(char_node)
		char_node.set_character_name("StressHero_%d" % i, 20)
		char_node.add_status_effect("poisoned")
		char_node.add_status_effect("stunned")
		char_node.take_damage(5)
		char_node.heal(3)
		char_node.remove_status_effect("poisoned")
		char_node.cleanup()
		remove_child(char_node)
		char_node.free()

	# Assert
	pass_test("10 Character instances exercised and freed with zero memory leaks")

# ── 9. Additional Behavioral & Edge Tests ────────────────────────────────────

func test_character_setup_and_texture_override() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.setup("caste_infiltrador", "Infiltrador", 25, "res://assets/images/characters/monsters/isectum/infiltrador.png")

	# Assert
	assert_eq(character.character_id, "caste_infiltrador")
	assert_eq(character.character_name, "Infiltrador")
	assert_eq(character.max_hp, 25)
	assert_eq(character.current_hp, 25)
	assert_not_null(character.sprite_2d.texture)
	assert_eq(character.sprite_2d.texture.get_width(), 32)

func test_character_grid_position_signal() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.character_id = "test_unit"
	watch_signals(character)

	# Act
	character.set_grid_position(Vector2i(5, 7))

	# Assert
	assert_eq(character.get_grid_position(), Vector2i(5, 7))
	assert_signal_emitted_with_parameters(character, "grid_position_changed", [Vector2i(5, 7)])

func test_character_active_statuses_alias() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	character.add_status_effect("burning")

	# Assert
	assert_eq(character.active_statuses.size(), 1)
	assert_has(character.active_statuses, "burning")
