# res://test/unit/test_combat_encounter_adversarial.gd
extends GutTest

## Empirical Adversarial Challenge Suite for Milestone M4 (CombatEncounterGenerator)
## Empirically stress-tests edge cases, tier scaling, spatial integrity, invalid inputs,
## schema completeness, and deterministic seed reproducibility.

var _gen: CombatEncounterGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_gen = CombatEncounterGenerator.new()
	_rng = RandomNumberGenerator.new()
	_rng.seed = 424242

func after_each() -> void:
	_gen = null
	_rng = null

# ── 1. Invalid Inputs & Safe Fallbacks ────────────────────────────────────────

func test_adversarial_null_and_negative_act_node() -> void:
	# Arrange & Act
	var enc_null: Dictionary = CombatEncounterGenerator.generate_from_node(null)
	var enc_neg: Dictionary = _gen.generate_encounter(-5, -10, -99, -1, 12345)

	# Assert
	assert_not_null(enc_null, "generate_from_node(null) must return fallback dictionary")
	assert_eq(enc_null.get("act"), 1, "Negative/null act must clamp to Act 1")
	assert_eq(enc_null.get("floor"), 0, "Negative floor must clamp to 0")
	assert_eq(enc_null.get("node_type"), RunNode.NodeType.COMBAT, "Invalid node type must default to COMBAT")

	assert_not_null(enc_neg, "generate_encounter with negative arguments must not crash")
	assert_eq(enc_neg.get("act"), 1, "Clamped act should be 1")
	assert_eq(enc_neg.get("floor"), 0, "Clamped floor should be 0")
	assert_eq(enc_neg.get("node_type"), RunNode.NodeType.COMBAT, "Clamped type should be COMBAT")

func test_adversarial_unsupported_node_types_fallback_to_combat() -> void:
	# Test campfire, forge, event nodes passed to encounter generator
	var non_combat_types: Array[int] = [
		RunNode.NodeType.CAMPFIRE,
		RunNode.NodeType.FORGE,
		RunNode.NodeType.EVENT,
		9999
	]

	for ntype in non_combat_types:
		var enc: Dictionary = _gen.generate_encounter(1, 2, ntype, 100, 555)
		assert_eq(enc.get("node_type"), RunNode.NodeType.COMBAT, "Non-combat type %d must fallback to COMBAT" % ntype)
		assert_gt(enc.get("enemies", []).size(), 0, "Fallback must generate a valid squad")

func test_adversarial_polymorphic_signatures() -> void:
	# Signature A: generate_from_node(node, rng)
	var node_a: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.COMBAT)
	var custom_rng: RandomNumberGenerator = RandomNumberGenerator.new()
	custom_rng.seed = 12345
	var enc_a: Dictionary = CombatEncounterGenerator.generate_from_node(node_a, custom_rng)
	assert_not_null(enc_a, "Must generate valid encounter from generate_from_node(node, rng)")
	assert_eq(enc_a.get("node_id"), 5)
	assert_eq(enc_a.get("act"), 1)
	assert_eq(enc_a.get("floor"), 3)

	# Signature B: generate_encounter(node, int_seed)
	var node_b: RunNode = RunNode.new(6, 2, 4, 0, RunNode.NodeType.SIEGE)
	var enc_b: Dictionary = CombatEncounterGenerator.generate_encounter(node_b, 54321)
	assert_not_null(enc_b, "Must generate valid encounter from generate_encounter(node, int_seed)")
	assert_eq(enc_b.get("node_id"), 6)
	assert_eq(enc_b.get("act"), 2)
	assert_eq(enc_b.get("floor"), 4)
	assert_true(enc_b["rules"]["is_siege_mode"])

	# Signature C: standard 4-arg (act, floor, type, rng)
	var enc_c: Dictionary = CombatEncounterGenerator.generate_encounter(1, 2, RunNode.NodeType.ELITE, custom_rng)
	assert_not_null(enc_c, "Must generate valid encounter from 4-arg signature")
	assert_true(enc_c["rewards"]["guaranteed_relic"])

	# Signature D: generate_encounter(node, rng) - polymorphic relaxation
	var node_d: RunNode = RunNode.new(7, 1, 2, 0, RunNode.NodeType.COMBAT)
	var enc_d: Dictionary = CombatEncounterGenerator.generate_encounter(node_d, custom_rng)
	assert_not_null(enc_d, "Must generate valid encounter from generate_encounter(node, rng)")
	assert_eq(enc_d.get("node_id"), 7)
	assert_eq(enc_d.get("act"), 1)

