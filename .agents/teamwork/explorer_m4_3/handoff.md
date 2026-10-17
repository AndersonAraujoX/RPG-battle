# Relatório de Handoff — Marco M4: Persistência de PV, Permadeath & Design dos Testes GUT

**Agente**: `explorer_m4_3` (Explorer de Persistência de PV, Permadeath & Design de Testes GUT)  
**Destinatário**: `orchestrator_1` (ou subagentes de implementação M4)  
**Data**: 2026-10-16  
**Status**: Concluído (Hard Handoff)

---

## 1. Observação

### 1.1. Arquitetura Atual do `RunState.gd`
- **Arquivo**: `godot_project/scripts/run/RunState.gd`
- **Linhas 30–46**:
  ```gdscript
  var status: int = Status.NOT_STARTED
  var heroes: Array[String] = []
  var hero_hp: Dictionary = {}
  var hero_max_hp: Dictionary = {}
  var fallen_heroes: Array[String] = []
  var deck: Array[String] = []
  var relics: Array[String] = []
  var gold: int = 0
  var current_node_id: int = -1
  var floors_cleared: int = 0
  var bosses_defeated: int = 0
  var enemies_killed: int = 0
  ```
- **Linhas 146–187**:
  - `get_living_heroes()`: filtra `heroes` excluindo os IDs presentes em `fallen_heroes`.
  - `damage_hero(hero_id, amount)`: reduz o PV; se atinge 0, anexa a `fallen_heroes` e emite `hero_died(hero_id)`. Se `get_living_heroes().is_empty()`, define `status = Status.DEFEAT` e emite `run_ended(false)`.
  - `heal_hero(hero_id, amount)`: rejeita curas em heróis caídos (`if not is_hero_alive(hero_id): return int(hero_hp[hero_id])`). A morte permanente já está modelada nesta camada.
  - `heal_party_percent(pct)`: aplica cura proporcional estritamente em `get_living_heroes()`.
- **Linhas 120–143**:
  - `complete_current_node()`: marca `node.visited = true`, incrementa `floors_cleared`. Se for chefe (`node.is_boss()`), chama `_on_boss_defeated()`, que avança o Ato (`act += 1`), cura 25% dos heróis vivos (`heal_party_percent(0.25)`), gera o mapa do novo Ato e emite `act_advanced(act)`; no Ato 3, define `status = Status.VICTORY` e emite `run_ended(true)`.
- **Linhas 247–252**:
  - `calculate_amber()`: calcula Âmbar Real como `floors_cleared * 1 + bosses_defeated * 10 + (25 if VICTORY else 0)`.

### 1.2. Arquitetura Atual do `CercoGameController.gd`
- **Arquivo**: `godot_project/scripts/main/CercoGameController.gd`
- **Linhas 40–60**:
  - `_initialize_models()`: hardcode dos heróis `"aquele"`, `"stark"` e `"lysander"` com valores fixos de PV (48, 52, 36) e posicionamento estático `(9, 10)`, `(10, 9)`, `(10, 11)`. Não checa se existe run ativa.
- **Linhas 801–830**:
  - Dano sofrido por heróis em combate reduz o PV no `board` via `board.damage_unit(target_hero_id, dmg)`.
  - Verifica `check_game_over_conditions()` a cada golpe e a cada final de turno.
- **Linhas 906–953**:
  - `check_game_over_conditions()`:
    1. Derrota se todos os heróis do time A estiverem mortos (`living_heroes.is_empty()`).
    2. Derrota se 3 ou mais invasores entrarem na Câmara Central (`central_invaders >= 3`).
    3. Vitória se sobreviver a `max_rounds` e eliminar todos os invasores ativos.
- **Linhas 956–1009**:
  - `trigger_game_over(victory, reason)`: exibe `GameOverModal`. O botão reiniciar recarrega a cena atual; o botão menu volta ao Menu Principal. Não existe integração com `RunState`, `RewardModal` ou mapa roguelike.

### 1.3. Padrão Existente de Sessão e Resolução de Nós
- **Arquivo**: `godot_project/scripts/run/RunSession.gd` (Linhas 16–29):
  - `RunSession.current`: referência estática à instância ativa de `RunState`.
  - `RunSession.has_active_run() -> bool`: indica se há expedição em andamento.
- **Arquivo**: `godot_project/scripts/run/RunNodeResolver.gd` (Linhas 5–8, 53–72):
  - Documentado explicitamente: *"No marco M4, uma subclasse/estratégia que abre o combate tático real substituirá resolve_combat() — por isso o resolver é injetado no RunMapScreen."*
- **Arquivo**: `godot_project/scripts/run/ui/RewardModal.gd` (Linhas 110–138, 262–337):
  - Modal M3 pós-combate completo: recebe `setup(state, node, rng)`, concede ouro do nó, relíquia (se Elite/Boss), oferece 3 cartas de draft (com botão de pular) e emite `reward_completed(summary)`.

---

## 2. Logic Chain (Cadeia de Raciocínio & Design da Solução)

### 2.1. Persistência Bidirecional de PV (Roundtrip HP Persistence)

