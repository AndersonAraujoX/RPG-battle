# res://test/unit/test_boss_swarm_queen.gd
extends GutTest

## Suíte de Testes Unitários: Chefe Rainha do Enxame (RainhaDoEnxame.gd)
## Marco M5: Valida atributos de boss (180-220 PV), mitigação de 50% por Guardas Reais,
## invocação periódica de ninhada a cada 2 turnos e gancho narrativo de transição para o Ato III.
## Padrão estrito Arrange-Act-Assert (AAA), segurança headless bare-node e zero memory leaks.

var _queen: RainhaDoEnxame
var _rng: RandomNumberGenerator

func before_each() -> void:
	_queen = autofree(RainhaDoEnxame.new())
	_rng = RandomNumberGenerator.new()
	_rng.seed = 4242

func after_each() -> void:
	_queen = null
	_rng = null

# ══════════════════════════════════════════════════════════════════════════════
# 1. INICIALIZAÇÃO & ATRIBUTOS DE CHEFE
# ══════════════════════════════════════════════════════════════════════════════

func test_queen_initialization_defaults() -> void:
	# Arrange & Act: Instanciado no before_each

	# Assert
	assert_not_null(_queen, "Rainha instanciada com sucesso")
	assert_gte(_queen.max_hp, 180, "HP máximo deve ser pelo menos 180")
	assert_lte(_queen.max_hp, 220, "HP máximo deve ser no máximo 220")
	assert_eq(_queen.current_hp, _queen.max_hp, "HP atual inicia igual ao máximo")
	assert_eq(_queen.ac, 16, "CA padrão da Rainha é 16")
	assert_eq(_queen.team, "B", "Rainha pertence ao time B (inimigos)")
	assert_true(_queen.is_boss, "Flag is_boss deve ser verdadeira")
	assert_true(_queen.is_alive, "Rainha inicia viva")
	assert_eq(_queen.caste_id, "rainha_do_enxame", "Caste ID canônico é rainha_do_enxame")
	assert_false(_queen.has_living_royal_guard(), "Sem guardas reais no início da instância")

func test_queen_caste_data_catalog_integrity() -> void:
	# Arrange & Act
	var caste: IsectumCasteData = IsectumCastes.get_caste(IsectumCastes.ID_RAINHA_DO_ENXAME)

	# Assert
	assert_not_null(caste, "Casta rainha_do_enxame deve existir no catálogo IsectumCastes")
	assert_true(caste.is_boss, "Casta marcada como chefe")
	assert_eq(caste.trait_id, "chamado_da_rainha", "Habilidade canônica é chamado_da_rainha")

# ══════════════════════════════════════════════════════════════════════════════
# 2. MECÂNICA DE PROTEÇÃO DA GUARDA REAL (50% DE REDUÇÃO DE DANO)
# ══════════════════════════════════════════════════════════════════════════════

func test_royal_guard_registration_and_status_tracking() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 25)

	# Act
	_queen.register_royal_guard(guard)

	# Assert
	assert_true(_queen.has_living_royal_guard(), "Deve detectar guarda real viva")
	assert_eq(_queen.get_living_royal_guards().size(), 1, "Exatamente 1 guarda viva")

func test_royal_guard_50_percent_damage_mitigation_when_guard_alive() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 25)
	_queen.register_royal_guard(guard)
	var initial_hp: int = _queen.current_hp
	watch_signals(_queen)

	# Act: Dano de 20 recebido com guarda viva (deve ser mitigado para 10)
	var dealt: int = _queen.take_damage(20)

	# Assert
	assert_eq(dealt, 10, "Dano efetivo deve ser reduzido em 50% (20 -> 10)")
	assert_eq(_queen.current_hp, initial_hp - 10, "HP da Rainha decresce exatamente 10 pontos")
	assert_signal_emitted(_queen, "royal_guard_damage_mitigated")

func test_royal_guard_odd_damage_mitigation_rounding() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 25)
	_queen.register_royal_guard(guard)
	var initial_hp: int = _queen.current_hp

	# Act: Dano ímpar de 15 recebido
	var dealt: int = _queen.take_damage(15)

	# Assert: int(15 * 0.5) = 7
	assert_eq(dealt, 7, "Dano ímpar 15 reduzido em 50% arredonda para 7")
	assert_eq(_queen.current_hp, initial_hp - 7, "HP atual decresce 7 pontos")

func test_normal_100_percent_damage_when_all_guards_are_dead() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 25)
	_queen.register_royal_guard(guard)

	# A guarda sofre 25 de dano e morre
	guard.take_damage(25)
	assert_false(guard.is_alive, "Guarda deve estar morta")
	assert_false(_queen.has_living_royal_guard(), "Rainha não possui mais guardas vivas")
	var initial_hp: int = _queen.current_hp

	# Act: Dano de 20 recebido após a morte das guardas
	var dealt: int = _queen.take_damage(20)

	# Assert: Dano integral de 20 sem mitigação
	assert_eq(dealt, 20, "Dano integral (100%) deve ser aplicado na ausência de guardas")
	assert_eq(_queen.current_hp, initial_hp - 20, "HP decresce 20 pontos completos")

