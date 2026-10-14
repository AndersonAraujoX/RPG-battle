# res://scripts/cerco/ThreatDeck.gd
class_name ThreatDeck
extends RefCounted

## ThreatDeck: Threat deck, spawn wave generator, and defense/rune card arbiter.
## Manages threat cards, active threat queue, draw/discard cycles, wave generation
## across the 4 canonical spawn zones, and defense/rune card counter-reactions.

# ── Signals ──────────────────────────────────────────────────────────────────
signal threat_drawn(threat: Dictionary)
signal threat_countered(threat: Dictionary, defense_card_id: String)
signal threat_resolved(threat: Dictionary)
signal threat_discarded(threat: Dictionary)
signal wave_generated(wave: Array[Dictionary], round_number: int)
signal deck_shuffled()

# ── Constants: Spawn Zones ───────────────────────────────────────────────────
const ZONE_SPAWN_NORTE: String = FortressBoard.ZONE_SPAWN_NORTE
const ZONE_SPAWN_SUL: String = FortressBoard.ZONE_SPAWN_SUL
const ZONE_SPAWN_LESTE: String = FortressBoard.ZONE_SPAWN_LESTE
const ZONE_SPAWN_OESTE: String = FortressBoard.ZONE_SPAWN_OESTE

const ALL_SPAWN_ZONES: Array[String] = [
	ZONE_SPAWN_NORTE,
	ZONE_SPAWN_SUL,
	ZONE_SPAWN_LESTE,
	ZONE_SPAWN_OESTE
]

# ── Constants: Threat Card Types ─────────────────────────────────────────────
const TYPE_SPAWN_WAVE: String = "spawn_wave"
const TYPE_CATAPULT_SIEGE: String = "catapult_siege"
const TYPE_INFILTRATION: String = "infiltration"
const TYPE_AREA_MIASMA: String = "area_miasma"
const TYPE_STUN_DISRUPTION: String = "stun_disruption"
const TYPE_BOSS_ASSAULT: String = "boss_assault"

# ── Constants: Threat Status ─────────────────────────────────────────────────
const STATUS_DECK: String = "deck"
const STATUS_ACTIVE: String = "active"
const STATUS_COUNTERED: String = "countered"
const STATUS_RESOLVED: String = "resolved"
const STATUS_DISCARDED: String = "discarded"

# ── Constants: Supported Defense and Rune Cards ──────────────────────────────
const DEFENSE_ESCUDO_QUITINA: String = "escudo_quitina"
const DEFENSE_TEIA_ENDURECIDA: String = "teia_endurecida"
const DEFENSE_ANTIDOTO_ALQUIMICO: String = "antidoto_alquimico"
const DEFENSE_AMULETO_RESISTENCIA: String = "amuleto_resistencia"

const RUNE_RUNA_HASTE: String = "runa_haste"
const RUNE_RUNA_VISAO: String = "runa_visao"
const RUNE_RUNA_FORTALEZA: String = "runa_fortaleza"
const RUNE_RUNA_RECUPERACAO: String = "runa_recuperacao"

# ── State Variables ──────────────────────────────────────────────────────────
var draw_pile: Array[Dictionary] = []
var discard_pile: Array[Dictionary] = []
var active_threats: Array[Dictionary] = []

var current_round: int = 1
var difficulty_factor: float = 1.0
var _threat_counter: int = 0
var _forced_waves: Array[Dictionary] = []

# ── Initialization & Reset ───────────────────────────────────────────────────

func reset() -> void:
	draw_pile.clear()
	discard_pile.clear()
	active_threats.clear()
	_forced_waves.clear()
	_threat_counter = 0
	current_round = 1
	difficulty_factor = 1.0

# ── Wave Generation ──────────────────────────────────────────────────────────

