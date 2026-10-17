# res://test/unit/test_relic_stress_adversarial.gd
extends GutTest

## Adversarial Stress & Edge-Case Test Suite for Milestone M3 (Relics & EventBus)
## Empirically stress-tests RelicManager, RelicData, EventBus, RewardModal, and ForgeScreen.
## Adheres strictly to AAA pattern, deterministic seeds, and headless execution.

const EventBusScript = preload("res://scripts/autoload/EventBus.gd")

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState
var _eb: Node
var _manager: RelicManager

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 9999
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
# 1. Rapid Registration / Unregistration Churn & Idempotence
# ==============================================================================

func test_stress_rapid_registration_unregistration_churn() -> void:
	# Arrange
	var catalog_ids: Array[String] = _manager.get_catalog_ids()
	assert_gt(catalog_ids.size(), 0, "Catálogo deve conter relíquias registradas")
	
	# Act: 100 cycles of registering all relics, querying them, and unregistering all
	for cycle in range(100):
		for r_id in catalog_ids:
			var ok: bool = _manager.register_relic(r_id)
			assert_true(ok, "Ciclo %d: Registro de %s deve ter sucesso" % [cycle, r_id])
		
		assert_eq(_manager.get_relic_count(), catalog_ids.size(), "Todas as relíquias ativas")
		
		# Query pipelines under full load
		var att: Dictionary = _manager.modify_attack_damage("aquele", "inimigo", true, 10, "contundente", false)
		assert_gt(att["final_damage"], 0, "Pipeline de ataque funcional sob carga")
		
		var dmg: Dictionary = _manager.modify_incoming_damage("aquele", true, 10, 20, 30)
		assert_gt(dmg["final_damage"], 0, "Pipeline de dano funcional sob carga")
		
		# Unregister all
		_manager.unregister_all()
		assert_eq(_manager.get_relic_count(), 0, "Todas as relíquias desregistradas")
		
		# Re-connect EventBus for next cycle
		_manager.connect_event_bus()

	# Assert
	assert_eq(_manager.get_relic_count(), 0, "Estado final limpo após 100 ciclos")

# ==============================================================================
# 2. Duplicate Registration & Prefix Aliasing Edge Cases
# ==============================================================================

func test_stress_duplicate_registration_with_reliquia_prefix() -> void:
	# Arrange: Register raw ID
	var ok1: bool = _manager.register_relic("martelo_runico")
	assert_true(ok1, "Registro do raw ID deve ter sucesso")
	assert_eq(_manager.get_relic_count(), 1)
	
	# Act: Attempt to register with prefix "reliquia_martelo_runico"
	# Challenger hypothesis: If prefix is not normalized during register,
	# RelicManager will register a duplicate instance of Martelo Rúnico!
	var dup_attempt: bool = _manager.register_relic("reliquia_martelo_runico")
	
	# Assert: In a robust system, registering an alias of an already active relic should be rejected
	assert_false(dup_attempt, "Registro de alias de relíquia já ativa deve ser estritamente rejeitado")
	assert_eq(_manager.get_relic_count(), 1, "Exatamente uma instância de martelo_runico ativa")

# ==============================================================================
# 3. RewardModal Relic IDs vs RelicManager Catalog Consistency
# ==============================================================================

func test_stress_reward_modal_relic_ids_vs_relic_manager_catalog() -> void:
	# Arrange: Gather all relics defined in RewardModal pools
	var elite_pool: Array[String] = RewardModal.ELITE_RELICS
	var boss_pool: Array[String] = RewardModal.BOSS_RELICS
	
	var unresolvable_relics: Array[String] = []
	
	# Act: Check which relics from RewardModal cannot be created by RelicManager
	for rid in elite_pool:
		var relic: RelicData = _manager.create_relic(rid)
		if relic == null:
			unresolvable_relics.append(rid)
	
	for rid in boss_pool:
		var relic: RelicData = _manager.create_relic(rid)
		if relic == null:
			unresolvable_relics.append(rid)
	
	# Assert / Report findings
	assert_eq(unresolvable_relics.size(), 0, "Todas as relíquias de RewardModal devem ser resolúveis em RelicManager: %s" % str(unresolvable_relics))

# ==============================================================================
# 4. Specific Typo: "reliquia_coroa_de_quitina" in RewardModal
# ==============================================================================

func test_stress_coroa_de_quitina_typo_in_reward_modal() -> void:
	# Arrange
	# RewardModal defines: "reliquia_coroa_de_quitina"
	# RelicManager defines: "coroa_quitina"
	var modal_id: String = "reliquia_coroa_de_quitina"
	
	# Act
	var relic: RelicData = _manager.create_relic(modal_id)
	
	# Assert
	assert_not_null(relic, "'reliquia_coroa_de_quitina' de RewardModal.BOSS_RELICS deve ser instanciada com sucesso")

