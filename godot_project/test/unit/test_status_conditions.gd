# res://test/unit/test_status_conditions.gd
extends GutTest

var _sm: StatusManager

func before_each() -> void:
	_sm = StatusManager.new()

func after_each() -> void:
	_sm = null

# ── 1. Registry & Registration of All 23 Conditions ─────────────────────────

func test_registration_all_23_conditions() -> void:
	# Arrange
	var expected_conditions: Array[String] = [
		# 14 Canonical D&D 5e
		"paralyzed", "poisoned", "stunned", "blinded", "charmed", "deafened",
		"frightened", "grappled", "incapacitated", "invisible", "petrified",
		"prone", "restrained", "unconscious",
		# 9 Elemental & Fantasy
		"bleeding", "burning", "frozen", "confused", "cursed",
		"blessed", "hasted", "slowed", "doomed"
	]
	
	# Act
	var registered: Array = _sm.get_registered_condition_ids()
	
	# Assert
	assert_gte(registered.size(), 23, "At least 23 conditions must be registered")
	for cond_id in expected_conditions:
		assert_has(registered, cond_id, "Condition '%s' must be registered" % cond_id)
		var def: StatusCondition = _sm.get_condition_definition(cond_id)
		assert_not_null(def, "Condition definition for '%s' must not be null" % cond_id)
		assert_false(def.display_name.is_empty(), "Display name for '%s' must not be empty" % cond_id)

# ── 2. Application & Duration Stacking ───────────────────────────────────────

func test_apply_and_extend_duration() -> void:
	# Arrange
	var character: CharacterData = CharacterData.new()
	character.id = "hero_1"
	
	# Act
	# Apply poisoned for 2 turns
	var applied_1: bool = _sm.apply_condition(character, "poisoned", 2)
	var active_first: Array[StatusCondition] = _sm.get_active_conditions(character)
	
	# Re-apply poisoned for 3 turns (should stack to 5 turns without duplicating)
	var applied_2: bool = _sm.apply_condition(character, "poisoned", 3)
	var active_second: Array[StatusCondition] = _sm.get_active_conditions(character)
	
	# Assert
	assert_true(applied_1, "First application succeeds")
	assert_true(applied_2, "Second application succeeds")
	assert_eq(active_first.size(), 1, "Only 1 condition in array initially")
	assert_eq(active_second.size(), 1, "Duration stacks without creating duplicate entries")
	assert_eq(active_second[0].duration_turns, 5, "Duration should sum to 2 + 3 = 5 turns")

# ── 3. Immunity Handling ─────────────────────────────────────────────────────

func test_immunity_blocks_application() -> void:
	# Arrange
	var lich: CharacterData = CharacterData.new()
	lich.id = "lich_boss"
	lich.imunidades = ["Veneno", "Paralisia"]
	
	# Act
	var apply_poison: bool = _sm.apply_condition(lich, "poisoned", 3)
	var apply_paralyze: bool = _sm.apply_condition(lich, "paralyzed", 2)
	var apply_stun: bool = _sm.apply_condition(lich, "stunned", 1)
	
	# Assert
	assert_false(apply_poison, "Immunity to 'Veneno' blocks 'poisoned'")
	assert_false(apply_paralyze, "Immunity to 'Paralisia' blocks 'paralyzed'")
	assert_true(apply_stun, "Lich is not immune to 'stunned', application succeeds")
	assert_false(_sm.has_condition(lich, "poisoned"), "Lich does not have poisoned")
	assert_false(_sm.has_condition(lich, "paralyzed"), "Lich does not have paralyzed")
	assert_true(_sm.has_condition(lich, "stunned"), "Lich has stunned")

# ── 4. Movement Restrictions & Speed Multipliers ─────────────────────────────

func test_movement_restriction_grappled_restrained_paralyzed() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.velocidade = 6
	
	# Act & Assert
	_sm.apply_condition(hero, "grappled", 2)
	assert_false(_sm.can_character_move(hero), "Grappled blocks movement")
	assert_eq(_sm.get_effective_speed(hero), 0, "Grappled reduces effective speed to 0")
	_sm.remove_condition(hero, "grappled")
	
	_sm.apply_condition(hero, "restrained", 2)
	assert_false(_sm.can_character_move(hero), "Restrained blocks movement")
	assert_eq(_sm.get_effective_speed(hero), 0, "Restrained reduces effective speed to 0")
	_sm.remove_condition(hero, "restrained")
	
	_sm.apply_condition(hero, "paralyzed", 2)
	assert_false(_sm.can_character_move(hero), "Paralyzed blocks movement")
	assert_eq(_sm.get_effective_speed(hero), 0, "Paralyzed reduces effective speed to 0")

