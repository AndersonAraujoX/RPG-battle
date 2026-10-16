# Handoff Report — Survey Phase: Technical Specification Mining (M3 - M8)

**Author**: Spec Miner (Survey Phase)  
**Target File**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1/handoff.md`  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/spec_miner_survey_1`  
**Date**: 2026-10-16T01:14:00Z  

---

## 1. Observation

### 1.1 Authoritative Specification Documents
- **`CAMPANHA_ROGUELIKE.md`**: Official Game Design & Architecture Document ("A Queda do Rei Isectum").
  - Lines 9–30: Core Roguelike Loop (`Escolher Nó -> Combate Tático/Cerco/Evento -> Recompensa -> Fogueira/Forja -> Vitória/Derrota -> Âmbar Real`), Micro/Meso/Macro/Meta tactical scales.
  - Lines 39–56: **Ato I** (*O Cerco da Última Fortaleza*), Fases `fase_01` a `fase_04`, Castas Tier 1 (`larva_carniceira`, `formiga_acida`, `besouro_gorgulho`, `gafanhoto_praga`), Chefe `viuva_canibal` (teias imobilizantes, canibalismo de larvas para cura).
  - Lines 59–80: **Ato II** (*A Descida pelos Túneis Vivos*), Fases `fase_05` a `fase_08`, Iluminação de tochas, Casulos de quitina e ovos (eclosão após 3 rodadas), Mini-chefe `cigarra_ressonante` (ondas sônicas atordoantes em área), Chefe `rainha_do_enxame` (`chamado_da_rainha` a cada 2 turnos, guardas reais protetores).
  - Lines 82–98: **Ato III** (*A Colmeia-Mãe e o Trono de Âmbar*), Fases `fase_09` a `fase_12`, 3 Corações da Colmeia (`fase_09` Mente, `fase_10` Carapaça, `fase_11` Ninhada) aplicando penalidades permanentes ao Rei Isectum; mecânica de desvio opcional com recompensa de Âmbar dobrado.
  - Lines 101–133: **Boss Final Rei Isectum (`rei_isectum`)**:
    - Tamanho: `3×3` tiles (imune a empurrões).
    - Vida Total: `450 PV` (3 Fases de 150 PV cada).
    - CA Base: `19` (`16` com Coração da Carapaça destruído).
    - Imunidades: *Envenenado*, *Atordoado*.
    - Fraqueza: *Fogo (2×)* na Fase 3.
    - Fase 1 (450 ➔ 300 PV): *O Soberano no Trono* (Trono de Âmbar, vantagem de elevação, Comando Absoluto, Lança de Âmbar, destruição de pilares via cartas de Escavação).
    - Fase 2 (300 ➔ 150 PV): *A Muralha Viva* (queda com screen shake, arena dinâmica com bordas em miasma ácido corrosivo, Rugido Feromônico, Esmagamento Colossal).
    - Fase 3 (150 ➔ 0 PV): *Coroa Quebrada / Desespero do Enxame* (CA -3, núcleo exposto a fogo 2x, 2 ações por rodada, habilidade letal *Devorar Essência* que drena herói caído a 0 PV curando 40 PV).
  - Lines 136–149: Tabela de tipos e pesos de nós do mapa (`COMBAT`: 45%, `ELITE`: 12%, `SIEGE`: 10%, `EVENT`: 15%, `CAMPFIRE`: 10%, `FORGE`: 8%, `BOSS`: Fixo).
  - Lines 152–165: Persistência na Run (grupo de 3, PV persistente, permadeath, deck, ouro, relíquias) vs. Meta-Progressão (Âmbar Real: `1 por andar + 10 por boss + 25 na vitória`, desbloqueio dos 8 heróis restantes, Códice/Bestiário, 10 Níveis de Ascensão).
  - Lines 187–195: Roteiro dos marcos M1 a M8.

- **`ORIGINAL_REQUEST.md`**:
  - Requisitos R1 (M3), R2 (M4), R3 (M5), R4 (M6), R5 (M7 & M8).
  - Foco em acoplamento type-safe, persistência contínua, D&D 5e death saves, e integridade da suíte de testes GUT.

