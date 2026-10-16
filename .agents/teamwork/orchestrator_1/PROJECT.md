# Project: Tactical Roguelike Campaign (M3-M8)

## Architecture
- **Language / Engine**: Godot 4.7+ (GDScript 2.0, headless capable)
- **Architecture**: Decoupled Event-Driven & Model-View-Controller.
  - `RunState` and `RunSession` manage persistent expedition data (HP, deck, gold, relics, hearts, amber).
  - `EventBus` facilitates loose coupling across subsystems (Relic hooks, combat events, UI modals).
  - `TacticalGrid` and `FortressBoard` handle 20x20 combat physics, line of sight, cover, and entities.
  - `MetaSaveManager` provides atomic disk persistence for permanent progression (`user://meta_save.json`).
  - Strict GUT test coverage (AAA format, deterministic RNG seeds, zero leaks).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Modal "Escolha 1 de 3 Cartas" | Modal pós-combate apresentando 3 cartas aleatórias para draft | M3 | survey |
| 2 | Opção de Skip ("Pular") | Recusar adicionar cartas mantendo o deck enxuto | M3 | survey |
| 3 | Coleta de Ouro do Nó | Concessão de ouro baseada no tipo de nó | M3 | survey |
| 4 | Gerenciador de Relíquias | Subsistema que escuta sinais do EventBus e ativa efeitos passivos | M3 | survey |
| 5 | Catálogo Canônico de Relíquias | Catálogo de 10 relíquias com efeitos táticos e econômicos | M3 | survey |
| 6 | Mercado da Forja Anã | Tela de compras do nó FORGE (cartas, relíquias) | M3 | survey |
| 7 | Remoção de Cartas do Deck | Serviço de remoção de cartas com custo progressivo de ouro | M3 | survey |
| 8 | Integração Nó ao Tabuleiro | Transição de nós COMBAT/ELITE/SIEGE/BOSS para arena Main.tscn | M4 | survey |
| 9 | Geração de Encontros por Ato | Composição de inimigos conforme Ato e andar via IsectumCastes | M4 | survey |
| 10 | Persistência Contínua de PV | Dano e cura no combate sincronizam bidirecionalmente com RunState | M4 | survey |
| 11 | Morte Permanente (Permadeath) | Heróis a 0 PV entram em fallen_heroes e não entram em futuros combates | M4 | survey |
| 12 | Fim de Expedição (Derrota/Vitória) | Derrota se todo o grupo morrer; avanço de Ato ao bater chefes | M4 | survey |
| 13 | Iluminação de Tochas | Visibilidade em raio de 3 células nos túneis do Ato II | M5 | survey |
| 14 | Casulos de Quitina e Ovos | Obstáculos com 15 PV e 3 turnos para eclosão em insetos Tier 2 | M5 | survey |
| 15 | Mini-Chefe Cigarra Ressonante | Elite voador com pulso sônico em área aplicando atordoamento | M5 | survey |
| 16 | Chefe Rainha do Enxame | Invocação periódica de ninhada e resistência por guardas reais | M5 | survey |
| 17 | Nós dos 3 Corações | Encontros especiais (fase_09, 10, 11) que aplicam debuffs no Rei | M6 | survey |
| 18 | Penalidade Coração da Mente | Suprime ataque fora de turno do Rei na rodada 1 | M6 | survey |
| 19 | Penalidade Coração da Carapaça | Reduz CA do Rei Isectum de 19 para 16 em todas as fases | M6 | survey |
| 20 | Penalidade Coração da Ninhada | Impede invocação de guardas reais na Fase 2 da batalha final | M6 | survey |
| 21 | Bônus por Pular Corações | Dobra Âmbar Real ganho se o Rei for derrotado sem destruir corações | M6 | survey |
| 22 | Entidade 3x3 Rei Isectum | Chefe multicelular ocupando bloco 3x3 imune a empurrões | M6 | survey |
| 23 | Rei Isectum Fase 1 | Trono de Âmbar, pilares de Escavação (450 -> 300 PV) | M6 | survey |
| 24 | Rei Isectum Fase 2 | Muralha Viva, miasma dinâmico e rugido feromônico (300 -> 150 PV) | M6 | survey |
| 25 | Rei Isectum Fase 3 | Coroa Quebrada, 2 ações/rodada, fraqueza fogo 2x, Devorar Essência | M6 | survey |
| 26 | Persistência Âmbar Real | Gravação atômica em user://meta_save.json com recuperação de erro | M7 | survey |
| 27 | Quartel dos Heróis | Desbloqueio permanente dos 8 heróis de dados/personagens.json | M7 | survey |
| 28 | Desbloqueio de Cartas Rúnicas | Liberação de cartas rúnicas e avançadas para pool de recompensas | M7 | survey |
| 29 | Níveis de Ascensão (1 a 10) | Modificadores cumulativos de dificuldade desbloqueados após vitória | M8 | survey |
| 30 | Telas de Vitória / Derrota | Estatísticas completas e conversão em Âmbar Real | M8 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M3 | Recompensas, Forja & Relíquias | RelicData, RelicManager, RewardModal, ForgeScreen, GUT tests | Baseline GUT passing | IN_PROGRESS |
| M4 | Integração Nó-Combate & Permadeath | RunCombatBridge, CercoGameController run integration, HP sync, permadeath | M3 | PLANNED |
| M5 | Conteúdo Ato II (Túneis Vivos) | TorchLighting, ChitinCocoon, Cigarra Ressonante, Rainha do Enxame | M4 | PLANNED |
| M6 | 3 Corações & Boss Rei Isectum 3x3 | HiveHeartsTracker, ReiIsectumBoss 3x3 FSM 3 fases | M5 | PLANNED |
| M7 & M8 | Meta-Progressão & Ascensão | MetaSaveManager, BarracksScreen, AscensionModifiers, Victory/Defeat | M6 | PLANNED |

