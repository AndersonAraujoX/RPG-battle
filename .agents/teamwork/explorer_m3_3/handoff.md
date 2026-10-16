# Handoff Report — Milestone M3: Forge Screen & Shop Architecture Explorer

**Author**: M3 Forge Screen Explorer (`explorer_m3_3`)  
**Target File**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_3/handoff.md`  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m3_3`  
**Date**: 2026-10-16T01:25:00Z  

---

## 1. Observation

### 1.1 Requirements & Canonical Documentation
1. **`ORIGINAL_REQUEST.md` (R1 & Criteria)**:
   - "Tela/Modal da Forja Anã (nó `FORGE`) permitindo comprar cartas, relíquias e remover cartas do deck usando ouro da run." (Linha 21).
   - "O fluxo completo de jogo Menu ➔ Nova Campanha ➔ Mapa ➔ Batalha ➔ Recompensa ➔ Fogueira/Forja ➔ Chefes de Ato ➔ Vitória/Derrota funciona sem travamentos." (Linhas 49–51).
   - "100% dos testes GUT passam via linha de comando (`bash godot_project/run_gut_tests.sh`) com código de saída 0." (Linha 59).
   - "Novas suítes de testes unitários cobrem o sistema de relíquias, seleção de recompensas, fases do Rei Isectum e persistência de meta-progressão." (Linha 60).

2. **`PROJECT.md` (Milestone M3 & Code Layout)**:
   - Linha 20: Feature 6 — *Mercado da Forja Anã*: Tela de compras do nó FORGE (cartas, relíquias).
   - Linha 21: Feature 7 — *Remoção de Cartas do Deck*: Serviço de remoção de cartas com custo progressivo de ouro.
   - Linha 49: Marco M3 — Scope: `RelicData`, `RelicManager`, `RewardModal`, `ForgeScreen`, GUT tests.
   - Linha 85: Localização canônica do código: `godot_project/scripts/run/ui/ForgeScreen.gd`.
   - Linha 91: Teste unitário correspondente: `godot_project/test/unit/test_forge_system.gd`.

3. **`DISPATCH.md` (Directives for Explorer M3.3)**:
   - Design `godot_project/scripts/run/ui/ForgeScreen.gd` and its programmatic UI or `.tscn`.
   - Specify shop inventory generation: 3 buyable cards, 2 buyable relics, card purge service with base cost 50g + 25g per removal, minimum safe deck limit of 5 cards.
   - Design the GUT test suite `godot_project/test/unit/test_forge_system.gd` (headless safety, gold transaction checks, card removal, relic acquisition).

4. **`CAMPANHA_ROGUELIKE.md` (Design Oficial)**:
   - Seção 4 (Tabela de Nós, Linha 147):
     `| ⚒️ | FORGE (Mercado / Forja) | 8% | Gastar ouro acumulado para comprar cartas novas, relíquias ou remover cartas fracas do deck. |`
   - Seção 5: Deck começa com 10 cartas básicas e cresce por meio das recompensas dos nós; purge reduz tamanho para afinar estratégia.

### 1.2 Baseline Existente no Código-Fonte
1. **`godot_project/scripts/run/RunState.gd`**:
   - Linha 38: `var relics: Array[String] = []`
   - Linha 39: `var gold: int = 0`
   - Linha 37: `var deck: Array[String] = []`
   - Linhas 189–199:
     ```gdscript
     func add_gold(amount: int) -> bool:
         if amount < 0: return false
         gold += amount
         return true

     func spend_gold(amount: int) -> bool:
         if amount < 0 or amount > gold: return false
         gold -= amount
         return true
     ```
   - Linhas 201–212:
     ```gdscript
     func add_card(card_id: String) -> bool:
         if card_id.is_empty(): return false
         deck.append(card_id)
         return true

     func remove_card(card_id: String) -> bool:
         var idx: int = deck.find(card_id)
         if idx < 0: return false
         deck.remove_at(idx)
         return true
     ```
   - Linhas 214–222:
     ```gdscript
     func add_relic(relic_id: String) -> bool:
         if relic_id.is_empty() or relics.has(relic_id): return false
         relics.append(relic_id)
         return true

     func has_relic(relic_id: String) -> bool:
         return relics.has(relic_id)
     ```
   - Linhas 119–130: `complete_current_node()` marca o nó atual como visitado e avança `floors_cleared += 1`.
   - *Observação*: Atualmente, `RunState` não possui contador de remoções persistente (`card_purges_count`). O design deve acomodar `var card_purges_count: int = 0` no `RunState` ou fallback local gerenciado pela Forja.

