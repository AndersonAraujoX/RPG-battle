# res://test/unit/test_cerco_combat_judge.gd
extends GutTest

## Test suite for CercoCombatJudge
## Validates custom D6 faces, deterministic roll injection, melee math (2 impactos = 1 dano),
## tower balestra ranged math (1 disparo = 1 dano), elevation advantage/disadvantage,
## Brutamontes 3-circle HP tracking, Infiltrador stealth bypass, and Catapult siege damage.

# ── 1. Custom D6 Faces & Roll Generator ──────────────────────────────────────

func test_d6_face_enum_values_and_names() -> void:
	# Arrange & Act
	var f_imp: CercoCombatJudge.D6Face = CercoCombatJudge.D6Face.IMPACTO
	var f_dis: CercoCombatJudge.D6Face = CercoCombatJudge.D6Face.DISPARO
	var f_crt: CercoCombatJudge.D6Face = CercoCombatJudge.D6Face.CRITICO
	var f_esq: CercoCombatJudge.D6Face = CercoCombatJudge.D6Face.ESQUIVA
	var f_nul: CercoCombatJudge.D6Face = CercoCombatJudge.D6Face.NULO

	# Assert
	assert_eq(CercoCombatJudge.d6_face_to_string(f_imp), "IMPACTO", "Face string matches IMPACTO")
	assert_eq(CercoCombatJudge.d6_face_to_string(f_dis), "DISPARO", "Face string matches DISPARO")
	assert_eq(CercoCombatJudge.d6_face_to_string(f_crt), "CRITICO", "Face string matches CRITICO")
	assert_eq(CercoCombatJudge.d6_face_to_string(f_esq), "ESQUIVA", "Face string matches ESQUIVA")
	assert_eq(CercoCombatJudge.d6_face_to_string(f_nul), "NULO", "Face string matches NULO")

func test_deterministic_roll_injection_via_forced_rolls() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var forced: Array = [
		CercoCombatJudge.D6Face.IMPACTO,
		CercoCombatJudge.D6Face.DISPARO,
		CercoCombatJudge.D6Face.CRITICO,
		CercoCombatJudge.D6Face.ESQUIVA,
		CercoCombatJudge.D6Face.NULO
	]

	# Act
	var rolls: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(5, false, false, forced)

	# Assert
	assert_eq(rolls.size(), 5, "Returns exactly 5 injected rolls")
	assert_eq(rolls[0], CercoCombatJudge.D6Face.IMPACTO)
	assert_eq(rolls[1], CercoCombatJudge.D6Face.DISPARO)
	assert_eq(rolls[2], CercoCombatJudge.D6Face.CRITICO)
	assert_eq(rolls[3], CercoCombatJudge.D6Face.ESQUIVA)
	assert_eq(rolls[4], CercoCombatJudge.D6Face.NULO)

func test_integer_enum_mapping_in_forced_rolls() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	# 0: Impacto, 1: Disparo, 2: Critico, 3: Esquiva, 4: Nulo
	var enum_ints: Array = [0, 1, 2, 3, 4]

	# Act
	var rolls: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(5, false, false, enum_ints)

	# Assert
	assert_eq(rolls[0], CercoCombatJudge.D6Face.IMPACTO, "Int 0 maps to IMPACTO")
	assert_eq(rolls[1], CercoCombatJudge.D6Face.DISPARO, "Int 1 maps to DISPARO")
	assert_eq(rolls[2], CercoCombatJudge.D6Face.CRITICO, "Int 2 maps to CRITICO")
	assert_eq(rolls[3], CercoCombatJudge.D6Face.ESQUIVA, "Int 3 maps to ESQUIVA")
	assert_eq(rolls[4], CercoCombatJudge.D6Face.NULO, "Int 4 maps to NULO")


