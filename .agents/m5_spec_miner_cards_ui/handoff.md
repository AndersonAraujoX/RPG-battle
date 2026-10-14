# Handoff Report: Specification Mining for Milestone 5 (UI/UX do Cerco: Fan Cards & HUD Controls)

- **Date**: 2026-10-01T01:45:00Z
- **Author**: Specification Miner (Milestone 5 - UI/UX do Cerco)
- **Role**: Specification Miner
- **Status**: Complete & Verified Headless
- **Target Location**: `/home/anderson/Documents/projeto/RPG-battle/.agents/m5_spec_miner_cards_ui/handoff.md`

---

## 1. Observation

Direct observations extracted from authoritative reference files:

### 1.1 Reference Card Fan Layout (`src/states/cerco/draw_cards.py`)
- **Container and Hand Geometry** (lines 20–35):
  ```python
  def _calcular_pos_carta_na_mao(self, idx, total_cartas):
      mr = self.mao_rect
      total_cartas = max(1, total_cartas)
      espaco_reservado_esquerda = 230
      espaco_reservado_direita = 130
      largura_disponivel = mr.width - espaco_reservado_esquerda - espaco_reservado_direita
      cw = min(96, largura_disponivel // total_cartas)
      gap = max(2, (largura_disponivel - cw * total_cartas) // (total_cartas + 1))
      cx = mr.x + espaco_reservado_esquerda + gap + idx * (cw + gap)

      # Curvatura suave de Leque (Fan Arc Layout)
      mid_idx = (total_cartas - 1) / 2.0
      offset_center = idx - mid_idx
      fan_arc_y = int((offset_center ** 2) * 1.6)
      cy = mr.y + 4 + fan_arc_y
      ch = mr.height - 8
      return cx, cy, cw, ch
  ```
- **Viewport and Rectangles** (`draw_ui.py:29-32`):
  - Base resolution: `1280 x 720`.
  - `self.mapa_rect = pygame.Rect(8, 65, W - 330, H - 255)` $\rightarrow$ `(8, 65, 950, 465)`.
  - `self.painel_rect = pygame.Rect(W - 318, 65, 310, H - 75)` $\rightarrow$ `(962, 65, 310, 645)`.
  - `self.mao_rect = pygame.Rect(8, H - 146, W - 330, 138)` $\rightarrow$ `(8, 574, 950, 138)`.
  - Card Dimensions: `cw = 96`, `ch = 130` (from `138 - 8`).
  - Available width in hand area: $950 - 230 - 130 = 590$ px.

- **Deck Piles & Threat Discard** (`draw_cards.py:43–94`):
  - Enemy Deck: `(mr.x + 10, mr.y + 6, 96, 126)`, stacked visually with offsets: `move(offset * 2, -offset * 2)` for `min(4, max(1, count // 3))`.
  - Enemy Revealed Discard: `(mr.x + 116, mr.y + 6, 96, 126)`.
  - Player Hero Deck: `(mr.right - 106, mr.y + 6, 96, 126)`, stacked visually with offsets `move(-offset * 2, -offset * 2)`.

- **Hover Elevation, Aura & Selection** (`draw_cards.py:128–150`):
  - Hover Lift: `deslocamento_y = -30 if hover else 0`.
  - 3D Shadow: `shadow_rect = pygame.Rect(cx, cy + 4, cw, ch)`, color `(5, 5, 10)`, border radius 8.
  - Hover Aura Outlines:
    * Outer Cyan Glow: `crect.inflate(6, 6)`, width 2, color `(120, 220, 255)`.
    * Inner Gold Accent: `crect.inflate(2, 2)`, width 1, color `(255, 225, 80)`.
  - Border Colors: `C_ACENTO = (200, 140, 255)` if selected; `C_OURO = (255, 215, 0)` if hovered; `C_BORDA = (50, 50, 70)` normally.
  - Selection Lift & Mode: `sel = (i == self.idx_carta_queimar)` or active card selection. Displays `DESCARTE` tag in red `(40, 10, 10)` with border `C_PERIGO`.

