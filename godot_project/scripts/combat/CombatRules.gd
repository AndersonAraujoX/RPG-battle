# res://scripts/combat/CombatRules.gd
class_name CombatRules
extends RefCounted

## Constants: Canonical 14 Damage Types
const DAMAGE_TYPES: Array[String] = [
	"cortante", "perfurante", "contundente", "fogo", "gelo",
	"eletrico", "acido", "veneno", "necrotico", "radiante",
	"psiquico", "forca", "trovao", "fisico"
]

## Constants: Character Combat States
const STATE_NORMAL: String = "NORMAL"
const STATE_INCONSCIENTE: String = "INCONSCIENTE"
const STATE_ESTABILIZADO: String = "ESTABILIZADO"
const STATE_MORTO: String = "MORTO"

## Ability Modifier: floor((stat - 10) / 2)
static func calculate_modifier(stat_value: int) -> int:
	return floori((float(stat_value) - 10.0) / 2.0)

## Proficiency Bonus: 1 + ceil(level / 4)
static func calculate_proficiency(level: int) -> int:
	var safe_level: int = maxi(1, level)
	return 1 + ceili(float(safe_level) / 4.0)

## Roll a single die with optional custom RNG
static func roll_die(faces: int, rng: RandomNumberGenerator = null) -> int:
	if faces <= 1:
		return 1
	if rng != null:
		return rng.randi_range(1, faces)
	return randi_range(1, faces)

## Roll d20 with Advantage / Disadvantage and mutual cancellation
static func roll_d20(has_advantage: bool, has_disadvantage: bool, rng: RandomNumberGenerator = null) -> Dictionary:
	var r1: int = roll_die(20, rng)
	var r2: int = roll_die(20, rng)
	var final_roll: int = r1
	var dice: Array[int] = [r1]

	if has_advantage and has_disadvantage:
		final_roll = r1 # Mutual cancellation to standard roll
	elif has_advantage:
		final_roll = maxi(r1, r2)
		dice = [r1, r2]
	elif has_disadvantage:
		final_roll = mini(r1, r2)
		dice = [r1, r2]

	return {
		"final_roll": final_roll,
		"dice": dice,
		"cancelled": has_advantage and has_disadvantage
	}

## Calculates effective attack modifier based on class archetype or weapon stat
static func get_attack_modifier(attacker: CharacterData, stat_override: String = "") -> int:
	var stat_name: String = stat_override
	if stat_name.is_empty():
		var dex: int = attacker.stats.get("destreza", attacker.destreza)
		var str_val: int = attacker.stats.get("forca", attacker.forca)
		var int_val: int = attacker.stats.get("inteligencia", attacker.inteligencia)
		if dex > str_val and attacker.alcance > 1:
			stat_name = "destreza"
		elif int_val >= 16:
			stat_name = "inteligencia"
		else:
			stat_name = "forca"

	var stat_val: int = attacker.stats.get(stat_name, attacker.forca)
	var mod: int = calculate_modifier(stat_val)
	var prof: int = calculate_proficiency(attacker.nivel)
	return mod + prof

## Character State Helpers
static func get_character_state(character: CharacterData) -> String:
	if "estado" in character and character.get("estado") != null and not str(character.get("estado")).is_empty():
		return str(character.get("estado"))
	if character.has_meta("estado"):
		return character.get_meta("estado")
	return STATE_NORMAL

static func set_character_state(character: CharacterData, new_state: String) -> void:
	if "estado" in character:
		character.set("estado", new_state)
	character.set_meta("estado", new_state)

static func get_death_save_successes(character: CharacterData) -> int:
	if "death_save_successes" in character:
		return character.get("death_save_successes")
	return character.get_meta("death_save_successes", 0)

static func set_death_save_successes(character: CharacterData, val: int) -> void:
	if "death_save_successes" in character:
		character.set("death_save_successes", val)
	character.set_meta("death_save_successes", val)

static func get_death_save_failures(character: CharacterData) -> int:
	if "death_save_failures" in character:
		return character.get("death_save_failures")
	return character.get_meta("death_save_failures", 0)

static func set_death_save_failures(character: CharacterData, val: int) -> void:
	if "death_save_failures" in character:
		character.set("death_save_failures", val)
	character.set_meta("death_save_failures", val)

