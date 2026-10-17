# res://scripts/run/ui/ForgeScreen.gd
class_name ForgeScreen
extends Control

## Tela da Forja Anã (Nó FORGE da Campanha Roguelike).
## Permite ao jogador:
## 1. Comprar até 3 cartas sorteadas por Ato.
## 2. Comprar até 2 relíquias passivas do catálogo canônico (sem duplicatas).
## 3. Expurgar cartas indesejadas do deck com custo progressivo (50g, 75g, 100g...)
##    respeitando o limite mínimo de segurança de 5 cartas no deck.
## 4. Usufruir de desconto passivo caso possua relíquias econômicas (ex: relogio_da_forja).
## Suporta instanciação programática autônoma e execução segura em GUT Headless.

signal card_purchased(card_id: String, cost: int)
signal relic_purchased(relic_id: String, cost: int)
signal card_purged(card_id: String, cost: int)
signal forge_closed()

# ── Constantes Canônicas ──────────────────────────────────────────────────────
const BASE_PURGE_COST: int = 50
const PURGE_COST_INCREMENT: int = 25
const MINIMUM_SAFE_DECK_LIMIT: int = 5
const CARD_SLOT_COUNT: int = 3
const RELIC_SLOT_COUNT: int = 2

# ── Catálogos de Mercado ──────────────────────────────────────────────────────
const CARD_PRICES: Dictionary = {
	# Ato I
	"marcha_rapida": {"name": "Marcha Rápida", "badge": "MARCHA", "cost": 45, "desc": "+25 Movimento tático"},
	"golpe_pesado": {"name": "Golpe Pesado", "badge": "COMBATE", "cost": 50, "desc": "Ataque Melee com +4 dano"},
	"bloqueio_ferreo": {"name": "Bloqueio Férreo", "badge": "COMBATE", "cost": 50, "desc": "+3 CA de Cobertura"},
	"trabalho_dobrado": {"name": "Trabalho Dobrado", "badge": "TRABALHO", "cost": 55, "desc": "+6 Trabalho de fortificação"},
	"picareta_reforcada": {"name": "Picareta Reforçada", "badge": "ESCAVACAO", "cost": 55, "desc": "+6 Escavação de rocha"},
	"tiro_balista": {"name": "Tiro de Balista", "badge": "COMBATE", "cost": 60, "desc": "Disparo perfurante à distância"},
	"escudo_quitina": {"name": "Escudo de Quitina", "badge": "DEFESA", "cost": 60, "desc": "Reação: absorve 10 dano"},
	# Ato II
	"tocha_sagrada": {"name": "Tocha Sagrada", "badge": "ESPECIAL", "cost": 65, "desc": "Revela células e queima alvos"},
	"lamina_ignea": {"name": "Lâmina Ígnea", "badge": "COMBATE", "cost": 70, "desc": "Ataque com dano de fogo (2x contra carapaça)"},
	"armadura_resinosa": {"name": "Armadura Resinosa", "badge": "DEFESA", "cost": 65, "desc": "Imunidade temporária a ácido"},
	"passo_ligeiro": {"name": "Passo Ligeiro", "badge": "MARCHA", "cost": 60, "desc": "+35 Movimento sem custos"},
	"evasao_tatica": {"name": "Evasão Tática", "badge": "MARCHA", "cost": 65, "desc": "Desengaja sem ataques de oportunidade"},
	"explorador_abissal": {"name": "Explorador Abissal", "badge": "ESPECIAL", "cost": 70, "desc": "+20 Mov +4 Trab +4 Esc"},
	"purificacao_fumegante": {"name": "Purificação Fumegante", "badge": "ESPECIAL", "cost": 75, "desc": "Remove condições ácidas e miasma"},
	# Ato III
	"martelo_do_trovao": {"name": "Martelo do Trovão", "badge": "COMBATE", "cost": 85, "desc": "Ataque sônico em área"},
	"forja_divina": {"name": "Forja Divina", "badge": "TRABALHO", "cost": 90, "desc": "+10 Trabalho e bônus de armas"},
	"furor_ancestral": {"name": "Furor Ancestral", "badge": "COMBATE", "cost": 85, "desc": "2 ataques corpo a corpo na rodada"},
	"runa_haste": {"name": "Runa da Haste", "badge": "RUNA", "cost": 80, "desc": "Ação extra de combate imediata"},
	"perfuratriz_real": {"name": "Perfuratriz Real", "badge": "ESCAVACAO", "cost": 85, "desc": "+10 Escavação de pilares do trono"},
	"colapso_estrutural": {"name": "Colapso Estrutural", "badge": "ESCAVACAO", "cost": 90, "desc": "Destrói estrutura e atordoa adjacentes"},
	"fogo_alquimico": {"name": "Fogo Alquímico", "badge": "COMBATE", "cost": 95, "desc": "Dano de fogo supremo (derrete o Rei)"},
}

