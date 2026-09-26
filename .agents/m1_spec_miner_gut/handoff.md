# Handoff Report: M1 GUT Framework & Headless Runner Specification

**Agent**: `m1_spec_miner_gut`  
**Milestone**: M1 (Foundation & Core Infrastructure)  
**Date**: 2026-09-26  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation

1. **Requirements & Scope**:
   - `ORIGINAL_REQUEST.md:51-58`:
     > "### R7. Suíte de Testes Automatizados via GUT (Godot Unit Testing)
     > - Instalar e configurar o framework GUT em `godot_project/addons/gut/` e `godot_project/test/`.
     > - ...
     > - Todos os testes devem rodar via linha de comando em modo headless (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`) com 100% de sucesso."
   - `PROJECT.md:7-12`:
     > "- **Autoload Singletons**:
     >   - `GameManager.gd`: Game state machine (`MENU`, `COMBATE_TATICO`, `CERCO_ISECTUM`, `FIM_DE_JOGO`, `MULTIPLAYER_LOBBY`).
     >   - `EventBus.gd`: Global event dispatcher (`unit_moved`, `damage_dealt`, `card_selected`, `round_resolved`, `turn_changed`, `network_event_received`).
     >   - `DataManager.gd`: Centralized loader and validator for structured data in `dados/` (`personagens.json`, `fases/`, etc.).
     >   - `AudioManager.gd`: Global sound and music controller with volume buses and pooling.
     > - **Testing Architecture**: GUT (Godot Unit Testing) in `godot_project/addons/gut/` and `godot_project/test/`, configured for headless CLI execution (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`)."
   - `TEST_INFRA.md:46-48`:
     > "- **Runner**: GUT 9.x headless CLI script: `godot_project/addons/gut/gut_cmdln.gd`.
     > - **Command**: `godot --headless -s addons/gut/gut_cmdln.gd -gexit -gdir=res://test/`
     > - **Configuration**: `godot_project/.gutconfig.json`"
   - `TEST_INFRA.md:67-73`:
     > "- **Tier 1 (Feature Coverage)**: $\ge 5$ test cases per feature...
     > - **Tier 2 (Boundary & Corner Cases)**: $\ge 5$ test cases per feature...
     > - **Total Minimum Target**: $\ge 313$ assertions / test cases passing with exit code 0."

2. **Environment & Host Observations**:
   - Tool `run_command` executing `ls -la godot_project/ 2>/dev/null`: returned `"godot_project does not exist yet"`. Milestone 1 project directory creation is currently being prepared by peer agents `m1_explorer_project` and `orchestrator_1`.
   - Tool `run_command` executing `which godot`: returned `"No godot in PATH"`.
   - Host filesystem inspection: `~/.config/godot/editor_settings-4.7.tres` exists on host (modified on 2026-09-25), confirming active Godot 4.x environment.

3. **Code Quality Rules**:
   - `GEMINI.md:86-105` and `SKILL_organizacao_refatoracao.md`: Mandatory Arrange-Act-Assert (AAA) pattern, minimum coverage (happy path, edge cases, error handling), clean decoupled test design.

---

## 2. Logic Chain

1. **GUT Setup Architecture**:
   - From `ORIGINAL_REQUEST.md:52` and `TEST_INFRA.md:46-48`, the testing framework must reside in `godot_project/addons/gut/` and be configured via root `.gutconfig.json`.
   - In Godot 4, GUT operates as an addon requiring `plugin.cfg` with version 9.x, a CLI entry script (`gut_cmdln.gd`), the core runner (`gut.gd`), and base test script (`test.gd` extending `Node` as `GutTest`).
   - If offline or air-gapped container boundaries prevent git/assetlib network fetches, providing a self-contained fallback implementation conforming strictly to the `GutTest` public API ensures CLI automation works deterministically.