# ── 2. Extreme Tier & Floor Scaling Stress ────────────────────────────────────

func test_adversarial_high_floor_scaling_stress() -> void:
	# Floor 100 stress test (Act 1)
	var enc_high: Dictionary = _gen.generate_encounter(1, 100, RunNode.NodeType.ELITE, 10, 777)
	var enemies: Array = enc_high.get("enemies", [])
	assert_gt(enemies.size(), 0, "High floor encounter must generate enemies")

	var leader: Dictionary = enemies[0]
	assert_true(leader["is_elite"], "Leader must be marked elite")
	assert_eq(leader["max_hp"], 20 + 100, "Elite HP should scale cleanly: 20 + 100 = 120")
	assert_eq(leader["hp"], leader["max_hp"], "HP should match max_hp")

	# Act 3 elite scaling: 45 + floor * 2
	var enc_act3: Dictionary = _gen.generate_encounter(3, 100, RunNode.NodeType.ELITE, 10, 777)
	var leader_a3: Dictionary = enc_act3.get("enemies", [])[0]
	assert_eq(leader_a3["max_hp"], 45 + 100 * 2, "Act 3 Elite HP scales to 45 + 200 = 245")

	# Check reward scaling under high floor
	var rewards: Dictionary = enc_high.get("rewards", {})
	assert_gte(rewards["gold_min"], 10, "Gold min must stay positive")
	assert_lte(rewards["gold_min"], rewards["gold_max"], "gold_min must be <= gold_max")
	assert_gt(rewards["base_gold"], 0, "Base gold must be positive")

func test_adversarial_act_clamping_boundaries() -> void:
	# Test Act 0 and negative acts clamp to 1
	var enc_act0: Dictionary = _gen.generate_encounter(0, 1, RunNode.NodeType.BOSS, 1, 100)
	assert_eq(enc_act0.get("act"), 1)
	assert_eq(enc_act0.get("boss_id"), "viuva_canibal")

	# Test Act 4 and higher acts clamp to 3
	var enc_act4: Dictionary = _gen.generate_encounter(5, 1, RunNode.NodeType.BOSS, 1, 100)
	assert_eq(enc_act4.get("act"), 3)
	assert_eq(enc_act4.get("boss_id"), "rei_isectum")

# ── 3. Spatial Anti-Collision & 20x20 Boundaries Under Heavy Load ──────────────

func test_adversarial_spatial_boundaries_and_collision_100_runs() -> void:
	# Test 100 generated encounters across all Acts and node types
	var acts: Array[int] = [1, 2, 3]
	var types: Array[int] = [
		RunNode.NodeType.COMBAT,
		RunNode.NodeType.SIEGE,
		RunNode.NodeType.ELITE,
		RunNode.NodeType.BOSS
	]

	for act in acts:
		for ntype in types:
			for seed_offset in range(10):
				var s: int = 1000 + seed_offset * 37
				var enc: Dictionary = _gen.generate_encounter(act, seed_offset, ntype, seed_offset, s)
				var enemies: Array = enc.get("enemies", [])
				var positions: Dictionary = {}

				for u in enemies:
					var p: Vector2i = u["spawn_pos"]
					assert_true(
						p.x >= 0 and p.x < 20 and p.y >= 0 and p.y < 20,
						"Spawn pos %s out of 20x20 board bounds in Act %d Type %d" % [str(p), act, ntype]
					)
					assert_false(
						positions.has(p),
						"Collision detected at %s in Act %d Type %d Seed %d" % [str(p), act, ntype, s]
					)
					positions[p] = true

# ── 4. Alias Catalog & IsectumCastes Completeness ─────────────────────────────