const ACT_CARDS: Dictionary = {
	1: ["marcha_rapida", "golpe_pesado", "bloqueio_ferreo", "trabalho_dobrado", "picareta_reforcada", "tiro_balista", "escudo_quitina"],
	2: ["tocha_sagrada", "lamina_ignea", "armadura_resinosa", "passo_ligeiro", "evasao_tatica", "explorador_abissal", "purificacao_fumegante"],
	3: ["martelo_do_trovao", "forja_divina", "furor_ancestral", "runa_haste", "perfuratriz_real", "colapso_estrutural", "fogo_alquimico"],
}

const CANONICAL_RELICS: Dictionary = {
	"martelo_runico": {"name": "Martelo Rúnico de Karak-Dur", "cost": 50, "rarity": "COMUM", "desc": "1º golpe Melee por combate causa +3 dano."},
	"escudo_ancestral": {"name": "Broquel dos Reis Anões", "cost": 70, "rarity": "INCOMUM", "desc": "Reduz dano recebido em 1 ponto (min 1)."},
	"bolsa_do_mercador": {"name": "Bolsa de Moedas da Guilda", "cost": 45, "rarity": "COMUM", "desc": "+10 de ouro por vitória em combate."},
	"amuleto_ambar": {"name": "Amuleto de Âmbar Resinoso", "cost": 65, "rarity": "INCOMUM", "desc": "Fogueira cura 45% do HP em vez de 30%."},
	"dente_da_viuva": {"name": "Dente da Viúva Canibal", "cost": 90, "rarity": "RARO", "desc": "Críticos causam +4 veneno e curam 2 PV."},
	"tocha_eterna": {"name": "Tocha Eterna de Sulfeto", "cost": 85, "rarity": "RARO", "desc": "+2 dano de fogo contra alvos em chamas."},
	"oleo_alquimico": {"name": "Frasco de Óleo de Incineração", "cost": 55, "rarity": "COMUM", "desc": "Ataques dos heróis causam +1 dano de fogo."},
	"frasco_feromonio": {"name": "Frasco de Feromônio Neutralizador", "cost": 80, "rarity": "RARO", "desc": "Anula a 1ª condição negativa por combate."},
	"coroa_quitina": {"name": "Carapaça de Quitina Cristalizada", "cost": 120, "rarity": "LENDARIO", "desc": "Vantagem no 1º Death Save por combate."},
	"relogio_da_forja": {"name": "Engrenagem Mestra da Forja", "cost": 95, "rarity": "RARO", "desc": "20% de desconto na Forja e +5 ouro ao entrar."},
}

# ── Estado do Mercado ────────────────────────────────────────────────────────
var state: RunState = null
var relic_manager: Variant = null
var rng: RandomNumberGenerator = null

## Slots de Cartas à venda: Array de Dictionaries
## [ { "id": String, "name": String, "cost": int, "badge": String, "desc": String, "sold": bool } ]
var card_inventory: Array[Dictionary] = []

## Slots de Relíquias à venda: Array de Dictionaries
## [ { "id": String, "name": String, "cost": int, "rarity": String, "desc": String, "sold": bool } ]
var relic_inventory: Array[Dictionary] = []

## Controle de expurgo
var purges_performed: int = 0
var purge_used_this_visit: bool = false

# ── Subnós da Interface (Suporte a .tscn e criação programática) ──────────────
var lbl_title: Label = null
var lbl_gold: Label = null
var lbl_deck_count: Label = null
var card_slots_container: HBoxContainer = null
var relic_slots_container: HBoxContainer = null
var purge_panel: PanelContainer = null
var lbl_purge_cost: Label = null
var btn_purge: Button = null
var deck_drawer_panel: PanelContainer = null
var deck_cards_vbox: VBoxContainer = null
var btn_close: Button = null
var lbl_feedback: Label = null

