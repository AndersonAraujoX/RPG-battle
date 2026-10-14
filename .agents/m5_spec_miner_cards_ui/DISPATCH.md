## 2026-10-01T01:25:39Z

You are the Specification Miner for Milestone 5 (UI/UX do Cerco: Fan Cards & HUD Controls) of RPG-battle.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m5_spec_miner_cards_ui

MANDATORY FIRST STEP:
Read these files before starting:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (Authoritative request)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md (Master architecture & contracts)
- /home/anderson/Documents/projeto/RPG-battle/TEST_INFRA.md (Test spec)
- /home/anderson/Documents/projeto/RPG-battle/src/states/cerco/draw_cards.py (Python card fan layout & interaction)
- /home/anderson/Documents/projeto/RPG-battle/src/states/cerco/draw_ui.py (Python UI drawing)
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/resources/CardData.gd
- /home/anderson/Documents/projeto/RPG-battle/godot_project/scripts/cerco/CercoDeck.gd

Your Mission:
Mine all specifications for the card fan layout and card visual interactions:
1. Mathematical layout of the hand cards in a fan arc:
   - What are the arc angle calculations, radius, center point, spacing per card count?
   - How does hover elevation (lift) work? How is card selection indicated?
   - Card dimensions, badges (Marcha, Trabalho, Escavação, Combate, Especial), cost display (Wood, Leather, Metal, Crystal, AP).
2. Interaction flow:
   - Selecting a card, triggering card play, drag & drop or click-to-target zone.
   - Signal contracts needed for Godot 4 (`card_selected`, `card_played_requested`, `card_hovered`, `card_unhovered`).
3. Godot 4 UI implementation strategy:
   - CanvasLayer / Control nodes (e.g. `CardFanContainer.gd`, `CardUI.gd`).
   - Clean, testable logic decoupled from rendering so GUT unit tests can verify layout calculations and signals headlessly without requiring a display server.

Deliverables:
- Write your comprehensive findings to /home/anderson/Documents/projeto/RPG-battle/.agents/m5_spec_miner_cards_ui/handoff.md.
- Send a completion message to parent.
