# res://test/unit/test_isectum_castes.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Milestone 3:
## 24 Castas Isectum & Decks de Ameaça (Cerco da Fortaleza contra Isectum).
## Tests:
##  1. IsectumCasteData Custom Resource typed fields and mechanics
##  2. IsectumCastes catalog: 24 canonical castes, traits, and archetype queries
##  3. ThreatDeck wave generator, budget scaling, and 4 spawn zones
##  4. Draw pile, discard pile, active threat queue, and reshuffle cycles
##  5. Cartas de Runa e Defesa counter-reactions against threat cards
##  6. Signals, boundary conditions, and leak-free teardown

var _deck: ThreatDeck = null

func before_each() -> void:
	_deck = ThreatDeck.new()

func after_each() -> void:
	if _deck != null:
		_deck.reset()
		_deck = null

# ==============================================================================
# SECTION 1: IsectumCasteData Typed Fields & Resource Behavior
# ==============================================================================

func test_isectum_caste_data_default_properties() -> void:
	# Arrange & Act
	var caste: IsectumCasteData = IsectumCasteData.new()

	# Assert
	assert_not_null(caste, "IsectumCasteData resource instantiated")
	assert_eq(caste.id, "")
	assert_eq(caste.caste_name, "")
	assert_eq(caste.hp, 4)
	assert_eq(caste.max_hp, 4)
	assert_false(caste.is_brutamontes)
	assert_false(caste.is_infiltrator)
	assert_false(caste.is_catapult)
	assert_false(caste.is_flyer)
	assert_eq(caste.speed, 3)
	assert_eq(caste.attack_dice, 2)
	assert_eq(caste.attack_range, 1)
	assert_eq(caste.trait_id, "")
	assert_eq(caste.threat_cost, 1)

func test_isectum_caste_data_typed_fields_integrity() -> void:
	# Arrange
	var caste: IsectumCasteData = IsectumCasteData.new()

	# Act
	caste.id = "teste_caste"
	caste.caste_name = "Casta Teste"
	caste.hp = 10
	caste.max_hp = 10
	caste.is_brutamontes = true
	caste.is_infiltrator = true
	caste.is_catapult = true
	caste.is_flyer = true
	caste.speed = 5
	caste.attack_dice = 4
	caste.attack_range = 3
	caste.trait_id = "traco_teste"
	caste.threat_cost = 5

	# Assert
	assert_eq(caste.id, "teste_caste")
	assert_eq(caste.caste_name, "Casta Teste")
	assert_eq(caste.name, "Casta Teste", "name property kept in sync")
	assert_eq(caste.hp, 10)
	assert_eq(caste.max_hp, 10)
	assert_true(caste.is_brutamontes)
	assert_true(caste.is_infiltrator)
	assert_true(caste.is_catapult)
	assert_true(caste.is_flyer)
	assert_eq(caste.speed, 5)
	assert_eq(caste.attack_dice, 4)
	assert_eq(caste.attack_range, 3)
	assert_eq(caste.trait_id, "traco_teste")
	assert_eq(caste.threat_cost, 5)

func test_isectum_caste_data_damage_and_healing() -> void:
	# Arrange
	var caste: IsectumCasteData = IsectumCasteData.new()
	caste.max_hp = 6
	caste.hp = 6

	# Act 1: Partial damage
	var dmg_taken: int = caste.take_damage(2)

	# Assert 1
	assert_eq(dmg_taken, 2)
	assert_eq(caste.hp, 4)
	assert_true(caste.is_alive())

	# Act 2: Overkill damage (clamps to 0)
	var fatal_dmg: int = caste.take_damage(10)

	# Assert 2
	assert_eq(fatal_dmg, 4)
	assert_eq(caste.hp, 0)
	assert_false(caste.is_alive())

	# Act 3: Healing
	var healed: int = caste.heal(3)

	# Assert 3
	assert_eq(healed, 3)
	assert_eq(caste.hp, 3)
	assert_true(caste.is_alive())

	# Act 4: Overheal (clamps to max_hp)
	var over_healed: int = caste.heal(10)

	# Assert 4
	assert_eq(over_healed, 3)
	assert_eq(caste.hp, 6)

