# res://test/unit/test_relic_system.gd
extends GutTest

## Test Suite for Relic System (Milestone M3)
## Validates RelicData, RelicManager, and the 10 Canonical Relics.
## Adheres strictly to Arrange-Act-Assert (AAA) pattern, zero leaks, and headless execution.

const EventBusScript = preload("res://scripts/autoload/EventBus.gd")

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState
var _eb: Node
var _manager: RelicManager

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 42
	_state = RunState.new(_generator, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque", "defesa"], 12345)
	
	if get_node_or_null("/root/EventBus") != null:
		_eb = get_node("/root/EventBus")
		_eb.reset_telemetry()
	else:
		_eb = autofree(EventBusScript.new())
	
	_manager = RelicManager.new(_state, _eb)

func after_each() -> void:
	if _manager != null:
		_manager.unregister_all()
		_manager = null
	_state = null
	_rng = null
	_generator = null
	_eb = null

# ==============================================================================
# 1. RelicData Base Model & Serialization
# ==============================================================================

func test_relic_data_initialization_and_serialization() -> void:
	# Arrange
	var relic: RelicData = RelicData.new("relic_test", "Relic Test", "Desc", RelicData.RARITY_RARO, 80)
	relic.counter = 2
	relic.counter_max = 5

	# Act
	var dict: Dictionary = relic.to_dict()
	var restored: RelicData = RelicData.new()
	restored.from_dict(dict)

	# Assert
	assert_eq(restored.id, "relic_test", "ID preservado")
	assert_eq(restored.relic_name, "Relic Test", "Nome preservado")
	assert_eq(restored.rarity, RelicData.RARITY_RARO, "Raridade preservada")
	assert_eq(restored.cost_gold, 80, "Custo preservado")
	assert_eq(restored.counter, 2, "Counter preservado")
	assert_true(restored.is_active, "Ativo por padrão")

# ==============================================================================
# 2. RelicManager Lifecycle & Registration
# ==============================================================================

func test_relic_manager_registration_and_duplicates() -> void:
	# Arrange & Act
	var ok: bool = _manager.register_relic("martelo_runico")
	var dup: bool = _manager.register_relic("martelo_runico")
	var invalid: bool = _manager.register_relic("reliquia_inexistente")
	var empty: bool = _manager.register_relic("")

	# Assert
	assert_true(ok, "Registro de martelo_runico com sucesso")
	assert_false(dup, "Registro duplicado deve ser rejeitado")
	assert_false(invalid, "ID não cadastrado no catálogo deve ser rejeitado")
	assert_false(empty, "ID vazio deve ser rejeitado")
	assert_eq(_manager.get_relic_count(), 1, "Apenas 1 relíquia ativa")
	assert_true(_state.has_relic("martelo_runico"), "RunState sincronizado")

func test_relic_manager_unregister_and_cleanup() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")
	_manager.register_relic("escudo_ancestral")
	assert_eq(_manager.get_relic_count(), 2)

	# Act
	var removed: bool = _manager.unregister_relic("martelo_runico")
	var not_found: bool = _manager.unregister_relic("martelo_runico")

	# Assert
	assert_true(removed, "Relíquia removida com sucesso")
	assert_false(not_found, "Segunda remoção retorna false")
	assert_eq(_manager.get_relic_count(), 1)
	assert_false(_state.has_relic("martelo_runico"), "Removido do RunState")

	# Clean all
	_manager.unregister_all()
	assert_eq(_manager.get_relic_count(), 0)

# ==============================================================================
# 3. Canonical Relic 1: Martelo Rúnico (Turn 1 Melee Burst)
# ==============================================================================

func test_relic_martelo_runico_applies_bonus_only_on_first_attack() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")

	# Act 1: Primeiro ataque Melee do combate
	var attack1: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 6, "contundente", false)

	# Assert 1
	assert_eq(attack1["bonus_damage"], 3, "Primeiro ataque recebe +3 de bônus")
	assert_eq(attack1["final_damage"], 9, "Dano total é 6 + 3 = 9")

	# Act 2: Segundo ataque Melee no mesmo combate
	var attack2: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 6, "contundente", false)

	# Assert 2
	assert_eq(attack2["bonus_damage"], 0, "Segundo ataque não recebe bônus")
	assert_eq(attack2["final_damage"], 6, "Dano normal")

	# Act 3: Novo combate (reset_all_combat_states)
	_manager.reset_all_combat_states()
	var attack3: Dictionary = _manager.modify_attack_damage("aquele", "larva_carniceira", true, 5, "cortante", false)
	assert_eq(attack3["bonus_damage"], 3, "Bônus restaurado no novo combate")

# ==============================================================================
# 4. Canonical Relic 2: Escudo Ancestral (Damage Reduction)
# ==============================================================================

