# res://test/unit/test_act2_mechanics.gd
extends GutTest

## Suíte de Testes Unitários: Mecânicas do Ato II (Túneis Vivos)
## Marco M5: Valida iluminação de tochas (TorchLighting), obstáculos de casulo (ChitinCocoon),
## mini-chefe Cigarra Ressonante (pulso_sonico e atordoamento em área) e determinismo espacial.
## Padrão estrito Arrange-Act-Assert (AAA), segurança headless (bare-node) e zero memory leaks.

var _torch: TorchLighting
var _rng: RandomNumberGenerator

func before_each() -> void:
	_torch = TorchLighting.new(20, 20, 3)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 12345

func after_each() -> void:
	_torch = null
	_rng = null

# ══════════════════════════════════════════════════════════════════════════════
# 1. ILUMINAÇÃO DE TOCHAS (TorchLighting)
# ══════════════════════════════════════════════════════════════════════════════

func test_torch_chebyshev_radius_3_calculation_at_center() -> void:
	# Arrange: Herói posicionado no centro do grid 20x20
	var hero_pos: Vector2i = Vector2i(10, 10)

	# Act: Atualiza visibilidade com raio base 3
	_torch.update_visibility([hero_pos], 0)
	var lit_cells: Array[Vector2i] = _torch.get_lit_cells()

	# Assert: Raio Chebyshev 3 gera um quadrado de (2*3 + 1)^2 = 7*7 = 49 células
	assert_eq(lit_cells.size(), 49, "Raio Chebyshev 3 no centro deve iluminar exatamente 49 células")
	assert_true(_torch.is_cell_lit(Vector2i(10, 10)), "Célula do próprio herói está iluminada")
	assert_true(_torch.is_cell_lit(Vector2i(7, 7)), "Vértice superior-esquerdo (dist 3) está iluminado")
	assert_true(_torch.is_cell_lit(Vector2i(13, 13)), "Vértice inferior-direito (dist 3) está iluminado")
	assert_true(_torch.is_cell_lit(Vector2i(10, 7)), "Borda norte (dist 3) está iluminada")
	assert_true(_torch.is_cell_lit(Vector2i(10, 13)), "Borda sul (dist 3) está iluminada")
	assert_false(_torch.is_cell_lit(Vector2i(6, 10)), "Célula a dist 4 na horizontal deve estar no escuro")
	assert_false(_torch.is_cell_lit(Vector2i(10, 14)), "Célula a dist 4 na vertical deve estar no escuro")
	assert_false(_torch.is_cell_lit(Vector2i(6, 6)), "Célula a dist 4 na diagonal deve estar no escuro")

func test_torch_boundary_clamping_corners() -> void:
	# Arrange: Herói no canto superior-esquerdo (0, 0)
	var corner_nw: Vector2i = Vector2i(0, 0)

	# Act
	_torch.update_visibility([corner_nw], 0)
	var lit_nw: Array[Vector2i] = _torch.get_lit_cells()

	# Assert: Clamping em [0..3] x [0..3] = 4 * 4 = 16 células
	assert_eq(lit_nw.size(), 16, "Canto (0, 0) deve iluminar 16 células sem índices negativos")
	assert_true(_torch.is_cell_lit(Vector2i(0, 0)))
	assert_true(_torch.is_cell_lit(Vector2i(3, 3)))
	assert_false(_torch.is_cell_lit(Vector2i(4, 0)))
	assert_false(_torch.is_cell_lit(Vector2i(0, 4)))

	# Arrange 2: Herói no canto inferior-direito (19, 19)
	var corner_se: Vector2i = Vector2i(19, 19)

	# Act 2
	_torch.update_visibility([corner_se], 0)
	var lit_se: Array[Vector2i] = _torch.get_lit_cells()

	# Assert 2: Clamping em [16..19] x [16..19] = 16 células
	assert_eq(lit_se.size(), 16, "Canto (19, 19) deve iluminar 16 células sem ultrapassar limite 19")
	assert_true(_torch.is_cell_lit(Vector2i(19, 19)))
	assert_true(_torch.is_cell_lit(Vector2i(16, 16)))
	assert_false(_torch.is_cell_lit(Vector2i(15, 19)))

func test_torch_empty_heroes_array_leaves_grid_completely_dark() -> void:
	# Arrange: Nenhum herói vivo presente
	var empty_heroes: Array[Vector2i] = []

	# Act
	_torch.update_visibility(empty_heroes, 0)

	# Assert
	assert_eq(_torch.get_lit_cells().size(), 0, "Grid vazio não possui células iluminadas")
	assert_false(_torch.is_cell_lit(Vector2i(10, 10)), "Célula central deve estar no escuro")
	assert_false(_torch.is_cell_lit(Vector2i(0, 0)), "Origem deve estar no escuro")

