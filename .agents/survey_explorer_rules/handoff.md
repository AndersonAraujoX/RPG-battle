# Handoff Report: Tactical Combat Rules, Grid Navigation, and Combat Resolution

**Agent**: `survey_explorer_rules`  
**Working Directory**: `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/`  
**Recipient**: `parent` (ID: `78d1f55b-e175-4f36-a462-ec295a59b44a`)  
**Type**: Hard Handoff (Investigation & Specification Phase Complete)  

---

## 1. Observation

Direct code observations from the reference Python codebase:

1. **Grid Representation & Boundaries**:
   - `src/tabuleiro.py:5-13`: `Tabuleiro(largura=20, altura=20)` initializes a 20x20 2D list `grid[y][x]` and `terrain_grid[y][x]`.
   - `src/tabuleiro.py:105-118`: `adicionar_limitadores()` sets row 0, row 19, col 0, and col 19 to `TERRENO_PAREDE`, bounding combat to internal cells.
   - `src/config.py:75-77`: `TAMANHO_CELULA = 30`, grid dimension is 600x600 pixels.
   - `src/utils.py:99-100`: `calcular_distancia(p1, p2)` computes Chebyshev distance: `max(abs(p1.pos_x - p2.pos_x), abs(p1.pos_y - p2.pos_y))`.

2. **Terrain Types & Destructible Structures**:
   - `src/config.py:158-171`: Defines `TERRENO_NORMAL`, `TERRENO_FLORESTA`, `TERRENO_DIFICIL`, `TERRENO_PAREDE`, `TERRENO_GELO`, `TERRENO_FOGO`, `TERRENO_AGUA`, `TERRENO_ROCHA`, `TERRENO_BARRIL`, `TERRENO_CAMPO`, `TERRENO_EXTERIOR`, `TERRENO_CORREDOR`, `TERRENO_MURALHA_LO`, `TERRENO_SUBSOLO`.
   - `src/tabuleiro.py:13`: Structures (`FLORESTA`, `ROCHA`, `BARRIL`) have 20 initial HP in `estrutura_hp_grid`.
   - `src/tabuleiro.py:31-39`: `aplicar_dano_estrutura(x, y, dano)` reduces HP; when $\le 0$, tile converts to `TERRENO_DIFICIL` (debris).
   - `src/tabuleiro.py:252-277`: `aplicar_dano_terreno(x, y, tipo_dano)` converts `FLORESTA` $\to$ `FOGO`, `GELO` $\to$ `AGUA` on fire, and `AGUA` $\to$ `GELO`, `FOGO` $\to$ `NORMAL` on ice.
   - `src/motor_combate.py:144-148`: Unit standing on `TERRENO_FOGO` suffers `random.randint(1, 6)` fire damage at start of turn.
   - `src/motor_combate.py:447-454, 831-863`: Moving into `TERRENO_GELO` triggers a 50% slip check (`random.random() < 0.5`) to slide to an adjacent free tile.

3. **Pathfinding & Movement**:
   - `src/tabuleiro.py:41-78`: `encontrar_caminho()` uses 4-directional BFS with orthogonal steps `((0, -1), (0, 1), (-1, 0), (1, 0))`.
   - `src/motor_combate.py:353-385`: `_astar_pathfinding()` uses 8-directional A* with diagonals: `[(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]`. Cost is 2 for `TERRENO_DIFICIL`, 1 for normal. Skips walls and occupied cells.
   - `src/motor_combate.py:245-260`: `_verificar_ataques_de_oportunidade()` checks if moving character leaves melee range (`dist <= 1`) of a living enemy with `alcance == 1`. If new distance is greater, enemy gets a free melee attack. Characters with status `"Desengajar"` are immune.

4. **Line of Sight & Cover Calculation**:
   - `src/tabuleiro.py:217-249`: `calcular_linha_visao(x1, y1, x2, y2, ignorar_personagens=False)` uses Bresenham line algorithm. Walls and living characters block line of sight.
   - `src/utils.py:184-219`: `calcular_cobertura(atacante, alvo, tabuleiro)`:
     - Passing through `TERRENO_PAREDE` returns `1000` (Total Cover).
     - Passing through an intervening creature returns `2` (Half Cover / Soft Cover).
     - Otherwise returns `0`.
   - `src/tabuleiro.py:15-29`: `obter_bonificacao_cobertura(x, y)`:
     - Adjacent to `FLORESTA` or `BARRIL` awards `+3 AC`.
     - Adjacent to `ROCHA` or `PAREDE` awards `+5 AC`.
   - `src/personagens/personagem_base.py:413-430`: Perks modify AC dynamically ("Muralha de Escudos" +2 AC with adjacent ally, "Mimetismo" +4 AC on Forest/Rock/Barrel).
   - `src/personagens/personagem_base.py:620-623`: Higher elevation (`elevacao > alvo.elevacao` with `alcance > 1`) grants Advantage on attack rolls.

