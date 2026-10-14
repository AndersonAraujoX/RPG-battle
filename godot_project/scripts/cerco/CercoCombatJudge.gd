# res://scripts/cerco/CercoCombatJudge.gd
class_name CercoCombatJudge
extends RefCounted

## CercoCombatJudge: Rule engine and combat arbiter for Cerco da Fortaleza contra Isectum.
## Implements custom D6 dice rolls, Melee resolution (2 impactos = 1 dano),
## Tower Balestra Ranged resolution (1 disparo = 1 dano), elevation modifiers,
## Brutamontes 3-circle HP tracking, Infiltrador stealth bypass, and Catapult siege damage.

# ── Signals ──────────────────────────────────────────────────────────────────
signal dice_rolled(rolls: Array, total_impacts: int, total_shots: int, total_crits: int)
signal melee_attack_resolved(result: Dictionary)
signal ranged_attack_resolved(result: Dictionary)
signal catapult_fired(wall_id: String, damage: int, is_breached: bool)

# ── Enum: Custom D6 Faces ───────────────────────────────────────────────────
enum D6Face {
	IMPACTO,   # Physical impact for melee combat
	DISPARO,   # Crossbow/Balestra shot for tower ranged combat
	CRITICO,   # Critical hit: counts as 2 Impacts or 2 Shots
	ESQUIVA,   # Dodge / defensive maneuver
	NULO       # Blank face / miss
}

# ── Constants ────────────────────────────────────────────────────────────────
const BRUTAMONTES_MAX_CIRCLES: int = 3

const INTERNAL_ZONES: Array[String] = [
	FortressBoard.ZONE_CAMARA_CENTRAL,
	FortressBoard.ZONE_CARPINTARIA,
	FortressBoard.ZONE_CURTUME,
	FortressBoard.ZONE_FUNDICAO,
	FortressBoard.ZONE_PATIO_CENTRAL
]

# ── Dice Roll Generator ──────────────────────────────────────────────────────
## Rolls N custom Cerco D6 dice with advantage/disadvantage modifier support.
## Supports deterministic roll injection via optional forced_rolls for unit testing.
func roll_cerco_dice(
	num_dice: int,
	has_advantage: bool = false,
	has_disadvantage: bool = false,
	forced_rolls: Array = []
) -> Array[D6Face]:
	var results: Array[D6Face] = []

	# 1. Deterministic Injection (Unit Test Hook)
	if not forced_rolls.is_empty():
		for item in forced_rolls:
			results.append(_normalize_d6_face(item))
		return results

	# 2. Advantage / Disadvantage resolution
	var effective_dice: int = num_dice
	if has_advantage and not has_disadvantage:
		effective_dice += 1
	elif has_disadvantage and not has_advantage:
		effective_dice = maxi(1, effective_dice - 1)

	# 3. Standard Random Rolls
	for i in range(effective_dice):
		var face_val: int = randi_range(1, 6)
		match face_val:
			1, 2:
				results.append(D6Face.IMPACTO)
			3:
				results.append(D6Face.DISPARO)
			4:
				results.append(D6Face.CRITICO)
			5:
				results.append(D6Face.ESQUIVA)
			_:
				results.append(D6Face.NULO)

	var impacts: int = count_face(results, D6Face.IMPACTO)
	var shots: int = count_face(results, D6Face.DISPARO)
	var crits: int = count_face(results, D6Face.CRITICO)
	dice_rolled.emit(results, impacts, shots, crits)

	return results

func _normalize_d6_face(item: Variant) -> D6Face:
	if item is D6Face:
		return item
	elif item is int:
		# If passed as 0..4 (enum integer value)
		if item >= 0 and item <= 4:
			return item as D6Face
		# If passed as 1..6 (d6 face pip numbers)
		match item:
			1, 2:
				return D6Face.IMPACTO
			3:
				return D6Face.DISPARO
			4:
				return D6Face.CRITICO
			5:
				return D6Face.ESQUIVA
			_:
				return D6Face.NULO
	return D6Face.NULO

func count_face(rolls: Array[D6Face], face: D6Face) -> int:
	var count: int = 0
	for r in rolls:
		if r == face:
			count += 1
	return count