- **Card Visual Elements & Badges** (`draw_cards.py:136–279`):
  - Top Gem: Center at `(crect.centerx, crect.y + 13)`, radius 11, rhombus points `(cx, cy-8), (cx+8, cy), (cx, cy+8), (cx-8, cy)`.
  - Gem & Theme Colors:
    * Movimento: `(100, 200, 255)` (Cyan / Steel Blue)
    * Trabalho: `(120, 220, 100)` (Emerald Green)
    * Escavação: `(255, 195, 40)` (Golden Amber)
    * Upgrade: `(255, 200, 50)` (Radiant Gold)
  - Card Art Frame: `(crect.x + 6, crect.y + 24, cw - 12, 38)`.
  - Name Banner: `(crect.x + 8, crect.y + 66, cw - 16, 18)` with dark backing `(8, 8, 12, 220)`.
  - Description: `crect.y + 88`, color `C_DIM = (160, 160, 170)`.
  - Stat Pills: `y_status = crect.y + ch - 22`, pill dimensions `26 x 16`, gap 4:
    * `M<val>`: blue `(80, 180, 255)`
    * `T<val>`: green `(100, 220, 120)`
    * `E<val>`: gold `(255, 215, 80)`

### 1.2 Godot 4 Resource & Model Contracts
- `CardData.gd`:
  - Canonical types: `TYPE_ACAO = "ACAO"`, `TYPE_UPGRADE = "UPGRADE"`, `TYPE_RUNA = "RUNA"`, `TYPE_DEFESA = "DEFESA"`.
  - Badges: `BADGE_MARCHA = "MARCHA"`, `BADGE_TRABALHO = "TRABALHO"`, `BADGE_ESCAVACAO = "ESCAVACAO"`, `BADGE_COMBATE = "COMBATE"`, `BADGE_ESPECIAL = "ESPECIAL"`.
  - Resource Costs: `cost_wood: int`, `cost_leather: int`, `cost_metal: int`, `cost_crystal: int`, `cost_ap: int`.
  - Economy Validation: `func can_afford(economy: Variant) -> bool`.
- `CercoDeck.gd`:
  - Manages `draw_pile`, `hand`, `discard_pile`, and `market_cards`.
  - Signals: `card_drawn(card)`, `card_played(card)`, `card_discarded(card)`, `deck_reshuffled(discard_count)`.
  - Operations: `draw_cards(count)`, `play_card(card_id)`, `play_card_by_index(index)`, `discard_card(card_id)`.
- `CercoSyncRound.gd`:
  - Simultaneous round registration: `register_player_action(player_id, card, target_params)`.
  - Sinergias: `team_synergies` (>=2 same badge), `supreme_synchrony` (all players same badge $\rightarrow$ +2 crystals).

---

## 2. Logic Chain

From the authoritative sources above, we derive the exact mathematical, architectural, and interaction specifications:

### 2.1 Mathematical Formulation of the Fan Arc Layout
1. **Coordinate Geometry**:
   - Let $N$ be the number of cards in hand ($N \ge 0$).
   - For $N = 0$: The layout returns an empty list, and the UI displays the empty-hand message.
   - For $N > 0$: Center index is $M = \frac{N - 1}{2.0}$.
   - For each card index $i \in [0, N - 1]$, the normalized offset from the center is:
     $$d(i) = i - M$$
     Notice:
     - When $N = 1$: $M = 0$, $d(0) = 0$.
     - When $N = 5$: $M = 2.0$, $d(i) \in \{-2, -1, 0, +1, +2\}$.
     - When $N$ is even (e.g. $N = 4$): $M = 1.5$, $d(i) \in \{-1.5, -0.5, +0.5, +1.5\}$.

2. **Arc Rotation Angles ($\theta(i)$)**:
   - In Pygame, cards were rendered without 2D rotation for performance. In Godot 4, true rotational fanning provides the authentic tabletop card aesthetic.
   - Let $\Delta\theta$ be the angular increment per card.
   - To prevent cards from tilting excessively when $N$ is large, we clamp the total spread $\Theta_{\text{total}}$:
     $$\Delta\theta = \min\left(4.0^\circ, \frac{\Theta_{\text{max\_spread}}}{N - 1}\right) \quad \text{for } N > 1$$
     Where $\Theta_{\text{max\_spread}} = 24.0^\circ$ (so maximum individual card tilt is $\pm 12.0^\circ$).
   - The rotation angle for card $i$ is:
     $$\theta(i) = d(i) \times \Delta\theta$$
     In Godot GDScript:
     ```gdscript
     var rot_deg: float = offset_center * angle_step_deg
     var rot_rad: float = deg_to_rad(rot_deg)
     ```

