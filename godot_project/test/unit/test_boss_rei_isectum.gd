# res://test/unit/test_boss_rei_isectum.gd
extends GutTest

## Testes Unitários: Chefe Final Rei dos Isectum (Marco M6)
## Valida a máquina de estados de 3 fases, ocupação 3x3, imunidades,
## fraqueza elemental a Fogo na Fase 3 e os debuffs dos 3 Corações da Colmeia.

var _boss: ReiIsectum

func before_each() -> void:
	_boss = ReiIsectum.new()

func after_each() -> void:
	if _boss != null:
		_boss.free()
		_boss = null

# ── 1. Inicialização & Atributos Base ─────────────────────────────────────────

func test_initial_state_and_base_stats() -> void:
	# Arrange & Act
	# (_boss criado em before_each)

	# Assert
	assert_eq(_boss.character_id, "rei_isectum")
	assert_eq(_boss.character_name, "Rei dos Isectum")
	assert_eq(_boss.team, "B")
	assert_eq(_boss.max_hp, 450)
	assert_eq(_boss.current_hp, 450)
	assert_eq(_boss.ac, 19)
	assert_eq(_boss.current_phase, ReiIsectum.Phase.THRONE_PHASE_1)
	assert_true(_boss.has_elevation_advantage)
	assert_true(_boss.is_immune_to_push())
	assert_eq(_boss.actions_per_turn, 1)

func test_3x3_grid_footprint_and_point_containment() -> void:
	# Arrange
	_boss.grid_position = Vector2i(5, 5)

	# Act
	var tiles: Array[Vector2i] = _boss.get_occupied_tiles()

	# Assert
	assert_eq(tiles.size(), 9, "O Rei deve ocupar exatamente 9 células (3x3)")
	assert_true(tiles.has(Vector2i(5, 5)), "Canto superior esquerdo")
	assert_true(tiles.has(Vector2i(6, 6)), "Centro do 3x3")
	assert_true(tiles.has(Vector2i(7, 7)), "Canto inferior direito")
	assert_true(_boss.is_point_inside(Vector2i(6, 5)))
	assert_false(_boss.is_point_inside(Vector2i(8, 8)))

func test_condition_immunities_strictly_reject_poison_and_stun() -> void:
	# Arrange & Act
	var added_poison: bool = _boss.add_status_effect("Envenenado")
	var added_stun: bool = _boss.add_status_effect("Atordoado")
	var added_fear: bool = _boss.add_status_effect("Medo")

	# Assert
	assert_false(added_poison, "O Rei deve ser imune a Envenenado")
	assert_false(added_stun, "O Rei deve ser imune a Atordoado")
	assert_false(_boss.has_status_effect("Envenenado"))
	assert_false(_boss.has_status_effect("Atordoado"))
	assert_true(added_fear, "Outras condições não imunes podem ser aplicadas")
	assert_true(_boss.has_status_effect("Medo"))

# ── 2. Mecânicas da Fase 1: Trono de Âmbar ───────────────────────────────────

func test_phase_1_excavate_throne_pillars_collapses_throne() -> void:
	# Arrange
	watch_signals(_boss)

	# Act 1: Escavação parcial
	var collapsed_early: bool = _boss.excavate_throne_pillars(30)

	# Assert 1
	assert_false(collapsed_early)
	assert_eq(_boss.throne_pillars_hp, 30)
	assert_true(_boss.has_elevation_advantage)
	assert_signal_emitted_with_parameters(_boss, "throne_pillars_damaged", [30, 30])

	# Act 2: Escavação total quebra os pilares
	var collapsed_final: bool = _boss.excavate_throne_pillars(35)

	# Assert 2
	assert_true(collapsed_final)
	assert_eq(_boss.throne_pillars_hp, 0)
	assert_false(_boss.has_elevation_advantage, "Ao cair o trono, perde vantagem de elevação")
	assert_signal_emitted(_boss, "throne_collapsed")
	assert_signal_emitted(_boss, "screen_shake_requested")

func test_phase_1_execute_absolute_command_orders_up_to_two_guards() -> void:
	# Arrange
	watch_signals(_boss)
	var g1: Dictionary = {"id": "g1", "hp": 20}
	var g2: Dictionary = {"id": "g2", "hp": 20}
	var g3: Dictionary = {"id": "g3", "hp": 20}
	var dead_g: Dictionary = {"id": "dead", "hp": 0}

	# Act
	var ordered: Array = _boss.execute_absolute_command([dead_g, g1, g2, g3])

	# Assert
	assert_eq(ordered.size(), 2, "Comando Absoluto comanda no máximo 2 guardas vivos")
	assert_eq(ordered[0].id, "g1")
	assert_eq(ordered[1].id, "g2")
	assert_signal_emitted(_boss, "absolute_command_executed")