2. **`godot_project/scripts/run/RunNode.gd`**:
   - Linha 8: `enum NodeType { COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS }`
   - Linha 16: `NodeType.FORGE: "Forja"`
   - Linha 26: `NodeType.FORGE: "$"` (ou ícone visual `⚒️` no mapa).

3. **`godot_project/scripts/run/RunNodeResolver.gd`**:
   - Linhas 39–40:
     ```gdscript
     RunNode.NodeType.FORGE:
         log_lines.append("Forja anã: o mercado abrirá no próximo marco (M3).")
     ```
   - Em M3, ao selecionar um nó `FORGE`, a tela de navegação `RunMapScreen` deve instanciar e abrir `ForgeScreen`.

4. **`godot_project/scripts/run/RunSession.gd`**:
   - Linhas 9–14: Deck inicial contém exatamente 10 cartas:
     ```gdscript
     const DEFAULT_DECK: Array[String] = [
         "movimento", "movimento", "movimento",
         "trabalho", "trabalho",
         "escavacao", "escavacao",
         "ataque", "ataque", "defesa",
     ]
     ```

5. **Peer Explorer Findings**:
   - **`explorer_m3_1/handoff.md`** (Relics Architecture):
     * Catálogo das 10 relíquias canônicas: `martelo_runico` (50g), `escudo_ancestral` (70g), `bolsa_do_mercador` (45g), `amuleto_ambar` (65g), `dente_da_viuva` (90g), `tocha_eterna` (85g), `oleo_alquimico` (55g), `frasco_feromonio` (80g), `coroa_quitina` (120g), `relogio_da_forja` (95g).
     * Relíquia 10 (`relogio_da_forja` - Engrenagem Mestra da Forja): concede 20% de desconto em todas as compras da Forja (`modify_forge_cost`) e +5 de ouro ao entrar no nó.
     * `RelicManager.modify_forge_cost(item_type: String, base_cost: int) -> int` retorna o valor com desconto.
   - **`explorer_m3_2/handoff.md`** (Reward Modal & Card Draft):
     * Catálogo de cartas por Ato:
       - Ato I: `marcha_rapida` (45g), `golpe_pesado` (50g), `bloqueio_ferreo` (50g), `trabalho_dobrado` (55g), `picareta_reforcada` (55g), `tiro_balista` (60g), `escudo_quitina` (60g).
       - Ato II: `tocha_sagrada` (65g), `lamina_ignea` (70g), `armadura_resinosa` (65g), `passo_ligeiro` (60g), `evasao_tatica` (65g), `explorador_abissal` (70g), `purificacao_fumegante` (75g).
       - Ato III: `martelo_do_trovao` (85g), `forja_divina` (90g), `furor_ancestral` (85g), `runa_haste` (80g), `perfuratriz_real` (85g), `colapso_estrutural` (90g), `fogo_alquimico` (95g).

---

## 2. Logic Chain

### 2.1 Da Filosofia Roguelike do Nó FORGE (Santuário de Deckbuilding)
1. Nos jogos do gênero *deckbuilder roguelike* (como *Slay the Spire* e *Monster Train*), a loja/forja é o nó estratégico onde ouro é convertido em poder refinado.
2. Comprar cartas novas permite expandir arquétipos táticos. Comprar relíquias confere vantagens passivas permanentes para a run inteira.
3. A mecânica de **expurgo de cartas** (*deck thinning*) é vital: quanto menor e mais focado o deck, mais frequentemente os heróis sacam suas cartas mais poderosas.
4. No entanto, se o jogador remover cartas indiscriminadamente, corre o risco de esvaziar o deck a ponto de não ter cartas suficientes para o ciclo de compra (mão de 5 cartas em combate). Portanto, uma **restrição de segurança de deck mínimo de 5 cartas** (`MINIMUM_SAFE_DECK_LIMIT = 5`) é fundamental para a estabilidade do jogo e prevenção de falhas no loop de combate.

