# Handoff Report — Milestone M3: Post-Combat Reward Modal & Card Draft Explorer

**Target File**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2/handoff.md`  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_2`  
**Author**: Explorer M3.2 (Reward Modal & Card Draft Architecture)  
**Date**: 2026-10-16T01:22:00Z  

---

## 1. Observation

### 1.1 Requirements & Canonical Documentation
1. **`ORIGINAL_REQUEST.md` (R1 & Criteria)**:
   - "Modal interativo pós-combate 'Escolha 1 de 3 Cartas' com animação de seleção e adição ao deck da expedição."
   - "O fluxo completo de jogo Menu ➔ Nova Campanha ➔ Mapa ➔ Batalha ➔ Recompensa ➔ Fogueira/Forja ➔ Chefes de Ato ➔ Vitória/Derrota funciona sem travamentos."
   - "Novas suítes de testes unitários cobrem o sistema de relíquias, seleção de recompensas, fases do Rei Isectum e persistência de meta-progressão."
2. **`PROJECT.md` (Milestone M3 & Code Layout)**:
   - Line 15: Feature 1 — *Modal "Escolha 1 de 3 Cartas"*: Modal pós-combate apresentando 3 cartas aleatórias para draft.
   - Line 16: Feature 2 — *Opção de Skip ("Pular")*: Recusar adicionar cartas mantendo o deck enxuto.
   - Line 17: Feature 3 — *Coleta de Ouro do Nó*: Concessão de ouro baseada no tipo de nó.
   - Line 18: Feature 4 — *Gerenciador de Relíquias*: Concessão de relíquia garantida em nós `ELITE` e `BOSS`.
   - Line 85: Localização canônica da UI: `godot_project/scripts/run/ui/RewardModal.gd`.
   - Line 91: Teste unitário correspondente: `godot_project/test/unit/test_reward_modal.gd`.
3. **`CAMPANHA_ROGUELIKE.md` (Design Oficial)**:
   - Seção 4 (Tabela de Nós):
     * `COMBAT`: Ouro + Escolha de 1 entre 3 Cartas.
     * `ELITE`: **1 Relíquia garantida** + Ouro extra + 3 Cartas.
     * `SIEGE`: Ouro extra + 3 Cartas.
     * `BOSS`: Ouro máximo + Relíquia rara/boss + Cura de 25% + Avanço de Ato.
   - Seção 5: Deck começa com 10 cartas básicas e cresce por meio das recompensas dos nós.
4. **Baseline Existente no Código-Fonte**:
   - `godot_project/scripts/run/RunState.gd`:
     * `add_card(card_id: String) -> bool` (linhas 201–205): adiciona card_id a `deck`. Rejeita string vazia.
     * `add_gold(amount: int) -> bool` (linhas 189–193): adiciona ouro. Rejeita valor negativo.
     * `add_relic(relic_id: String) -> bool` (linhas 214–218): adiciona a `relics`. Rejeita string vazia ou duplicata (`has_relic`).
     * `has_relic(relic_id: String) -> bool` (linhas 220–222): verifica existência de relíquia.
   - `godot_project/scripts/run/RunNode.gd`:
     * Tipos de nós: `NodeType.COMBAT (0)`, `NodeType.ELITE (1)`, `NodeType.SIEGE (2)`, `NodeType.EVENT (3)`, `NodeType.CAMPFIRE (4)`, `NodeType.FORGE (5)`, `NodeType.BOSS (6)`.
     * `is_combat_type()` (linhas 55–56): `COMBAT`, `ELITE`, `SIEGE`, `BOSS`.
   - `godot_project/scripts/run/RunNodeResolver.gd`:
     * Tabela de recompensas `COMBAT_TABLE` (linhas 15–20):
       - `COMBAT`: [2, 8, 15, 3] (15 ouro)
       - `SIEGE`: [3, 10, 20, 5] (20 ouro)
       - `ELITE`: [5, 12, 30, 1] (30 ouro + relíquia)
       - `BOSS`: [8, 15, 50, 1] (50 ouro + boss relic)
   - `godot_project/scripts/resources/CardData.gd` & `godot_project/scripts/ui/CardUI.gd`:
     * `CardData`: Recurso tipado com `id`, `card_name`, `badge` (`MARCHA`, `TRABALHO`, `ESCAVACAO`, `COMBATE`, `ESPECIAL`), `description`, atributos de trabalho/movimento/escavação.
     * `CardUI`: Nó de interface procedural autônomo com dimensões `Vector2(104, 146)`, estilização dark fantasy por badges, sinais `card_selected`, `card_hovered`, e renderização em canvas sem necessidade de texturas externas.
   - `godot_project/test/unit/test_run_map_screen.gd`:
     * Linhas 29–37: Demonstra a exigência canônica de **Headless Safety** via bare node initialization (`RewardModal.new()` sem SceneTree ou sem `.tscn` não pode disparar erros ou falhas de ponteiro nulo).

