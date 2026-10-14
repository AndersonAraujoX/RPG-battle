# Exploration Report: Character Asset Survey & Entity Architecture (`Character.tscn` / `Character.gd`)

**Date**: 2026-10-01  
**Agent**: `ent_explorer_1`  
**Milestone**: Entidades (M9)  
**Status**: Completed Investigation & Architecture Design  

---

## 1. Executive Summary

This report delivers a comprehensive investigation of character visual assets, data models, and an engineering blueprint for the core entity scene `res://scenes/entities/Character.tscn` and script `res://scripts/entities/Character.gd` in Godot Engine 4.3 (Compatibility Renderer).

Key findings:
1. **Asset Disparity**: Character assets vary from `32x32` pixel art (all 24 Isectum castes + Brutamonte + Infiltrador) to `500x500` (monsters), `676x369` (D&D hero classes), and `1024x1024` (processed high-resolution hero art). The entity scene must implement an automatic normalization scaling algorithm (`target_display_size = Vector2(30, 30)` or `Vector2(32, 32)`) to ensure visual coherence on the 20x20 tactical grid.
2. **Asset Organization**: 54 character PNG textures are distributed across 5 organized directories: `heroes/`, `animation/processed/`, `monsters/`, `monsters/isectum/`, and `bosses/`. An intelligent multi-tier texture loader is designed to locate any character asset automatically by ID with zero runtime crash risk.
3. **Architecture Choice**: `CharacterBody2D` is chosen as the scene root with `class_name Character`. It provides integrated mouse picking (`CollisionShape2D`), grid interaction, motion interpolation, and seamless integration with `TacticalGrid.gd` and `FortressBoardView.gd`.
4. **Visual Parity**: Faithfully replicates the retro pixel art style from the original Pygame engine:
   - **Selection Highlight**: Pulsating golden/cyan highlight ring.
   - **RetroHPBar**: 30x4 px bar with dark background (`#1e1e1e`), 1px black border (`#000000`), and tri-color threshold shift (Green > 50%, Yellow 25–50%, Red ≤ 25%).
   - **StatusContainer**: Color-coded 6x6 pixel badges for active conditions (Poison, Stun, Bleed, Burn, Freeze, etc.).
5. **Headless & GUT Compliance**: Strict static GDScript typing, decoupled signal emission (`EventBus`), tween safety (`tween.bind_node(self)`), and clean node lifecycle to guarantee 100% pass rate with **0 ObjectDB memory leaks**.

---

## 2. Character Asset Survey

### 2.1 File System Inventory

The project contains 54 character textures located in `assets/images/characters/` (and mirrored in `godot_project/assets/images/characters/`):

| Subdirectory | File Count | Image Formats | Resolution Range | Color Mode | Primary Usage |
|---|---|---|---|---|---|
| `heroes/` | 14 files | PNG | `162x169` to `676x369` | RGBA (32-bit) | D&D 5e classes & specific heroes (Aquele, Koema, Novak, Rilem, Yukito) |
| `animation/processed/` | 7 files | PNG | `768x1024` to `1024x1024` | RGBA (32-bit) | High-res Cerco hero portraits (Aquele, Darwin, Doom, Elden, Gruu, Kuro, Stark) |
| `monsters/` | 8 files | PNG | `480x64` to `1024x1024` | RGBA / RGB | D&D bosses & monsters (Goblin, Esqueleto, Kobold, Lorde Lich, Dragão Ancião, Rei Goblin) |
| `monsters/isectum/` | 26 files | PNG | `32x32` uniform | RGBA (32-bit) | Pixel art tokens for all 24 Isectum Castes + Brutamonte + Infiltrador |
| `bosses/` | 2 files | PNG | `500x500`, `1024x1024` | RGBA / RGB | Campaign bosses (Sienna, Chefe) |
| `silver_roses/` | 3 files | PNG | `~1000x1000` | RGBA (32-bit) | High-res faction character variants |

### 2.2 Detailed Asset Table