func test_isectum_caste_data_clone_independence() -> void:
	# Arrange
	var original: IsectumCasteData = IsectumCasteData.new()
	original.id = "orig_caste"
	original.caste_name = "Original"
	original.hp = 5
	original.max_hp = 5
	original.is_brutamontes = true

	# Act
	var copy_caste: IsectumCasteData = original.clone()
	copy_caste.take_damage(3)
	copy_caste.caste_name = "Modificado"

	# Assert
	assert_ne(copy_caste, original, "Clone is a distinct object")
	assert_eq(original.hp, 5, "Original HP unaffected by clone damage")
	assert_eq(copy_caste.hp, 2, "Clone HP updated")
	assert_eq(original.caste_name, "Original")
	assert_eq(copy_caste.caste_name, "Modificado")
	assert_true(copy_caste.is_brutamontes)

func test_isectum_caste_data_to_dict_serialization() -> void:
	# Arrange
	var caste: IsectumCasteData = IsectumCasteData.new()
	caste.id = "zangao_invasor"
	caste.caste_name = "Zangão Invasor"
	caste.hp = 2
	caste.max_hp = 2
	caste.is_flyer = true
	caste.threat_cost = 1

	# Act
	var d: Dictionary = caste.to_dict()

	# Assert
	assert_eq(d["id"], "zangao_invasor")
	assert_eq(d["caste_name"], "Zangão Invasor")
	assert_eq(d["hp"], 2)
	assert_true(d["is_flyer"])
	assert_eq(d["threat_cost"], 1)

# ==============================================================================
# SECTION 2: IsectumCastes Catalog (24 Canonical Castes)
# ==============================================================================

func test_all_24_canonical_castes_registered() -> void:
	# Arrange & Act
	var all_ids: Array[String] = IsectumCastes.get_all_caste_ids()
	var all_castes: Array[IsectumCasteData] = IsectumCastes.get_all_castes()

	# Assert
	assert_eq(all_ids.size(), 24, "Catalog must contain exactly 24 canonical caste IDs")
	assert_eq(all_castes.size(), 24, "Catalog must return exactly 24 caste objects")

func test_every_caste_has_valid_attributes() -> void:
	# Arrange
	var all_ids: Array[String] = IsectumCastes.get_all_caste_ids()

	# Act & Assert
	for caste_id in all_ids:
		var c: IsectumCasteData = IsectumCastes.get_caste(caste_id)
		assert_not_null(c, "Caste %s must not be null" % caste_id)
		assert_eq(c.id, caste_id, "ID matches key")
		assert_false(c.caste_name.is_empty(), "Caste name is non-empty for %s" % caste_id)
		assert_gte(c.hp, 2, "HP is at least 2 for %s" % caste_id)
		assert_gte(c.max_hp, 2, "Max HP is at least 2 for %s" % caste_id)
		assert_gte(c.speed, 1, "Speed is at least 1 for %s" % caste_id)
		assert_gte(c.attack_dice, 1, "Attack dice is at least 1 for %s" % caste_id)
		assert_gte(c.attack_range, 1, "Attack range is at least 1 for %s" % caste_id)
		assert_false(c.trait_id.is_empty(), "Trait ID is non-empty for %s" % caste_id)
		assert_gte(c.threat_cost, 1, "Threat cost is at least 1 for %s" % caste_id)
		assert_false(c.symbol.is_empty(), "Symbol is defined for %s" % caste_id)
		assert_false(c.description.is_empty(), "Description is defined for %s" % caste_id)

func test_all_24_castes_have_unique_traits() -> void:
	# Arrange
	var all_ids: Array[String] = IsectumCastes.get_all_caste_ids()
	var traits_seen: Dictionary = {}

	# Act & Assert
	for caste_id in all_ids:
		var c: IsectumCasteData = IsectumCastes.get_caste(caste_id)
		var t_id: String = c.trait_id
		assert_false(traits_seen.has(t_id), "Trait %s must be unique, duplicated by %s and %s" % [t_id, traits_seen.get(t_id, ""), caste_id])
		traits_seen[t_id] = caste_id

	assert_eq(traits_seen.size(), 24, "All 24 castes possess distinct traits")

