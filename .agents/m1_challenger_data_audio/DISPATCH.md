# Task Assignment: M1 Data & Audio Challenger

## Objective
Empirically and adversarially challenge `DataManager` and `AudioManager`:
1. Stress-test `DataManager` with corrupted JSON, missing keys, empty files, non-string keys, and verify deep-clone mutation isolation on `CharacterData` instances.
2. Stress-test `AudioManager` SFX pool exhaustion (>30 concurrent requests), rapid volume changes, mute toggle cycles, and behavior under headless dummy audio driver.
3. Execute empirical tests using Godot headless CLI (`./godot_project/bin/godot --headless ...`).

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `godot_project/scripts/autoload/DataManager.gd`
- `godot_project/scripts/autoload/AudioManager.gd`
- `godot_project/scripts/resources/CharacterData.gd`

## Deliverables
- Adversarial report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/analysis.md`.
- Handoff report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/handoff.md`.
- Explicit verdict in handoff: `APPROVE` or `REJECT`.
- Send message to orchestrator with summary and verdict.

## 2026-09-26T13:03:25Z
You are m1_challenger_data_audio.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read PROJECT.md and your assignment in /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/DISPATCH.md.

Adversarially challenge DataManager and AudioManager. Write empirical stress tests checking corrupt/missing JSON handling, CharacterData mutation isolation, audio pool exhaustion (>30 concurrent SFX), volume bounds, and headless safety.
Write your analysis to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/analysis.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_data_audio/handoff.md. Include your explicit verdict: APPROVE or REJECT.
When finished, send a message to orchestrator with summary and verdict.