## Generates a structured swarm invasion wave distributed among the 4 spawn zones.
func generate_wave(round_number: int, difficulty: float = 1.0) -> Array[Dictionary]:
	if not _forced_waves.is_empty():
		var forced: Array[Dictionary] = []
		for w in _forced_waves:
			forced.append(w.duplicate(true))
		wave_generated.emit(forced, round_number)
		return forced

	var effective_round: int = maxi(1, round_number)
	var effective_diff: float = maxf(0.5, difficulty)
	current_round = effective_round
	difficulty_factor = effective_diff

	var budget: int = int((4 + effective_round * 3) * effective_diff)
	var wave: Array[Dictionary] = []

	var available_castes: Array[String] = _get_castes_for_round(effective_round)
	var zone_index: int = (effective_round - 1) % ALL_SPAWN_ZONES.size()

	# Check for Boss spawning (Round 8+, or every 5 rounds after round 5)
	var spawn_boss: bool = (effective_round >= 8 and effective_round % 4 == 0) or (effective_round == 5)
	if spawn_boss:
		var boss_id: String = IsectumCastes.ID_RAINHA_DO_ENXAME if (effective_round % 2 != 0) else IsectumCastes.ID_COLOSSO_ISECTUM
		var boss_caste: IsectumCasteData = IsectumCastes.get_caste(boss_id)
		if boss_caste:
			var boss_zone: String = ALL_SPAWN_ZONES[zone_index]
			var boss_threat: Dictionary = _create_threat_dict(
				TYPE_BOSS_ASSAULT,
				"Chegada do Chefe: " + boss_caste.caste_name,
				boss_id,
				1,
				boss_zone,
				effective_round,
				boss_caste.threat_cost
			)
			wave.append(boss_threat)
			budget = maxi(0, budget - boss_caste.threat_cost)
			zone_index = (zone_index + 1) % ALL_SPAWN_ZONES.size()

	# Spend remaining budget on squad spawns across the 4 zones
	var attempts: int = 0
	while budget > 0 and attempts < 25:
		attempts += 1
		var caste_id: String = available_castes[randi() % available_castes.size()]
		var caste_data: IsectumCasteData = IsectumCastes.get_caste(caste_id)
		if caste_data == null:
			continue

		var cost: int = maxi(1, caste_data.threat_cost)
		var max_count: int = maxi(1, floori(float(budget) / float(cost)))
		var count: int = mini(3, maxi(1, randi_range(1, max_count)))

		var zone: String = ALL_SPAWN_ZONES[zone_index]
		zone_index = (zone_index + 1) % ALL_SPAWN_ZONES.size()

		var threat: Dictionary = _create_threat_dict(
			TYPE_SPAWN_WAVE,
			"Horda: " + caste_data.caste_name,
			caste_id,
			count,
			zone,
			effective_round,
			cost * count
		)
		wave.append(threat)
		budget -= (cost * count)

	wave_generated.emit(wave, effective_round)
	return wave

func set_forced_waves(waves: Array[Dictionary]) -> void:
	_forced_waves.clear()
	for w in waves:
		_forced_waves.append(w.duplicate(true))

func _get_castes_for_round(rnd: int) -> Array[String]:
	if rnd <= 2:
		return [
			IsectumCastes.ID_ZANGAO_INVASOR,
			IsectumCastes.ID_SOLDADO_MANDIBULA,
			IsectumCastes.ID_OPERARIO_ESCAVADOR,
			IsectumCastes.ID_BARATA_PRAGA
		]
	elif rnd <= 4:
		return [
			IsectumCastes.ID_ZANGAO_INVASOR,
			IsectumCastes.ID_SOLDADO_MANDIBULA,
			IsectumCastes.ID_OPERARIO_ESCAVADOR,
			IsectumCastes.ID_TECE_TEIA,
			IsectumCastes.ID_ESCARAVELHO_COURACADO,
			IsectumCastes.ID_VESPA_FURTIVA,
			IsectumCastes.ID_FORMIGA_ACIDA,
			IsectumCastes.ID_CENTOPEIA_VENENOSA,
			IsectumCastes.ID_ARANHA_SALTADORA
		]
	elif rnd <= 6:
		return [
			IsectumCastes.ID_SOLDADO_MANDIBULA,
			IsectumCastes.ID_ESCARAVELHO_COURACADO,
			IsectumCastes.ID_VESPA_FURTIVA,
			IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
			IsectumCastes.ID_BESOURO_RINOCERONTE,
			IsectumCastes.ID_TRACA_DA_RUNA,
			IsectumCastes.ID_VAGALUME_CEGO,
			IsectumCastes.ID_CUPIM_ROEDOR,
			IsectumCastes.ID_PULGA_SALTADORA,
			IsectumCastes.ID_GRILO_ATORDOANTE,
			IsectumCastes.ID_LARVA_NECROTICA
		]
	else:
		return [
			IsectumCastes.ID_ESCARAVELHO_COURACADO,
			IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
			IsectumCastes.ID_BESOURO_RINOCERONTE,
			IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
			IsectumCastes.ID_BICHO_PAU_EMBOSCADOR,
			IsectumCastes.ID_PERCEVEJO_PESTILENTO,
			IsectumCastes.ID_CARRAPATO_PARASITA,
			IsectumCastes.ID_PULGA_SALTADORA,
			IsectumCastes.ID_GRILO_ATORDOANTE,
			IsectumCastes.ID_LARVA_NECROTICA
		]