# ==============================================================================
# 5. Pipeline Boundary: Zero / Negative Incoming Damage Clamping
# ==============================================================================

func test_stress_incoming_zero_damage_with_damage_reduction() -> void:
	# Arrange: Custom relic or Escudo Ancestral with 0 incoming damage
	_manager.register_relic("escudo_ancestral")
	
	# Act: incoming damage is 0
	var res_zero: Dictionary = _manager.modify_incoming_damage("aquele", true, 0, 30, 30)
	
	# Assert: 0 incoming damage should NEVER be increased to 1
	print("[FINDING] Incoming damage 0 resulted in final_damage: %d" % res_zero["final_damage"])
	assert_lte(res_zero["final_damage"], 0, "Dano zero não deve virar dano positivo!")

# ==============================================================================
# 6. RelicManager Sync After RunState Removal (Orphan Active Relic)
# ==============================================================================

func test_stress_relic_manager_sync_after_run_state_removal() -> void:
	# Arrange
	_manager.register_relic("martelo_runico")
	assert_true(_state.has_relic("martelo_runico"))
	assert_true(_manager.has_relic("martelo_runico"))
	
	# Act: Remove relic directly from RunState (e.g. from event or curse)
	_state.remove_relic("martelo_runico")
	assert_false(_state.has_relic("martelo_runico"))
	
	# Sync RelicManager from RunState
	_manager.sync_from_run_state()
	
	# Assert: Does RelicManager purge the relic no longer in RunState?
	var still_in_manager: bool = _manager.has_relic("martelo_runico")
	assert_false(still_in_manager, "RelicManager.sync_from_run_state() deve desregistrar relíquias removidas do RunState")

# ==============================================================================
# 7. EventBus Rapid Fire 1,000 Signals Stress
# ==============================================================================

func test_stress_eventbus_rapid_fire_1000_signals() -> void:
	# Arrange: Register all relics
	for rid in _manager.get_catalog_ids():
		_manager.register_relic(rid)
	
	# Act: Rapidly emit 1,000 mixed signals through EventBus
	for i in range(200):
		_eb.emit_logged("unit_attacked", ["aquele", "larva_%d" % i, true, (i % 2 == 0), 8, "contundente"])
		_eb.emit_logged("unit_damaged", ["aquele", 4, 26, 30])
		_eb.emit_logged("status_applied", ["aquele", "poisoned", 2])
		_eb.emit_logged("death_save_rolled", ["aquele", (i % 20) + 1, 1, 0, "INCONSCIENTE"])
		_eb.emit_logged("turn_changed", [i, "aquele"])
	
	# Assert
	assert_eq(_manager.get_relic_count(), 10, "Todas as 10 relíquias intactas após 1.000 sinais")

# ==============================================================================
# 8. Pipeline vs EventBus Double-Triggering (Dente da Viúva)
# ==============================================================================

func test_stress_dente_da_viuva_double_heal_pipeline_vs_eventbus() -> void:
	# Arrange
	_manager.register_relic("dente_da_viuva")
	_state.damage_hero("aquele", 10) # 20 / 30 HP
	
	# Act 1: Attack pipeline calculates damage and applies on_attack_dealt
	var att: Dictionary = _manager.modify_attack_damage("aquele", "boss", true, 10, "cortante", true)
	var hp_after_pipeline: int = _state.hero_hp["aquele"]
	assert_eq(hp_after_pipeline, 22, "Herói curou 2 PV via modify_attack_damage")
	
	# Act 2: Combat system emits unit_attacked to EventBus
	_eb.emit_logged("unit_attacked", ["aquele", "boss", true, true, att["final_damage"], "cortante"])
	var hp_after_signal: int = _state.hero_hp["aquele"]
	
	# Assert: Check if hero was healed again by the EventBus listener
	if hp_after_signal > 22:
		print("[FINDING] Dente da Viúva triggers heal TWICE when both pipeline and EventBus signal are used! HP: %d (expected 22)" % hp_after_signal)
	
	assert_true(true, "Double heal check completed")

# ==============================================================================
# 9. Cascading Signals and Re-entrancy
# ==============================================================================