func test_advantage_and_disadvantage_modify_dice_count() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act & Assert - Advantage adds +1 die (2 -> 3)
	var r_adv: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(2, true, false)
	assert_eq(r_adv.size(), 3, "Advantage increases 2 dice to 3")

	# Act & Assert - Disadvantage removes 1 die (3 -> 2)
	var r_dis: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(3, false, true)
	assert_eq(r_dis.size(), 2, "Disadvantage decreases 3 dice to 2")

	# Act & Assert - Both cancel out (2 -> 2)
	var r_can: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(2, true, true)
	assert_eq(r_can.size(), 2, "Advantage and Disadvantage cancel out to 2")

	# Act & Assert - Disadvantage minimum is 1 die (1 -> 1)
	var r_min: Array[CercoCombatJudge.D6Face] = judge.roll_cerco_dice(1, false, true)
	assert_eq(r_min.size(), 1, "Disadvantage cannot reduce below 1 die")

# ── 2. Melee Combat Resolution (2 Impactos = 1 Dano) ──────────────────────────

func test_melee_math_two_impacts_equal_one_damage() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var rolls: Array = [CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO]

	# Act
	var res: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 2, rolls, 0)

	# Assert
	assert_eq(res["impacts"], 2, "2 impacts rolled")
	assert_eq(res["raw_damage"], 1, "2 impacts = 1 raw damage")
	assert_eq(res["final_damage"], 1, "1 final damage dealt")
	assert_true(res["is_hit"], "Attack registered as hit")

func test_melee_odd_impacts_round_down() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act & Assert 1: 1 impact -> 0 damage
	var res1: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 1, [CercoCombatJudge.D6Face.IMPACTO], 0)
	assert_eq(res1["impacts"], 1)
	assert_eq(res1["raw_damage"], 0, "1 impact rounds down to 0 damage")
	assert_eq(res1["final_damage"], 0)
	assert_false(res1["is_hit"])

	# Act & Assert 2: 3 impacts -> 1 damage (1 remainder discarded)
	var r3: Array = [CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO]
	var res3: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 3, r3, 0)
	assert_eq(res3["impacts"], 3)
	assert_eq(res3["raw_damage"], 1, "3 impacts = 1 raw damage")
	assert_eq(res3["final_damage"], 1)

	# Act & Assert 3: 5 impacts -> 2 damage
	var r5: Array = [
		CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO,
		CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO,
		CercoCombatJudge.D6Face.IMPACTO
	]
	var res5: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 5, r5, 0)
	assert_eq(res5["impacts"], 5)
	assert_eq(res5["raw_damage"], 2, "5 impacts = 2 raw damage")

func test_melee_crit_counts_as_two_impacts() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act 1: 1 Crit = 2 effective impacts = 1 damage
	var res1: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 1, [CercoCombatJudge.D6Face.CRITICO], 0)
	assert_eq(res1["crits"], 1)
	assert_eq(res1["effective_impacts"], 2, "1 Crit = 2 effective impacts")
	assert_eq(res1["raw_damage"], 1, "2 effective impacts = 1 damage")

	# Act 2: 1 Crit + 2 Impacts = 4 effective impacts = 2 damage
	var r_combo: Array = [
		CercoCombatJudge.D6Face.CRITICO,
		CercoCombatJudge.D6Face.IMPACTO,
		CercoCombatJudge.D6Face.IMPACTO
	]
	var res2: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 3, r_combo, 0)
	assert_eq(res2["effective_impacts"], 4, "1 Crit (2) + 2 Impacts (2) = 4 effective impacts")
	assert_eq(res2["raw_damage"], 2, "4 effective impacts = 2 damage")

	# Act 3: 2 Crits = 4 effective impacts = 2 damage
	var r_cr2: Array = [CercoCombatJudge.D6Face.CRITICO, CercoCombatJudge.D6Face.CRITICO]
	var res3: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 2, r_cr2, 0)
	assert_eq(res3["effective_impacts"], 4)
	assert_eq(res3["raw_damage"], 2)

func test_melee_armor_deducts_from_raw_damage() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	# 4 impacts = 2 raw damage
	var r4: Array = [
		CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO,
		CercoCombatJudge.D6Face.IMPACTO, CercoCombatJudge.D6Face.IMPACTO
	]

	# Act 1: 1 armor -> 2 - 1 = 1 damage
	var res1: Dictionary = judge.resolve_melee_attack("guerreiro", "armored_foe", 4, r4, 1)
	assert_eq(res1["raw_damage"], 2)
	assert_eq(res1["final_damage"], 1, "2 raw damage - 1 armor = 1 final damage")

	# Act 2: 3 armor -> 2 - 3 clamped at 0 damage
	var res2: Dictionary = judge.resolve_melee_attack("guerreiro", "heavy_foe", 4, r4, 3)
	assert_eq(res2["final_damage"], 0, "Damage cannot drop below 0")
	assert_false(res2["is_hit"])

