# res://scripts/combat/StatusManager.gd
class_name StatusManager
extends RefCounted

## Centralized Status Effect Processor
## Manages condition registration, application, ticks, queries, and EventBus signals.

var _registry: Dictionary = {}

func _init() -> void:
	_register_all_conditions()

func _register_all_conditions() -> void:
	# ── 14 Canonical D&D 5e Conditions ──────────────────────────────────────
	# 1. Paralyzed
	_register_def("paralyzed", "Paralisado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_crit_range": 1.5, "auto_fail_str_dex_saves": true
	})
	# 2. Poisoned
	_register_def("poisoned", "Envenenado", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "dot_fixed_damage": 2, "dot_damage_type": "veneno"
	})
	# 3. Stunned
	_register_def("stunned", "Atordoado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_fail_str_dex_saves": true
	})
	# 4. Blinded
	_register_def("blinded", "Cego", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "grants_attacker_advantage": true
	})
	# 5. Charmed
	_register_def("charmed", "Encantado", StatusCondition.Category.CANONICAL_5E, {})
	# 6. Deafened
	_register_def("deafened", "Surdo", StatusCondition.Category.CANONICAL_5E, {})
	# 7. Frightened
	_register_def("frightened", "Assustado", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true
	})
	# 8. Grappled
	_register_def("grappled", "Agarrado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_movement": true
	})
	# 9. Incapacitated
	_register_def("incapacitated", "Incapacitado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true
	})
	# 10. Invisible
	_register_def("invisible", "Invisível", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_advantage_on_attack": true, "grants_attacker_disadvantage": true
	})
	# 11. Petrified
	_register_def("petrified", "Petrificado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_fail_str_dex_saves": true, "damage_resistance_modifier": 0.5
	})
	# 12. Prone
	_register_def("prone", "Caído", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "speed_multiplier": 0.5, "save_disadvantage_dex": true
	})
	# 13. Restrained
	_register_def("restrained", "Contido", StatusCondition.Category.CANONICAL_5E, {
		"blocks_movement": true, "inflicts_disadvantage_on_attack": true,
		"grants_attacker_advantage": true, "save_disadvantage_dex": true
	})
	# 14. Unconscious
	_register_def("unconscious", "Inconsciente", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_crit_range": 1.5, "auto_fail_str_dex_saves": true
	})

	# ── 9 Elemental & Fantasy Conditions ────────────────────────────────────
	# 15. Bleeding
	_register_def("bleeding", "Sangrando", StatusCondition.Category.ELEMENTAL, {
		"dot_percent_hp_max": 0.05, "dot_damage_type": "fisico"
	})
	# 16. Burning
	_register_def("burning", "Queimando", StatusCondition.Category.ELEMENTAL, {
		"dot_dice_count": 1, "dot_dice_faces": 6, "dot_fixed_damage": 3, "dot_damage_type": "fogo"
	})
	# 17. Frozen
	_register_def("frozen", "Congelado", StatusCondition.Category.ELEMENTAL, {
		"speed_multiplier": 0.5, "grants_attacker_advantage": true
	})
	# 18. Confused
	_register_def("confused", "Confuso", StatusCondition.Category.ELEMENTAL, {})
	# 19. Cursed
	_register_def("cursed", "Amaldiçoado", StatusCondition.Category.ELEMENTAL, {
		"dot_fixed_damage": 3, "bonus_attack_roll": -2, "dot_damage_type": "necrotico"
	})
	# 20. Blessed
	_register_def("blessed", "Abençoado", StatusCondition.Category.TACTICAL_BUFF, {
		"bonus_attack_roll": 2
	})
	# 21. Hasted
	_register_def("hasted", "Acelerado", StatusCondition.Category.TACTICAL_BUFF, {
		"speed_multiplier": 2.0, "bonus_ac": 2, "save_advantage_dex": true
	})
	# 22. Slowed
	_register_def("slowed", "Lentificado", StatusCondition.Category.TACTICAL_DEBUFF, {
		"speed_bonus": -2, "bonus_ac": -2
	})
	# 23. Doomed
	_register_def("doomed", "Condenado", StatusCondition.Category.TACTICAL_DEBUFF, {
		"extra_data": {"crit_threshold": 19}
	})

	# ── Tactical Buffs & Debuffs ───────────────────────────────────────────
	_register_def("furia", "Fúria", StatusCondition.Category.TACTICAL_BUFF, {
		"bonus_damage": 2, "damage_resistance_modifier": 0.25
	})
	_register_def("provocado", "Provocado", StatusCondition.Category.TACTICAL_DEBUFF, {})
	_register_def("defesa_quebrada", "Defesa Quebrada", StatusCondition.Category.TACTICAL_DEBUFF, {
		"bonus_ac": -3
	})
	_register_def("ataque_reduzido", "Ataque Reduzido", StatusCondition.Category.TACTICAL_DEBUFF, {
		"bonus_attack_roll": -2, "bonus_damage": -2
	})
	_register_def("comando_tatico", "Comando Tático", StatusCondition.Category.TACTICAL_BUFF, {
		"bonus_attack_roll": 2, "bonus_damage": 2
	})
	_register_def("inspirado", "Inspirado", StatusCondition.Category.TACTICAL_BUFF, {
		"speed_bonus": 2
	})
	_register_def("dash", "Disparada", StatusCondition.Category.TACTICAL_BUFF, {
		"speed_multiplier": 2.0
	})
	_register_def("desengajar", "Desengajar", StatusCondition.Category.TACTICAL_BUFF, {})
	_register_def("esquiva", "Esquiva", StatusCondition.Category.TACTICAL_BUFF, {
		"grants_attacker_disadvantage": true, "save_advantage_dex": true
	})
	_register_def("ajuda", "Alvo de Ajuda", StatusCondition.Category.TACTICAL_BUFF, {
		"grants_attacker_advantage": true
	})
	_register_def("fuga", "Fuga Garantida", StatusCondition.Category.TACTICAL_BUFF, {})
	_register_def("escondido", "Escondido", StatusCondition.Category.TACTICAL_BUFF, {
		"inflicts_advantage_on_attack": true
	})
	_register_def("ver_o_invisivel", "Ver o Invisível", StatusCondition.Category.TACTICAL_BUFF, {})