func test_brutamontes_archetype_castes() -> void:
	# Arrange & Act
	var brutamontes: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("brutamontes")
	var ids: Array[String] = []
	for c in brutamontes:
		ids.append(c.id)

	# Assert
	assert_eq(brutamontes.size(), 2, "Besouro Rinoceronte and Colosso Isectum are Brutamontes")
	assert_true(ids.has(IsectumCastes.ID_BESOURO_RINOCERONTE))
	assert_true(ids.has(IsectumCastes.ID_COLOSSO_ISECTUM))
	for c in brutamontes:
		assert_true(c.is_brutamontes)
		assert_eq(c.hp, 3, "Brutamontes have 3 circles of HP")

func test_infiltrator_archetype_castes() -> void:
	# Arrange & Act
	var infiltrators: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("infiltrator")
	var ids: Array[String] = []
	for c in infiltrators:
		ids.append(c.id)

	# Assert
	assert_gte(infiltrators.size(), 5, "At least 5 infiltrator castes")
	assert_true(ids.has(IsectumCastes.ID_VESPA_FURTIVA))
	assert_true(ids.has(IsectumCastes.ID_TRACA_DA_RUNA))
	assert_true(ids.has(IsectumCastes.ID_ARANHA_SALTADORA))
	assert_true(ids.has(IsectumCastes.ID_BICHO_PAU_EMBOSCADOR))
	assert_true(ids.has(IsectumCastes.ID_PULGA_SALTADORA))
	for c in infiltrators:
		assert_true(c.is_infiltrator)

func test_catapult_archetype_castes() -> void:
	# Arrange & Act
	var catapults: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("catapult")
	var ids: Array[String] = []
	for c in catapults:
		ids.append(c.id)

	# Assert
	assert_eq(catapults.size(), 2, "Libélula Bombardeira and Colosso Isectum are Catapults")
	assert_true(ids.has(IsectumCastes.ID_LIBELULA_BOMBARDEIRA))
	assert_true(ids.has(IsectumCastes.ID_COLOSSO_ISECTUM))
	for c in catapults:
		assert_true(c.is_catapult)

func test_flyer_archetype_castes() -> void:
	# Arrange & Act
	var flyers: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("flyer")
	var ids: Array[String] = []
	for c in flyers:
		ids.append(c.id)

	# Assert
	assert_gte(flyers.size(), 6, "At least 6 flyer castes")
	assert_true(ids.has(IsectumCastes.ID_ZANGAO_INVASOR))
	assert_true(ids.has(IsectumCastes.ID_VESPA_FURTIVA))
	assert_true(ids.has(IsectumCastes.ID_TRACA_DA_RUNA))
	assert_true(ids.has(IsectumCastes.ID_VAGALUME_CEGO))
	assert_true(ids.has(IsectumCastes.ID_LIBELULA_BOMBARDEIRA))
	assert_true(ids.has(IsectumCastes.ID_RAINHA_DO_ENXAME))
	for c in flyers:
		assert_true(c.is_flyer)

func test_boss_archetype_castes() -> void:
	# Arrange & Act
	var bosses: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("boss")
	var ids: Array[String] = []
	for c in bosses:
		ids.append(c.id)

	# Assert
	assert_eq(bosses.size(), 2, "Rainha do Enxame and Colosso Isectum are bosses")
	assert_true(ids.has(IsectumCastes.ID_RAINHA_DO_ENXAME))
	assert_true(ids.has(IsectumCastes.ID_COLOSSO_ISECTUM))
	for c in bosses:
		assert_true(c.is_boss)

func test_archetype_query_case_insensitivity_and_aliases() -> void:
	# Arrange & Act
	var brut_lower: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("brutamontes")
	var brut_upper: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("BRUTAMONTES")
	var infilt_pt: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("infiltrador")
	var catap_pt: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("catapulta")
	var flyer_pt: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("voador")
	var ranged: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("ranged")
	var melee: Array[IsectumCasteData] = IsectumCastes.get_castes_by_archetype("melee")

	# Assert
	assert_eq(brut_lower.size(), brut_upper.size(), "Case-insensitive query matches")
	assert_eq(infilt_pt.size(), 5, "Infiltrador PT-BR alias works")
	assert_eq(catap_pt.size(), 2, "Catapulta PT-BR alias works")
	assert_gte(flyer_pt.size(), 6, "Voador PT-BR alias works")
	assert_gt(ranged.size(), 0, "Ranged castes exist")
	assert_gt(melee.size(), 0, "Melee castes exist")

