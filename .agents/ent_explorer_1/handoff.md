# Handoff Report: Character Asset Survey & Entity Architecture

**Agent**: `ent_explorer_1`  
**To**: `parent` (Orchestrator) / `ent_implementer_1` (Implementer)  
**Date**: 2026-10-01  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

1. **Character Asset Inventory & Resolutions**:
   A comprehensive survey of `assets/images/characters/` (mirrored in `godot_project/assets/images/characters/`) via directory listing and Python image inspection confirmed:
   - `assets/images/characters/monsters/isectum/`: Exactly 26 files, all **uniform 32x32 RGBA pixels**. Covers all 24 canonical Isectum castes (`abelha_tecela.png`, `aranha_clepto.png`, `besouro_gorgulho.png`, `besouro_rinoceronte.png`, `besouro_unicornio.png`, `carrapato_vampiro.png`, `centopeia_olhos.png`, `cigarra_ressonante.png`, `efemera_mimetica.png`, `enxame_rainha.png`, `escaravelho_necrofago.png`, `formiga_correicao.png`, `gafanhoto_praga.png`, `larva_carniceira.png`, `libelula_blindada.png`, `louva_deus.png`, `mariposa_esfinge.png`, `mosca_tse_tse.png`, `tarantula_golias.png`, `vagalume_sombras.png`, `vespa_cacadora.png`, `vespa_joia.png`, `viuva_canibal.png`, `viuva_negra.png`) plus special Cerco units `brutamonte.png` (32x32) and `infiltrador.png` (32x32).
   - `assets/images/characters/heroes/`: 14 files, RGBA:
     * `Aquele.png` (162x169)
     * `Koema.png` (658x379), `Novak.png` (548x455), `Rilem.png` (441x565), `Yukito.png` (544x459)
     * Class textures: `guerreiro.png`, `mago.png`, `ladino.png`, `arqueiro.png`, `barbaro.png`, `clerigo.png`, `paladino.png`, `druida.png` (all 676x369), and `bruxo.png` (500x500).
   - `assets/images/characters/animation/processed/`: 7 high-resolution RGBA portraits:
     * `aquele.png`, `darwin.png`, `gruu.png` (1024x1024)
     * `doom.png`, `elden.png`, `kuro.png`, `stark.png` (768x1024).
   - `assets/images/characters/monsters/`: 8 files:
     * `dragao_anciao.png`, `esqueleto.png`, `goblin.png`, `kobold.png`, `lorde_lich.png`, `rei_goblin.png` (all 500x500 RGBA).
     * `ItemsInsectA.png` (480x64), `isectum_spritesheet.png` (1024x1024).
   - `assets/images/characters/bosses/`: `Sienna.png` (500x500 RGBA), `chefe.png` (1024x1024 RGB).

2. **Data Definitions (`dados/personagens.json`)**:
   Contains 26 structured definitions with `stats` (força, constituicao, destreza, inteligencia, sabedoria, carisma), `ac`, `dado_vida`, `dado_dano`, `velocidade`, `alcance`, `tipo_dano`, and optional `hp`, `resistencias`, `vulnerabilidades`, `imunidades`.

3. **Existing Godot Engine Scripts**:
   - `godot_project/scripts/resources/CharacterData.gd`: Implements the canonical Resource model for characters with getters `get_modifier`, `get_proficiency_bonus`, `sync_stats_dict`, and `duplicate_data`.
   - `godot_project/scripts/autoload/DataManager.gd`: Parses `personagens.json` into `CharacterData` instances cached in `_characters_cache`.
   - `godot_project/scripts/combat/StatusManager.gd`: Defines canonical 5e and tactical conditions (`poisoned`, `stunned`, `bleeding`, `burning`, `frozen`, `paralyzed`, `blessed`, etc.).
   - `godot_project/scripts/autoload/EventBus.gd`: Contains global signals: `unit_moved`, `unit_attacked`, `unit_damaged`, `unit_died`, `status_applied`, `status_removed`.

4. **Pygame Reference Visual Implementation (`src/ui/render_combate.py:407-414`)**:
   Direct observation of retro health bar logic:
   ```python
   hp_percent = p.hp_atual / p.hp_max
   hp_bar_bg = pygame.Rect(rect.left, rect.top - 8, 30, 4)
   pygame.draw.rect(tela, (30, 30, 30), hp_bar_bg)
   hp_color = (60, 200, 60) if hp_percent > 0.5 else (200, 200, 60) if hp_percent > 0.25 else (200, 60, 60)
   hp_bar_fg = pygame.Rect(rect.left, rect.top - 8, int(30 * hp_percent), 4)
   pygame.draw.rect(tela, hp_color, hp_bar_fg)
   pygame.draw.rect(tela, (0, 0, 0), hp_bar_bg, 1)
   ```

5. **Headless GUT Testing Environment**:
   Verified execution via `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`:
   - 15 test scripts executed.
   - 463 tests run, 463 tests passed (100% pass rate, exit code 0, 0 ObjectDB memory leaks).

---