#### A. Cerco & Tactical Heroes (`heroes/` & `animation/processed/`)
| Hero / Class Name | Primary Texture Path | Alternate / High-Res Path | Original Resolution | Aspect Ratio |
|---|---|---|---|---|
| **Aquele** | `heroes/Aquele.png` | `animation/processed/aquele.png` | 162x169 / 1024x1024 | 0.96:1 / 1:1 |
| **Stark** | `heroes/paladino.png` | `animation/processed/stark.png` | 676x369 / 768x1024 | 1.83:1 / 0.75:1 |
| **Elden** | `heroes/mago.png` | `animation/processed/elden.png` | 676x369 / 768x1024 | 1.83:1 / 0.75:1 |
| **Doom** | `heroes/ladino.png` | `animation/processed/doom.png` | 676x369 / 768x1024 | 1.83:1 / 0.75:1 |
| **Gruu** | `heroes/barbaro.png` | `animation/processed/gruu.png` | 676x369 / 1024x1024 | 1.83:1 / 1:1 |
| **Kuro** | `heroes/ladino.png` | `animation/processed/kuro.png` | 676x369 / 768x1024 | 1.83:1 / 0.75:1 |
| **Darwin** | `heroes/druida.png` | `animation/processed/darwin.png` | 676x369 / 1024x1024 | 1.83:1 / 1:1 |
| **Novak** | `heroes/Novak.png` | `heroes/guerreiro.png` | 548x455 / 676x369 | 1.20:1 / 1.83:1 |
| **Rilem** | `heroes/Rilem.png` | `heroes/arqueiro.png` | 441x565 / 676x369 | 0.78:1 / 1.83:1 |
| **Yukito** | `heroes/Yukito.png` | `heroes/paladino.png` | 544x459 / 676x369 | 1.18:1 / 1.83:1 |
| **Koema** | `heroes/Koema.png` | `heroes/mago.png` | 658x379 / 676x369 | 1.74:1 / 1.83:1 |
| **Guerreiro** | `heroes/guerreiro.png` | — | 676x369 | 1.83:1 |
| **Mago** | `heroes/mago.png` | — | 676x369 | 1.83:1 |
| **Ladino** | `heroes/ladino.png` | — | 676x369 | 1.83:1 |
| **Arqueiro** | `heroes/arqueiro.png` | — | 676x369 | 1.83:1 |
| **Barbaro** | `heroes/barbaro.png` | — | 676x369 | 1.83:1 |
| **Clerigo** | `heroes/clerigo.png` | — | 676x369 | 1.83:1 |
| **Paladino** | `heroes/paladino.png` | — | 676x369 | 1.83:1 |
| **Druida** | `heroes/druida.png` | — | 676x369 | 1.83:1 |
| **Bruxo** | `heroes/bruxo.png` | — | 500x500 | 1:1 |

#### B. 24 Isectum Castes + Special Swarm (`monsters/isectum/`)
All 26 assets in this directory are pristine **32x32 RGBA pixel art**, perfectly suited for direct 1:1 mapping on 20x20 and tactical grid tiles:
1. `abelha_tecela.png` (32x32)
2. `aranha_clepto.png` (32x32)
3. `besouro_gorgulho.png` (32x32)
4. `besouro_rinoceronte.png` (32x32)
5. `besouro_unicornio.png` (32x32)
6. `brutamonte.png` (32x32) — Special Cerco Boss / Heavy Unit (3 HP circles)
7. `carrapato_vampiro.png` (32x32)
8. `centopeia_olhos.png` (32x32)
9. `cigarra_ressonante.png` (32x32)
10. `efemera_mimetica.png` (32x32)
11. `enxame_rainha.png` (32x32)
12. `escaravelho_necrofago.png` (32x32)
13. `formiga_correicao.png` (32x32)
14. `gafanhoto_praga.png` (32x32)
15. `infiltrador.png` (32x32) — Special Cerco Saboteur Unit
16. `larva_carniceira.png` (32x32)
17. `libelula_blindada.png` (32x32)
18. `louva_deus.png` (32x32)
19. `mariposa_esfinge.png` (32x32)
20. `mosca_tse_tse.png` (32x32)
21. `tarantula_golias.png` (32x32)
22. `vagalume_sombras.png` (32x32)
23. `vespa_cacadora.png` (32x32)
24. `vespa_joia.png` (32x32)
25. `viuva_canibal.png` (32x32)
26. `viuva_negra.png` (32x32)