func test_create_instance_returns_independent_instance() -> void:
	# Arrange & Act
	var inst1: IsectumCasteData = IsectumCastes.create_instance(IsectumCastes.ID_SOLDADO_MANDIBULA)
	var inst2: IsectumCasteData = IsectumCastes.create_instance(IsectumCastes.ID_SOLDADO_MANDIBULA)

	# Assert
	assert_not_null(inst1)
	assert_not_null(inst2)
	assert_ne(inst1, inst2, "Instances must be separate objects")
	inst1.take_damage(2)
	assert_eq(inst1.hp, 2)
	assert_eq(inst2.hp, 4, "Instance 2 remains unhurt")

func test_caste_aliases_backward_compatibility() -> void:
	# Arrange
	var legacy_id = "vespa_cacadora"

	# Act
	var c = IsectumCastes.get_caste(legacy_id)
	var exists = IsectumCastes.has_caste(legacy_id)

	# Assert
	assert_not_null(c, "Legacy alias vespa_cacadora resolves to Vespa Furtiva")
	assert_true(exists)
	assert_eq(c.id, IsectumCastes.ID_VESPA_FURTIVA)

func test_nonexistent_caste_query_returns_null() -> void:
	# Arrange & Act
	var c_empty = IsectumCastes.get_caste("")
	var c_bad = IsectumCastes.get_caste("dragao_fantasma_xyz")
	var exists = IsectumCastes.has_caste("dragao_fantasma_xyz")

	# Assert
	assert_null(c_empty)
	assert_null(c_bad)
	assert_false(exists)

# ==============================================================================
# SECTION 3: ThreatDeck Wave Generation & 4 Spawn Zones
# ==============================================================================

func test_threat_deck_initialization() -> void:
	# Assert
	assert_not_null(_deck)
	assert_eq(_deck.draw_pile.size(), 0)
	assert_eq(_deck.discard_pile.size(), 0)
	assert_eq(_deck.active_threats.size(), 0)
	assert_eq(_deck.current_round, 1)

func test_wave_generation_early_rounds() -> void:
	# Arrange & Act
	var wave: Array[Dictionary] = _deck.generate_wave(1, 1.0)

	# Assert
	assert_gt(wave.size(), 0, "Wave must have at least one spawn threat")
	for threat in wave:
		assert_eq(threat["card_type"], ThreatDeck.TYPE_SPAWN_WAVE)
		assert_false(threat["caste_id"].is_empty())
		assert_gt(threat["count"], 0)
		assert_true(ThreatDeck.ALL_SPAWN_ZONES.has(threat["target_zone"]), "Zone %s must be one of the 4 spawn zones" % threat["target_zone"])
		assert_eq(threat["status"], ThreatDeck.STATUS_ACTIVE)

func test_wave_generation_uses_all_four_spawn_zones() -> void:
	# Arrange
	var zones_hit: Dictionary = {}

	# Act: generate waves across 4 consecutive rounds
	for r in range(1, 5):
		var wave: Array[Dictionary] = _deck.generate_wave(r, 1.0)
		for t in wave:
			zones_hit[t["target_zone"]] = true

	# Assert
	assert_true(zones_hit.has(ThreatDeck.ZONE_SPAWN_NORTE), "Northern spawn zone targeted")
	assert_true(zones_hit.has(ThreatDeck.ZONE_SPAWN_SUL), "Southern spawn zone targeted")
	assert_true(zones_hit.has(ThreatDeck.ZONE_SPAWN_LESTE), "Eastern spawn zone targeted")
	assert_true(zones_hit.has(ThreatDeck.ZONE_SPAWN_OESTE), "Western spawn zone targeted")