```
[RunMapScreen: Node Selecionado]
       │
       ▼
[RunCombatBridge.setup_combat(state, node)]
       │ - Extrai apenas living_heroes
       │ - Mapeia hero_hp e hero_max_hp
       │ - Passa deck e relíquias da run
       │ - Gera esquadrão via CombatEncounterGenerator
       ▼
[Carregamento de Main.tscn / CercoGameController]
       │ - Verifica RunSession.has_active_run()
       │ - Spawna heróis sobreviventes com PV persistido
       │ - Heróis caídos NÃO são colocados no tabuleiro
       ▼
[Combate Tático 20x20]
       │ - Dano e cura ocorrem no FortressBoard
       │ - Heróis que chegam a 0 PV são marcados como caídos
       ▼
[Fim do Combate (Vitória ou Derrota)]
       │ - CercoGameController monta Dictionary de resultado
       │ - RunCombatBridge.sync_combat_result(state, result)
       │ - hero_hp atualizado e clampeado em [0, max_hp]
       ▼
[Persistência Confirmada no RunState]
```

1. **Setup Inicial da Batalha**:
   - `CercoGameController._initialize_models()` verifica `RunSession.has_active_run()`.
   - Se `false`: opera em **Modo Cerco Clássico Standalone** (3 heróis padrão, sem alterações de compatibilidade).
   - Se `true`:
     * Obtém `state = RunSession.current`.
     * Itera sobre `state.heroes`. Se `not state.is_hero_alive(h)`: **ignora o herói** (não chama `board.place_unit` nem `board.register_unit`).
     * Para cada herói vivo, recupera `cur_hp = state.hero_hp[h]` e `max_hp = state.hero_max_hp[h]`.
     * Registra no `board` com `hp = cur_hp` e `max_hp = max_hp`.
     * Deck: substitui o baralho inicial estático pelas cartas de `state.deck`.
     * Relíquias: invoca `RelicManager.sync_from_run_state(state)`.

2. **Sincronização no Término do Combate**:
   - `CercoGameController` empacota o dicionário de resultado:
     ```gdscript
     var result: Dictionary = {
         "victory": victory,
         "surviving_heroes_hp": {
             # "aquele": 14, "stark": 28, ...
         },
         "fallen_heroes": [
             # heróis cujo PV caiu para <= 0 durante esta batalha
         ],
         "enemies_killed": enemies_defeated_count,
         "rounds_survived": current_round,
         "gold_earned": 0 # ouro de saques em baús do mapa
     }
     ```
   - `RunCombatBridge.sync_combat_result(state, result)`:
     * Para cada herói em `state.heroes`:
       - Se estiver em `result.surviving_heroes_hp`:
         ```gdscript
         var raw_hp: int = int(result["surviving_heroes_hp"][h])
         var max_h: int = int(state.hero_max_hp.get(h, raw_hp))
         state.hero_hp[h] = clampi(raw_hp, 0, max_h)
         if state.hero_hp[h] == 0 and not state.fallen_heroes.has(h):
             state.fallen_heroes.append(h)
             state.hero_died.emit(h)
         ```
       - Se estiver em `result.fallen_heroes` ou PV <= 0:
         ```gdscript
         state.hero_hp[h] = 0
         if not state.fallen_heroes.has(h):
             state.fallen_heroes.append(h)
             state.hero_died.emit(h)
         ```
     * Registra abates: `state.register_kills(result.get("enemies_killed", 0))`.
     * Se houver ouro de baús: `state.add_gold(result.get("gold_earned", 0))`.

### 2.2. Regras de Morte Permanente (Permadeath Tracking)

1. **Condição de Morte**:
   - Um herói tomba quando seu PV no tabuleiro atinge `0` (seja por ataque direto ou falha em salvaguardas de morte).
   - O herói é imediatamente adicionado a `state.fallen_heroes` e seu PV em `state.hero_hp` fica travado em `0`.

2. **Invariantes de Permadeath**:
   - **Exclusão de Spawns Futuros**: Nos nós de combate seguintes, `RunCombatBridge.setup_combat` apenas seleciona `state.get_living_heroes()`. Heróis em `fallen_heroes` não entram no grid.
   - **Imunidade a Curas**: `RunState.heal_hero` checa `is_hero_alive(hero_id)`. Se morto, retorna 0 sem alterar o PV.
   - **Fogueiras (`CAMPFIRE`)**: `heal_party_percent(0.30)` itera estritamente sobre `get_living_heroes()`. Heróis mortos permanecem mortos.
   - **Transições de Ato**: Ao derrotar o chefe do Ato, a cura de 25% recupera apenas os heróis sobreviventes.
   - **Visual no Mapa**: `RunMapScreen._update_hero_bars()` renderiza o herói caído com fundo vermelho escuro, caveira `💀` e 0 PV.

### 2.3. Roteamento de Vitória & Derrota (Win/Loss Routing)