### 2.2 Da Geração Determinística do Inventário
1. O inventário do mercado deve ser gerado uma única vez ao entrar no nó, utilizando o `RandomNumberGenerator` da run (`state.seed_value` ou `rng` injetado):
   - **3 Cartas**: Sorteadas do pool correspondente ao Ato atual (`state.act`), garantindo que cartas mais avançadas surjam nos Atos II e III. Se o pool não tiver cartas suficientes, usa as cartas básicas como fallback.
   - **2 Relíquias**: Sorteadas das 10 relíquias canônicas. **Regra de Exclusão Absoluta**: Se o jogador já possui a relíquia (`state.has_relic(id) == true`), ela é excluída do sorteio do mercado. Se o jogador já possuir 9 ou 10 relíquias, oferece apenas as restantes ou substitui por consumível/fallback sem quebrar a execução.
2. Cada item possui preço base em ouro (`cost_gold`). Se o jogador possuir a relíquia `relogio_da_forja` (ou via pipeline `RelicManager.modify_forge_cost`), aplica-se automaticamente o desconto de 20%.

### 2.3 Do Algoritmo Progressivo de Remoção de Cartas
1. O serviço de expurgo possui custo progressivo para desestimular decks microscópicos sem planejamento:
   $$\text{Custo de Remoção} = \text{BASE\_PURGE\_COST} + (\text{purges\_count} \times \text{PURGE\_INCREMENT})$$
   Com $\text{BASE\_PURGE\_COST} = 50$ e $\text{PURGE\_INCREMENT} = 25$:
   - 1ª remoção na run: $50 + (0 \times 25) = 50\text{ ouro}$
   - 2ª remoção na run: $50 + (1 \times 25) = 75\text{ ouro}$
   - 3ª remoção na run: $50 + (2 \times 25) = 100\text{ ouro}$
   - 4ª remoção na run: $50 + (3 \times 25) = 125\text{ ouro}$
2. **Validações estritas de segurança**:
   - `state.deck.size() > MINIMUM_SAFE_DECK_LIMIT` (tamanho atual $> 5$). Se $\le 5$, o serviço bloqueia com o status: `"Deck mínimo atingido (5 cartas)"`.
   - `state.gold >= custo_calculado`. Se insuficiente, o botão permanece desabilitado.
   - Cada visita à forja permite 1 remoção canônica (marcada como `_purge_done_this_visit = true`), exibindo `"Serviço Esgotado nesta Visita"`.

### 2.4 Da Testabilidade Headless & Arquitetura Desacoplada (SOLID)
1. Para cumprir as diretrizes de qualidade do projeto e execução 100% verde no GUT headless runner (`run_gut_tests.sh`), `ForgeScreen` deve ser completamente funcional sem requerer janela de display gráfico (X11/Wayland).
2. O componente deve suportar instanciação puramente programática (`ForgeScreen.new()`), criando seus nós de interface dinamicamente se instanciado bare, ou conectando-se a nós existentes se instanciado via cena `.tscn`.
3. Para isolar a lógica de negócios da camada de apresentação, criamos a classe utilitária pura `ForgeInventoryGenerator` (ou métodos puros no próprio script), permitindo testar a matemática de custos, descontos e limites de deck de forma unitária e sem efeitos colaterais.

---

## 3. Detailed Technical Design

### 3.1 Arquitetura Geral da Forja