func test_wave_generation_scaling_with_difficulty() -> void:
	# Arrange
	var d_easy: ThreatDeck = ThreatDeck.new()
	var d_hard: ThreatDeck = ThreatDeck.new()

	# Act
	var wave_easy: Array[Dictionary] = d_easy.generate_wave(4, 0.5)
	var wave_hard: Array[Dictionary] = d_hard.generate_wave(4, 2.0)

	var total_cost_easy: int = 0
	for t in wave_easy:
		total_cost_easy += int(t.get("threat_cost", 1))

	var total_cost_hard: int = 0
	for t in wave_hard:
		total_cost_hard += int(t.get("threat_cost", 1))

	# Assert
	assert_gt(total_cost_hard, total_cost_easy, "Hard difficulty generates significantly higher threat cost")

func test_boss_wave_generation_in_advanced_rounds() -> void:
	# Arrange
	var round_num = 5

	# Act
	var wave: Array[Dictionary] = _deck.generate_wave(round_num, 1.0)
	var has_boss: bool = false
	for t in wave:
		if t["card_type"] == ThreatDeck.TYPE_BOSS_ASSAULT:
			has_boss = true
			var c = IsectumCastes.get_caste(t["caste_id"])
			assert_not_null(c)
			assert_true(c.is_boss, "Spawned boss caste must have is_boss == true")

	# Assert
	assert_true(has_boss, "Round 5 must generate a Boss Assault threat")

func test_forced_waves_deterministic_injection() -> void:
	# Arrange
	var custom_wave: Array[Dictionary] = [
		{
			"id": "forced_1",
			"card_type": ThreatDeck.TYPE_SPAWN_WAVE,
			"title": "Horda Forçada",
			"caste_id": IsectumCastes.ID_ZANGAO_INVASOR,
			"count": 5,
			"target_zone": ThreatDeck.ZONE_SPAWN_NORTE,
			"threat_cost": 5,
			"status": ThreatDeck.STATUS_ACTIVE
		}
	]
	_deck.set_forced_waves(custom_wave)

	# Act
	var generated: Array[Dictionary] = _deck.generate_wave(1)

	# Assert
	assert_eq(generated.size(), 1)
	assert_eq(generated[0]["id"], "forced_1")
	assert_eq(generated[0]["count"], 5)
	assert_eq(generated[0]["caste_id"], IsectumCastes.ID_ZANGAO_INVASOR)

# ==============================================================================
# SECTION 4: Draw Pile, Discard Pile & Active Threat Queue
# ==============================================================================

func test_build_standard_deck_populates_draw_pile() -> void:
	# Arrange & Act
	_deck.build_standard_deck(1, 1.0)

	# Assert
	assert_gt(_deck.draw_pile.size(), 4, "Standard deck populated with spawns and events")
	assert_eq(_deck.discard_pile.size(), 0)
	assert_eq(_deck.active_threats.size(), 0)

func test_draw_threat_moves_card_to_active_queue() -> void:
	# Arrange
	_deck.build_standard_deck(1, 1.0)
	var init_draw_size: int = _deck.draw_pile.size()

	# Act
	var drawn: Dictionary = _deck.draw_threat()

	# Assert
	assert_false(drawn.is_empty())
	assert_eq(drawn["status"], ThreatDeck.STATUS_ACTIVE)
	assert_eq(_deck.draw_pile.size(), init_draw_size - 1)
	assert_eq(_deck.active_threats.size(), 1)
	assert_eq(_deck.active_threats[0]["id"], drawn["id"])

func test_draw_threat_empty_deck_triggers_reshuffle_from_discard() -> void:
	# Arrange
	_deck.draw_pile.clear()
	_deck.discard_pile.append({
		"id": "discarded_1",
		"card_type": ThreatDeck.TYPE_SPAWN_WAVE,
		"caste_id": IsectumCastes.ID_ZANGAO_INVASOR,
		"status": ThreatDeck.STATUS_DISCARDED
	})

	# Act: draw from empty draw pile with 1 discarded card
	var drawn: Dictionary = _deck.draw_threat()

	# Assert
	assert_false(drawn.is_empty())
	assert_eq(drawn["id"], "discarded_1")
	assert_eq(drawn["status"], ThreatDeck.STATUS_ACTIVE)
	assert_eq(_deck.discard_pile.size(), 0, "Discard pile emptied by reshuffle")
	assert_eq(_deck.active_threats.size(), 1)