#### Caso A: Vitória em Batalha Regular (`COMBAT`, `ELITE`, `SIEGE`)
1. Inimigos eliminados ou rodadas concluídas com sucesso.
2. `RunCombatBridge.sync_combat_result(state, result)` persiste o PV restante e eventuais mortes parciais.
3. Invoca `state.complete_current_node()`, marcando o nó como `visited = true` e incrementando `floors_cleared`.
4. Instancia e apresenta o modal M3 `RewardModal`:
   - Oferta 3 cartas do pool do Ato atual.
   - Concede ouro baseado no tipo de nó (15 para Combat, 20 para Siege, 30 para Elite).
   - Se for nó `ELITE`, concede 1 Relíquia garantida.
5. Ao concluir o modal (`reward_completed`):
   - Transiciona a cena de volta para `res://scenes/run/RunMapScreen.tscn`.
   - O mapa é atualizado: o nó atual exibe status visitado e os nós do próximo andar tornam-se interativos.

#### Caso B: Vitória contra Chefe de Ato (`BOSS`)
1. Chefe derrotado (`viuva_canibal` no Ato 1, `rainha_do_enxame` no Ato 2, `rei_isectum` no Ato 3).
2. `RunCombatBridge.sync_combat_result(state, result)` sincroniza o grupo.
3. `state.complete_current_node()` dispara `_on_boss_defeated()`:
   - **Se Ato 1 ou 2**: Incrementa `bosses_defeated`, cura 25% dos heróis sobreviventes, gera o novo mapa do Ato seguinte e reseta `current_node_id = -1`.
   - Exibe `RewardModal` com ouro de Boss (50) e Relíquia de Boss.
   - Ao fechar o modal, retorna ao `RunMapScreen`, que agora exibe o cabeçalho do novo Ato (ex: *"ATO II: OS TÚNEIS VIVOS"*).
   - **Se Ato 3 (Rei Isectum)**: Define `state.status = Status.VICTORY`, emite `run_ended(true)`. Exibe tela de vitória triunfal com pontuação máxima de Âmbar Real (bônus de +25).

#### Caso C: Derrota em Batalha (Party Wipe ou Invasão da Câmara)
1. Condição: Todos os heróis aliados morreram (`living_heroes.is_empty()`) OU 3 invasores tomaram a Câmara Central.
2. `RunCombatBridge.sync_combat_result(state, result)`:
   - Define `state.status = Status.DEFEAT`.
   - Emite `state.run_ended(false)`.
3. Cálculo de Âmbar Real: `amber = state.calculate_amber()` (`floors_cleared * 1 + bosses_defeated * 10`).
4. Apresenta a tela/modal de Fim de Expedição (`GameOverModal` ou transição para `GameOver.tscn`):
   - Exibe estatísticas da campanha: Andares vencidos, Chefes batidos, Insetos eliminados, Âmbar acumulado e Lista de Heróis tombados.
   - Opções: "Novo Jogo" (reiniciar run) ou "Menu Principal".
   - Limpa a sessão estática com `RunSession.clear()`.

---

## 3. Especificação do `RunCombatBridge.gd`

```gdscript
# res://scripts/run/combat/RunCombatBridge.gd
class_name RunCombatBridge
extends RefCounted

## Ponte estática e pura para orquestração entre RunState e o combate tático.
## Desacoplada de nós gráficos para garantir 100% de testabilidade em GUT headless.

static func setup_combat(run_state: RunState, node: RunNode, rng: RandomNumberGenerator = null) -> Dictionary:
	if run_state == null or node == null or not run_state.is_active():
		return {
			"ok": false,
			"living_heroes": [],
			"hero_hp": {},
			"hero_max_hp": {},
			"deck": [],
			"relics": [],
			"encounter": {}
		}

	var living: Array[String] = run_state.get_living_heroes()
	var h_hp: Dictionary = {}
	var h_max: Dictionary = {}
	for h in living:
		h_hp[h] = int(run_state.hero_hp.get(h, 1))
		h_max[h] = int(run_state.hero_max_hp.get(h, 1))

	var gen: CombatEncounterGenerator = CombatEncounterGenerator.new()
	var enc: Dictionary = gen.generate_encounter(run_state.act, node.floor_index, node.type, rng)

	return {
		"ok": true,
		"act": run_state.act,
		"node_id": node.id,
		"node_type": node.type,
		"living_heroes": living,
		"hero_hp": h_hp,
		"hero_max_hp": h_max,
		"deck": run_state.deck.duplicate(),
		"relics": run_state.relics.duplicate(),
		"encounter": enc
	}

static func sync_combat_result(run_state: RunState, result: Dictionary) -> Dictionary:
	var summary: Dictionary = {
		"victory": false,
		"game_over": false,
		"party_wipe": false,
		"status": RunState.Status.NOT_STARTED,
		"living_heroes_count": 0,
		"amber_earned": 0,
		"newly_fallen": []
	}

	if run_state == null or not run_state.is_active():
		return summary

	var victory: bool = bool(result.get("victory", false))
	var surviving_hp: Dictionary = result.get("surviving_heroes_hp", {})
	var reported_fallen: Array = result.get("fallen_heroes", [])

	# 1. Atualizar PV e detectar novos heróis caídos
	for h in run_state.heroes:
		if run_state.fallen_heroes.has(h):
			run_state.hero_hp[h] = 0
			continue

		if surviving_hp.has(h):
			var max_h: int = int(run_state.hero_max_hp.get(h, 1))
			var cur_h: int = clampi(int(surviving_hp[h]), 0, max_h)
			run_state.hero_hp[h] = cur_h
			if cur_h == 0:
				run_state.fallen_heroes.append(h)
				run_state.hero_died.emit(h)
				summary["newly_fallen"].append(h)
		elif reported_fallen.has(h):
			run_state.hero_hp[h] = 0
			run_state.fallen_heroes.append(h)
			run_state.hero_died.emit(h)
			summary["newly_fallen"].append(h)

	# 2. Registrar abates e ouro de baús
	var kills: int = int(result.get("enemies_killed", 0))
	if kills > 0:
		run_state.register_kills(kills)

	var bonus_gold: int = int(result.get("gold_earned", 0))
	if bonus_gold > 0:
		run_state.add_gold(bonus_gold)

	var living_count: int = run_state.get_living_heroes().size()
	summary["living_heroes_count"] = living_count

	# 3. Avaliar derrota (Party Wipe ou falha de objetivo)
	if living_count == 0 or not victory:
		run_state.status = RunState.Status.DEFEAT
		run_state.run_ended.emit(false)
		summary["victory"] = false
		summary["game_over"] = true
		summary["party_wipe"] = (living_count == 0)
		summary["status"] = run_state.status
		summary["amber_earned"] = run_state.calculate_amber()
		return summary

	# 4. Avaliar vitória: completar o nó
	run_state.complete_current_node()
	summary["victory"] = true
	summary["game_over"] = (run_state.status == RunState.Status.VICTORY)
	summary["status"] = run_state.status
	summary["amber_earned"] = run_state.calculate_amber()
	return summary

static func can_deploy_hero(run_state: RunState, hero_id: String) -> bool:
	if run_state == null:
		return false
	return run_state.is_hero_alive(hero_id) and int(run_state.hero_hp.get(hero_id, 0)) > 0
```

