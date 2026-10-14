# res://test/unit/test_combat_rules.gd
extends GutTest

func before_each() -> void:
	pass

func after_each() -> void:
	pass

# ── 1. Ability Modifiers ─────────────────────────────────────────────────────

func test_modifier_baseline_ten_and_eleven() -> void:
	# Arrange & Act & Assert
	assert_eq(CombatRules.calculate_modifier(10), 0, "Stat 10 modifier must be 0")
	assert_eq(CombatRules.calculate_modifier(11), 0, "Stat 11 modifier must be 0")

func test_modifier_even_positive_values() -> void:
	# Arrange & Act & Assert
	assert_eq(CombatRules.calculate_modifier(12), 1, "Stat 12 modifier must be +1")
	assert_eq(CombatRules.calculate_modifier(14), 2, "Stat 14 modifier must be +2")
	assert_eq(CombatRules.calculate_modifier(16), 3, "Stat 16 modifier must be +3")
	assert_eq(CombatRules.calculate_modifier(18), 4, "Stat 18 modifier must be +4")
	assert_eq(CombatRules.calculate_modifier(20), 5, "Stat 20 modifier must be +5")

func test_modifier_negative_odd_precision() -> void:
	# Arrange & Act & Assert
	# Strict verification of floor division for negative odd numbers
	assert_eq(CombatRules.calculate_modifier(9), -1, "Stat 9 modifier must be -1 (not 0)")
	assert_eq(CombatRules.calculate_modifier(8), -1, "Stat 8 modifier must be -1")
	assert_eq(CombatRules.calculate_modifier(7), -2, "Stat 7 modifier must be -2")
	assert_eq(CombatRules.calculate_modifier(1), -5, "Stat 1 modifier must be -5")

func test_modifier_extreme_values() -> void:
	# Arrange & Act & Assert
	assert_eq(CombatRules.calculate_modifier(30), 10, "Stat 30 (Godly) modifier must be +10")
	assert_eq(CombatRules.calculate_modifier(0), -5, "Stat 0 modifier must be -5")
	assert_eq(CombatRules.calculate_modifier(-10), -10, "Stat -10 modifier must be -10")

# ── 2. Proficiency Bonus ─────────────────────────────────────────────────────

func test_proficiency_levels_1_to_20() -> void:
	# Arrange & Act & Assert
	for lvl in range(1, 5):
		assert_eq(CombatRules.calculate_proficiency(lvl), 2, "Levels 1-4 prof bonus must be +2")
	for lvl in range(5, 9):
		assert_eq(CombatRules.calculate_proficiency(lvl), 3, "Levels 5-8 prof bonus must be +3")
	for lvl in range(9, 13):
		assert_eq(CombatRules.calculate_proficiency(lvl), 4, "Levels 9-12 prof bonus must be +4")
	for lvl in range(13, 17):
		assert_eq(CombatRules.calculate_proficiency(lvl), 5, "Levels 13-16 prof bonus must be +5")
	for lvl in range(17, 21):
		assert_eq(CombatRules.calculate_proficiency(lvl), 6, "Levels 17-20 prof bonus must be +6")

func test_proficiency_boundary_zero_and_negative() -> void:
	# Arrange & Act & Assert
	assert_eq(CombatRules.calculate_proficiency(0), 2, "Level 0 defaults safely to +2")
	assert_eq(CombatRules.calculate_proficiency(-5), 2, "Negative level defaults safely to +2")

# ── 3. Advantage / Disadvantage & Cancellation ───────────────────────────────

func test_roll_d20_advantage_picks_higher() -> void:
	# Arrange
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 12345
	
	# Act
	var result: Dictionary = CombatRules.roll_d20(true, false, rng)
	
	# Assert
	assert_eq(result["dice"].size(), 2, "Advantage rolls two dice")
	assert_eq(result["final_roll"], maxi(result["dice"][0], result["dice"][1]), "Advantage picks the maximum die")
	assert_false(result["cancelled"], "Cancelled should be false")

func test_roll_d20_disadvantage_picks_lower() -> void:
	# Arrange
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 54321
	
	# Act
	var result: Dictionary = CombatRules.roll_d20(false, true, rng)
	
	# Assert
	assert_eq(result["dice"].size(), 2, "Disadvantage rolls two dice")
	assert_eq(result["final_roll"], mini(result["dice"][0], result["dice"][1]), "Disadvantage picks the minimum die")
	assert_false(result["cancelled"], "Cancelled should be false")