# ── Threat Deck Building & Deck Cycles ───────────────────────────────────────

## Builds a standardized threat deck containing spawns, sieges, infiltrations, and hazards.
func build_standard_deck(round_number: int = 1, difficulty: float = 1.0) -> void:
	draw_pile.clear()
	discard_pile.clear()
	active_threats.clear()

	var wave_spawns: Array[Dictionary] = generate_wave(round_number, difficulty)
	for w in wave_spawns:
		var c: Dictionary = w.duplicate(true)
		c["status"] = STATUS_DECK
		draw_pile.append(c)

	# Add Special Event Cards
	draw_pile.append(_create_event_dict(
		TYPE_CATAPULT_SIEGE,
		"Bombardeio de Catapulta",
		FortressBoard.ZONE_MURALHA_NORTE,
		"Disparo direto de cerco contra as fortificações norte.",
		3
	))
	draw_pile.append(_create_event_dict(
		TYPE_INFILTRATION,
		"Infiltração Furtiva",
		FortressBoard.ZONE_MURALHA_OESTE,
		"Infiltradores escalam as muralhas nas sombras.",
		2
	))
	draw_pile.append(_create_event_dict(
		TYPE_AREA_MIASMA,
		"Nuvem de Miasma",
		FortressBoard.ZONE_PATIO_CENTRAL,
		"Miasma sufocante cobre o pátio central.",
		2
	))
	draw_pile.append(_create_event_dict(
		TYPE_STUN_DISRUPTION,
		"Pulso Desestabilizador",
		FortressBoard.ZONE_CAMARA_CENTRAL,
		"Vibração sônica interrompe o planejamento tático.",
		2
	))

	shuffle_draw_pile()

func shuffle_draw_pile() -> void:
	draw_pile.shuffle()
	deck_shuffled.emit()

func set_draw_pile(cards: Array[Dictionary]) -> void:
	draw_pile.clear()
	for c in cards:
		var card_copy: Dictionary = c.duplicate(true)
		card_copy["status"] = STATUS_DECK
		draw_pile.append(card_copy)

## Draws the top card from draw_pile. If empty, reshuffles discard_pile.
func draw_threat() -> Dictionary:
	if draw_pile.is_empty():
		if discard_pile.is_empty():
			return {}
		# Reshuffle discard into draw
		for d in discard_pile:
			d["status"] = STATUS_DECK
			draw_pile.append(d)
		discard_pile.clear()
		shuffle_draw_pile()

	var threat: Dictionary = draw_pile.pop_front()
	threat["status"] = STATUS_ACTIVE
	active_threats.append(threat)
	threat_drawn.emit(threat)
	return threat

## Peeks at the top N cards of the draw pile without removing them (e.g. for Runa da Visão).
func peek_threats(count: int = 3) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var limit: int = mini(count, draw_pile.size())
	for i in range(limit):
		result.append(draw_pile[i].duplicate(true))
	return result

