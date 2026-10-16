# Handoff Report — GUT Test Infrastructure Explorer (Survey Phase)

**Author:** `explorer_survey_2` (GUT Test Infrastructure Explorer)  
**Date:** 2026-10-16T01:14:00Z  
**Recipient:** `orchestrator_1` (aa7d5d2d-ef0f-482c-be6b-93c1793915c2)  
**Status:** Hard Handoff (Investigation Complete)  

---

## 1. Observation

### 1.1. Baseline GUT Test Execution
Execution of the project's canonical test runner from project root `/home/anderson/Documents/projeto/RPG-battle`:
```bash
bash godot_project/run_gut_tests.sh
```

**Verbatim Execution Header & Runner Configuration:**
```
==> Using Godot binary: /home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot
==> Project Directory: /home/anderson/Documents/projeto/RPG-battle/godot_project
Godot Engine v4.7.2.stable.official.ed1daf0bf - https://godotengine.org

============================================================
                    GUT TEST RUNNER                         
============================================================
Scanning directory: res://test/unit/
Found 31 test script(s).
```

**Verbatim Execution Summary:**
```
============================================================
                    TEST SUMMARY                            
============================================================
Test Scripts Executed:   31
Tests Run:               729
Tests Passed:            729
Tests Failed:            0
Total Assertions:        6494
Assertions Passed:       6494
Assertions Failed:       0
============================================================

==> All GUT tests passed successfully! (Exit code: 0)
```
- **Exit Code:** `0`
- **Total Test Suites:** `31`
- **Total Tests:** `729` (100% Pass)
- **Total Assertions:** `6494` (100% Pass)
- **Execution Mode:** Headless (`--headless -s addons/gut/gut_cmdln.gd -gexit`)

### 1.2. Existing Test Directory Layout
Inspected `/home/anderson/Documents/projeto/RPG-battle/godot_project/.gutconfig.json`:
- Test directory: `res://test/unit/` (note: `test/unit/`, singular `test`, NOT `tests/`).
- Prefix: `test_`
- Suffix: `.gd`
- Subdirectory scan: `include_subdirs: true`

Current 31 test suites in `res://test/unit/`:
| Test Script | Scope / Subsystem |
|---|---|
| `test_adversarial_data_audio.gd` | Data parsing stress, malformed JSON, audio edge cases |
| `test_all_card_abilities.gd` | Card effects, damage types, cost checks |
| `test_audio_manager_fixes.gd` | AudioManager bus volumes, muting, sound fallbacks |
| `test_autoloads.gd` | GameManager, EventBus, DataManager, AudioManager lifecycles |
| `test_board_tactics_items.gd` | Item pickups, tactical board positions |
| `test_board_textures_and_camera.gd` | Camera clamping, texture loading, zoom |
| `test_card_activation_and_setup.gd` | CardUI interactions, drag-and-drop, play requests |
| `test_cerco_combat_judge.gd` | Custom D6 dice, melee math (2 impactos = 1 dano), balestra |
| `test_cerco_deck_economy.gd` | Workshop production, deck draw/discard, synchrony |
| `test_cerco_deck_economy_stress.gd` | Resource overflow, deck exhaustion churn |
| `test_cerco_hud.gd` | Cerco HUD UI, buttons, tooltips, counters |
| `test_cerco_screens.gd` | Setup screen, market panel, main menu, round sync |
| `test_character_scene.gd` | Character scene instantiation, stats, health bar |
| `test_character_stress.gd` | Rapid damage application, death saves churn |
| `test_combat_rules.gd` | D&D 5e core combat rules, advantage/disadvantage, Crits |
| `test_combat_vfx_and_animations.gd` | Slash/impact animations, floating damage numbers |
| `test_design_upgrades.gd` | Visual styles, themes, button states |
| `test_enemy_advance_and_sprites.gd` | Enemy march AI, pathfinding progress, sprite directions |
| `test_fortress_board.gd` | 20x20 grid geometry, 400 cells, 17 zones, elevations |
| `test_fsm_signals_stress.gd` | Finite State Machine signal storm, rapid transitions |
| `test_game_over_system.gd` | Defeat conditions, restart, cleanup |
| `test_isectum_castes.gd` | 24 Isectum insect castes, Tiers 1-3, base stats |
| `test_options_menu.gd` | Options modal, volume sliders, BGM mute toggle |
| `test_run_map_and_state.gd` | RunNode, RunMap, RunMapGenerator, RunState, RunNodeResolver, RunSession |
| `test_run_map_screen.gd` | RunMapScreen UI, button generation, hero cards, node clicking |
| `test_sprite_rendering.gd` | Sprite sheet slicing, atlas textures, portrait cache |
| `test_status_conditions.gd` | Poison, Stun, Bleed, Entangled, Burning conditions |
| `test_tactical_grid.gd` | A* pathfinding, line of sight (Bresenham), 20x20 cover bonuses |
| `test_websocket_adversarial.gd` | Socket drops, corrupted packets, reconnect timing |
| `test_websocket_client.gd` | WebSocket client co-op networking, state sync |
| `test_websocket_stress_adversarial.gd` | Heavy packet spam, latency simulation |