---

## 4. Design da Suíte de Testes GUT: `test_run_combat_integration.gd`

**Caminho**: `godot_project/test/unit/test_run_combat_integration.gd`  
**Framework**: `GutTest`  
**Regras**: Formato estrito Arrange-Act-Assert (AAA), isolamento via instâncias limpas no `before_each`/`after_each`, zero leaks (`autofree`), execução segura em modo headless.

### Matriz de Casos de Teste Planejados

| # | Método de Teste | Categoria | Descrição |
|---|---|---|---|
| 1 | `test_bridge_setup_combat_without_run_safe_fallback` | Headless Safety | Retorna dicionário seguro e vazio se `RunState` for nulo ou inativo. |
| 2 | `test_bridge_setup_combat_populates_living_heroes_and_deck` | Setup | Gera payload com heróis vivos, HP atual, max HP, deck e relíquias. |
| 3 | `test_bridge_setup_combat_filters_out_fallen_heroes` | Permadeath | Heróis caídos em combates prévios não são incluídos no setup de combate. |
| 4 | `test_sync_combat_result_updates_partial_hp` | Persistência de PV | Dano parcial sofrido reflete no `RunState.hero_hp`. |
| 5 | `test_sync_combat_result_clamps_overheal_to_max_hp` | Casos de Borda | Cura em combate que ultrapassa `max_hp` é clampeada no limite. |
| 6 | `test_sync_combat_result_clamps_negative_hp_to_zero` | Casos de Borda | HP negativo é clampeado a 0 e ativa permadeath. |
| 7 | `test_sync_combat_result_single_hero_death_marks_fallen` | Permadeath | Herói com 0 HP entra em `fallen_heroes` e emite `hero_died`. |
| 8 | `test_permadeath_hero_cannot_be_healed_subsequently` | Permadeath | `heal_hero` e `heal_party_percent` recusam curar herói caído. |
| 9 | `test_sync_combat_result_party_wipe_triggers_defeat` | Roteamento Derrota | Se todos os heróis caírem, `status = DEFEAT` e `run_ended(false)`. |
| 10 | `test_sync_combat_result_defeat_calculates_amber_without_bonus` | Economia / Meta | Derrota calcula Âmbar Real com base em andares e chefes, sem bônus final. |
| 11 | `test_sync_combat_result_victory_completes_current_node` | Roteamento Vitória | Vitória marca nó como visitado, incrementa andares e mantém run ativa. |
| 12 | `test_sync_combat_result_victory_registers_kills_and_gold` | Economia | Inimigos abatidos e ouro de baús são somados ao estado. |
| 13 | `test_victory_boss_act1_advances_act_and_heals_survivors` | Transição de Ato | Vitória contra Viúva Canibal avança para Ato 2 e cura 25% dos vivos. |
| 14 | `test_victory_final_boss_act3_triggers_final_victory_and_bonus` | Fim de Jogo | Derrotar Rei Isectum define `VICTORY` e adiciona +25 de Âmbar Real. |
| 15 | `test_can_deploy_hero_validation` | Validador | Valida se herói vivo pode ser posicionado e morto é barrado. |