func _register_def(id: String, display_name: String, cat: StatusCondition.Category, props: Dictionary) -> void:
	var cond: StatusCondition = StatusCondition.new()
	cond.id = id
	cond.display_name = display_name
	cond.category = cat
	for k in props:
		cond.set(k, props[k])
	_registry[id] = cond

func get_registered_condition_ids() -> Array:
	return _registry.keys()

func get_condition_definition(id: String) -> StatusCondition:
	return _registry.get(id, null)

## Immunity checking helper
func is_character_immune(character: CharacterData, condition_id: String) -> bool:
	var def: StatusCondition = _registry.get(condition_id, null)
	var disp_name: String = def.display_name.to_lower() if def != null else ""
	var cond_lower: String = condition_id.to_lower()

	# Aliases in Portuguese / English for immunities
	var alias_map: Dictionary = {
		"poisoned": ["veneno", "envenenado", "poison"],
		"paralyzed": ["paralisia", "paralisado", "paralyze", "paralyzed"],
		"stunned": ["atordoado", "atordoamento", "stun", "stunned"],
		"burning": ["fogo", "queimando", "burn", "burning", "fire"],
		"frozen": ["gelo", "congelado", "frio", "freeze", "frozen", "cold"]
	}

	var checked_names: Array[String] = [cond_lower]
	if not disp_name.is_empty():
		checked_names.append(disp_name)
	if alias_map.has(cond_lower):
		for a in alias_map[cond_lower]:
			checked_names.append(str(a).to_lower())

	for im in character.imunidades:
		var im_lower: String = str(im).to_lower()
		if im_lower in checked_names:
			return true

	return false

## Condition Application
func apply_condition(character: CharacterData, condition_id: String, duration: int, extra_data: Dictionary = {}) -> bool:
	if not _registry.has(condition_id):
		push_error("[StatusManager] Unknown condition '%s'" % condition_id)
		return false

	if is_character_immune(character, condition_id):
		return false

	if not character.has_meta("active_conditions"):
		character.set_meta("active_conditions", [])

	var active_list: Array = character.get_meta("active_conditions")
	for cond in active_list:
		if cond.id == condition_id:
			cond.duration_turns += duration
			cond.extra_data.merge(extra_data, true)
			EventBus.status_applied.emit(character.id, condition_id, cond.duration_turns)
			return true

	var new_cond: StatusCondition = _registry[condition_id].duplicate_condition()
	new_cond.duration_turns = duration
	new_cond.extra_data = extra_data.duplicate(true)
	active_list.append(new_cond)
	character.set_meta("active_conditions", active_list)

	# Set helper meta flags for quick queries
	if condition_id == "paralyzed":
		character.set_meta("paralyzed", true)

	EventBus.status_applied.emit(character.id, condition_id, duration)
	return true