func test_melee_ignores_non_impact_faces() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var non_melee: Array = [
		CercoCombatJudge.D6Face.DISPARO,
		CercoCombatJudge.D6Face.ESQUIVA,
		CercoCombatJudge.D6Face.NULO
	]

	# Act
	var res: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 3, non_melee, 0)

	# Assert
	assert_eq(res["impacts"], 0)
	assert_eq(res["crits"], 0)
	assert_eq(res["raw_damage"], 0, "Disparos and Esquivas grant 0 melee damage")
	assert_eq(res["final_damage"], 0)

func test_melee_flanking_flag_and_bonus() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act
	var res: Dictionary = judge.resolve_melee_attack("guerreiro", "invasor", 2, [], 0, 2)

	# Assert
	assert_true(res["had_flanking"], "Flanking recognized when >= 2 allies in zone")

# ── 3. Tower Ranged (Balestra) Resolution (1 Disparo = 1 Dano) ────────────────

func test_tower_ranged_one_shot_equals_one_damage() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var rolls: Array = [CercoCombatJudge.D6Face.DISPARO, CercoCombatJudge.D6Face.DISPARO]

	# Act
	var res: Dictionary = judge.resolve_tower_ranged_attack(
		FortressBoard.ZONE_TORRE_NOROESTE,
		FortressBoard.ZONE_MURALHA_NORTE,
		2,
		rolls
	)

	# Assert
	assert_true(res["valid"], "Attack is valid")
	assert_eq(res["shots"], 2, "2 shots rolled")
	assert_eq(res["raw_damage"], 2, "2 shots = 2 raw damage")
	assert_eq(res["final_damage"], 2, "2 final damage dealt")
	assert_true(res["is_hit"])

func test_tower_ranged_crit_counts_as_two_shots() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var rolls: Array = [
		CercoCombatJudge.D6Face.CRITICO,
		CercoCombatJudge.D6Face.DISPARO
	]

	# Act
	var res: Dictionary = judge.resolve_tower_ranged_attack(
		FortressBoard.ZONE_TORRE_NORDESTE,
		FortressBoard.ZONE_SPAWN_NORTE,
		2,
		rolls
	)

	# Assert
	assert_eq(res["crits"], 1)
	assert_eq(res["shots"], 1)
	assert_eq(res["effective_shots"], 3, "1 Crit (2) + 1 Shot (1) = 3 effective shots")
	assert_eq(res["raw_damage"], 3, "3 raw damage")
	assert_eq(res["final_damage"], 3)

func test_tower_ranged_elevation_advantage_and_disadvantage() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var board: FortressBoard = FortressBoard.new()

	# Act 1: Tower (elev 2) shooting down to Wall (elev 1)
	var res_down: Dictionary = judge.resolve_tower_ranged_attack(
		FortressBoard.ZONE_TORRE_NOROESTE,
		FortressBoard.ZONE_MURALHA_NORTE,
		2,
		[],
		board
	)
	# Assert 1: Has elevation advantage
	assert_true(res_down["has_advantage"], "Shooting from tower down to wall gives advantage")
	assert_false(res_down["has_disadvantage"])

	# Act 2: Tower (elev 2) shooting down to Spawn (elev 0)
	var res_spawn: Dictionary = judge.resolve_tower_ranged_attack(
		FortressBoard.ZONE_TORRE_NOROESTE,
		FortressBoard.ZONE_SPAWN_NORTE,
		2,
		[],
		board
	)
	assert_true(res_spawn["has_advantage"], "Shooting from tower down to spawn gives advantage")