# ── Melee Resolution ─────────────────────────────────────────────────────────
## Melee resolution: 2 impactos = 1 damage ((impacts + 2*crits) / 2). Odd impacts round down.
## Defender armor deducts directly from raw damage.
## Flanking rule: >= 2 allies in zone grants +1 D6.
func resolve_melee_attack(
	attacker_id: String,
	defender_id: String,
	num_dice: int = 2,
	forced_rolls: Array = [],
	defender_armor: int = 0,
	num_allies_in_zone: int = 1
) -> Dictionary:
	var effective_dice: int = num_dice
	var had_flanking: bool = num_allies_in_zone >= 2
	if had_flanking and forced_rolls.is_empty():
		effective_dice += 1

	var rolls: Array[D6Face] = roll_cerco_dice(effective_dice, false, false, forced_rolls)

	var impacts: int = count_face(rolls, D6Face.IMPACTO)
	var crits: int = count_face(rolls, D6Face.CRITICO)
	var effective_impacts: int = impacts + (2 * crits)
	var raw_damage: int = floori(float(effective_impacts) / 2.0) # Integer division: odd impacts round down
	var final_damage: int = maxi(0, raw_damage - defender_armor)

	var result: Dictionary = {
		"attacker_id": attacker_id,
		"defender_id": defender_id,
		"rolls": rolls,
		"impacts": impacts,
		"crits": crits,
		"effective_impacts": effective_impacts,
		"raw_damage": raw_damage,
		"defender_armor": defender_armor,
		"final_damage": final_damage,
		"had_flanking": had_flanking,
		"is_hit": final_damage > 0
	}

	melee_attack_resolved.emit(result)
	return result

# ── Tower Ranged (Balestra) Resolution ───────────────────────────────────────
## Tower Ranged resolution: 1 disparo de balestra = 1 damage (shots + 2*crits).
## Elevation modifiers: Tower down to Ground/Wall gains advantage (+1 die);
## Ground up to Tower suffers disadvantage (-1 die).
## Valid targets: Walls, Spawns, siege engines. Internal workshops/camara are blocked.
func resolve_tower_ranged_attack(
	attacker_zone: String,
	target_zone: String,
	num_dice: int = 2,
	forced_rolls: Array = [],
	board: FortressBoard = null,
	target_armor: int = 0
) -> Dictionary:
	var is_valid_target: bool = is_valid_ranged_target(attacker_zone, target_zone)
	if not is_valid_target:
		return {
			"valid": false,
			"error": "Invalid target: cannot shoot into internal zones or invalid position.",
			"final_damage": 0,
			"raw_damage": 0,
			"rolls": []
		}

	var has_advantage: bool = false
	var has_disadvantage: bool = false

	if board != null:
		var elev_att: int = board.get_elevation(attacker_zone)
		var elev_tgt: int = board.get_elevation(target_zone)
		if elev_att > elev_tgt:
			has_advantage = true
		elif elev_att < elev_tgt:
			has_disadvantage = true

	var rolls: Array[D6Face] = roll_cerco_dice(num_dice, has_advantage, has_disadvantage, forced_rolls)

	var shots: int = count_face(rolls, D6Face.DISPARO)
	var crits: int = count_face(rolls, D6Face.CRITICO)
	var effective_shots: int = shots + (2 * crits)
	var raw_damage: int = effective_shots
	var final_damage: int = maxi(0, raw_damage - target_armor)

	var result: Dictionary = {
		"valid": true,
		"attacker_zone": attacker_zone,
		"target_zone": target_zone,
		"rolls": rolls,
		"shots": shots,
		"crits": crits,
		"effective_shots": effective_shots,
		"raw_damage": raw_damage,
		"target_armor": target_armor,
		"final_damage": final_damage,
		"has_advantage": has_advantage,
		"has_disadvantage": has_disadvantage,
		"is_hit": final_damage > 0
	}

	ranged_attack_resolved.emit(result)
	return result