func test_torch_dead_hero_positions_ignored() -> void:
	# Arrange: 1 herói vivo em (5, 5) e simulação de herói morto cujo ponto foi excluído
	var living_heroes: Array[Vector2i] = [Vector2i(5, 5)]

	# Act
	_torch.update_visibility(living_heroes, 0)

	# Assert: Apenas a área do herói vivo em (5, 5) é iluminada
	assert_true(_torch.is_cell_lit(Vector2i(5, 5)))
	# Posição onde o herói tombou (15, 15) permanece no escuro
	assert_false(_torch.is_cell_lit(Vector2i(15, 15)), "Posição de herói caído não deve emitir luz")

func test_torch_relic_tocha_eterna_boosts_radius_by_plus_two() -> void:
	# Arrange: Herói em (10, 10) com relíquia 'tocha_eterna' ativa (+2 de raio)
	var bonus_radius: int = _torch.calculate_bonus_from_relics(["tocha_eterna"])
	assert_eq(bonus_radius, 2, "Relíquia tocha_eterna deve conceder exatamente +2 de bônus")

	# Act: Raio efetivo passa de 3 para 5
	_torch.update_visibility([Vector2i(10, 10)], bonus_radius)
	var lit: Array[Vector2i] = _torch.get_lit_cells()

	# Assert: (2*5 + 1)^2 = 11*11 = 121 células
	assert_eq(lit.size(), 121, "Raio 5 deve iluminar 121 células no centro")
	assert_true(_torch.is_cell_lit(Vector2i(5, 5)), "Vértice dist 5 iluminado")
	assert_true(_torch.is_cell_lit(Vector2i(15, 15)), "Vértice dist 5 iluminado")
	assert_false(_torch.is_cell_lit(Vector2i(4, 10)), "Distância 6 deve permanecer no escuro")

func test_torch_darkness_blocks_ranged_targeting_but_allows_melee() -> void:
	# Arrange: Herói em (10, 10), inimigo no escuro em (2, 2)
	_torch.update_visibility([Vector2i(10, 10)], 0)
	watch_signals(_torch)

	# Act 1: Ataque à distância (alcance 15) contra alvo no escuro
	var ranged_can_target: bool = _torch.can_target_cell(Vector2i(10, 10), Vector2i(2, 2), 15)

	# Assert 1: Alvo no escuro bloqueia ataque à distância
	assert_false(ranged_can_target, "Ataque à distância mirando em célula no escuro deve ser bloqueado")
	assert_signal_emitted(_torch, "darkness_blocked_targeting")

	# Act 2: Ataque corpo-a-corpo (alcance 1) entre duas células adjacentes no escuro
	var melee_in_darkness: bool = _torch.can_target_cell(Vector2i(1, 1), Vector2i(1, 2), 1)

	# Assert 2: Melee adjacente é permitido mesmo no escuro
	assert_true(melee_in_darkness, "Ataque Melee adjacente é permitido mesmo na escuridão")

func test_torch_enemy_shroud_modifiers_in_darkness() -> void:
	# Arrange: Iluminação apenas em torno de (10, 10)
	_torch.update_visibility([Vector2i(10, 10)], 0)

	# Act: Consulta modificadores de cobertura/camuflagem de inimigo em (0, 0)
	var shroud_unlit: Dictionary = _torch.get_shroud_modifiers(Vector2i(0, 0))
	var shroud_lit: Dictionary = _torch.get_shroud_modifiers(Vector2i(10, 10))

	# Assert
	assert_true(shroud_unlit["is_shrouded"], "Inimigo no escuro está camuflado (shrouded)")
	assert_true(shroud_unlit["blocks_ranged"], "Inimigo no escuro bloqueia projéteis")
	assert_eq(shroud_unlit["ac_bonus"], 2, "Inimigo no escuro recebe bônus de +2 na CA")
	assert_false(shroud_lit["is_shrouded"], "Inimigo na luz não recebe camuflagem")

# ══════════════════════════════════════════════════════════════════════════════
# 2. CASULOS DE QUITINA (ChitinCocoon)
# ══════════════════════════════════════════════════════════════════════════════

func test_cocoon_initialization_stats() -> void:
	# Arrange & Act
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_1", Vector2i(8, 8))

	# Assert
	assert_eq(cocoon.max_hp, 15, "Casulo possui 15 PV")
	assert_eq(cocoon.current_hp, 15, "PV atual igual ao máximo")
	assert_eq(cocoon.ac, 10, "CA padrão do casulo é 10")
	assert_eq(cocoon.hatch_countdown, 3, "Contagem regressiva inicial é de 3 turnos")
	assert_false(cocoon.is_destroyed, "Casulo inicia intacto")
	assert_false(cocoon.is_hatched, "Casulo inicia não eclodido")