## Interface Contracts
### RunState ↔ RelicManager (M3)
- `RunState.relics: Array[String]`
- `RelicManager.register_relic(relic_id: String) -> void`
- `RelicManager.unregister_all() -> void`
- `RelicData.on_attack_dealt(...)`, `on_damage_received(...)`, `on_turn_started(...)`, `on_combat_victory(...)`

### RunState ↔ RunCombatBridge (M4)
- `RunCombatBridge.setup_combat(run_state: RunState, node: RunNode) -> Dictionary`
- `RunCombatBridge.sync_combat_result(run_state: RunState, result: Dictionary) -> void`
- Emits / updates: `hero_hp`, `fallen_heroes`, `gold`, `status`

### TacticalGrid ↔ TorchLighting (M5)
- `TorchLighting.update_visibility(heroes_positions: Array[Vector2i], grid: TacticalGrid) -> void`
- `TorchLighting.is_cell_lit(cell: Vector2i) -> bool`

### TacticalGrid ↔ ReiIsectumBoss (M6)
- Multi-cell footprint: `top_left: Vector2i`, `size: Vector2i(3, 3)`.
- `ReiIsectumBoss.get_occupied_cells() -> Array[Vector2i]`
- Immune to displacement / push.

### MetaSaveManager ↔ RunState (M7 & M8)
- `MetaSaveManager.load_meta() -> Dictionary`
- `MetaSaveManager.save_meta(data: Dictionary) -> bool`
- `MetaSaveManager.add_amber(amount: int) -> int`
- `MetaSaveManager.unlock_hero(hero_id: String) -> bool`
- `AscensionModifiers.apply_to_run(run_state: RunState, level: int) -> void`

## Code Layout
- `godot_project/scripts/run/relics/` — RelicData.gd, RelicManager.gd
- `godot_project/scripts/run/ui/` — RewardModal.gd, ForgeScreen.gd, BarracksScreen.gd, RunSummaryModal.gd
- `godot_project/scripts/run/combat/` — RunCombatBridge.gd, CombatEncounterGenerator.gd
- `godot_project/scripts/tactical/` — TorchLighting.gd
- `godot_project/scripts/entities/` — ChitinCocoon.gd
- `godot_project/scripts/entities/bosses/` — ReiIsectumBoss.gd, CigarraRessonante.gd, RainhaDoEnxame.gd
- `godot_project/scripts/run/meta/` — MetaSaveManager.gd, AscensionModifiers.gd
- `godot_project/test/unit/` — All unit test suites starting with `test_` and ending with `.gd`