### Código de Referência para Implementação (`test_run_combat_integration.gd`)

```gdscript
# res://test/unit/test_run_combat_integration.gd
extends GutTest

## Suíte de Testes Unitários de Integração: Combate Tático ↔ Run Roguelike (M4)
## Valida persistência bidirecional de PV, permadeath, roteamento e transições.

var _generator: RunMapGenerator
var _rng: RandomNumberGenerator
var _state: RunState

func before_each() -> void:
	_generator = RunMapGenerator.new(8, 3, 2)
	_rng = RandomNumberGenerator.new()
	_rng.seed = 4242
	_state = RunState.new(_generator, _rng)
	var party: Dictionary = {"aquele": 30, "stark": 34, "elden": 26}
	var starter_deck: Array[String] = ["movimento", "trabalho", "escavacao", "ataque", "defesa"]
	_state.start_run(party, starter_deck, 4242)

func after_each() -> void:
	RunSession.clear()
	_state = null
	_generator = null
	_rng = null

# ── 1. Setup & Headless Safety ───────────────────────────────────────────────

func test_bridge_setup_combat_without_run_safe_fallback() -> void:
	# Arrange
	RunSession.clear()

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(null, null)

	# Assert
	assert_false(payload.get("ok", true), "Setup sem run deve retornar ok: false")
	assert_eq(payload.get("living_heroes", []).size(), 0)

func test_bridge_setup_combat_populates_living_heroes_and_deck() -> void:
	# Arrange
	var start_nodes: Array[RunNode] = _state.get_available_nodes()
	var node: RunNode = start_nodes[0]
	_state.move_to(node.id)

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(_state, node, _rng)

	# Assert
	assert_true(payload.get("ok", false))
	assert_eq(payload.get("act", 0), 1)
	assert_eq(payload.get("node_id", -1), node.id)
	assert_eq(payload.get("living_heroes", []).size(), 3)
	assert_eq(payload.get("hero_hp", {})["aquele"], 30)
	assert_eq(payload.get("deck", []).size(), 5)

func test_bridge_setup_combat_filters_out_fallen_heroes() -> void:
	# Arrange
	_state.damage_hero("aquele", 30) # Aquele morre
	var node: RunNode = _state.get_available_nodes()[0]

	# Act
	var payload: Dictionary = RunCombatBridge.setup_combat(_state, node, _rng)

	# Assert
	var living: Array = payload.get("living_heroes", [])
	assert_false(living.has("aquele"), "Herói morto não pode estar nos vivos")
	assert_true(living.has("stark"))
	assert_true(living.has("elden"))
	assert_eq(living.size(), 2)

# ── 2. Persistência de PV ───────────────────────────────────────────────────

func test_sync_combat_result_updates_partial_hp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 18, "stark": 22, "elden": 26},
		"enemies_killed": 3
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary.get("victory", false))
	assert_eq(_state.hero_hp["aquele"], 18, "PV de Aquele persistido")
	assert_eq(_state.hero_hp["stark"], 22, "PV de Stark persistido")
	assert_eq(_state.hero_hp["elden"], 26, "PV de Elden persistido")
	assert_true(_state.is_hero_alive("aquele"))

func test_sync_combat_result_clamps_overheal_to_max_hp() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 999}, # Excesso de cura
		"enemies_killed": 2
	}

	# Act
	RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 30, "PV deve ser clampeado em max_hp (30)")

func test_sync_combat_result_clamps_negative_hp_to_zero() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": -15, "stark": 20, "elden": 20},
		"enemies_killed": 2
	}

	# Act
	RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_eq(_state.hero_hp["aquele"], 0)
	assert_true(_state.fallen_heroes.has("aquele"))

# ── 3. Permadeath ───────────────────────────────────────────────────────────

func test_sync_combat_result_single_hero_death_marks_fallen() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"stark": 20, "elden": 25},
		"fallen_heroes": ["aquele"],
		"enemies_killed": 4
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_false(_state.is_hero_alive("aquele"))
	assert_true(_state.fallen_heroes.has("aquele"))
	assert_eq(_state.get_living_heroes().size(), 2)

func test_permadeath_hero_cannot_be_healed_subsequently() -> void:
	# Arrange
	_state.damage_hero("aquele", 30) # Tombou
	_state.damage_hero("stark", 20)  # 14 / 34 PV

	# Act 1: Fogueira (30% heal)
	_state.heal_party_percent(0.30)

	# Assert 1
	assert_eq(_state.hero_hp["aquele"], 0, "Herói morto não é curado por fogueira")
	assert_gt(_state.hero_hp["stark"], 14, "Herói vivo recebe cura")

	# Act 2: Cura direta
	var res_heal: int = _state.heal_hero("aquele", 50)
	assert_eq(res_heal, 0, "heal_hero direto recusa curar morto")

# ── 4. Roteamento de Derrota & Vitória ───────────────────────────────────────

func test_sync_combat_result_party_wipe_triggers_defeat() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {},
		"fallen_heroes": ["aquele", "stark", "elden"],
		"enemies_killed": 1
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_false(summary["victory"])
	assert_true(summary["game_over"])
	assert_true(summary["party_wipe"])
	assert_eq(_state.status, RunState.Status.DEFEAT)
	assert_false(_state.is_active())

func test_sync_combat_result_defeat_calculates_amber_without_bonus() -> void:
	# Arrange
	_state.floors_cleared = 4
	_state.bosses_defeated = 1
	var combat_res: Dictionary = {
		"victory": false,
		"surviving_heroes_hp": {},
		"fallen_heroes": ["aquele", "stark", "elden"],
		"enemies_killed": 0
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	# 4 andares * 1 + 1 boss * 10 = 14 âmbar (sem bônus de 25 de vitória)
	assert_eq(summary["amber_earned"], 14)

func test_sync_combat_result_victory_completes_current_node() -> void:
	# Arrange
	var node: RunNode = _state.get_available_nodes()[0]
	_state.move_to(node.id)
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 25, "stark": 25, "elden": 25},
		"enemies_killed": 3,
		"gold_earned": 10
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_true(node.visited)
	assert_eq(_state.floors_cleared, 1)
	assert_eq(_state.gold, RunState.STARTING_GOLD + 10)
	assert_eq(_state.enemies_killed, 3)

func test_victory_boss_act1_advances_act_and_heals_survivors() -> void:
	# Arrange
	var boss: RunNode = _state.map.get_boss_node()
	_state.current_node_id = boss.id
	_state.damage_hero("aquele", 15) # 15 / 30 PV
	var combat_res: Dictionary = {
		"victory": true,
		"surviving_heroes_hp": {"aquele": 15, "stark": 34, "elden": 26},
		"enemies_killed": 5
	}

	# Act
	var summary: Dictionary = RunCombatBridge.sync_combat_result(_state, combat_res)

	# Assert
	assert_true(summary["victory"])
	assert_eq(_state.act, 2, "Avançou para o Ato 2")
	assert_eq(_state.bosses_defeated, 1)
	assert_gt(_state.hero_hp["aquele"], 15, "Sobrevivente recebeu cura de transição de Ato (+25%)")

func test_can_deploy_hero_validation() -> void:
	# Arrange
	_state.damage_hero("aquele", 30)

	# Act & Assert
	assert_false(RunCombatBridge.can_deploy_hero(_state, "aquele"))
	assert_true(RunCombatBridge.can_deploy_hero(_state, "stark"))
	assert_false(RunCombatBridge.can_deploy_hero(_state, "inexistente"))
	assert_false(RunCombatBridge.can_deploy_hero(null, "stark"))
```