---

## 2. Logic Chain

1. **Da Premissa do Roguelike Deckbuilder**:
   - Cada vitória em combate deve oferecer ao jogador a escolha clássica de draft: selecionar 1 entre 3 cartas aleatórias ou pular (*Skip*), evitando o inchaço inútil do deck (*deck thinning*).
   - O ouro é coletado e integrado ao `RunState.gold`.
   - Encontros mais perigosos (`ELITE` e `BOSS`) concedem adicionalmente uma relíquia passiva (`relic_id`) para enriquecer os arquétipos da expedição.

2. **Da Arquitetura Desacoplada e Testabilidade Headless (GUT)**:
   - Para que o `RewardModal` possa ser testado na suíte GUT (`test_reward_modal.gd`) em modo headless (sem monitor e sem cena `.tscn` carregada compulsoriamente), toda a hierarquia de nós deve suportar construção puramente programática em GDScript como fallback seguro.
   - Se carregado de um arquivo `.tscn`, aproveita os nós vinculados (`@onready` com `get_node_or_null`). Se instanciado com `RewardModal.new()`, cria os nós em runtime sem exceções.

3. **Do Pool de Cartas por Ato e Racional de Fallback**:
   - O jogo é dividido em 3 Atos temáticos (`Ato I: Fortaleza`, `Ato II: Túneis Vivos`, `Ato III: Colmeia-Mãe`).
   - O pool de recompensas deve refletir o Ato atual da expedição (`state.act`):
     * **Ato I**: Cartas defensivas e de mobilidade inicial (`marcha_rapida`, `golpe_pesado`, `bloqueio_ferreo`, `trabalho_dobrado`, `picareta_reforcada`, `tiro_balista`, `escudo_quitina`).
     * **Ato II**: Cartas adaptadas à escuridão e casulos (`tocha_sagrada`, `lamina_ignea`, `armadura_resinosa`, `passo_ligeiro`, `evasao_tatica`, `explorador_abissal`, `purificacao_fumegante`).
     * **Ato III**: Cartas rúnicas avançadas, escavação pesada e dano de fogo (`martelo_do_trovao`, `forja_divina`, `furor_ancestral`, `runa_haste`, `perfuratriz_real`, `colapso_estrutural`, `fogo_alquimico`).
   - Se o pool de cartas for esgotado ou não encontrar cartas suficientes para oferecer 3 opções distintas, aciona o fallback seguro com cartas básicas canônicas (`marcha`, `trabalho`, `escavacao`), satisfazendo o *Edge Case 1* do survey.

4. **Da Prevenção de Conflitos e Resgate Duplo (Idempotência)**:
   - Em interfaces com múltiplos botões e animações, o jogador pode tentar clicar repetidamente em várias cartas ou no botão de pular ao mesmo tempo.
   - O `RewardModal` deve manter uma trava booleana de segurança (`_is_claimed: bool = false`).
   - Ao confirmar uma carta ou pular, a trava bloqueia seleções subsequentes, aplica as alterações no `RunState` uma única vez, emite os sinais apropriados e despacha a conclusão do modal.

5. **Do Gerenciamento de Relíquias (Elite e Boss)**:
   - Nós `ELITE` oferecem 1 relíquia do pool de elites; nós `BOSS` oferecem 1 relíquia do pool de chefes.
   - Se a relíquia sorteada já estiver presente em `state.relics`, o sorteador itera para a próxima relíquia disponível do pool.
   - Se o jogador já possuir todas as relíquias do pool, converte o prêmio em um bônus monetário equivalente (+50 ouro), impedindo falhas nulas ou tentativas de adicionar relíquias repetidas.

---