func test_cocoon_countdown_decrement_per_round() -> void:
	# Arrange
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_1", Vector2i(8, 8))
	watch_signals(cocoon)

	# Act & Assert - Turno 1 (3 -> 2)
	var res1: Dictionary = cocoon.tick_round()
	assert_eq(cocoon.hatch_countdown, 2, "Contagem decresce para 2")
	assert_eq(res1["status"], "counting_down")
	assert_signal_emitted(cocoon, "countdown_ticked")

	# Act & Assert - Turno 2 (2 -> 1)
	var res2: Dictionary = cocoon.tick_round()
	assert_eq(cocoon.hatch_countdown, 1, "Contagem decresce para 1")
	assert_eq(res2["status"], "counting_down")

func test_cocoon_hp_damage_and_destruction() -> void:
	# Arrange
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_1", Vector2i(8, 8))
	watch_signals(cocoon)

	# Act 1: Dano parcial de 6 PV
	var dealt1: int = cocoon.apply_damage(6)
	assert_eq(dealt1, 6)
	assert_eq(cocoon.current_hp, 9)
	assert_false(cocoon.is_destroyed)
	assert_signal_emitted(cocoon, "damaged")

	# Act 2: Dano fatal de 12 PV (overkill)
	var dealt2: int = cocoon.apply_damage(12)
	assert_eq(dealt2, 12)
	assert_eq(cocoon.current_hp, 0, "HP clampado em 0")
	assert_true(cocoon.is_destroyed, "Casulo marcado como destruído")
	assert_signal_emitted(cocoon, "destroyed")

func test_cocoon_cancellation_on_death_before_hatch() -> void:
	# Arrange: Casulo sofre 15 de dano no primeiro turno
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_1", Vector2i(8, 8))
	cocoon.apply_damage(15)
	assert_true(cocoon.is_destroyed)

	# Act: Avança o turno com o casulo morto
	var res: Dictionary = cocoon.tick_round()

	# Assert: Eclosão cancelada permanentemente
	assert_eq(res["status"], "cancelled", "Eclosão deve ser cancelada se destruído")
	assert_eq(res["reason"], "destroyed")
	assert_false(cocoon.is_hatched, "Casulo destruído não eclode")

func test_cocoon_hatching_at_countdown_zero_spawns_t2_and_deals_acid_damage() -> void:
	# Arrange: Casulo pronto para eclodir no 3º turno
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_1", Vector2i(10, 10))
	var grid: TacticalGrid = TacticalGrid.new(20, 20)
	watch_signals(cocoon)

	# Act: 3 rodadas completas
	cocoon.tick_round(grid, _rng) # 3 -> 2
	cocoon.tick_round(grid, _rng) # 2 -> 1
	var hatch_result: Dictionary = cocoon.tick_round(grid, _rng) # 1 -> 0 (Eclode!)

	# Assert
	assert_eq(hatch_result["status"], "hatched", "Status de retorno deve ser 'hatched'")
	assert_true(cocoon.is_hatched, "Flag is_hatched deve ser verdadeira")
	assert_signal_emitted(cocoon, "hatched")
	assert_signal_emitted(cocoon, "acid_burst")

	# Validação da casta Tier 2
	var spawned_caste: String = str(hatch_result["caste_id"])
	assert_true(
		spawned_caste in ChitinCocoon.TIER_2_CASTES,
		"Casta gerada (%s) deve pertencer ao pool Tier 2 de casulos" % spawned_caste
	)

	# Validação da célula adjacente de spawn
	var spawn_pos: Vector2i = hatch_result["spawn_pos"]
	assert_ne(spawn_pos, Vector2i(-1, -1), "Spawn cell válida encontrada")
	var dist_to_cocoon: int = maxi(abs(spawn_pos.x - 10), abs(spawn_pos.y - 10))
	assert_lte(dist_to_cocoon, 2, "Célula gerada deve ser contígua ao casulo")

	# Validação do dano ácido de 5 pontos
	assert_eq(hatch_result["acid_damage"], 5, "Dano ácido da explosão de casulo é exatamente 5")
	assert_gt(hatch_result["acid_cells"].size(), 0, "Células adjacentes devem receber rajada ácida")

