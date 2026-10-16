# Handoff Report — Codebase Architecture Survey (M3 to M8)

**Agent**: `explorer_survey_1` (Codebase Architecture Explorer)  
**Date**: 2026-10-16  
**Target Milestone**: Survey Phase for M3-M8 Roguelike Tactical Campaign  

---

## 1. Observation

Direct code inspections, file verifications, and tool executions yielded the following verified facts:

### 1.1 Test Suite Baseline
- Executed `bash godot_project/run_gut_tests.sh` with Godot 4 headless runner.
- **Result**: 31 test scripts executed, **729 tests run, 729 passed, 0 failed, 6489 assertions passed** (Exit code: 0).
- The existing codebase is stable, regression-free, and thoroughly covered by GUT unit tests.

### 1.2 Run Architecture (`godot_project/scripts/run/`)
1. **`RunNode.gd`**:
   - `enum NodeType { COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS }` (lines 8).
   - Data-only `RefCounted` model containing `id`, `act`, `floor_index`, `column`, `type`, `next_ids: Array[int]`, `visited: bool`.
   - Serialization: `to_dict()` (lines 64-73) and `from_dict(data: Dictionary) -> RunNode` (lines 75-82).
   - Helper methods: `is_boss()`, `is_combat_type()` (returns true for COMBAT, ELITE, SIEGE, BOSS).

2. **`RunMap.gd`**:
   - Graph structure with `nodes: Array[RunNode]` and `_index: Dictionary`.
   - Node retrieval by floor: `get_nodes_on_floor(floor_idx: int)`.
   - BFS path validator: `can_reach_boss(node_id: int) -> bool` (lines 62-76), guaranteeing reachability of the boss on the final floor.
   - Serialization: `to_dict()` and `from_dict()`.

3. **`RunMapGenerator.gd`**:
   - Procedural generation parameterized by `total_floors` (default 12), `columns` (4), `start_paths` (3).
   - Anti-edge-crossing algorithm ensures clean planar graphs.
   - Floor layout: Floor 0 has start nodes (COMBAT); penultimate floor has guaranteed CAMPFIRE; final floor has single centered BOSS node.

4. **`RunState.gd`**:
   - Core run state machine (`RefCounted`).
   - Party limits: `const MAX_PARTY_SIZE: int = 3` (line 17), `const FINAL_ACT: int = 3` (line 16), `const STARTING_GOLD: int = 50` (line 18).
   - Act Boss mapping (lines 24-28):
     ```gdscript
     const ACT_BOSSES: Dictionary = {
         1: "viuva_canibal",
         2: "rainha_do_enxame",
         3: "rei_isectum",
     }
     ```
   - Hero HP & Permadeath (lines 145-186):
     - `heroes: Array[String]`, `hero_hp: Dictionary`, `hero_max_hp: Dictionary`, `fallen_heroes: Array[String]`.
     - `damage_hero(hero_id, amount)`: if HP reaches 0, hero is added to `fallen_heroes`, emits `hero_died(hero_id)`. If `get_living_heroes().is_empty()`, triggers `Status.DEFEAT` and emits `run_ended(false)`.
     - `heal_hero(hero_id, amount)`: explicitly refuses to heal fallen heroes (`not is_hero_alive(hero_id)`), enforcing permadeath.
     - `heal_party_percent(pct)`: heals all living heroes by percentage of their `max_hp`.
   - Deck, Gold & Relics (lines 188-222):
     - `deck: Array[String]`, `relics: Array[String]`, `gold: int`.
     - `add_card(card_id)`, `remove_card(card_id)`.
     - `add_relic(relic_id)` (prevents duplicate relics), `has_relic(relic_id)`.
   - Meta-progression currency (lines 227-232):
     - `calculate_amber() -> int`: `floors_cleared * 1 + bosses_defeated * 10 + (25 if victory else 0)`.
   - Act transition: `_on_boss_defeated()` (lines 131-142): if `act >= FINAL_ACT`, victory; otherwise `act += 1`, `heal_party_percent(0.25)`, generates new `map` for the new Act, emits `act_advanced(act)`.