### 1.2 Baseline Existente no Código
- **`godot_project/scripts/run/RunState.gd`**:
  - `status`: Enum `NOT_STARTED`, `ACTIVE`, `VICTORY`, `DEFEAT`.
  - Constantes: `FINAL_ACT = 3`, `MAX_PARTY_SIZE = 3`, `STARTING_GOLD = 50`, `ACT_TRANSITION_HEAL_PCT = 0.25`, `AMBER_PER_FLOOR = 1`, `AMBER_PER_BOSS = 10`, `AMBER_VICTORY_BONUS = 25`.
  - Dicionário de chefes: `ACT_BOSSES = {1: "viuva_canibal", 2: "rainha_do_enxame", 3: "rei_isectum"}`.
  - Métodos implementados: `start_run()`, `damage_hero()`, `heal_hero()`, `heal_party_percent()`, `add_gold()`, `spend_gold()`, `add_card()`, `remove_card()`, `add_relic()`, `has_relic()`, `calculate_amber()`, `to_dict()`, `from_dict()`.
  - Observação crítica: `RunState.relics` armazena `Array[String]`, mas atualmente não há um `RelicManager` que conecte esses IDs aos sinais do `EventBus`.

- **`godot_project/scripts/run/RunNodeResolver.gd`**:
  - Auto-resolução simplificada (placeholder de M1/M2) via `resolve_combat()`.
  - Em M4, deve ser especializado/substituído pela transição e resolução do combate tático real.

- **`godot_project/scripts/run/RunMapScreen.gd`**:
  - Interface do mapa funcional. Exibe barras de PV dos heróis (`_update_hero_bars`), ouro, cartas, âmbar acumulado.
  - Botão de nó aciona `resolver.resolve(state, rng)`. Em M4, a seleção de nós de combate levará à arena de batalha em `Main.tscn`.

- **`godot_project/scripts/autoload/EventBus.gd`**:
  - Sinais disponíveis: `unit_attacked`, `unit_damaged`, `unit_died`, `card_played`, `dice_rolled`, `turn_changed`, `wall_breached`, `status_applied`, `status_removed`, etc.
  - Telemetria integrada: `emit_logged()`, `get_emission_count()`.

- **`godot_project/scripts/cerco/IsectumCastes.gd` & `dados/fases/`**:
  - Catálogo de 24 castas completas (`CANONICAL_IDS`) com estatísticas de combate, atributos de Brutamontes, Infiltrador, Catapulta, Voador e Boss.
  - Todos os 24 assets gráficos `.png` estão presentes e importados em `godot_project/assets/images/characters/monsters/isectum/`.
  - `FortressBoardView.gd` possui mapeamento de sprites para todas as castas e seus apelidos.

- **`dados/personagens.json` & `DataManager.gd`**:
  - Contém os 3 heróis iniciais (`Aquele`, `Stark`, `Elden`) e todos os 8 heróis de meta-progressão (`Doom`, `Gruu`, `Kuro`, `Darwin`, `Novak`, `Rilem`, `Yukito`, `Koema`).

- **`godot_project/scripts/tactical/TacticalGrid.gd` & `FortressBoard.gd`**:
  - Grade 20x20 com AStar2D pathfinding, cálculo de cobertura (+2/+5 CA), linha de visão (Bresenham), destruição de estruturas (`_structure_hp_grid`, `structure_damaged`, `structure_destroyed`), terrenos e perigos (`TERRENO_VENENO`, `TERRENO_FOGO`).
  - `CombatRules.gd`: D&D 5e regras, modificadores, testes de resistência, `DeathSaveResult` e estados (`NORMAL`, `INCONSCIENTE`, `ESTABILIZADO`, `MORTO`).
  - `StatusManager.gd`: Condições canônicas (`stunned`, `poisoned`, `frightened`, `burning`, `restrained`, etc.).

---

## 2. Logic Chain

1. **Da Premissa de M3 (Recompensas, Relíquias e Forja)**:
   - *Observação*: `RunState.relics` já armazena `Array[String]`, e `RunState` já possui `add_card`, `remove_card`, `add_gold`, `spend_gold`.
   - *Dedução*: A camada de dados de M3 no `RunState` está pronta, mas faltam:
     a) O modal interativo visual pós-combate "Escolha 1 de 3 Cartas" com opção de Skip e coleta de ouro.
     b) A classe de controle/catálogo de Relíquias (`RelicManager`) que escuta sinais no `EventBus` e injeta bônus passivos (ex: dano adicional, redução de dano, ouro extra, cura na fogueira).
     c) O modal/tela da Forja Anã (`FORGE`) conectando a compra de cartas, remoção de cartas por taxa progressiva de ouro e compra de relíquias ao `RunState`.

