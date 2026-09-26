# Task Assignment: Entities & Cerco Mode Survey

## Objective
Survey the reference Python codebase and data files for all entity classes, heroes, 24 Isectum casts, and Cerco contra Isectum mode (deckbuilding, synergies, fortress economy).

## Working Directory
`/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_content`

## Authoritative Inputs
- `/home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md` (MUST READ FIRST)
- `/home/anderson/Documents/projeto/RPG-battle/src/castas_isectum.py`
- `/home/anderson/Documents/projeto/RPG-battle/src/cerco_isectum.py`
- `/home/anderson/Documents/projeto/RPG-battle/dados/` (`dados/personagens.json`, `dados/fases/`, etc.)
- `/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/`

## Scope & Investigation Questions
1. **Heroes & Character Data**:
   - Details of all 11 heroes: Aquele, Stark, Elden, Doom, Gruu, Kuro, Darwin, Novak, Rilem, Yukito, Koema.
   - Base attributes (HP, AC, Speed, Attack bonus, Damage dice, special abilities/actions).
   - Sprite/portrait asset mappings in `assets/images/characters/`.
2. **24 Isectum Insect Casts**:
   - Enumerate all 24 castes from `src/castas_isectum.py`.
   - Name, tier/category, HP, attack, defenses, movement, unique passives, special traits, and active behaviors for each.
3. **Cerco contra Isectum Mode & Deckbuilder**:
   - Cards architecture: types (Action, Upgrade, Rune), costs, badges (Movement, Work, Excavation).
   - Hand mechanics: drawing, discarding, hand fan presentation requirements.
   - Simultaneous Co-op Sync Turn: combo resolution, Synergy types (Supreme synergy, Team synergy).
   - Fortress Free Actions: spending movement points, attacking targets, excavating rocks for materials (Wood, Metal, Crystal).

## Deliverables
- Write comprehensive inventory and analysis to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_content/analysis.md`.
- Write handoff to `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_content/handoff.md`.
- Send completion message to orchestrator with summary and paths.