func is_valid_ranged_target(attacker_zone: String, target_zone: String) -> bool:
	var att_norm: String = attacker_zone.to_upper()
	var tgt_norm: String = target_zone.to_upper()

	# Crossbow shots must originate from a Watch Tower
	if not (att_norm in FortressBoard.ALL_TOWERS):
		return false

	# Cannot shoot into internal fortress zones
	if tgt_norm in INTERNAL_ZONES:
		return false

	# Valid targets: Walls, Spawns, or external siege entities
	var is_wall_or_spawn: bool = (tgt_norm in FortressBoard.ALL_WALLS) or (tgt_norm in FortressBoard.ALL_SPAWNS)
	var is_siege_engine: bool = tgt_norm == "CATAPULTA" or tgt_norm == "TORRE_ASSALTO"

	return is_wall_or_spawn or is_siege_engine

# ── Brutamontes HP Rules ────────────────────────────────────────────────────
## Brutamontes rules: 3 circles of HP. Each successful damage application ticks off 1 circle.
func create_brutamontes_data() -> Dictionary:
	return {
		"circles_total": BRUTAMONTES_MAX_CIRCLES,
		"circles_marked": 0,
		"is_defeated": false
	}

func resolve_brutamontes_hit(brutamontes_data: Dictionary, damage_amount: int) -> Dictionary:
	var total: int = brutamontes_data.get("circles_total", BRUTAMONTES_MAX_CIRCLES)
	var marked: int = brutamontes_data.get("circles_marked", 0)

	if damage_amount > 0 and marked < total:
		marked += 1

	var is_defeated: bool = marked >= total
	var remaining: int = maxi(0, total - marked)

	brutamontes_data["circles_marked"] = marked
	brutamontes_data["is_defeated"] = is_defeated
	brutamontes_data["circles_remaining"] = remaining

	return {
		"circles_total": total,
		"circles_marked": marked,
		"circles_remaining": remaining,
		"is_defeated": is_defeated
	}

# ── Infiltradores Rules ──────────────────────────────────────────────────────
## Infiltradores: bypasses unbreached walls if no defenders are stationed on the wall.
## If defenders are present (defenders_count > 0), the infiltrator is blocked.
## If the wall is already breached, passage is free regardless of defenders.
func can_infiltrator_bypass_wall(_wall_id: String, defenders_count: int, is_wall_breached: bool) -> bool:
	if is_wall_breached:
		return true
	return defenders_count == 0

func can_infiltrator_pass_wall_on_board(board: FortressBoard, wall_id: String) -> bool:
	if board == null:
		return false
	var is_breached: bool = board.is_wall_breached(wall_id)
	var defenders: int = board.get_units_in_zone(wall_id).size()
	return can_infiltrator_bypass_wall(wall_id, defenders, is_breached)

# ── Catapulta Siege Resolution ───────────────────────────────────────────────
## Catapulta: deals direct siege damage to wall HP.
func resolve_catapult_siege_damage(board: FortressBoard, wall_id: String, damage: int) -> Dictionary:
	if board == null:
		return {"error": "Null board"}

	var remaining_hp: int = board.damage_wall(wall_id, damage)
	var is_breached: bool = board.is_wall_breached(wall_id)

	catapult_fired.emit(wall_id, damage, is_breached)

	return {
		"wall_id": wall_id,
		"damage_dealt": damage,
		"remaining_hp": remaining_hp,
		"is_breached": is_breached
	}

# ── Static Helper Math ───────────────────────────────────────────────────────
static func calculate_melee_damage(impacts: int, crits: int = 0, armor: int = 0) -> int:
	var total_impacts: int = impacts + (2 * crits)
	var raw: int = floori(float(total_impacts) / 2.0)
	return maxi(0, raw - armor)

static func calculate_ranged_damage(shots: int, crits: int = 0, armor: int = 0) -> int:
	var total_shots: int = shots + (2 * crits)
	return maxi(0, total_shots - armor)

static func d6_face_to_string(face: D6Face) -> String:
	match face:
		D6Face.IMPACTO:
			return "IMPACTO"
		D6Face.DISPARO:
			return "DISPARO"
		D6Face.CRITICO:
			return "CRITICO"
		D6Face.ESQUIVA:
			return "ESQUIVA"
		D6Face.NULO:
			return "NULO"
	return "UNKNOWN"