2. **Da Premissa de M4 (Integração do Combate Tático e Permadeath)**:
   - *Observação*: `RunNodeResolver.resolve_combat` é explicitamente um placeholder procedural que causa dano aleatório no M1/M2.
   - *Dedução*: Para M4, o fluxo deve interceptar nós de combate (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`):
     a) Salvar o nó atual e a configuração de combate no `RunSession`.
     b) Transicionar a cena para `Main.tscn` (ou instanciar `CercoGameController`/`TacticalGrid`).
     c) Carregar a arena tática 20x20 e posicionar os heróis vivos de acordo com `RunState.hero_hp` (heróis em `fallen_heroes` não entram no tabuleiro).
     d) Gerar os inimigos correspondentes ao Ato e andar da expedição a partir de `IsectumCastes`.
     e) Sincronizar qualquer dano sofrido diretamente com `RunState.damage_hero()`.
     f) Ao fim do combate: se o grupo for derrotado (`get_living_heroes().is_empty()`), acionar `RunState.status = Status.DEFEAT` e tela de derrota; se vitorioso, abrir Recompensas M3 e retornar ao `RunMapScreen` com o nó concluído.

3. **Da Premissa de M5 (Ato II: Túneis Vivos)**:
   - *Observação*: No Ato II, o combate se desloca da superfície de Karak-Dur para as galerias subterrâneas de quitina e resina.
   - *Dedução*: Requer três mecânicas centrais:
     a) **Iluminação de Tochas**: Sistema de visibilidade em torno de cada herói vivo (raio padrão de 3 células Chebyshev; células na escuridão impedem mirar ataques à distância e impõem névoa).
     b) **Casulos de Quitina e Ovos**: Entidades no grid com 15 PV e temporizador de 3 turnos. Se não destruídos a tempo, eclodem invocando insetos Tier 2 e causando espirro ácido aos adjacentes.
     c) **Chefes do Ato II**: Mini-chefe de Elite `cigarra_ressonante` (ataque sônico em área que atordoa heróis agrupados) e Chefe do Ato `rainha_do_enxame` (`chamado_da_rainha` a cada 2 turnos, carapaça imune/resistente enquanto houver guardas adjacentes).

4. **Da Premissa de M6 (Ato III: 3 Corações e Rei Isectum)**:
   - *Observação*: `CAMPANHA_ROGUELIKE.md` define que os 3 Corações da Colmeia (`fase_09`, `fase_10`, `fase_11`) aplicam debuffs permanentes ao Rei Isectum, e o Rei ocupa `3×3` células na `fase_12` com 3 fases de 150 PV (total 450 PV).
   - *Dedução*:
     a) Cada Coração vencido grava um flag no estado (`heart_mind_destroyed`, `heart_carapace_destroyed`, `heart_brood_destroyed`).
     b) Se o jogador desviar dos Corações, o Rei enfrenta o grupo com força total, mas concede o dobro de Âmbar Real ao final.
     c) O Boss Final `rei_isectum` necessita de uma máquina de estados tática de 3 fases:
        - **Fase 1 (450 ➔ 300 PV)**: Trono de Âmbar com pilares destrutíveis via cartas de *Escavação*; Lança de Âmbar e Comando Absoluto fora de turno (suprimido se Coração da Mente abatido).
        - **Fase 2 (300 ➔ 150 PV)**: Muralha Viva com queda na arena, Screen Shake, miasma ácido que engole as bordas da arena 20x20 reduzindo a área útil, Rugido Feromônico (teste de sabedoria contra Medo), Esmagamento Colossal e reforços da guarda (suprimidos se Coração da Ninhada abatido).
        - **Fase 3 (150 ➔ 0 PV)**: Coroa Quebrada com CA reduzida em -3, fraqueza 2x a dano de fogo, 2 ações por rodada e habilidade letal *Devorar Essência* que tenta consumir heróis caídos a 0 PV dentro de 1 turno para curar 40 PV.

5. **Da Premissa de M7 & M8 (Meta-Progressão e Ascensão 1-10)**:
   - *Observação*: O Âmbar Real acumulado deve persistir entre expedições e ser utilizável para destravar 8 heróis adicionais e cartas rúnicas.
   - *Dedução*:
     a) Criar subsistema de serialização permanente `user://meta_save.json` com versão de schema, saldo de âmbar, lista de heróis desbloqueados, cartas desbloqueadas e estatísticas globais.
     b) Interface gráfica no Menu Principal para o **Quartel dos Heróis & Códice**, permitindo compras com Âmbar.
     c) **Modo de Ascensão (1 a 10)**: Desbloqueado após abater o Rei Isectum pela primeira vez. Cada nível adiciona modificadores de dificuldade cumulativos (dano inimigo, CA inimiga, ouro escasso, fogueira reduzida, tocha menor, chefes reforçados).
     d) Telas de encerramento da expedição (Vitória Épica / Derrota Detalhada) exibindo estatísticas completas e conversão em Âmbar Real.

