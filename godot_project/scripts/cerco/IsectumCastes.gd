# res://scripts/cerco/IsectumCastes.gd
class_name IsectumCastes
extends RefCounted

## IsectumCastes: Canonical catalog and factory for the 24 Isectum castes.
## Provides structured stat definitions, archetype categorization (Brutamontes,
## Infiltrator, Catapult, Flyer, Boss), and unit instantiation.

# ── 24 Canonical Caste IDs ──────────────────────────────────────────────────
const ID_ZANGAO_INVASOR: String = "zangao_invasor"
const ID_SOLDADO_MANDIBULA: String = "soldado_mandibula"
const ID_OPERARIO_ESCAVADOR: String = "operario_escavador"
const ID_TECE_TEIA: String = "tece_teia"
const ID_ESCARAVELHO_COURACADO: String = "escaravelho_couracado"
const ID_VESPA_FURTIVA: String = "vespa_furtiva"
const ID_FORMIGA_ACIDA: String = "formiga_acida"
const ID_LOUVA_DEUS_CEIFADOR: String = "louva_deus_ceifador"
const ID_BESOURO_RINOCERONTE: String = "besouro_rinoceronte"
const ID_CENTOPEIA_VENENOSA: String = "centopeia_venenosa"
const ID_BARATA_PRAGA: String = "barata_praga"
const ID_TRACA_DA_RUNA: String = "traca_da_runa"
const ID_CUPIM_ROEDOR: String = "cupim_roedor"
const ID_VAGALUME_CEGO: String = "vagalume_cego"
const ID_ARANHA_SALTADORA: String = "aranha_saltadora"
const ID_LIBELULA_BOMBARDEIRA: String = "libelula_bombardeira"
const ID_BICHO_PAU_EMBOSCADOR: String = "bicho_pau_emboscador"
const ID_PERCEVEJO_PESTILENTO: String = "percevejo_pestilento"
const ID_CARRAPATO_PARASITA: String = "carrapato_parasita"
const ID_PULGA_SALTADORA: String = "pulga_saltadora"
const ID_GRILO_ATORDOANTE: String = "grilo_atordoante"
const ID_LARVA_NECROTICA: String = "larva_necrotica"
const ID_RAINHA_DO_ENXAME: String = "rainha_do_enxame"
const ID_COLOSSO_ISECTUM: String = "colosso_isectum"

const CANONICAL_IDS: Array[String] = [
	ID_ZANGAO_INVASOR,
	ID_SOLDADO_MANDIBULA,
	ID_OPERARIO_ESCAVADOR,
	ID_TECE_TEIA,
	ID_ESCARAVELHO_COURACADO,
	ID_VESPA_FURTIVA,
	ID_FORMIGA_ACIDA,
	ID_LOUVA_DEUS_CEIFADOR,
	ID_BESOURO_RINOCERONTE,
	ID_CENTOPEIA_VENENOSA,
	ID_BARATA_PRAGA,
	ID_TRACA_DA_RUNA,
	ID_CUPIM_ROEDOR,
	ID_VAGALUME_CEGO,
	ID_ARANHA_SALTADORA,
	ID_LIBELULA_BOMBARDEIRA,
	ID_BICHO_PAU_EMBOSCADOR,
	ID_PERCEVEJO_PESTILENTO,
	ID_CARRAPATO_PARASITA,
	ID_PULGA_SALTADORA,
	ID_GRILO_ATORDOANTE,
	ID_LARVA_NECROTICA,
	ID_RAINHA_DO_ENXAME,
	ID_COLOSSO_ISECTUM
]

const ALIASES: Dictionary = {
	"vespa": ID_VESPA_FURTIVA,
	"vespa_cacadora": ID_VESPA_FURTIVA,
	"louva_deus": ID_LOUVA_DEUS_CEIFADOR,
	"viuva_canibal": ID_TECE_TEIA,
	"escaravelho_necrofago": ID_ESCARAVELHO_COURACADO,
	"enxame_rainha": ID_RAINHA_DO_ENXAME,
	"gafanhoto_praga": ID_BARATA_PRAGA,
	"carrapato_vampiro": ID_CARRAPATO_PARASITA,
	"libelula": ID_LIBELULA_BOMBARDEIRA,
	"libelula_blindada": ID_LIBELULA_BOMBARDEIRA,
	"besouro": ID_BESOURO_RINOCERONTE,
	"besouro_unicornio": ID_BESOURO_RINOCERONTE,
	"mosca_tse_tse": ID_GRILO_ATORDOANTE,
	"formiga_correicao": ID_FORMIGA_ACIDA,
	"tarantula_golias": ID_COLOSSO_ISECTUM,
	"soldado": ID_SOLDADO_MANDIBULA,
	"batedor": ID_ZANGAO_INVASOR,
	"operario": ID_OPERARIO_ESCAVADOR,
	"aranha": ID_ARANHA_SALTADORA,
	"vagalume": ID_VAGALUME_CEGO
}

