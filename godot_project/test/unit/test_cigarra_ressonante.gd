# res://test/unit/test_cigarra_ressonante.gd
extends GutTest

## Suíte de Testes Unitários: Mini-Chefe Cigarra Ressonante (CigarraRessonante.gd)
## Marco M5: Valida HP 70-90, alta mobilidade, imunidade a Atordoamento,
## e pulso_sonico com trigger de agrupamento (>= 2 heróis em distância <= 2).
## Padrão estrito Arrange-Act-Assert (AAA), segurança headless bare-node e zero leaks.

var _cigarra: CigarraRessonante
var _rng: RandomNumberGenerator

func before_each() -> void:
	_cigarra = autofree(CigarraRessonante.new())
	_rng = RandomNumberGenerator.new()
	_rng.seed = 9999

func after_each() -> void:
	_cigarra = null
	_rng = null

# ── 1. Atributos de Elite & Imunidade ─────────────────────────────────────────

func test_cigarra_initialization_defaults() -> void:
	# Arrange & Act: no before_each

	# Assert
	assert_not_null(_cigarra, "Cigarra instanciada com sucesso")
	assert_gte(_cigarra.max_hp, 70, "HP mínimo de elite é 70")
	assert_lte(_cigarra.max_hp, 90, "HP máximo de elite é 90")
	assert_gte(_cigarra.move_speed, 4, "Alta mobilidade (velocidade >= 4)")
	assert_true(_cigarra.is_flyer, "Cigarra é unidade voadora")
	assert_true(_cigarra.is_elite, "Flag is_elite deve ser verdadeira")
	assert_eq(_cigarra.team, "B", "Time B (inimigo)")

func test_cigarra_immunity_to_stun_and_atordoado() -> void:
	# Arrange & Act
	var ok_stun: bool = _cigarra.add_status_effect("stunned")
	var ok_ator: bool = _cigarra.add_status_effect("atordoado")
	var ok_burn: bool = _cigarra.add_status_effect("burning")

	# Assert
	assert_false(ok_stun, "Imune a 'stunned'")
	assert_false(ok_ator, "Imune a 'atordoado'")
	assert_false(_cigarra.has_status_effect("stunned"), "Não deve possuir stunned ativo")
	assert_true(ok_burn, "Outras condições (ex: burning) devem funcionar normalmente")

# ── 2. Detecção Espacial de Agrupamento (Chebyshev) ──────────────────────────

func test_clustering_detection_chebyshev_distance() -> void:
	# Arrange
	var center: Vector2i = Vector2i(5, 5)
	var hero_near: Vector2i = Vector2i(7, 6) # dx=2, dy=1 -> chebyshev = 2 (dentro)
	var hero_far: Vector2i = Vector2i(8, 5)  # dx=3, dy=0 -> chebyshev = 3 (fora)

	# Act
	var clustered_heroes: Array = _cigarra.find_clustered_heroes(center, [hero_near, hero_far], 2)

	# Assert
	assert_eq(clustered_heroes.size(), 1, "Apenas o herói dentro do raio 2 é retornado")
	assert_eq(clustered_heroes[0], hero_near)

func test_is_hero_clustered_requires_at_least_two_heroes() -> void:
	# Arrange
	var center: Vector2i = Vector2i(5, 5)
	var h1: Vector2i = Vector2i(5, 6) # d = 1
	var h2: Vector2i = Vector2i(6, 7) # d = 2
	var h3_far: Vector2i = Vector2i(10, 10) # d = 5

	# Act & Assert
	assert_true(_cigarra.is_hero_clustered(center, [h1, h2], 2, 2), "2 heróis no raio = agrupado")
	assert_false(_cigarra.is_hero_clustered(center, [h1, h3_far], 2, 2), "1 herói no raio = não agrupado")

# ── 3. Pulso Sônico: Dano em Área e Atordoamento ──────────────────────────────

func test_pulso_sonico_clustered_applies_aoe_damage_and_stun() -> void:
	# Arrange
	var hero1: Character = autofree(Character.new())
	hero1.setup("aquele", "Aquele", 30)
	hero1.set_grid_position(Vector2i(5, 5))

	var hero2: Character = autofree(Character.new())
	hero2.setup("stark", "Stark", 30)
	hero2.set_grid_position(Vector2i(6, 6))

	watch_signals(_cigarra)

	# Act: Pulso disparado no centro (5, 5) pegando ambos
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [hero1, hero2], _rng)

	# Assert
	assert_true(res["success"], "Ataque sônico bem sucedido")
	assert_true(res["clustered"], "Detectou agrupamento (>= 2 heróis)")
	assert_true(res["stun_applied"], "Aplicou atordoamento")
	assert_eq(res["duration"], 1, "Duração do atordoamento é 1 rodada")
	assert_gt(res["damage_dealt"], 0, "Dano positivo")

	assert_lt(hero1.current_hp, 30, "Hero 1 sofreu dano")
	assert_lt(hero2.current_hp, 30, "Hero 2 sofreu dano")
	assert_true(hero1.has_status_effect("stunned"), "Hero 1 está atordoado")
	assert_true(hero2.has_status_effect("stunned"), "Hero 2 está atordoado")
	assert_signal_emitted(_cigarra, "pulso_sonico_triggered")

func test_pulso_sonico_unclustered_deals_damage_without_stun() -> void:
	# Arrange: Apenas 1 herói isolado
	var hero_solo: Character = autofree(Character.new())
	hero_solo.setup("elden", "Elden", 30)
	hero_solo.set_grid_position(Vector2i(5, 5))

	# Act
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [hero_solo], _rng)

	# Assert
	assert_true(res["success"], "Ataque sônico disparado")
	assert_false(res["clustered"], "Não agrupado (apenas 1 herói)")
	assert_false(res["stun_applied"], "NÃO aplica atordoamento em herói isolado")
	assert_false(hero_solo.has_status_effect("stunned"), "Herói isolado livre de stun")
	assert_lt(hero_solo.current_hp, 30, "Herói isolado ainda recebe o dano")

func test_pulso_sonico_empty_or_dead_heroes_edge_case() -> void:
	# Arrange: Herói morto
	var dead_hero: Character = autofree(Character.new())
	dead_hero.setup("morto", "Herói Caído", 30)
	dead_hero.take_damage(30)
	dead_hero.set_grid_position(Vector2i(5, 5))

	# Act
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [dead_hero], _rng)

	# Assert
	assert_false(res["success"], "Herói morto não constitui alvo válido")
	assert_eq(res["targets_hit"].size(), 0)