---

## 3. Features Discovered & Edge Cases

### 3.1 Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | M3: Recompensas | Modal "Escolha 1 de 3 Cartas" | Modal pós-combate apresentando 3 cartas aleatórias do pool para draft na expedição | `RunState`, pool de cartas do Ato | Carta adicionada ao deck via `add_card()` | Se o deck estiver cheio ou pool vazio, oferece cartas básicas | `CAMPANHA_ROGUELIKE.md` § 1, 4; `ORIGINAL_REQUEST.md` R1 |
| 2 | M3: Recompensas | Opção de Skip ("Pular") | Permite recusar adicionar cartas para manter o deck enxuto | Clique no botão "Pular" | Nenhuma carta adicionada; avança tela | N/A (operação segura) | `CAMPANHA_ROGUELIKE.md` § 1, 4 |
| 3 | M3: Recompensas | Coleta de Ouro do Nó | Concede ouro baseado no tipo do nó (`COMBAT`: 15, `SIEGE`: 20, `ELITE`: 30, `BOSS`: 50) | Tipo do nó, modificadores de relíquias | `RunState.add_gold(amount)` | Não permite valores negativos | `RunNodeResolver.gd:16-20`; `RunState.gd:189` |
| 4 | M3: Relíquias | Gerenciador de Relíquias (`RelicManager`) | Subsistema que registra relíquias ativas e conecta callbacks aos sinais do `EventBus` | IDs de relíquias no `RunState.relics` | Buffs/debuffs passivos em combate/mapa | Ignora IDs não cadastrados com log de warning | `ORIGINAL_REQUEST.md` R1; `EventBus.gd:8-71` |
| 5 | M3: Relíquias | Catálogo Canônico de Relíquias | Catálogo inicial com 10 relíquias temáticas com efeitos táticos e econômicos | Identificador da relíquia | Efeito passivo vinculado ao `EventBus` | IDs duplicados são rejeitados por `RunState.add_relic()` | `CAMPANHA_ROGUELIKE.md` § 4; `RunState.gd:214` |
| 6 | M3: Forja | Mercado da Forja Anã (`FORGE`) | Tela interativa de compras no nó de forja permitindo comprar cartas, relíquias e serviços | Saldo de ouro do `RunState` | Dedução de ouro e inclusão de itens | Botões desabilitados quando ouro < custo | `CAMPANHA_ROGUELIKE.md` § 4; `ORIGINAL_REQUEST.md` R1 |
| 7 | M3: Forja | Remoção de Cartas do Deck | Serviço de remoção de cartas indesejadas por ouro com custo progressivo (50g, 75g, 100g...) | Seleção da carta a expurgar | `RunState.remove_card(card_id)` | Impede remover até deixar deck vazio (mínimo de cartas seguras) | `CAMPANHA_ROGUELIKE.md` § 4; `RunState.gd:207` |
| 8 | M4: Combate | Integração do Nó ao Tabuleiro Tático | Transiciona a seleção de nós `COMBAT`/`ELITE`/`SIEGE`/`BOSS` para a arena de combate `Main.tscn` | Nó clicado no `RunMapScreen`, `RunSession` | Inicialização da cena de combate 20x20 | Valida se nó está na lista de disponíveis | `RunNodeResolver.gd:5-9`; `ORIGINAL_REQUEST.md` R2 |
| 9 | M4: Combate | Geração de Encontros por Ato | Monta a composição de inimigos conforme o Ato atual e o andar utilizando o catálogo `IsectumCastes` | Ato (1, 2, 3), andar e tipo de nó | Lista de unidades spawnadas na arena | Fallback para zangão/soldado se casta falhar | `IsectumCastes.gd:35-83`; `CAMPANHA_ROGUELIKE.md` § 2 |
| 10 | M4: Combate | Persistência Contínua de PV | Dano e cura sofridos na arena tática são refletidos diretamente em `RunState.hero_hp` | Sinais `unit_damaged`, cura em batalha | `RunState.damage_hero()`, `RunState.heal_hero()` | Dano limitado a 0; cura limitada ao PV máximo | `RunState.gd:156-186`; `CAMPANHA_ROGUELIKE.md` § 5 |
| 11 | M4: Combate | Morte Permanente na Run (*Permadeath*) | Heróis que chegam a 0 PV (ou falham death saves) entram em `fallen_heroes` e não reaparecem | PV = 0 ou falha nos 3 Death Saves | `hero_died` emitido; herói indisponível | Não pode ser curado na fogueira nem em nós futuros | `RunState.gd:165-174`; `CAMPANHA_ROGUELIKE.md` § 5 |
| 12 | M4: Combate | Fim da Expedição por Derrota | Se todos os heróis caírem (`get_living_heroes().is_empty()`), a run termina em derrota imediata | Todos os heróis em `fallen_heroes` | `RunState.status = Status.DEFEAT`, `run_ended(false)` | Encerra o ciclo e aciona tela de derrota | `RunState.gd:168-170` |
| 13 | M5: Ato II | Iluminação de Tochas Subterrâneas | Visibilidade dinâmica na grade 20x20 ao redor dos heróis (raio 3 células); névoa nas células escuras | Posições dos heróis na grade | Células iluminadas vs. escuras no `TacticalGrid` | Alvos na escuridão não podem ser alvejados à distância | `CAMPANHA_ROGUELIKE.md` § 2 (Ato II); `ORIGINAL_REQUEST.md` R3 |
| 14 | M5: Ato II | Casulos de Quitina e Ovos | Estruturas no tabuleiro com 15 PV e temporizador de 3 turnos que eclodem se não forem destruídas | Turno de combate decrementando | Eclosão: spawna Isectum Tier 2 + dano ácido adjacente | Se destruído antes do turno 0, impede o spawn | `CAMPANHA_ROGUELIKE.md` § 2 (Ato II) |
| 15 | M5: Ato II | Mini-Chefe Cigarra Ressonante | Casta de elite com ataque sônico em área que aplica a condição `stunned` em heróis agrupados | Posição dos heróis na explosão sônica | Dano sônico + condição `stunned` (DC 13 Con) | Imune a atordoamento próprio | `CAMPANHA_ROGUELIKE.md` § 2 (Ato II); `StatusManager.gd:25` |
| 16 | M5: Ato II | Chefe Rainha do Enxame | Chefe do Ato II com invocação de ninhadas (`chamado_da_rainha`) e resistência por guardas | Turnos pares de combate, posições dos guardas | Spawns de larvas/casulos; 50% redução de dano | Morte aciona transição narrativa e cura de 25% | `CAMPANHA_ROGUELIKE.md` § 2 (Ato II); `IsectumCastes.gd:113` |
| 17 | M6: Ato III | Nós Especiais dos 3 Corações | 3 encontros de Elite (`fase_09`, `fase_10`, `fase_11`) cuja destruição enfraquece o Rei Isectum | Nós de Coração no grafo do Ato III | Flags de enfraquecimento gravadas no `RunState` | O jogador pode contornar os Corações | `CAMPANHA_ROGUELIKE.md` § 2 (Ato III); `ORIGINAL_REQUEST.md` R4 |
| 18 | M6: Ato III | Penalidade do Coração da Mente | Desativa o controle mental e suprime o comando de ataque fora de turno do Rei na rodada 1 | `fase_09` concluída | Flag `heart_mind_destroyed = true` | Se não destruído, Rei age com Comando Absoluto | `CAMPANHA_ROGUELIKE.md` § 2 (Ato III) |
| 19 | M6: Ato III | Penalidade do Coração da Carapaça | Reduz a Classe de Armadura (CA) do Rei Isectum de 19 para 16 em todas as fases | `fase_10` concluída | Flag `heart_carapace_destroyed = true` | Se não destruído, Rei mantém CA 19 | `CAMPANHA_ROGUELIKE.md` § 2 (Ato III) |
| 20 | M6: Ato III | Penalidade do Coração da Ninhada | Impede o Rei Isectum de invocar guardas reais na Fase 2 da luta final | `fase_11` concluída | Flag `heart_brood_destroyed = true` | Se não destruído, Rei invoca 2 guardas reais | `CAMPANHA_ROGUELIKE.md` § 2 (Ato III) |
| 21 | M6: Ato III | Bônus por Pular os Corações | Dobra o Âmbar Real ganho se o jogador derrotar o Rei Isectum sem destruir nenhum dos 3 Corações | Derrota do Rei com os 3 Corações intactos | `amber = amber * 2` | Requer vitória válida contra o Rei em força total | `CAMPANHA_ROGUELIKE.md` § 2 (Ato III) |
| 22 | M6: Boss Final | Entidade Multicelular Rei Isectum (3×3) | Entidade gigante ocupando bloco 3x3 (9 células) no grid 20x20, imune a empurrões e deslocamentos | Posição de âncora `(x, y)` | Ocupa 9 células na grade tática; bloqueia passagem | Impede sobreposição com obstáculos | `CAMPANHA_ROGUELIKE.md` § 3; `TacticalGrid.gd:220` |
| 23 | M6: Boss Final | Fase 1: O Soberano no Trono | Trono elevado (+vantagem), Lança de Âmbar e pilares destrutíveis com cartas de *Escavação* | PV 450 -> 300, dano nos pilares | Queda do trono quando os 4 pilares caírem | Cartas sem badge de Escavação causam dano normal | `CAMPANHA_ROGUELIKE.md` § 3 (Fase 1); `CardData.gd:17` |
| 24 | M6: Boss Final | Fase 2: A Muralha Viva | Queda com Screen Shake, arena dinâmica com anéis externos de miasma ácido e Rugido Feromônico | PV 300 -> 150, rodadas decorridas | Encolhimento da arena segura; teste contra Medo | Heróis em miasma sofrem 10 dano ácido/turno | `CAMPANHA_ROGUELIKE.md` § 3 (Fase 2); `StatusManager.gd:38` |
| 25 | M6: Boss Final | Fase 3: Coroa Quebrada | CA -3, fraqueza 2x a dano de fogo, 2 ações/rodada e habilidade letal *Devorar Essência* | PV 150 -> 0, herói caído adjacente | Ataques duplicados, consome aliado para curar 40 PV | Jogador tem 1 rodada para resgatar/curar aliado | `CAMPANHA_ROGUELIKE.md` § 3 (Fase 3); `CombatRules.gd:14` |
| 26 | M7: Meta | Persistência de Âmbar Real (`user://meta_save.json`) | Gravação atômica em disco do progresso permanente, saldo de âmbar, desbloqueios e histórico | Final de cada run ou compra no quartel | Arquivo JSON persistido em `user://meta_save.json` | Recuperação automática com backup se JSON corrompido | `ORIGINAL_REQUEST.md` R5; `RunState.gd:227` |
| 27 | M7: Meta | Quartel dos Heróis (Desbloqueio de 8 Heróis) | Desbloqueio permanente de `Doom`, `Gruu`, `Kuro`, `Darwin`, `Novak`, `Rilem`, `Yukito`, `Koema` | Saldo de Âmbar Real no meta-save | Heróis liberados para seleção em novas expedições | Impede compra se saldo de âmbar insuficiente | `CAMPANHA_ROGUELIKE.md` § 5; `dados/personagens.json` |
| 28 | M7: Meta | Desbloqueio de Cartas Rúnicas | Liberação de cartas rúnicas e avançadas para o pool de drops de expedições futuras | Âmbar gasto na aba de runas do Códice | Cartas rúnicas adicionadas ao pool de recompensas | Cartas já destravadas ficam indisponíveis para compra | `CAMPANHA_ROGUELIKE.md` § 1, 5; `ORIGINAL_REQUEST.md` R5 |
| 29 | M8: Ascensão | Níveis de Ascensão (1 a 10) | Modificadores cumulativos de dificuldade desbloqueados após a primeira vitória sobre o Rei | Nível de Ascensão selecionado (1 a 10) | Aplicação de modificadores de regras na run | Níveis superiores exigem vitória no nível anterior | `CAMPANHA_ROGUELIKE.md` § 5, 7; `ORIGINAL_REQUEST.md` R5 |
| 30 | M8: Telas Finais | Tela de Vitória / Derrota com Estatísticas | Tela de encerramento detalhando andares vencidos, abates, chefes, dano, relíquias e âmbar ganho | Estado final da run (`RunState.to_dict()`) | Resumo visual dark fantasy e concessão de Âmbar | Mostra causas de derrota ou triunfo definitivo | `CAMPANHA_ROGUELIKE.md` § 1, 5; `GameOverModal.gd` |