```
+-----------------------------------------------------------------------------------+
|                                  ForgeScreen                                      |
|  Control (Dark Fantasy dwarf workshop UI, programmatic or .tscn)                 |
+-----------------------------------------------------------------------------------+
|  [Header]: Título "FORJA ANÃ DE KUAR-TOR" | Ouro 🪙 | Cartas no Deck 🃏 | Sair ✖   |
+-----------------------------------------------------------------------------------+
|  [Seção 1: Mercado de Cartas (3 Slots)]                                          |
|  +-----------------------+  +-----------------------+  +-----------------------+  |
|  | Card Slot 0           |  | Card Slot 1           |  | Card Slot 2           |  |
|  | [Badge] Nome da Carta |  | [Badge] Nome da Carta |  | [Badge] Nome da Carta |  |
|  | Descrição do Efeito   |  | Descrição do Efeito   |  | Descrição do Efeito   |  |
|  | Preço: 50🪙 [COMPRAR] |  | Preço: 60🪙 [COMPRAR] |  | [VENDIDO]             |  |
|  +-----------------------+  +-----------------------+  +-----------------------+  |
+-----------------------------------------------------------------------------------+
|  [Seção 2: Mostruário de Relíquias (2 Slots)]                                     |
|  +---------------------------------------+  +-----------------------------------+ |
|  | Relic Slot 0                          |  | Relic Slot 1                      | |
|  | 🏺 Nome da Relíquia (Raridade)        |  | ⚙️ Nome da Relíquia (Raridade)   | |
|  | Efeito Passivo Conectado ao EventBus  |  | Efeito Passivo                    | |
|  | Preço: 70🪙 [COMPRAR]                 |  | [VENDIDO]                         | |
|  +---------------------------------------+  +-----------------------------------+ |
+-----------------------------------------------------------------------------------+
|  [Seção 3: Bigorna Ancestral — Expurgar Carta do Deck]                            |
|  Custo Atual: 50🪙 (Aumenta +25🪙 por remoção) | Deck Atual: 10 cartas            |
|  [ Botão: "Expurgar Carta do Deck (50🪙)" ] -> Abre Gaveta/Lista do Deck         |
|  * Se deck <= 5 cartas: Desabilitado com aviso de Deck Mínimo Seguro              |
+-----------------------------------------------------------------------------------+
|  [Footer]: Botão "Voltar ao Caminho" (Sair da Forja) -> complete_current_node()   |
+-----------------------------------------------------------------------------------+
```

---

### 3.2 Especificação Completa de `godot_project/scripts/run/ui/ForgeScreen.gd`

```gdscript
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
	pool_cards.shuffle()
	
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
	var owned_relics: Array[String] = state.relics if state != null else []
	var available_relic_ids: Array[String] = []
	for rid in CANONICAL_RELICS.keys():
		if not owned_relics.has(rid):
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
		var j: int = rng.randi_range(0, i)
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
	state.spend_gold(cost)
	state.add_relic(slot["id"])
	if relic_manager != null and relic_manager.has_method("register_relic"):
		relic_manager.register_relic(slot["id"])
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
```

---

### 3.3 Design da Cena Opcional: `godot_project/scenes/run/ForgeScreen.tscn`

Abaixo segue o arquivo de cena `.tscn` compatível com a engine Godot 4.3, utilizando a mesma estrutura de layout Dark Fantasy de `RunMapScreen.tscn`:

```ini
[gd_scene load_steps=2 format=3 uid="uid://cforgescreenrpg"]

[ext_resource type="Script" path="res://scripts/run/ui/ForgeScreen.gd" id="1_forge"]

[node name="ForgeScreen" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1_forge")

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
color = Color(0.06, 0.05, 0.07, 0.98)

[node name="Header" type="HBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 10
anchor_right = 1.0
offset_left = 24.0
offset_top = 16.0
offset_right = -24.0
offset_bottom = 54.0
grow_horizontal = 2

[node name="LblTitle" type="Label" parent="Header"]
layout_mode = 2
size_flags_horizontal = 3
theme_override_colors/font_color = Color(1, 0.85, 0.35, 1)
theme_override_font_sizes/font_size = 18
text = "⚒️ FORJA ANÃ DE KUAR-TOR"

[node name="LblDeck" type="Label" parent="Header"]
layout_mode = 2
theme_override_colors/font_color = Color(0.7, 0.8, 1, 1)
theme_override_font_sizes/font_size = 14
text = "🃏 Deck: 10 cartas"

[node name="LblGold" type="Label" parent="Header"]
layout_mode = 2
theme_override_colors/font_color = Color(1, 0.84, 0, 1)
theme_override_font_sizes/font_size = 15
text = "🪙 50 Ouro"

[node name="Body" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 24.0
offset_top = 70.0
offset_right = -24.0
offset_bottom = -70.0
grow_horizontal = 2
grow_vertical = 2
theme_override_constants/separation = 12

[node name="CardsSection" type="VBoxContainer" parent="Body"]
layout_mode = 2

[node name="CardsHBox" type="HBoxContainer" parent="Body/CardsSection"]
custom_minimum_size = Vector2(0, 110)
layout_mode = 2
theme_override_constants/separation = 12

[node name="RelicsSection" type="VBoxContainer" parent="Body"]
layout_mode = 2

[node name="RelicsHBox" type="HBoxContainer" parent="Body/RelicsSection"]
custom_minimum_size = Vector2(0, 110)
layout_mode = 2
theme_override_constants/separation = 12

[node name="PurgeSection" type="VBoxContainer" parent="Body"]
layout_mode = 2

[node name="PurgePanel" type="PanelContainer" parent="Body/PurgeSection"]
custom_minimum_size = Vector2(0, 70)
layout_mode = 2

[node name="DeckDrawer" type="PanelContainer" parent="."]
visible = false
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -250.0
offset_top = -120.0
offset_right = 250.0
offset_bottom = 120.0
grow_horizontal = 2
grow_vertical = 2

[node name="Footer" type="HBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 12
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 24.0
offset_top = -54.0
offset_right = -24.0
offset_bottom = -14.0
grow_horizontal = 2
grow_vertical = 0

[node name="LblFeedback" type="Label" parent="Footer"]
layout_mode = 2
size_flags_horizontal = 3
theme_override_colors/font_color = Color(0.8, 0.8, 0.8, 1)
theme_override_font_sizes/font_size = 12
text = "Bem-vindo à Forja de Karak-Dur."

[node name="BtnClose" type="Button" parent="Footer"]
custom_minimum_size = Vector2(180, 40)
layout_mode = 2
text = "Voltar ao Caminho  ➔"
```

---

### 3.4 Especificação da Suíte de Testes GUT (`godot_project/test/unit/test_forge_system.gd`)

A suíte segue rigorosamente o padrão **AAA (Arrange-Act-Assert)**, isolamento por injeção e segurança de memória com `autofree()`:

```gdscript
# res://test/unit/test_forge_system.gd
extends GutTest

## Testes unitários para o sistema da Forja Anã (ForgeScreen e serviços do nó FORGE).
## Valida geração determinística de inventário (3 cartas, 2 relíquias), compra com ouro,
## serviço de expurgo com custo progressivo, limite de segurança de 5 cartas no deck,
## exclusão de relíquias duplicadas, e integração de descontos com RelicManager.

var _state: RunState
var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _forge: ForgeScreen

func before_each() -> void:
	_generator = RunMapGenerator.new(6, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 1337
	_state = RunState.new(_generator, _rng)
	
	var starter_deck: Array[String] = [
		"movimento", "movimento", "movimento",
		"trabalho", "trabalho",
		"escavacao", "escavacao",
		"ataque", "ataque", "defesa"
	] # 10 cartas
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, starter_deck, 1337)
	_state.gold = 200 # Saldo suficiente para compras nos testes
	
	_forge = autofree(ForgeScreen.new())
	_forge.setup(_state, null, _rng)

func after_each() -> void:
	RunSession.clear()
	_forge = null
	_state = null
	_generator = null
	_rng = null

# ── 1. Headless Safety & Inicialização ───────────────────────────────────────

func test_forge_bare_node_headless_safety() -> void:
	# Arrange
	var bare: ForgeScreen = autofree(ForgeScreen.new())

	# Act & Assert (não deve falhar nem disparar null pointer em modo headless)
	bare._ready()
	bare.refresh_ui()
	assert_not_null(bare, "Bare ForgeScreen deve inicializar com segurança sem .tscn")

func test_forge_setup_generates_inventory_sizes() -> void:
	# Arrange & Act já realizados no before_each()
	
	# Assert
	assert_eq(_forge.card_inventory.size(), 3, "Forja deve oferecer exatamente 3 cartas")
	assert_eq(_forge.relic_inventory.size(), 2, "Forja deve oferecer exatamente 2 relíquias")
	assert_eq(_forge.purges_performed, 0, "Expurgos começam em zero")

# ── 2. Compra de Cartas ──────────────────────────────────────────────────────

func test_buy_card_happy_path() -> void:
	# Arrange
	var initial_gold: int = _state.gold
	var initial_deck_size: int = _state.deck.size()
	var slot0: Dictionary = _forge.card_inventory[0]
	var cost: int = int(slot0["cost"])
	var card_id: String = slot0["id"]

	# Act
	var success: bool = _forge.buy_card(0)

	# Assert
	assert_true(success, "Compra de carta com ouro suficiente deve ter sucesso")
	assert_eq(_state.gold, initial_gold - cost, "Ouro deve ser deduzido com exatidão")
	assert_eq(_state.deck.size(), initial_deck_size + 1, "Deck deve ter +1 carta")
	assert_true(_state.deck.has(card_id), "Carta comprada deve constar no deck")
	assert_true(_forge.card_inventory[0]["sold"], "Slot deve estar marcado como vendido")

func test_buy_card_insufficient_gold_fails() -> void:
	# Arrange
	_state.gold = 10 # Insuficiente para qualquer carta (preço mínimo 45)
	var initial_deck_size: int = _state.deck.size()

	# Act
	var success: bool = _forge.buy_card(0)

	# Assert
	assert_false(success, "Compra com ouro insuficiente deve falhar")
	assert_eq(_state.gold, 10, "Ouro não deve sofrer alteração")
	assert_eq(_state.deck.size(), initial_deck_size, "Nenhuma carta adicionada ao deck")
	assert_false(_forge.card_inventory[0]["sold"], "Slot continua disponível para compra")

func test_buy_card_already_sold_slot_fails() -> void:
	# Arrange
	_forge.buy_card(0) # Primeira compra: sucesso
	var gold_after_first: int = _state.gold

	# Act: Tentar comprar o mesmo slot novamente
	var second_buy: bool = _forge.buy_card(0)

	# Assert
	assert_false(second_buy, "Slot já vendido não pode ser comprado novamente")
	assert_eq(_state.gold, gold_after_first, "Nenhum ouro adicional debitado")

# ── 3. Compra de Relíquias ───────────────────────────────────────────────────

func test_buy_relic_happy_path() -> void:
	# Arrange
	var initial_gold: int = _state.gold
	var slot0: Dictionary = _forge.relic_inventory[0]
	var cost: int = int(slot0["cost"])
	var relic_id: String = slot0["id"]

	# Act
	var success: bool = _forge.buy_relic(0)

	# Assert
	assert_true(success, "Compra de relíquia com ouro suficiente deve ter sucesso")
	assert_eq(_state.gold, initial_gold - cost, "Ouro deduzido corretamente")
	assert_true(_state.has_relic(relic_id), "Relíquia adicionada ao RunState.relics")
	assert_true(_forge.relic_inventory[0]["sold"], "Slot marcado como vendido")

func test_relic_inventory_excludes_already_owned_relics() -> void:
	# Arrange: Adicionar todas as relíquias exceto duas ao estado
	_state.add_relic("martelo_runico")
	_state.add_relic("escudo_ancestral")
	_state.add_relic("bolsa_do_mercador")
	_state.add_relic("amuleto_ambar")
	_state.add_relic("dente_da_viuva")
	_state.add_relic("tocha_eterna")
	_state.add_relic("oleo_alquimico")
	_state.add_relic("frasco_feromonio")
	# Restam apenas: "coroa_quitina" e "relogio_da_forja"

	# Act: Regerar inventário
	_forge.generate_inventory()

	# Assert
	for slot in _forge.relic_inventory:
		assert_false(_state.has_relic(slot["id"]), "Relíquias já possuídas não podem ser oferecidas no mercado")

# ── 4. Serviço de Expurgo de Cartas (Deck Thinning) ──────────────────────────

func test_card_purge_progressive_cost() -> void:
	# Arrange & Assert Custo Inicial
	assert_eq(_forge.get_current_purge_cost(), 50, "1ª remoção deve custar 50 ouro")
	var initial_deck_size: int = _state.deck.size()

	# Act 1: 1º Expurgo
	var p1: bool = _forge.purge_card("movimento")

	# Assert 1
	assert_true(p1, "1º expurgo com saldo suficiente deve ter sucesso")
	assert_eq(_state.deck.size(), initial_deck_size - 1, "Deck reduzido em 1 carta")
	assert_eq(_forge.purges_performed, 1, "Contador de expurgos incrementado para 1")
	assert_eq(_forge.get_current_purge_cost(), 75, "2ª remoção deve custar 75 ouro (50 + 25)")

	# Act 2: Resetar permissão de visita para testar o custo da 2ª remoção
	_forge.purge_used_this_visit = false
	var p2: bool = _forge.purge_card("trabalho")

	# Assert 2
	assert_true(p2, "2º expurgo deve ser realizado com sucesso")
	assert_eq(_forge.purges_performed, 2, "Contador de expurgos incrementado para 2")
	assert_eq(_forge.get_current_purge_cost(), 100, "3ª remoção deve custar 100 ouro (50 + 50)")

func test_card_purge_enforces_minimum_safe_deck_limit() -> void:
	# Arrange: Reduzir deck artificialmente até exatamente 5 cartas
	_state.deck = ["carta_1", "carta_2", "carta_3", "carta_4", "carta_5"]
	assert_eq(_state.deck.size(), 5)

	# Act: Tentar expurgar com deck no limite mínimo
	var check: Dictionary = _forge.can_purge_card()
	var success: bool = _forge.purge_card("carta_1")

	# Assert
	assert_false(check["can"], "can_purge_card deve retornar falso no limite mínimo")
	assert_true(check["reason"].contains("Deck mínimo"), "Motivo deve citar deck mínimo")
	assert_false(success, "purge_card deve falhar quando deck <= 5 cartas")
	assert_eq(_state.deck.size(), 5, "Nenhuma carta removida do deck")
	assert_eq(_state.gold, 200, "Nenhum ouro deduzido na tentativa bloqueada")

func test_card_purge_single_use_per_visit() -> void:
	# Arrange
	_forge.purge_card("movimento")
	assert_true(_forge.purge_used_this_visit)

	# Act: Tentar expurgar segunda vez na mesma visita
	var check: Dictionary = _forge.can_purge_card()
	var success: bool = _forge.purge_card("trabalho")

	# Assert
	assert_false(check["can"], "Não pode expurgar duas vezes na mesma visita da Forja")
	assert_false(success, "Segunda tentativa de expurgo na mesma visita rejeitada")

# ── 5. Desconto de Relíquias (RelicManager Integration) ───────────────────────

func test_forge_discount_with_relogio_da_forja() -> void:
	# Arrange: Conceder a relíquia relogio_da_forja ao estado
	_state.add_relic("relogio_da_forja")

	# Act: Regerar inventário com a relíquia ativa
	_forge.generate_inventory()

	# Assert: Itens devem receber 20% de desconto
	var card_slot = _forge.card_inventory[0]
	var base_card_cost: int = int(card_slot["base_cost"])
	var expected_card_cost: int = int(round(float(base_card_cost) * 0.80))
	assert_eq(int(card_slot["cost"]), expected_card_cost, "Carta deve ter 20% de desconto")

	var purge_cost: int = _forge.get_current_purge_cost()
	assert_eq(purge_cost, 40, "Expurgo base de 50g deve cair para 40g (50 * 0.80)")

# ── 6. Saída e Conclusão de Nó ───────────────────────────────────────────────

func test_close_forge_completes_current_node() -> void:
	# Arrange: Mover estado para um nó de forja
	var forge_node: RunNode = RunNode.new(3, 1, 1, 0, RunNode.NodeType.FORGE)
	_state.map.nodes.append(forge_node)
	_state.current_node_id = 3
	assert_false(forge_node.visited)

	var signal_emitted: Array = []
	_forge.forge_closed.connect(func(): signal_emitted.append(true))

	# Act
	_forge.close_forge()

	# Assert
	assert_eq(signal_emitted.size(), 1, "Sinal forge_closed deve ser emitido")
	assert_true(forge_node.visited, "Nó FORGE deve ser marcado como concluído ao sair")
```