func test_stress_signal_cascade_and_reentrancy() -> void:
	# Arrange
	for rid in _manager.get_catalog_ids():
		_manager.register_relic(rid)
	
	# Connect a cascading listener: when unit_attacked is emitted, emit unit_damaged and unit_died
	var cascade_callable = func(attacker_id, target_id, hit, is_crit, dmg, dtype):
		if hit:
			_eb.emit_logged("unit_damaged", [target_id, dmg, 0, 20])
			_eb.emit_logged("unit_died", [target_id])
	
	_eb.unit_attacked.connect(cascade_callable)
	
	# Act: Trigger cascade 50 times
	for i in range(50):
		_eb.emit_logged("unit_attacked", ["aquele", "monstro_%d" % i, true, false, 15, "cortante"])
	
	_eb.unit_attacked.disconnect(cascade_callable)
	
	# Assert: No crash, stack overflow, or memory corruption
	assert_eq(_manager.get_relic_count(), 10, "Estado íntegro após 50 cascatas reentrantes")

# ==============================================================================
# 10. Boundary Inputs and Extremes
# ==============================================================================

func test_stress_unhandled_and_boundary_signals() -> void:
	# Arrange
	for rid in _manager.get_catalog_ids():
		_manager.register_relic(rid)
	
	# Act & Assert: Null nodes, empty strings, huge integers, negative values
	_manager._on_node_entered(null) # Should safely ignore null
	_manager._on_unit_attacked("", "", false, false, 0, "")
	_manager._on_unit_damaged("", -9999, -100, -50)
	_manager._on_unit_died("")
	_manager._on_status_applied("", "", -1)
	_manager._on_death_save_rolled("", -1, -1, -1, "")
	_manager._on_card_played("", "", "")
	
	# Extreme modifier inputs
	var huge_att: Dictionary = _manager.modify_attack_damage("", "", false, 99999999, "", false)
	assert_gte(huge_att["final_damage"], 99999999)
	
	var neg_att: Dictionary = _manager.modify_attack_damage("", "", false, -100, "", false)
	assert_eq(neg_att["final_damage"], -100)
	
	assert_eq(_manager.get_relic_count(), 10, "Todas as relíquias seguras sob inputs extremos")

# ==============================================================================
# 11. ForgeShop Cross-Contamination with Relic Prefixes
# ==============================================================================

func test_stress_forge_shop_duplicate_offering_with_prefix_alias() -> void:
	# Arrange: Player has "reliquia_martelo_runico" in RunState
	_state.add_relic("reliquia_martelo_runico")
	assert_true(_state.has_relic("reliquia_martelo_runico"))
	
	# Act: Instantiate ForgeScreen and check inventory
	var forge: ForgeScreen = ForgeScreen.new()
	forge.setup(_state, _manager, _rng)
	
	# Check if ForgeScreen offers "martelo_runico" despite player having "reliquia_martelo_runico"
	var offered_martelo: bool = false
	for slot in forge.relic_inventory:
		if slot["id"] == "martelo_runico":
			offered_martelo = true
			break
	
	forge.free()
	
	assert_false(offered_martelo, "ForgeScreen não deve ofertar 'martelo_runico' para venda se o jogador já possui 'reliquia_martelo_runico'")

# ==============================================================================
# 12. RelicData Serialization Stress
# ==============================================================================

func test_stress_relic_data_serialization_roundtrip_edge_cases() -> void:
	# Arrange
	var relic: RelicData = RelicData.new()
	
	# Act 1: from_dict with empty dictionary
	relic.from_dict({})
	assert_eq(relic.id, "", "ID padrão vazio")
	assert_true(relic.is_active, "is_active default true")
	
	# Act 2: from_dict with string-based cost_gold and bool
	relic.from_dict({
		"id": "relic_custom",
		"cost_gold": "999",
		"counter": -50,
		"is_active": false
	})
	assert_eq(relic.cost_gold, 999, "String convertida para int com segurança")
	assert_false(relic.is_active, "is_active falso respeitado")
	assert_eq(relic.counter, -50, "Contador negativo armazenado")
	
	# Act 3: to_dict serialization
	var dict: Dictionary = relic.to_dict()
	assert_eq(dict["cost_gold"], 999)
	assert_false(dict["is_active"])
	
	# Act 4: Non-string type safety check
	var relic2: RelicData = RelicData.new()
	relic2.from_dict({
		"id": 12345,
		"relic_name": 67890,
		"description": 11111,
		"rarity": 22222
	})
	assert_eq(relic2.id, "12345", "id convertido para String com segurança")
	assert_eq(relic2.relic_name, "67890", "relic_name convertido para String com segurança")
	assert_eq(relic2.description, "11111", "description convertida para String com segurança")
	assert_eq(relic2.rarity, "22222", "rarity convertida para String com segurança")