---

### 3.2 Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | M3: Recompensas | Pool de cartas vazio ou esgotado ao abrir o modal pós-combate | O seletor deve gerar cópias de cartas básicas de fallback (`marcha`, `trabalho`, `escavacao`) em vez de falhar com erro nulo ou travar o modal. |
| 2 | M3: Recompensas | Jogador clica repetidamente no botão de selecionar carta ou fecha a janela | A recompensa de carta e ouro deve ser consumida uma única vez por nó; reabrir o modal não pode duplicar recompensas. |
| 3 | M3: Relíquias | Inclusão de relíquia já existente no inventário (`add_relic`) | `RunState.add_relic()` retorna `false` e impede itens duplicados idênticos de poluir a lista `relics`. |
| 4 | M3: Forja | Tentativa de compra de carta ou relíquia com ouro exatamente igual ao custo | Deve debitar 100% do ouro, reduzir o saldo a 0 e entregar o item com sucesso sem erros de arredondamento. |
| 5 | M3: Forja | Remoção de cartas repetida até restar 1 ou nenhuma carta no deck | O sistema deve impor um tamanho mínimo de deck (ex: 5 cartas) para evitar que o jogador fique sem cartas para sacar em combate. |
| 6 | M4: Combate | Iniciar combate com apenas 1 herói sobrevivente (2 heróis já mortos) | O tabuleiro deve instanciar apenas o herói sobrevivente na célula central de deploy e omitir os heróis caídos sem disparar null pointers. |
| 7 | M4: Combate | Dano letal simultâneo matando todos os heróis no mesmo turno | O `RunState` detecta `get_living_heroes().is_empty()` no handler de morte e aciona `status = Status.DEFEAT` e `run_ended(false)`. |
| 8 | M4: Combate | Retorno ao mapa após combate sem sobreviventes | O jogo não deve permitir navegar para novos nós; a tela de derrota deve sobrepor o mapa bloqueando cliques. |
| 9 | M5: Ato II | Herói entra em célula de escuridão sem tochas adjacentes | O movimento é permitido, mas ataques à distância sofrem desvantagem ou são bloqueados e nenhuma criatura oculta é revelada. |
| 10 | M5: Ato II | Casulo de quitina atacado por dano que não o destrói (ex: 14 de 15 PV) | O casulo continua sua contagem regressiva normalmente; o dano persiste até ser destruído ou atingir a rodada 0. |
| 11 | M5: Ato II | Dois casulos eclodem na mesma rodada com células de spawn limitadas | Cada casulo seleciona a célula livre adjacente mais próxima via BFS; se não houver células livres, o inseto nasce na célula do próprio casulo. |
| 12 | M5: Ato II | Cigarra Ressonante atinge apenas 1 herói isolado com o pulso sônico | Causa o dano normal de 2d6, mas o teste de resistência contra `stunned` é anulado (o atordoamento em área exige 2+ heróis agrupados). |
| 13 | M6: Ato III | Jogador destrói os 3 Corações da Colmeia na mesma run | O Rei Isectum entra na Fase 1 sem Comando Absoluto na rodada 1, com CA 16 em vez de 19, e sem guardas de reforço na Fase 2. |
| 14 | M6: Ato III | Jogador não visita nenhum nó de Coração e vai direto ao Boss Final | O Rei Isectum luta em sua potência máxima (CA 19, guardas ativos, comando ativo), mas a vitória dobra o Âmbar Real ganho. |
| 15 | M6: Boss Final | Ataque de deslocamento/empurrão aplicado contra o Rei Isectum (3×3) | O deslocamento é totalmente anulado (`imune a empurrões`); o dano do ataque é aplicado normalmente. |
| 16 | M6: Boss Final | Heróis destroem os 4 pilares do Trono de Âmbar antes do Rei sofrer 150 de dano | O Trono desaba imediatamente; o Rei sofre dano de queda (ex: 20 PV) e transiciona compulsoriamente para o chão da arena. |
| 17 | M6: Boss Final | Unidade de herói ou inseto ocupa uma das células onde o miasma da Fase 2 avançou | A unidade sofre 10 de dano ácido no início de seu turno e recebe a condição `corrosao` até se mover para o centro seguro. |
| 18 | M6: Boss Final | Herói a 0 PV é curado ou estabilizado antes da ação do Rei na Fase 3 | A habilidade `devorar_essencia` perde o alvo válido; o Rei redireciona sua ação para um ataque Melee padrão contra o herói mais próximo. |
| 19 | M7: Meta | Arquivo `user://meta_save.json` corrompido ou ausente no carregamento | O sistema deve criar um novo arquivo com valores padrão seguros (`royal_amber = 0`, 3 heróis iniciais liberados) e salvar sem crash. |
| 20 | M8: Ascensão | Jogador seleciona Ascensão 10 sem ter vencido as Ascensões anteriores | A UI desabilita a seleção de níveis não desbloqueados, permitindo escolher apenas até `highest_ascension_unlocked + 1`. |