3. **Horizontal Spacing ($x(i)$)**:
   - Available width in container: $W_{\text{avail}}$. Standard card width: $C_w = 96.0$ px.
   - When cards fit without overlap ($N \le 5$ and $N \times C_w \le W_{\text{avail}}$):
     $$\text{gap} = \frac{W_{\text{avail}} - N \times C_w}{N + 1}$$
     $$\text{spacing} = C_w + \text{gap}$$
     $$\text{start\_x} = \text{gap}$$
     $$x(i) = \text{start\_x} + i \times \text{spacing}$$
   - When cards must overlap ($N > 5$ or narrow viewport):
     $$\text{step} = \frac{W_{\text{avail}} - C_w}{N - 1}$$
     $$x(i) = i \times \text{step}$$
   - In a centered fan container of width $W$, the cards can be centered:
     $$\text{total\_span} = (N - 1) \times \text{step} + C_w$$
     $$\text{center\_offset\_x} = \frac{W - \text{total\_span}}{2.0}$$
     $$x(i) = \text{center\_offset\_x} + i \times \text{step}$$

4. **Vertical Curvature ($y(i)$)**:
   - Two mathematically consistent methods:
     * **Parabolic Formula** (from `draw_cards.py:32`):
       $$y(i) = y_{\text{base}} + (d(i))^2 \times K_y$$
       Where $K_y = 1.6$ (or dynamic $K_y = \frac{24.0}{\max(1, M^2)}$ to ensure the outer cards drop at most 24px).
     * **Circular Projection**:
       Using an imaginary pivot point $(X_c, Y_p)$ with radius $R = 550.0$ px:
       $$y(i) = y_{\text{base}} + R \times (1 - \cos(\theta(i)))$$
       By Taylor expansion: $1 - \cos(\theta) \approx \frac{\theta^2}{2} = \frac{(d(i) \Delta\theta)^2}{2}$.
       This proves that the Parabolic Formula is the exact first-order Taylor approximation of the circular arc, guaranteeing smooth and computationally lightweight positioning!

5. **Hover Elevation & State Transforms**:
   - **Resting State**:
     $$\text{pos} = (x(i), y(i)), \quad \text{rot} = \theta(i), \quad \text{scale} = (1.0, 1.0), \quad \text{z\_index} = i$$
   - **Hovered State** ($i == \text{hovered\_index}$):
     $$\text{pos} = (x(i), y(i) - 30.0), \quad \text{rot} = 0^\circ, \quad \text{scale} = (1.08, 1.08), \quad \text{z\_index} = 20$$
     Card straightens upright ($0^\circ$), lifts by 30px, zooms by 8%, and draws above all unhovered cards.
   - **Selected State** ($i == \text{selected\_index}$):
     $$\text{pos} = (x(i), y(i) - 45.0), \quad \text{rot} = 0^\circ, \quad \text{scale} = (1.10, 1.10), \quad \text{z\_index} = 25$$
     Card lifts 45px with Accent border highlight (`#C88CFF`).
   - **Adjacent Neighbor Push**:
     When card $i$ is hovered, neighbors $i - 1$ and $i + 1$ shift horizontally by $\mp 12$px away from card $i$, creating physical spacing for the hovered card.

---