2. **Headless CLI Invocation**:
   - Godot 4 deprecates `--no-window` in favor of `--headless`.
   - Running `godot --headless -s addons/gut/gut_cmdln.gd -gexit`:
     * `--headless` initializes `DisplayServerHeadless` and `AudioDriverDummy`, preventing display/audio server crashes in headless CI/CD.
     * `-s addons/gut/gut_cmdln.gd` boots Godot into the GUT CLI runner.
     * `-gexit` enforces process termination (`quit(0)` on all assertions pass, `quit(1)` on any failure). Without `-gexit`, Godot headless hangs indefinitely waiting for OS signals.
     * When `.gutconfig.json` is located at `res://.gutconfig.json`, GUT auto-loads configuration defaults without requiring verbose CLI flags.

3. **Design of `test/unit/test_autoloads.gd`**:
   - The test script must validate all 4 singletons (`GameManager`, `EventBus`, `DataManager`, `AudioManager`).
   - To adhere to AAA and prevent cross-test state pollution, `before_each()` supports dual-resolution: querying the global node at `/root/<Autoload>` if initialized by Godot, or instantiating a clean instance via `preload(...).new()` wrapped in `autofree()`.
   - The suite is divided into 4 clear sections:
     * `GameManager`: 10 tests (Initial state MENU, state transitions, state_changed signal, is_in_combat flag, state names, idempotency, reset, rapid transitions, invalid state rejection).
     * `EventBus`: 11 tests (unit_moved, unit_attacked, unit_damaged, unit_died, death_save_rolled, status applied/removed, cards/round resolved, resources updated, multi-subscribers, disconnect safety, extreme boundary values).
     * `DataManager`: 12 tests (personagens.json loading, Guerreiro stats, Mago stats, Ladino stats, hero count >= 9, ReiGoblin boss stats, null on unknown hero, null on empty string, cache persistence, clear_cache, missing file fallback, corrupt JSON parsing).
     * `AudioManager`: 11 tests (play BGM, stop BGM, switch BGM, SFX pool allocation, bus volume control, nonexistent SFX/BGM safety, volume clamping [0.0, 1.0], 16-SFX rapid fire pool reuse, headless dummy driver execution).
   - Total assertions: 44 tests, comprehensively covering happy paths, edge cases, and error handling, satisfying M1 coverage requirements.

---

## 3. Caveats

1. The `godot` binary path on the host machine must be confirmed by `m1_explorer_project`. If not in global PATH, workers must invoke the command using the resolved binary path (e.g. `path/to/godot --headless ...`).
2. When creating the project, `project.godot` must declare the 4 Autoloads under `[autoload]` pointing to `res://scripts/autoload/<Name>.gd` and enable the GUT plugin under `[editor_plugins]` (`enabled=PackedStringArray("res://addons/gut/plugin.cfg")`).

---

## 4. Conclusion

The complete technical specification for GUT in Godot 4 has been established and documented in `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_spec_miner_gut/analysis.md`. The design includes:
1. Complete directory structure and script roles for `godot_project/addons/gut/` and full `.gutconfig.json` configuration file.
2. CLI headless test invocation flags and operational semantics: `godot --headless -s addons/gut/gut_cmdln.gd -gexit`.
3. Complete 44-test GDScript suite for `test/unit/test_autoloads.gd` adhering to AAA pattern, testing happy paths, edge cases, and error handling across all 4 Autoloads (`GameManager`, `EventBus`, `DataManager`, `AudioManager`).

---

## 5. Verification Method

1. **Inspect Analysis Report**:
   ```bash
   cat /home/anderson/Documents/projeto/RPG-battle/.agents/m1_spec_miner_gut/analysis.md
   ```
2. **Verify JSON Validity of `.gutconfig.json` Specification**:
   Verify that `.gutconfig.json` in Section 2.1 parses cleanly as valid JSON:
   ```bash
   python3 -c 'import json; json.loads("""'"$(grep -A 25 '"dirs"' /home/anderson/Documents/projeto/RPG-battle/.agents/m1_spec_miner_gut/analysis.md | sed -n '1,/^}/p')"'""")'
   ```
3. **Execution Command Verification (Once Godot project and Autoloads are materialized)**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project && godot --headless -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_autoloads.gd -gexit
   ```
   **Expected Result**: Exit code 0, 44 passing tests, 0 failures, 0 errors.