func test_tower_ranged_target_validation_rules() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act & Assert 1: Valid targets from Watch Tower
	assert_true(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_MURALHA_NORTE))
	assert_true(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NORDESTE, FortressBoard.ZONE_SPAWN_LESTE))
	assert_true(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_SUDOESTE, "CATAPULTA"))

	# Act & Assert 2: Cannot shoot into internal fortress zones
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_CAMARA_CENTRAL))
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_CARPINTARIA))
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_CURTUME))
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_FUNDICAO))
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_TORRE_NOROESTE, FortressBoard.ZONE_PATIO_CENTRAL))

	# Act & Assert 3: Cannot shoot from non-tower zones
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_PATIO_CENTRAL, FortressBoard.ZONE_MURALHA_NORTE))
	assert_false(judge.is_valid_ranged_target(FortressBoard.ZONE_MURALHA_NORTE, FortressBoard.ZONE_SPAWN_NORTE))

	# Act 4: Attempting attack on invalid target returns invalid result
	var inv_res: Dictionary = judge.resolve_tower_ranged_attack(
		FortressBoard.ZONE_TORRE_NOROESTE,
		FortressBoard.ZONE_CAMARA_CENTRAL
	)
	assert_false(inv_res["valid"], "Attack on internal chamber flagged as invalid")
	assert_eq(inv_res["final_damage"], 0)

# ── 4. Brutamontes 3-Circle HP Tracking ───────────────────────────────────────

func test_brutamontes_initial_state() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act
	var brute: Dictionary = judge.create_brutamontes_data()

	# Assert
	assert_eq(brute["circles_total"], 3, "Brutamontes starts with 3 circles total")
	assert_eq(brute["circles_marked"], 0, "0 circles marked initially")
	assert_false(brute["is_defeated"], "Not defeated initially")

func test_brutamontes_damage_progression_across_3_circles() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var brute: Dictionary = judge.create_brutamontes_data()

	# Act 1: First hit with damage
	var h1: Dictionary = judge.resolve_brutamontes_hit(brute, 1)
	assert_eq(h1["circles_marked"], 1, "Hit 1 marks 1st circle")
	assert_eq(h1["circles_remaining"], 2, "2 circles remaining")
	assert_false(h1["is_defeated"], "Not defeated after 1 hit")

	# Act 2: Second hit with damage
	var h2: Dictionary = judge.resolve_brutamontes_hit(brute, 2)
	assert_eq(h2["circles_marked"], 2, "Hit 2 marks 2nd circle")
	assert_eq(h2["circles_remaining"], 1, "1 circle remaining")
	assert_false(h2["is_defeated"], "Not defeated after 2 hits")

	# Act 3: Third hit with damage -> Defeated!
	var h3: Dictionary = judge.resolve_brutamontes_hit(brute, 1)
	assert_eq(h3["circles_marked"], 3, "Hit 3 marks 3rd circle")
	assert_eq(h3["circles_remaining"], 0, "0 circles remaining")
	assert_true(h3["is_defeated"], "Brutamontes defeated upon marking 3rd circle")

func test_brutamontes_zero_damage_does_not_mark_circle() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var brute: Dictionary = judge.create_brutamontes_data()

	# Act
	var res: Dictionary = judge.resolve_brutamontes_hit(brute, 0)

	# Assert
	assert_eq(res["circles_marked"], 0, "0 damage marks 0 circles")
	assert_false(res["is_defeated"])

func test_brutamontes_overkill_damage_clamped_at_total() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var brute: Dictionary = judge.create_brutamontes_data()
	judge.resolve_brutamontes_hit(brute, 1)
	judge.resolve_brutamontes_hit(brute, 1)
	judge.resolve_brutamontes_hit(brute, 1) # Now at 3

	# Act: Extra hit
	var over: Dictionary = judge.resolve_brutamontes_hit(brute, 5)

	# Assert
	assert_eq(over["circles_marked"], 3, "Circles marked cannot exceed total 3")
	assert_true(over["is_defeated"])

# ── 5. Infiltradores Wall Bypass Rules ────────────────────────────────────────

func test_infiltrator_bypasses_unattended_unbreached_wall() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act: Wall unbreached, 0 defenders
	var can_bypass: bool = judge.can_infiltrator_bypass_wall(FortressBoard.ZONE_MURALHA_NORTE, 0, false)

	# Assert
	assert_true(can_bypass, "Infiltrator successfully sneaks through unattended unbreached wall")