func _init() -> void:
	custom_minimum_size = Vector2(960.0, 640.0)
	size = custom_minimum_size

func _ready() -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	_setup_ui_structure()
	refresh_ui()

## Injeção de dependências e inicialização dos estoques
func setup(p_state: RunState, p_relic_manager: Variant = null, p_rng: RandomNumberGenerator = null) -> void:
	state = p_state
	relic_manager = p_relic_manager
	rng = p_rng if p_rng != null else RandomNumberGenerator.new()
	
	# Sincroniza contador de expurgos com o estado persistente
	if state != null:
		if "card_purges_count" in state:
			purges_performed = int(state.get("card_purges_count"))
		else:
			purges_performed = 0
	
	purge_used_this_visit = false
	generate_inventory()
	
	if is_inside_tree():
		refresh_ui()

# ── Geração de Inventário ────────────────────────────────────────────────────

func generate_inventory() -> void:
	card_inventory.clear()
	relic_inventory.clear()
	
	var cur_act: int = state.act if state != null else 1
	var pool_cards: Array = ACT_CARDS.get(cur_act, ACT_CARDS[1]).duplicate()
	_shuffle_array(pool_cards)
	
	# 1. Gerar 3 Cartas
	var card_count: int = mini(CARD_SLOT_COUNT, pool_cards.size())
	for i in range(card_count):
		var cid: String = pool_cards[i]
		var info: Dictionary = CARD_PRICES.get(cid, {
			"name": cid.capitalize(), "badge": "ACAO", "cost": 50, "desc": "Carta de ação tática"
		})
		var final_cost: int = _calculate_discounted_cost(int(info["cost"]), "card")
		card_inventory.append({
			"id": cid,
			"name": info["name"],
			"badge": info["badge"],
			"cost": final_cost,
			"base_cost": int(info["cost"]),
			"desc": info["desc"],
			"sold": false
		})
	
	# Fallback se não preencheu 3 cartas
	while card_inventory.size() < CARD_SLOT_COUNT:
		var fallback_id: String = "trabalho_%d" % (card_inventory.size() + 1)
		card_inventory.append({
			"id": fallback_id,
			"name": "Trabalho",
			"badge": "TRABALHO",
			"cost": _calculate_discounted_cost(40, "card"),
			"base_cost": 40,
			"desc": "+3 Trabalho básico",
			"sold": false
		})
	
	# 2. Gerar 2 Relíquias (excluindo relíquias já possuídas pelo jogador)
	var empty_relics: Array[String] = []
	var owned_relics: Array[String] = state.relics if state != null else empty_relics
	var available_relic_ids: Array[String] = []
	for rid in CANONICAL_RELICS.keys():
		var norm_rid: String = RelicManager.normalize_id(rid)
		var already_owned: bool = false
		if state != null:
			for owned in state.relics:
				if RelicManager.normalize_id(owned) == norm_rid:
					already_owned = true
					break
		if not already_owned:
			available_relic_ids.append(rid)
	
	# Embaralha com RNG determinístico
	_shuffle_array(available_relic_ids)
	
	var relic_count: int = mini(RELIC_SLOT_COUNT, available_relic_ids.size())
	for i in range(relic_count):
		var rid: String = available_relic_ids[i]
		var rinfo: Dictionary = CANONICAL_RELICS[rid]
		var final_cost: int = _calculate_discounted_cost(int(rinfo["cost"]), "relic")
		relic_inventory.append({
			"id": rid,
			"name": rinfo["name"],
			"rarity": rinfo["rarity"],
			"cost": final_cost,
			"base_cost": int(rinfo["cost"]),
			"desc": rinfo["desc"],
			"sold": false
		})

func _calculate_discounted_cost(base_cost: int, item_type: String) -> int:
	if relic_manager != null and relic_manager.has_method("modify_forge_cost"):
		return relic_manager.modify_forge_cost(item_type, base_cost)
	elif state != null and state.has_relic("relogio_da_forja"):
		return int(round(float(base_cost) * 0.80))
	return base_cost

func _shuffle_array(arr: Array) -> void:
	if arr.is_empty():
		return
	for i in range(arr.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i) if rng != null else 0
		var tmp = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp

