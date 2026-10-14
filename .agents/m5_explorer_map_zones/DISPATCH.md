## 2026-10-01T01:25:39Z

You are the Map & Zones Visual Explorer for Milestone 5 (Tabuleiro da Fortaleza & Painel de Recursos) of RPG-battle.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_map_zones

MANDATORY FIRST STEP:
Read these files before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Authoritative request)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master architecture & contracts)
- /home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md (Test spec)
- /home/anderson/Documents/projeto/RPG-battle/src/states/cerco/draw_map.py (Python map drawing for 17 zones)
- /home/anderson/Documents/projeto/RPG-battle/src/states/cerco/draw_panel.py (Python resource panel drawing)
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/FortressBoard.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/WorkshopEconomy.gd

Your Mission:
Investigate how the 17 zones of the fortress and the economy scoreboard are visually represented and updated:
1. 17 Zones on the 20x20 grid:
   - How are zones delineated visually (Câmara Central, 4 Oficinas/Pátio, 4 Muralhas, 4 Torres, 4 Campos de Invasão)?
   - How are elevation levels (0 = ground/spawns, 1 = walls, 2 = towers) represented?
   - How are wall breaches (HP <= 0) and damage states indicated?
   - How is zone highlighting (valid movement destinations, targeting for actions/repairs) calculated and triggered?
2. Resource Scoreboard & Round Status:
   - How are resources (Madeira, Couro, Metal, Cristais, AP) displayed?
   - How are the 4 co-op synchrony layers (Marcha, Trabalho, Escavação, Combate) and current round/threat level displayed?
   - Reactive updates from `WorkshopEconomy` signals (`resources_updated`, `wall_repaired_with_resources`).
3. Godot 4 Component Architecture:
   - Design of `FortressBoardView.gd` / `ZoneOverlay.gd` and `ResourceScoreboard.gd`.
   - Pure headless testability: ensure data structures and calculations can be verified by GUT without crashes.

Deliverables:
- Write your comprehensive findings to /home/anderson/Documents/projeto/RPG-battle/.agents/m5_explorer_map_zones/handoff.md.
- Send a completion message to parent.