---

## 4. Caveats

- **Ambiente de Execução Sandbox**: Durante a sondagem, comandos externos no terminal sofreram reset de conexão pelo sandbox do ambiente; no entanto, todas as inspeções de código-fonte, dados JSON, diagramas de arquitetura e arquivos de especificação foram realizadas de maneira direta e exaustiva via `view_file`, `list_dir` e `grep_search`.
- **Escopo Read-Only**: Por ser uma tarefa estrita de Spec Miner, nenhum código de produção ou de teste foi alterado nesta etapa. Toda a mineração está documentada para orientar a decomposição e implementação pelos agentes executores.
- **Mapeamento Gráfico do Rei Isectum**: Embora todas as 24 castas Isectum possuam arquivos `.png` dedicados em `godot_project/assets/images/characters/monsters/isectum/`, o Rei Isectum (por ser uma entidade nova de 3x3 tiles desenhada no design de M6) precisará ser renderizado por sprite ampliado de alta resolução (ou recorte de `enxame_rainha` / textura âmbar procedural de 3x3) na implementação de M6.

---

## 5. Conclusion

1. **Prontidão de M3**: A estrutura de dados de `RunState` já aceita relíquias e cartas. A implementação necessita criar a UI do Modal de Recompensas (`RewardModal`), o painel da Forja Anã (`ForgeModal`) e o singleton/controlador `RelicManager` integrado ao `EventBus`.
2. **Prontidão de M4**: O ponto de integração está delimitado no `RunNodeResolver.resolve_combat()` e `RunMapScreen._on_node_pressed()`. O combate tático deve carregar `Main.tscn` / `CercoGameController`, vincular o PV persistente de `RunState` e gerenciar permadeath estrito.
3. **Prontidão de M5**: O Ato II requer iluminação de tochas no `TacticalGrid` (raio de 3 células), entidade destrutível de casulos/ovos (15 PV, 3 turnos), a casta de elite `cigarra_ressonante` (onda sônica DC 13 Con) e o chefe `rainha_do_enxame` (invocação de ninhada a cada 2 turnos e proteção por guardas adjacentes).
4. **Prontidão de M6**: O Ato III requer os 3 nós de Coração (`fase_09`, `fase_10`, `fase_11`) conectando flags de enfraquecimento ao `RunState`, e a máquina de 3 fases do Boss Final `rei_isectum` (3x3 tiles, 450 PV, pilares de escavação, miasma ácido dinâmico, fraqueza 2x a fogo na Fase 3 e mecânica de Devorar Essência).
5. **Prontidão de M7 & M8**: Meta-progressão persistente em `user://meta_save.json`, Quartel dos Heróis com os 8 personagens de `dados/personagens.json`, cartas rúnicas desbloqueáveis, sistema de Ascensão 1-10 cumulativo e telas finais de estatísticas.