# ── Operações Comerciais (Ações) ─────────────────────────────────────────────

## Compra a carta do slot especificado (0 a 2)
func buy_card(slot_index: int) -> bool:
	if slot_index < 0 or slot_index >= card_inventory.size():
		_set_feedback("Slot de carta inválido.")
		return false
	var slot: Dictionary = card_inventory[slot_index]
	if slot["sold"]:
		_set_feedback("Esta carta já foi comprada.")
		return false
	
	var cost: int = int(slot["cost"])
	if state == null:
		_set_feedback("Erro: Estado da expedição não vinculado.")
		return false
	
	if state.gold < cost:
		_set_feedback("Ouro insuficiente! Necessário %d🪙." % cost)
		return false
	
	# Executa transação
	state.spend_gold(cost)
	state.add_card(slot["id"])
	slot["sold"] = true
	
	_set_feedback("Carta '%s' adicionada ao deck!" % slot["name"])
	card_purchased.emit(slot["id"], cost)
	refresh_ui()
	return true

## Compra a relíquia do slot especificado (0 a 1)
func buy_relic(slot_index: int) -> bool:
	if slot_index < 0 or slot_index >= relic_inventory.size():
		_set_feedback("Slot de relíquia inválido.")
		return false
	var slot: Dictionary = relic_inventory[slot_index]
	if slot["sold"]:
		_set_feedback("Esta relíquia já foi comprada.")
		return false
	
	var cost: int = int(slot["cost"])
	if state == null:
		_set_feedback("Erro: Estado da expedição não vinculado.")
		return false
	
	if state.gold < cost:
		_set_feedback("Ouro insuficiente! Necessário %d🪙." % cost)
		return false
	
	# Executa transação
	var norm_relic_id: String = RelicManager.normalize_id(slot["id"])
	state.spend_gold(cost)
	state.add_relic(norm_relic_id)
	if relic_manager != null and relic_manager.has_method("register_relic"):
		relic_manager.register_relic(norm_relic_id)
	slot["sold"] = true
	
	_set_feedback("Relíquia '%s' obtida!" % slot["name"])
	relic_purchased.emit(slot["id"], cost)
	refresh_ui()
	return true

## Calcula o custo atual do serviço de expurgo
func get_current_purge_cost() -> int:
	var base: int = BASE_PURGE_COST + (purges_performed * PURGE_COST_INCREMENT)
	return _calculate_discounted_cost(base, "purge")

## Verifica se o serviço de expurgo está disponível
func can_purge_card() -> Dictionary:
	if state == null:
		return {"can": false, "reason": "Estado ausente."}
	if purge_used_this_visit:
		return {"can": false, "reason": "A Bigorna Ancestral já foi usada nesta visita."}
	if state.deck.size() <= MINIMUM_SAFE_DECK_LIMIT:
		return {"can": false, "reason": "Deck mínimo atingido (%d cartas). Segurança da expedição!" % MINIMUM_SAFE_DECK_LIMIT}
	var cost: int = get_current_purge_cost()
	if state.gold < cost:
		return {"can": false, "reason": "Ouro insuficiente (%d/%d🪙)." % [state.gold, cost]}
	return {"can": true, "cost": cost, "reason": "Disponível"}

## Expulsa/remove uma carta específica do deck
func purge_card(card_id: String) -> bool:
	var check: Dictionary = can_purge_card()
	if not check["can"]:
		_set_feedback(check["reason"])
		return false
	
	if not state.deck.has(card_id):
		_set_feedback("Carta não encontrada no deck.")
		return false
	
	var cost: int = int(check["cost"])
	state.spend_gold(cost)
	var removed: bool = state.remove_card(card_id)
	if not removed:
		state.add_gold(cost) # Rollback de segurança
		_set_feedback("Erro ao remover carta.")
		return false
	
	purges_performed += 1
	if state != null and "card_purges_count" in state:
		state.set("card_purges_count", purges_performed)
	
	purge_used_this_visit = true
	_set_feedback("Carta '%s' expurgada da expedição por %d🪙!" % [card_id, cost])
	card_purged.emit(card_id, cost)
	
	if deck_drawer_panel != null:
		deck_drawer_panel.visible = false
	
	refresh_ui()
	return true