## Resolves an active threat, moving it to discard_pile.
func resolve_threat(threat_id: String) -> bool:
	for i in range(active_threats.size()):
		if active_threats[i].get("id") == threat_id:
			var t: Dictionary = active_threats[i]
			t["status"] = STATUS_RESOLVED
			active_threats.remove_at(i)
			discard_pile.append(t)
			threat_resolved.emit(t)
			return true
	return false

## Discards an active threat without resolving its positive effect.
func discard_threat(threat_id: String) -> bool:
	for i in range(active_threats.size()):
		if active_threats[i].get("id") == threat_id:
			var t: Dictionary = active_threats[i]
			t["status"] = STATUS_DISCARDED
			active_threats.remove_at(i)
			discard_pile.append(t)
			threat_discarded.emit(t)
			return true
	return false

func clear_active_threats() -> void:
	for t in active_threats:
		t["status"] = STATUS_DISCARDED
		discard_pile.append(t)
	active_threats.clear()

# ── Cartas de Runa e Defesa Reactions ────────────────────────────────────────

## Resolves a defense or rune card reaction against an active or upcoming threat.
func resolve_defense_card(
	card_id: String,
	target_threat_id: String = "",
	context: Dictionary = {}
) -> Dictionary:
	var clean_card_id: String = card_id.to_lower().strip_edges()

	# 1. Runa da Visão (Peeks ahead in draw pile, does not require active threat)
	if clean_card_id == RUNE_RUNA_VISAO:
		var peek_count: int = int(context.get("peek_count", 3))
		var peeked: Array[Dictionary] = peek_threats(peek_count)
		return {
			"success": true,
			"card_id": clean_card_id,
			"threat_id": "",
			"effect": "revelar_deck",
			"revealed_threats": peeked,
			"countered": false,
			"message": "Runa da Visão revelou as próximas %d ameaças." % peeked.size()
		}

	# 2. Find target threat in active threats queue
	var target_index: int = -1
	if not target_threat_id.is_empty():
		for i in range(active_threats.size()):
			if active_threats[i].get("id") == target_threat_id:
				target_index = i
				break
	else:
		# Auto-target first compatible threat in queue
		target_index = _find_compatible_threat(clean_card_id)

	if target_index == -1:
		return {
			"success": false,
			"card_id": clean_card_id,
			"threat_id": target_threat_id,
			"effect": "none",
			"countered": false,
			"message": "Nenhuma ameaça compatível encontrada na fila ativa para " + card_id
		}

	var threat: Dictionary = active_threats[target_index]
	var can_counter: bool = _can_card_counter_threat(clean_card_id, threat)

	if not can_counter:
		return {
			"success": false,
			"card_id": clean_card_id,
			"threat_id": threat.get("id", ""),
			"effect": "incompatible",
			"countered": false,
			"message": "A carta %s não neutraliza a ameaça do tipo %s." % [card_id, threat.get("card_type", "")]
		}

	# Apply counter reaction
	threat["status"] = STATUS_COUNTERED
	active_threats.remove_at(target_index)
	discard_pile.append(threat)
	threat_countered.emit(threat, clean_card_id)

	var effect_name: String = _get_card_effect_name(clean_card_id)
	return {
		"success": true,
		"card_id": clean_card_id,
		"threat_id": threat.get("id", ""),
		"effect": effect_name,
		"countered": true,
		"threat": threat,
		"message": "Ameaça '%s' neutralizada por %s!" % [threat.get("title", ""), clean_card_id]
	}

func _find_compatible_threat(card_id: String) -> int:
	for i in range(active_threats.size()):
		if _can_card_counter_threat(card_id, active_threats[i]):
			return i
	return -1