func test_roll_d20_mutual_cancellation() -> void:
	# Arrange
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 99999
	
	# Act
	# When both advantage and disadvantage are true, they cancel out completely
	var result: Dictionary = CombatRules.roll_d20(true, true, rng)
	
	# Assert
	assert_true(result["cancelled"], "Advantage and Disadvantage mutually cancel out")
	assert_eq(result["final_roll"], result["dice"][0], "Cancelled roll uses standard first die")

# ── 4. Attack Rolls & AC Resolution ──────────────────────────────────────────

func test_attack_roll_meets_ac_hits() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 14 # Mod +2
	attacker.nivel = 1  # Prof +2 -> Attack mod = +4
	attacker.stats["forca"] = 14
	var target: CharacterData = CharacterData.new()
	target.ac = 14
	
	# Act
	# Force d20 roll = 10 -> Total attack = 10 + 4 = 14 (Meets AC 14)
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 0, null, 10)
	
	# Assert
	assert_true(result.hit, "Attack meeting target AC must hit (Tie goes to attacker)")
	assert_eq(result.total_attack, 14, "Total attack calculation 10 + 4 = 14")
	assert_not_null(result.damage_result, "DamageResult generated on hit")

func test_attack_roll_below_ac_misses() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 10 # Mod 0
	attacker.nivel = 1  # Prof +2 -> Attack mod = +2
	attacker.stats["forca"] = 10
	var target: CharacterData = CharacterData.new()
	target.ac = 15
	
	# Act
	# Force d20 roll = 10 -> Total attack = 10 + 2 = 12 < 15
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 0, null, 10)
	
	# Assert
	assert_false(result.hit, "Attack below target AC must miss")
	assert_null(result.damage_result, "No damage result on miss")

func test_attack_roll_soft_cover_bonus_turns_hit_to_miss() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 10
	attacker.nivel = 1
	attacker.stats["forca"] = 10 # mod 0 + prof 2 = +2
	var target: CharacterData = CharacterData.new()
	target.ac = 12
	
	# Act
	# Roll 10 -> Total 12 vs AC 12 (+2 soft cover = 14)
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 2, null, 10)
	
	# Assert
	assert_false(result.hit, "Target with +2 soft cover raises effective AC to 14, causing miss")
	assert_eq(result.target_ac, 14, "Target AC augmented by cover bonus")

func test_attack_roll_total_cover_blocked() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	var target: CharacterData = CharacterData.new()
	target.ac = 10
	
	# Act
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 1000, null, 20)
	
	# Assert
	assert_false(result.hit, "Total cover (+1000) completely blocks attack even with Nat 20")

# ── 5. Critical Hits and Misses ──────────────────────────────────────────────

func test_critical_hit_nat_20_always_hits() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 10
	attacker.stats["forca"] = 10
	var target: CharacterData = CharacterData.new()
	target.ac = 40 # Impossible AC
	
	# Act
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 0, null, 20)
	
	# Assert
	assert_true(result.hit, "Natural 20 automatically hits regardless of astronomical AC")
	assert_true(result.is_critical, "Natural 20 is a Critical Hit")

func test_critical_miss_nat_1_always_misses() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 30 # Huge +10 mod
	attacker.nivel = 20 # +6 prof -> +16 total
	attacker.stats["forca"] = 30
	var target: CharacterData = CharacterData.new()
	target.ac = 5 # Fragile target
	
	# Act
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 0, null, 1)
	
	# Assert
	assert_false(result.hit, "Natural 1 automatically misses regardless of huge attack modifier")
	assert_true(result.is_critical_miss, "Natural 1 is flagged as Critical Miss")

func test_melee_attack_on_paralyzed_target_auto_crits() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 14
	attacker.stats["forca"] = 14
	var target: CharacterData = CharacterData.new()
	target.ac = 10
	target.set_meta("paralyzed", true)
	
	# Act
	# Melee hit at distance 1 with normal roll of 12
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 1, false, false, 0, null, 12)
	
	# Assert
	assert_true(result.hit, "Attack hits target")
	assert_true(result.is_critical, "Hit within 1 tile on Paralyzed target triggers Auto-Crit")