## Resolves an entire attack sequence
static func resolve_attack(
	attacker: CharacterData,
	target: CharacterData,
	distance: int = 1,
	has_advantage: bool = false,
	has_disadvantage: bool = false,
	cover_ac_bonus: int = 0,
	rng: RandomNumberGenerator = null,
	forced_d20: int = 0
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	result.had_advantage = has_advantage
	result.had_disadvantage = has_disadvantage
	result.cover_ac_bonus = cover_ac_bonus
	result.target_ac = target.ac + cover_ac_bonus

	# Total cover blocks attack completely
	if cover_ac_bonus >= 1000:
		result.hit = false
		result.modifiers_log.append("Cobertura Total (Ataque Bloqueado)")
		return result

	var roll_data: Dictionary
	if forced_d20 > 0:
		roll_data = {"final_roll": forced_d20, "dice": [forced_d20], "cancelled": false}
	else:
		roll_data = roll_d20(has_advantage, has_disadvantage, rng)

	result.d20_roll = roll_data["final_roll"]
	result.dice_rolled = roll_data["dice"]
	result.attack_modifier = get_attack_modifier(attacker)
	result.total_attack = result.d20_roll + result.attack_modifier

	# Critical Hit & Critical Miss evaluation
	if result.d20_roll == 1:
		result.is_critical_miss = true
		result.hit = false
		return result

	if result.d20_roll == 20:
		result.is_critical = true
		result.hit = true
	elif result.total_attack >= result.target_ac:
		result.hit = true
	else:
		result.hit = false

	# Automatic Critical for Paralyzed / Unconscious target within melee distance (<= 1)
	var target_state: String = get_character_state(target)
	var is_incapacitated: bool = (
		target_state == STATE_INCONSCIENTE or
		target.get_meta("paralyzed", false) or
		target.get_meta("is_paralyzed", false)
	)
	if result.hit and is_incapacitated and distance <= 1:
		result.is_critical = true
		result.modifiers_log.append("CRÍTICO AUTOMÁTICO (Incapacitado)")

	# If hit, compute and apply damage
	if result.hit:
		var dmg_type: String = attacker.tipo_dano if not attacker.tipo_dano.is_empty() else "cortante"
		var num_dice: int = attacker.dado_dano[0] if attacker.dado_dano.size() > 0 else 1
		var die_faces: int = attacker.dado_dano[1] if attacker.dado_dano.size() > 1 else 6
		var stat_mod: int = calculate_modifier(attacker.forca)

		result.damage_result = calculate_and_apply_damage(
			target, num_dice, die_faces, stat_mod, dmg_type, result.is_critical, rng
		)

	return result

## Resolves damage roll, resistance/vulnerability multipliers, and applies to CharacterData HP
static func calculate_and_apply_damage(
	target: CharacterData,
	num_dice: int,
	die_faces: int,
	flat_modifier: int,
	damage_type: String,
	is_critical: bool = false,
	rng: RandomNumberGenerator = null,
	forced_dice_sum: int = -1
) -> DamageResult:
	var res: DamageResult = DamageResult.new()
	res.damage_type = damage_type
	res.is_critical = is_critical
	res.modifier_applied = flat_modifier
	res.target_hp_before = target.hp

	var actual_dice_count: int = num_dice * 2 if is_critical else num_dice
	var dice_sum: int = 0

	if forced_dice_sum >= 0:
		dice_sum = forced_dice_sum
		res.dice_rolls = [forced_dice_sum]
	elif actual_dice_count > 0 and die_faces > 0:
		for i in range(actual_dice_count):
			var r: int = roll_die(die_faces, rng)
			res.dice_rolls.append(r)
			dice_sum += r

	res.dice_sum = dice_sum
	var raw_calc: int = dice_sum + flat_modifier
	res.raw_damage = maxi(1, raw_calc)

	# 1. Immunity (0.0x)
	var normalized_type: String = damage_type.to_lower()
	var immune_types: Array = target.imunidades.map(func(s): return str(s).to_lower())
	if normalized_type in immune_types:
		res.is_immune = true
		res.final_damage = 0
		res.target_hp_after = target.hp
		return res

	var dmg_float: float = float(res.raw_damage)

	# 2. Vulnerability (2.0x)
	var vuln_keys: Array = target.vulnerabilidades.keys().map(func(s): return str(s).to_lower())
	if normalized_type in vuln_keys:
		res.is_vulnerable = true
		dmg_float *= 2.0

	# 3. Resistance (0.5x)
	var res_keys: Array = target.resistencias.keys().map(func(s): return str(s).to_lower())
	if normalized_type in res_keys:
		res.is_resistant = true
		dmg_float *= 0.5

	res.final_damage = int(round(dmg_float))

	# Apply damage to target HP
	var overkill: int = res.final_damage - target.hp
	target.hp = maxi(0, target.hp - res.final_damage)
	res.target_hp_after = target.hp

	# Check state transitions (Unconscious / Massive Damage Instant Death / Last Stand)
	if target.hp == 0:
		if overkill >= target.max_hp:
			# Massive damage instant death: damage remainder >= max_hp
			set_character_state(target, STATE_MORTO)
			res.caused_death = true
		else:
			var has_last_stand: bool = "ultima_linha" in target.perks and not target.get_meta("last_stand_used", false)
			if has_last_stand:
				target.hp = 1
				target.set_meta("last_stand_used", true)
				set_character_state(target, STATE_NORMAL)
				res.target_hp_after = 1
			else:
				set_character_state(target, STATE_INCONSCIENTE)
				set_death_save_successes(target, 0)
				set_death_save_failures(target, 0)
				res.caused_unconscious = true

	return res

## Contract alias conforming to PROJECT.md
static func apply_damage(target: CharacterData, amount: int, damage_type: String) -> DamageResult:
	return calculate_and_apply_damage(target, 0, 0, amount, damage_type, false, null, amount)

## Evaluates damage taken while already unconscious (at 0 HP)
static func apply_damage_at_zero_hp(target: CharacterData, is_critical: bool = false) -> DeathSaveResult:
	var res: DeathSaveResult = DeathSaveResult.new()
	res.previous_state = get_character_state(target)
	var fails_to_add: int = 2 if is_critical else 1
	var current_fails: int = get_death_save_failures(target) + fails_to_add
	set_death_save_failures(target, current_fails)

	res.failures = current_fails
	res.successes = get_death_save_successes(target)

	if current_fails >= 3:
		set_character_state(target, STATE_MORTO)
		res.new_state = STATE_MORTO
	else:
		res.new_state = STATE_INCONSCIENTE

	return res

## Rolls Death Saving Throw for unconscious character
static func roll_death_save(
	target: CharacterData,
	forced_roll: int = 0,
	rng: RandomNumberGenerator = null
) -> DeathSaveResult:
	var res: DeathSaveResult = DeathSaveResult.new()
	res.previous_state = get_character_state(target)

	var roll_val: int = forced_roll if forced_roll > 0 else roll_die(20, rng)
	res.roll = roll_val

	var current_successes: int = get_death_save_successes(target)
	var current_failures: int = get_death_save_failures(target)

	if roll_val == 20:
		res.is_critical_success = true
		res.is_success = true
		res.hp_recovered = 1
		target.hp = 1
		set_character_state(target, STATE_NORMAL)
		set_death_save_successes(target, 0)
		set_death_save_failures(target, 0)
		res.successes = 0
		res.failures = 0
		res.new_state = STATE_NORMAL
	elif roll_val == 1:
		res.is_critical_failure = true
		res.is_success = false
		current_failures += 2
		set_death_save_failures(target, current_failures)
		res.failures = current_failures
		res.successes = current_successes
		if current_failures >= 3:
			set_character_state(target, STATE_MORTO)
			res.new_state = STATE_MORTO
		else:
			res.new_state = STATE_INCONSCIENTE
	elif roll_val >= 10:
		res.is_success = true
		current_successes += 1
		set_death_save_successes(target, current_successes)
		res.successes = current_successes
		res.failures = current_failures
		if current_successes >= 3:
			set_character_state(target, STATE_ESTABILIZADO)
			set_death_save_successes(target, 0)
			set_death_save_failures(target, 0)
			res.new_state = STATE_ESTABILIZADO
		else:
			res.new_state = STATE_INCONSCIENTE
	else:
		res.is_success = false
		current_failures += 1
		set_death_save_failures(target, current_failures)
		res.failures = current_failures
		res.successes = current_successes
		if current_failures >= 3:
			set_character_state(target, STATE_MORTO)
			res.new_state = STATE_MORTO
		else:
			res.new_state = STATE_INCONSCIENTE

	# Emit death_save_rolled signal on EventBus
	EventBus.death_save_rolled.emit(target.id, res.roll, res.successes, res.failures, res.new_state)
	return res