## Encerra as compras na Forja e avança o nó do mapa
func close_forge() -> void:
	if state != null and state.is_active():
		var cur_node: RunNode = state.get_current_node()
		if cur_node != null and not cur_node.visited:
			state.complete_current_node()
	forge_closed.emit()
	queue_free()

# ── Construção e Atualização da Interface (Headless Safe) ─────────────────────

func _setup_ui_structure() -> void:
	# Se a cena já possui nós via .tscn, localiza referências
	lbl_title = get_node_or_null("Header/LblTitle") as Label
	lbl_gold = get_node_or_null("Header/LblGold") as Label
	lbl_deck_count = get_node_or_null("Header/LblDeck") as Label
	card_slots_container = get_node_or_null("Body/CardsSection/CardsHBox") as HBoxContainer
	relic_slots_container = get_node_or_null("Body/RelicsSection/RelicsHBox") as HBoxContainer
	purge_panel = get_node_or_null("Body/PurgeSection/PurgePanel") as PanelContainer
	lbl_purge_cost = get_node_or_null("Body/PurgeSection/PurgePanel/VBox/LblCost") as Label
	btn_purge = get_node_or_null("Body/PurgeSection/PurgePanel/VBox/BtnPurge") as Button
	deck_drawer_panel = get_node_or_null("DeckDrawer") as PanelContainer
	deck_cards_vbox = get_node_or_null("DeckDrawer/Scroll/CardsVBox") as VBoxContainer
	btn_close = get_node_or_null("Footer/BtnClose") as Button
	lbl_feedback = get_node_or_null("Footer/LblFeedback") as Label
	
	# Se os nós forem nulos (instanciação programática direta ou teste headless), constrói hierarquia
	if lbl_title == null:
		_build_programmatic_ui()