func test_ranged_attack_on_paralyzed_target_does_not_auto_crit() -> void:
	# Arrange
	var attacker: CharacterData = CharacterData.new()
	attacker.forca = 14
	attacker.stats["forca"] = 14
	var target: CharacterData = CharacterData.new()
	target.ac = 10
	target.set_meta("paralyzed", true)
	
	# Act
	# Ranged hit at distance 3 with normal roll of 12
	var result: AttackResult = CombatRules.resolve_attack(attacker, target, 3, false, false, 0, null, 12)
	
	# Assert
	assert_true(result.hit, "Attack hits target")
	assert_false(result.is_critical, "Ranged hit (> 1 tile) does NOT trigger auto-crit")

# ── 6. Damage & Resistance Mechanics ─────────────────────────────────────────

func test_critical_hit_doubles_damage_dice() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 50
	
	# Act
	# 1d8 weapon with +3 modifier on Critical Hit
	# When critical: 2d8 is rolled; forced_dice_sum simulates 2 dice rolling 6 each = 12
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 1, 8, 3, "cortante", true, null, 12
	)
	
	# Assert
	assert_true(dmg.is_critical, "Result marked critical")
	assert_eq(dmg.raw_damage, 15, "Raw damage: 12 (dice) + 3 (flat mod) = 15")
	assert_eq(dmg.final_damage, 15, "Final damage is 15")
	assert_eq(target.hp, 35, "Target HP reduced from 50 to 35")

func test_damage_minimum_floor_is_one() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 20
	
	# Act
	# Rolled 1 on die with negative modifier -5: raw_calc = -4 -> floor is 1
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 1, 6, -5, "cortante", false, null, 1
	)
	
	# Assert
	assert_eq(dmg.raw_damage, 1, "Damage floor is guaranteed minimum 1")
	assert_eq(dmg.final_damage, 1, "Final damage applied is 1")
	assert_eq(target.hp, 19, "Target HP drops by 1")

func test_damage_immunity_yields_zero() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 30
	target.imunidades = ["Fogo", "Veneno"]
	
	# Act
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 2, 6, 4, "fogo", false, null, 10
	)
	
	# Assert
	assert_true(dmg.is_immune, "Target identified as immune to fire")
	assert_eq(dmg.final_damage, 0, "Immune target takes 0 final damage")
	assert_eq(target.hp, 30, "Target HP unchanged")

func test_damage_resistance_halves_damage() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 30
	target.resistencias = {"cortante": 0.5}
	
	# Act
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 1, 10, 4, "cortante", false, null, 10 # raw = 14
	)
	
	# Assert
	assert_true(dmg.is_resistant, "Resistance applied")
	assert_eq(dmg.final_damage, 7, "14 damage halved by 0.5x resistance = 7")
	assert_eq(target.hp, 23, "Target HP reduced to 23")

func test_damage_vulnerability_doubles_damage() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 30
	target.vulnerabilidades = {"gelo": 2.0}
	
	# Act
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 1, 8, 2, "gelo", false, null, 8 # raw = 10
	)
	
	# Assert
	assert_true(dmg.is_vulnerable, "Vulnerability applied")
	assert_eq(dmg.final_damage, 20, "10 damage doubled by 2.0x vulnerability = 20")
	assert_eq(target.hp, 10, "Target HP reduced to 10")

func test_canonical_14_damage_types_exist() -> void:
	# Arrange & Act
	var types: Array[String] = CombatRules.DAMAGE_TYPES
	
	# Assert
	assert_eq(types.size(), 14, "Exactly 14 canonical damage types")
	var expected: Array[String] = [
		"cortante", "perfurante", "contundente", "fogo", "gelo",
		"eletrico", "acido", "veneno", "necrotico", "radiante",
		"psiquico", "forca", "trovao", "fisico"
	]
	for t in expected:
		assert_has(types, t, "Expected damage type '%s' present" % t)

# ── 7. Death Saving Throws & 0 HP FSM ────────────────────────────────────────

func test_damage_drops_character_to_unconscious() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 10
	target.max_hp = 10
	
	# Act
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 0, 0, 0, "cortante", false, null, 12
	)
	
	# Assert
	assert_eq(target.hp, 0, "HP clamped at 0")
	assert_true(dmg.caused_unconscious, "Flagged as causing unconsciousness")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_INCONSCIENTE, "State becomes INCONSCIENTE")
	assert_eq(CombatRules.get_death_save_successes(target), 0, "Successes reset to 0")
	assert_eq(CombatRules.get_death_save_failures(target), 0, "Failures reset to 0")