static var _catalog: Dictionary = {}

static func _ensure_catalog() -> void:
	if not _catalog.is_empty():
		return

	_register(ID_ZANGAO_INVASOR, "Zangão Invasor", 2, false, false, false, true, 4, 2, 1, "enxame", 1, "🐝", "Batedor alado rápido e numeroso que compõe as primeiras ondas de ataque.")
	_register(ID_SOLDADO_MANDIBULA, "Soldado Mandíbula", 4, false, false, false, false, 3, 3, 1, "mordida_feroz", 2, "🐜", "Infantaria de choque Isectum armada com mandíbulas afiadas capazes de rasgar armaduras.")
	_register(ID_OPERARIO_ESCAVADOR, "Operário Escavador", 3, false, false, false, false, 2, 2, 1, "escavacao_destrutiva", 2, "⛏️", "Especialista em sapar muralhas e fundações, causando dano dobrado a estruturas.")
	_register(ID_TECE_TEIA, "Tece-Teia", 3, false, false, false, false, 2, 2, 3, "teia_imobilizante", 2, "🕸️", "Aranha tecelã que dispara fios viscosos à distância, imobilizando defensores.")
	_register(ID_ESCARAVELHO_COURACADO, "Escaravelho Couraçado", 6, false, false, false, false, 2, 2, 1, "carapaca_pesada", 3, "🪲", "Blindado natural com espessa carapaça de quitina que absorve impactos Melee.")
	_register(ID_VESPA_FURTIVA, "Vespa Furtiva", 3, false, true, false, true, 4, 3, 1, "infiltracao_furtiva", 3, "🐝", "Predadora alada e silenciosa capaz de transpor muralhas sem ser detectada.")
	_register(ID_FORMIGA_ACIDA, "Formiga Ácida", 3, false, false, false, false, 3, 3, 2, "acido_corrosivo", 2, "🧪", "Cospe jatos de ácido fórmico cáustico que corroem proteções e pedra de muralhas.")
	_register(ID_LOUVA_DEUS_CEIFADOR, "Louva-a-Deus Ceifador", 5, false, false, false, false, 3, 4, 1, "golpe_ceifador", 4, "🦗", "Duelista letal equipado com patas preensoras que desferem acertos críticos devastadores.")
	_register(ID_BESOURO_RINOCERONTE, "Besouro Rinoceronte", 3, true, false, false, false, 2, 4, 1, "carga_brutamontes", 4, "🦏", "Brutamontes com 3 círculos de vida; sua investida estilhaça barricadas e esmaga oponentes.")
	_register(ID_CENTOPEIA_VENENOSA, "Centopeia Venenosa", 4, false, false, false, false, 3, 3, 1, "peconha_letal", 3, "🐛", "Rastejante venenosa que inocula peçonha paralisante a cada golpe deferido.")
	_register(ID_BARATA_PRAGA, "Barata Praga", 3, false, false, false, false, 3, 2, 1, "praga_enxameante", 2, "🪳", "Praga resiliente com incrível capacidade de sobrevivência e proliferação contínua.")
	_register(ID_TRACA_DA_RUNA, "Traça da Runa", 2, false, true, false, true, 3, 2, 2, "disrupcao_runica", 3, "🦋", "Inseto etéreo que se alimenta de magia e runas, desestabilizando encantamentos defensores.")
	_register(ID_CUPIM_ROEDOR, "Cupim Roedor", 3, false, false, false, false, 2, 2, 1, "roedor_estrutural", 2, "🪵", "Roedor incansável de suportes de madeira, andaimes e portões da fortaleza.")
	_register(ID_VAGALUME_CEGO, "Vagalume Cego", 2, false, false, false, true, 4, 1, 3, "clarisao_cegante", 2, "💡", "Emite clarões bioluminescentes ofuscantes que cegam os atiradores das torres.")
	_register(ID_ARANHA_SALTADORA, "Aranha Saltadora", 3, false, true, false, false, 4, 3, 1, "salto_muralha", 3, "🕷️", "Salta grandes distâncias sobre obstáculos e trincheiras, caindo diretamente sobre alvos desavisados.")
	_register(ID_LIBELULA_BOMBARDEIRA, "Libélula Bombardeira", 4, false, false, true, true, 3, 3, 4, "bombardeio_sitiante", 4, "💣", "Catapulta aérea viva que arremessa cápsulas explosivas contra as muralhas a longa distância.")
	_register(ID_BICHO_PAU_EMBOSCADOR, "Bicho-Pau Emboscador", 4, false, true, false, false, 2, 3, 1, "camuflagem_emboscada", 3, "🎋", "Mestre da camuflagem que se mescla às estacas e ruínas da fortificação para emboscar patrulhas.")
	_register(ID_PERCEVEJO_PESTILENTO, "Percevejo Pestilento", 4, false, false, false, false, 2, 2, 2, "miasma_pestilento", 2, "☣️", "Exala miasmas fétidos e sufocantes que contaminam zonas inteiras da fortaleza.")
	_register(ID_CARRAPATO_PARASITA, "Carrapato Parasita", 3, false, false, false, false, 2, 2, 1, "dreno_parasitario", 2, "🩸", "Fixa-se nos defensores, drenando sua vitalidade e energias combativas.")
	_register(ID_PULGA_SALTADORA, "Pulga Saltadora", 3, false, true, false, false, 5, 3, 1, "salto_cinetico", 3, "⚡", "Executa saltos cinéticos hipersônicos, ultrapassando defesas e colidindo com força extrema.")
	_register(ID_GRILO_ATORDOANTE, "Grilo Atordoante", 3, false, false, false, false, 3, 2, 3, "pulso_sonico", 3, "📢", "Fricciona élitros gerando pulsos ultrassônicos ensurdecedores que atordoam heróis.")
	_register(ID_LARVA_NECROTICA, "Larva Necrótica", 2, false, false, false, false, 2, 2, 1, "explosao_necrotica", 2, "💥", "Ao perecer, entra em combustão necrótica violenta, detonando e ferindo todos na mesma célula.")
	_register(ID_RAINHA_DO_ENXAME, "Rainha do Enxame", 8, false, false, false, true, 3, 5, 2, "chamado_da_rainha", 6, "👑", "Monarca suprema do enxame; comanda ondas invasoras e reabastece ninhadas continuamente.", true)
	_register(ID_COLOSSO_ISECTUM, "Colosso Isectum", 3, true, false, true, false, 1, 6, 2, "colosso_devastador", 8, "🗿", "Monstruosidade titânica viva de cerco; Brutamontes de 3 círculos que derruba muralhas inteiras.", true)