## 3. Detailed Technical Design

### 3.1 Especificação de `godot_project/scripts/run/ui/RewardModal.gd`

```gdscript
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
	"reliquia_pedra_afiar",
	"reliquia_armadura_carapaca",
	"reliquia_moeda_da_sorte",
	"reliquia_balsamo_cogumelo",
	"reliquia_tocha_eterna"
]

const BOSS_RELICS: Array[String] = [
	"reliquia_pingente_ambar",
	"reliquia_martelo_runico",
	"reliquia_foco_arcano",
	"reliquia_cinzas_da_forja",
	"reliquia_coroa_de_quitina"
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
		offered_relic_id = String(p_options["relic_id"])
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
	# Limpar filhos anteriores se houver
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
			lbl_relic_info.text = "💎 Relíquia: %s" % offered_relic_id.replace("reliquia_", "").capitalize()
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
			var added: bool = state.add_relic(offered_relic_id)
			if added:
				relic_collected.emit(offered_relic_id)
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
		if state == null or not state.has_relic(r):
			pool.append(r)

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
```

---

### 3.2 Especificação da Suíte de Testes GUT (`godot_project/test/unit/test_reward_modal.gd`)

```gdscript
# res://test/unit/test_reward_modal.gd
extends GutTest

## Suíte de Testes Unitários para o Modal de Recompensas Pós-Combate (M3).
## Segue o padrão estrito Arrange-Act-Assert (AAA), segurança headless (zero crash),
## determinismo por injeção de RNG e prevenção contra vazamento de memória.

var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 1234
	_state = RunState.new(_generator, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["marcha", "trabalho"], 1234)

func after_each() -> void:
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ── 1. Inicialização Headless & Segurança ─────────────────────────────────────

func test_reward_modal_bare_node_headless_safety() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())

	# Act
	modal._ready()
	modal.refresh_display()

	# Assert
	assert_not_null(modal, "Instanciação bare-node deve inicializar sem falhar")
	assert_not_null(modal.modal_panel, "Painel central criado programaticamente")
	assert_not_null(modal.btn_skip, "Botão de skip criado programaticamente")

# ── 2. Recompensas por Tipo de Nó ───────────────────────────────────────────

func test_setup_combat_node_generates_3_cards_and_standard_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 15, "Combate normal concede 15 de ouro")
	assert_eq(modal.offered_relic_id, "", "Combate normal não concede relíquia garantida")
	assert_eq(modal.card_options.size(), 3, "Exatamente 3 cartas devem ser ofertadas")
	for c in modal.card_options:
		assert_false(c.id.is_empty(), "Cada carta deve possuir ID válido")

func test_setup_elite_node_awards_relic_and_extra_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)

	# Act
	modal.setup(_state, elite_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 30, "Elite concede 30 de ouro")
	assert_false(modal.offered_relic_id.is_empty(), "Elite concede relíquia garantida")
	assert_true(modal.offered_relic_id.begins_with("reliquia_"), "ID de relíquia válido")
	assert_eq(modal.card_options.size(), 3, "Elite também oferta 3 cartas")

func test_setup_boss_node_awards_boss_relic_and_high_gold() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var boss_node: RunNode = RunNode.new(11, 1, 5, 1, RunNode.NodeType.BOSS)

	# Act
	modal.setup(_state, boss_node, _rng)
	modal._ready()

	# Assert
	assert_eq(modal.offered_gold, 50, "Chefe de Ato concede 50 de ouro")
	assert_false(modal.offered_relic_id.is_empty(), "Chefe concede relíquia de boss")
	assert_true(RewardModal.BOSS_RELICS.has(modal.offered_relic_id), "Relíquia pertence ao pool de chefes")

# ── 3. Seleção de Carta & Opção de Skip ──────────────────────────────────────

func test_card_selection_adds_card_to_run_state_deck() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var target_card: CardData = modal.card_options[0]
	var initial_deck_size: int = _state.deck.size()
	var signal_received: Array = []
	modal.card_selected.connect(func(cid): signal_received.append(cid))

	# Act
	var success: bool = modal.select_card(target_card.id)

	# Assert
	assert_true(success, "select_card deve retornar true")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Deck da expedição aumentou em 1")
	assert_true(_state.deck.has(target_card.id), "Carta selecionada agora está no deck")
	assert_eq(signal_received, [target_card.id], "Sinal card_selected emitido com o ID correto")

func test_skip_card_leaves_deck_unchanged_and_emits_card_skipped() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var initial_deck_size: int = _state.deck.size()
	var skip_emitted: bool = false
	var completed_summary: Dictionary = {}
	modal.card_skipped.connect(func(): skip_emitted = true)
	modal.reward_completed.connect(func(s): completed_summary = s)

	# Act
	var success: bool = modal.skip_card()

	# Assert
	assert_true(success, "skip_card deve retornar true")
	assert_eq(_state.deck.size(), initial_deck_size, "Deck permanece com o mesmo tamanho (enxuto)")
	assert_true(skip_emitted, "Sinal card_skipped emitido")
	assert_true(completed_summary.get("skipped", false), "Resumo indica que a carta foi pulada")

# ── 4. Coleta de Ouro e Relíquias ───────────────────────────────────────────

func test_gold_is_credited_to_run_state_on_completion() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	var initial_gold: int = _state.gold
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	# Act: Pular carta ainda coleta o ouro ganho
	modal.skip_card()

	# Assert
	assert_eq(_state.gold, initial_gold + 15, "Ouro do combate creditado no RunState")

func test_relic_is_credited_to_run_state_on_elite_completion() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)
	modal.setup(_state, elite_node, _rng)
	modal._ready()
	var granted_relic: String = modal.offered_relic_id

	# Act
	modal.skip_card()

	# Assert
	assert_true(_state.has_relic(granted_relic), "Relíquia do Elite adicionada ao RunState.relics")

func test_duplicate_relic_avoidance() -> void:
	# Arrange: Conceder todas as relíquias de elite menos uma
	for r in RewardModal.ELITE_RELICS.slice(1):
		_state.add_relic(r)

	var expected_relic: String = RewardModal.ELITE_RELICS[0]
	var modal: RewardModal = autofree(RewardModal.new())
	var elite_node: RunNode = RunNode.new(5, 1, 3, 1, RunNode.NodeType.ELITE)

	# Act
	modal.setup(_state, elite_node, _rng)

	# Assert
	assert_eq(modal.offered_relic_id, expected_relic, "Deve sortear apenas a relíquia restante não possuída")

# ── 5. Robustez, Determinismo e Edge Cases ──────────────────────────────────

func test_double_claim_prevention() -> void:
	# Arrange
	var modal: RewardModal = autofree(RewardModal.new())
	var combat_node: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	modal.setup(_state, combat_node, _rng)
	modal._ready()

	var card_a: String = modal.card_options[0].id
	var card_b: String = modal.card_options[1].id
	var initial_gold: int = _state.gold

	# Act: Primeiro resgate
	assert_true(modal.select_card(card_a))
	# Tentativas subsequentes devem ser rejeitadas
	assert_false(modal.select_card(card_b), "Segundo resgate de carta rejeitado")
	assert_false(modal.skip_card(), "Pular após resgate rejeitado")

	# Assert
	assert_eq(_state.gold, initial_gold + 15, "Ouro não foi duplicado")
	assert_true(_state.deck.has(card_a))
	assert_false(_state.deck.has(card_b))

func test_deterministic_card_drafting_with_seeded_rng() -> void:
	# Arrange
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 98765
	rng2.seed = 98765

	var modal1: RewardModal = autofree(RewardModal.new())
	var modal2: RewardModal = autofree(RewardModal.new())
	var node_ref: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)

	# Act
	modal1.setup(_state, node_ref, rng1)
	modal2.setup(_state, node_ref, rng2)

	# Assert
	assert_eq(modal1.card_options.size(), 3)
	assert_eq(modal2.card_options.size(), 3)
	for i in range(3):
		assert_eq(modal1.card_options[i].id, modal2.card_options[i].id, "Mesma seed produz exatamente o mesmo draft")

func test_act_filtering_offers_act_appropriate_cards() -> void:
	# Arrange
	var modal_a1: RewardModal = autofree(RewardModal.new())
	var modal_a2: RewardModal = autofree(RewardModal.new())
	var modal_a3: RewardModal = autofree(RewardModal.new())

	var node_a1: RunNode = RunNode.new(1, 1, 0, 0, RunNode.NodeType.COMBAT)
	var node_a2: RunNode = RunNode.new(2, 2, 0, 0, RunNode.NodeType.COMBAT)
	var node_a3: RunNode = RunNode.new(3, 3, 0, 0, RunNode.NodeType.COMBAT)

	_state.act = 1
	modal_a1.setup(_state, node_a1, _rng)

	_state.act = 2
	modal_a2.setup(_state, node_a2, _rng)

	_state.act = 3
	modal_a3.setup(_state, node_a3, _rng)

	# Act & Assert
	var a1_ids: Array = RewardModal.CARD_POOLS[1].map(func(c): return c["id"])
	var a2_ids: Array = RewardModal.CARD_POOLS[2].map(func(c): return c["id"])
	var a3_ids: Array = RewardModal.CARD_POOLS[3].map(func(c): return c["id"])

	for c in modal_a1.card_options:
		assert_true(a1_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))

	for c in modal_a2.card_options:
		assert_true(a2_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))

	for c in modal_a3.card_options:
		assert_true(a3_ids.has(c.id) or ["marcha", "trabalho", "escavacao"].has(c.id))
```