## 2. Logic Chain

1. **Resolution Normalization Requirement**:
   From Observation 1, asset resolutions range widely from 32x32 to 1024x1024. If rendered without dynamic scaling, high-res portraits would dominate the 20x20 tactical board. Therefore, `Character.gd` must calculate `scale_factor = min(target_display_size.x / tex_size.x, target_display_size.y / tex_size.y)` to normalize all textures to a standard display box (`Vector2(30.0, 30.0)` or `Vector2(32.0, 32.0)`).

2. **Root Node Selection (`CharacterBody2D`)**:
   From Observation 1 and 3, characters occupy cells on `TacticalGrid.gd` and require mouse selection picking. `CharacterBody2D` with an attached `CollisionShape2D` (`CircleShape2D` radius 14.0) provides native picking, physics query, and motion smoothing while maintaining zero overhead in headless tests.

3. **Visual Parity Replicating Pygame Mechanics**:
   From Observation 4:
   - `RetroHPBar` must be positioned at `Vector2(-15, -20)`, with dimensions 30x4 px.
   - Background rect: `#1e1e1e` (`Color(0.12, 0.12, 0.12, 0.95)`).
   - Border: 1px black outline `#000000`.
   - Fill thresholds: Green (`#3cc83c`) when HP > 50%, Amber (`#c8c83c`) when 25% < HP ≤ 50%, Crimson (`#c83c3c`) when HP ≤ 25%.
   - `SelectionHighlight`: Node2D with circular line ring that pulses via Tween when `is_selected == true` and hides when false.
   - `StatusContainer`: Positioned at `Vector2(-15, -28)`, dynamically adding 6x6 pixel color-coded badges for active status effects (`poisoned`, `stunned`, `bleeding`, etc.).

4. **Multi-Tier Asset Search Algorithm**:
   From Observation 1, textures for different unit types reside in disparate folders. The method `load_texture_for_character(char_id)` must search candidate paths in precedence:
   1. `monsters/isectum/<snake_name>.png` (Cerco insects)
   2. `heroes/<name>.png` / `heroes/<lower_name>.png` (Tactical heroes)
   3. `animation/processed/<lower_name>.png` (High-res heroes)
   4. `monsters/<name>.png` (Monsters)
   5. `bosses/<name>.png` (Bosses)
   If none are found, fallback gracefully without throwing errors or crashing.

5. **Headless Safety and Memory Discipline**:
   From Observation 5, all GUT tests must run headless with 0 ObjectDB leaks. Any tweens instantiated in `Character.gd` (such as selection pulse or damage red-flash) must be bound to the node using `tween.bind_node(self)`. All child nodes must be safely freed.

---

## 3. Caveats

1. **Read-Only Explorer Scope**: In accordance with the Explorer persona and constraints, no production files were created or modified inside `godot_project/scenes/` or `godot_project/scripts/`. Complete, drop-in blueprints are provided in `exploration_report.md` for the implementer agent.
2. **Multi-frame Walk Animations**: While spritesheets exist in `assets/images/characters/animation/` and `isectum_spritesheet.png`, the primary requirement for the tactical and Cerco fortress board is token-based rendering with directional facing and tween-based interpolation. Full animated sprite sheets can be layered later via `AnimatedSprite2D` if desired, without changing the public API of `Character.gd`.
3. **Godot Binary Location**: The system PATH does not include `godot`, but the canonical executable is located at `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot` (or `./bin/godot` within `godot_project/`).

---

## 4. Conclusion

The character asset survey, data mapping, and architectural designs for `Character.tscn` and `Character.gd` are completely resolved.

- **Scene File**: `res://scenes/entities/Character.tscn`
  - Hierarchy: `Character (CharacterBody2D)` -> `CollisionShape2D`, `SelectionHighlight`, `Sprite2D`, `RetroHPBar`, `StatusContainer`.
- **Script File**: `res://scripts/entities/Character.gd`
  - Fully typed GDScript with complete API (`initialize_from_data`, `take_damage`, `heal`, `set_selected`, `add_status_effect`, `remove_status_effect`, `has_status_effect`, `load_texture_for_character`, `update_hp_bar`).
  - Signals: `hp_changed`, `died`, `healed`, `damaged`, `selection_changed`, `status_effect_applied`, `status_effect_removed`, `grid_position_changed`.
  - Integration with `EventBus` signals.
- **Detailed Report**: Delivered at `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/exploration_report.md`.

---

## 5. Verification Method

To independently verify all observations and the GUT testing environment:

1. **Verify Asset Inventory**:
   ```bash
   ls -la assets/images/characters/heroes/
   ls -la assets/images/characters/monsters/isectum/
   ls -la assets/images/characters/animation/processed/
   ```

2. **Verify Existing GUT Test Suite**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
   ```
   *Expected outcome*: Exit code 0, 463 tests run, 463 tests passed, 0 ObjectDB leaks.

3. **Verify Exploration Artifacts**:
   - Inspect `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/exploration_report.md`
   - Inspect `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/handoff.md`