func remove_condition(character: CharacterData, condition_id: String) -> bool:
	if not character.has_meta("active_conditions"):
		return false
	var active_list: Array = character.get_meta("active_conditions")
	var removed: bool = false
	for i in range(active_list.size() - 1, -1, -1):
		if active_list[i].id == condition_id:
			active_list.remove_at(i)
			removed = true
			if condition_id == "paralyzed":
				character.set_meta("paralyzed", false)
			EventBus.status_removed.emit(character.id, condition_id)
			break
	character.set_meta("active_conditions", active_list)
	return removed

func has_condition(character: CharacterData, condition_id: String) -> bool:
	if not character.has_meta("active_conditions"):
		return false
	var active_list: Array = character.get_meta("active_conditions")
	for cond in active_list:
		if cond.id == condition_id:
			return true
	return false

func get_active_conditions(character: CharacterData) -> Array[StatusCondition]:
	var result: Array[StatusCondition] = []
	if not character.has_meta("active_conditions"):
		return result
	for c in character.get_meta("active_conditions"):
		if c is StatusCondition:
			result.append(c)
	return result

func clear_all_conditions(character: CharacterData) -> void:
	if not character.has_meta("active_conditions"):
		return
	var active_list: Array = character.get_meta("active_conditions")
	for cond in active_list:
		EventBus.status_removed.emit(character.id, cond.id)
	character.set_meta("active_conditions", [])
	character.set_meta("paralyzed", false)

## Mechanical Query Methods
func can_character_act(character: CharacterData) -> bool:
	if character.hp <= 0:
		return false
	if not character.has_meta("active_conditions"):
		return true
	for cond in character.get_meta("active_conditions"):
		if cond.blocks_action:
			return false
	return true

func can_character_move(character: CharacterData) -> bool:
	if character.hp <= 0:
		return false
	if not character.has_meta("active_conditions"):
		return true
	for cond in character.get_meta("active_conditions"):
		if cond.blocks_movement:
			return false
	return true

func get_effective_speed(character: CharacterData) -> int:
	if not can_character_move(character):
		return 0
	if not character.has_meta("active_conditions"):
		return character.velocidade
	var active_list: Array = character.get_meta("active_conditions")
	var speed: float = float(character.velocidade)
	for cond in active_list:
		speed = (speed + float(cond.speed_bonus)) * cond.speed_multiplier
	return maxi(0, int(round(speed)))

func get_effective_ac_bonus(character: CharacterData) -> int:
	if not character.has_meta("active_conditions"):
		return 0
	var total_ac: int = 0
	for cond in character.get_meta("active_conditions"):
		total_ac += cond.bonus_ac
	return total_ac

func get_effective_attack_bonus(character: CharacterData) -> int:
	if not character.has_meta("active_conditions"):
		return 0
	var total_atk: int = 0
	for cond in character.get_meta("active_conditions"):
		total_atk += cond.bonus_attack_roll
	return total_atk

func get_effective_damage_bonus(character: CharacterData) -> int:
	if not character.has_meta("active_conditions"):
		return 0
	var total_dmg: int = 0
	for cond in character.get_meta("active_conditions"):
		total_dmg += cond.bonus_damage
	return total_dmg

