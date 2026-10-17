# res://scripts/run/ui/RewardModal.gd
class_name RewardModal
extends Control

## Modal pós-combate da Campanha Roguelike ("Escolha 1 de 3 Cartas").
## Apresenta opções de cartas baseadas no Ato atual, coleta de ouro, relíquias
## para nós Elite/Boss, e botão de Pular ("Skip") para manter o deck enxuto.
## Suporta instanciação programática autônoma e execução segura em GUT Headless.

signal card_selected(card_id: String)
signal card_skipped()
signal gold_collected(amount: int)
signal relic_collected(relic_id: String)
signal reward_completed(summary: Dictionary)

# ── Tabelas de Economia e Pools Canônicos ─────────────────────────────────────
const NODE_GOLD_TABLE: Dictionary = {
	RunNode.NodeType.COMBAT: 15,
	RunNode.NodeType.SIEGE: 20,
	RunNode.NodeType.ELITE: 30,
	RunNode.NodeType.BOSS: 50,
}

const CARD_POOLS: Dictionary = {
	1: [
		{"id": "marcha_rapida", "nome": "Marcha Rápida", "badge": "MARCHA", "mov": 25, "desc": "+25 Movimento tático"},
		{"id": "golpe_pesado", "nome": "Golpe Pesado", "badge": "COMBATE", "desc": "Ataque corpo-a-corpo com +4 dano"},
		{"id": "bloqueio_ferreo", "nome": "Bloqueio Férreo", "badge": "COMBATE", "desc": "+3 CA de Cobertura Temporária"},
		{"id": "trabalho_dobrado", "nome": "Trabalho Dobrado", "badge": "TRABALHO", "trab": 6, "desc": "+6 Trabalho de fortificação"},
		{"id": "picareta_reforcada", "nome": "Picareta Reforçada", "badge": "ESCAVACAO", "esc": 6, "desc": "+6 Escavação de rocha"},
		{"id": "tiro_balista", "nome": "Tiro de Balista", "badge": "COMBATE", "desc": "Disparo perfurante de longo alcance"},
		{"id": "escudo_quitina", "nome": "Escudo de Quitina", "badge": "COMBATE", "desc": "Reação: absorve 5 de dano ácido"}
	],
	2: [
		{"id": "tocha_sagrada", "nome": "Tocha Sagrada", "badge": "ESPECIAL", "desc": "Ilumina raio de 5 células por 2 rodadas"},
		{"id": "lamina_ignea", "nome": "Lâmina Ígnea", "badge": "COMBATE", "desc": "Ataque que causa dano de fogo contínuo"},
		{"id": "armadura_resinosa", "nome": "Armadura Resinosa", "badge": "COMBATE", "desc": "Imunidade a corrosão ácida por 1 turno"},
		{"id": "passo_ligeiro", "nome": "Passo Ligeiro", "badge": "MARCHA", "mov": 35, "desc": "+35 Movimento; ignora terreno difícil"},
		{"id": "evasao_tatica", "nome": "Evasão Tática", "badge": "MARCHA", "desc": "Desengaja sem provocar ataques de oportunidade"},
		{"id": "explorador_abissal", "nome": "Explorador Abissal", "badge": "TRABALHO", "trab": 4, "mov": 20, "desc": "+20 Mov +4 Trab nos túneis"},
		{"id": "purificacao_fumegante", "nome": "Purificação", "badge": "ESPECIAL", "desc": "Remove condições Envenenado e Atordoado"}
	],
	3: [
		{"id": "martelo_do_trovao", "nome": "Martelo do Trovão", "badge": "COMBATE", "desc": "Golpe em área que estilhaça coberturas"},
		{"id": "forja_divina", "nome": "Forja Divina", "badge": "TRABALHO", "trab": 10, "desc": "+10 Trabalho e restaura 10 PV de barricada"},
		{"id": "furor_ancestral", "nome": "Furor Ancestral", "badge": "ESPECIAL", "desc": "Concede 2 ações no mesmo turno"},
		{"id": "runa_haste", "nome": "Runa da Haste", "badge": "ESPECIAL", "desc": "Dobra a velocidade de deslocamento do grupo"},
		{"id": "perfuratriz_real", "nome": "Perfuratriz Real", "badge": "ESCAVACAO", "esc": 12, "desc": "+12 Escavação nos pilares do Rei"},
		{"id": "colapso_estrutural", "nome": "Colapso Estrutural", "badge": "ESCAVACAO", "desc": "Dano massivo contra estruturas e chefes gigantes"},
		{"id": "fogo_alquimico", "nome": "Fogo Alquímico", "badge": "COMBATE", "desc": "Dano de Fogo 2x contra alvos vulneráveis"}
	]
}