5. **`RunSession.gd`**:
   - Lightweight static singleton container (`RefCounted`) with `static var current: RunState = null`.
   - `DEFAULT_PARTY = {"aquele": 30, "stark": 34, "elden": 26}`.
   - `DEFAULT_DECK = ["movimento", "movimento", "movimento", "trabalho", "trabalho", "escavacao", "escavacao", "ataque", "ataque", "defesa"]`.
   - Provides `start_new(p_seed, party, deck) -> RunState`, `has_active_run() -> bool`, `clear()`.

6. **`RunNodeResolver.gd`**:
   - Current implementation is an MVP placeholder (lines 35-45):
     - `CAMPFIRE`: `state.heal_party_percent(0.30)`.
     - `FORGE`: logs "Forja anã: o mercado abrirá no próximo marco (M3)."
     - `EVENT`: 50% chance +20 gold, 50% chance 5 damage to a random hero.
     - `COMBAT / ELITE / SIEGE / BOSS`: `resolve_combat()` rolls random damage from `COMBAT_TABLE` and applies directly to a living hero, awards gold and kills, awards relic on ELITE.
   - Comments explicitly state (lines 5-8):
     `"No marco M4, uma subclasse/estratégia que abre o combate tático real substituirá resolve_combat() — por isso o resolver é injetado no RunMapScreen."`

7. **`RunMapScreen.gd` & `RunMapScreen.tscn`**:
   - Scene hierarchy: `Header` (title, Act label, Boss name, gold, deck size, amber, `HeroesContainer`), `Scroll/MapCanvas` (`RunMapCanvas.gd` drawing edges and button nodes), `Footer/LogBox`.
   - Button styling: active nodes highlighted in gold, visited in muted slate, available in type color.
   - On node click (`_on_node_pressed` lines 280-302): calls `state.move_to(node_id)`, invokes `resolver.resolve(state, rng)`, prints outcome to log, refreshes UI.
   - Signals: `node_selected(node: RunNode)`, `run_finished(victory: bool)`.

### 1.3 Combat Systems & Board Architectures
1. **`Main.tscn` & `CercoGameController.gd`**:
   - `Main.tscn` has root `Node2D` with `CercoGameController.gd` and child `HUD.tscn`.
   - `CercoGameController.gd` (1034 lines):
     - Models: `board = FortressBoard.new()`, `economy = WorkshopEconomy.new()`, `deck = CercoDeck.new()`, `judge = CercoCombatJudge.new()`, `sync_round = CercoSyncRound.new()`, `threat_deck = ThreatDeck.new()`.
     - Connects models to `HUD.gd` (`hud_instance.bind_board(board)`, `bind_economy`, `bind_deck`, `bind_judge`, `bind_sync_round`).
     - Spawns heroes (`aquele`, `stark`, `lysander`) in central chamber and courtyard.
     - Spawns waves via `threat_deck.generate_wave(wave_num)` or fallback caste dictionary.
     - Game over checking in `check_game_over_conditions()` (lines 906-953):
       - Defeat 1: All allied heroes dead (`living_heroes.is_empty()`).
       - Defeat 2: 3 or more invaders enter `CAMARA_CENTRAL`.
       - Victory: Survived `max_rounds` and eliminated all living enemies.
     - On game over: calls `trigger_game_over(victory, reason)`, shows `GameOverModal.tscn`.

2. **`FortressBoard.gd` & `FortressBoardView.gd`**:
   - 20x20 discrete board representing 17 canonical zones:
     - 1 Central Core (`CAMARA_CENTRAL`)
     - 4 Interior workshops/courtyard (`CARPINTARIA`, `CURTUME`, `FUNDICAO`, `PATIO_CENTRAL`)
     - 4 Perimeter walls (`MURALHA_NORTE`, `SUL`, `LESTE`, `OESTE`)
     - 4 Watchtowers (`TORRE_NOROESTE`, `NORDESTE`, `SUDOESTE`, `SUDESTE`)
     - 4 Outer spawn zones (`SPAWN_NORTE`, `SUL`, `LESTE`, `OESTE`)
   - `FortressBoardView.gd` renders tiles, units, HP bars, movement ranges (blue), attack ranges (red), animations, impact particles, and item drops (crystals, chests, potions).