func test_massive_damage_causes_instant_death() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 5
	target.max_hp = 20
	
	# Act
	# 30 damage: reduces HP to 0 with 25 overkill >= max_hp (20)
	var dmg: DamageResult = CombatRules.calculate_and_apply_damage(
		target, 0, 0, 30, "cortante", false, null, 30
	)
	
	# Assert
	assert_true(dmg.caused_death, "Massive damage causes instant death")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_MORTO, "State transitions directly to MORTO")

func test_perk_last_stand_triggers_at_zero_hp() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 10
	target.max_hp = 20
	target.perks = ["ultima_linha"]
	
	# Act
	CombatRules.calculate_and_apply_damage(target, 0, 0, 0, "cortante", false, null, 15)

	
	# Assert
	assert_eq(target.hp, 1, "Last stand restores HP to 1")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_NORMAL, "State remains NORMAL")
	assert_true(target.get_meta("last_stand_used"), "Last stand marked as used")

func test_damage_while_unconscious_adds_death_save_failures() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 0
	CombatRules.set_character_state(target, CombatRules.STATE_INCONSCIENTE)
	CombatRules.set_death_save_failures(target, 0)
	
	# Act & Assert
	# Normal damage adds 1 failure
	var res1: DeathSaveResult = CombatRules.apply_damage_at_zero_hp(target, false)
	assert_eq(res1.failures, 1, "Taking normal damage at 0 HP adds 1 failure")
	assert_eq(res1.new_state, CombatRules.STATE_INCONSCIENTE, "Still unconscious with 1 failure")
	
	# Critical damage adds 2 failures (total 3 -> Death)
	var res2: DeathSaveResult = CombatRules.apply_damage_at_zero_hp(target, true)
	assert_eq(res2.failures, 3, "Taking critical hit adds 2 failures (total 3)")
	assert_eq(res2.new_state, CombatRules.STATE_MORTO, "3 failures results in death")

func test_death_save_nat_20_revives_character_to_one_hp() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 0
	CombatRules.set_character_state(target, CombatRules.STATE_INCONSCIENTE)
	CombatRules.set_death_save_failures(target, 2)
	
	# Act
	var res: DeathSaveResult = CombatRules.roll_death_save(target, 20)
	
	# Assert
	assert_true(res.is_critical_success, "Nat 20 is critical success")
	assert_eq(res.hp_recovered, 1, "Recovers 1 HP")
	assert_eq(target.hp, 1, "Target HP is now 1")
	assert_eq(res.new_state, CombatRules.STATE_NORMAL, "State becomes NORMAL")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_NORMAL, "Character wakes up")
	assert_eq(CombatRules.get_death_save_failures(target), 0, "Failures reset on revive")

func test_death_save_nat_1_adds_two_failures() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 0
	CombatRules.set_character_state(target, CombatRules.STATE_INCONSCIENTE)
	CombatRules.set_death_save_failures(target, 0)
	
	# Act
	var res: DeathSaveResult = CombatRules.roll_death_save(target, 1)
	
	# Assert
	assert_true(res.is_critical_failure, "Nat 1 is critical failure")
	assert_eq(res.failures, 2, "Nat 1 adds 2 failures immediately")
	assert_eq(res.new_state, CombatRules.STATE_INCONSCIENTE, "Still unconscious at 2 failures")

func test_death_save_three_successes_stabilizes() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 0
	CombatRules.set_character_state(target, CombatRules.STATE_INCONSCIENTE)
	CombatRules.set_death_save_successes(target, 2)
	
	# Act
	# Rolling 15 is a standard success (10-19)
	var res: DeathSaveResult = CombatRules.roll_death_save(target, 15)
	
	# Assert
	assert_true(res.is_success, "Roll 15 is success")
	assert_eq(res.new_state, CombatRules.STATE_ESTABILIZADO, "3 successes stabilizes character")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_ESTABILIZADO, "State is ESTABILIZADO")

func test_death_save_three_failures_causes_death() -> void:
	# Arrange
	var target: CharacterData = CharacterData.new()
	target.hp = 0
	CombatRules.set_character_state(target, CombatRules.STATE_INCONSCIENTE)
	CombatRules.set_death_save_failures(target, 2)
	
	# Act
	# Rolling 5 is a standard failure (2-9)
	var res: DeathSaveResult = CombatRules.roll_death_save(target, 5)
	
	# Assert
	assert_false(res.is_success, "Roll 5 is failure")
	assert_eq(res.failures, 3, "Failures reach 3")
	assert_eq(res.new_state, CombatRules.STATE_MORTO, "3 failures causes death")
	assert_eq(CombatRules.get_character_state(target), CombatRules.STATE_MORTO, "State is MORTO")
