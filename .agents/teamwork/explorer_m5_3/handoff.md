# Handoff Report: Milestone M5 — Act II Encounters & GUT Test Architecture

**Agent**: Explorer 3 (`explorer_m5_3`)  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3`  
**Milestone**: M5 (Conteúdo Ato II: Túneis Vivos — Encontros e Arquitetura de Testes GUT)  
**Parent Agent ID**: `aa7d5d2d-ef0f-482c-be6b-93c1793915c2`  
**Deliverable Path**: `/home/anderson/Documents/projeto/RPG-battle/.agents/teamwork/explorer_m5_3/handoff.md`  

---

## 1. Observation

Direct, verifiable observations from the codebase, documentation, and test infrastructure:

1. **GUT Test Infrastructure Baseline**:
   - Command: `bash godot_project/run_gut_tests.sh`
   - Direct execution result:
     ```
     Test Scripts Executed: 40
     Tests Run:             873
     Tests Passed:          873
     Tests Failed:          0
     Total Assertions:      9559
     Assertions Passed:     9559
     Assertions Failed:     0
     Exit code: 0
     ```
   - 100% green test baseline with 0 memory leaks. All tests adhere to the AAA pattern.

2. **Campaign Specification (`CAMPANHA_ROGUELIKE.md`)**:
   - Lines 59–79 (*ATO II — MEIO: "A Descida pelos Túneis Vivos"*):
     - Line 64: *"Escuridão subterrânea (visibilidade reduzida ao redor das tochas dos heróis), paredes bioluminescentes e som abafado de milhares de asas vibrando."*
     - Lines 66–71: Tier 2 Castes:
       - *Louva-Deus Ceifador* (`louva_deus_ceifador`): duelista letal de dano crítico.
       - *Vespa Caçadora* (`vespa_cacadora`): voadora, ignora terreno difícil.
       - *Aranha Clepto* (`aranha_clepto`): salta obstáculos e embosca defensores.
       - *Libélula Blindada* (`libelula_blindada`): alta esquiva, mobilidade e bombardeio sítico.
       - *Infiltrador & Vagalume das Sombras* (`infiltrador`, `vagalume_sombras`): furtividade, ofuscamento e emboscada.
     - Line 73: *"Casulos de Quitina: estruturas no tabuleiro que eclodem após 3 rodadas se não forem destruídas."*
     - Line 75: *"Mini-Chefe de Elite: 🦗 Cigarra Ressonante (`cigarra_ressonante`) — emite ondas sônicas que aplicam Atordoado em área se os heróis ficarem agrupados."*
     - Lines 76–78: *"Chefe do Ato II: 👑 Rainha do Enxame (`rainha_do_enxame`) — Possui habilidade `chamado_da_rainha` (reabastece ninhadas continuamente a cada 2 turnos) e protege-se atrás de guardas reais."*
     - Line 78: *"Gancho de Transição (Ato II ➔ Ato III): Antes de morrer, a Rainha libera um grito psíquico: 'Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!'."*

3. **Current Encounter Generator (`godot_project/scripts/run/combat/CombatEncounterGenerator.gd`)**:
   - Lines 11–25: `CASTE_ALIASES` maps aliases to canonical caste IDs from `IsectumCastes.gd`. Currently lacks canonical aliases for `louva_deus_ceifador`, `vespa_cacadora`, `aranha_clepto`, `libelula_blindada`, `infiltrador`, `vagalume_sombras`, `rainha_do_enxame`, and `guarda_real`.
   - Lines 52–59: `ACT_2_COMBAT_POOL` defines the Tier 2 combat pool:
     ```gdscript
     const ACT_2_COMBAT_POOL: Array[String] = [
         IsectumCastes.ID_VESPA_FURTIVA,
         IsectumCastes.ID_LOUVA_DEUS_CEIFADOR,
         IsectumCastes.ID_CENTOPEIA_VENENOSA,
         IsectumCastes.ID_LIBELULA_BOMBARDEIRA,
         IsectumCastes.ID_VAGALUME_CEGO,
         IsectumCastes.ID_ARANHA_SALTADORA,
     ]
     ```
   - Lines 301–332: `_generate_elite_squad` currently generates Act 1 leaders (`ACT_1_ELITE_LEADERS`) even when called for Act 2! It does not yet generate the mini-boss **Cigarra Ressonante**.
   - Lines 376–412: `_generate_boss_squad` for `act == 2` assigns a placeholder 85 HP queen with 2 furtive wasps, lacking the 200 HP statline, the Royal Guards (Guarda Real) with 50% damage reduction, the transition hook quote, and initial cocoons.
   - Lines 208–222: Return dictionary contains `squad`, `enemies`, `hazards`, `rules`, `rewards`, `forced_waves`, but lacks top-level `cocoons` array and cocoon spatial integration.

4. **Peer Explorer Alignment**:
   - **Explorer 1 (`explorer_m5_1/handoff.md`)**:
     - `TorchLighting.gd` (RefCounted): Chebyshev distance radius 3 centered on living heroes. Relic `tocha_eterna` increases radius by +2 (effective radius 5 = 121 cells). Methods: `update_visibility(heroes_positions, bonus_radius)`, `is_cell_lit(cell)`, `get_lit_cells()`, `can_target_cell(attacker, target, range)` (blocks ranged into darkness), `get_shroud_modifiers(enemy_pos)` (+2 AC, blocks ranged).
     - `ChitinCocoon.gd` (RefCounted): 15 HP, 10 AC, 3-turn hatch countdown (`hatch_countdown = 3`). Method `apply_damage(amount)` reduces HP; if `<= 0`, sets `is_destroyed = true` and permanently cancels hatching. `tick_round(grid, rng)` decrements countdown; at 0, spawns Tier 2 unit in adjacent free cell and deals 5 acid damage to adjacent cells (`acid_burst`).
   - **Explorer 2 (`explorer_m5_2/handoff.md`)**:
     - `CigarraRessonante.gd` (extends `Character`): 70–90 HP (default 80), AC 15, move speed 5, flyer. Imunne to stun (`add_status_effect("stunned") == false`). Hability `pulso_sonico(target_pos, heroes, rng)`: checks if $\ge 2$ living heroes are within Chebyshev distance $\le 2$; if clustered, deals AoE sonic damage and inflicts `stunned` for 1 round. If isolated, deals damage without stun.
     - `RainhaDoEnxame.gd` (extends `Character`): 180–220 HP (default 200), AC 16. Royal Guard passive: `register_royal_guard(guard)`, `has_living_royal_guard() -> bool`. `take_damage(amount)` reduces damage by 50% (`effective = int(amount * 0.5)`) while any guard is alive; normal 100% damage when guards are dead. Hability `chamado_da_rainha(grid, count, rng)` invoked periodically every 2 turns (`turn_counter % 2 == 0`). Defeat emits `transition_narrative_triggered` with canonical quote: `"Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"`.

---

## 2. Logic Chain

From the observations above, the system integration and test architecture follow these precise steps:

```
[M5 Act II Requirements]
        │
        ├──► 1. CombatEncounterGenerator.gd Enhancements
        │       ├── Caste Aliases: louva_deus_ceifador, vespa_cacadora, aranha_clepto,
        │       │   libelula_blindada, infiltrador, vagalume_sombras, rainha_do_enxame, guarda_real.
        │       ├── ACT_2_COMBAT_POOL & ACT_2_SIEGE_POOL formalization.
        │       ├── ACT_2_ELITE: Mini-boss Cigarra Ressonante (80 HP, AC 15, speed 4, pulso_sonico).
        │       ├── ACT_2_BOSS: Rainha do Enxame (200 HP, AC 16, 2 Royal Guards, transition hook).
        │       ├── ChitinCocoon Generation: _generate_act2_cocoons() placing 1-3 cocoons with
        │       │   anti-collision against unit spawns. Integrated in both `enc["cocoons"]` and `enc["hazards"]`.
        │
        ├──► 2. Test Suite Architecture: test_act2_mechanics.gd
        │       ├── Part A: TorchLighting
        │       │   ├── Chebyshev radius 3: 49 cells centered at (10, 10).
        │       │   ├── Boundary tests: (0, 0) -> 16 cells, (19, 19) -> 16 cells.
        │       │   ├── Empty hero array: 0 lit cells, all cells dark.
        │       │   ├── Dead hero positions ignored (omitted from positions array).
        │       │   ├── Relic tocha_eterna: radius 5 (121 cells centered).
        │       │   └── Darkness combat rules: blocks ranged into dark, allows melee, shrouds enemies.
        │       ├── Part B: ChitinCocoon
        │       │   ├── Stats: 15 HP, 10 AC, countdown 3 turns.
        │       │   ├── Countdown decrement: 3 -> 2 -> 1 via tick_round().
        │       │   ├── HP damage & destruction: overkill clamped to 0, emits destroyed.
        │       │   ├── Cancellation: destroyed at turn 1 cancels subsequent tick_round().
        │       │   ├── Hatching at 0: spawns T2 unit in adjacent cell, deals 5 acid damage.
        │       │   └── Corner boundary: acid damage only on in-bounds cells (0, 0 -> 3 cells).
        │       └── Part C: Cigarra Ressonante
        │           ├── Mini-boss stats & native stun immunity.
        │           ├── pulso_sonico clustering trigger (>= 2 heroes within Chebyshev dist <= 2).
        │           ├── AoE sonic damage & stun condition application.
        │           └── Isolated hero: damage dealt without stun application.
        │
        └──► 3. Test Suite Architecture: test_boss_swarm_queen.gd
                ├── Part A: Boss Stats & Initialization
                │   ├── 180-220 HP (default 200), AC 16, team B, is_boss = true.
                │   └── Caste data verification via IsectumCastes.
                ├── Part B: Royal Guard Protection Passive (50%)
                │   ├── 1+ guards alive: 20 damage -> 10 damage (50% reduction).
                │   ├── Odd damage rounding: 15 damage -> 7 damage.
                │   ├── All guards dead: 20 damage -> 20 damage (100% normal damage).
                │   └── Progressive defeat: multiple guards tracked dynamically.
                ├── Part C: Chamado da Rainha Brood Summoning
                │   ├── Turn 1: does not summon.
                │   ├── Turn 2: triggers summoning (>= 2 brood units, signal emitted).
                │   ├── Turn 3: cooldown.
                │   └── Turn 4: triggers summoning again.
                └── Part D: Transition Narrative Hook Upon Defeat
                    ├── HP reduced to 0 triggers boss_defeated and transition_narrative_triggered.
                    ├── Exact quote match: "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"
                    └── Target mechanic points to "tres_coracoes_colmeia" for Act III.