5. **D&D 5e Combat Math & Advantage Cancellation**:
   - `src/personagens/personagem_base.py:433-447`: Modifiers are `(stat - 10) // 2`. Proficiency bonus is `1 + math.ceil(self.nivel / 4)`.
   - `src/utils.py:111-150`: `rolar_d20(vantagem=False, desvantagem=False)`:
     - If both `vantagem` and `desvantagem` are active: they strictly cancel out to standard roll `r1`.
     - If advantage only: `max(r1, r2)`.
     - If disadvantage only: `min(r1, r2)`.
   - `src/condicoes.py:3-82`: Implements Advantage/Disadvantage evaluation for Blinded, Poisoned, Prone (melee advantage $\le 1.5$m, ranged disadvantage $> 1.5$m), Invisible, Paralyzed, Stunned, Unconscious, Petrified, Frightened, Restrained, Dodge, and Help.
   - `src/personagens/personagem_base.py:606-618`: Flanking grants Advantage if attacker and ally with reach 1 are diametrically opposite across target (`dx_self == -dx_ally and dy_self == -dy_ally`).
   - `src/condicoes.py:84-95`: Auto-Crit occurs if target is Paralyzed or Unconscious, distance $\le 1.5$, and attack hits (`total >= AC`).
   - `src/personagens/personagem_base.py:678-685`: Critical hits double damage dice count (`num_rolagens = dado_dano[0] * 2`), while flat modifiers are added once.

6. **Damage Types, Resistances & Vulnerabilities**:
   - `src/config.py:137-150`: 14 damage types defined.
   - `src/personagens/personagem_base.py:691-723`:
     - Immunity: damage becomes 0.
     - Vulnerability: damage multiplied by 2.0.
     - Resistance: damage multiplied by 0.5.
     - Rounding: `int(round(dano_final))`.
     - Percent damage reduction from status effects (e.g. Fúria 25%) subtracted afterwards.

7. **Death Saving Throws**:
   - `src/personagens/personagem_base.py:724-749`: At 0 HP, falls `INCONSCIENTE` (unless perk "Última Linha" sets HP to 1). Counters reset to 0/3. Taking damage while unconscious increments `death_saves_failures` by 1. At 3 failures, character dies.
   - `src/personagens/personagem_base.py:769-804`: `realizar_teste_morte()` rolls 1d20:
     - Natural 20: recovers 1 HP, revives to `NORMAL`, resets counters.
     - Natural 1: 2 failures added.
     - 10–19: 1 success.
     - 2–9: 1 failure.
     - 3 successes: `ESTABILIZADO` (remains at 0 HP, stops rolling).
     - 3 failures: `MORTO`.

8. **Cerco contra Isectum System (`juiz_combate.py`)**:
   - Custom D6: Faces 1-2 = 1 Impact; Face 3 = 2 Impacts; Face 4 = 3 Impacts; Faces 5-6 = 1 Balestra Shot.
   - Melee: Same zone only; Damage = `impactos // 2` (odd discarded). Flanking ($\ge 2$ allies) = `+1 D6`.
   - Balestra Ranged: Towers only; 1 Shot = 1 Damage. Elevation advantage = `+1 D6`, disadvantage = `-1 D6`.
   - Brutamontes: 3 circles of HP, 2 damage/turn per circle. Unspent damage does not carry over between rounds (`resetar_dano_turno_brutamonte`).

9. **Canonical Tests in `tests/`**:
   - 27 test files present. 12 files directly test combat and board invariants: `test_cover.py`, `test_tabuleiro.py`, `test_pathfinding_swarm.py`, `test_death_saves.py`, `test_saving_throws.py`, `test_status_effects.py`, `test_damage_types.py`, `test_action_economy.py`, `test_core_mechanics.py`, `test_cerco_rules.py`, `test_class_mechanics.py`, `teste_perks.py`.

---

## 2. Logic Chain

1. **Grid & Navigation Parity**:
   - From Observation 1 & 3: The tactical map is 20x20 with outer border walls, Chebyshev distance metric, 8-directional movement with diagonal cost 1, and terrain multiplier 2 for difficult terrain.
   - Inference: Godot 4's native `AStar2D` can model this with 400 point IDs (`y * 20 + x`), 8-way point connections, `weight_scale = 2.0` on `TERRENO_DIFICIL`, and disabled points on walls and occupied cells.