func test_relic_escudo_ancestral_reduces_damage_with_min_clamp() -> void:
	# Arrange
	_manager.register_relic("escudo_ancestral")

	# Act 1: Dano superior a 1
	var dmg1: Dictionary = _manager.modify_incoming_damage("aquele", true, 8, 30, 30)

	# Assert 1
	assert_eq(dmg1["damage_reduction"], 1, "Redução de 1 ponto")
	assert_eq(dmg1["final_damage"], 7, "8 reduzido para 7")

	# Act 2: Dano exatamente 1 (não pode ser reduzido a 0)
	var dmg2: Dictionary = _manager.modify_incoming_damage("aquele", true, 1, 20, 30)
	assert_eq(dmg2["final_damage"], 1, "Piso de 1 dano preservado")

	# Act 3: Inimigo sofrendo dano (is_hero == false não reduz)
	var dmg_enemy: Dictionary = _manager.modify_incoming_damage("larva", false, 5, 10, 10)
	assert_eq(dmg_enemy["damage_reduction"], 0, "Inimigos não se beneficiam do escudo")

# ==============================================================================
# 5. Canonical Relic 3: Bolsa do Mercador (Victory Gold Bonus)
# ==============================================================================

func test_relic_bolsa_do_mercador_awards_extra_gold() -> void:
	# Arrange
	_manager.register_relic("bolsa_do_mercador")
	var initial_gold: int = _state.gold

	# Act
	var rewards: Dictionary = _manager.modify_combat_victory_rewards({"gold": 15})

	# Assert
	assert_eq(rewards["gold"], 25, "15 base + 10 bônus = 25")
	assert_eq(_state.gold, initial_gold, "RunState.gold NÃO deve ser alterado antes da coleta da recompensa")

	# Downstream application (e.g. RewardModal collecting the reward)
	_state.add_gold(rewards["gold"])
	assert_eq(_state.gold, initial_gold + 25, "Recompensa coletada totaliza exatamente +25 ouro (sem duplicação)")

# ==============================================================================
# 6. Canonical Relic 4: Amuleto de Âmbar (Campfire Heal Boost)
# ==============================================================================

func test_relic_amuleto_ambar_boosts_campfire_healing() -> void:
	# Arrange
	_manager.register_relic("amuleto_ambar")

	# Act
	var heal_pct: float = _manager.modify_campfire_heal(0.30)

	# Assert
	assert_almost_eq(heal_pct, 0.45, 0.001, "Cura da fogueira aumentada para 45%")

# ==============================================================================
# 7. Canonical Relic 5: Dente da Viúva (Crit Poison + Leech)
# ==============================================================================

func test_relic_dente_da_viuva_triggers_on_crit_only() -> void:
	# Arrange
	_manager.register_relic("dente_da_viuva")
	_state.damage_hero("aquele", 10) # 20 / 30 HP

	# Act 1: Ataque normal (sem crit)
	var normal_att: Dictionary = _manager.modify_attack_damage("aquele", "boss", true, 10, "cortante", false)
	assert_eq(normal_att["bonus_damage"], 0)
	assert_eq(_state.hero_hp["aquele"], 20, "Sem cura no golpe normal")

	# Act 2: Acerto crítico
	var crit_att: Dictionary = _manager.modify_attack_damage("aquele", "boss", true, 10, "cortante", true)
	assert_eq(crit_att["bonus_damage"], 4, "+4 de dano")
	assert_eq(crit_att["bonus_type"], "veneno", "Dano de veneno")
	assert_eq(_state.hero_hp["aquele"], 22, "Curou 2 PV do herói atacante")

# ==============================================================================
# 8. Canonical Relics 6, 7 & 8: Tocha, Óleo e Frasco de Feromônio
# ==============================================================================

func test_relic_tocha_e_oleo_alquimico() -> void:
	# Arrange
	_manager.register_relic("tocha_eterna")
	_manager.register_relic("oleo_alquimico")

	# Act: Ataque que causa dano de fogo
	var att: Dictionary = _manager.modify_attack_damage("aquele", "casulo", true, 8, "fogo", false)

	# Assert
	# tocha_eterna (+2) + oleo_alquimico (+1) = +3
	assert_eq(att["bonus_damage"], 3, "Bônus somado de tocha e óleo")

func test_relic_frasco_feromonio_negates_first_debuff() -> void:
	# Arrange
	_manager.register_relic("frasco_feromonio")
	var relic: RelicData = _manager.get_relic("frasco_feromonio")

	# Act 1: Primeira aplicação de veneno
	var res1: Dictionary = relic.on_status_applied("aquele", "poisoned", 3, _state)
	assert_true(res1.get("cancel_status", false), "Primeiro status cancelado")

	# Act 2: Segunda aplicação no mesmo combate
	var res2: Dictionary = relic.on_status_applied("aquele", "stunned", 1, _state)
	assert_false(res2.get("cancel_status", false), "Segundo status NÃO cancelado")

# ==============================================================================
# 9. Canonical Relics 9 & 10: Coroa de Quitina e Relógio da Forja
# ==============================================================================