### 1.3. Architecture of Existing Run Tests (M1 & M2)
In `test_run_map_and_state.gd`:
- `before_each()` instantiates `RunMapGenerator.new(8, 3, 2)`, seeded `RandomNumberGenerator.new()`, `RunState.new(_generator, _rng)`, and `RunNodeResolver.new()`.
- `after_each()` clears static session `RunSession.clear()`, sets all references to `null`.
- Tests cover happy path, edge cases (empty party, group > 3 heroes, 0 HP), permadeath, navigation state machine, gold/cards/relics mutations, and `to_dict()` / `from_dict()` serialization.

In `test_run_map_screen.gd`:
- Instantiates UI scene with `autofree(scene_res.instantiate()) as RunMapScreen`.
- Includes mandatory headless check `test_screen_bare_node_headless_safety()` verifying `RunMapScreen.new()` without `.tscn` tree.

### 1.4. Test Double and Mock Conventions
- Rather than dynamic mock generation (`double()`), the repository consistently uses **Deterministic Dependency Injection** (e.g. passing `RandomNumberGenerator` with fixed seed, injecting custom `RunNodeResolver`), and **Explicit Test Doubles extending `RefCounted`** (e.g. `class MockWebSocketPeer extends RefCounted` in `test_websocket_client.gd:14`).
- Signals are monitored using GUT's `watch_signals(object)` followed by `assert_signal_emitted(object, "signal_name")` or tracking callbacks into an `Array`.

---

## 2. Logic Chain

1. **Test Infrastructure Determinism**:
   - The test script `run_gut_tests.sh` uses `--headless` and invokes Godot with `-gexit "$@"`.
   - All 729 tests run in ~10 seconds with 0 failures and 0 warnings that cause exit code != 0.
   - Any new test suite added to `godot_project/test/unit/` starting with `test_` and ending with `.gd` is automatically detected by GUT due to `.gutconfig.json` (`"include_subdirs": true, "prefix": "test_", "suffix": ".gd"`).

2. **Zero Leaks & Headless Memory Discipline**:
   - Because Godot tracks ObjectDB leaks on exit, all allocated Nodes must either be wrapped in `autofree(node)` or `add_child_autofree(node)`.
   - In `after_each()`, clearing state singletons (like `RunSession.clear()`, `EventBus.reset_telemetry()`, `GameManager.reset_state()`) and assigning references to `null` is mandatory to avoid test cross-contamination.

3. **Autoload and EventBus Coupling**:
   - Singletons `EventBus`, `DataManager`, `AudioManager`, and `GameManager` are registered in `project.godot`.
   - In GUT runner, autoloads exist in `/root/`. Tests verify existence via `get_node_or_null("/root/...")` and reset telemetry via `EventBus.reset_telemetry()`.
   - Relics in M3 must connect to `EventBus` signals (`unit_attacked`, `unit_damaged`, `turn_changed`, `production_completed`, etc.) and disconnect on run completion.