```

---

## 3. Caveats

1. **Bare-Node Headless Lifecycle**:
   Classes inheriting from `Character` (`CharacterBody2D`) require `autofree()` in GUT tests to prevent orphan node leaks when run headlessly in CI/CLI. Classes extending `RefCounted` (`TorchLighting`, `ChitinCocoon`, `CombatEncounterGenerator`) are automatically garbage-collected and must not be wrapped in `autofree()`.
2. **Backward Compatibility of Encounter Data**:
   Consumers of `CombatEncounterGenerator` may expect environmental obstacles in `hazards` (such as `FortressBoard.gd` or `RunCombatBridge.gd`) while new M5 code expects `cocoons`. To maintain 100% backward compatibility, `CombatEncounterGenerator` populates `cocoons` as a dedicated array **and** appends each cocoon dictionary into `hazards` with `"type": "COCOON"`.
3. **Deterministic Seeding**:
   `CombatEncounterGenerator._pick_spawn_cell` and `_generate_act2_cocoons` must share the same `occupied_cells` dictionary during encounter generation to strictly prevent unit-cocoon or unit-unit spatial collisions.

---

## 4. Conclusion

The Act II encounter generation and test architecture are fully designed and drafted in working directory artifacts:

| Proposed Artifact | Target Location in Project | Purpose |
|-------------------|----------------------------|---------|
| `proposed_CombatEncounterGenerator.gd` | `godot_project/scripts/run/combat/CombatEncounterGenerator.gd` | Act II Tier 2 enemy pools, mini-boss Cigarra Ressonante, Boss Rainha do Enxame, Royal Guards, and ChitinCocoon placement. |
| `proposed_test_act2_mechanics.gd` | `godot_project/test/unit/test_act2_mechanics.gd` | Comprehensive GUT suite covering TorchLighting, ChitinCocoon, and Cigarra Ressonante. |
| `proposed_test_boss_swarm_queen.gd` | `godot_project/test/unit/test_boss_swarm_queen.gd` | Comprehensive GUT suite covering Swarm Queen stats, Royal Guard 50% damage reduction, periodic brood summoning, and transition narrative hook. |
| `proposed_test_combat_encounter_generator_additions.gd` | `godot_project/test/unit/test_combat_encounter_generator.gd` | Regression and feature tests for Act II encounter generator additions. |

---

## 5. Verification Method

To independently verify the implementation once applied by the worker:

1. **Run the Complete GUT Test Suite**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   bash run_gut_tests.sh
   ```
   **Expected Outcome**: 100% of tests pass (exit code 0), zero failures, zero orphan nodes.

2. **Verify Specific Milestone M5 Suites**:
   ```bash
   godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_act2_mechanics.gd
   godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_boss_swarm_queen.gd
   godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_combat_encounter_generator.gd
   ```

3. **Check Spatial Anti-Collision Guarantee**:
   Inspect `test_act2_spatial_anti_collision_between_units_and_cocoons()`: verifies that no two units or cocoons occupy the same coordinate on the 20x20 grid under deterministic seeding.

4. **Check Exact Transition Narrative Quote**:
   Inspect `test_transition_narrative_hook_triggered_upon_defeat()`: asserts string equivalence with `"Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"`.

5. **Check Damage Reduction Clamp**:
   Inspect `test_royal_guard_50_percent_damage_mitigation_when_guard_alive()` and `test_normal_100_percent_damage_when_all_guards_are_dead()`: validates 50% reduction with living guards and 100% damage once guards are dead.