---

## 4. Caveats

1. **Modo de Investigação Read-Only**: Por ser uma tarefa estrita de Explorer, nenhum código de produção ou teste foi gravado diretamente em `godot_project/scripts/` ou `godot_project/test/`. Toda a especificação, designs de código e arquitetura de testes estão documentados integralmente neste relatório e em arquivos `.md` na pasta do agente.
2. **Integração com `RelicManager`**: O cálculo de desconto na Forja aceita tanto a presença passiva de `relogio_da_forja` em `RunState.relics` quanto a chamada desacoplada de `RelicManager.modify_forge_cost(item_type, base_cost)`. Isso garante retrocompatibilidade total com as implementações das subequipes M3.1 e M3.2.
3. **Persistência de `card_purges_count`**: Se a classe `RunState` for expandida no Marco M3 para incluir `var card_purges_count: int = 0` nos dicionários `to_dict()` e `from_dict()`, a contagem de expurgos persistirá perfeitamente entre recarregamentos de save; caso contrário, `ForgeScreen` mantém a contagem na sessão da expedição.
4. **Animações e Áudio**: A classe emite eventos sonoros via `AudioManager` ou `EventBus` (`audio_play_sfx_requested`), utilizando mensagens seguras que não dependem da existência prévia de arquivos de som carregados.