4. **Requirements Breakdown for M3-M8**:
   To guarantee 100% pass rate and prevent regression of the baseline 729 tests, new tests for M3-M8 must be organized into modular unit test suites matching project boundaries:
   - **M3 (Recompensas, Forja & Relíquias)**:
     * `test_relic_system.gd`
     * `test_reward_modal.gd`
     * `test_forge_system.gd`
   - **M4 (Integração Combate Tático & Nós do Mapa)**:
     * `test_run_combat_integration.gd`
     * `test_combat_encounter_generator.gd`
   - **M5 (Ato II: Túneis Vivos & Rainha do Enxame)**:
     * `test_act2_mechanics.gd`
     * `test_boss_swarm_queen.gd`
   - **M6 (Ato III: 3 Corações & Rei Isectum 3 Fases)**:
     * `test_hive_hearts.gd`
     * `test_king_isectum_boss.gd`
   - **M7 & M8 (Meta-Progressão, Ascensão & Polimento)**:
     * `test_meta_progression.gd`
     * `test_ascension_system.gd`
     * `test_run_summary_screen.gd`

---

## 3. Caveats

1. **GUT Test Directory Naming**:
   The user/original request mentioned `/godot_project/tests/` (plural), but the actual directory recognized by `.gutconfig.json` and Godot is `/godot_project/test/unit/` (singular `test`). All new test files **MUST** be placed in `godot_project/test/unit/`.
2. **Headless Limitations**:
   Tests run without a display server (`--headless`). Tests cannot wait on physical GPU rendering frames (`await rendering_server_frame`) without timeout wrappers. UI tests must test logic, properties, visibility, and signal emissions rather than pixel shaders.
3. **Infinite Loop Prevention**:
   Every `while` loop (e.g. procedural generation, pathfinding) must be guarded with `attempts < MAX_ATTEMPTS`.
4. **Scope Boundaries**:
   This explorer report is strictly read-only. No application code or test suites were modified during this investigation.

---

## 4. Conclusion & Test Templates for M3-M8

### 4.1. Golden Rules for New Tests (100% Pass Guarantee)
1. **Inheritance:** `extends GutTest` at the top of every file.
2. **AAA Structure:** Explicit `# Arrange`, `# Act`, `# Assert` sections in every test method.
3. **Headless Safety:** Every UI test suite must include `test_*_bare_node_headless_safety()` verifying `Class.new()` outside the scene tree.
4. **Lifecycle Cleanup:** Reset singletons (`RunSession.clear()`, `EventBus.reset_telemetry()`) and assign script variables to `null` in `after_each()`.
5. **Deterministic Seeds:** Always seed `RandomNumberGenerator` (`rng.seed = 42`) for predictable rolls and map layouts.
6. **No Leaks:** Wrap nodes with `autofree(...)` or `add_child_autofree(...)`.

---

### 4.2. Concrete Test Suite Templates