3. **`TacticalGrid.gd`**:
   - Standalone 20x20 grid with terrain constants: `NORMAL`, `FLORESTA`, `DIFICIL`, `PAREDE`, `GELO`, `FOGO`, `AGUA`, `ROCHA`, `BARRIL`, `VENENO`.
   - D&D 5e Cover rules: +2 (soft creature cover), +3 (light adjacent forest/barrel), +5 (three-quarters rock/wall), 1000 (total cover).
   - Pathfinding: AStar2D supporting Chebyshev (D&D 5e standard), Euclidean, and Manhattan metrics.
   - Line of sight: Bresenham raycasting with cover calculation.

4. **`IsectumCastes.gd`**:
   - Canonical catalog of 24 Isectum castes with stats (`hp`, `ac`, `speed`, `attack_dice`, `attack_range`, `threat_cost`, `traits`, `symbols`).
   - Bosses defined in catalog:
     - `rainha_do_enxame` (HP 8, speed 3, attack 5, range 2, trait `chamado_da_rainha`, `is_boss: true`).
     - `colosso_isectum` (HP 3, brutamontes, speed 1, attack 6, range 2, threat 8, `is_boss: true`).
   - Aliases map `viuva_canibal -> tece_teia`, `cigarra_ressonante -> grilo_atordoante`, `enxame_rainha -> rainha_do_enxame`.
   - `rei_isectum` is referenced in `RunState` and `CAMPANHA_ROGUELIKE.md` as a 3x3 multi-cell boss with 450 HP across 3 phases, but not yet defined in `IsectumCastes.gd`.

5. **`EventBus.gd`**:
   - Autoload singleton with comprehensive signal catalog:
     - Combat: `unit_moved`, `unit_attacked`, `unit_damaged`, `unit_died`, `death_save_rolled`, `status_applied`, `status_removed`, `turn_changed`.
     - Cerco/Cards: `card_selected`, `card_played`, `dice_rolled`, `damage_dealt`, `production_completed`, `wall_breached`, `round_resolved`, `resources_updated`.
     - System: `game_state_changed`, `game_reset`, `audio_play_sfx_requested`, `floating_text_requested`, `combat_log_entry_added`.
     - Built-in telemetry tracking: `emit_logged(sig_name, args)`, `get_emission_count(sig_name)`, `reset_telemetry()`.

6. **`GameManager.gd`**:
   - Central state machine with `GameState`: `MENU` (0), `COMBATE_TATICO` (1), `CERCO_ISECTUM` (2), `FIM_DE_JOGO` (3), `MULTIPLAYER_LOBBY` (4).
   - Routes: `MENU -> res://scenes/main/Menu.tscn`, `COMBATE_TATICO -> res://scenes/main/Main.tscn`, `FIM_DE_JOGO -> res://scenes/main/GameOver.tscn`.
   - Stores `state_payload: Dictionary`.

---

## 2. Logic Chain

From the observations above, the system flow and architectural dependencies lead to the following deductions:

### Step 1: Session Decoupling
- `RunSession.current` holds the active `RunState` across scene switches without requiring an Autoload.
- `RunMapScreen` checks `RunSession.has_active_run()`. When moving to a combat node (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`), instead of executing the placeholder `resolver.resolve_combat()` inline, the application must transition to the combat arena (`Main.tscn`) while keeping `RunSession.current` active.

### Step 2: Combat Initialization from RunState
- When `Main.tscn` (`CercoGameController`) initializes:
  - It must check `if RunSession.has_active_run():`.
  - If a run is active, instead of loading the default 3 heroes (`aquele`, `stark`, `lysander`) with static HP:
    1. Retrieve `RunSession.current.heroes` and filter by `RunSession.current.get_living_heroes()`.
    2. Fallen heroes (`RunSession.current.fallen_heroes`) must NOT be placed on the board (*Permadeath*).
    3. Place surviving heroes on the grid with `hp = RunSession.current.hero_hp[h]` and `max_hp = RunSession.current.hero_max_hp[h]`.
    4. Deck: initialize `deck` from `RunSession.current.deck`.
    5. Enemy composition: determine encounter based on `RunSession.current.act`, current node type (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`), and node floor.
       - Act 1: Tier 1 castes; Boss = Viúva Canibal (`viuva_canibal`).
       - Act 2: Tier 2 castes; Elite = Cigarra Ressonante (`cigarra_ressonante`); Boss = Rainha do Enxame (`rainha_do_enxame`).
       - Act 3: Tier 3 castes; Special Elites = Hive Hearts (`fase_09`, `fase_10`, `fase_11`); Final Boss = Rei Isectum 3x3 (`rei_isectum`).