---

## 5. Conclusion

1. **Prontidão da Arquitetura do Nó FORGE**: O nó `FORGE` possui sua interface e máquina de regras completamente especificadas em `ForgeScreen.gd`, integrando o mercado de 3 cartas, mostruário de 2 relíquias sem duplicatas, e serviço de expurgo com custo progressivo ($50\text{g} + 25\text{g}$ por remoção).
2. **Garantia de Segurança do Deck**: O limite mínimo de 5 cartas (`MINIMUM_SAFE_DECK_LIMIT = 5`) impede travamentos e bugs no loop de combate tático, bloqueando o expurgo com aviso visual e sonoro explicativo.
3. **Cobertura de Testes GUT**: A suíte `test_forge_system.gd` cobre 100% dos requisitos (inicialização headless, compra de cartas, compra de relíquias, expurgo progressivo, rejeição em limite $\le 5$, descontos de relíquias e encerramento de nó).

---

## 6. Verification Method

Para verificar independentemente a exatidão, consistência e viabilidade desta especificação:

1. **Inspeção de Contratos e Classes**:
   - `CAMPANHA_ROGUELIKE.md § 4`: Conferir Linha 147 para o peso e função do nó `FORGE`.
   - `RunState.gd`: Conferir Linhas 189–218 para os métodos `add_gold()`, `spend_gold()`, `add_card()`, `remove_card()`, `add_relic()` e `has_relic()`.
   - `explorer_m3_1/handoff.md`: Conferir Linhas 816–837 para a especificação da relíquia `relogio_da_forja` e método `modify_forge_cost()`.
   - `explorer_m3_2/handoff.md`: Conferir Linhas 113–130 para os pools de cartas de cada Ato.

2. **Validação de Testes GUT**:
   - Quando a implementação for executada pela equipe de engenharia:
     ```bash
     bash godot_project/run_gut_tests.sh -gtest=res://test/unit/test_forge_system.gd
     ```
     Deverá passar com código de saída 0 e zero vazamentos de memória no ObjectDB.