## Evaluates all attack conditions, advantage/disadvantage cancellation, and auto-crit
func evaluate_attack_modifiers(attacker: CharacterData, target: CharacterData, distance: float = 1.0) -> Dictionary:
	var has_adv: bool = false
	var has_disadv: bool = false
	var is_crit: bool = false
	var log_mods: Array[String] = []

	# Attacker checks
	if has_condition(attacker, "blinded"):
		has_disadv = true
		log_mods.append("Cego (Atacante)")
	if has_condition(attacker, "poisoned"):
		has_disadv = true
		log_mods.append("Envenenado")
	if has_condition(attacker, "prone"):
		has_disadv = true
		log_mods.append("Caído (Atacante)")
	if has_condition(attacker, "restrained"):
		has_disadv = true
		log_mods.append("Contido (Atacante)")
	if has_condition(attacker, "frightened"):
		has_disadv = true
		log_mods.append("Assustado")
	if has_condition(attacker, "invisible") or has_condition(attacker, "escondido"):
		has_adv = true
		log_mods.append("Invisível / Escondido (Atacante)")

	# Target checks
	if has_condition(target, "blinded"):
		has_adv = true
		log_mods.append("Cego (Alvo)")
	if has_condition(target, "restrained"):
		has_adv = true
		log_mods.append("Contido (Alvo)")
	if has_condition(target, "paralyzed") or has_condition(target, "stunned") or has_condition(target, "unconscious") or has_condition(target, "petrified"):
		has_adv = true
		log_mods.append("Alvo Incapacitado")
	if has_condition(target, "ajuda"):
		has_adv = true
		log_mods.append("Alvo de Ajuda")

	if has_condition(target, "prone"):
		if distance <= 1.5:
			has_adv = true
			log_mods.append("Alvo Caído (Perto)")
		else:
			has_disadv = true
			log_mods.append("Alvo Caído (Longe)")

	if has_condition(target, "invisible") and not has_condition(attacker, "ver_o_invisivel"):
		has_disadv = true
		log_mods.append("Alvo Invisível")

	if has_condition(target, "esquiva"):
		has_disadv = true
		log_mods.append("Alvo em Esquiva")

	# Auto-Crit check: melee (<= 1.5m) against Paralyzed or Unconscious
	if (has_condition(target, "paralyzed") or has_condition(target, "unconscious")) and distance <= 1.5:
		is_crit = true
		log_mods.append("CRÍTICO AUTOMÁTICO (Incapacitado)")

	var final_adv: bool = has_adv and not has_disadv
	var final_disadv: bool = has_disadv and not has_adv
	if has_adv and has_disadv:
		log_mods.append("Vantagem e Desvantagem canceladas")

	return {
		"has_advantage": final_adv,
		"has_disadvantage": final_disadv,
		"is_auto_crit": is_crit,
		"log_modifiers": log_mods
	}

## Turn Start Tick: processes DoT damage and decrements duration
func tick_turn_start(character: CharacterData, rng: RandomNumberGenerator = null) -> Dictionary:
	var total_damage: int = 0
	var logs: Array[String] = []
	var expired_ids: Array[String] = []

	if not character.has_meta("active_conditions"):
		return {"damage_dealt": 0, "logs": [], "expired_conditions": []}

	var active_list: Array = character.get_meta("active_conditions")
	var to_remove: Array[String] = []

	for cond in active_list:
		var tick_dmg: int = 0

		# 1. Fixed DoT (e.g. Poison: 2, Curse: 3)
		if cond.dot_fixed_damage > 0:
			tick_dmg += cond.dot_fixed_damage

		# 2. Percent HP DoT (e.g. Bleeding: 5% max HP)
		if cond.dot_percent_hp_max > 0.0:
			tick_dmg += maxi(1, int(round(float(character.max_hp) * cond.dot_percent_hp_max)))

		# 3. Dice DoT (e.g. Burning: 1d6)
		if cond.dot_dice_count > 0 and cond.dot_dice_faces > 0:
			var dice_sum: int = 0
			for i in range(cond.dot_dice_count):
				if rng != null:
					dice_sum += rng.randi_range(1, cond.dot_dice_faces)
				else:
					dice_sum += randi_range(1, cond.dot_dice_faces)
			# Burning uses the rolled dice
			tick_dmg = dice_sum

		if tick_dmg > 0:
			character.hp = maxi(0, character.hp - tick_dmg)
			total_damage += tick_dmg
			logs.append("%s sofre %d de dano por %s." % [character.name, tick_dmg, cond.display_name])
			EventBus.unit_damaged.emit(character.id, tick_dmg, character.hp, character.max_hp)

		# Decrement duration
		cond.duration_turns -= 1
		if cond.duration_turns <= 0:
			to_remove.append(cond.id)

	for cond_id in to_remove:
		expired_ids.append(cond_id)
		remove_condition(character, cond_id)

	return {
		"damage_dealt": total_damage,
		"logs": logs,
		"expired_conditions": expired_ids
	}