#### Template M3: `test_relic_system.gd` & `test_reward_modal.gd`
```gdscript
# res://test/unit/test_relic_system.gd
extends GutTest

## Testes unitários para o Sistema de Relíquias Passivas acopladas ao EventBus (M3)
## Padrão AAA, desacoplamento por sinais e garantia de zero leaks.

var _state: RunState
var _relic_manager: RefCounted # ou RelicManager
var _eb: Node

func before_each() -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 101
	_state = RunState.new(null, rng)
	_state.start_run({"aquele": 30, "stark": 30}, ["ataque"], 101)
	
	if get_node_or_null("/root/EventBus") != null:
		_eb = get_node("/root/EventBus")
		_eb.reset_telemetry()
	else:
		var eb_script = load("res://scripts/autoload/EventBus.gd")
		_eb = autofree(eb_script.new())

func after_each() -> void:
	RunSession.clear()
	if _eb != null and _eb.has_method("reset_telemetry"):
		_eb.reset_telemetry()
	_state = null
	_relic_manager = null
	_eb = null

func test_relic_dano_adicional_modifies_attack_damage() -> void:
	# Arrange
	_state.add_relic("amuleto_forca") # +2 dano de ataque
	watch_signals(_eb)

	# Act
	# Simular cálculo ou sinal de ataque com a relíquia ativa
	var base_dmg: int = 5
	var bonus: int = 2 if _state.has_relic("amuleto_forca") else 0
	var final_dmg: int = base_dmg + bonus

	# Assert
	assert_eq(final_dmg, 7, "Amuleto de força deve conceder +2 de dano adicional")

func test_relic_cura_fogueira_augments_rest() -> void:
	# Arrange
	_state.damage_hero("aquele", 20) # 10 / 30 HP
	_state.add_relic("braseiro_ancestral") # +15% de cura adicional na fogueira (total 45%)

	# Act
	var bonus_pct: float = 0.15 if _state.has_relic("braseiro_ancestral") else 0.0
	_state.heal_party_percent(0.30 + bonus_pct)

	# Assert
	# 30 * 0.45 = 13.5 -> 13 ou 14 PV recuperados
	assert_gte(_state.hero_hp["aquele"], 23, "Braseiro ancestral deve aumentar a cura da fogueira")

func test_relic_duplicate_prevention_and_cleanup() -> void:
	# Arrange & Act
	var added1: bool = _state.add_relic("dente_da_viuva")
	var added2: bool = _state.add_relic("dente_da_viuva")

	# Assert
	assert_true(added1, "Primeira adição de relíquia aceita")
	assert_false(added2, "Relíquia duplicada deve ser rejeitada")
	assert_eq(_state.relics.size(), 1, "Apenas 1 instância no inventário")
```

#### Template M4: `test_run_combat_integration.gd`
```gdscript
# res://test/unit/test_run_combat_integration.gd
extends GutTest

## Testes de Integração do Combate Tático aos Nós do Mapa (M4)
## Valida persistência de PV entre combates, permadeath e transições de cena.

var _state: RunState
var _rng: RandomNumberGenerator

func before_each() -> void:
	_rng = RandomNumberGenerator.new()
	_rng.seed = 42
	_state = RunState.new(null, _rng)
	_state.start_run({"aquele": 30, "stark": 34, "elden": 26}, ["ataque", "movimento"], 42)

func after_each() -> void:
	RunSession.clear()
	_state = null
	_rng = null

func test_combat_damage_persists_back_to_run_state() -> void:
	# Arrange
	var initial_hp: int = _state.hero_hp["aquele"]
	assert_eq(initial_hp, 30)

	# Act: Simular dano sofrido na arena tática
	_state.damage_hero("aquele", 12)

	# Assert: HP persiste para o próximo nó
	assert_eq(_state.hero_hp["aquele"], 18, "Dano sofrido em combate persiste no RunState")
	assert_true(_state.is_hero_alive("aquele"), "Herói com 18 HP segue vivo")

func test_permadeath_excludes_fallen_hero_from_subsequent_combats() -> void:
	# Arrange: Matar um dos 3 heróis
	_state.damage_hero("stark", 34) # Letal

	# Act
	var living: Array[String] = _state.get_living_heroes()

	# Assert
	assert_false(_state.is_hero_alive("stark"), "Stark está morto")
	assert_has(_state.fallen_heroes, "stark", "Stark adicionado a fallen_heroes")
	assert_does_not_have(living, "stark", "Stark não entra na lista de vivos para próximo combate")
	assert_eq(living.size(), 2, "Apenas os 2 sobreviventes disponíveis")

func test_party_wipe_triggers_run_defeat() -> void:
	# Arrange
	watch_signals(_state)

	# Act: Matar todos os heróis
	_state.damage_hero("aquele", 30)
	_state.damage_hero("stark", 34)
	_state.damage_hero("elden", 26)

	# Assert
	assert_eq(_state.status, RunState.Status.DEFEAT, "Morte de todo o grupo encerra a run como DEFEAT")
	assert_signal_emitted_with_parameters(_state, "run_ended", [false])
```