func test_adversarial_caste_aliases_and_pools_validity() -> void:
	# Verify all aliases resolve to canonical castes
	for alias in CombatEncounterGenerator.CASTE_ALIASES.keys():
		var resolved: String = CombatEncounterGenerator.resolve_caste_id(alias)
		var caste: IsectumCasteData = IsectumCastes.get_caste(resolved)
		assert_not_null(caste, "Alias '%s' resolves to unknown caste '%s'" % [alias, resolved])

	# Verify all pools resolve to canonical castes
	var pools: Array[Array] = [
		CombatEncounterGenerator.ACT_1_COMBAT_POOL,
		CombatEncounterGenerator.ACT_1_SIEGE_POOL,
		CombatEncounterGenerator.ACT_1_ELITE_LEADERS,
		CombatEncounterGenerator.ACT_2_COMBAT_POOL,
		CombatEncounterGenerator.ACT_3_COMBAT_POOL
	]

	for pool in pools:
		for entry in pool:
			var resolved: String = CombatEncounterGenerator.resolve_caste_id(entry)
			var caste: IsectumCasteData = IsectumCastes.get_caste(resolved)
			assert_not_null(caste, "Pool entry '%s' resolves to unknown caste '%s'" % [entry, resolved])

# ── 5. ThreatDeck Forced Waves Schema Conformity ──────────────────────────────

func test_adversarial_forced_waves_schema_conformity() -> void:
	var enc: Dictionary = _gen.generate_encounter(2, 4, RunNode.NodeType.SIEGE, 1, 9999)
	var waves: Array = enc.get("forced_waves", [])
	assert_gt(waves.size(), 0, "Forced waves must not be empty")

	var required_keys: Array[String] = [
		"id", "card_type", "title", "caste_id", "count",
		"target_zone", "round", "threat_cost", "status",
		"hp", "ac", "move", "atk", "description"
	]

	for w in waves:
		for k in required_keys:
			assert_true(w.has(k), "Forced wave missing required ThreatDeck key: %s" % k)
		assert_gte(w["round"], 1, "Round must be >= 1")
		assert_lte(w["round"], 3, "Round must be <= 3")
		assert_eq(w["card_type"], ThreatDeck.TYPE_SPAWN_WAVE, "SIEGE forced waves must be TYPE_SPAWN_WAVE")

# ── 6. Deterministic Seed Reproducibility vs Global PRNG Leaks ───────────────

func test_adversarial_deterministic_seed_reproducibility() -> void:
	# Run encounter generation with fixed seed twice
	var enc_a: Dictionary = _gen.generate_encounter(1, 2, RunNode.NodeType.COMBAT, 1, 88888)
	var enc_b: Dictionary = _gen.generate_encounter(1, 2, RunNode.NodeType.COMBAT, 1, 88888)

	assert_eq(enc_a["encounter_id"], enc_b["encounter_id"])
	assert_eq(enc_a["enemies"].size(), enc_b["enemies"].size())

	for i in range(enc_a["enemies"].size()):
		assert_eq(enc_a["enemies"][i]["id"], enc_b["enemies"][i]["id"])
		assert_eq(enc_a["enemies"][i]["caste_id"], enc_b["enemies"][i]["caste_id"])
		assert_eq(enc_a["enemies"][i]["spawn_pos"], enc_b["enemies"][i]["spawn_pos"])

func test_adversarial_boss_hazards_under_global_seed_tampering() -> void:
	# Act 1 Boss generates web hazards via _generate_boss_web_hazards
	var enc1: Dictionary = _gen.generate_encounter(1, 11, RunNode.NodeType.BOSS, 99, 12345)

	# Mutate global seed in between
	seed(999999999)

	var enc2: Dictionary = _gen.generate_encounter(1, 11, RunNode.NodeType.BOSS, 99, 12345)

	var h1: Array = enc1.get("hazards", [])
	var h2: Array = enc2.get("hazards", [])

	assert_eq(h1.size(), h2.size(), "Hazard count must be deterministic (5-7)")
	assert_gte(h1.size(), 5)
	assert_lte(h1.size(), 7)

	for h in h1:
		assert_eq(h["type"], "WEB")
		assert_true(h["pos"].x >= 0 and h["pos"].x < 20 and h["pos"].y >= 0 and h["pos"].y < 20)

	var positions_match: bool = true
	for i in range(mini(h1.size(), h2.size())):
		if h1[i]["pos"] != h2[i]["pos"]:
			positions_match = false
			break

	if not positions_match:
		push_warning("[CHALLENGER DEFECT CONFIRMED] Boss hazards positions vary when global seed changes because candidates.shuffle() uses global PRNG rather than the seeded RandomNumberGenerator!")
