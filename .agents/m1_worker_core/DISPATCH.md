# Task Assignment: M1 Core Implementation Worker

## 2026-09-26T12:50:12Z
You are m1_worker_core.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read /home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/DISPATCH.md, PROJECT.md, and the analysis reports from:
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_project/analysis.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/analysis.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_spec_miner_gut/analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your mission is to implement Milestone 1 (Foundation & Core Infrastructure):
1. Initialize godot_project/ with project.godot, default_bus_layout.tres, .gutconfig.json, directory layout.
2. Copy the host Godot binary (/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64) into godot_project/bin/godot (and chmod +x it), and copy assets/ and dados/ into godot_project/.
3. Implement the 4 Autoload singletons (EventBus.gd, DataManager.gd, GameManager.gd, AudioManager.gd) and 3 Custom Resources (CharacterData.gd, IsectumCasteData.gd, CardData.gd).
4. Implement GUT in godot_project/addons/gut/ and the 44-test unit test suite in godot_project/test/unit/test_autoloads.gd.
5. Run the headless GUT test suite via godot_project/bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit and verify 100% tests pass with exit code 0.
6. Write your report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/report.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/handoff.md.
When finished, send a message to orchestrator with summary, test output, and report paths.

## Objective
Implement Milestone 1 (Foundation & Core Infrastructure) in `godot_project/`:
1. Godot 4 project initialization (`project.godot`, `default_bus_layout.tres`, directory layout, Godot binary in `godot_project/bin/godot`).
2. Assets and data replication (`assets/` -> `godot_project/assets/`, `dados/` -> `godot_project/dados/`).
3. Core Autoload singletons (`EventBus.gd`, `DataManager.gd`, `GameManager.gd`, `AudioManager.gd`) and Custom Resources (`CharacterData.gd`, `IsectumCasteData.gd`, `CardData.gd`).
4. GUT framework setup in `godot_project/addons/gut/`, `.gutconfig.json`, and runner script `run_gut_tests.sh`.
5. Comprehensive unit test suite in `godot_project/test/unit/test_autoloads.gd` (44 tests, AAA pattern).
6. Execute headless GUT tests (`./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`) and verify 100% pass with exit code 0.

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core`

## Owned Files Exclusively
All files inside `/home/anderson/Documents/projeto/RPG-battle/godot_project/`.

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_project/analysis.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/analysis.md`
- `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_spec_miner_gut/analysis.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverables
- Fully working Godot 4 project in `/home/anderson/Documents/projeto/RPG-battle/godot_project/`.
- Test execution output showing all 44 unit tests passing with exit code 0.
- Report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/report.md`.
- Handoff at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_core/handoff.md`.
- Message to orchestrator with summary.