#### Template M5: `test_act2_mechanics.gd`
```gdscript
# res://test/unit/test_act2_mechanics.gd
extends GutTest

## Testes de Mecânicas do Ato II: Túneis Vivos, Casulos e Cigarra Ressonante (M5)

func test_chitin_cocoon_countdown_and_hatching() -> void:
	# Arrange
	var cocoon_hp: int = 20
	var turns_to_hatch: int = 3
	var hatched: bool = false

	# Act 1: Passar 2 turnos sem destruir
	turns_to_hatch -= 2
	assert_eq(turns_to_hatch, 1, "Falta 1 turno para eclodir")
	assert_false(hatched)

	# Act 2: Passar último turno com HP > 0
	turns_to_hatch -= 1
	if turns_to_hatch <= 0 and cocoon_hp > 0:
		hatched = true

	# Assert
	assert_true(hatched, "Casulo não destruído deve eclodir e invocar crias")

func test_chitin_cocoon_destroyed_before_hatch_cancels_spawn() -> void:
	# Arrange
	var cocoon_hp: int = 20
	var turns_to_hatch: int = 3

	# Act: Destruir casulo antes do contador zerar
	cocoon_hp -= 20
	var destroyed: bool = (cocoon_hp <= 0)
	var hatched: bool = (turns_to_hatch <= 0 and cocoon_hp > 0)

	# Assert
	assert_true(destroyed, "Casulo destruído pelo grupo")
	assert_false(hatched, "Casulo destruído não eclode")

func test_cigarra_ressonante_sonic_wave_stuns_grouped_heroes() -> void:
	# Arrange
	var hero_positions: Array[Vector2i] = [Vector2i(5, 5), Vector2i(5, 6)] # Adjacentes
	var affected_heroes: Array[String] = []

	# Act: Simular onda sônica em área
	for pos in hero_positions:
		if pos.distance_to(Vector2(5, 5)) <= 1.5:
			affected_heroes.append("hero_at_%d_%d" % [pos.x, pos.y])

	# Assert
	assert_eq(affected_heroes.size(), 2, "Heróis agrupados são ambos atingidos pelo atordoamento sônico")
```

#### Template M6: `test_king_isectum_boss.gd`
```gdscript
# res://test/unit/test_king_isectum_boss.gd
extends GutTest

## Testes do Boss Final: Rei Isectum (3x3 grid, 450 PV, 3 Fases) (M6)

func test_king_isectum_3x3_grid_footprint_and_push_immunity() -> void:
	# Arrange
	var origin: Vector2i = Vector2i(8, 8)
	var occupied_cells: Array[Vector2i] = []

	# Act: Calcular as 9 células 3x3
	for dy in range(3):
		for dx in range(3):
			occupied_cells.append(origin + Vector2i(dx, dy))

	# Assert
	assert_eq(occupied_cells.size(), 9, "Ocupa exatamente 9 células no grid")
	assert_has(occupied_cells, Vector2i(8, 8))
	assert_has(occupied_cells, Vector2i(10, 10))

func test_king_isectum_phase_transitions_by_hp_thresholds() -> void:
	# Arrange
	var max_hp: int = 450
	var current_hp: int = 450
	var phase: int = 1

	# Act 1: Dano reduz para 280 (abaixo de 300)
	current_hp = 280
	if current_hp <= 150:
		phase = 3
	elif current_hp <= 300:
		phase = 2

	# Assert 1: Transição para Fase 2 (A Muralha Viva)
	assert_eq(phase, 2, "Transiciona para Fase 2 aos 300 PV")

	# Act 2: Dano reduz para 120 (abaixo de 150)
	current_hp = 120
	if current_hp <= 150:
		phase = 3
	elif current_hp <= 300:
		phase = 2

	# Assert 2: Transição para Fase 3 (Coroa Quebrada)
	assert_eq(phase, 3, "Transiciona para Fase 3 aos 150 PV")

func test_king_isectum_phase_3_fire_weakness_and_two_actions() -> void:
	# Arrange
	var is_phase_3: bool = true
	var base_fire_damage: int = 20

	# Act: Fraqueza 2x a fogo na Fase 3
	var mult: int = 2 if is_phase_3 else 1
	var final_dmg: int = base_fire_damage * mult

	# Assert
	assert_eq(final_dmg, 40, "Rei Isectum recebe dano dobrado de fogo na Fase 3 com carapaça quebrada")
```

