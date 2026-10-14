## 2026-09-26T15:47:36Z

You are the Remediation Worker for Milestone 1 (Foundation & Autoloads) of the RPG-battle Godot Engine 4 migration.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_remedy

You MUST read these files before doing any work:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Mandatory authoritative request)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master architecture & contracts)
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md (Code quality, AAA tests, clean architecture)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_architecture/handoff.md (Detailed review findings)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_reviewer_tests/handoff.md (Detailed test review findings)
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/analysis.md (Adversarial stress findings & test_fsm_signals_stress.gd)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- godot_project/scripts/autoload/GameManager.gd
- godot_project/scripts/autoload/EventBus.gd
- godot_project/scripts/autoload/DataManager.gd
- godot_project/scripts/autoload/AudioManager.gd
- godot_project/test/unit/test_autoloads.gd

Your Objectives:
1. Fix GameManager.gd:
   - Implement real re-entrancy protection: check `if is_transitioning: push_warning("[GameManager] Transition rejected: already transitioning"); return false` in `can_transition_to` and `change_state`.
   - Prevent signal order inversion & desynchronization: in `change_state`, store target_state locally, emit `state_changed` and `EventBus.game_state_changed` cleanly.
   - Deep copy state_payload: `state_payload = payload.duplicate(true)` to prevent external reference aliasing.
   - Fix reset methods: in `reset_state()` and `reset_to_menu()`, cleanly emit state change to MENU or handle reset so external listeners stay in sync.
   - Decouple from AudioManager: use EventBus signals rather than `get_node("/root/AudioManager").play_bgm(...)`.

2. Fix AudioManager.gd:
   - Provide `stop_all_sfx()` and proper stream/player release to completely eliminate the 74 ObjectDB leaked instances and 12 leaked resources at exit.
   - Connect to EventBus audio request signals.
   - Implement bus mute/pitch scaling helpers.

3. Fix DataManager.gd:
   - Segregate heroes vs enemies: update `get_all_heroes()` to return only playable heroes (e.g. where team == "A" or canonical heroes), excluding boss monsters (`ReiGoblin`, `LordeLich`, etc.). Add `get_all_enemies()` for monster/boss queries.
   - Implement missing helper methods: `get_isectum_caste()`, `get_all_isectum_castes()`, `has_caste()`, `get_card_data()`, `get_all_cards()`, `has_card()`, `get_hero_duplicate()`.

4. Fix EventBus.gd:
   - Fix `emit_logged`: support arbitrary argument counts (using `Callable(self, sig_name).callv(args)`), check `has_signal(sig_name)`.
   - Deep-copy arguments in `_event_history.append({"signal": sig_name, "args": args.duplicate(true), ...})`.

5. Fix test/unit/test_autoloads.gd:
   - Eliminate false-positive test transitions: replace invalid transitions (`COMBATE_TATICO -> CERCO_ISECTUM`, `MENU -> FIM_DE_JOGO`) with valid transition chains (`MENU -> COMBATE_TATICO -> FIM_DE_JOGO -> MENU`).
   - Assert all boolean return values from `change_state()` (`assert_true(...)`).
   - Strictly follow Arrange-Act-Assert (AAA) pattern for ALL test functions (distinct `# Arrange`, `# Act`, `# Assert` sections, no merged comments).
   - In `after_each()`, call `_am.stop_all_sfx()` and teardown audio players to prevent leaks.
   - Add unit tests for all new helper methods (castes, cards, duplicates, payloads, mute).

6. Verification:
   - Run `./godot_project/run_gut_tests.sh` and ensure 100% tests pass (both `test_autoloads.gd` and `test_fsm_signals_stress.gd`).
   - Verify that ZERO `[GameManager] Invalid state transition` warnings occur during positive test executions.
   - Run `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` and verify 0 ObjectDB leaks at exit.
   - Write comprehensive handoff.md in your working directory (.agents/m1_worker_remedy/handoff.md) with test commands and verbatim outputs, then notify parent.