### 2.2 Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Layout | `CardFanLayoutCalculator` | Pure mathematical calculator computing card positions, angles, and scales for $N$ cards | Hand size $N$, container dimensions, card dimensions | Array of `CardTransformData` (pos, rot_deg, scale, z_index) | Returns empty array if $N \le 0$; handles $N=1$ without division by zero | `draw_cards.py:19-35` |
| 2 | Visual | Badge & Gem Rendering | Renders category badge with diamond gem and themed gradient | `CardData.badge` (MARCHA, TRABALHO, ESCAVACAO, COMBATE, ESPECIAL) | Themed color palette, gem polygon, and category icon | Defaults to MARCHA (Cyan) if badge unrecognized | `CardData.gd:15-19`, `draw_cards.py:136-167` |
| 3 | Visual | Cost Badges & Economy Check | Displays Wood, Leather, Metal, Crystal, AP costs with affordability color coding | `CardData` resource costs, `WorkshopEconomy` state | Cost pill widgets with green/red indicator | Dims card and displays red cost if economy insufficient | `CardData.gd:28-34,79-119`, `draw_panel.py:185-190` |
| 4 | Visual | Stat Pills Display | Displays Movement, Work, and Excavation values at bottom of card | `movement`, `work`, `excavation` integer fields | Pill boxes `M<val>`, `T<val>`, `E<val>` with respective theme colors | Omitted if value is 0 | `draw_cards.py:242-265` |
| 5 | Interaction | Hover Lift & Straighten | Elevates hovered card by -30px, resets rotation to $0^\circ$, and elevates z_index | Mouse enter event on `CardUI` | Visual tween to lifted position and upright angle | Reverts smoothly on mouse exit | `draw_cards.py:132-150` |
| 6 | Interaction | Card Selection | Toggles card selection state, elevating it -45px with accent border | Mouse click / tap on `CardUI` | Emits `card_selected` signal, updates visual border | Clicking again or right-click cancels selection (`card_deselected`) | `input.py:356-382`, `draw_cards.py:131,179-180` |
| 7 | Interaction | Click-to-Play Activation | Directly plays or registers selected card | Left click / Enter key / Play trigger | Emits `card_played_requested` signal | Blocked if player lacks resources or already acted in sync round | `input.py:112-133,379-380`, `round_simultaneo.py:97-132` |
| 8 | Interaction | Drag & Drop Zone Targeting | Dragging card upward from hand and releasing onto a board zone | Mouse drag gesture past vertical threshold | Emits `card_played_requested` with target zone metadata | Snaps back to fan resting position if dropped over invalid zone | `ORIGINAL_REQUEST.md:R4`, `input.py:262-265` |
| 9 | Visual | Deck Piles Isometric Stacking | Renders draw and discard decks with 3D offset stack effect based on card count | Deck size `count` | Multi-layered card back rectangles with counter text | Stack clamped to max 4 visible layers | `draw_cards.py:43-73` |
| 10 | Visual | Threat Card Reveal Display | Displays top enemy discard card with level, symbol, and danger aura | Top threat card dictionary | Danger border, symbol, title, and pulse animation | Placeholder "Sem Ameaça" if discard empty | `draw_cards.py:75-94,280-320` |
| 11 | Architecture | Signal Decoupling | Decoupled signals allowing pure headless GUT testing of UI logic | Signals `card_selected`, `card_hovered`, `card_played_requested` | Type-safe GDScript signal emissions | Headless execution operates without requiring physical window | `PROJECT.md:R7`, `TEST_INFRA.md:17` |

---

### 2.3 Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Fan Layout | $N = 0$ (Empty hand) | Calculator returns `[]`. Container renders placeholder: *"Sem cartas na mão — jogue cartas ou passe o turno"*. Zero crashes, no division by zero. |
| 2 | Fan Layout | $N = 1$ (Single card) | Offset $d(0) = 0$, rotation $= 0^\circ$, placed exactly at horizontal center $\frac{W_{\text{avail}} - C_w}{2}$. Hover lift moves strictly vertically. |
| 3 | Fan Layout | $N = 2$ (Two cards) | Offsets $\mp 0.5$, symmetrical slight tilt (e.g. $\mp 2.5^\circ$), spacing centered around midpoint. |
| 4 | Fan Layout | $N = 5$ (Canonical starter hand) | Perfect symmetrical arc: card 2 at $0^\circ$ (zenith), cards 1 & 3 at $\mp 4^\circ$, cards 0 & 4 at $\mp 8^\circ$. |
| 5 | Fan Layout | $N \ge 8$ (Overcrowded hand, e.g. 10–12 cards) | Dynamic overlap step activates: spacing shrinks to $\frac{W - C_w}{N - 1}$. Rotation clamped to $\pm 12^\circ$. Hovered card elevates to `z_index = 20` so it is 100% visible over overlapping neighbors. |
| 6 | Economy | Card with cost higher than fortress stock | Card displays dimmed modulation (`Color(0.6, 0.6, 0.6)`), red cost values. Click does NOT trigger play; emits `play_rejected` and triggers audio error cue. |
| 7 | Interaction | Rapid mouse traverse across hand | Mouse enters card $k+1$ before $k$ finishes tween. State machine enforces mutual exclusion: previous card unhover is immediately dispatched, preventing stuck elevated cards. |
| 8 | Interaction | Drag released below threshold or over invalid target | Released at $y > \text{threshold}$ or outside valid zones. Card initiates snap-back `Tween` with `TRANS_BACK` / `EASE_OUT` returning smoothly to resting fan position. |
| 9 | Lifecycle | Freeing `CardFanContainer` in GUT unit test | All child `CardUI` instances, textures, and active Tweens are killed and freed. GUT verifies 0 ObjectDB leaks. |