func _can_card_counter_threat(card_id: String, threat: Dictionary) -> bool:
	var t_type: String = threat.get("card_type", "")
	var caste_id: String = threat.get("caste_id", "")
	var caste: IsectumCasteData = IsectumCastes.get_caste(caste_id) if not caste_id.is_empty() else null

	match card_id:
		DEFENSE_ESCUDO_QUITINA:
			# Neutralizes infiltration, stealth ambushes, and theft
			if t_type == TYPE_INFILTRATION:
				return true
			if caste and (caste.is_infiltrator or caste.trait_id == "dreno_parasitario"):
				return true
			return false

		DEFENSE_TEIA_ENDURECIDA:
			# Blocks spawn wave marching or rush on walls
			if t_type == TYPE_SPAWN_WAVE:
				return true
			return false

		DEFENSE_ANTIDOTO_ALQUIMICO:
			# Cleanses miasma, poison, and stuns
			if t_type == TYPE_AREA_MIASMA or t_type == TYPE_STUN_DISRUPTION:
				return true
			if caste and (caste.trait_id in ["peconha_letal", "acido_corrosivo", "pulso_sonico", "miasma_pestilento"]):
				return true
			return false

		DEFENSE_AMULETO_RESISTENCIA:
			# Generic resistance counter against non-boss threats
			return t_type != TYPE_BOSS_ASSAULT

		RUNE_RUNA_FORTALEZA:
			# Hard counter against catapult and direct siege damage
			if t_type == TYPE_CATAPULT_SIEGE:
				return true
			if caste and caste.is_catapult:
				return true
			return false

		RUNE_RUNA_HASTE:
			# Allows pre-emptive reaction against standard spawn waves or infiltrators
			return t_type in [TYPE_SPAWN_WAVE, TYPE_INFILTRATION]

		RUNE_RUNA_RECUPERACAO:
			# Mitigates disruption and enables card recovery
			return t_type in [TYPE_STUN_DISRUPTION, TYPE_AREA_MIASMA]

		_:
			return false

func _get_card_effect_name(card_id: String) -> String:
	match card_id:
		DEFENSE_ESCUDO_QUITINA:
			return "anular_infiltracao_ou_roubo"
		DEFENSE_TEIA_ENDURECIDA:
			return "bloquear_avanco_muralha"
		DEFENSE_ANTIDOTO_ALQUIMICO:
			return "cancelar_veneno_atordoamento"
		DEFENSE_AMULETO_RESISTENCIA:
			return "resistencia_dano"
		RUNE_RUNA_FORTALEZA:
			return "imunidade_catapulta_fortificacao"
		RUNE_RUNA_HASTE:
			return "acao_extra_antecipada"
		RUNE_RUNA_RECUPERACAO:
			return "recuperacao_tencao"
		_:
			return "defesa_generica"

# ── Helper Builders ──────────────────────────────────────────────────────────

func _create_threat_dict(
	p_type: String,
	p_title: String,
	p_caste_id: String,
	p_count: int,
	p_zone: String,
	p_round: int,
	p_threat_cost: int
) -> Dictionary:
	_threat_counter += 1
	var caste_data: IsectumCasteData = IsectumCastes.get_caste(p_caste_id)
	var sym: String = caste_data.symbol if caste_data else "🦗"
	return {
		"id": "threat_%d" % _threat_counter,
		"card_type": p_type,
		"title": p_title,
		"caste_id": p_caste_id,
		"count": p_count,
		"target_zone": p_zone,
		"round": p_round,
		"threat_cost": p_threat_cost,
		"threat_level": mini(5, maxi(1, floori(float(p_threat_cost) / float(maxi(1, p_count))))),
		"status": STATUS_ACTIVE,
		"symbol": sym,
		"description": "%s: %d unidade(s) atacando %s." % [p_title, p_count, p_zone]
	}

func _create_event_dict(
	p_type: String,
	p_title: String,
	p_zone: String,
	p_desc: String,
	p_level: int
) -> Dictionary:
	_threat_counter += 1
	return {
		"id": "threat_event_%d" % _threat_counter,
		"card_type": p_type,
		"title": p_title,
		"caste_id": "",
		"count": 1,
		"target_zone": p_zone,
		"round": current_round,
		"threat_cost": p_level * 2,
		"threat_level": p_level,
		"status": STATUS_DECK,
		"symbol": "⚠️",
		"description": p_desc
	}