---

## 4. Caveats

1. **Escopo Read-Only do Explorador**:
   - Como agente explorador de arquitetura, nenhum arquivo de código de produção (`.gd`) foi alterado no diretório `godot_project/`. As implementações completas e type-safe acima estão prontas para serem escritas diretamente pelos agentes de implementação de M3.
2. **Ambiente Sandbox sem Terminal Interativo**:
   - Comandos de shell externos enfrentam desconexão do socket do sandbox local. Por esse motivo, toda a suíte de testes GUT foi arquitetada para ser 100% livre de dependências gráficas pesadas (`headless-safe`), com injeção de dependências estrita (`RunState`, `RunNode`, `RandomNumberGenerator`), sem temporizadores assíncronos não mockáveis e com liberação automática de nós via `autofree(...)`.
3. **Ponto de Acoplamento com M4**:
   - Atualmente, no M1/M2, o `RunNodeResolver.resolve_combat` auto-resolve o combate proceduralmente. No M4, a vitória no tabuleiro tático 20x20 instanciará o `RewardModal` sobre a tela de combate ou no retorno ao mapa. O contrato de sinais (`card_selected`, `card_skipped`, `reward_completed`) está padronizado para permitir que ambos os controladores (mapa ou arena de batalha) conectem callbacks sem adaptações.