func test_multiple_guards_and_progressive_defeat() -> void:
	# Arrange: Duas guardas reais
	var guard1: Character = autofree(Character.new())
	guard1.setup("guard_1", "Guarda 1", 20)
	var guard2: Character = autofree(Character.new())
	guard2.setup("guard_2", "Guarda 2", 20)

	_queen.register_royal_guard(guard1)
	_queen.register_royal_guard(guard2)
	assert_eq(_queen.get_living_royal_guards().size(), 2)

	# Act 1: Mata a primeira guarda
	guard1.take_damage(20)
	assert_true(_queen.has_living_royal_guard(), "Ainda há 1 guarda viva")

	# Assert 1: Mitigação de 50% ainda ativa
	var dealt1: int = _queen.take_damage(10)
	assert_eq(dealt1, 5, "Dano de 10 mitigado para 5 com 1 guarda remanescente")

	# Act 2: Mata a segunda guarda
	guard2.take_damage(20)
	assert_false(_queen.has_living_royal_guard(), "Ambas as guardas mortas")

	# Assert 2: Mitigação desativada
	var dealt2: int = _queen.take_damage(10)
	assert_eq(dealt2, 10, "Dano de 10 aplicado integralmente")

# ══════════════════════════════════════════════════════════════════════════════
# 3. CHAMADO DA RAINHA (chamado_da_rainha) A CADA 2 TURNOS
# ══════════════════════════════════════════════════════════════════════════════

func test_chamado_da_rainha_periodic_every_two_turns() -> void:
	# Arrange
	_queen.grid_position = Vector2i(10, 2)
	watch_signals(_queen)

	# Act & Assert - Turno 1 (não invoca)
	var t1: Dictionary = _queen.advance_turn(null, _rng)
	assert_false(t1["summoned"], "Turno 1 não deve invocar ninhadas")
	assert_eq(t1["brood_spawned"].size(), 0)

	# Act & Assert - Turno 2 (invoca!)
	var t2: Dictionary = _queen.advance_turn(null, _rng)
	assert_true(t2["summoned"], "Turno 2 deve disparar o Chamado da Rainha")
	assert_gte(t2["brood_spawned"].size(), 2, "Pelo menos 2 insetos invocados")
	assert_signal_emitted(_queen, "brood_summoned")

	# Act & Assert - Turno 3 (cooldown de 1 turno)
	var t3: Dictionary = _queen.advance_turn(null, _rng)
	assert_false(t3["summoned"], "Turno 3 não deve invocar ninhadas")

	# Act & Assert - Turno 4 (invoca novamente!)
	var t4: Dictionary = _queen.advance_turn(null, _rng)
	assert_true(t4["summoned"], "Turno 4 deve disparar nova invocação")
	assert_gte(t4["brood_spawned"].size(), 2)

func test_chamado_da_rainha_brood_unit_properties() -> void:
	# Arrange
	_queen.grid_position = Vector2i(10, 2)

	# Act: Invocação direta
	var brood: Array = _queen.chamado_da_rainha(null, 2, _rng)

	# Assert
	assert_eq(brood.size(), 2, "Invoca exatamente 2 unidades por padrão")
	for u in brood:
		assert_true(u.has("caste_id"), "Unidade gerada possui caste_id")
		assert_true(u.has("hp"), "Unidade gerada possui hp")
		assert_true(u.has("spawn_pos"), "Unidade gerada possui coordenada de spawn")
		assert_eq(u["team"], "B", "Unidades invocadas pertencem ao time B")

# ══════════════════════════════════════════════════════════════════════════════
# 4. GANCHO NARRATIVO DE TRANSIÇÃO (ATO II ➔ ATO III)
# ══════════════════════════════════════════════════════════════════════════════

func test_transition_narrative_hook_triggered_upon_defeat() -> void:
	# Arrange: Rainha sem guardas
	_queen.clear_royal_guards()
	watch_signals(_queen)
	var expected_quote: String = "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"

	# Act: Dano letal
	_queen.take_damage(_queen.max_hp)

	# Assert: Rainha derrotada
	assert_eq(_queen.current_hp, 0, "HP da Rainha zerado")
	assert_false(_queen.is_alive, "Rainha não está mais viva")

	# Sinais de transição emitidos
	assert_signal_emitted(_queen, "transition_narrative_triggered")
	assert_signal_emitted(_queen, "boss_defeated")

	# Validação da fala canônica exata
	var hook: Dictionary = _queen.get_transition_narrative_hook()
	assert_eq(hook["quote"], expected_quote, "Frase canônica de transição do Ato II deve ser idêntica")
	assert_eq(hook["act_from"], 2, "Origem no Ato 2")
	assert_eq(hook["act_to"], 3, "Destino no Ato 3")
	assert_eq(hook["target_mechanic"], "tres_coracoes_colmeia", "Alvo narrativo são os 3 Corações da Colmeia")

func test_transition_narrative_hook_idempotence() -> void:
	# Arrange
	_queen.clear_royal_guards()
	_queen.take_damage(_queen.max_hp)
	assert_true(_queen.narrative_hook_triggered)

	# Act: Dano adicional após a morte
	var dealt_after: int = _queen.take_damage(50)

	# Assert: Dano posterior não causa novo disparo de transição
	assert_eq(dealt_after, 0, "Dano após morte é ignorado")
	assert_eq(_queen.current_hp, 0)