func test_phase_1_execute_amber_spear_creates_obstacle() -> void:
	# Arrange
	_boss.grid_position = Vector2i(10, 2)
	watch_signals(_boss)

	# Act
	var res: Dictionary = _boss.execute_amber_spear(Vector2i(10, 8))

	# Assert
	assert_eq(res.origin, Vector2i(10, 2))
	assert_eq(res.target, Vector2i(10, 8))
	assert_eq(res.obstacle_created, Vector2i(10, 8))
	assert_signal_emitted_with_parameters(_boss, "amber_spear_fired", [Vector2i(10, 2), Vector2i(10, 8), Vector2i(10, 8)])

# ── 3. Transição para Fase 2: A Muralha Viva ──────────────────────────────────

func test_transition_to_phase_2_at_300_hp() -> void:
	# Arrange
	watch_signals(_boss)

	# Act: Dano suficiente para baixar de 450 para 290 (<= 300)
	_boss.take_damage(160)

	# Assert
	assert_eq(_boss.current_hp, 290)
	assert_eq(_boss.current_phase, ReiIsectum.Phase.LIVING_WALL_PHASE_2)
	assert_false(_boss.has_elevation_advantage, "Desce do trono para a arena")
	assert_signal_emitted_with_parameters(_boss, "phase_changed", [ReiIsectum.Phase.LIVING_WALL_PHASE_2, ReiIsectum.Phase.THRONE_PHASE_1])
	assert_signal_emitted(_boss, "screen_shake_requested")

func test_phase_2_miasma_expansion_cells() -> void:
	# Arrange
	watch_signals(_boss)

	# Act
	var border_cells: Array[Vector2i] = _boss.get_miasma_border_cells(20, 1)

	# Assert
	assert_gt(border_cells.size(), 0)
	assert_true(border_cells.has(Vector2i(0, 0)))
	assert_true(border_cells.has(Vector2i(19, 19)))
	assert_false(border_cells.has(Vector2i(10, 10)), "Centro não deve ter miasma no anel 1")
	assert_signal_emitted(_boss, "miasma_expanded")

func test_phase_2_colossal_slam_hits_3x3_area() -> void:
	# Arrange
	var hero_near: Character = Character.new()
	hero_near.character_id = "stark"
	hero_near.max_hp = 50
	hero_near.current_hp = 50
	hero_near.grid_position = Vector2i(5, 5)

	var hero_far: Character = Character.new()
	hero_far.character_id = "elden"
	hero_far.max_hp = 40
	hero_far.current_hp = 40
	hero_far.grid_position = Vector2i(10, 10)

	watch_signals(_boss)

	# Act
	var slam_res: Dictionary = _boss.execute_colossal_slam(Vector2i(5, 5), [hero_near, hero_far], 25)

	# Assert
	assert_eq(slam_res.hit_units.size(), 1)
	assert_eq(hero_near.current_hp, 25, "Sofreu 25 de dano do esmagamento")
	assert_eq(hero_far.current_hp, 40, "Herói longe não foi atingido")
	assert_signal_emitted(_boss, "colossal_slam_executed")

	hero_near.free()
	hero_far.free()

func test_phase_2_summon_guard_respects_brood_heart_debuff() -> void:
	# Arrange: Sem debuff
	_boss.heart_brood_destroyed = false

	# Act 1: Invoca com sucesso
	var guard: Dictionary = _boss.summon_royal_guard(Vector2i(5, 5))

	# Assert 1
	assert_false(guard.is_empty(), "Deve invocar se o Coração da Ninhada não foi destruído")
	assert_eq(guard.caste_id, "escaravelho_couracado")

	# Arrange 2: Com Coração da Ninhada destruído
	_boss.heart_brood_destroyed = true

	# Act 2: Tentativa de invocação
	var blocked_guard: Dictionary = _boss.summon_royal_guard(Vector2i(5, 5))

	# Assert 2
	assert_true(blocked_guard.is_empty(), "Deve ser bloqueado se o Coração da Ninhada foi destruído")

# ── 4. Transição para Fase 3: Coroa Quebrada ──────────────────────────────────

func test_transition_to_phase_3_at_150_hp() -> void:
	# Arrange
	watch_signals(_boss)

	# Act: Dano para reduzir para 140 (<= 150)
	_boss.take_damage(310)

	# Assert
	assert_eq(_boss.current_hp, 140)
	assert_eq(_boss.current_phase, ReiIsectum.Phase.BROKEN_CROWN_PHASE_3)
	assert_eq(_boss.ac, 16, "CA reduzida em 3 pontos pela carapaça quebrada")
	assert_eq(_boss.actions_per_turn, 2, "Entra em frenesi e ganha 2 ações por turno")
	assert_signal_emitted_with_parameters(_boss, "phase_changed", [ReiIsectum.Phase.BROKEN_CROWN_PHASE_3, ReiIsectum.Phase.THRONE_PHASE_1])