func test_resolve_threat_moves_to_discard_pile() -> void:
	# Arrange
	_deck.build_standard_deck(1, 1.0)
	var drawn: Dictionary = _deck.draw_threat()
	var threat_id: String = drawn["id"]

	# Act
	var success: bool = _deck.resolve_threat(threat_id)

	# Assert
	assert_true(success)
	assert_eq(_deck.active_threats.size(), 0)
	assert_eq(_deck.discard_pile.size(), 1)
	assert_eq(_deck.discard_pile[0]["status"], ThreatDeck.STATUS_RESOLVED)

func test_discard_threat_moves_to_discard_pile() -> void:
	# Arrange
	_deck.build_standard_deck(1, 1.0)
	var drawn: Dictionary = _deck.draw_threat()
	var threat_id: String = drawn["id"]

	# Act
	var success: bool = _deck.discard_threat(threat_id)

	# Assert
	assert_true(success)
	assert_eq(_deck.active_threats.size(), 0)
	assert_eq(_deck.discard_pile.size(), 1)
	assert_eq(_deck.discard_pile[0]["status"], ThreatDeck.STATUS_DISCARDED)

func test_peek_threats_does_not_modify_draw_pile() -> void:
	# Arrange
	_deck.build_standard_deck(1, 1.0)
	var count_before: int = _deck.draw_pile.size()

	# Act
	var peeked: Array[Dictionary] = _deck.peek_threats(3)

	# Assert
	assert_eq(peeked.size(), 3)
	assert_eq(_deck.draw_pile.size(), count_before, "Draw pile count remains unchanged after peek")

# ==============================================================================
# SECTION 5: Cartas de Runa e Defesa Reactions
# ==============================================================================

func test_defense_escudo_quitina_counters_infiltration() -> void:
	# Arrange
	var threat: Dictionary = {
		"id": "infilt_1",
		"card_type": ThreatDeck.TYPE_INFILTRATION,
		"title": "Infiltração Furtiva",
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(threat)

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.DEFENSE_ESCUDO_QUITINA, "infilt_1")

	# Assert
	assert_true(result["success"], "Escudo de Quitina successfully counters infiltration")
	assert_true(result["countered"])
	assert_eq(_deck.active_threats.size(), 0)
	assert_eq(_deck.discard_pile.size(), 1)
	assert_eq(_deck.discard_pile[0]["status"], ThreatDeck.STATUS_COUNTERED)

func test_defense_teia_endurecida_blocks_spawn_wave() -> void:
	# Arrange
	var wave_threat: Dictionary = {
		"id": "wave_threat_1",
		"card_type": ThreatDeck.TYPE_SPAWN_WAVE,
		"caste_id": IsectumCastes.ID_SOLDADO_MANDIBULA,
		"target_zone": ThreatDeck.ZONE_SPAWN_NORTE,
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(wave_threat)

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.DEFENSE_TEIA_ENDURECIDA, "wave_threat_1")

	# Assert
	assert_true(result["success"])
	assert_true(result["countered"])
	assert_eq(result["effect"], "bloquear_avanco_muralha")
	assert_eq(_deck.active_threats.size(), 0)

func test_defense_antidoto_alquimico_cleanses_miasma_and_stun() -> void:
	# Arrange
	var miasma_threat: Dictionary = {
		"id": "miasma_1",
		"card_type": ThreatDeck.TYPE_AREA_MIASMA,
		"title": "Miasma Venenoso",
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(miasma_threat)

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.DEFENSE_ANTIDOTO_ALQUIMICO, "miasma_1")

	# Assert
	assert_true(result["success"])
	assert_true(result["countered"])
	assert_eq(result["effect"], "cancelar_veneno_atordoamento")
	assert_eq(_deck.active_threats.size(), 0)

func test_rune_runa_visao_peeks_upcoming_threats() -> void:
	# Arrange
	_deck.build_standard_deck(1, 1.0)
	var expected_peek: int = 3

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.RUNE_RUNA_VISAO, "", {"peek_count": expected_peek})

	# Assert
	assert_true(result["success"])
	assert_eq(result["effect"], "revelar_deck")
	assert_false(result["countered"])
	var revealed: Array = result["revealed_threats"]
	assert_eq(revealed.size(), expected_peek)