func test_cocoon_boundary_acid_burst_at_grid_corner() -> void:
	# Arrange: Casulo no canto (0, 0)
	var cocoon: ChitinCocoon = ChitinCocoon.new("cocoon_corner", Vector2i(0, 0))
	var grid: TacticalGrid = TacticalGrid.new(20, 20)

	# Act: Força eclosão direta
	var res: Dictionary = cocoon.hatch(grid, _rng)
	var acid_cells: Array[Vector2i] = res["acid_cells"]

	# Assert: Apenas 3 células adjacentes válidas (1,0), (0,1), (1,1)
	assert_eq(acid_cells.size(), 3, "No canto (0, 0), apenas 3 células adjacentes existem")
	for p in acid_cells:
		assert_true(p.x >= 0 and p.x < 20 and p.y >= 0 and p.y < 20, "Célula ácida deve ser válida")

# ══════════════════════════════════════════════════════════════════════════════
# 3. MINI-CHEFE CIGARRA RESSONANTE (CigarraRessonante)
# ══════════════════════════════════════════════════════════════════════════════

func test_cigarra_ressonante_stats_and_immunity() -> void:
	# Arrange & Act
	var cicada: CigarraRessonante = autofree(CigarraRessonante.new())

	# Assert
	assert_gte(cicada.max_hp, 70, "PV da Cigarra dentro da faixa de mini-boss (70-90)")
	assert_lte(cicada.max_hp, 90, "PV da Cigarra dentro da faixa de mini-boss (70-90)")
	assert_eq(cicada.ac, 15, "CA da Cigarra é 15")
	assert_gte(cicada.move_speed, 4, "Alta mobilidade (>= 4)")
	assert_true(cicada.is_elite, "Flag is_elite deve ser verdadeira")

	# Imunidade a atordoamento
	var stun_applied: bool = cicada.add_status_effect("stunned")
	assert_false(stun_applied, "Cigarra Ressonante deve ser imune a Stun")
	assert_false(cicada.has_status_effect("stunned"))

func test_cigarra_pulso_sonico_triggers_aoe_and_stun_on_clustered_heroes() -> void:
	# Arrange: Dois heróis agrupados (distância Chebyshev 1 <= 2)
	var cicada: CigarraRessonante = autofree(CigarraRessonante.new())
	cicada.grid_position = Vector2i(10, 5)

	var hero1: Character = autofree(Character.new())
	hero1.setup("guerreiro", "Guerreiro", 40)
	hero1.grid_position = Vector2i(10, 8)

	var hero2: Character = autofree(Character.new())
	hero2.setup("mago", "Mago", 25)
	hero2.grid_position = Vector2i(11, 8)

	var party: Array = [hero1, hero2]
	watch_signals(cicada)

	# Act: Cigarra dispara pulso sônico no ponto médio do agrupamento
	var pulse_res: Dictionary = cicada.pulso_sonico(Vector2i(10, 8), party, _rng)

	# Assert
	assert_true(pulse_res["success"], "Pulso executado com sucesso")
	assert_true(pulse_res["clustered"], "Detectou heróis agrupados (>= 2 em raio <= 2)")
	assert_true(pulse_res["stun_applied"], "Condição Atordoado aplicada devido ao agrupamento")
	assert_gte(pulse_res["damage_dealt"], 8, "Causou dano sônico")

	# Verifica se ambos os heróis sofreram dano e ficaram atordoados
	assert_lt(hero1.current_hp, 40, "Herói 1 sofreu dano")
	assert_lt(hero2.current_hp, 25, "Herói 2 sofreu dano")
	assert_true(hero1.has_status_effect("stunned"), "Herói 1 ficou atordoado")
	assert_true(hero2.has_status_effect("stunned"), "Herói 2 ficou atordoado")
	assert_signal_emitted(cicada, "pulso_sonico_triggered")

func test_cigarra_pulso_sonico_does_not_stun_isolated_hero() -> void:
	# Arrange: Apenas 1 herói isolado (distância > 2 de qualquer aliado)
	var cicada: CigarraRessonante = autofree(CigarraRessonante.new())
	var isolated_hero: Character = autofree(Character.new())
	isolated_hero.setup("ladino", "Ladino", 30)
	isolated_hero.grid_position = Vector2i(5, 5)

	var party: Array = [isolated_hero]

	# Act: Disparo contra o herói isolado
	var pulse_res: Dictionary = cicada.pulso_sonico(Vector2i(5, 5), party, _rng)

	# Assert: Dano ocorre, mas NÃO atordoa
	assert_true(pulse_res["success"])
	assert_false(pulse_res["clustered"], "Não há agrupamento (apenas 1 alvo)")
	assert_false(pulse_res["stun_applied"], "Não aplica stun em alvo isolado")
	assert_lt(isolated_hero.current_hp, 30, "Herói isolado sofreu dano normal")
	assert_false(isolated_hero.has_status_effect("stunned"), "Herói isolado NÃO deve ficar atordoado")