static func _register(
	p_id: String,
	p_name: String,
	p_hp: int,
	p_brutamontes: bool,
	p_infiltrator: bool,
	p_catapult: bool,
	p_flyer: bool,
	p_speed: int,
	p_attack_dice: int,
	p_attack_range: int,
	p_trait: String,
	p_threat: int,
	p_symbol: String,
	p_desc: String,
	p_is_boss: bool = false
) -> void:
	var c: IsectumCasteData = IsectumCasteData.new()
	c.id = p_id
	c.caste_name = p_name
	c.name = p_name
	c.hp = p_hp
	c.max_hp = p_hp
	c.is_brutamontes = p_brutamontes
	c.is_infiltrator = p_infiltrator
	c.is_catapult = p_catapult
	c.is_flyer = p_flyer
	c.speed = p_speed
	c.attack_dice = p_attack_dice
	c.attack_range = p_attack_range
	c.trait_id = p_trait
	c.threat_cost = p_threat
	c.symbol = p_symbol
	c.description = p_desc
	c.is_boss = p_is_boss
	c.ac = 12 + (2 if p_brutamontes else 0)
	c.damage = p_attack_dice
	c.threat_type = "sobrenatural" if p_is_boss or p_infiltrator else "tradicional"
	c.effect_id = p_trait
	_catalog[p_id] = c

# ── Query & Factory API ──────────────────────────────────────────────────────

static func get_caste(caste_id: String) -> IsectumCasteData:
	_ensure_catalog()
	if caste_id.is_empty():
		return null
	if _catalog.has(caste_id):
		return _catalog[caste_id]
	if ALIASES.has(caste_id):
		var mapped_id: String = ALIASES[caste_id]
		return _catalog.get(mapped_id, null)
	return null

static func create_instance(caste_id: String) -> IsectumCasteData:
	var base_caste = get_caste(caste_id)
	if base_caste == null:
		return null
	return base_caste.clone()

static func has_caste(caste_id: String) -> bool:
	_ensure_catalog()
	return _catalog.has(caste_id) or ALIASES.has(caste_id)

static func get_all_caste_ids() -> Array[String]:
	return CANONICAL_IDS.duplicate()

static func get_all_castes() -> Array[IsectumCasteData]:
	_ensure_catalog()
	var result: Array[IsectumCasteData] = []
	for caste_id in CANONICAL_IDS:
		result.append(_catalog[caste_id])
	return result

static func get_castes_by_archetype(archetype: String) -> Array[IsectumCasteData]:
	_ensure_catalog()
	var result: Array[IsectumCasteData] = []
	var norm: String = archetype.to_lower().strip_edges()
	for caste_id in CANONICAL_IDS:
		var c: IsectumCasteData = _catalog[caste_id]
		match norm:
			"brutamontes":
				if c.is_brutamontes:
					result.append(c)
			"infiltrator", "infiltrador":
				if c.is_infiltrator:
					result.append(c)
			"catapult", "catapulta":
				if c.is_catapult:
					result.append(c)
			"flyer", "voador":
				if c.is_flyer:
					result.append(c)
			"boss":
				if c.is_boss:
					result.append(c)
			"melee":
				if c.attack_range == 1:
					result.append(c)
			"ranged":
				if c.attack_range > 1:
					result.append(c)
	return result