---

## 5. Design da Suíte de Testes GUT: `test_combat_encounter_generator.gd`

**Caminho**: `godot_project/test/unit/test_combat_encounter_generator.gd`  
**Framework**: `GutTest`  
**Regras**: Formato estrito Arrange-Act-Assert (AAA), determinismo via injeção de RNG com seeds fixas, integridade de castas consultando `IsectumCastes`.

### Matriz de Casos de Teste Planejados

| # | Método de Teste | Categoria | Descrição |
|---|---|---|---|
| 1 | `test_generator_initialization` | Headless Safety | Instanciação bare-node segura sem scene. |
| 2 | `test_generator_safe_fallback_on_invalid_inputs` | Casos de Borda | Retorna encontro básico seguro para atos, nós ou andares inválidos. |
| 3 | `test_generator_determinism_with_same_seed` | Determinismo | Mesma seed gera esquadrão idêntico (tamanho, castas, posições). |
| 4 | `test_combat_node_act1_squad_size_and_basic_castes` | Ato 1 / Combat | Nó `COMBAT` gera 3 a 4 insetos do Tier 1. |
| 5 | `test_siege_node_act1_has_siege_castes_and_larger_squad` | Ato 1 / Siege | Nó `SIEGE` gera 4 a 6 insetos incluindo brutamontes/escavadores. |
| 6 | `test_elite_node_act1_contains_heavy_castes` | Ato 1 / Elite | Nó `ELITE` contém insetos de alto impacto (`escaravelho_couracado`). |
| 7 | `test_boss_node_act1_generates_viuva_canibal` | Ato 1 / Boss | Nó `BOSS` do Ato 1 gera `viuva_canibal` (`tece_teia`) com alta vida. |
| 8 | `test_combat_node_act2_includes_tier2_castes` | Ato 2 / Scaling | Nó no Ato 2 seleciona castas como `vespa_furtiva` ou `louva_deus_ceifador`. |
| 9 | `test_boss_node_act2_generates_rainha_do_enxame` | Ato 2 / Boss | Nó `BOSS` do Ato 2 gera `rainha_do_enxame`. |
| 10 | `test_boss_node_act3_generates_rei_isectum` | Ato 3 / Boss | Nó `BOSS` do Ato 3 gera `rei_isectum`. |
| 11 | `test_generated_enemies_have_valid_caste_data` | Integridade | Todos os inimigos gerados possuem casta válida no catálogo `IsectumCastes`. |
| 12 | `test_spawn_zones_are_valid_perimeter_zones` | Tabuleiro | As zonas alvo de spawn pertencem aos 4 perímetros (`SPAWN_NORTE`, `SUL`, etc.). |

