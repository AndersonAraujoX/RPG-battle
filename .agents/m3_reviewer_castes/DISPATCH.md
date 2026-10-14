# DISPATCH

## 2026-09-30T22:00:30Z
Review and verify Milestone 3 deliverables:
1. `godot_project/scripts/resources/IsectumCasteData.gd` and `godot_project/scripts/cerco/IsectumCastes.gd`:
   - Verify all 24 canonical Isectum castes are implemented with unique stats, traits, and archetypes (Brutamontes, Infiltrador, Catapulta, Voador, Boss).
   - Verify archetype queries and factory instantiation.
2. `godot_project/scripts/cerco/ThreatDeck.gd`:
   - Verify wave generation, difficulty scaling, perimeter spawn zone assignment (4 spawn zones).
   - Verify draw, discard, and shuffle cycles.
   - Verify Rune and Defense card reactions.
3. Tests & Memory:
   - Run `./godot_project/run_gut_tests.sh` and confirm all 276 tests pass with exit code 0.
   - Run `./godot_project/bin/godot --headless --verbose --path ./godot_project -s addons/gut/gut_cmdln.gd -gexit` and verify 0 ObjectDB leaks at exit.
4. Deliver your handoff.md in your working directory with an explicit verdict: APPROVE or REQUEST_CHANGES, and notify parent.