### Step 3: Combat Termination & State Writeback
- When battle concludes in `CercoGameController`:
  - **Hero HP sync**: For each hero on the board, update `RunSession.current.hero_hp[hero_id] = unit.hp`.
    - If `unit.hp <= 0`, call `RunSession.current.damage_hero(hero_id, 999)` to record death in `fallen_heroes`.
  - **Defeat condition**: If all heroes are dead (`RunSession.current.get_living_heroes().is_empty()`):
    - `RunSession.current.status = RunState.Status.DEFEAT`
    - Calculate Amber: `amber = RunSession.current.calculate_amber()`
    - Add amber to persistent disk meta-progression (`user://meta_save.json`).
    - Transition to `GameOver.tscn` passing run statistics.
  - **Victory condition**:
    - Add gold from encounter to `RunSession.current.add_gold(...)`.
    - Register kills in `RunSession.current.register_kills(...)`.
    - If `ELITE` node: grant guaranteed relic to `RunSession.current.add_relic(...)`.
    - Open M3 Reward Modal: "Choose 1 of 3 Cards".
    - Player selects card -> appended to `RunSession.current.add_card(...)`.
    - Mark node complete: `RunSession.current.complete_current_node()`.
    - Transition back to `res://scenes/run/RunMapScreen.tscn`.

### Step 4: Separation of Concerns for Milestones M3-M8
- **M3**: UI Modals and pure logic components (`RewardModal`, `ForgeScreen`, `RelicManager`). Can be tested in isolation with mock `RunState` and mock `EventBus`.
- **M4**: Scene router and state synchronization bridge (`RunCombatBridge` / `TacticalCombatResolver`). Connects `RunMapScreen` to `Main.tscn` and handles round-trip state persistence.
- **M5**: Environment and enemy extensions (Torch lighting, Casulos de quitina, Cigarra Ressonante, Rainha do Enxame).
- **M6**: Multi-cell 3x3 entity and 3-phase FSM boss (`rei_isectum`), plus Hive Heart tracking flags in `RunState`.
- **M7**: Disk persistence (`MetaSaveManager`), barracks hero unlock UI, rune card unlocks.
- **M8**: Ascension modifiers (1..10) scaling enemy stats and restrictions, epilogue screens.

---

## 3. Caveats

1. **Standalone Cerco Mode vs Roguelike Campaign**:
   - `CercoGameController.gd` is currently used by "JOGAR CERCO" from the Main Menu. The integration must preserve standalone Cerco functionality when `RunSession.has_active_run()` is false.
2. **`FortressBoard.tscn` vs `Main.tscn`**:
   - `GameManager.gd` contains `SCENE_ROUTES[GameState.CERCO_ISECTUM] = "res://scenes/cerco/FortressBoard.tscn"`, but `FortressBoard.tscn` does not exist on disk — `Main.tscn` is the actual combat scene containing `FortressBoardView`. `SCENE_ROUTES` in `GameManager` should be updated or aliased to `Main.tscn`.
3. **Multi-cell 3x3 Unit Footprint**:
   - Current `FortressBoard` and `TacticalGrid` primarily track units as occupying a single `Vector2i` cell (`_units_grid[y][x]`). Supporting a 3x3 boss (`rei_isectum`) in M6 requires either registering 9 occupied cells in the board model or an adapter that checks a 3x3 bounding box for collisions, line of sight, and targeting.

---

## 4. Conclusion & Proposed Architecture (M3 through M8)