---

## 6. Verification Method

Para verificar independentemente a exatidão e consistência desta especificação:

1. **Inspeção de Documentos Oficiais**:
   - `CAMPANHA_ROGUELIKE.md`: Seções 1 a 7 confirmam todas as fórmulas, pesos de nós, regras dos 3 Atos e ficha do Rei Isectum.
   - `ORIGINAL_REQUEST.md`: Requisitos R1 a R5 mapeados um-a-um para os marcos M3 a M8.

2. **Inspeção de Contratos e Classes Existentes**:
   - `RunState.gd`: Conferir linhas 16–28 e 156–232 para as fórmulas de ouro, dano persistente e cálculo de Âmbar (`floors_cleared * 1 + bosses_defeated * 10 + 25`).
   - `IsectumCastes.gd`: Conferir linhas 35–83 para as 24 castas e apelidos.
   - `DataManager.gd`: Conferir linhas 7–10 para os 11 heróis canônicos.
   - `EventBus.gd`: Conferir linhas 8–71 para os sinais de combate tático necessários para o `RelicManager`.
   - `TacticalGrid.gd`: Conferir linhas 31–43 para tipos de terreno, cobertura (+2/+5 CA) e linhas 204–218 para perigos de veneno e fogo.

3. **Validação de Testes GUT**:
   - Executar quando o sandbox estiver pronto: `bash godot_project/run_gut_tests.sh` para confirmar que a suíte base de 729 testes permanece 100% verde.