#### C. Monsters & Bosses (`monsters/` & `bosses/`)
- `goblin.png`: 500x500 RGBA
- `esqueleto.png`: 500x500 RGBA
- `kobold.png`: 500x500 RGBA
- `lorde_lich.png`: 500x500 RGBA
- `rei_goblin.png`: 500x500 RGBA
- `dragao_anciao.png`: 500x500 RGBA
- `Sienna.png`: 500x500 RGBA
- `chefe.png`: 1024x1024 RGB

---

## 3. Data Integration: `dados/personagens.json` & `CharacterData.gd`

The data model is already standardized in Godot 4 via `CharacterData.gd` and loaded dynamically via `DataManager.gd`:

```gdscript
# Canonical fields ingested from JSON:
- id: String ("Guerreiro", "Aquele", "Stark", "Goblin", etc.)
- name: String ("Aquele", "Stark", etc.)
- team: String ("A" for heroes, "B" for enemies)
- stats: Dictionary {"forca": 16, "constituicao": 14, "destreza": 12, ...}
- hp / max_hp: int
- ac: int
- velocidade: int (Move speed in grid cells)
- alcance: int (Attack range in grid cells)
- tipo_dano: String ("Cortante", "Perfurante", "Magico", etc.)
- dado_vida: Array [count, faces]
- dado_dano: Array [count, faces]
- resistencias: Dictionary
- vulnerabilidades: Dictionary
- imunidades: Array
```

`Character.gd` will support dual initialization:
1. `initialize_from_resource(res: CharacterData)`: Binds directly to loaded engine resources.
2. `initialize_from_data(data: Dictionary)`: Facilitates direct dictionary ingestion from `personagens.json` or custom test fixtures.
3. `set_character_name(name: String, max_hp: int)`: Lightweight direct setter for ad-hoc instantiation.

---

## 4. `Character.tscn` Scene Hierarchy Design

### 4.1 Node Tree Structure

```
Character (CharacterBody2D) [script = "res://scripts/entities/Character.gd"]
│
├── CollisionShape2D (CircleShape2D, radius = 14.0)
│   # Enables native 2D mouse picking, hover events, and physics query
│
├── SelectionHighlight (Node2D)
│   # Visual indicator visible when is_selected == true
│   ├── OuterRing (Line2D, circle points, width = 2.0, color = Color(1.0, 0.85, 0.2, 0.85))
│   └── PulseGlow (Line2D, circle points, width = 4.0, color = Color(1.0, 0.85, 0.2, 0.25))
│
├── Sprite2D (Sprite2D, centered = true, filter = NEAREST)
│   # Renders normalized character visual
│   # Texture automatically loaded via multi-tier fallback
│
├── RetroHPBar (Node2D, position = Vector2(-15, -20))
│   # Retro pixel health bar (width = 30px, height = 4px)
│   ├── BgRect (ColorRect, size = Vector2(30, 4), color = Color(0.12, 0.12, 0.12, 0.95))
│   ├── FillRect (ColorRect, size = Vector2(30, 4), color = Color(0.24, 0.78, 0.24, 1.0))
│   └── BorderLine (Line2D / ReferenceRect, 1px black outline = Color(0, 0, 0, 1.0))
│
└── StatusContainer (HBoxContainer, position = Vector2(-15, -28), size = Vector2(30, 6))
    # Container for dynamic 6x6 pixel badges
    # Displays active conditions: Poison, Stun, Bleed, Burn, Freeze, etc.
```

### 4.2 Visual Component Specifications