The codebase has clean, modular foundations ready for M3 through M8. Below is the concrete specification for each milestone:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MAIN MENU / BARRACKS                            │
│  - MetaSaveManager (user://meta_save.json)                             │
│  - Spend Real Amber (💎) to unlock heroes & rune cards (M7)             │
│  - Select Ascension Level 1-10 (M8)                                    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ "Nova Campanha"
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        RUN MAP SCREEN                                  │
│  - RunSession.current (RunState)                                       │
│  - Persistent Hero HP Bars & Permadeath (💀)                           │
│  - Graph: COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS           │
└───────┬──────────────────────────┬──────────────────────────────┬──────┘
        │ CAMPFIRE / EVENT         │ FORGE                        │ COMBAT / ELITE /
        ▼                          ▼                              │ SIEGE / BOSS
┌──────────────────┐     ┌──────────────────────┐                 ▼
│ Auto-resolve     │     │ ForgeScreen (M3)     │      ┌───────────────────────┐
│ Heal 30% / Gold  │     │ - Buy Cards (Gold)   │      │ RunCombatBridge (M4)  │
└──────────────────┘     │ - Buy Relics (Gold)  │      │ - Ingest RunState HP  │
                         │ - Purge Deck Card    │      │ - Spawn Act Enemies   │
                         └──────────────────────┘      └──────────┬────────────┘
                                                                  ▼
                                                       ┌───────────────────────┐
                                                       │ TACTICAL COMBAT ARENA │
                                                       │ Main.tscn / BoardView │
                                                       │ - Act 1: Spider Web   │
                                                       │ - Act 2: Torches (M5) │
                                                       │ - Act 3: King 3x3(M6) │
                                                       └──────────┬────────────┘
                                                                  │
                                    ┌─────────────────────────────┴─────────────────────────────┐
                                    ▼ Victory                                                   ▼ Defeat (Party Wiped)
                         ┌──────────────────────┐                                    ┌──────────────────────┐
                         │ RewardModal (M3)     │                                    │ GameOverScene (M7)   │
                         │ - Pick 1 of 3 Cards  │                                    │ - Tally Real Amber   │
                         │ - Relic (if Elite)   │                                    │ - Save to Disk       │
                         └──────────┬───────────┘                                    └──────────────────────┘
                                    │
                                    ▼
                         Return to RunMapScreen
```

### 4.1 Milestone M3: Post-Combat Rewards, Forge & Relics System

#### Proposed Files:
1. `godot_project/scripts/run/relics/RelicData.gd` (`RefCounted`):
   - Attributes: `id: String`, `name: String`, `description: String`, `icon: String`, `rarity: int`, `gold_cost: int`.
   - Virtual hook methods:
     - `on_attack_dealt(attacker_id, target_id, damage, event_bus) -> int`
     - `on_damage_received(target_id, amount, event_bus) -> int`
     - `on_turn_started(turn_number, event_bus)`
     - `on_combat_victory(run_state) -> void`
     - `on_campfire_rest(heal_bonus_pct) -> float`

2. `godot_project/scripts/run/relics/RelicManager.gd` (`RefCounted`):
   - Manages active relics in `RunState.relics`.
   - Subscribes to `EventBus` signals (`unit_attacked`, `unit_damaged`, `round_resolved`, etc.).
   - Dispatches events to active `RelicData` instances.
   - Initial relic catalog (8 passives):
     - `gorgulho_horn`: +2 flat damage on physical attacks.
     - `chitin_carapace`: +1 AC to all heroes.
     - `miners_pouch`: +10 gold upon clearing any node.
     - `karak_balm`: Campfire heals +15% extra HP (45% total).
     - `torch_tallow`: Increases vision radius by 2 tiles in dark tunnels (Ato II).
     - `amber_lens`: 20% chance to obtain +1 extra Real Amber per combat.
     - `spiked_shield`: When taking damage, deal 2 reflective damage to attacker.
     - `anointed_oil`: Weapon attacks deal +2 fire damage.

3. `godot_project/scripts/run/ui/RewardModal.gd` & `RewardModal.tscn`:
   - Modal overlay that appears over combat or map upon victory.
   - Displays 3 CardUI cards generated randomly based on current Act and hero classes.
   - Buttons: "Escolher Carta", "Pular Recompensa".
   - Shows gold awarded and relics gained (if Elite/Boss).

4. `godot_project/scripts/run/ui/ForgeScreen.gd` & `ForgeScreen.tscn`:
   - Interactive screen for the `FORGE` node.
   - Section 1: "Comprar Cartas" (3 cards from pool, costs 30-60 gold).
   - Section 2: "Comprar Relíquias" (2 random relics, costs 80-150 gold).
   - Section 3: "Purificar Deck" (Remove 1 selected card from deck, costs 50 gold + 25 per prior removal).

---

### 4.2 Milestone M4: Full Tactical Combat Integration into Run Map (Act I)

#### Proposed Files:
1. `godot_project/scripts/run/RunCombatBridge.gd` (`RefCounted` or Node):
   - Ingests `RunSession.current`.
   - Encapsulates battle setup config:
     - `hero_party`: Array of living hero IDs with their current `RunState.hero_hp`.
     - `encounter_type`: `COMBAT`, `ELITE`, `SIEGE`, `BOSS`.
     - `encounter_def`: Generates enemy group matching Act 1 floor progression:
       - Low floors (0-2): 3-4 Tier 1 insects (`larva_carniceira`, `formiga_acida`).
       - Mid floors (3-6): Mixed squad (`besouro_gorgulho`, `gafanhoto_praga`, `formiga_acida`).
       - Elite floors: Mini-boss / heavy insect (`escaravelho_couracado` or `tarantula_golias`).
       - Boss floor (Andar 11): `viuva_canibal` with web trap tiles and feeding mechanics.
   - Configures `CercoGameController` to initialize from `RunCombatBridge` data.
   - Subscribes to combat finish:
     - Updates `RunState.hero_hp` with surviving HP.
     - Records deaths in `RunState.fallen_heroes`.
     - Awards gold and kills.
     - Routes to `RewardModal` -> `RunMapScreen`.

2. Adaptation in `RunMapScreen.gd`:
   - When a combat-type node (`COMBAT`, `ELITE`, `SIEGE`, `BOSS`) is clicked:
     - Save current node position.
     - Set `GameManager.state_payload = {"from_run": true, "node": target_node}`.
     - Call `get_tree().change_scene_to_file("res://scenes/main/Main.tscn")`.

---

### 4.3 Milestone M5: Act II Content & Mechanics (Túneis Vivos)

#### Proposed Files:
1. `godot_project/scripts/tactical/TorchLighting.gd`:
   - Dynamic visibility system around hero units (radius 3-4 tiles).
   - Enemies outside torchlight are shrouded (modulate darkened, cannot be targeted by ranged attacks).
2. `godot_project/scripts/entities/ChitinCocoon.gd`:
   - Grid obstacle with 15 HP.
   - Turn counter: after 3 rounds, hatches into a random Tier 2 insect (`louva_deus_ceifador`, `vespa_furtiva`).
3. Mini-Boss `cigarra_ressonante`:
   - High mobility flyer.
   - Ability `pulso_sonico`: AoE cone dealing sound damage and applying `atordoado` (stun) to heroes within 2 tiles of each other.
4. Boss `rainha_do_enxame`:
   - Ability `chamado_da_rainha`: Every 2 turns, spawns 2 brood minions at map edges.
   - Guarded by 2 `soldado_mandibula`.

---

### 4.4 Milestone M6: Act III Content & King Isectum Final Boss

#### Proposed Files:
1. `godot_project/scripts/run/HiveHeartsTracker.gd`:
   - Tracks destruction of the 3 hearts in `RunState`:
     - `heart_mind_destroyed: bool` (`fase_09`)
     - `heart_carapace_destroyed: bool` (`fase_10`)
     - `heart_brood_destroyed: bool` (`fase_11`)
2. `godot_project/scripts/entities/bosses/ReiIsectumBoss.gd`:
   - 3x3 multi-cell entity occupying 9 tiles on the `TacticalGrid` / `FortressBoard`.
   - Total HP: 450 (150 per phase).
   - Base AC: 19 (reduced to 16 if `heart_carapace_destroyed`).
   - Phase 1 (450 -> 300 HP): "O Soberano no Trono"
     - Elevated throne: King immune to melee from floor level.
     - Pillars can be attacked with *Escavação* cards (30 HP each). When pillars fall, throne collapses.
     - Mental Control ordered attacks (disabled if `heart_mind_destroyed`).
   - Phase 2 (300 -> 150 HP): "A Muralha Viva"
     - Descends to arena floor; screen shake effect.
     - Acid miasma encroaches from grid borders by 1 tile every 2 rounds.
     - Pheromone Roar (cone AoE inflicting Fear).
     - Spawns Royal Guard (disabled if `heart_brood_destroyed`).
   - Phase 3 (150 -> 0 HP): "Coroa Quebrada"
     - AC reduced by -3.
     - Double actions per round (frenzy).
     - Weakness: 2x damage from Fire (`CombatRules.DAMAGE_TYPES.fogo`).
     - Lethal skill: "Devorar Essência" targeting adjacent fallen heroes at 0 HP.

---

### 4.5 Milestone M7: Permanent Meta-Progression & Barracks

#### Proposed Files:
1. `godot_project/scripts/run/meta/MetaSaveManager.gd`:
   - Disk file: `user://meta_save.json`.
   - Schema:
     ```json
     {
       "real_amber": 140,
       "total_runs": 12,
       "victories": 1,
       "unlocked_heroes": ["aquele", "stark", "elden", "doom", "gruu"],
       "unlocked_cards": ["runa_haste", "escudo_quitina"],
       "highest_ascension": 1,
       "codex_discovered_castes": ["zangao_invasor", "soldado_mandibula", "viuva_canibal"]
     }
     ```
   - Safe file operations with error handling and backup fallback.
2. `godot_project/scenes/run/BarracksScreen.tscn` & `BarracksScreen.gd`:
   - Screen accessible from Menu ("QUARTEL / DESBLOQUEIOS").
   - Spend Real Amber (💎) to unlock the remaining 8 heroes (`dados/personagens.json`).
   - Codex tab displaying the 24 Isectum castes and their recorded stats.

---

### 4.6 Milestone M8: Ascension System & Final Epilogue

#### Proposed Files:
1. `godot_project/scripts/run/meta/AscensionModifiers.gd`:
   - Levels 1 to 10 with cumulative multipliers:
     - Level 1: Enemies +15% HP.
     - Level 2: Elites gain +1 extra attack dice.
     - Level 3: Campfires heal only 20% HP (down from 30%).
     - Level 4: Market prices +25% gold.
     - Level 5: Bosses gain +2 AC.
     - Level 10: King Isectum acts 3 times in Phase 3; fire weakness reduced to 1.5x.
2. Victory & Defeat Epilogue Modals:
   - Detailed breakdown: Floors cleared, enemies defeated, cards acquired, relics held, total amber earned.

---

## 5. Verification Method

To independently verify the facts and architecture documented in this report:

1. **GUT Test Suite Execution**:
   - Run command from repository root:
     ```bash
     bash godot_project/run_gut_tests.sh
     ```
   - Verification criteria: All 31 test scripts execute and pass 100% (729/729 tests) with exit code 0.

2. **Inspect Existing Run State Machine & Resolver**:
   - Check `godot_project/scripts/run/RunState.gd` lines 24-28 (Act bosses), lines 145-186 (hero damage, permadeath, healing), and lines 227-232 (amber calculation).
   - Check `godot_project/scripts/run/RunNodeResolver.gd` lines 5-8 (M4 extension hook documentation) and lines 53-72 (`resolve_combat` placeholder).

3. **Inspect Main Scene & Board View**:
   - Check `godot_project/scenes/main/Main.tscn` (binds `CercoGameController.gd` and `HUD.tscn`).
   - Check `godot_project/scripts/main/CercoGameController.gd` lines 32-88 (`_initialize_models()`) and lines 906-953 (`check_game_over_conditions()`).

4. **Invalidation Conditions**:
   - If any GUT test fails, the baseline is broken and must be reconciled before implementing M3-M8.
   - If `RunState.from_dict()` fails roundtrip serialization with new fields (e.g. relics, hearts), the run persistence contract is broken.
