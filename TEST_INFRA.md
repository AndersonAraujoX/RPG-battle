# E2E Test Infra: RPG-battle Godot Engine 4 Migration

## Test Philosophy
- Opaque-box, requirement-driven, strictly derived from `ORIGINAL_REQUEST.md` and user specifications.
- Complete coverage: every feature listed in `PROJECT.md § Feature Inventory` must be exercised.
- Implementation: GDScript using GUT (Godot Unit Testing) headless runner (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`).
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.

---

## Feature Inventory Coverage Matrix
| # | Feature | Requirement Source | Tier 1 (Min 5) | Tier 2 (Min 5) | Tier 3 (Pairwise) | Tier 4 (Scenario) |
|---|---------|-------------------|:--------------:|:--------------:|:-----------------:|:-----------------:|
| 1 | Godot 4 Base Project Config | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | Autoload Singletons | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | GUT Framework & Headless Runner | ORIGINAL_REQUEST §R7 | 5 | 5 | ✓ | ✓ |
| 4 | 20x20 Tactical Grid & Bounds | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 5 | AStar2D Pathfinding & Terrain | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 6 | Destructible Structures | src/tabuleiro.py | 5 | 5 | ✓ | ✓ |
| 7 | Line of Sight & Cover System | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 8 | D&D 5e Combat Math & Advantage | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 9 | Damage Types & Resistances | src/config.py | 5 | 5 | ✓ | ✓ |
| 10 | Death Saving Throws FSM | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 11 | Status Conditions System | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 12 | Character Custom Resource | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 13 | 11 Playable Heroes & Lysander | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 14 | Character Scene & Visuals | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 15 | 24 Isectum Insect Castes | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 16 | Cerco Card Custom Resource | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 17 | Card Scene & Fan Arc Layout | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 18 | Simultaneous Sync Turn Co-op | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 19 | Synergy Combo System | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 20 | Fortress Economy & Free Actions | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 21 | Cerco Combat Judge Engine | src/juiz_combate.py | 5 | 5 | ✓ | ✓ |
| 22 | Dark Fantasy HUD (CanvasLayer) | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| 23 | Scrollable Combat Log | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| 24 | Floating Combat Text (FCT) | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| 25 | Audio & SFX Integration | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| 26 | WebSocket Client Engine | ORIGINAL_REQUEST §R6 | 5 | 5 | ✓ | ✓ |
| 27 | Typed Protocol Serialization | ORIGINAL_REQUEST §R6 | 5 | 5 | ✓ | ✓ |
| 28 | State Sync & Anti-Cheat | ORIGINAL_REQUEST §R6 | 5 | 5 | ✓ | ✓ |

---

## Test Architecture
- **Runner**: GUT 9.x headless CLI script: `godot_project/addons/gut/gut_cmdln.gd`.
- **Command**: `godot --headless -s addons/gut/gut_cmdln.gd -gexit -gdir=res://test/`
- **Configuration**: `godot_project/.gutconfig.json`
- **Output Directories**:
  - `godot_project/test/unit/`: Isolated unit tests per module.
  - `godot_project/test/integration/`: Cross-module contract tests.
  - `godot_project/test/e2e/`: Full combat, Cerco round, and WebSocket session flows.

---

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Tactical Skirmish (Novak & Koema vs Invasor Swarm) | F4, F5, F7, F8, F9, F10, F11, F12, F13, F14 | High |
| 2 | Death Save Dramatic Comeback (Natural 20 Revive under Fire) | F8, F9, F10, F23, F24 | Medium |
| 3 | Cerco Round 1-3 Simultaneous Sync & Fortress Excavation | F16, F17, F18, F19, F20, F21, F22 | High |
| 4 | Boss Caste Encounter (Libélula Blindada / Enxame Rainha Inverted) | F8, F15, F21, F23, F25 | High |
| 5 | Co-op 2-Player WebSocket Session (Room Join -> Sync Card -> Move -> End) | F1, F2, F18, F26, F27, F28 | Very High |

---

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: $\ge 5$ test cases per feature ($28 \times 5 = 140$ tests).
- **Tier 2 (Boundary & Corner Cases)**: $\ge 5$ test cases per feature ($28 \times 5 = 140$ tests).
- **Tier 3 (Cross-Feature Pairwise)**: $\ge 28$ interaction test cases.
- **Tier 4 (Real-World Scenarios)**: $\ge 5$ end-to-end integration scenarios.
- **Total Minimum Target**: $\ge 313$ assertions / test cases passing with exit code 0.
