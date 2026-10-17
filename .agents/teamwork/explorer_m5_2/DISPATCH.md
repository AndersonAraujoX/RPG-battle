## 2026-10-16T10:12:31Z
You are Explorer 2 for Milestone M5 (Cigarra Ressonante & Rainha do Enxame).
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_2
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_2/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/IsectumCastes.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/InvasorPawn.gd

Design the Act II mini-boss and boss:
1. `godot_project/scripts/entities/bosses/CigarraRessonante.gd`:
   - Elite mini-boss (70-90 HP, high mobility).
   - `pulso_sonico`: checks hero clustering (>=2 heroes within distance <=2), deals AoE damage and applies Atordoado (Stun) for 1 round.
2. `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd`:
   - Act II Boss (180-220 HP).
   - Royal Guard protection: 50% damage reduction while any Royal Guard / Guarda Real is alive.
   - `chamado_da_rainha`: periodic brood summoning every 2 turns.
   - Transition narrative hook upon defeat.
Provide complete GDScript designs, methods, state handling, and GUT test specifications.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_2/handoff.md.
When finished, notify orchestrator via send_message.