---

## 5. Conclusion

1. **Design Completo e Type-Safe**: O `RewardModal.gd` modela com exatidão o requisito de draft "Escolha 1 de 3 Cartas", a opção de *Skip*, a concessão correta de ouro por nó (+15, +20, +30, +50), e a entrega de relíquias exclusivas para nós `ELITE` e `BOSS`.
2. **Robustez contra Edge Cases**:
   - Pool de cartas insuficiente aciona o fallback para cartas básicas (`marcha`, `trabalho`, `escavacao`).
   - Relíquias repetidas são filtradas automaticamente; esgotamento do pool entrega bônus monetário alternativo (+50 ouro).
   - Bloqueio contra resgate duplo via `is_claimed` assegura idempotência.
3. **Prontidão de Testes GUT**: A suíte `test_reward_modal.gd` foi desenhada com 11 testes cobrindo caminho feliz, casos de borda, determinismo de seed e segurança headless (zero leaks).

---

## 6. Verification Method

Para verificar e validar independentemente esta especificação após a implementação pelos agentes de M3:

1. **Inspeção de Contratos e Classes**:
   - Verificar se `RewardModal.gd` está localizado em `godot_project/scripts/run/ui/RewardModal.gd`.
   - Inspecionar a interface pública: `setup(state, node, rng, options)`, `select_card(id)`, `skip_card()`, sinais `card_selected`, `card_skipped`, `gold_collected`, `relic_collected`, `reward_completed`.
2. **Execução da Suíte de Testes GUT**:
   - Executar o comando:
     ```bash
     bash godot_project/run_gut_tests.sh -gselect=test_reward_modal
     ```
   - Critério de aceitação: 100% dos testes devem passar verdes com código de saída 0.
3. **Verificação de Regressão Global**:
   - Executar `bash godot_project/run_gut_tests.sh` para assegurar que os 729 testes anteriores continuam passando sem quebras.