2. **Line of Sight & Cover Parity**:
   - From Observation 4: Cover is bipartite: raycast cover (+2 for intervening creatures, 1000 for walls) and tactical adjacent cover (+3 for forest/barrel, +5 for rock/wall).
   - Inference: `TacticalGrid.gd` must implement both `calculate_raycast_cover(from, to)` via Bresenham raycasting and `get_adjacent_cover_bonus(pos)` checking the 8-neighbor Moore neighborhood.

3. **Attack Resolution & Mathematical Parity**:
   - From Observation 5: D&D 5e mechanics require a strict cancellation rule (if both advantage and disadvantage are present, roll a single d20). Attack hits if roll + attack_bonus $\ge$ target AC. Critical hits occur on natural 20 or auto-crit on paralyzed/unconscious targets within 1.5m.
   - Inference: `CombatRules.gd` must duplicate this exact roll logic. Critical damage doubles dice count while leaving flat modifiers unchanged.

4. **Resilience & State Transitions**:
   - From Observation 6 & 7: Zero HP clamps to 0 and transitions to `INCONSCIENTE` (unless Last Stand perk triggers). Damage while unconscious inflicts death save failures. Death save rolls obey D&D 5e RAW (nat 20 = 1 HP revive, nat 1 = 2 fails, 3 fails = dead, 3 succ = stabilized).
   - Inference: `DeathSaves.gd` / `CharacterStats.gd` must implement this finite state machine without deviating from these thresholds.

5. **Cerco Engine Parity**:
   - From Observation 8: Cerco combat resolution is separate from the 20x20 tactical engine. It operates on discrete fortress zones and custom D6 mappings.
   - Inference: `CercoCombatJudge.gd` must be an independent pure GDScript rule engine that translates D6 rolls into impacts and shots according to `FACES_D6`.

---

## 3. Caveats

- **Pygame Dependency in Python Tests**: Running `python3 -m unittest` in the current Linux environment fails because `pygame` is not installed globally. However, the Python test files and source code were thoroughly inspected line by line to extract all assertions, inputs, and expected outputs.
- **Deckbuilder / Cerco Cards Track**: Specific card effects and synergies are analyzed by the Deckbuilder track; this investigation focused strictly on combat resolution, dice rules, movement/navigation, cover, and status conditions.
- No other caveats.

---

## 4. Conclusion

The tactical combat and navigation rules have been completely analyzed and documented in `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/analysis.md`. The design is fully specified for implementation in Godot 4 using pure, statically typed GDScript classes (`TacticalGrid.gd`, `CombatRules.gd`, `DeathSaves.gd`, `StatusEffectManager.gd`, `CercoCombatJudge.gd`), and can be validated autonomously using headless GUT unit tests mirroring `tests/`.

---

## 5. Verification Method

To verify these findings:
1. **Inspect Specification Files**:
   - `/home/anderson/Documents/projeto/RPG-battle/.agents/survey_explorer_rules/analysis.md` (Detailed analysis and GDScript signatures).
   - `/home/anderson/Documents/projeto/RPG-battle/src/tabuleiro.py` (Lines 15-78, 217-277).
   - `/home/anderson/Documents/projeto/RPG-battle/src/motor_combate.py` (Lines 353-385, 413-440, 580-608, 911-1000).
   - `/home/anderson/Documents/projeto/RPG-battle/src/personagens/personagem_base.py` (Lines 433-470, 587-690, 724-804).
   - `/home/anderson/Documents/projeto/RPG-battle/src/condicoes.py` (Lines 3-95).
   - `/home/anderson/Documents/projeto/RPG-battle/src/juiz_combate.py` (Lines 52-270).
2. **Unit Test Invariant Verification**:
   - Compare `analysis.md` Section 5 with `tests/test_cover.py`, `tests/test_pathfinding_swarm.py`, `tests/test_damage_types.py`, and `tests/test_death_saves.py`.
3. **Invalidation Conditions**:
   - Any proposed Godot 4 combat engine implementation that doubles flat modifiers on critical hits violates D&D 5e parity (`personagem_base.py:678-685`).
   - Any pathfinder that does not support diagonal movement or ignores difficult terrain cost (2.0) violates `_astar_pathfinding` parity (`motor_combate.py:367-375`).
   - Any death save mechanism that revives on 3 successes instead of stabilizing at 0 HP violates `realizar_teste_morte` parity (`personagem_base.py:796-800`).
