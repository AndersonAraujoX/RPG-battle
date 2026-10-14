# Milestone 5 Architecture & Testing Explorer Handoff Report

## Executive Summary
This report establishes the complete architectural specification, audio integration contract, and GUT unit testing blueprint for **Milestone 5: HUD do Cerco, Tabuleiro & Áudio** of the RPG-battle project (`godot_project/`).

The design satisfies all requirements from `.agents/ORIGINAL_REQUEST.md`, `PROJECT.md`, and `TEST_INFRA.md`, ensuring 100% decoupled clean architecture, headless audio safety with zero leaks, and an exhaustive 40-test GUT unit test suite (`test_cerco_hud.gd`) following strict Arrange-Act-Assert (AAA) standards.

---

## 1. Direct Observations

### 1.1 Existing Scope & Contracts
- **`ORIGINAL_REQUEST.md` (lines 77–92)**:
  - Definitive project pivot: exclusive focus on "Cerco da Fortaleza contra Isectum" (tactical fortress defense, 17 logical zones, custom D6 combat judge, 24 castes, deckbuilding with synchrony co-op, card fan hand, resource scoreboard, and combat log).
- **`PROJECT.md` (lines 4–13, 17–25, 38–46)**:
  - Viewport: 1280x720 base, Compatibility renderer, 2D mode.
  - Autoloads: `GameManager.gd`, `EventBus.gd`, `DataManager.gd`, `AudioManager.gd`.
  - 17 Canonical Zones: 1 Central Chamber, 3 Workshops (Carpintaria, Curtume, Fundição), 1 Courtyard (Pátio Central), 4 Perimeter Walls (N, S, L, O), 4 Watch Towers (NO, NE, SO, SE), 4 Invasion Spawn Fields (N, S, L, O).
  - Milestone 5 scope: "HUD do Cerco, Tabuleiro & Áudio - Cartas em leque interativas, destaque visual de zonas, placar de recursos e log do cerco."
  - Test threshold: 100% passing tests with exit code 0 and 0 ObjectDB leaks under headless execution (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`).
- **`TEST_INFRA.md` (lines 35–38, 46–52)**:
  - Specifies Tier 1–4 tests for Dark Fantasy HUD (CanvasLayer), Scrollable Combat Log, Floating Combat Text, and Audio/SFX.

### 1.2 Subsystem Implementations & Signal Signatures
- **`godot_project/scripts/autoload/EventBus.gd` (lines 8–36)**:
  - Central singleton managing global event dispatching.
  - Currently contains signals: `card_selected(player_id, card_id)`, `round_resolved(round_number, sync_results)`, `synergy_triggered(synergy_type, bonus_description)`, `resources_updated(wood, metal, crystal, ap)`, `combat_log_entry_added(bbcode_text)`, `audio_play_sfx_requested(sound_name, volume_db)`, `floating_text_requested(text, position, color)`.
  - *Observation*: Requirement 1 calls for wiring to `card_played`, `dice_rolled`, `damage_dealt`, `production_completed`, `synergy_triggered`, `supreme_synchrony_triggered`, and `round_resolved`. Signals `card_played`, `dice_rolled`, `damage_dealt`, `production_completed`, `supreme_synchrony_triggered`, and `wall_breached` are presently missing from `EventBus.gd` and need addition.
- **`godot_project/scripts/autoload/AudioManager.gd` (lines 7–27, 58–81, 224–260)**:
  - SFX pool size: 12 pre-allocated `AudioStreamPlayer` nodes assigned to the `SFX` audio bus.
  - Exactly 11 audio files exist in `res://assets/sounds/`:
    `attack.ogg`, `battle1.ogg` (BGM), `button_click.ogg`, `critical_hit.ogg`, `damage.ogg`, `heal.ogg`, `hit.ogg`, `intro.ogg` (BGM), `level_up.ogg`, `menu.ogg` (BGM), `miss.ogg`.
  - Methods: `play_sfx(sound_key: String, volume_scale: float = 1.0, pitch_scale: float = 1.0) -> AudioStreamPlayer`. Returns `null` and pushes a warning if the key is unknown.
  - Volume scale is clamped `[0.0001, 1.0]` and converted to dB via `linear_to_db()`. Pitch scale is clamped `[0.5, 2.0]`.
  - Listens to `EventBus.audio_play_sfx_requested`.
- **`godot_project/scripts/cerco/CercoSyncRound.gd` (lines 16–22, 68–73, 151–170, 388–395)**:
  - Defines `signal action_registered`, `layer_started`, `layer_resolved`, `synergy_detected`, `supreme_synchrony_triggered(badge, crystal_bonus)`, `round_completed(round_number, summary)`.
  - Connects to EventBus to emit `card_selected`, `synergy_triggered("SUPREME", ...)`, `synergy_triggered("TEAM", ...)`, and `round_resolved`.
- **`godot_project/scripts/cerco/FortressBoard.gd` (lines 9–16, 23–70)**:
  - Defines signals: `wall_damaged(wall_id, amount, remaining_hp)`, `wall_repaired(wall_id, amount, new_hp)`, `wall_breached(wall_id)`, `unit_placed`, `unit_moved`, `unit_removed`.
  - All 17 canonical zones declared as constants.
- **`godot_project/scripts/cerco/CercoCombatJudge.gd` (lines 10–15, 39–80)**:
  - Defines signals: `dice_rolled(rolls, total_impacts, total_shots, total_crits)`, `melee_attack_resolved(result)`, `ranged_attack_resolved(result)`, `catapult_fired(wall_id, damage, is_breached)`.
  - Custom D6 faces: `IMPACTO`, `DISPARO`, `CRITICO`, `ESQUIVA`, `NULO`.
- **`godot_project/scripts/cerco/WorkshopEconomy.gd` (lines 8–14)**:
  - Defines signals: `resources_updated(wood, leather, metal, crystal, ap)`, `resource_added`, `resource_spent`, `production_completed(workshop_zone, produced)`, `wall_repaired_with_resources`.
- **`godot_project/scripts/cerco/CercoDeck.gd` (lines 9–16)**:
  - Defines signals: `card_drawn(card)`, `card_played(card)`, `card_discarded(card)`, `deck_reshuffled(discard_count)`, `card_bought(card, cost)`, `market_refreshed(count)`.
- **Reference Math in `src/states/cerco/draw_cards.py` (lines 19–35, 129–134)**:
  - `mid_idx = (total_cartas - 1) / 2.0`
  - `offset_center = idx - mid_idx`
  - `fan_arc_y = int((offset_center ** 2) * 1.6)`
  - Hover displacement: `deslocamento_y = -30 if hover else 0`
- **Current Baseline Test Execution**:
  - Command: `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`
  - Result: 11 test suites executed, 339 tests run, 339 passed, 0 failed, 2909 assertions passed, exit code 0, 0 memory leaks.
- **Directory Inventory in `godot_project/`**:
  - `scenes/ui/` is currently empty.
  - `scripts/ui/` does not yet exist.
  - `test/unit/test_cerco_hud.gd` does not yet exist.

---

## 2. Logic Chain & Architectural Design

### 2.1 Overall HUD Architecture (`HUD.tscn` & `HUD.gd`)
The HUD is designed as a modular `CanvasLayer` (layer 1) ensuring it renders on top of the 2D world without interfering with camera transforms.

```text
HUD (CanvasLayer) [script: res://scripts/ui/HUD.gd]
└── RootControl (Control, Full Rect: 1280x720, mouse_filter = MOUSE_FILTER_IGNORE)
    ├── TopBar (PanelContainer, anchors: top, 1280x64)
    │   └── ResourceScoreboard (HBoxContainer, script: res://scripts/ui/ResourceScoreboard.gd)
    │       ├── RoundPhaseContainer (HBoxContainer: RoundLabel, PhaseLabel)
    │       ├── VSeparator1
    │       ├── ResourcesContainer (HBoxContainer: WoodBox, LeatherBox, MetalBox, CrystalBox, APBox)
    │       ├── VSeparator2
    │       └── WallIntegrityContainer (HBoxContainer: WallNLabel, WallSLabel, WallLLabel, WallOLabel)
    │
    ├── MainArea (HBoxContainer, anchors: 8, 70, 1272, 560)
    │   ├── BoardViewPanel (PanelContainer, size_flags_stretch_ratio: 2.2)
    │   │   └── BoardView (Control, script: res://scripts/ui/BoardView.gd)
    │   │       ├── FortressMapContainer (Control, interactive layout of 17 zones)
    │   │       │   ├── ChamberZone (Button / ZoneItem)
    │   │       │   ├── WorkshopZones (Carpintaria, Curtume, Fundicao, Patio)
    │   │       │   ├── WallZones (Muralha Norte, Sul, Leste, Oeste)
    │   │       │   ├── TowerZones (Torres NO, NE, SO, SE)
    │   │       │   └── SpawnZones (Campos Spawn N, S, L, O)
    │   │       └── ZoneTooltip (PanelContainer, visible = false)
    │   │
    │   └── RightPanel (VBoxContainer, size_flags_stretch_ratio: 1.0)
    │       ├── CombatLogPanel (PanelContainer, size_flags_vertical: Expand | Fill)
    │       │   └── VBoxContainer
    │       │       ├── LogHeader (HBoxContainer: TitleLabel, ClearBtn)
    │       │       └── CombatLog (RichTextLabel, script: res://scripts/ui/CombatLog.gd)
    │       └── BannerArea (Control, min_height: 50)
    │           ├── SynergyBanner (PanelContainer, visible = false)
    │           └── BreachWarningBanner (PanelContainer, visible = false)
    │
    └── BottomBar (Control, anchors: bottom, 0, 560, 1280, 720)
        ├── ActionControls (HBoxContainer, 0, 0, 240, 160)
        │   ├── BtnSyncRound (Button, text: "Sincronizar [Espaço]")
        │   ├── BtnDrawCard (Button, text: "Comprar Carta")
        │   └── BtnAutoPlay (Button, text: "AutoPlay [F5]")
        │
        ├── CardFanContainer (Control, 240, 0, 1020, 160)
        │   └── CardFan (Control, script: res://scripts/ui/CardFan.gd)
        │       └── CardsHolder (Control)
        │
        └── DeckCounters (VBoxContainer, 1030, 10, 1260, 150)
            ├── DrawPileLabel (Label, text: "Baralho: 10")
            └── DiscardPileLabel (Label, text: "Descarte: 0")
```

### 2.2 Component Responsibilities & Public APIs

#### A. `CardFan.gd` (`res://scripts/ui/CardFan.gd`)
- **Responsibility**: Manages the visual layout, smooth positioning, rotation angles, hover lift, card selection, and dynamic addition/removal of player hand cards.
- **Constants**:
  - `CARD_WIDTH: float = 100.0`
  - `CARD_HEIGHT: float = 140.0`
  - `HOVER_LIFT_Y: float = 30.0`
  - `ARC_FACTOR: float = 3.5`
  - `ANGLE_STEP_RAD: float = 0.05` (~2.86 degrees)
  - `MAX_SPREAD_WIDTH: float = 650.0`
- **Signals**:
  - `signal card_clicked(card: CardData, index: int)`
  - `signal card_hovered(card: CardData, index: int)`
  - `signal card_unhovered(card: CardData, index: int)`
  - `signal card_drag_started(card: CardData, index: int)`
  - `signal card_drag_ended(card: CardData, index: int)`
- **Math Formula**:
  For $N$ cards and card at index $i \in [0, N-1]$:
  $$\text{mid} = \frac{N - 1}{2.0}$$
  $$\text{offset} = i - \text{mid}$$
  $$\text{step\_x} = \begin{cases} 0 & N \le 1 \\ \min(\text{CARD\_WIDTH} + 12.0, \frac{\text{MAX\_SPREAD\_WIDTH}}{N - 1}) & N > 1 \end{cases}$$
  $$\text{pos.x} = \text{center\_x} + (\text{offset} \times \text{step\_x}) - (\text{CARD\_WIDTH} / 2.0)$$
  $$\text{pos.y} = \text{base\_y} + (\text{offset}^2 \times \text{ARC\_FACTOR})$$
  $$\text{rotation} = \text{offset} \times \text{ANGLE\_STEP\_RAD}$$
  $$\text{When Hovered}: \text{pos.y} \mathrel{-}= \text{HOVER\_LIFT\_Y}, \quad \text{rotation} = 0.0, \quad \text{scale} = (1.1, 1.1), \quad \text{z\_index} = 100$$
- **Public API**:
  - `set_cards(cards: Array[CardData]) -> void`
  - `add_card(card: CardData) -> CardUI`
  - `remove_card(index: int) -> CardData`
  - `clear_cards() -> void`
  - `get_card_count() -> int`
  - `get_card_node(index: int) -> CardUI`
  - `select_card(index: int) -> void`
  - `get_selected_index() -> int`

#### B. `CardUI.gd` (`res://scripts/ui/CardUI.gd`)
- **Responsibility**: Individual interactive card Control node displaying card name, badge icon, resource costs, effect text, and hover/selection outline.
- **Visuals**:
  - Color themes per badge: Marcha (`#1e3a8a`), Trabalho (`#14532d`), Escavação (`#78350f`), Combate (`#7f1d1d`), Upgrade (`#581c87`).
  - Badge tag: `[MOV]`, `[TRAB]`, `[ESC]`, `[COMB]`, `[UPG]`.
  - Cost badges: Wood, Leather, Metal, Crystal, AP.

#### C. `ResourceScoreboard.gd` (`res://scripts/ui/ResourceScoreboard.gd`)
- **Responsibility**: Displays current fortress resources (Wood, Leather, Metal, Crystal, AP), round number, current turn phase, and 4 wall integrity bars.
- **Signals**:
  - `signal resource_display_updated(type: String, value: int)`
- **Public API**:
  - `update_resources(wood: int, leather: int, metal: int, crystal: int, ap: int) -> void`
  - `update_wall_hp(wall_id: String, hp: int, max_hp: int) -> void`
  - `set_round(round_number: int, phase_name: String) -> void`
  - `get_resource_value(res_name: String) -> int`
  - `get_wall_hp(wall_id: String) -> int`

#### D. `BoardView.gd` (`res://scripts/ui/BoardView.gd`)
- **Responsibility**: Visual overlay representing all 17 fortress zones. Supports interactive selection, hover information, unit occupancy indicators, and wall breach warnings.
- **Signals**:
  - `signal zone_clicked(zone_id: String)`
  - `signal zone_hovered(zone_id: String)`
  - `signal zone_unhovered(zone_id: String)`
- **Visual States per Zone**:
  - `NORMAL`: Default stone/timber theme (`#1e293b`).
  - `HOVERED`: Accent outline (`#38bdf8`).
  - `SELECTED`: Golden glow outline (`#f59e0b`).
  - `BREACHED`: Emergency pulsing red border (`#ef4444`) with `[BRECHA!]` badge.
  - `CONTESTED`: Swarm warning badge (`#dc2626`).
- **Public API**:
  - `set_zone_state(zone_id: String, state: String) -> void`
  - `set_wall_breached(wall_id: String, breached: bool) -> void`
  - `set_zone_units(zone_id: String, defenders: Array[String], enemies: Array[String]) -> void`
  - `highlight_valid_moves(zone_ids: Array[String]) -> void`
  - `clear_highlights() -> void`
  - `get_zone_breached(wall_id: String) -> bool`

#### E. `CombatLog.gd` (`res://scripts/ui/CombatLog.gd`)
- **Responsibility**: Scrollable event log using `RichTextLabel` with BBCode formatting, auto-scroll, entry limits, and type-colored prefixes.
- **Constants**:
  - `MAX_LOG_ENTRIES: int = 100`
- **Prefixes & BBCode Colors**:
  - `[SISTEMA]`: `#94a3b8` (Slate Gray)
  - `[CARTA]`: `#38bdf8` (Sky Blue)
  - `[DADOS]`: `#facc15` (Amber Gold)
  - `[DANO]`: `#f87171` (Crimson Red)
  - `[BRECHA!]`: `#ef4444` (Bold Danger Red)
  - `[PRODUÇÃO]`: `#4ade80` (Emerald Green)
  - `[SINERGIA]`: `#c084fc` (Purple)
  - `[SINCRONIA SUPREMA!]`: `#f472b6` (Bold Magenta)
  - `[VITÓRIA]`: `#22c55e` (Bright Green)
  - `[DERROTA]`: `#ef4444` (Dark Red)
- **Public API**:
  - `append_entry(entry_type: String, message: String) -> void`
  - `append_bbcode(bbcode_text: String) -> void`
  - `clear_log() -> void`
  - `get_entry_count() -> int`
  - `get_last_entry_text() -> String`

### 2.3 EventBus Wiring & Decoupling Architecture
To guarantee clean architecture and full testability:
1. **Production Autoload Integration**:
   When added to the SceneTree, `HUD.gd` automatically checks for `/root/EventBus` and connects:
   - `EventBus.card_played` $\to$ `_on_event_card_played`
   - `EventBus.dice_rolled` $\to$ `_on_event_dice_rolled`
   - `EventBus.damage_dealt` $\to$ `_on_event_damage_dealt`
   - `EventBus.production_completed` $\to$ `_on_event_production_completed`
   - `EventBus.synergy_triggered` $\to$ `_on_event_synergy_triggered`
   - `EventBus.supreme_synchrony_triggered` $\to$ `_on_event_supreme_synchrony_triggered`
   - `EventBus.round_resolved` $\to$ `_on_event_round_resolved`
   - `EventBus.wall_breached` $\to$ `_on_event_wall_breached`
   - `EventBus.resources_updated` $\to$ `_on_event_resources_updated`
   - `EventBus.combat_log_entry_added` $\to$ `_on_event_combat_log_entry_added`
2. **Explicit Model Binding (Hermetic Unit Testing Hook)**:
   For isolated tests that do not run inside the global scene tree, `HUD.gd` provides:
   - `bind_board(board: FortressBoard) -> void`
   - `bind_deck(deck: CercoDeck) -> void`
   - `bind_economy(economy: WorkshopEconomy) -> void`
   - `bind_judge(judge: CercoCombatJudge) -> void`
   - `bind_sync_round(sync_round: CercoSyncRound) -> void`
   - `unbind_all() -> void`
3. **Signal Lifecycle Safety**:
   In `HUD._exit_tree()`, all connected signals (both EventBus and model bindings) are explicitly disconnected.

### 2.4 EventBus Signal Additions
To align `EventBus.gd` with `PROJECT.md` line 10 and the User Request, the following 6 signals should be added to `EventBus.gd`:
```gdscript
# ── Cerco & Tactical Signals (Milestone 5 additions) ─────────────────────────
signal card_played(player_id: String, card: CardData)
signal dice_rolled(rolls: Array, total_impacts: int, total_shots: int, total_crits: int)
signal damage_dealt(target_id: String, amount: int, is_crit: bool)
signal production_completed(workshop_zone: String, produced: Dictionary)
signal supreme_synchrony_triggered(badge: String, crystal_bonus: int)
signal wall_breached(wall_id: String)
```
*Note*: Adding these signals is 100% backwards-compatible and causes no regressions to existing tests.

---

## 3. Audio Integration & Headless Safety

### 3.1 Audio Event Mappings via `AudioManager.gd`
Because the asset folder contains exactly 11 `.ogg` files, HUD audio triggers are semantically mapped with pitch and volume scaling:

| Gameplay Event | Target SFX | Volume Scale | Pitch Scale | Acoustic Intent |
|---|---|---|---|---|
| Card Drawn | `button_click` | 0.8 | 1.3 | Light paper-like flick |
| Card Played / Selected | `button_click` | 1.0 | 0.9 | Crisp card placement |
| Dice Rolled | `hit` | 0.9 | 1.4 | Wooden dice tumble impact |
| Critical Dice / Impact | `critical_hit` | 1.0 | 1.1 | Resonant heavy strike |
| Damage Dealt | `damage` | 0.9 | 1.0 | Standard impact crunch |
| Wall Breach Warning | `damage` + `critical_hit` | 1.0 | 0.6 | Deep crumbling structural failure |
| Workshop Production | `button_click` | 0.8 | 1.1 | Mechanical anvil / tool tap |
| Team Synergy Triggered | `heal` | 0.9 | 1.2 | Harmonious magical chime |
| Supreme Synchrony | `level_up` | 1.0 | 1.1 | Epic golden synchrony fanfare |
| Victory Achieved | `level_up` | 1.0 | 1.0 | Triumphant brass sequence |
| Defeat / Breach Lost | `miss` | 1.0 | 0.7 | Low mournful descent |

### 3.2 Headless Safety & Zero Leaks Protocol
1. **No Hardware Audio Dependency**:
   - In headless mode (`DisplayServer.get_name() == "headless"` or CLI runner), Godot uses the `Dummy` audio driver.
   - All audio calls route through `EventBus.audio_play_sfx_requested` or `AudioManager.play_sfx()`.
2. **Zero Leaked Audio Nodes**:
   - `HUD.gd` and its sub-controls **NEVER** instantiate ad-hoc `AudioStreamPlayer` nodes.
   - `AudioManager.gd` uses a fixed pool of 12 pre-allocated players that recycle round-robin.
3. **Graceful Null Checking**:
   - If `AudioManager` or `EventBus` is absent or null in unit tests, HUD audio functions execute safely without null dereference or test crashes.

---

## 4. Comprehensive GUT Test Suite Design (`test_cerco_hud.gd`)

The test suite is authored in `godot_project/test/unit/test_cerco_hud.gd`. It tests the entire HUD system in complete isolation following the strict Arrange-Act-Assert (AAA) pattern.

### 4.1 Test Suite Setup & Teardown Architecture
```gdscript
# res://test/unit/test_cerco_hud.gd
extends GutTest

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
const CardUIScript = preload("res://scripts/ui/CardUI.gd")
const CardFanScript = preload("res://scripts/ui/CardFan.gd")
const BoardViewScript = preload("res://scripts/ui/BoardView.gd")
const ResourceScoreboardScript = preload("res://scripts/ui/ResourceScoreboard.gd")
const CombatLogScript = preload("res://scripts/ui/CombatLog.gd")

var _hud: CanvasLayer = null
var _board: FortressBoard = null
var _deck: CercoDeck = null
var _economy: WorkshopEconomy = null
var _judge: CercoCombatJudge = null

func before_each() -> void:
    _board = FortressBoard.new()
    _deck = CercoDeck.new()
    _economy = WorkshopEconomy.new()
    _judge = CercoCombatJudge.new()
    _hud = autofree(HUD_SCENE.instantiate())
    add_child_autofree(_hud)

func after_each() -> void:
    if _hud != null and is_instance_valid(_hud):
        _hud.cleanup()
    _hud = null
    _board = null
    _deck = null
    _economy = null
    _judge = null
```

### 4.2 Complete Enumeration of Test Cases (40 Tests)

#### Category 1: Card Fan Math & Layout Dynamics (Tests 1–10)
1. `test_card_fan_empty_hand`:
   - `# Arrange`: Initialize `CardFan` with an empty card array `[]`.
   - `# Act`: Call `fan.set_cards([])`.
   - `# Assert`: `assert_eq(fan.get_card_count(), 0)`, verify no child card nodes exist, no division-by-zero errors.
2. `test_card_fan_single_card`:
   - `# Arrange`: Create 1 `CardData` (Marcha).
   - `# Act`: Call `fan.set_cards([c1])`.
   - `# Assert`: `assert_eq(fan.get_card_count(), 1)`, rotation is `0.0`, X position is centered within container width.
3. `test_card_fan_even_card_count_symmetry`:
   - `# Arrange`: Create 4 `CardData` cards.
   - `# Act`: Call `fan.set_cards(cards)`.
   - `# Assert`: Offsets are symmetric ($-1.5, -0.5, +0.5, +1.5$), card 0 rotation $< 0$, card 3 rotation $> 0$, card 0 rotation $== -$card 3 rotation, arc Y of card 0 equals arc Y of card 3.
4. `test_card_fan_odd_card_count_symmetry`:
   - `# Arrange`: Create 5 `CardData` cards.
   - `# Act`: Call `fan.set_cards(cards)`.
   - `# Assert`: Card 2 (middle) offset is $0.0$, rotation is $0.0$, arc Y is lowest point ($0.0$), cards 0/4 and 1/3 have symmetric positions.
5. `test_card_fan_max_hand_scaling`:
   - `# Arrange`: Create 8 `CardData` cards.
   - `# Act`: Call `fan.set_cards(cards)`.
   - `# Assert`: Total fan bounding width does not exceed container `MAX_SPREAD_WIDTH`, horizontal step auto-scales without overflowing viewport.
6. `test_card_fan_hover_lift`:
   - `# Arrange`: Populate fan with 3 cards.
   - `# Act`: Simulate mouse enter on card 1 (`card_node.set_hovered(true)`).
   - `# Assert`: `card_node.position.y` decreases by exactly `HOVER_LIFT_Y` (30.0 px), `card_node.scale` is $(1.1, 1.1)$, `card_node.z_index == 100`.
7. `test_card_fan_unhover_restores_position`:
   - `# Arrange`: Hover card 1.
   - `# Act`: Simulate mouse exit (`card_node.set_hovered(false)`).
   - `# Assert`: `card_node.position.y` returns to resting position, `scale` returns to $(1.0, 1.0)$, `z_index` returns to resting index `1`.
8. `test_card_fan_card_added_dynamically`:
   - `# Arrange`: Fan with 2 cards.
   - `# Act`: Call `fan.add_card(new_card)`.
   - `# Assert`: Count becomes 3, fan layout recalculates, new card node is added to tree and properly styled.
9. `test_card_fan_card_removed_dynamically`:
   - `# Arrange`: Fan with 3 cards.
   - `# Act`: Call `fan.remove_card(1)`.
   - `# Assert`: Count becomes 2, remaining cards re-index and re-center, removed node is queued for deletion.
10. `test_card_fan_custom_card_data_display`:
    - `# Arrange`: Build card with name "Martelo", badge TRABALHO, cost 2 wood, 1 metal.
    - `# Act`: Render card node.
    - `# Assert`: CardUI labels match name "Martelo", badge text matches "[TRAB]", cost counters display 2 wood, 1 metal.

#### Category 2: Resource Scoreboard Updates & Responsiveness (Tests 11–15)
11. `test_scoreboard_initial_values_zero`:
    - `# Arrange & Act`: Inspect freshly instantiated `ResourceScoreboard`.
    - `# Assert`: Wood, Leather, Metal, Crystal, and AP values report 0.
12. `test_scoreboard_update_resources_direct`:
    - `# Arrange`: Scoreboard node.
    - `# Act`: Call `scoreboard.update_resources(10, 5, 8, 3, 2)`.
    - `# Assert`: `assert_eq(scoreboard.get_resource_value("wood"), 10)`, leather is 5, metal is 8, crystal is 3, AP is 2.
13. `test_scoreboard_eventbus_resources_updated`:
    - `# Arrange`: HUD connected to EventBus.
    - `# Act`: `EventBus.resources_updated.emit(12, 6, 4, 1)`.
    - `# Assert`: Scoreboard displays wood 12, metal 6, crystal 4, AP 1.
14. `test_scoreboard_wall_hp_display`:
    - `# Arrange`: Scoreboard node.
    - `# Act`: Call `scoreboard.update_wall_hp(FortressBoard.ZONE_MURALHA_NORTE, 75, 100)`.
    - `# Assert`: North wall label displays 75 HP, internal tracking records 75.
15. `test_scoreboard_round_phase_banner`:
    - `# Arrange`: Scoreboard node.
    - `# Act`: Call `scoreboard.set_round(3, "Combate")`.
    - `# Assert`: Round label contains "3", Phase label contains "Combate".

#### Category 3: Zone Overlay Highlighting & Breach State Changes (Tests 16–21)
16. `test_zone_overlay_all_17_zones_initialized`:
    - `# Arrange & Act`: Inspect `BoardView`.
    - `# Assert`: Exactly 17 zone widgets exist matching the 17 constants of `FortressBoard.ALL_ZONES`.
17. `test_zone_overlay_hover_highlight`:
    - `# Arrange`: BoardView.
    - `# Act`: Simulate mouse enter on zone `ZONE_CARPINTARIA`.
    - `# Assert`: Zone visual state is `HOVERED`, signal `zone_hovered("CARPINTARIA")` is caught.
18. `test_zone_overlay_selection_state`:
    - `# Arrange`: BoardView.
    - `# Act`: Call `board_view.select_zone(FortressBoard.ZONE_CAMARA_CENTRAL)`.
    - `# Assert`: Central chamber state is `SELECTED`, `zone_clicked` signal emitted with zone ID.
19. `test_zone_overlay_wall_damage_color_shift`:
    - `# Arrange`: BoardView with North wall at 100 HP.
    - `# Act`: Update North wall HP to 30 HP.
    - `# Assert`: Health indicator shifts color/style to damaged warning state.
20. `test_zone_overlay_wall_breach_warning_state`:
    - `# Arrange`: BoardView with East wall at 100 HP.
    - `# Act`: Call `board_view.set_wall_breached(FortressBoard.ZONE_MURALHA_LESTE, true)`.
    - `# Assert`: Zone state is `BREACHED`, danger styling is applied, `get_zone_breached` returns `true`.
21. `test_zone_overlay_unbreach_on_repair`:
    - `# Arrange`: East wall breached (`breached == true`).
    - `# Act`: Call `board_view.set_wall_breached(FortressBoard.ZONE_MURALHA_LESTE, false)`.
    - `# Assert`: Breach state cleared, structural styling restored, `get_zone_breached` returns `false`.

#### Category 4: Combat Log Appending & BBCode Formatting (Tests 22–30)
22. `test_combat_log_initial_state`:
    - `# Arrange & Act`: Inspect `CombatLog`.
    - `# Assert`: `bbcode_enabled == true`, `scroll_following == true`, entry count is 0 or contains welcome message.
23. `test_combat_log_append_system_message`:
    - `# Arrange`: CombatLog.
    - `# Act`: Call `combat_log.append_entry("SISTEMA", "Cerco iniciado.")`.
    - `# Assert`: Entry count increments, text contains `[SISTEMA]` and "Cerco iniciado."
24. `test_combat_log_append_card_played`:
    - `# Arrange`: CombatLog.
    - `# Act`: Call `combat_log.append_entry("CARTA", "Jogador jogou Marcha (+15 MOV)")`.
    - `# Assert`: Text contains `[CARTA]` and "Marcha".
25. `test_combat_log_append_dice_roll`:
    - `# Arrange`: CombatLog.
    - `# Act`: Call `combat_log.append_entry("DADOS", "Rolagem: 2 Impactos, 1 Balestra")`.
    - `# Assert`: Text contains `[DADOS]` and Amber color tag.
26. `test_combat_log_append_damage_dealt`:
    - `# Arrange`: CombatLog.
    - `# Act`: Call `combat_log.append_entry("DANO", "Muralha Sul recebeu 20 de dano!")`.
    - `# Assert`: Text contains `[DANO]` and Crimson Red tag.
27. `test_combat_log_append_synergy_and_supreme_synchrony`:
    - `# Arrange`: CombatLog.
    - `# Act`: Call `combat_log.append_entry("SINERGIA", "Sinergia de Equipe: TRABALHO")` and `append_entry("SUPREMA", "Sincronia Suprema! +2 Cristais!")`.
    - `# Assert`: Text contains both entries with appropriate Purple and Magenta tags.
28. `test_combat_log_max_entries_truncation`:
    - `# Arrange`: CombatLog with limit of 100 entries.
    - `# Act`: Add 120 lines in a loop.
    - `# Assert`: Total retained lines do not exceed `MAX_LOG_ENTRIES` (100), oldest entries pruned, memory usage bounded.
29. `test_combat_log_clear`:
    - `# Arrange`: CombatLog with 10 entries.
    - `# Act`: Call `combat_log.clear_log()`.
    - `# Assert`: Text is empty, entry count is 0.
30. `test_combat_log_eventbus_integration`:
    - `# Arrange`: HUD connected to EventBus.
    - `# Act`: `EventBus.combat_log_entry_added.emit("Alerta de Cerco!")`.
    - `# Assert`: Message appears in CombatLog text.

#### Category 5: Signal Emissions & User Input Event Handling (Tests 31–35)
31. `test_hud_card_clicked_emits_signal`:
    - `# Arrange`: HUD with 1 card in fan.
    - `# Act`: Trigger click on card 0.
    - `# Assert`: HUD emits `card_selected` or `card_played` signal with card data.
32. `test_hud_sync_button_pressed_emits_signal`:
    - `# Arrange`: HUD instance.
    - `# Act`: Simulate button click on `BtnSyncRound`.
    - `# Assert`: `sync_round_requested` signal is emitted.
33. `test_hud_shortcut_toggle_combat_log`:
    - `# Arrange`: HUD instance with visible combat log.
    - `# Act`: Send unhandled input event for `toggle_combat_log` (Key 'L').
    - `# Assert`: Combat log panel visibility toggles or adjusts height.
34. `test_hud_bind_models_directly`:
    - `# Arrange`: Independent `FortressBoard` and `WorkshopEconomy`.
    - `# Act`: Call `_hud.bind_board(_board)` and `_hud.bind_economy(_economy)`. Emitting `_board.wall_damaged` updates scoreboard.
    - `# Assert`: HUD updates wall HP reactively without requiring EventBus autoload.
35. `test_hud_unbind_models_safely`:
    - `# Arrange`: Models bound to HUD.
    - `# Act`: Call `_hud.unbind_all()`. Emit signals on models.
    - `# Assert`: No exceptions, no dangling callable errors, HUD state remains stable.

#### Category 6: Teardown & Memory Safety (Tests 36–40)
36. `test_hud_tree_lifecycle_add_and_remove`:
    - `# Arrange`: Instantiate fresh HUD scene.
    - `# Act`: Add to tree via `add_child_autofree(hud)`, then call `hud.queue_free()`.
    - `# Assert`: Node exits tree without errors, ObjectDB leak count is 0.
37. `test_hud_rapid_creation_and_destruction`:
    - `# Arrange`: Loop count 10.
    - `# Act`: Instantiate and `free()` 10 HUD instances sequentially.
    - `# Assert`: Memory stabilizes, no orphaned child nodes remain in ObjectDB.
38. `test_hud_disconnects_all_eventbus_signals_on_exit_tree`:
    - `# Arrange`: HUD connected to EventBus.
    - `# Act`: Remove HUD from tree and call `hud.cleanup()`. Emit `EventBus.resources_updated`.
    - `# Assert`: No errors or dead callable invocations.
39. `test_hud_subcontrols_are_freed_recursively`:
    - `# Arrange`: HUD with populated CardFan, BoardView, and Scoreboard.
    - `# Act`: Call `hud.free()`.
    - `# Assert`: All sub-controls (`CardFan`, `BoardView`, `CombatLog`, `ResourceScoreboard`) are safely freed with parent.
40. `test_hud_headless_audio_safety`:
    - `# Arrange`: HUD instance in headless mode.
    - `# Act`: Trigger all audio mapped events (`card_draw`, `dice_roll`, `wall_breach`, `victory`, `defeat`, `supreme_synchrony`).
    - `# Assert`: No audio driver crashes, no exceptions, 0 extra audio players allocated outside the pool.

---

## 5. Caveats
1. **Audio Assets**: The project contains 11 sound files in `res://assets/sounds/`. No dedicated sound effects exist specifically for dice tumbling or wall alarms. The design uses pitch-shifted and volume-scaled variants of `hit.ogg`, `damage.ogg`, and `critical_hit.ogg`.
2. **2D Control Overlay vs Isometric Tilemap**: The Board View designed in Milestone 5 is an interactive Control layer overlay representing the 17 logical zones with status badges, HP, and highlights. This is fully decoupled from the low-level isometric tile renderer, allowing fast, deterministic headless GUT testing without requiring GPU rendering.
3. **Read-Only Explorer Scope**: In accordance with the Teamwork explorer persona, this document delivers specifications and designs; implementation will be carried out by the developer/worker agents in subsequent steps.

---

## 6. Conclusion
The architecture and testing strategy designed for Milestone 5 delivers:
1. **A Modular, Decoupled HUD**: Clean separation between `ResourceScoreboard`, `BoardView` (17 zones), `CombatLog` (BBCode), and `CardFan` (arc layout with hover lift).
2. **Dual-Wiring Versatility**: Connects to `EventBus` in production while supporting direct model injection (`bind_board`, `bind_deck`, etc.) for hermetic unit testing.
3. **Headless Audio Safety**: Zero-leak semantic mapping to pre-allocated audio pools.
4. **Exhaustive 40-Test GUT Suite**: 100% AAA compliance and strict `autofree` / `add_child_autofree` memory safety ensuring 0 ObjectDB leaks.

---

## 7. Verification Method

### 7.1 GUT Headless Test Commands
Once implemented, verify Milestone 5 via CLI:
```bash
cd /home/anderson/Documents/projeto/RPG-battle/godot_project

# 1. Run the dedicated Cerco HUD test suite:
./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit -gselect=test_cerco_hud.gd

# 2. Run the entire test suite to guarantee 0 regressions:
./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
```

### 7.2 Pass Criteria
- **Exit Code**: Exactly `0`.
- **Pass Rate**: 100% of tests pass (40 new HUD tests + 339 existing tests = 379 tests total).
- **Assertions**: 0 assertion failures.
- **Leaks**: 0 ObjectDB memory leaks upon engine exit.

### 7.3 Invalidation Conditions
- Any test failure in `test_cerco_hud.gd` or regression in prior suites.
- Any engine warning regarding orphaned nodes or ObjectDB leaks on exit.
- Any audio crash or crash in `--headless` execution mode.
- Non-symmetric fan layout calculation or card overlap clipping.