func test_phase_3_fire_weakness_applies_double_damage() -> void:
	# Arrange: Coloca o chefe na Fase 3
	_boss.take_damage(310) # Fica com 140 PV
	var hp_before: int = _boss.current_hp

	# Act 1: Dano físico normal de 20
	var phys_dmg: int = _boss.take_damage(20, "Cortante")

	# Assert 1
	assert_eq(phys_dmg, 20)
	assert_eq(_boss.current_hp, hp_before - 20)

	# Act 2: Dano de Fogo de 20 (deve dobrar para 40)
	var fire_hp_before: int = _boss.current_hp
	var fire_dmg: int = _boss.take_damage(20, "Fogo")

	# Assert 2
	assert_eq(fire_dmg, 40, "Fraqueza elemental deve aplicar 2x de dano de Fogo na Fase 3")
	assert_eq(_boss.current_hp, fire_hp_before - 40)

func test_phase_3_devour_essence_heals_from_fallen_hero() -> void:
	# Arrange: Coloca na Fase 3 e reduz HP
	_boss.take_damage(350) # Fica com 100 PV
	var fallen_hero: Character = Character.new()
	fallen_hero.character_id = "kuro"
	fallen_hero.max_hp = 35
	fallen_hero.current_hp = 0
	fallen_hero.is_alive = false

	watch_signals(_boss)

	# Act
	var devoured: Character = _boss.execute_devour_essence([fallen_hero])

	# Assert
	assert_not_null(devoured)
	assert_eq(_boss.current_hp, 140, "Deve curar 40 PV ao devorar herói caído")
	assert_signal_emitted_with_parameters(_boss, "devour_essence_attempted", [fallen_hero, 40])

	fallen_hero.free()

# ── 5. Derrota do Boss & Vitória da Campanha ──────────────────────────────────

func test_boss_death_emits_boss_defeated_signal_with_amber_reward() -> void:
	# Arrange
	watch_signals(_boss)

	# Act: Causa 450 de dano total
	_boss.take_damage(450)

	# Assert
	assert_eq(_boss.current_hp, 0)
	assert_false(_boss.is_alive)
	assert_signal_emitted(_boss, "died")
	assert_signal_emitted(_boss, "boss_defeated")

# ── 6. Debuffs dos 3 Corações da Colmeia ───────────────────────────────────────

func test_apply_heart_debuffs_affects_all_parameters() -> void:
	# Arrange
	var hearts: Array = ["coracao_da_mente", "coracao_da_carapaca", "coracao_da_ninhada"]
	watch_signals(_boss)

	# Act
	var summary: Dictionary = _boss.apply_heart_debuffs(hearts)

	# Assert
	assert_true(_boss.heart_mind_destroyed)
	assert_true(_boss.heart_carapace_destroyed)
	assert_true(_boss.heart_brood_destroyed)
	assert_eq(_boss.ac, 16, "Coração da Carapaça reduz CA para 16")
	assert_signal_emitted(_boss, "heart_debuffs_applied")
	assert_true(summary.mind_disabled)
	assert_true(summary.carapace_weakened)
	assert_true(summary.brood_blocked)

func test_apply_heart_debuffs_empty_leaves_full_strength() -> void:
	# Arrange & Act
	var summary: Dictionary = _boss.apply_heart_debuffs([])

	# Assert
	assert_false(_boss.heart_mind_destroyed)
	assert_false(_boss.heart_carapace_destroyed)
	assert_false(_boss.heart_brood_destroyed)
	assert_eq(_boss.ac, 19, "Sem destruir o Coração da Carapaça, mantém CA 19")
	assert_false(summary.mind_disabled)

# ── 7. Casos de Borda e Erro ──────────────────────────────────────────────────

func test_edge_case_negative_and_zero_damage() -> void:
	# Arrange & Act
	var dmg_zero: int = _boss.take_damage(0)
	var dmg_neg: int = _boss.take_damage(-15)

	# Assert
	assert_eq(dmg_zero, 0)
	assert_eq(dmg_neg, 0)
	assert_eq(_boss.current_hp, 450)

func test_edge_case_damage_after_death_returns_zero() -> void:
	# Arrange
	_boss.take_damage(450)
	assert_false(_boss.is_alive)

	# Act
	var overkill: int = _boss.take_damage(50)

	# Assert
	assert_eq(overkill, 0)
	assert_eq(_boss.current_hp, 0)