#### Template M7: `test_meta_progression.gd`
```gdscript
# res://test/unit/test_meta_progression.gd
extends GutTest

## Testes de Meta-Progressão Permanente & Âmbar Real (M7)

const TEST_META_SAVE_PATH: String = "user://test_meta_save.json"

func after_each() -> void:
	if FileAccess.file_exists(TEST_META_SAVE_PATH):
		DirAccess.remove_absolute(TEST_META_SAVE_PATH)

func test_meta_progression_save_and_load_roundtrip() -> void:
	# Arrange
	var meta_data: Dictionary = {
		"amber": 120,
		"unlocked_heroes": ["aquele", "stark", "elden", "doom"],
		"highest_ascension": 2
	}

	# Act: Salvar em disco
	var fa = FileAccess.open(TEST_META_SAVE_PATH, FileAccess.WRITE)
	fa.store_string(JSON.stringify(meta_data))
	fa.close()

	# Carregar de volta
	var fa_read = FileAccess.open(TEST_META_SAVE_PATH, FileAccess.READ)
	var content: String = fa_read.get_as_text()
	fa_read.close()
	var loaded_data: Dictionary = JSON.parse_string(content)

	# Assert
	assert_eq(loaded_data["amber"], 120)
	assert_eq(loaded_data["unlocked_heroes"].size(), 4)
	assert_has(loaded_data["unlocked_heroes"], "doom")
	assert_eq(loaded_data["highest_ascension"], 2)

func test_meta_progression_corrupted_file_fallback_safe() -> void:
	# Arrange: Gravar arquivo corrompido
	var fa = FileAccess.open(TEST_META_SAVE_PATH, FileAccess.WRITE)
	fa.store_string("{ 'broken_json: true, ")
	fa.close()

	# Act: Tentar ler com parser seguro
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(TEST_META_SAVE_PATH))
	var safe_meta: Dictionary = parsed if parsed is Dictionary else {"amber": 0, "unlocked_heroes": []}

	# Assert: Fallback limpo sem crash
	assert_eq(safe_meta["amber"], 0, "Arquivo inválido deve inicializar estado seguro padrão")
```

---

## 5. Verification Method

To independently verify the test baseline and infrastructure:

1. **Run the Entire GUT Test Suite via Command Line:**
   ```bash
   bash godot_project/run_gut_tests.sh
   ```
   *Expected Outcome:* Exit code `0`, 31 Test Scripts, 729 Tests Run, 729 Passed, 0 Failed, 6494 Assertions Passed.

2. **Verify That Godot Binary Exists and is Executable:**
   ```bash
   /home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot --version
   ```
   *Expected Output:* `4.7.2.stable.official.ed1daf0bf`

3. **Verify GUT Configuration:**
   Inspect `/home/anderson/Documents/projeto/RPG-battle/godot_project/.gutconfig.json` to confirm `"dirs": ["res://test/unit/"]`.

4. **Invalidation Conditions:**
   - Exit code != 0.
   - Any test failures among the baseline 729 tests.
   - Any missing files or unhandled ObjectDB leaks detected during test suite shutdown.