func test_movement_hasted_and_slowed() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.velocidade = 4
	
	# Act & Assert: Haste
	_sm.apply_condition(hero, "hasted", 3)
	assert_eq(_sm.get_effective_speed(hero), 8, "Hasted doubles speed (4 * 2 = 8)")
	_sm.remove_condition(hero, "hasted")
	
	# Act & Assert: Slow
	_sm.apply_condition(hero, "slowed", 3)
	assert_eq(_sm.get_effective_speed(hero), 2, "Slowed reduces speed by 2 (4 - 2 = 2)")
	_sm.remove_condition(hero, "slowed")
	
	# Act & Assert: Prone
	_sm.apply_condition(hero, "prone", 1)
	assert_eq(_sm.get_effective_speed(hero), 2, "Prone crawls at half speed (4 * 0.5 = 2)")

# ── 5. Action Blocking ───────────────────────────────────────────────────────

func test_action_blocked_stunned_paralyzed_unconscious() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.hp = 20
	
	# Act & Assert
	assert_true(_sm.can_character_act(hero), "Healthy character can act")
	
	_sm.apply_condition(hero, "stunned", 1)
	assert_false(_sm.can_character_act(hero), "Stunned blocks action")
	_sm.remove_condition(hero, "stunned")
	
	_sm.apply_condition(hero, "paralyzed", 1)
	assert_false(_sm.can_character_act(hero), "Paralyzed blocks action")
	_sm.remove_condition(hero, "paralyzed")
	
	_sm.apply_condition(hero, "unconscious", 1)
	assert_false(_sm.can_character_act(hero), "Unconscious blocks action")
	_sm.remove_condition(hero, "unconscious")
	
	_sm.apply_condition(hero, "incapacitated", 1)
	assert_false(_sm.can_character_act(hero), "Incapacitated blocks action")

# ── 6. Attack Modifiers & Advantage / Disadvantage ───────────────────────────

func test_attack_advantage_blinded_and_invisible() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	var target: CharacterData = CharacterData.new()
	
	# Act: Blinded Attacker
	_sm.apply_condition(attacker, "blinded", 2)
	var mods_blind: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	assert_true(mods_blind["has_disadvantage"], "Blinded attacker suffers disadvantage")
	_sm.remove_condition(attacker, "blinded")
	
	# Act: Invisible Attacker
	_sm.apply_condition(attacker, "invisible", 2)
	var mods_invis: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	assert_true(mods_invis["has_advantage"], "Invisible attacker gains advantage")
	_sm.remove_condition(attacker, "invisible")
	
	# Act: Blinded Target
	_sm.apply_condition(target, "blinded", 2)
	var mods_target_blind: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	assert_true(mods_target_blind["has_advantage"], "Attacking a blinded target grants advantage")

func test_advantage_disadvantage_cancellation() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	var target: CharacterData = CharacterData.new()
	
	# Act: Attacker is Poisoned (Disadvantage) AND Target is Stunned (Advantage)
	_sm.apply_condition(attacker, "poisoned", 2)
	_sm.apply_condition(target, "stunned", 2)
	var mods: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	
	# Assert
	assert_false(mods["has_advantage"], "Advantage canceled by disadvantage")
	assert_false(mods["has_disadvantage"], "Disadvantage canceled by advantage")

func test_prone_melee_vs_ranged_distance_threshold() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	var target: CharacterData = CharacterData.new()
	_sm.apply_condition(target, "prone", 2)
	
	# Act: Melee attack (distance 1.0 <= 1.5m)
	var melee_mods: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	
	# Act: Ranged attack (distance 3.0 > 1.5m)
	var ranged_mods: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 3.0)
	
	# Assert
	assert_true(melee_mods["has_advantage"], "Melee attack against prone target grants advantage")
	assert_true(ranged_mods["has_disadvantage"], "Ranged attack against prone target imposes disadvantage")

func test_auto_crit_paralyzed_and_unconscious_melee_only() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	var target: CharacterData = CharacterData.new()
	_sm.apply_condition(target, "paralyzed", 2)
	
	# Act: Melee attack (1.0m)
	var melee_mods: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 1.0)
	
	# Act: Ranged attack (3.0m)
	var ranged_mods: Dictionary = _sm.evaluate_attack_modifiers(attacker, target, 3.0)
	
	# Assert
	assert_true(melee_mods["is_auto_crit"], "Melee hit on paralyzed target triggers auto-crit")
	assert_false(ranged_mods["is_auto_crit"], "Ranged attack on paralyzed target does NOT auto-crit")

# ── 7. DoT Ticks & Turn Lifecycle ────────────────────────────────────────────

