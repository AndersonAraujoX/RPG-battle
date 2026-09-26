# Task Assignment: M1 FSM & Signals Challenger

## Objective
Empirically and adversarially challenge `GameManager` FSM and `EventBus` signals:
1. Stress-test rapid, chaotic, and invalid state transitions in `GameManager`.
2. Stress-test high-throughput signal emission, multi-subscriber listener re-entrancy, disconnect safety, and extreme payload handling in `EventBus`.
3. Execute empirical tests using Godot headless CLI (`./godot_project/bin/godot --headless ...`).

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `godot_project/scripts/autoload/GameManager.gd`
- `godot_project/scripts/autoload/EventBus.gd`

## Deliverables
- Adversarial report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/analysis.md`.
- Handoff report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/handoff.md`.
- Explicit verdict in handoff: `APPROVE` or `REJECT`.
- Send message to orchestrator with summary and verdict.

## 2026-09-26T13:03:25Z
You are m1_challenger_fsm_signals.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read PROJECT.md and your assignment in /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/DISPATCH.md.

Adversarially challenge GameManager and EventBus. Write empirical tests or stress harnesses checking rapid/invalid transitions, recursive/re-entrant signal emission, multi-subscriber edge cases, and extreme payloads.
Write your analysis to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/analysis.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_challenger_fsm_signals/handoff.md. Include your explicit verdict: APPROVE or REJECT.
When finished, send a message to orchestrator with summary and verdict.

