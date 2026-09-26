# Task Assignment: M1 Autoload Singletons Architecture Explorer

## Objective
Design the concrete architecture, typed GDScript signatures, error handling, and testable interfaces for the global Autoload singletons (`EventBus.gd`, `DataManager.gd`, `GameManager.gd`, `AudioManager.gd`).

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/PROJECT.md`
- `/home/anderson/Documents/projeto/RPG-battle/dados/` (`dados/personagens.json`, etc.)
- `/home/anderson/Documents/projeto/RPG-battle/assets/sounds/`

## Deliverables
- Detailed report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/analysis.md`.
- Handoff report at `/home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/handoff.md`.
- Message to orchestrator with summary.

## 2026-09-26T12:42:00Z
You are m1_explorer_autoloads.
Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/
You MUST read /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md first.
Then read /home/anderson/Documents/projeto/RPG-battle/PROJECT.md and /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/DISPATCH.md.

Your mission is to design the concrete architecture, typed GDScript code, error handling, and testable interfaces for:
1. EventBus.gd (all global signals from PROJECT.md Interface Contracts).
2. DataManager.gd (loading and parsing dados/personagens.json, caching, fallback).
3. GameManager.gd (state machine: MENU, COMBATE_TATICO, CERCO_ISECTUM, FIM_DE_JOGO).
4. AudioManager.gd (BGM and SFX playback, audio bus integration).
Write your analysis to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/analysis.md and handoff report to /home/anderson/Documents/projeto/RPG-battle/.agents/m1_explorer_autoloads/handoff.md.
When finished, send a message to orchestrator with summary and report paths.
