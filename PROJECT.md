# Project: RPG-battle Godot Engine 4 Migration

## Architecture
- **Engine**: Godot Engine 4.x (Compatibility Renderer, 1280x720 base viewport, 2D mode, WebAssembly + Desktop exportable).
- **Language**: Statically typed GDScript (`@export`, explicit types, class_name declarations, strict typing).
- **Core Design**: Decoupled clean architecture, single responsibility, data-driven (`Custom Resources`), event-driven communication via global `EventBus.gd` singleton.
- **Autoload Singletons**:
  - `GameManager.gd`: Game state machine (`MENU`, `COMBATE_TATICO`, `CERCO_ISECTUM`, `FIM_DE_JOGO`, `MULTIPLAYER_LOBBY`).
  - `EventBus.gd`: Global event dispatcher (`unit_moved`, `damage_dealt`, `card_selected`, `round_resolved`, `turn_changed`, `network_event_received`).
  - `DataManager.gd`: Centralized loader and validator for structured data in `dados/` (`personagens.json`, `fases/`, etc.).
  - `AudioManager.gd`: Global sound and music controller with volume buses and pooling.
- **Testing Architecture**: GUT (Godot Unit Testing) in `godot_project/addons/gut/` and `godot_project/test/`, configured for headless CLI execution (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`).

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Godot 4 Base Project Config | Viewport 1280x720, Compatibility renderer, project.godot, input maps | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Autoload Singletons | GameManager, EventBus, DataManager, AudioManager autoloads | M1 | ORIGINAL_REQUEST §R1 |
| 3 | GUT Framework & Headless Runner | GUT install, .gutconfig.json, CLI runner script, AAA templates | M1 | ORIGINAL_REQUEST §R7 |
| 4 | 20x20 Tactical Grid & Bounds | 20x20 coordinates, border walls, Chebyshev distance, cell types | M2 | ORIGINAL_REQUEST §R2 |
| 5 | AStar2D Pathfinding & Terrain | 8-way diagonal A*, difficult terrain cost 2.0, ice slip 50%, fire hazard | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Destructible Structures | Forest, rock, barrel (20 HP -> difficult terrain on destroy) | M2 | src/tabuleiro.py |
| 7 | Line of Sight & Cover System | Bresenham LoS, soft creature cover (+2), total wall cover (1000), adjacent (+3/+5) | M2 | ORIGINAL_REQUEST §R2 |
| 8 | D&D 5e Combat Math & Advantage | d20 rolls, modifier formulas, advantage/disadvantage cancellation, critical doubling | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Damage Types & Resistances | 14 damage types, vulnerability (2.0x), resistance (0.5x), immunity (0.0x) | M2 | src/config.py |
| 10 | Death Saving Throws FSM | Nat 20 (1 HP), Nat 1 (2 fails), 10+ success, 3 fails (dead), 3 succ (stabilized) | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Status Conditions System | 23 conditions (Poisoned, Stunned, Focus, Bleed, etc.), tick order, mechanical effects | M2 | ORIGINAL_REQUEST §R2 |
| 12 | Character Custom Resource | CharacterData.gd with typed stats, modifiers, perks, abilities | M3 | ORIGINAL_REQUEST §R3 |
| 13 | 11 Playable Heroes & Lysander | Resource files (.tres) for all 11 heroes + Prince Lysander with canonical stats | M3 | ORIGINAL_REQUEST §R3 |
| 14 | Character Scene & Visuals | Character.tscn with Sprite2D/AnimatedSprite2D, retro HP bar, selection highlight | M3 | ORIGINAL_REQUEST §R3 |
| 15 | 24 Isectum Insect Castes | IsectumCaste.gd, 24 active insect behaviors, 6 inverted boss effects, 32x32 sprites | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Cerco Card Custom Resource | CardData.gd (Action, Upgrade, Rune), costs, badges (Movement, Work, Excavation) | M4 | ORIGINAL_REQUEST §R4 |
| 17 | Card Scene & Fan Arc Layout | Card.tscn, interactive hover, fan arc positioning math, badges, gem frames | M4 | ORIGINAL_REQUEST §R4 |
| 18 | Simultaneous Sync Turn Co-op | CercoSyncRound.gd, 4 layers (movement, work, excavation, upgrade), speed advantage | M4 | ORIGINAL_REQUEST §R4 |
| 19 | Synergy Combo System | Team synergy (2+ same type), Supreme Synchrony (all same type -> +2 crystals) | M4 | ORIGINAL_REQUEST §R4 |
| 20 | Fortress Economy & Free Actions | Movement spending, rock excavation (Wood, Metal, Crystal), workshop craft, market | M4 | ORIGINAL_REQUEST §R4 |
| 21 | Cerco Combat Judge Engine | Custom D6 dice (impacts // 2, balestra shots, elevation adv/disadv, Brutamontes) | M4 | src/juiz_combate.py |
| 22 | Dark Fantasy HUD (CanvasLayer) | Top resource bar (Wood, Metal, Crystal, AP), side roster with dynamic HP/status | M5 | ORIGINAL_REQUEST §R5 |
| 23 | Scrollable Combat Log | RichTextLabel with colored BBCode tags for attacks, damage, crits, death saves | M5 | ORIGINAL_REQUEST §R5 |
| 24 | Floating Combat Text (FCT) | Floating damage/heal text using Tween interpolation, drift, and fade out | M5 | ORIGINAL_REQUEST §R5 |
| 25 | Audio & SFX Integration | 3 BGM tracks, 8 combat/UI SFX mapped to AudioManager and AudioStreamPlayers | M5 | ORIGINAL_REQUEST §R5 |
| 26 | WebSocket Client Engine | Native WebSocketPeer connecting to /ws/{room_id}/{player_id}?player_name={name} | M6 | ORIGINAL_REQUEST §R6 |
| 27 | Typed Protocol Serialization | Typed JSON serialization/deserialization for all 9 client and 8 server message types | M6 | ORIGINAL_REQUEST §R6 |
| 28 | State Sync & Anti-Cheat | State synchronization with GameManager, hidden hand filtering, rejection handling | M6 | ORIGINAL_REQUEST §R6 |
| 29 | Comprehensive GUT Test Suite | 100% passing tests for Grid, Combat, Characters, Cerco, UI, and WebSocket | M7 | ORIGINAL_REQUEST §R7 |
| 30 | Adversarial Test Hardening | Stress testing edge cases, boundary coordinates, race conditions, extreme values | M7 | Project Pattern §Dual Track |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Foundation & Core Infrastructure | Godot 4 project setup, Autoloads (GameManager, EventBus, DataManager, AudioManager), GUT test runner infra | none | PLANNED |
| M2 | Tactical Grid & Combat Engine | 20x20 grid, AStar2D 8-way, LoS, cover, D&D 5e math, death saves, status conditions | M1 | PLANNED |
| M3 | Entities, Heroes & 24 Isectum Castes | CharacterData.gd, Character.tscn, 11 Heroes + Lysander (.tres), 24 Isectum castes (.tres/scripts) | M1, M2 | PLANNED |
| M4 | Cerco Mode, Deckbuilder & Sinergias | CardData.gd, Card.tscn (fan layout), CercoSyncRound.gd, synergies, fortress economy, CercoCombatJudge | M1, M2, M3 | PLANNED |
| M5 | UI/UX (HUD Dark Fantasy) & Audio | CanvasLayer HUD, top resource bar, hero roster, CombatLog (RichTextLabel), FloatingCombatText, AudioManager | M1, M2, M3, M4 | PLANNED |
| M6 | WebSocket Multiplayer Co-op Client | WebSocketClient.gd, typed JSON protocol serializer, /ws/{room_id}/{player_id} handler, state sync | M1, M2, M4 | PLANNED |
| M7 | Final Milestone: 100% GUT Test Pass & Hardening | Phase 1: 100% passing GUT tests (Tiers 1-4). Phase 2: Adversarial coverage hardening (Tier 5) | M1, M2, M3, M4, M5, M6 | PLANNED |

---

## Interface Contracts

### EventBus Signals
```gdscript
# EventBus.gd
signal unit_moved(unit_id: String, from_pos: Vector2i, to_pos: Vector2i)
signal unit_attacked(attacker_id: String, target_id: String, hit: bool, is_crit: bool, damage: int, damage_type: String)
signal unit_damaged(unit_id: String, amount: int, current_hp: int, max_hp: int)
signal unit_died(unit_id: String)
signal death_save_rolled(unit_id: String, roll: int, successes: int, failures: int, status: String)
signal status_applied(unit_id: String, status_id: String, duration: int)
signal status_removed(unit_id: String, status_id: String)
signal card_selected(player_id: String, card_id: String)
signal round_resolved(round_number: int, sync_results: Dictionary)
signal synergy_triggered(synergy_type: String, bonus_description: String)
signal resources_updated(wood: int, metal: int, crystal: int, ap: int)
signal network_message_received(message_type: String, payload: Dictionary)
signal network_connection_status_changed(connected: bool, room_id: String)
```

### DataManager API
```gdscript
# DataManager.gd
func get_hero_data(hero_id: String) -> CharacterData
func get_all_heroes() -> Array[CharacterData]
func get_isectum_caste(caste_id: String) -> IsectumCasteData
func get_all_isectum_castes() -> Array[IsectumCasteData]
func get_card_data(card_id: String) -> CardData
func get_all_cards() -> Array[CardData]
```

### TacticalGrid ↔ CombatRules Contract
```gdscript
# TacticalGrid.gd
func is_valid_cell(pos: Vector2i) -> bool
func is_cell_walkable(pos: Vector2i) -> bool
func get_terrain_cost(pos: Vector2i) -> float
func find_path(from_pos: Vector2i, to_pos: Vector2i) -> Array[Vector2i]
func has_line_of_sight(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false) -> bool
func get_raycast_cover(attacker_pos: Vector2i, target_pos: Vector2i) -> int # 0, 2, or 1000
func get_adjacent_cover_bonus(pos: Vector2i) -> int # 0, 3, or 5

# CombatRules.gd
func calculate_modifier(stat_value: int) -> int # floor((stat - 10) / 2)
func calculate_proficiency(level: int) -> int # 1 + ceil(level / 4)
func resolve_attack(attacker: CharacterData, target: CharacterData, distance: int, has_advantage: bool, has_disadvantage: bool, cover_ac_bonus: int) -> AttackResult
func apply_damage(target: CharacterData, amount: int, damage_type: String) -> DamageResult
func roll_death_save(character: CharacterData) -> DeathSaveResult
```

### CercoEngine ↔ WebSocketClient Contract
```gdscript
# CercoSyncRound.gd
func register_player_card(player_id: String, card: CardData) -> void
func resolve_synchrony_round(round_number: int) -> SyncRoundResult

# WebSocketClient.gd
func send_select_card(card_id: String) -> void
func send_move_hero(target_pos: Vector2i) -> void
func send_attack_target(target_id: String) -> void
func send_work_action(action_type: String, zone_id: String) -> void
func send_end_round() -> void
```

---

## Code Layout
```text
godot_project/
├── project.godot
├── .gutconfig.json
├── addons/
│   └── gut/                        # GUT framework files
├── assets/
│   ├── images/
│   │   ├── characters/
│   │   ├── environment/
│   │   └── ui/
│   └── sounds/
├── dados/                          # JSON data files (mirrored/linked)
├── scenes/
│   ├── main/
│   │   ├── Main.tscn
│   │   └── Main.gd
│   ├── entities/
│   │   ├── Character.tscn
│   │   └── Character.gd
│   ├── cerco/
│   │   ├── Card.tscn
│   │   ├── Card.gd
│   │   ├── FortressBoard.tscn
│   │   └── FortressBoard.gd
│   └── ui/
│       ├── HUD.tscn
│       ├── HUD.gd
│       ├── CombatLog.tscn
│       ├── CombatLog.gd
│       ├── FloatingCombatText.tscn
│       └── FloatingCombatText.gd
├── scripts/
│   ├── autoload/
│   │   ├── GameManager.gd
│   │   ├── EventBus.gd
│   │   ├── DataManager.gd
│   │   └── AudioManager.gd
│   ├── core/
│   │   ├── TacticalGrid.gd
│   │   ├── CombatRules.gd
│   │   ├── DeathSaves.gd
│   │   └── StatusEffectManager.gd
│   ├── resources/
│   │   ├── CharacterData.gd
│   │   ├── IsectumCasteData.gd
│   │   ├── CardData.gd
│   │   └── AttackResult.gd
│   ├── cerco/
│   │   ├── CercoSyncRound.gd
│   │   ├── FortressEconomy.gd
│   │   └── CercoCombatJudge.gd
│   └── network/
│       ├── WebSocketClient.gd
│       └── ProtocolMessages.gd
└── test/
    ├── unit/
    │   ├── test_autoloads.gd
    │   ├── test_tactical_grid.gd
    │   ├── test_combat_rules.gd
    │   ├── test_death_saves.gd
    │   ├── test_status_effects.gd
    │   ├── test_entities.gd
    │   ├── test_isectum_castes.gd
    │   ├── test_cerco_deckbuilder.gd
    │   ├── test_cerco_judge.gd
    │   ├── test_ui_audio.gd
    │   └── test_websocket_client.gd
    └── e2e/
        ├── test_full_combat_flow.gd
        ├── test_cerco_full_cycle.gd
        └── test_coop_session_sync.gd
```