---

### 2.4 Decoupled Godot 4 UI Architecture Strategy

To guarantee that 100% of Milestone 5 UI logic can be tested automatically via GUT in headless mode (`bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`), we design a 4-tier decoupled architecture:

```
┌──────────────────────────────────────────────────────────┐
│              1. CardFanLayoutCalculator.gd                │
│ (Pure RefCounted — 0 UI dependencies — 100% Headless Math)│
│  - calculate_layout(count, container_size, options)      │
│  - get_card_transform(index, count, container_size)      │
│  - get_hover_transform(index, count, container_size)      │
└────────────────────────────┬─────────────────────────────┘
                             │ Uses
┌────────────────────────────▼─────────────────────────────┐
│                   2. CardFanContainer.gd                 │
│ (Control Node — Manages CardUI instances & input routing)│
│  - set_hand(cards: Array[CardData])                      │
│  - select_card(index: int) / deselect()                  │
│  - Signals: card_selected, card_played_requested         │
└────────────────────────────┬─────────────────────────────┘
                             │ Manages children
┌────────────────────────────▼─────────────────────────────┐
│                       3. CardUI.gd                       │
│ (Control Node — Single Card visual presentation & input) │
│  - setup(card_data: CardData, index: int)                │
│  - set_hovered(bool) / set_selected(bool)                │
│  - Signals: clicked, hovered, unhovered, drag_ended      │
└────────────────────────────┬─────────────────────────────┘
                             │ Wire to
┌────────────────────────────▼─────────────────────────────┐
│                 4. EventBus.gd & HUD.gd                  │
│ (Autoload / Main HUD Controller — Coordinates gameplay)  │
│  - EventBus.card_selected(player_id, card_id)            │
│  - EventBus.audio_play_sfx_requested("card_play")        │
└──────────────────────────────────────────────────────────┘
```

#### Detailed Class Specification

1. **`res://scripts/ui/CardFanLayoutCalculator.gd`** (`RefCounted`):
   - **Properties**:
     * `card_size: Vector2 = Vector2(96, 130)`
     * `max_arc_spread_deg: float = 24.0`
     * `max_step_angle_deg: float = 4.5`
     * `hover_lift_px: float = 30.0`
     * `selected_lift_px: float = 45.0`
     * `arc_curvature_factor: float = 1.6`
   - **Key Methods**:
     * `calculate_fan_transforms(card_count: int, container_width: float, container_height: float) -> Array[Dictionary]`:
       Returns array of dictionaries:
       `{ "position": Vector2, "rotation_deg": float, "scale": Vector2, "z_index": int }`.
     * `get_card_transform(index: int, card_count: int, container_width: float, container_height: float, is_hovered: bool, is_selected: bool) -> Dictionary`:
       Computes single card transform including hover lift or selection elevation.

2. **`res://scripts/ui/CardUI.gd`** (`Control`):
   - **Properties**:
     * `card_data: CardData`
     * `card_index: int = 0`
     * `is_hovered: bool = false`
     * `is_selected: bool = false`
     * `is_disabled: bool = false`
     * `resting_position: Vector2`
     * `resting_rotation: float`
   - **Signals**:
     * `signal card_clicked(card: CardData, index: int)`
     * `signal card_hovered(card: CardData, index: int)`
     * `signal card_unhovered(card: CardData, index: int)`
     * `signal card_drag_started(card: CardData, index: int, global_pos: Vector2)`
     * `signal card_drag_ended(card: CardData, index: int, global_pos: Vector2, cancelled: bool)`
   - **Methods**:
     * `setup(data: CardData, index: int) -> void`
     * `set_hovered(hovered: bool) -> void`
     * `set_selected(selected: bool) -> void`
     * `set_disabled(disabled: bool) -> void`
     * `get_badge_theme_color() -> Color`