func test_relic_coroa_quitina_death_save_advantage_and_crit_mitigation() -> void:
	# Arrange
	_manager.register_relic("coroa_quitina")
	var relic: RelicData = _manager.get_relic("coroa_quitina")

	# Act 1: Primeiro Death Save
	var ds1: Dictionary = relic.on_death_save_rolled("aquele", 12, 1, 0, "INCONSCIENTE", _state)
	assert_true(ds1.get("force_advantage", false), "Força vantagem no primeiro save")

	# Act 2: Falha crítica (1)
	var ds_crit: Dictionary = relic.on_death_save_rolled("aquele", 1, 1, 1, "INCONSCIENTE", _state)
	assert_true(ds_crit.get("mitigate_crit_fail", false), "Mitiga falha crítica de 2 para 1 falha")

func test_relic_relogio_da_forja_discount_and_node_gold() -> void:
	# Arrange
	_manager.register_relic("relogio_da_forja")
	var start_gold: int = _state.gold

	# Act 1: Desconto de 20%
	var cost100: int = _manager.modify_forge_cost("carta", 100)
	var cost75: int = _manager.modify_forge_cost("relic", 75)

	# Assert 1
	assert_eq(cost100, 80, "100g com 20% desconto = 80g")
	assert_eq(cost75, 60, "75g com 20% desconto = 60g")

	# Act 2: Entrada no nó FORGE
	var forge_node: RunNode = RunNode.new(50, 1, 3, 0, RunNode.NodeType.FORGE)
	_state.map.add_node(forge_node)
	_state.current_node_id = 50
	_state.node_entered.emit(forge_node)

	# Assert 2: +5 de ouro ao entrar na forja
	assert_eq(_state.gold, start_gold + 5, "+5 ouro ao entrar no nó de Forja")

func test_relic_frasco_feromonio_ignores_enemy_debuffs() -> void:
	# Arrange
	_manager.register_relic("frasco_feromonio")
	var relic: RelicData = _manager.get_relic("frasco_feromonio")

	# Act 1: Status aplicado em inimigo ("larva_carniceira" não está em _state.heroes)
	var enemy_res: Dictionary = relic.on_status_applied("larva_carniceira", "poisoned", 3, _state)

	# Assert 1: Inimigo NÃO deve ser protegido e a carga da relíquia NÃO deve ser gasta
	assert_false(enemy_res.get("cancel_status", false), "Inimigos não devem ter status cancelado pela relíquia")
	assert_eq(relic.counter, 0, "Carga permanece intacta após debuff em inimigo")

	# Act 2: Heroi sofre debuff em seguida
	var hero_res: Dictionary = relic.on_status_applied("aquele", "poisoned", 3, _state)
	assert_true(hero_res.get("cancel_status", false), "Herói é protegido pelo feromônio")
	assert_eq(relic.counter, 1, "Carga é consumida pelo herói")

func test_relic_frasco_feromonio_cancels_portuguese_condition_names() -> void:
	# Arrange
	_manager.register_relic("frasco_feromonio")
	var relic: RelicData = _manager.get_relic("frasco_feromonio")

	# Act: Debuff com nome em português "atordoado"
	var res: Dictionary = relic.on_status_applied("aquele", "atordoado", 1, _state)
	assert_true(res.get("cancel_status", false), "Nome em português 'atordoado' deve ser cancelado")

func test_relic_manager_unregister_by_alias_and_deactivates() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")
	var relic: RelicData = _manager.get_relic("martelo_runico")
	assert_true(relic.is_active)

	# Act: Unregister using prefixed alias
	var ok: bool = _manager.unregister_relic("reliquia_martelo_runico")

	# Assert
	assert_true(ok, "Desregistro via alias com prefixo deve ser bem-sucedido")
	assert_false(_manager.has_relic("martelo_runico"), "Relíquia removida do gerenciador")
	assert_false(_state.has_relic("martelo_runico"), "Relíquia removida do RunState")
	assert_false(relic.is_active, "Instância da relíquia é desativada")

func test_relic_manager_sync_prunes_removed_relics() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")
	_manager.register_relic("escudo_ancestral")
	assert_eq(_manager.get_relic_count(), 2)

	# Act: Remove relic directly from RunState (e.g. by event / curse)
	_state.remove_relic("martelo_runico")
	_manager.sync_from_run_state()

	# Assert: RelicManager must prune the orphan active relic
	assert_eq(_manager.get_relic_count(), 1, "Apenas a relíquia restante deve estar ativa")
	assert_false(_manager.has_relic("martelo_runico"), "Relíquia expurgada não deve estar ativa")
	assert_true(_manager.has_relic("escudo_ancestral"), "Relíquia preservada permanece ativa")

func test_relic_manager_rejects_alias_duplicate_registration() -> void:
	# Arrange
	var ok1: bool = _manager.register_relic("martelo_runico")
	assert_true(ok1, "Primeiro registro deve suceder")

	# Act: Tentativa de registrar duplicata com alias
	var ok2: bool = _manager.register_relic("reliquia_martelo_runico")

	# Assert
	assert_false(ok2, "Registro duplicado com prefixo deve ser estritamente rejeitado")
	assert_eq(_manager.get_relic_count(), 1, "Permanece exatamente 1 relíquia ativa")
