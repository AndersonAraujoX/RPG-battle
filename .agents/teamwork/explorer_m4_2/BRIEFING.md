# BRIEFING — 2026-10-16T02:27:50Z

## Mission
Design CombatEncounterGenerator.gd with deterministic procedural squad generation by Act, floor, and node type (COMBAT, SIEGE, ELITE, BOSS - viuva_canibal) based on IsectumCastes and RunNode.

## 🔒 My Identity
- Archetype: explorer
- Roles: explorer, analyst, synthesizer
- Working directory: /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2
- Original parent: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Milestone: M4

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Design CombatEncounterGenerator.gd with deterministic squad generation by Act, floor, and node type (COMBAT, SIEGE, ELITE, BOSS - viuva_canibal)
- Support deterministic RNG seeding (via seed + Act + floor + node index)
- Follow project standards (SOLID, AAA testing principles, Godot RefCounted architecture)
- Deliver report to /home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m4_2/handoff.md

## Current Parent
- Conversation ID: aa7d5d2d-ef0f-482c-be6b-93c1793915c2
- Updated: 2026-10-16T02:27:50Z

## Investigation State
- **Explored paths**:
  - .agents/teamwork/explorer_m4_2/DISPATCH.md
  - .agents/teamwork/ORIGINAL_REQUEST.md
  - .agents/teamwork/orchestrator_1/PROJECT.md
  - CAMPANHA_ROGUELIKE.md
  - godot_project/scripts/cerco/IsectumCastes.gd
  - godot_project/scripts/resources/IsectumCasteData.gd
  - godot_project/scripts/run/RunNode.gd
  - godot_project/scripts/run/RunState.gd
  - godot_project/scripts/run/RunNodeResolver.gd
  - godot_project/scripts/cerco/ThreatDeck.gd
  - godot_project/scripts/cerco/FortressBoard.gd
  - godot_project/scripts/main/CercoGameController.gd
  - godot_project/scripts/ui/FortressBoardView.gd
  - godot_project/test/unit/test_isectum_castes.gd
  - godot_project/test/unit/test_reward_modal.gd
- **Key findings**:
  - `IsectumCastes` provides 24 canonical castes with `get_caste()`, `create_instance()`, `ALIASES` mapping.
  - Caste aliases exist for `viuva_canibal` -> `tece_teia`, `gafanhoto_praga` -> `barata_praga`, `tarantula_golias` -> `colosso_isectum`. `larva_carniceira` maps to `larva_necrotica`, `besouro_gorgulho` to `cupim_roedor` / `operario_escavador`.
  - Grid is 20x20 with 4 outer invasion spawn zones (`SPAWN_NORTE`, `SPAWN_SUL`, `SPAWN_LESTE`, `SPAWN_OESTE`) and central core.
  - Encounter specification must produce ready-to-place squad dictionaries, hazard dictionaries (web hazards for Viúva Canibal), and reward metadata matching `RewardModal` and `RunNodeResolver` conventions.
  - Deterministic RNG seeding formula combines base run seed, Act, floor, and node id with prime hashing multipliers.
- **Unexplored areas**:
  - None for M4 encounter design.

## Key Decisions Made
- Design `CombatEncounterGenerator` as a standalone `RefCounted` class with pure static and instance methods.
- Define internal alias mapper `CASTE_ALIASES` to seamlessly bridge design doc names to `IsectumCastes`.
- Design squad algorithms with distinct composition patterns for COMBAT (3-4 basic), SIEGE (4-6 sappers/brutamontes), ELITE (1 heavy + 2-3 minions), and BOSS (Viúva Canibal + larvae + web hazards).
- Structure complete handoff report with exact code proposal, schema definitions, logic chain, and GUT test suite specification.

## Artifact Index
- .agents/teamwork/explorer_m4_2/DISPATCH.md — Task dispatch and instructions
- .agents/teamwork/explorer_m4_2/BRIEFING.md — Working memory
- .agents/teamwork/explorer_m4_2/progress.md — Progress and heartbeat tracking
- .agents/teamwork/explorer_m4_2/handoff.md — Final deliverable report