### Código de Referência para Implementação (`test_combat_encounter_generator.gd`)

```gdscript
# res://test/unit/test_combat_encounter_generator.gd
extends GutTest

## Suíte de Testes Unitários: Gerador de Encontros de Combate (CombatEncounterGenerator)
## Valida composição de esquadrões por Ato, nó e determinismo via seed.

var _gen: CombatEncounterGenerator
var _rng: RandomNumberGenerator

func before_each() -> void:
	_gen = CombatEncounterGenerator.new()
	_rng = RandomNumberGenerator.new()
	_rng.seed = 98765

func after_each() -> void:
	_gen = null
	_rng = null

# ── 1. Inicialização & Segurança ─────────────────────────────────────────────

func test_generator_initialization() -> void:
	assert_not_null(_gen, "Gerador deve instanciar com sucesso")

func test_generator_safe_fallback_on_invalid_inputs() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(-1, -1, -1, null)

	# Assert
	assert_not_null(enc)
	assert_true(enc.has("enemies"))
	assert_gt(enc["enemies"].size(), 0, "Deve gerar fallback com pelo menos 1 inimigo básico")

# ── 2. Determinismo ──────────────────────────────────────────────────────────

func test_generator_determinism_with_same_seed() -> void:
	# Arrange
	var rng1: RandomNumberGenerator = RandomNumberGenerator.new()
	var rng2: RandomNumberGenerator = RandomNumberGenerator.new()
	rng1.seed = 5555
	rng2.seed = 5555

	# Act
	var enc1: Dictionary = _gen.generate_encounter(1, 3, RunNode.NodeType.COMBAT, rng1)
	var enc2: Dictionary = _gen.generate_encounter(1, 3, RunNode.NodeType.COMBAT, rng2)

	# Assert
	assert_eq(enc1["enemies"].size(), enc2["enemies"].size())
	for i in range(enc1["enemies"].size()):
		assert_eq(enc1["enemies"][i]["caste_id"], enc2["enemies"][i]["caste_id"])
		assert_eq(enc1["enemies"][i]["target_zone"], enc2["enemies"][i]["target_zone"])

# ── 3. Composição de Esquadrão no Ato 1 ──────────────────────────────────────

func test_combat_node_act1_squad_size_and_basic_castes() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 0, RunNode.NodeType.COMBAT, _rng)
	var enemies: Array = enc["enemies"]

	# Assert
	assert_between(enemies.size(), 3, 4, "COMBAT regular do Ato 1 tem 3 a 4 inimigos")
	for e in enemies:
		var cid: String = str(e["caste_id"])
		assert_true(
			cid in ["zangao_invasor", "soldado_mandibula", "operario_escavador", "formiga_acida", "barata_praga", "batedor", "soldado"],
			"Casta %s deve ser básica do Tier 1" % cid
		)

func test_siege_node_act1_has_siege_castes_and_larger_squad() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 4, RunNode.NodeType.SIEGE, _rng)
	var enemies: Array = enc["enemies"]

	# Assert
	assert_between(enemies.size(), 4, 6, "SIEGE tem 4 a 6 inimigos")
	var has_siege_unit: bool = false
	for e in enemies:
		var cid: String = str(e["caste_id"])
		if cid in ["operario_escavador", "besouro_rinoceronte", "escaravelho_couracado", "besouro"]:
			has_siege_unit = true
			break
	assert_true(has_siege_unit, "Encontro de Cerco deve conter especialista em estruturas")

func test_elite_node_act1_contains_heavy_castes() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 6, RunNode.NodeType.ELITE, _rng)
	var enemies: Array = enc["enemies"]

	# Assert
	assert_gt(enemies.size(), 0)
	var has_heavy: bool = false
	for e in enemies:
		var cid: String = str(e["caste_id"])
		if cid in ["escaravelho_couracado", "besouro_rinoceronte", "louva_deus_ceifador", "colosso_isectum"]:
			has_heavy = true
			break
	assert_true(has_heavy, "Nó Elite deve conter pelo menos uma casta pesada")

func test_boss_node_act1_generates_viuva_canibal() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 11, RunNode.NodeType.BOSS, _rng)

	# Assert
	assert_eq(enc.get("boss_id", ""), "viuva_canibal", "Chefe do Ato 1 é Viúva Canibal")
	var boss_found: bool = false
	for e in enc["enemies"]:
		if str(e.get("caste_id", "")) in ["tece_teia", "viuva_canibal"] and bool(e.get("is_boss", false)):
			boss_found = true
			assert_gte(int(e["hp"]), 50, "Chefe deve ter vida substancialmente maior")
			break
	assert_true(boss_found, "Chefe Viúva Canibal deve estar na lista de inimigos")

# ── 4. Escalonamento por Ato ────────────────────────────────────────────────

func test_combat_node_act2_includes_tier2_castes() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(2, 2, RunNode.NodeType.COMBAT, _rng)
	var enemies: Array = enc["enemies"]

	# Assert
	assert_gt(enemies.size(), 0)
	var has_tier2: bool = false
	for e in enemies:
		var cid: String = str(e["caste_id"])
		if cid in ["vespa_furtiva", "louva_deus_ceifador", "centopeia_venenosa", "libelula_bombardeira", "vagalume_cego", "aranha_saltadora"]:
			has_tier2 = true
			break
	assert_true(has_tier2, "Ato 2 deve introduzir castas Tier 2")

func test_boss_node_act2_generates_rainha_do_enxame() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(2, 11, RunNode.NodeType.BOSS, _rng)

	# Assert
	assert_eq(enc.get("boss_id", ""), "rainha_do_enxame")

func test_boss_node_act3_generates_rei_isectum() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(3, 11, RunNode.NodeType.BOSS, _rng)

	# Assert
	assert_eq(enc.get("boss_id", ""), "rei_isectum")

# ── 5. Integridade do Catálogo de Castas ─────────────────────────────────────

func test_generated_enemies_have_valid_caste_data() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 1, RunNode.NodeType.COMBAT, _rng)

	# Assert
	for e in enc["enemies"]:
		var cid: String = str(e["caste_id"])
		var caste: IsectumCasteData = IsectumCastes.get_caste(cid)
		assert_not_null(caste, "Casta %s deve existir no IsectumCastes" % cid)
		assert_gt(int(e["hp"]), 0)
		assert_gt(int(e["ac"]), 0)
		assert_gt(int(e["move_range"]), 0)

func test_spawn_zones_are_valid_perimeter_zones() -> void:
	# Arrange & Act
	var enc: Dictionary = _gen.generate_encounter(1, 1, RunNode.NodeType.COMBAT, _rng)
	var valid_zones: Array[String] = [
		FortressBoard.ZONE_SPAWN_NORTE,
		FortressBoard.ZONE_SPAWN_SUL,
		FortressBoard.ZONE_SPAWN_LESTE,
		FortressBoard.ZONE_SPAWN_OESTE
	]

	# Assert
	for e in enc["enemies"]:
		var z: String = str(e.get("target_zone", ""))
		assert_true(z in valid_zones, "Zona de spawn %s deve ser um dos 4 perímetros externos" % z)
```