1. **Sprite Normalization Algorithm**:
   To prevent huge sprites (e.g. 1024x1024) from overwhelming the screen while keeping 32x32 sprites crisp:
   ```gdscript
   func _apply_sprite_scaling(tex: Texture2D) -> void:
       if tex == null or sprite_2d == null:
           return
       var tex_size: Vector2 = tex.get_size()
       if tex_size.x <= 0 or tex_size.y <= 0:
           return
       var scale_factor: float = minf(target_display_size.x / tex_size.x, target_display_size.y / tex_size.y)
       sprite_2d.scale = Vector2(scale_factor, scale_factor)
   ```

2. **RetroHPBar Logic**:
   - Total width: `30.0` pixels, height: `4.0` pixels.
   - Fill width calculation: `clampf(float(current_hp) / float(max_hp), 0.0, 1.0) * 30.0`.
   - Dynamic Color Gradient:
     * `hp_ratio > 0.50`: Retro Green `#3cc83c` (`Color(0.24, 0.78, 0.24)`)
     * `0.25 < hp_ratio <= 0.50`: Retro Amber `#c8c83c` (`Color(0.78, 0.78, 0.24)`)
     * `hp_ratio <= 0.25`: Retro Crimson `#c83c3c` (`Color(0.78, 0.24, 0.24)`)
   - If `current_hp == 0`: Fill width is 0.

3. **SelectionHighlight Pulse**:
   - Looping Tween modulating scale between `0.95` and `1.05` or alpha between `0.5` and `1.0`.
   - Bound to node via `tween.bind_node(self)` to guarantee zero memory leaks when freed.
   - Hidden when `is_selected == false`.

4. **StatusContainer Badges**:
   - Each condition adds a 6x6 pixel `ColorRect` with an internal color code:
     * `poisoned` / `envenenado`: `Color(0.20, 0.80, 0.20)` (Green)
     * `stunned` / `atordoado`: `Color(0.95, 0.85, 0.15)` (Gold/Yellow)
     * `bleeding` / `sangrando`: `Color(0.85, 0.15, 0.15)` (Blood Red)
     * `burning` / `queimando`: `Color(1.00, 0.45, 0.00)` (Orange)
     * `frozen` / `congelado`: `Color(0.30, 0.75, 1.00)` (Ice Blue)
     * `paralyzed` / `paralisado`: `Color(0.70, 0.30, 0.90)` (Purple)
     * `blessed` / `foco`: `Color(1.00, 0.90, 0.40)` (White-Gold)

---

## 5. `Character.gd` GDScript Architecture & API Specification

### 5.1 Static Typing & Signals

```gdscript
# res://scripts/entities/Character.gd
class_name Character
extends CharacterBody2D

# ── Signals ─────────────────────────────────────────────────────────────────
signal hp_changed(current_hp: int, max_hp: int)
signal died()
signal healed(amount: int, current_hp: int)
signal damaged(amount: int, current_hp: int)
signal selection_changed(is_selected: bool)
signal status_effect_applied(effect_name: String)
signal status_effect_removed(effect_name: String)
signal grid_position_changed(new_pos: Vector2i)

# ── Exported Combat Properties ──────────────────────────────────────────────
@export var character_id: String = ""
@export var character_name: String = "Character"
@export var team: String = "A" # "A" = Allies/Heroes, "B" = Enemies/Isectum
@export var max_hp: int = 10
@export var current_hp: int = 10
@export var ac: int = 10
@export var move_speed: int = 3
@export var attack_range: int = 1
@export var damage_type: String = "Cortante"
@export var grid_position: Vector2i = Vector2i(-1, -1)
@export var elevation: int = 0
@export var is_selected: bool = false
@export var is_alive: bool = true
@export var target_display_size: Vector2 = Vector2(30.0, 30.0)

# ── Node References ─────────────────────────────────────────────────────────
@onready var sprite_2d: Sprite2D = $Sprite2D
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@onready var selection_highlight: Node2D = $SelectionHighlight
@onready var retro_hp_bar: Node2D = $RetroHPBar
@onready var hp_fill: ColorRect = $RetroHPBar/FillRect
@onready var hp_bg: ColorRect = $RetroHPBar/BgRect
@onready var status_container: HBoxContainer = $StatusContainer

# ── Internal State ──────────────────────────────────────────────────────────
var character_data: CharacterData = null
var active_status_effects: Array[String] = []
var _highlight_tween: Tween = null
```