func test_infiltrator_blocked_by_defenders_on_unbreached_wall() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act 1: 1 defender
	var blocked_1: bool = judge.can_infiltrator_bypass_wall(FortressBoard.ZONE_MURALHA_NORTE, 1, false)
	# Act 2: 3 defenders
	var blocked_3: bool = judge.can_infiltrator_bypass_wall(FortressBoard.ZONE_MURALHA_NORTE, 3, false)

	# Assert
	assert_false(blocked_1, "Blocked by 1 defender")
	assert_false(blocked_3, "Blocked by 3 defenders")

func test_infiltrator_passes_breached_wall_regardless_of_defenders() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()

	# Act & Assert
	assert_true(judge.can_infiltrator_bypass_wall(FortressBoard.ZONE_MURALHA_NORTE, 0, true), "Free pass on breached wall")
	assert_true(judge.can_infiltrator_bypass_wall(FortressBoard.ZONE_MURALHA_NORTE, 2, true), "Passes breached wall even with defenders")

func test_infiltrator_board_integration() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var board: FortressBoard = FortressBoard.new()
	var wall: String = FortressBoard.ZONE_MURALHA_LESTE

	# Act & Assert 1: Empty unbreached wall -> can pass
	assert_true(judge.can_infiltrator_pass_wall_on_board(board, wall), "Empty wall allows bypass")

	# Act & Assert 2: Place defender on wall -> blocked!
	board.place_unit("defensor_leste", Vector2i(16, 5)) # In Muralha Leste
	assert_false(judge.can_infiltrator_pass_wall_on_board(board, wall), "Stationed defender blocks bypass")

	# Act & Assert 3: Breach wall -> can pass again!
	board.damage_wall(wall, 100)
	assert_true(board.is_wall_breached(wall))
	assert_true(judge.can_infiltrator_pass_wall_on_board(board, wall), "Breached wall allows pass despite defender")

# ── 6. Catapulta Direct Siege Damage ──────────────────────────────────────────

func test_catapult_deals_direct_siege_damage_to_wall() -> void:
	# Arrange
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	var board: FortressBoard = FortressBoard.new()
	var wall: String = FortressBoard.ZONE_MURALHA_OESTE
	watch_signals(judge)

	# Act 1: Partial siege damage
	var res1: Dictionary = judge.resolve_catapult_siege_damage(board, wall, 45)

	# Assert 1
	assert_eq(res1["damage_dealt"], 45)
	assert_eq(res1["remaining_hp"], 55)
	assert_false(res1["is_breached"], "Wall not yet breached")
	assert_eq(board.get_wall_hp(wall), 55)
	assert_signal_emitted(judge, "catapult_fired")

	# Act 2: Fatal siege damage causing breach
	var res2: Dictionary = judge.resolve_catapult_siege_damage(board, wall, 60)

	# Assert 2
	assert_eq(res2["remaining_hp"], 0)
	assert_true(res2["is_breached"], "Wall is breached by catapult")
	assert_true(board.is_wall_breached(wall))

# ── 7. Static Helper Math ─────────────────────────────────────────────────────

func test_static_helper_math_formulas() -> void:
	# Act & Assert - Melee math: (impacts + 2*crits)/2 - armor
	assert_eq(CercoCombatJudge.calculate_melee_damage(2, 0, 0), 1)
	assert_eq(CercoCombatJudge.calculate_melee_damage(3, 0, 0), 1) # odd rounds down
	assert_eq(CercoCombatJudge.calculate_melee_damage(0, 1, 0), 1) # 1 crit = 2 impacts = 1 dmg
	assert_eq(CercoCombatJudge.calculate_melee_damage(2, 1, 1), 1) # (2 + 2)/2 - 1 = 1
	assert_eq(CercoCombatJudge.calculate_melee_damage(1, 0, 1), 0) # 0 - 1 clamped to 0

	# Act & Assert - Ranged math: (shots + 2*crits) - armor
	assert_eq(CercoCombatJudge.calculate_ranged_damage(1, 0, 0), 1)
	assert_eq(CercoCombatJudge.calculate_ranged_damage(0, 1, 0), 2)
	assert_eq(CercoCombatJudge.calculate_ranged_damage(3, 1, 2), 3) # (3 + 2) - 2 = 3
	assert_eq(CercoCombatJudge.calculate_ranged_damage(1, 0, 3), 0) # clamped to 0