const FALLBACK_CARDS: Array[Dictionary] = [
	{"id": "marcha", "nome": "Marcha", "badge": "MARCHA", "mov": 15, "desc": "+15 Movimento"},
	{"id": "trabalho", "nome": "Trabalho", "badge": "TRABALHO", "trab": 3, "desc": "+3 Trabalho"},
	{"id": "escavacao", "nome": "Escavação", "badge": "ESCAVACAO", "esc": 4, "desc": "+4 Escavação"}
]

const ELITE_RELICS: Array[String] = [
	"escudo_ancestral",
	"bolsa_do_mercador",
	"tocha_eterna",
	"oleo_alquimico",
	"frasco_feromonio"
]

const BOSS_RELICS: Array[String] = [
	"martelo_runico",
	"amuleto_ambar",
	"dente_da_viuva",
	"coroa_quitina",
	"relogio_da_forja"
]

# ── Propriedades de Estado da Recompensa ──────────────────────────────────────
var state: RunState = null
var node: RunNode = null
var rng: RandomNumberGenerator = null

var offered_gold: int = 0
var offered_relic_id: String = ""
var card_options: Array[CardData] = []
var selected_card_id: String = ""

var is_claimed: bool = false
var is_card_skipped: bool = false

# Nós visuais internos
var backdrop: ColorRect = null
var modal_panel: PanelContainer = null
var lbl_title: Label = null
var lbl_subtitle: Label = null
var lbl_gold_info: Label = null
var lbl_relic_info: Label = null
var cards_container: HBoxContainer = null
var btn_skip: Button = null

func _init() -> void:
	custom_minimum_size = Vector2(640, 480)
	set_anchors_preset(PRESET_FULL_RECT)
	mouse_filter = MOUSE_FILTER_STOP

func _ready() -> void:
	if backdrop == null and modal_panel == null:
		_build_programmatic_ui()
	refresh_display()

## Configura e popula o modal com base no nó e estado da expedição
func setup(p_state: RunState, p_node: RunNode, p_rng: RandomNumberGenerator = null, p_options: Dictionary = {}) -> void:
	state = p_state
	node = p_node
	rng = p_rng if p_rng != null else RandomNumberGenerator.new()
	is_claimed = false
	is_card_skipped = false
	selected_card_id = ""

	var act: int = state.act if state != null else 1
	var ntype: int = node.type if node != null else RunNode.NodeType.COMBAT

	# 1. Determinar Ouro
	offered_gold = int(p_options.get("gold", NODE_GOLD_TABLE.get(ntype, 15)))

	# 2. Determinar Relíquia (Garantida em Elite e Boss)
	if p_options.has("relic_id"):
		offered_relic_id = RelicManager.normalize_id(String(p_options["relic_id"]))
	elif ntype == RunNode.NodeType.BOSS:
		offered_relic_id = _select_available_relic(BOSS_RELICS)
	elif ntype == RunNode.NodeType.ELITE:
		offered_relic_id = _select_available_relic(ELITE_RELICS)
	else:
		offered_relic_id = ""

	# 3. Gerar Draft de 3 Cartas
	card_options = _generate_card_options(act)

	refresh_display()

