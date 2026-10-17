## 2026-10-16T10:12:31Z
You are Explorer 1 for Milestone M5 (TorchLighting & ChitinCocoon).
Your working directory is: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1
You must read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/orchestrator_1/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/CAMPANHA_ROGUELIKE.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1/DISPATCH.md
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/tactical/TacticalGrid.gd (if present) or board scripts in godot_project/scripts/cerco/

Design the TorchLighting system and ChitinCocoon obstacle mechanics for Act II:
1. `godot_project/scripts/tactical/TorchLighting.gd` (RefCounted):
   - Chebyshev distance radius 3 around living heroes.
   - Relic synergy: `tocha_eterna` increases radius by +2 (radius 5).
   - Methods: `update_visibility(heroes_positions: Array[Vector2i], bonus_radius: int = 0)`, `is_cell_lit(cell: Vector2i) -> bool`, `get_lit_cells() -> Array[Vector2i]`.
   - Darkness rules: blocks ranged targeting into darkness; shrouds enemies.
2. `godot_project/scripts/entities/ChitinCocoon.gd` (RefCounted or Node):
   - 15 HP structure.
   - 3-turn hatch countdown: decrement per round.
   - Hatching at 0: spawns Tier 2 insect in adjacent free cell, deals 5 acid damage to adjacent cells.
   - Cancellation if destroyed before hatching.
Provide complete GDScript design, method signatures, edge cases, and GUT test design.
Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_1/handoff.md.
When finished, notify orchestrator via send_message.