---

## 6. Caveats

1. **Boss Multicelular 3x3 (Rei Isectum)**:
   - A lógica de pegada física 3x3 e fases FSM pertence ao Marco M6. No Marco M4, `CombatEncounterGenerator` fornece o identificador de chefe canônico (`boss_id = "rei_isectum"`) e sua casta base, permitindo que a integração de M4 permaneça desacoplada e 100% testável antes da implementação completa de M6.
2. **Salvaguardas de Morte (Death Saves)**:
   - O `CombatRules.gd` suporta contadores de sucesso/falha de salvaguardas de morte. O design de M4 estabelece que se um herói terminar o combate com 0 PV (seja por incapacitação ou morte definitiva), ele é registrado em `fallen_heroes` para fins de persistência na run.
3. **Isolamento Standalone do Cerco**:
   - `CercoGameController` não deve quebrar nem assumir que `RunSession.has_active_run()` é sempre verdadeiro. Quando executado fora da run, o fallback preserva estritamente o comportamento legado.

---

## 7. Conclusão

O design de persistência de PV, permadeath e roteamento de vitória/derrota para o Marco M4 fecha o elo vital entre o mapa procedimental (M1/M2), os espólios e relíquias (M3) e o combate tático no tabuleiro 20x20. As duas novas classes estipuladas (`RunCombatBridge` e `CombatEncounterGenerator`) operam como modelos puros (`RefCounted`), viabilizando cobertura de testes 100% automatizada e livre de vazamento de nós em GUT headless, garantindo robustez antes da fase de implementação.

---

## 8. Método de Verificação Independente

1. **Inspeção de Arquivos**:
   - Verificar se `godot_project/scripts/run/combat/RunCombatBridge.gd` e `godot_project/scripts/run/combat/CombatEncounterGenerator.gd` seguem estritamente as assinaturas projetadas.
   - Verificar se `godot_project/test/unit/test_run_combat_integration.gd` e `godot_project/test/unit/test_combat_encounter_generator.gd` utilizam a estrutura Arrange-Act-Assert (AAA) e limpam os nós criados (`autofree`).
2. **Execução de Testes Unitários GUT**:
   ```bash
   bash godot_project/run_gut_tests.sh -gselect=test_run_combat_integration.gd
   bash godot_project/run_gut_tests.sh -gselect=test_combat_encounter_generator.gd
   bash godot_project/run_gut_tests.sh
   ```
3. **Condições de Invalidação**:
   - Herói caído sendo curado por fogueira ou transição de ato (violação de permadeath).
   - Herói caído sendo colocado no tabuleiro no combate seguinte.
   - PV do herói após combate não persistindo na tela do mapa (`RunMapScreen`).
   - Falha ao disparar `RewardModal` após vitória em nó de combate regular.