## Constrói os elementos de interface procedural de forma headless-safe
func _build_programmatic_ui() -> void:
	for c in get_children():
		c.queue_free()

	backdrop = ColorRect.new()
	backdrop.name = "Backdrop"
	backdrop.color = Color(0.04, 0.05, 0.08, 0.88)
	backdrop.set_anchors_preset(PRESET_FULL_RECT)
	add_child(backdrop)

	var center: CenterContainer = CenterContainer.new()
	center.set_anchors_preset(PRESET_FULL_RECT)
	add_child(center)

	modal_panel = PanelContainer.new()
	modal_panel.name = "ModalPanel"
	modal_panel.custom_minimum_size = Vector2(580, 420)
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.09, 0.14, 0.98)
	sb.border_color = Color(0.85, 0.70, 0.25, 0.95)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 24
	sb.content_margin_right = 24
	sb.content_margin_top = 20
	sb.content_margin_bottom = 20
	modal_panel.add_theme_stylebox_override("panel", sb)
	center.add_child(modal_panel)

	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	modal_panel.add_child(vbox)

	lbl_title = Label.new()
	lbl_title.text = "⚔️ ESPÓLIOS DE BATALHA"
	lbl_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_title.add_theme_font_size_override("font_size", 20)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.35))
	vbox.add_child(lbl_title)

	lbl_subtitle = Label.new()
	lbl_subtitle.text = "Escolha 1 carta para adicionar ao seu deck permanente da run:"
	lbl_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_subtitle.add_theme_font_size_override("font_size", 12)
	lbl_subtitle.add_theme_color_override("font_color", Color(0.8, 0.85, 0.9))
	vbox.add_child(lbl_subtitle)

	# Linha de Ouro e Relíquia
	var rewards_hbox: HBoxContainer = HBoxContainer.new()
	rewards_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	rewards_hbox.add_theme_constant_override("separation", 24)
	vbox.add_child(rewards_hbox)

	lbl_gold_info = Label.new()
	lbl_gold_info.text = "🪙 +15 Ouro"
	lbl_gold_info.add_theme_font_size_override("font_size", 13)
	lbl_gold_info.add_theme_color_override("font_color", Color(1.0, 0.85, 0.2))
	rewards_hbox.add_child(lbl_gold_info)

	lbl_relic_info = Label.new()
	lbl_relic_info.text = ""
	lbl_relic_info.add_theme_font_size_override("font_size", 13)
	lbl_relic_info.add_theme_color_override("font_color", Color(0.4, 0.85, 1.0))
	rewards_hbox.add_child(lbl_relic_info)

	# Container das 3 Cartas
	cards_container = HBoxContainer.new()
	cards_container.alignment = BoxContainer.ALIGNMENT_CENTER
	cards_container.add_theme_constant_override("separation", 16)
	cards_container.custom_minimum_size = Vector2(0, 160)
	vbox.add_child(cards_container)

	# Botão de Pular (Skip)
	var bottom_hbox: HBoxContainer = HBoxContainer.new()
	bottom_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	bottom_hbox.add_theme_constant_override("separation", 12)
	vbox.add_child(bottom_hbox)

	btn_skip = Button.new()
	btn_skip.name = "BtnSkip"
	btn_skip.text = "Pular Carta (Manter Deck Enxuto) ⏩"
	btn_skip.custom_minimum_size = Vector2(260, 34)
	btn_skip.focus_mode = Control.FOCUS_NONE
	var skip_style: StyleBoxFlat = StyleBoxFlat.new()
	skip_style.bg_color = Color(0.2, 0.22, 0.28, 0.9)
	skip_style.border_color = Color(0.5, 0.55, 0.65)
	skip_style.set_border_width_all(1)
	skip_style.set_corner_radius_all(6)
	btn_skip.add_theme_stylebox_override("normal", skip_style)
	btn_skip.pressed.connect(_on_btn_skip_pressed)
	bottom_hbox.add_child(btn_skip)

## Atualiza a interface gráfica com os valores atuais
func refresh_display() -> void:
	if lbl_gold_info != null:
		lbl_gold_info.text = "🪙 +%d Ouro" % offered_gold
	
	if lbl_relic_info != null:
		if not offered_relic_id.is_empty():
			var display_name: String = offered_relic_id.capitalize()
			if ForgeScreen.CANONICAL_RELICS.has(offered_relic_id):
				display_name = String(ForgeScreen.CANONICAL_RELICS[offered_relic_id]["name"])
			lbl_relic_info.text = "💎 Relíquia: %s" % display_name
			lbl_relic_info.visible = true
		else:
			lbl_relic_info.text = ""
			lbl_relic_info.visible = false

	if cards_container != null:
		for child in cards_container.get_children():
			child.queue_free()

		for i in range(card_options.size()):
			var cdata: CardData = card_options[i]
			var card_ui: CardUI = CardUI.new()
			card_ui.setup(cdata, i)
			var target_id: String = cdata.id
			card_ui.card_selected.connect(func(_d, _idx): select_card(target_id))
			card_ui.card_played_requested.connect(func(_d, _z): select_card(target_id))
			cards_container.add_child(card_ui)