func _build_programmatic_ui() -> void:
	for child in get_children():
		child.queue_free()
	
	# Fundo escuro dark fantasy
	var bg: ColorRect = ColorRect.new()
	bg.name = "Background"
	bg.set_anchors_preset(PRESET_FULL_RECT)
	bg.color = Color(0.06, 0.05, 0.07, 0.98)
	add_child(bg)
	
	var main_vbox: VBoxContainer = VBoxContainer.new()
	main_vbox.set_anchors_preset(PRESET_FULL_RECT)
	main_vbox.offset_left = 24
	main_vbox.offset_top = 16
	main_vbox.offset_right = -24
	main_vbox.offset_bottom = -16
	main_vbox.add_theme_constant_override("separation", 14)
	add_child(main_vbox)
	
	# ── Header ─────────────────────────────────────────────────────────────
	var header_hbox: HBoxContainer = HBoxContainer.new()
	header_hbox.name = "Header"
	main_vbox.add_child(header_hbox)
	
	lbl_title = Label.new()
	lbl_title.name = "LblTitle"
	lbl_title.text = "⚒️ FORJA ANÃ DE KUAR-TOR"
	lbl_title.add_theme_font_size_override("font_size", 18)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.85, 0.35))
	lbl_title.size_flags_horizontal = SIZE_EXPAND_FILL
	header_hbox.add_child(lbl_title)
	
	lbl_deck_count = Label.new()
	lbl_deck_count.name = "LblDeck"
	lbl_deck_count.text = "🃏 Deck: 10 cartas"
	lbl_deck_count.add_theme_font_size_override("font_size", 14)
	lbl_deck_count.add_theme_color_override("font_color", Color(0.7, 0.8, 1.0))
	header_hbox.add_child(lbl_deck_count)
	
	lbl_gold = Label.new()
	lbl_gold.name = "LblGold"
	lbl_gold.text = "🪙 50 Ouro"
	lbl_gold.add_theme_font_size_override("font_size", 15)
	lbl_gold.add_theme_color_override("font_color", Color(1.0, 0.84, 0.0))
	header_hbox.add_child(lbl_gold)
	
	# Separator
	main_vbox.add_child(HSeparator.new())
	
	# ── Body (Seções) ──────────────────────────────────────────────────────
	var body_vbox: VBoxContainer = VBoxContainer.new()
	body_vbox.size_flags_vertical = SIZE_EXPAND_FILL
	body_vbox.add_theme_constant_override("separation", 12)
	main_vbox.add_child(body_vbox)
	
	# Seção 1: Cartas
	var lbl_sec_cards: Label = Label.new()
	lbl_sec_cards.text = ">> CARTAS RÚNICAS À VENDA <<"
	lbl_sec_cards.add_theme_font_size_override("font_size", 13)
	lbl_sec_cards.add_theme_color_override("font_color", Color(0.6, 0.8, 1.0))
	body_vbox.add_child(lbl_sec_cards)
	
	card_slots_container = HBoxContainer.new()
	card_slots_container.name = "CardsHBox"
	card_slots_container.custom_minimum_size = Vector2(0, 110)
	card_slots_container.add_theme_constant_override("separation", 12)
	body_vbox.add_child(card_slots_container)
	
	# Seção 2: Relíquias
	var lbl_sec_relics: Label = Label.new()
	lbl_sec_relics.text = ">> MOSTRUÁRIO DE RELÍQUIAS PASSIVAS <<"
	lbl_sec_relics.add_theme_font_size_override("font_size", 13)
	lbl_sec_relics.add_theme_color_override("font_color", Color(0.9, 0.65, 0.3))
	body_vbox.add_child(lbl_sec_relics)
	
	relic_slots_container = HBoxContainer.new()
	relic_slots_container.name = "RelicsHBox"
	relic_slots_container.custom_minimum_size = Vector2(0, 110)
	relic_slots_container.add_theme_constant_override("separation", 12)
	body_vbox.add_child(relic_slots_container)
	
	# Seção 3: Bigorna (Expurgo)
	var lbl_sec_purge: Label = Label.new()
	lbl_sec_purge.text = ">> BIGORNA ANCESTRAL (EXPURGO DE CARTAS) <<"
	lbl_sec_purge.add_theme_font_size_override("font_size", 13)
	lbl_sec_purge.add_theme_color_override("font_color", Color(0.85, 0.35, 0.35))
	body_vbox.add_child(lbl_sec_purge)
	
	purge_panel = PanelContainer.new()
	purge_panel.custom_minimum_size = Vector2(0, 70)
	var purge_style: StyleBoxFlat = StyleBoxFlat.new()
	purge_style.bg_color = Color(0.12, 0.08, 0.08, 0.9)
	purge_style.border_color = Color(0.65, 0.25, 0.25)
	purge_style.set_border_width_all(1)
	purge_style.set_corner_radius_all(6)
	purge_panel.add_theme_stylebox_override("panel", purge_style)
	body_vbox.add_child(purge_panel)
	
	var purge_hbox: HBoxContainer = HBoxContainer.new()
	purge_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	purge_hbox.add_theme_constant_override("separation", 24)
	purge_panel.add_child(purge_hbox)
	
	lbl_purge_cost = Label.new()
	lbl_purge_cost.text = "Custo de Remoção: 50🪙 (Mínimo: 5 cartas no deck)"
	lbl_purge_cost.add_theme_font_size_override("font_size", 12)
	purge_hbox.add_child(lbl_purge_cost)
	
	btn_purge = Button.new()
	btn_purge.text = "Expurgar Carta..."
	btn_purge.custom_minimum_size = Vector2(160, 36)
	btn_purge.pressed.connect(_on_btn_purge_pressed)
	purge_hbox.add_child(btn_purge)
	
	# Gaveta de seleção de carta para expurgo (oculta por padrão)
	deck_drawer_panel = PanelContainer.new()
	deck_drawer_panel.name = "DeckDrawer"
	deck_drawer_panel.visible = false
	deck_drawer_panel.custom_minimum_size = Vector2(0, 100)
	var drawer_style: StyleBoxFlat = StyleBoxFlat.new()
	drawer_style.bg_color = Color(0.04, 0.04, 0.06, 0.95)
	drawer_style.border_color = Color(0.5, 0.4, 0.2)
	drawer_style.set_border_width_all(1)
	drawer_style.set_corner_radius_all(4)
	deck_drawer_panel.add_theme_stylebox_override("panel", drawer_style)
	
	var drawer_scroll: ScrollContainer = ScrollContainer.new()
	drawer_scroll.custom_minimum_size = Vector2(0, 90)
	deck_drawer_panel.add_child(drawer_scroll)
	
	deck_cards_vbox = VBoxContainer.new()
	deck_cards_vbox.size_flags_horizontal = SIZE_EXPAND_FILL
	drawer_scroll.add_child(deck_cards_vbox)
	body_vbox.add_child(deck_drawer_panel)
	
	# ── Footer ─────────────────────────────────────────────────────────────
	var footer_hbox: HBoxContainer = HBoxContainer.new()
	main_vbox.add_child(footer_hbox)
	
	lbl_feedback = Label.new()
	lbl_feedback.text = "Bem-vindo à Forja de Karak-Dur. Aprimore sua expedição."
	lbl_feedback.add_theme_font_size_override("font_size", 12)
	lbl_feedback.add_theme_color_override("font_color", Color(0.8, 0.8, 0.8))
	lbl_feedback.size_flags_horizontal = SIZE_EXPAND_FILL
	footer_hbox.add_child(lbl_feedback)
	
	btn_close = Button.new()
	btn_close.text = "Voltar ao Caminho  ➔"
	btn_close.custom_minimum_size = Vector2(180, 40)
	btn_close.pressed.connect(close_forge)
	footer_hbox.add_child(btn_close)