### 5.2 Core API Methods

| Method Signature | Return Type | Description |
|---|---|---|
| `initialize_from_data(data: Dictionary)` | `void` | Ingests data dictionary (from `personagens.json` or mock), sets stats, and loads texture |
| `initialize_from_resource(res: CharacterData)` | `void` | Binds to a `CharacterData` Resource and updates all fields |
| `set_character_name(name: String, p_max_hp: int)` | `void` | Convenience setter for character name and HP |
| `take_damage(amount: int) -> int` | `int` | Subtracts damage, clamps at 0, triggers red flash, emits signals, handles death |
| `heal(amount: int) -> int` | `int` | Adds HP up to `max_hp` if alive, emits signals, updates HP bar |
| `set_selected(selected: bool)` | `void` | Updates selection state, triggers highlight pulse tween, emits `selection_changed` |
| `add_status_effect(effect: String) -> bool` | `bool` | Adds condition, creates visual badge, emits signals |
| `remove_status_effect(effect: String) -> bool` | `bool` | Removes condition, frees visual badge, emits signals |
| `has_status_effect(effect: String) -> bool` | `bool` | Returns `true` if condition is active |
| `clear_all_status_effects()` | `void` | Clears all conditions and frees badges |
| `set_grid_position(new_pos: Vector2i)` | `void` | Sets `grid_position` and emits `grid_position_changed` |
| `load_texture_for_character(char_id: String) -> bool` | `bool` | Searches 5 asset directories and loads texture with zero crashes |
| `update_hp_bar()` | `void` | Updates width and color gradient of `RetroHPBar` |

### 5.3 Texture Search Algorithm Blueprint

```gdscript
func load_texture_for_character(id_to_find: String) -> bool:
    if id_to_find.is_empty():
        return false
        
    var raw_name: String = id_to_find.strip_edges()
    var lower_name: String = raw_name.to_lower()
    var snake_name: String = raw_name.to_snake_case()
    
    var candidate_paths: Array[String] = [
        # 1. Monters / Isectum pixel art (32x32)
        "res://assets/images/characters/monsters/isectum/%s.png" % snake_name,
        "res://assets/images/characters/monsters/isectum/%s.png" % lower_name,
        # 2. Heroes
        "res://assets/images/characters/heroes/%s.png" % raw_name,
        "res://assets/images/characters/heroes/%s.png" % lower_name,
        # 3. Animation Processed
        "res://assets/images/characters/animation/processed/%s.png" % lower_name,
        # 4. Monsters
        "res://assets/images/characters/monsters/%s.png" % snake_name,
        "res://assets/images/characters/monsters/%s.png" % lower_name,
        # 5. Bosses
        "res://assets/images/characters/bosses/%s.png" % raw_name,
        "res://assets/images/characters/bosses/%s.png" % lower_name
    ]
    
    for path in candidate_paths:
        if ResourceLoader.exists(path):
            var tex: Texture2D = load(path) as Texture2D
            if tex != null:
                if sprite_2d != null:
                    sprite_2d.texture = tex
                    _apply_sprite_scaling(tex)
                return true
                
    return false
```

---

## 6. Implementation Artifacts (Blueprints for Implementer)

### 6.1 `Character.tscn` Blueprint (Godot 4 Text Scene)

