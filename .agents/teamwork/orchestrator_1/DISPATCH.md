## 2026-10-16T01:06:11Z
Sender: e6c8fea6-dcda-464c-87c7-2622c2802a11
Priority: MESSAGE_PRIORITY_HIGH

You are the Project Orchestrator for the RPG-battle Godot 4 project.

Your working directory is: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1`.
Original user request file: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md`.
Specification document: `/home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md`.
Godot project root: `/home/anderson/Documents/projeto/RPG-battle/godot_project`.

Task:
Implement Milestones M3 to M8 of the Tactical Roguelike Campaign in Godot 4 as detailed in `CAMPANHA_ROGUELIKE.md` and `ORIGINAL_REQUEST.md`:
- R1 (M3): Recompensas Pós-Combate, Forja & Sistema de Relíquias
- R2 (M4): Integração do Combate Tático aos Nós do Mapa (COMBAT, ELITE, SIEGE, BOSS) com persistência de PV e Permadeath
- R3 (M5): Conteúdo e Mecânicas do Ato II (Túneis Vivos: tochas, casulos/ovos, mini-chefe cigarra_ressonante, chefe rainha_do_enxame)
- R4 (M6): Os 3 Corações da Colmeia e Batalha Final contra o Rei Isectum (fase_09, fase_10, fase_11 e boss rei_isectum 3x3 na fase_12 com 3 fases de combate)
- R5 (M7 & M8): Meta-Progressão Permanente & Ascensão (user://meta_save.json, quartel de heróis e cartas rúnicas, Ascensão 1-10, telas de vitória/derrota com estatísticas)

Requirements:
- Strict unit testing with GUT (Arrange-Act-Assert, edge cases, error handling).
- 100% tests passing via `bash godot_project/run_gut_tests.sh`.
- Prevent infinite execution / watchdog timer pattern where applicable.
- Clean architecture and decoupled code.
- Maintain `BRIEFING.md`, `plan.md`, and `progress.md` in your working directory `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1`.
- Report back to the Sentinel when the implementation and testing are complete.