func refresh_ui() -> void:
	if not is_inside_tree() and lbl_title == null:
		return
	
	# 1. Atualizar contadores
	if lbl_gold != null and state != null:
		lbl_gold.text = "🪙 %d Ouro" % state.gold
	if lbl_deck_count != null and state != null:
		lbl_deck_count.text = "🃏 Deck: %d cartas" % state.deck.size()
	
	# 2. Renderizar Slots de Cartas
	if card_slots_container != null:
		for child in card_slots_container.get_children():
			card_slots_container.remove_child(child)
			child.queue_free()
		
		for i in range(card_inventory.size()):
			var slot: Dictionary = card_inventory[i]
			var panel: PanelContainer = PanelContainer.new()
			panel.size_flags_horizontal = SIZE_EXPAND_FILL
			var style: StyleBoxFlat = StyleBoxFlat.new()
			style.bg_color = Color(0.10, 0.11, 0.16, 0.9) if not slot["sold"] else Color(0.06, 0.06, 0.08, 0.6)
			style.border_color = Color(0.4, 0.6, 0.8) if not slot["sold"] else Color(0.3, 0.3, 0.3)
			style.set_border_width_all(1)
			style.set_corner_radius_all(6)
			panel.add_theme_stylebox_override("panel", style)
			
			var vbox: VBoxContainer = VBoxContainer.new()
			vbox.offset_left = 8
			vbox.offset_top = 8
			vbox.offset_right = -8
			vbox.offset_bottom = -8
			vbox.add_theme_constant_override("separation", 4)
			panel.add_child(vbox)
			
			var lbl_cname: Label = Label.new()
			lbl_cname.text = slot["name"]
			lbl_cname.add_theme_font_size_override("font_size", 12)
			lbl_cname.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0) if not slot["sold"] else Color(0.5, 0.5, 0.5))
			vbox.add_child(lbl_cname)
			
			var lbl_cdesc: Label = Label.new()
			lbl_cdesc.text = slot["desc"]
			lbl_cdesc.add_theme_font_size_override("font_size", 10)
			lbl_cdesc.add_theme_color_override("font_color", Color(0.7, 0.8, 0.7) if not slot["sold"] else Color(0.4, 0.4, 0.4))
			vbox.add_child(lbl_cdesc)
			
			var btn_buy_card: Button = Button.new()
			var idx: int = i
			btn_buy_card.pressed.connect(func(): buy_card(idx))
			
			if slot["sold"]:
				btn_buy_card.text = "[ VENDIDO ]"
				btn_buy_card.disabled = true
			else:
				var cost: int = int(slot["cost"])
				btn_buy_card.text = "Comprar (%d🪙)" % cost
				btn_buy_card.disabled = (state != null and state.gold < cost)
			
			vbox.add_child(btn_buy_card)
			card_slots_container.add_child(panel)
	
	# 3. Renderizar Slots de Relíquias
	if relic_slots_container != null:
		for child in relic_slots_container.get_children():
			relic_slots_container.remove_child(child)
			child.queue_free()
		
		for i in range(relic_inventory.size()):
			var slot: Dictionary = relic_inventory[i]
			var panel: PanelContainer = PanelContainer.new()
			panel.size_flags_horizontal = SIZE_EXPAND_FILL
			var style: StyleBoxFlat = StyleBoxFlat.new()
			style.bg_color = Color(0.14, 0.11, 0.08, 0.9) if not slot["sold"] else Color(0.06, 0.06, 0.08, 0.6)
			style.border_color = Color(0.85, 0.6, 0.25) if not slot["sold"] else Color(0.3, 0.3, 0.3)
			style.set_border_width_all(1)
			style.set_corner_radius_all(6)
			panel.add_theme_stylebox_override("panel", style)
			
			var vbox: VBoxContainer = VBoxContainer.new()
			vbox.offset_left = 8
			vbox.offset_top = 8
			vbox.offset_right = -8
			vbox.offset_bottom = -8
			vbox.add_theme_constant_override("separation", 4)
			panel.add_child(vbox)
			
			var lbl_rname: Label = Label.new()
			lbl_rname.text = "🏺 %s (%s)" % [slot["name"], slot["rarity"]]
			lbl_rname.add_theme_font_size_override("font_size", 12)
			lbl_rname.add_theme_color_override("font_color", Color(1.0, 0.9, 0.6) if not slot["sold"] else Color(0.5, 0.5, 0.5))
			vbox.add_child(lbl_rname)
			
			var lbl_rdesc: Label = Label.new()
			lbl_rdesc.text = slot["desc"]
			lbl_rdesc.add_theme_font_size_override("font_size", 10)
			lbl_rdesc.add_theme_color_override("font_color", Color(0.8, 0.8, 0.7) if not slot["sold"] else Color(0.4, 0.4, 0.4))
			vbox.add_child(lbl_rdesc)
			
			var btn_buy_relic: Button = Button.new()
			var idx: int = i
			btn_buy_relic.pressed.connect(func(): buy_relic(idx))
			
			if slot["sold"]:
				btn_buy_relic.text = "[ VENDIDO ]"
				btn_buy_relic.disabled = true
			else:
				var cost: int = int(slot["cost"])
				btn_buy_relic.text = "Comprar (%d🪙)" % cost
				btn_buy_relic.disabled = (state != null and state.gold < cost)
			
			vbox.add_child(btn_buy_relic)
			relic_slots_container.add_child(panel)
	
	# 4. Atualizar Painel de Expurgo
	if btn_purge != null and lbl_purge_cost != null:
		var pinfo: Dictionary = can_purge_card()
		var cur_cost: int = get_current_purge_cost()
		lbl_purge_cost.text = "Custo de Remoção: %d🪙 (Remoções realizadas: %d | Deck: %d cartas)" % [
			cur_cost, purges_performed, state.deck.size() if state != null else 0
		]
		
		if purge_used_this_visit:
			btn_purge.text = "[ SERVIÇO ESGOTADO ]"
			btn_purge.disabled = true
		elif not pinfo["can"]:
			btn_purge.text = pinfo["reason"]
			btn_purge.disabled = true
		else:
			btn_purge.text = "Expurgar Carta (%d🪙)" % cur_cost
			btn_purge.disabled = false

func _on_btn_purge_pressed() -> void:
	if deck_drawer_panel == null or state == null:
		return
	
	deck_drawer_panel.visible = not deck_drawer_panel.visible
	if not deck_drawer_panel.visible:
		return
	
	# Preencher lista com as cartas do deck atual
	for child in deck_cards_vbox.get_children():
		deck_cards_vbox.remove_child(child)
		child.queue_free()
	
	for cid in state.deck:
		var hbox: HBoxContainer = HBoxContainer.new()
		hbox.add_theme_constant_override("separation", 10)
		
		var lbl: Label = Label.new()
		lbl.text = "🃏 %s" % cid.capitalize()
		lbl.size_flags_horizontal = SIZE_EXPAND_FILL
		lbl.add_theme_font_size_override("font_size", 11)
		hbox.add_child(lbl)
		
		var btn_remove: Button = Button.new()
		btn_remove.text = "Expurgar"
		var target_card: String = cid
		btn_remove.pressed.connect(func(): purge_card(target_card))
		hbox.add_child(btn_remove)
		
		deck_cards_vbox.add_child(hbox)

func _set_feedback(msg: String) -> void:
	if lbl_feedback != null:
		lbl_feedback.text = msg