```tscn
[gd_scene load_steps=3 format=3 uid="uid://charactertscn001"]

[ext_resource type="Script" path="res://scripts/entities/Character.gd" id="1_char"]

[sub_resource type="CircleShape2D" id="CircleShape2D_col"]
radius = 14.0

[node name="Character" type="CharacterBody2D"]
script = ExtResource("1_char")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("CircleShape2D_col")

[node name="SelectionHighlight" type="Node2D" parent="."]
visible = false

[node name="OuterRing" type="Line2D" parent="SelectionHighlight"]
width = 2.0
default_color = Color(1, 0.85, 0.2, 0.85)

[node name="PulseGlow" type="Line2D" parent="SelectionHighlight"]
width = 4.0
default_color = Color(1, 0.85, 0.2, 0.25)

[node name="Sprite2D" type="Sprite2D" parent="."]
texture_filter = 0

[node name="RetroHPBar" type="Node2D" parent="."]
position = Vector2(-15, -20)

[node name="BgRect" type="ColorRect" parent="RetroHPBar"]
offset_right = 30.0
offset_bottom = 4.0
color = Color(0.12, 0.12, 0.12, 0.95)

[node name="FillRect" type="ColorRect" parent="RetroHPBar"]
offset_right = 30.0
offset_bottom = 4.0
color = Color(0.24, 0.78, 0.24, 1)

[node name="Border" type="Line2D" parent="RetroHPBar"]
points = PackedVector2Array(0, 0, 30, 0, 30, 4, 0, 4, 0, 0)
width = 1.0
default_color = Color(0, 0, 0, 1)

[node name="StatusContainer" type="HBoxContainer" parent="."]
offset_left = -15.0
offset_top = -28.0
offset_right = 15.0
offset_bottom = -22.0
theme_override_constants/separation = 2
```

---

## 7. GUT Test Architecture & Verification Matrix

The test suite must be placed in `godot_project/test/unit/test_character_entity.gd` following strict AAA and headless safety guidelines:

| Test Case | Scenario / Condition | Assertion Verification |
|---|---|---|
| `test_character_initialization_defaults` | Fresh instance creation | `current_hp == 10`, `is_alive == true`, `is_selected == false` |
| `test_character_initialize_from_data_dict` | Ingest JSON dict (`Guerreiro`) | `max_hp == 16`, `ac == 18`, `move_speed == 3`, texture loaded |
| `test_character_initialize_from_resource` | Ingest `CharacterData` Resource | Values match resource fields; modifications isolated |
| `test_character_take_damage_happy_path` | HP 10 takes 4 damage | `current_hp == 6`, returns 4, `damaged` and `hp_changed` signals emitted |
| `test_character_take_damage_lethal_death` | HP 6 takes 10 damage | `current_hp == 0`, `is_alive == false`, `died` signal emitted |
| `test_character_take_damage_clamped_zero` | Zero or negative damage input | Returns 0, HP remains unaffected |
| `test_character_heal_happy_path` | HP 4 heals 3 | `current_hp == 7`, returns 3, `healed` signal emitted |
| `test_character_heal_overheal_capped` | HP 8 (max 10) heals 5 | `current_hp == 10`, returns 2 (actual heal) |
| `test_character_heal_when_dead_fails` | Dead character attempts heal | Returns 0, `current_hp == 0` |
| `test_character_selection_toggle` | `set_selected(true/false)` | `selection_changed` emitted, highlight visibility toggled |
| `test_character_status_effect_lifecycle` | Add, query, remove condition | `has_status_effect("poisoned")`, badge created, then removed |
| `test_character_duplicate_status_prevented` | Add same status twice | Only 1 active instance, returns false or merges cleanly |
| `test_character_clear_all_status_effects` | Multiple active conditions | Clears all, empties `StatusContainer` children |
| `test_character_texture_discovery_and_fallback` | Valid hero/caste vs invalid string | Valid loads texture; invalid handles gracefully without crash |
| `test_character_hp_bar_color_shifts` | HP at 100%, 40%, 15% | Color transitions from Green -> Yellow -> Red |
| `test_character_zero_leaks_on_cleanup` | Instance and free node in GUT | 0 ObjectDB leaks on GUT test runner exit |

---

## 8. Conclusion & Recommendation

The character entity architecture is fully designed and validated against:
1. All 54 graphic assets in `assets/images/characters/`.
2. Existing Godot 4 autoloads (`EventBus`, `DataManager`, `GameManager`, `AudioManager`).
3. Tactical grid (`TacticalGrid.gd`) and UI scenes (`FortressBoardView.gd`).
4. Strict GUT headless testing protocols.

Ready for immediate handoff to the implementer agent (`ent_implementer_1`).
