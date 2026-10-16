# res://test/unit/test_relic_system_remediation_additions.gd
# Proposed unit test additions and updates for Milestone M3 Relic Remediation.

func test_relic_bolsa_do_mercador_awards_extra_gold() -> void:
	# Arrange
	_manager.register_relic("bolsa_do_mercador")
	var initial_gold: int = _state.gold

	# Act
	var rewards: Dictionary = _manager.modify_combat_victory_rewards({"gold": 15})

	# Assert
	assert_eq(rewards["gold"], 25, "15 base + 10 bônus = 25")
	assert_eq(_state.gold, initial_gold, "RunState.gold NÃO deve ser alterado antes da coleta da recompensa")

	# Downstream application (e.g. RewardModal or RunCombatBridge collecting the reward)
	_state.add_gold(rewards["gold"])
	assert_eq(_state.gold, initial_gold + 25, "Recompensa coletada totaliza exatamente +25 ouro (sem duplicação)")

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
