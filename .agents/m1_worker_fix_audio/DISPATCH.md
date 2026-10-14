## 2026-09-26T16:17:52Z
You are the Final Audio & Teardown Remediation Worker for Milestone 1 of RPG-battle.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m1_worker_fix_audio

Read these files first:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/m1_recheck_reviewer/handoff.md (CRITICAL: exact root-cause analysis and reproduction)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. DO NOT falsify, truncate, or fabricate terminal output. Full, unedited verification output is required. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- godot_project/scripts/autoload/AudioManager.gd
- godot_project/addons/gut/gut_cmdln.gd
- godot_project/test/unit/test_adversarial_data_audio.gd

Your Objectives:
1. Fix AudioManager.gd:
   - In headless mode, `player.playing` is always false in the dummy audio driver, causing `_get_available_sfx_player()` to constantly return `_sfx_pool[0]`. Multiple `play()` calls on the same player without prior `stop()` create orphaned playback objects in Godot's `AudioServer`.
   - Fix: Use round-robin pool cycling (`_next_sfx_pool_index = (_next_sfx_pool_index + 1) % _sfx_pool.size()`), and ALWAYS call `player.stop()` and `player.stream = null` before assigning a new stream and calling `player.play()`.
   - In `stop_all_sfx()` and `cleanup()`: stop every player, set `p.stream = null`, and ensure proper release.

2. Fix gut_cmdln.gd:
   - In teardown, when calling `cleanup()` / `stop_all_sfx()` on `AudioManager`, do NOT immediately call `node.free()` on the same frame.
   - Add a 2-frame wait (`await get_tree().process_frame; await get_tree().process_frame`) BEFORE calling `remove_child(node)` and `node.free()` on the autoload nodes. This allows `AudioServer` to process and destroy playback instances while the node hierarchy remains valid.

3. Fix test_adversarial_data_audio.gd:
   - In `after_each()` and `after_all()`, add `if _am != null and _am.has_method("stop_all_sfx"): _am.stop_all_sfx()`.
   - Fix all merged AAA comments (`# Arrange & Act`, `# Act & Assert`) into strict separate `# Arrange`, `# Act`, `# Assert` blocks without merged comments.

4. Independent Empirical Verification:
   - Run:
     `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit`
     Verify with your own eyes that the exit output contains:
     ZERO `WARNING: ObjectDB instances were leaked at exit`
     ZERO `ERROR: resources still in use at exit`
     ZERO orphan StringNames.
   - Run:
     `./godot_project/run_gut_tests.sh`
     Verify 100% tests pass and NO leak warnings appear after the summary.
   - Report the full verbatim output honestly in `handoff.md`.

## 2026-09-26T16:30:24Z
From parent:
**Context**: Milestone 1 Audio Fix Worker Progress Check
**Content**: Heartbeat check: What is your current progress on AudioManager round-robin pool cycling, gut_cmdln 2-frame wait, and test_adversarial_data_audio cleanup?
**Action**: Please report your current step and update your progress.md.