func test_rune_runa_fortaleza_counters_catapult_siege() -> void:
	# Arrange
	var siege_threat: Dictionary = {
		"id": "siege_1",
		"card_type": ThreatDeck.TYPE_CATAPULT_SIEGE,
		"title": "Catapulta Sitiante",
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(siege_threat)

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.RUNE_RUNA_FORTALEZA, "siege_1")

	# Assert
	assert_true(result["success"])
	assert_true(result["countered"])
	assert_eq(result["effect"], "imunidade_catapulta_fortificacao")
	assert_eq(_deck.active_threats.size(), 0)

func test_incompatible_defense_card_rejected() -> void:
	# Arrange: Infiltration defense used against Catapult siege
	var siege_threat: Dictionary = {
		"id": "siege_2",
		"card_type": ThreatDeck.TYPE_CATAPULT_SIEGE,
		"title": "Catapulta Sitiante",
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(siege_threat)

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.DEFENSE_ESCUDO_QUITINA, "siege_2")

	# Assert
	assert_false(result["success"], "Escudo de Quitina cannot counter catapult siege")
	assert_false(result["countered"])
	assert_eq(_deck.active_threats.size(), 1, "Threat remains in queue")

func test_defense_reaction_with_empty_active_queue_returns_failure() -> void:
	# Arrange: active threats queue is completely empty
	_deck.active_threats.clear()

	# Act
	var result: Dictionary = _deck.resolve_defense_card(ThreatDeck.DEFENSE_ESCUDO_QUITINA, "non_existent_threat")

	# Assert
	assert_false(result["success"])
	assert_false(result["countered"])

# ==============================================================================
# SECTION 6: Signals, Boundary Conditions & Teardown
# ==============================================================================

func test_signals_emitted_on_draw_counter_resolve_and_wave() -> void:
	# Arrange
	watch_signals(_deck)
	_deck.build_standard_deck(1, 1.0)

	# Act 1: Draw
	var drawn: Dictionary = _deck.draw_threat()

	# Assert 1
	assert_signal_emitted(_deck, "threat_drawn")

	# Act 2: Resolve
	_deck.resolve_threat(drawn["id"])

	# Assert 2
	assert_signal_emitted(_deck, "threat_resolved")

	# Act 3: Counter
	var infilt: Dictionary = {
		"id": "inf_test",
		"card_type": ThreatDeck.TYPE_INFILTRATION,
		"status": ThreatDeck.STATUS_ACTIVE
	}
	_deck.active_threats.append(infilt)
	_deck.resolve_defense_card(ThreatDeck.DEFENSE_ESCUDO_QUITINA, "inf_test")

	# Assert 3
	assert_signal_emitted(_deck, "threat_countered")

func test_clear_active_threats_moves_all_to_discard() -> void:
	# Arrange
	_deck.active_threats.append({"id": "t1", "status": ThreatDeck.STATUS_ACTIVE})
	_deck.active_threats.append({"id": "t2", "status": ThreatDeck.STATUS_ACTIVE})

	# Act
	_deck.clear_active_threats()

	# Assert
	assert_eq(_deck.active_threats.size(), 0)
	assert_eq(_deck.discard_pile.size(), 2)

func test_memory_leak_free_teardown() -> void:
	# Arrange: create instances of all resources and managers
	var caste_objs: Array[IsectumCasteData] = []
	for id in IsectumCastes.get_all_caste_ids():
		caste_objs.append(IsectumCastes.create_instance(id))

	var temp_deck: ThreatDeck = ThreatDeck.new()
	temp_deck.build_standard_deck(3, 1.5)
	for i in range(5):
		temp_deck.draw_threat()

	var weak_deck: WeakRef = weakref(temp_deck)

	# Act: clean up
	caste_objs.clear()
	temp_deck.reset()
	temp_deck = null

	# Assert
	assert_eq(caste_objs.size(), 0, "Caste objects array cleared")
	assert_null(weak_deck.get_ref(), "ThreatDeck deallocated cleanly")