func test_poison_and_bleed_dot_tick_lifecycle() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.id = "victim"
	target.name = "Victim"
	target.max_hp = 40
	target.hp = 40
	
	_sm.apply_condition(target, "poisoned", 3) # 2 fixed damage
	_sm.apply_condition(target, "bleeding", 3) # 5% of 40 = 2 damage
	
	# Act: First turn tick (2 + 2 = 4 damage)
	var tick1: Dictionary = _sm.tick_turn_start(target)
	
	# Assert
	assert_eq(tick1["damage_dealt"], 4, "Poison (2) + Bleed (2) = 4 damage")
	assert_eq(target.hp, 36, "Target HP reduced to 36")
	
	var active: Array[StatusCondition] = _sm.get_active_conditions(target)
	for c in active:
		assert_eq(c.duration_turns, 2, "Duration decremented from 3 to 2")

func test_burning_and_cursed_dot_ticks() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.id = "cursed_foe"
	target.name = "Foe"
	target.max_hp = 30
	target.hp = 30
	
	_sm.apply_condition(target, "cursed", 2)  # 3 flat damage
	_sm.apply_condition(target, "burning", 2) # 1d6 damage (seeded RNG)
	
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 42
	
	# Act
	var tick: Dictionary = _sm.tick_turn_start(target, rng)
	
	# Assert
	assert_gt(tick["damage_dealt"], 3, "Curse (3) + Burning (1-6) > 3 damage")
	assert_lt(target.hp, 30, "Target HP reduced by tick")

func test_duration_decrement_and_removal() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.id = "target_exp"
	target.name = "Target"
	target.max_hp = 20
	target.hp = 20
	
	_sm.apply_condition(target, "poisoned", 1) # 1 turn only
	assert_true(_sm.has_condition(target, "poisoned"), "Condition present before tick")
	
	# Act
	var tick: Dictionary = _sm.tick_turn_start(target)
	
	# Assert
	assert_has(tick["expired_conditions"], "poisoned", "Condition expired during tick")
	assert_false(_sm.has_condition(target, "poisoned"), "Condition removed after 1 turn")

# ── 8. Stat Offsets (AC, Attack, Damage) ─────────────────────────────────────

func test_stat_modifiers_blessed_cursed_slowed_hasted() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.ac = 14
	
	# Act & Assert: Blessed (+2 atk)
	_sm.apply_condition(hero, "blessed", 2)
	assert_eq(_sm.get_effective_attack_bonus(hero), 2, "Blessed grants +2 attack roll bonus")
	_sm.remove_condition(hero, "blessed")
	
	# Act & Assert: Cursed (-2 atk)
	_sm.apply_condition(hero, "cursed", 2)
	assert_eq(_sm.get_effective_attack_bonus(hero), -2, "Cursed imposes -2 attack roll penalty")
	_sm.remove_condition(hero, "cursed")
	
	# Act & Assert: Hasted (+2 AC)
	_sm.apply_condition(hero, "hasted", 2)
	assert_eq(_sm.get_effective_ac_bonus(hero), 2, "Hasted grants +2 AC")
	_sm.remove_condition(hero, "hasted")
	
	# Act & Assert: Slowed (-2 AC)
	_sm.apply_condition(hero, "slowed", 2)
	assert_eq(_sm.get_effective_ac_bonus(hero), -2, "Slowed imposes -2 AC")

# ── 9. EventBus Signal Emissions ─────────────────────────────────────────────

func test_eventbus_signal_emissions() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.id = "hero_eb"
	watch_signals(EventBus)
	
	# Act
	_sm.apply_condition(hero, "frightened", 2)
	_sm.remove_condition(hero, "frightened")
	
	# Assert
	assert_signal_emitted(EventBus, "status_applied", "EventBus.status_applied emitted")
	assert_signal_emitted(EventBus, "status_removed", "EventBus.status_removed emitted")

# ── 10. Clear All Conditions ─────────────────────────────────────────────────

func test_clear_all_conditions() -> void:
	# Arrange
	var hero: CharacterData = CharacterData.new()
	hero.id = "hero_clean"
	_sm.apply_condition(hero, "poisoned", 3)
	_sm.apply_condition(hero, "blinded", 2)
	_sm.apply_condition(hero, "paralyzed", 1)
	assert_eq(_sm.get_active_conditions(hero).size(), 3, "3 conditions active")
	
	# Act
	_sm.clear_all_conditions(hero)
	
	# Assert
	assert_eq(_sm.get_active_conditions(hero).size(), 0, "All conditions cleared")
	assert_false(_sm.has_condition(hero, "poisoned"), "Poisoned cleared")
	assert_false(_sm.has_condition(hero, "paralyzed"), "Paralyzed cleared")