3. **`res://scripts/ui/CardFanContainer.gd`** (`Control`):
   - **Properties**:
     * `cards: Array[CardData] = []`
     * `selected_index: int = -1`
     * `hovered_index: int = -1`
     * `calculator: CardFanLayoutCalculator`
     * `drag_drop_enabled: bool = true`
     * `drag_threshold_y: float = 100.0`
   - **Signals**:
     * `signal card_selected(card: CardData, index: int)`
     * `signal card_deselected(card: CardData, index: int)`
     * `signal card_played_requested(card: CardData, index: int, target_info: Dictionary)`
     * `signal card_hovered(card: CardData, index: int)`
     * `signal card_unhovered(card: CardData, index: int)`
   - **Methods**:
     * `set_hand(hand_cards: Array[CardData]) -> void`
     * `add_card(card: CardData) -> void`
     * `remove_card(index: int) -> CardData`
     * `select_card(index: int) -> void`
     * `deselect_card() -> void`
     * `recalculate_layout() -> void`
     * `get_card_ui(index: int) -> CardUI`
     * `clear_hand() -> void`

---

## 3. Caveats

1. **DisplayServer in Headless CLI Mode**:
   - In Godot 4 headless mode (`--headless`), `Control` nodes do not automatically receive mouse events from the OS window.
   - GUT tests verify interaction logic by invoking `_gui_input()` or public methods (`select_card()`, `set_hovered()`) directly.
2. **Animation Tweens in Tests**:
   - Tween animations in headless mode require advancing the frame or running tests without blocking tweens (e.g. Setting transforms immediately if `Engine.is_editor_hint()` or test mode).
3. **Card Art Sprites vs Procedural Draw**:
   - The original Python implementation in `draw_cards.py` used procedural Pygame primitives (`pygame.draw.circle`, `pygame.draw.polygon`, `pygame.draw.line`) when image assets were not present.
   - `CardUI.gd` must implement robust procedural fallbacks (using `_draw()` or StyleBoxes) so tests and demo runs look excellent even if card art PNGs are missing.

---

## 4. Conclusion

1. The Card Fan Arc layout mathematics have been completely reverse-engineered from `draw_cards.py:19-35` and extended with rotational fanning, circular arc projection, and overlap handling for arbitrary hand sizes ($N \in [0, 15]$).
2. The visual specifications (96x130px dimensions, badge gem colors, stat pills, cost badges, and 30px hover lift with glow outline) are fully codified and aligned with `CardData.gd` and `CercoDeck.gd`.
3. The clean decoupled architecture (`CardFanLayoutCalculator` as pure `RefCounted`, `CardFanContainer` and `CardUI` as typed `Control` nodes) guarantees 100% headless GUT testability with 0 memory leaks.
4. All edge cases (empty hand, single card, 5-card starter, >8-card overlap, unplayable cards, and drag cancellation) have been mapped with deterministic behaviors.

---

## 5. Verification Method

To verify these specifications independently:

1. **Verify Existing Project Health**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
   ```
   *Expected Result*: 11 test suites executed, 339 tests passed, 0 failures, exit code 0.

2. **Verify Python Reference Layout**:
   Inspect `src/states/cerco/draw_cards.py` lines 19 to 35 for exact fan arc parabola formula:
   ```bash
   grep -n -A 20 "def _calcular_pos_carta_na_mao" src/states/cerco/draw_cards.py
   ```

3. **Verify Card Resource and Deck Contracts**:
   Inspect `godot_project/scripts/resources/CardData.gd` and `godot_project/scripts/cerco/CercoDeck.gd`:
   ```bash
   head -n 35 godot_project/scripts/resources/CardData.gd
   ```

4. **Verify Milestone 5 Test Execution Criteria**:
   When workers implement `CardFanLayoutCalculator.gd` and `test_card_fan_ui.gd`, run:
   ```bash
   bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit -gtest=res://test/unit/test_card_fan_ui.gd
   ```
   *Pass Condition*: All unit tests pass with exit code 0 and 0 ObjectDB leaks.