## Seleciona 1 das 3 cartas ofertadas e conclui a recompensa
func select_card(card_id: String) -> bool:
	if is_claimed or card_id.is_empty():
		return false

	var valid: bool = false
	for c in card_options:
		if c.id == card_id:
			valid = true
			break
	if not valid:
		return false

	is_claimed = true
	selected_card_id = card_id

	# 1. Adicionar Carta ao Deck da Run
	if state != null:
		state.add_card(card_id)
	card_selected.emit(card_id)

	# 2. Conceder Ouro e Relíquia
	_apply_gold_and_relic()

	# 3. Finalizar e Fechar Modal
	_finish_reward()
	return true

## Pula a escolha de cartas sem alterar o deck
func skip_card() -> bool:
	if is_claimed:
		return false

	is_claimed = true
	is_card_skipped = true
	selected_card_id = ""
	card_skipped.emit()

	# Conceder Ouro e Relíquia mesmo pulando a carta
	_apply_gold_and_relic()

	_finish_reward()
	return true

func _apply_gold_and_relic() -> void:
	if state != null:
		if offered_gold > 0:
			state.add_gold(offered_gold)
			gold_collected.emit(offered_gold)

		if not offered_relic_id.is_empty():
			var norm_id: String = RelicManager.normalize_id(offered_relic_id)
			var added: bool = state.add_relic(norm_id)
			if added:
				relic_collected.emit(norm_id)
			else:
				# Se já possuía a relíquia, compensa com bônus monetário
				state.add_gold(50)
				gold_collected.emit(50)

func _finish_reward() -> void:
	var summary: Dictionary = {
		"card_id": selected_card_id,
		"skipped": is_card_skipped,
		"gold": offered_gold,
		"relic_id": offered_relic_id
	}
	reward_completed.emit(summary)

	if is_inside_tree():
		var tw: Tween = create_tween()
		if tw != null:
			tw.tween_property(self, "modulate:a", 0.0, 0.2)
			tw.tween_callback(queue_free)
		else:
			queue_free()

func _on_btn_skip_pressed() -> void:
	skip_card()

# ── Gerador de Cartas e Relíquias ─────────────────────────────────────────────

func _generate_card_options(act: int) -> Array[CardData]:
	var result: Array[CardData] = []
	var pool: Array = CARD_POOLS.get(act, CARD_POOLS[1]).duplicate()
	var picked_ids: Array[String] = []

	# Embaralhar se houver RNG injetado
	if rng != null:
		_shuffle_array(pool, rng)

	for entry in pool:
		if picked_ids.has(entry["id"]):
			continue
		picked_ids.append(entry["id"])
		var cdata: CardData = _create_card_from_dict(entry)
		result.append(cdata)
		if result.size() >= 3:
			break

	# Fallback para cartas básicas se o pool for menor que 3
	var fb_idx: int = 0
	while result.size() < 3 and fb_idx < FALLBACK_CARDS.size():
		var fb_entry: Dictionary = FALLBACK_CARDS[fb_idx]
		if not picked_ids.has(fb_entry["id"]):
			picked_ids.append(fb_entry["id"])
			result.append(_create_card_from_dict(fb_entry))
		fb_idx += 1

	return result

func _create_card_from_dict(d: Dictionary) -> CardData:
	var c: CardData = CardData.new()
	c.id = d.get("id", "carta_generica")
	c.card_name = d.get("nome", c.id.capitalize())
	c.badge = d.get("badge", CardData.BADGE_MARCHA)
	c.card_type = CardData.TYPE_ACAO
	c.description = d.get("desc", "")
	c.movement = int(d.get("mov", 0))
	c.work = int(d.get("trab", 0))
	c.excavation = int(d.get("esc", 0))
	c.effect_value = maxi(c.movement, maxi(c.work, c.excavation))
	return c

func _select_available_relic(relic_list: Array[String]) -> String:
	var pool: Array[String] = []
	for r in relic_list:
		var norm_r: String = RelicManager.normalize_id(r)
		if state == null or not state.has_relic(norm_r):
			pool.append(norm_r)

	if pool.is_empty():
		return ""
	var idx: int = rng.randi_range(0, pool.size() - 1) if rng != null else 0
	return pool[idx]

func _shuffle_array(arr: Array, p_rng: RandomNumberGenerator) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j: int = p_rng.randi_range(0, i)
		var tmp = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp
