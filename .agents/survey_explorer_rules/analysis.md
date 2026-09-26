# Comprehensive Technical Survey: Tactical Combat Rules, Grid Navigation, and Combat Resolution

**Target**: Godot Engine 4 (GDScript Statically Typed)  
**Author**: `survey_explorer_rules`  
**Reference Source Files**: `src/tabuleiro.py`, `src/motor_combate.py`, `src/juiz_combate.py`, `src/condicoes.py`, `src/personagens/status_efeito.py`, `src/personagens/personagem_base.py`, `src/utils.py`, `src/config.py`, `tests/`  

---

## 1. Executive Summary & Problem Boundary

This document provides the authoritative technical specification of the tactical combat engine, grid navigation, and combat resolution systems of the RPG-battle project. The objective is to achieve **100% mechanical parity** when migrating from the reference Python implementation to Godot Engine 4 using statically typed GDScript, headless GUT testing, and native engine primitives (such as `AStar2D`, `Vector2i`, and custom `Resource` definitions).

The project contains two complementary combat subsystems:
1. **D&D 5e Tactical Combat (Grid 20x20)**: Turn-based tactical simulation featuring d20 rolls, proficiency scaling, Chebyshev distance, 8-directional A* navigation, line-of-sight raycasting, soft/hard cover calculation, death saving throws, 14 damage types, and 23 distinct status conditions.
2. **Cerco contra Isectum Resolution Engine (`juiz_combate.py`)**: Asymmetric siege board game mechanics using custom D6 dice, physical impacts, balestra ranged shots, tower elevation advantage/disadvantage, and multi-circle Brutamonte boss HP tracking.

---

## 2. Grid & Navigation Technical Specification

### 2.1 Coordinate System & Boundaries
- **Dimensions**: Fixed 20x20 grid (width = 20, height = 20).
- **Indexing Convention**:
  - In Python: Row-major 2D matrix `grid[y][x]` and `terrain_grid[y][x]`.
  - In GDScript: `Vector2i(x, y)`. Coordinates obey `0 <= x < 20` and `0 <= y < 20`.
- **Pixel Mapping**:
  - Cell size: `TAMANHO_CELULA = 30` pixels.
  - Tactical board visual area: 600x600 pixels (`20 * 30`).
- **Limiting Walls (`adicionar_limitadores`)**:
  - Outer border tiles are permanently set to `PAREDE`:
    - Row 0: `(x, 0)` for `0 <= x < 20`
    - Row 19: `(x, 19)` for `0 <= x < 20`
    - Column 0: `(0, y)` for `0 <= y < 20`
    - Column 19: `(19, y)` for `0 <= y < 20`
  - Units cannot occupy or traverse these outer bounds.
- **Spawn Zones**:
  - **Team A (Players/Heroes)**: South border, rows 16 to 18 (`range(self.altura - 4, self.altura - 1)`).
  - **Team B (Enemies/Monsters)**: North border, rows 1 to 3 (`range(1, 4)`).
  - **Spawn Heuristic (`adicionar_personagem_na_borda`)**:
    - Candidate positions sorted by weight: `peso = dist_centro + (dist_borda_y * 5)`, where `dist_centro = abs(x - largura // 2)`.
    - Spacing algorithm attempts first to place units with no adjacent neighbors (`dx, dy in (-1, 0, 1)`), falling back to closest available position.

### 2.2 Terrain Types & Structural Mechanics
The tactical grid supports the following terrain constants:

| Terrain ID | Value (String) | Movement Cost | Cover Granted | Destructible | Transition Trigger / Notes |
|---|---|---|---|---|---|
| `TERRENO_NORMAL` | `"NORMAL"` | 1 | None (0 AC) | No | Standard open floor. |
| `TERRENO_FLORESTA`| `"FLORESTA"` | 1 | +3 AC (Adjacent) | Yes (20 HP) | Catches fire from `"Fogo"` damage -> `TERRENO_FOGO`. |
| `TERRENO_DIFICIL` | `"DIFICIL"` | 2 | None (0 AC) | No | Debris / rubble left by destroyed structures. |
| `TERRENO_PAREDE` | `"PAREDE"` | Blocked (inf) | +5 AC (Adjacent) / 1000 LoS | No | Total cover; blocks movement & line of sight. |
| `TERRENO_GELO` | `"GELO"` | 1 | None (0 AC) | No | 50% slip hazard on enter; melts to `TERRENO_AGUA` from Fire. |
| `TERRENO_FOGO` | `"FOGO"` | 1 | None (0 AC) | No | Deals 1d6 fire damage at turn start; quenched to `NORMAL` by Ice. |
| `TERRENO_AGUA` | `"AGUA"` | 1 | None (0 AC) | No | Freezes to `TERRENO_GELO` when taking Ice damage. |
| `TERRENO_ROCHA` | `"ROCHA"` | Blocked | +5 AC (Adjacent) | Yes (20 HP) | Destructible rock cover; becomes `TERRENO_DIFICIL` at 0 HP. |
| `TERRENO_BARRIL` | `"BARRIL"` | Blocked | +3 AC (Adjacent) | Yes (20 HP) | Destructible barrel cover; becomes `TERRENO_DIFICIL` at 0 HP. |

#### Structural Damage Formula (`aplicar_dano_estrutura`)
- Grid `estrutura_hp_grid[y][x]` initialized to `20` for `FLORESTA`, `ROCHA`, and `BARRIL`, `0` elsewhere.
- When damage is applied:
  ```python
  estrutura_hp_grid[y][x] = max(0, estrutura_hp_grid[y][x] - dano)
  if estrutura_hp_grid[y][x] <= 0:
      terrain_grid[y][x] = TERRENO_DIFICIL
  ```

#### Elemental Terrains Interactions (`aplicar_dano_terreno`)
- **Damage Type `"Fogo"`**:
  - `FLORESTA` -> `FOGO`
  - `GELO` -> `AGUA`
- **Damage Type `"Gelo"`**:
  - `AGUA` -> `GELO`
  - `FOGO` -> `NORMAL` (extinguishes fire)

### 2.3 Pathfinding Specifications

Two algorithms exist in the reference code:

#### A. 4-Way BFS (`Tabuleiro.encontrar_caminho`)
- Allowed vectors: `(0, -1), (0, 1), (-1, 0), (1, 0)`.
- Traversal rule: Cannot enter `TERRENO_PAREDE` or occupied cell (unless occupied cell is destination).
- Returns list of `(x, y)` tuples excluding the origin. If `len(path) >= max_passos` or destination unreachable, returns `[]`.

#### B. 8-Way Tactical A* (`MotorCombate._astar_pathfinding`)
- Allowed vectors: 8 directions including diagonals:
  `[(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]`.
- Node cost: `2` if neighbor is `TERRENO_DIFICIL`, `1` otherwise.
- Obstacle rule: `TERRENO_PAREDE` and occupied tiles (`grid[ny][nx] is not None and neighbor != end_pos`) are impassable.
- Budget constraint: `tentative_g_cost > max_cost` skips expansion.
- Heuristic: Manhattan distance `abs(x1 - x2) + abs(y1 - y2)`.
- Returns reconstructed path `[(x1, y1), ..., (dest_x, dest_y)]` or `None`.

#### Godot 4 Native Mapping with `AStar2D`
To port this directly to Godot 4:
- Cell ID generation: `id = y * 20 + x`.
- Coordinate back-conversion: `pos = Vector2i(id % 20, id / 20)`.
- Weight scaling: Set point weight scale via `astar.set_point_weight_scale(id, 2.0)` for `TERRENO_DIFICIL`, `1.0` for normal.
- Disable impassable points: `astar.set_point_disabled(id, true)` for `TERRENO_PAREDE` and cells occupied by living characters.
- Diagonal connections: Connect adjacent 8 neighbors using `astar.connect_points(id1, id2, true)`.

### 2.4 Movement Execution, Slip Hazard & Opportunity Attacks

During stepwise execution along `caminho`:
1. **Opportunity Attack (`_verificar_ataques_de_oportunidade`)**:
   - Evaluated upon moving from `current_pos` to `step`.
   - Immunity: If unit has status `"Desengajar"` (Disengage), no opportunity attacks trigger.
   - Trigger condition: For each living enemy with melee reach (`alcance == 1`) adjacent at `current_pos` (`dist <= 1`), if new distance `abs(novo_x - inimigo.pos_x) + abs(novo_y - inimigo.pos_y) > dist_antiga`, enemy makes an immediate melee attack against the moving unit.
   - If unit dies, movement immediately halts.
2. **Ice Hazard (Slip)**:
   - If unit steps onto `TERRENO_GELO`, rolls `random.random() < 0.5`.
   - If slip triggers, unit slides 1 extra tile into an adjacent unoccupied, non-wall tile.
3. **Fire Hazard**:
   - At turn start (`proximo_passo`), if standing on `TERRENO_FOGO`, unit suffers `1d6` fire damage (`random.randint(1, 6)`).

### 2.5 Distance Metric
- Formula: Chebyshev Distance (D&D 5e diagonal rule):
  $$\text{dist}(p_1, p_2) = \max(|p_1.x - p_2.x|, |p_1.y - p_2.y|)$$
  A diagonal step costs 1 grid square (5 ft).

### 2.6 Elevation & Line of Sight (LoS)
- **Elevation Grid**: Stored in `elevation_grid[y][x]` (integers 0 to 6, default 0..2).
- **Advantage from Elevation**:
  - In tactical combat: If `atacante.elevacao > alvo.elevacao` and `atacante.alcance > 1` (ranged attack from high ground), the attacker gains **Advantage** on the attack roll.
  - In Cerco Balestra: Tower elevation > target elevation grants `+1 D6`; tower elevation < target elevation inflicts `-1 D6`.
- **Line of Sight Raycasting (`calcular_linha_visao`)**:
  - Uses the Bresenham line algorithm between `(x1, y1)` and `(x2, y2)`.
  - Evaluates intermediate points (excluding start point):
    - If `terrain_grid[y][x] == TERRENO_PAREDE`: LoS is **blocked** (`return False`).
    - If `not ignorar_personagens` and `grid[y][x] is not None`: LoS is **blocked** (`return False`).
- **Fog of War Visibility**:
  - Vision radius: `raio_visao = 8` tiles.
  - Team A characters reveal tiles where Euclidean distance $\le 8$ and `calcular_linha_visao(p.x, p.y, x, y, ignorar_personagens=True)` is true.

### 2.7 Cover Calculation Systems

Two distinct cover systems exist in the codebase:

#### 1. Dynamic Raycast Cover (`calcular_cobertura(atacante, alvo, tabuleiro)`)
Evaluates the Bresenham line between attacker and target:
- If ray hits `TERRENO_PAREDE` $\to$ returns **1000** (Total Cover / Blocked).
- If ray passes through another creature (`char != atacante and char != alvo`) $\to$ returns **+2** (Half Cover / Soft Cover).
- Otherwise $\to$ returns **0** (No Cover).

In `Personagem.atacar`:
- Target AC is augmented: `ac_alvo = alvo.ac + bonus_cobertura`.
- If `bonus_cobertura >= 1000`: Target has Total Cover (Line of sight completely blocked).
- If `bonus_cobertura >= 5`: Target has +5 AC (Three-quarters Cover).
- If `bonus_cobertura >= 2`: Target has +2 AC (Half Cover).

#### 2. Adjacent Tactical Terrain Cover (`obter_bonificacao_cobertura(x, y)`)
Evaluates the 8 adjacent tiles around character `(x + dx, y + dy)`:
- If adjacent to `FLORESTA` or `BARRIL`: `bonus = max(bonus, 3)` (+3 AC).
- If adjacent to `ROCHA` or `PAREDE`: `bonus = max(bonus, 5)` (+5 AC).

#### 3. Defensive Perks Modifying AC
- **Muralha de Escudos** (Novak Perk): +2 AC if at least 1 living ally is adjacent ($\text{dist} \le 1.5$).
- **Mimetismo** (Koema Perk): +4 AC when standing directly in `FLORESTA`, `ROCHA`, or `BARRIL`.

---

## 3. Combat Math & D&D 5e Mechanics Specification

### 3.1 Attributes, Modifiers & Proficiency
- Six core attributes: Strength (`forca`), Dexterity (`destreza`), Constitution (`constituicao`), Intelligence (`inteligencia`), Wisdom (`sabedoria`), Charisma (`carisma`).
- **Modifier Formula**:
  $$\text{mod} = \lfloor(\text{stat} - 10) / 2\rfloor$$
  Examples: 10 $\to$ +0; 12 $\to$ +1; 14 $\to$ +2; 16 $\to$ +3; 18 $\to$ +4; 20 $\to$ +5; 9 $\to$ -1.
- **Proficiency Bonus Formula**:
  $$\text{bonus\_proficiencia} = 1 + \lceil\text{nivel} / 4\rceil$$
  - Level 1: $1 + \lceil 0.25 \rceil = 2$.
  - Level 2–4: +2.
  - Level 5–8: +3.
  - Level 9–12: +4.

### 3.2 Attack Roll & Armor Class (AC)
- Attack roll formula:
  $$\text{total\_ataque} = \text{rolagem\_d20} + \text{bonus\_ataque}$$
  Where `bonus_ataque = bonus_proficiencia + sum(status_ataque_fixo)`.
- Armor Class formula:
  $$\text{AC}_{\text{final}} = (\text{armadura\_equipada.bonus\_ac} \text{ or } \text{ac\_base}) + \text{bonus\_cobertura} + \text{bonus\_perks}$$
- **Hit Condition**: An attack hits if:
  $$\text{total\_ataque} \ge \text{AC}_{\text{final}}$$

### 3.3 Advantage / Disadvantage System
- Dice function: `rolar_d20(vantagem=False, desvantagem=False)`.
- Rolls two independent d20 values: $r_1, r_2 \in [1, 20]$.
- **Cancellation Rule**: If both `vantagem` and `desvantagem` are active, they **strictly cancel out**, reverting to a normal roll:
  $$\text{result} = r_1$$
- **Advantage Only**:
  $$\text{result} = \max(r_1, r_2)$$
- **Disadvantage Only**:
  $$\text{result} = \min(r_1, r_2)$$

#### Complete Advantage / Disadvantage Conditions Matrix

| Condition | Target / Source | Effect on Attack Roll | Reference Code Location |
|---|---|---|---|
| **Flanking** | Attacker & Ally opposite target | **Advantage** | `personagem_base.py:606-618` |
| **High Ground** | Attacker elevation > Target (ranged) | **Advantage** | `personagem_base.py:620-623` |
| **Invisível (Attacker)** | Attacker is Invisible | **Advantage** | `condicoes.py:38-40` |
| **Cego (Target)** | Target is Blind | **Advantage** | `condicoes.py:17-19` |
| **Caído (Target Melee)** | Target is Prone, distance $\le 1.5$ | **Advantage** | `condicoes.py:30-33` |
| **Incapacitado/Paralisado/Atordoado/Inconsciente/Petrificado** | Target has condition | **Advantage** | `condicoes.py:46-49` |
| **Contido (Target)** | Target is Restrained | **Advantage** | `condicoes.py:60-62` |
| **Alvo de Ajuda (Help)** | Target has Help buff | **Advantage** | `condicoes.py:69-72` |
| **Ataque Descuidado (Reckless)**| Barbarian active perk/skill | **Advantage** | `motor_combate.py:995` |
| **Cego (Attacker)** | Attacker is Blind | **Disadvantage** | `condicoes.py:14-16` |
| **Envenenado (Attacker)** | Attacker is Poisoned | **Disadvantage** | `condicoes.py:21-23` |
| **Caído (Attacker)** | Attacker is Prone | **Disadvantage** | `condicoes.py:26-28` |
| **Caído (Target Ranged)** | Target is Prone, distance $> 1.5$ | **Disadvantage** | `condicoes.py:34-36` |
| **Invisível (Target)** | Target is Invisible (without See Inv) | **Disadvantage** | `condicoes.py:41-43` |
| **Assustado (Attacker)** | Attacker is Frightened | **Disadvantage** | `condicoes.py:51-53` |
| **Contido (Attacker)** | Attacker is Restrained | **Disadvantage** | `condicoes.py:56-58` |
| **Esquiva (Target Dodge)** | Target activated Dodge | **Disadvantage** | `condicoes.py:64-66` |

### 3.4 Critical Hits
An attack is classified as a Critical Hit under two conditions:
1. **Natural 20**: The rolled d20 value is exactly 20 (`rolagem_ataque == 20`).
2. **Automatic Critical (`verificar_critico_automatico`)**:
   $$\text{target is } (\text{Paralisado} \lor \text{INCONSCIENTE}) \land \text{distancia} \le 1.5 \land \text{total\_ataque} \ge \text{AC}$$

#### Damage Dice Doubling Formula (`Personagem.causar_dano`)
- When critical: The **number of damage dice is doubled**, while flat modifiers remain single:
  $$\text{num\_rolagens} = \begin{cases} \text{dado\_dano}[0] \times 2 & \text{if is\_critico} \\ \text{dado\_dano}[0] & \text{otherwise} \end{cases}$$
  $$\text{dano\_rolado} = \sum_{i=1}^{\text{num\_rolagens}} \text{random}(1, \text{dado\_dano}[1])$$
  $$\text{dano\_total} = \max(1, \text{dano\_rolado} + \text{bonus\_dano} + \text{bonus\_dano\_extra})$$
- Example: A 1d8 weapon with +3 bonus on a normal hit deals $1d8 + 3$. On a Critical Hit, it deals $2d8 + 3$.

### 3.5 Damage Types & Damage Resilience Math
The engine implements 14 damage types:
`cortante`, `perfurante`, `contundente`, `fogo`, `gelo`, `eletrico`, `acido`, `veneno`, `necrotico`, `radiante`, `psiquico`, `forca`, `trovao`, `fisico`.

In `receber_dano(quantidade, ... tipo_dano)`:
1. **Immunity**: If `tipo_dano in self.imunidades` $\to$ damage is 0 (`return 0`).
2. **Vulnerability**: If `tipo_dano in self.vulnerabilidades` $\to$ damage is multiplied by 2.0.
3. **Resistance**: If `tipo_dano in self.resistencias` $\to$ damage is multiplied by 0.5.
4. **Rounding**: `dano_final = int(round(dano_final))`.
5. **Percent Reductions**: If character has active status with `resistencia_dano_percentual` (e.g. Fúria = 0.25), `dano_final -= int(dano_final * percent)`.

### 3.6 Death Saving Throws & State Transitions
- **State Machine**:
  ```
  [ NORMAL ] --(HP drops to 0)--> [ INCONSCIENTE ]
                                      |
         +----------------------------+----------------------------+
         | (Roll d20 == 20)           | (3 Successes)              | (3 Failures)
         v                            v                            v
    [ NORMAL ]                 [ ESTABILIZADO ]                [ MORTO ]
    (HP = 1)                   (0 HP, no saves)                (esta_vivo = false)
  ```
- **Zero HP Drop**:
  - `hp_atual` is clamped to 0.
  - Perk **Última Linha (Last Stand)**: If character has this perk and hasn't triggered it, `hp_atual = 1`, stays `NORMAL` (prevents unconsciousness once per battle).
  - Otherwise: `estado = "INCONSCIENTE"`, resets `death_saves_successes = 0`, `death_saves_failures = 0`.
- **Taking Damage While Unconscious**:
  - Receiving any damage while `INCONSCIENTE` inflicts **1 Death Save Failure**:
    `death_saves_failures += 1`.
  - If `death_saves_failures >= 3`, character dies immediately (`morrer()`).
- **Turn Roll Execution (`realizar_teste_morte`)**:
  On character's turn when unconscious, rolls 1d20:
  - **Natural 20**: Recovers 1 HP (`hp_atual = 1`), transitions to `"NORMAL"`, clears counters.
  - **Natural 1**: Suffers **2 failures** (`death_saves_failures += 2`).
  - **Roll 10 to 19**: 1 success (`death_saves_successes += 1`).
  - **Roll 2 to 9**: 1 failure (`death_saves_failures += 1`).
  - **Stabilization**: If `death_saves_successes >= 3`, transitions to `"ESTABILIZADO"`, resets counters.
  - **Death**: If `death_saves_failures >= 3`, calls `morrer()`, sets `estado = "MORTO"`, `esta_vivo = False`.

### 3.7 Saving Throws (`fazer_teste_resistencia`)
- Roll formula:
  $$\text{total} = \text{rolagem\_d20} + \text{modificadores}[\text{atributo}]$$
- Check: Successful if $\text{total} \ge \text{dificuldade (DC)}$.

### 3.8 Complete Status Conditions Catalog

| Condition Name | Duration | Properties / Data | Turn Tick Effect | Removal Condition |
|---|---|---|---|---|
| **Envenenado** | N turnos | Attack Disadvantage | Deals fixed damage: 2 HP per turn | `duracao_restante <= 0` or Antidote |
| **Atordoado** | N turnos | `pode_agir = False`, Attackers gain Advantage | None | `duracao_restante <= 0` |
| **Sangrando** | N turnos | Icon 'B', Red | Deals 5% max HP damage (`int(hp_max * 0.05)`) | `duracao_restante <= 0` |
| **Fúria** | N turnos | `bonus_dano_ataque = 2`, `resistencia_dano_percentual = 0.25`, `pode_fugir = False` | None | `duracao_restante <= 0` |
| **Amaldiçoado** | N turnos | `bonus_ataque_fixo = -2` | Deals fixed damage: 3 HP per turn | `duracao_restante <= 0` |
| **Provocado** | N turnos | `provocador = Character` | Forces movement & attack toward provocador | `duracao_restante <= 0` |
| **Defesa Quebrada**| N turnos | `bonus_ac_fixo = -3` (or -20% damage resistance) | None | `duracao_restante <= 0` |
| **Ataque Reduzido**| N turnos | `bonus_dano_ataque = -2`, `bonus_ataque_fixo = -2` | None | `duracao_restante <= 0` |
| **Ataque Aumentado**| N turnos | `bonus_dano_ataque = 2`, `bonus_ataque_fixo = 2` | None | `duracao_restante <= 0` |
| **Cego** | N turnos | Attacker Disadv / Target Adv | None | `duracao_restante <= 0` |
| **Caído (Prone)**| 100 turns | Attacker Disadv; Target Adv (melee) / Disadv (ranged) | Speed spent to stand | Action to stand up |
| **Invisível** | N turnos | Attacker Adv / Target Disadv | None | `duracao_restante <= 0` |
| **Paralisado** | N turnos | Incapacitated, Auto-Crit within 1.5m, Target Adv | None | `duracao_restante <= 0` |
| **Petrificado** | N turnos | Incapacitated, Target Adv | None | `duracao_restante <= 0` |
| **Assustado** | N turnos | Attack Disadvantage, cannot move toward fear source | None | `duracao_restante <= 0` |
| **Contido** | N turnos | Speed 0, Attack Disadvantage, Target Adv | None | `duracao_restante <= 0` |
| **Esquiva** | 1 turno | Target Disadvantage on attacks against self | None | Expires next turn start |
| **Alvo de Ajuda** | 1 turno | Next attack roll against target has Advantage | None | Next attack or turn end |
| **Agarrado** | 100 turns | Speed 0 | Athletics contest | Escape contest |
| **Desengajar** | 1 turno | Immune to Opportunity Attacks | None | Expires next turn start |
| **Dash** | 1 turno | Doubles movement range | None | Expires next turn start |
| **Lentidão** | N turnos | `velocidade_reducao = 2` | None | `duracao_restante <= 0` |
| **Inspirado** | N turnos | `bonus_velocidade = 2` | None | `duracao_restante <= 0` |

---

## 4. Cerco contra Isectum Combat Rules (`juiz_combate.py`)

In the Cerco mode, combat is resolved at the zone level rather than on the 20x20 cell grid.

### 4.1 Custom D6 Faces Distribution
- **Faces 1 and 2**: 1 Physical Impact (`impactos = 1, disparos = 0`).
- **Face 3**: 2 Physical Impacts (`impactos = 2, disparos = 0`).
- **Face 4**: 3 Physical Impacts (`impactos = 3, disparos = 0`).
- **Faces 5 and 6**: 1 Balestra Ranged Shot (`impactos = 0, disparos = 1`).

### 4.2 Melee Combat Resolution (`resolver_melee`)
- Hero must be in the same zone as enemy (`pos_heroi == zona_combate`).
- **Flanking Rule**: If `num_aliados_zona >= 2`, roll **+1 D6** (`num_dados += 1`).
- Physical Impacts convert to Damage:
  $$\text{dano} = \lfloor\text{impactos} / 2\rfloor \quad (\text{odd impacts discarded})$$
- Damage Allocation Priority:
  1. Common Invaders in zone (1 HP each, 1 damage kills 1 invader).
  2. Infiltrators in Patio (1 HP each, 1 damage kills 1 infiltrator).
  3. Brutamonte.

### 4.3 Ranged Combat Resolution (`resolver_distancia`)
- Attacker must be in a Watchtower (`torre_nw`, `torre_ne`, `torre_sw`, `torre_se`).
- Internal zones (`camara_central`, `curtume`, `carpintaria`, `fundicao`, `patio`) are **INVALID** targets.
- Valid targets: Adjacent walls, external fields (`campo_*`), or siege weapons (`catapulta_cerco`, `torre_assalto_inimiga`).
- **Elevation Advantage / Disadvantage**:
  - If `elev(defensor) > elev(alvo)`: **+1 D6** to roll.
  - If `elev(defensor) < elev(alvo)`: **-1 D6** to roll (minimum 1 D6).
- Damage:
  $$\text{dano} = \text{disparos} \quad (1 \text{ Disparo} = 1 \text{ Dano})$$

### 4.4 Brutamonte Multi-Circle HP System
- Total health circles: `BRUTAMONTE_CIRCULOS_HP = 3`.
- Damage threshold per circle: `BRUTAMONTE_DANO_POR_CIRCULO = 2` damage within a single turn.
- Accumulation logic:
  $$\text{novos\_circulos} = (\text{dano\_acumulado\_turno} + \text{dano}) // 2$$
- Brutamonte is defeated only when `circulos_marcados >= 3`.
- **Turn Reset Invariant (`resetar_dano_turno_brutamonte`)**:
  At the beginning of each new turn, `dano_turno_atual` is reset to 0. Unspent damage points do NOT carry over across rounds.

---

## 5. Canonical Tests & Edge Cases Audit

The test suite in `tests/` establishes the golden invariants that must pass in Godot's GUT suite:

| Test File | Test Case | Target Invariant & Assertion |
|---|---|---|
| `test_cover.py` | `test_obter_bonificacao_cobertura_floresta_concede_3_ac` | Adjacent `TERRENO_FLORESTA` awards exactly +3 AC. |
| `test_cover.py` | `test_obter_bonificacao_cobertura_rocha_concede_5_ac` | Adjacent `TERRENO_ROCHA` awards exactly +5 AC. |
| `test_cover.py` | `test_aplicar_dano_estrutura_destroi_terreno_vira_escombros`| Structure HP drops to 0 $\to$ tile transforms to `TERRENO_DIFICIL`, structure HP becomes 0, returns true. |
| `test_tabuleiro.py`| `test_tabuleiro_posicionamento_unidade` | Placing unit sets `grid[y][x] = unit`, unit `pos_x=x`, `pos_y=y`. |
| `test_tabuleiro.py`| `test_tabuleiro_limites_grid` | Boundary coordinates verified: `0 <= x < 20`, `0 <= y < 20`. |
| `test_tabuleiro.py`| `test_tabuleiro_movimentacao_unidade` | Moving cleans previous cell `grid[y1][x1] = None` and populates `grid[y2][x2]`. |
| `test_pathfinding_swarm.py`| `test_encontrar_caminho_retorna_rota_direta` | Path returns direct route excluding start pos, len=3 for 3 steps. |
| `test_pathfinding_swarm.py`| `test_encontrar_caminho_desvia_de_obstaculo_parede` | Path detours around wall obstacle, never includes wall coordinate. |
| `test_pathfinding_swarm.py`| `test_encontrar_caminho_respeita_limite_max_passos` | If path exceeds `max_passos`, returns empty list `[]`. |
| `test_pathfinding_swarm.py`| `test_calculo_leque_cartas_arco_simetrico` | Fan curve equation: $y = \lfloor (i - \text{mid})^2 \times 1.6 \rfloor$, center is 0, outer cards symmetric. |
| `test_death_saves.py`| `test_falling_unconscious` | HP reduced to 0 $\to$ status is `INCONSCIENTE`, character remains alive (`esta_vivo = True`). |
| `test_death_saves.py`| `test_taking_damage_while_unconscious` | Damage taken while unconscious increments `death_saves_failures` by 1. |
| `test_saving_throws.py`| `test_calculate_modifier` | Stat 14 yields +2 modifier. Low DC (2) always passes; high DC (30) always fails. |
| `test_status_effects.py`| `test_apply_and_tick_effect` | Status duration decrements each turn; removed when duration drops to 0. |
| `test_status_effects.py`| `test_remove_effect` | Explicit removal empties `status_efeitos` list. |
| `test_damage_types.py`| `test_damage_mechanics` | Resistance halves damage (20 $\to$ 10); Vulnerability doubles damage (15 $\to$ 30); Immunity zeroes damage (50 $\to$ 0). |
| `test_action_economy.py`| `test_move_and_attack` | Action flags: `movimento_realizado`, `acao_realizada`, `acao_bonus_realizada`. Cannot act twice. |
| `test_core_mechanics.py`| `test_cancellation` | Advantage + Disadvantage simultaneously cancels to standard single roll. |
| `test_cerco_rules.py`| `test_bloqueio_de_oficina` | Working workshop blocked if Orcs present in that workshop. |
| `test_cerco_rules.py`| `test_combate_corpo_a_corpo_mesmo_espaco` | Melee attack valid only in same zone as hero. |
| `test_cerco_rules.py`| `test_ataque_a_distancia_torres_adjacentes` | Tower can target adjacent walls and external fields, not internal zones. |
| `test_cerco_rules.py`| `test_bloqueio_de_escavacao` | Excavation blocked if enemies in Patio. |
| `teste_perks.py` | `test_lamina_incendiaria` | Attack with perk transforms defender's tile into `TERRENO_FOGO`. |
| `teste_perks.py` | `test_aura_vitalidade` | Cleric perk heals adjacent allies at turn start. |
| `teste_perks.py` | `test_sede_sangue` | Killing blow heals attacker with perk. |

---

## 6. GDScript 4 Migration Architecture

To achieve clean architecture, decoupling from visual nodes, and high performance in Godot 4, the combat and grid engine should be organized into pure `RefCounted` or `Node` scripts:

```
godot_project/
├── scripts/
│   ├── core/
│   │   ├── EventBus.gd                 # Global signals (autoload)
│   │   ├── DataManager.gd              # JSON loader (autoload)
│   │   └── GameManager.gd              # State machine (autoload)
│   ├── rules/
│   │   ├── Constants.gd                # Enums: DamageType, TerrainType, StatusType
│   │   ├── TacticalGrid.gd             # 20x20 Grid, AStar2D, line of sight, cover
│   │   ├── CombatRules.gd              # d20 rolls, advantage, crits, AC, damage math
│   │   ├── DeathSaves.gd               # Unconscious state machine, death save ticks
│   │   ├── StatusEffectManager.gd      # Duration tracking, per-turn effect application
│   │   ├── CercoCombatJudge.gd         # D6 roll, melee impacts, balestra, Brutamonte HP
│   │   └── CharacterStats.gd           # Attributes, modifiers, AC, proficiency
│   └── tests/ (GUT)
│       ├── test_grid_astar.gd
│       ├── test_combat_d20.gd
│       ├── test_cover_los.gd
│       ├── test_status_conditions.gd
│       ├── test_death_saves.gd
│       └── test_cerco_judge.gd
```

### 6.1 Sample Statically Typed GDScript API Signatures

```gdscript
# CombatRules.gd
class_name CombatRules
extends RefCounted

static func calculate_modifier(stat_value: int) -> int:
    return int(floor((stat_value - 10) / 2.0))

static func calculate_proficiency(level: int) -> int:
    return 1 + int(ceil(level / 4.0))

static func roll_d20(advantage: bool = false, disadvantage: bool = false) -> int:
    var r1: int = randi_range(1, 20)
    var r2: int = randi_range(1, 20)
    if advantage and disadvantage:
        return r1
    elif advantage:
        return maxi(r1, r2)
    elif disadvantage:
        return mini(r1, r2)
    return r1

static func calculate_attack(
    attacker_prof: int,
    attacker_bonus: int,
    target_ac: int,
    advantage: bool,
    disadvantage: bool
) -> Dictionary:
    var roll: int = roll_d20(advantage, disadvantage)
    var total: int = roll + attacker_prof + attacker_bonus
    var is_crit: bool = (roll == 20)
    var is_hit: bool = is_crit or (total >= target_ac)
    return {
        "roll": roll,
        "total": total,
        "is_hit": is_hit,
        "is_crit": is_crit
    }
```

```gdscript
# TacticalGrid.gd
class_name TacticalGrid
extends RefCounted

const WIDTH: int = 20
const HEIGHT: int = 20

var terrain_grid: Array[Array]
var elevation_grid: Array[Array]
var structure_hp: Array[Array]
var astar: AStar2D

func _init() -> void:
    astar = AStar2D.new()
    _setup_grid()
    _build_astar()

func get_point_id(pos: Vector2i) -> int:
    return pos.y * WIDTH + pos.x

func get_point_pos(id: int) -> Vector2i:
    return Vector2i(id % WIDTH, id / WIDTH)

func chebyshev_distance(p1: Vector2i, p2: Vector2i) -> int:
    return maxi(absi(p1.x - p2.x), absi(p1.y - p2.y))

func calculate_raycast_cover(from: Vector2i, to: Vector2i) -> int:
    var line: Array[Vector2i] = bresenham_line(from, to)
    var soft_cover: bool = false
    for pt in line:
        if terrain_grid[pt.y][pt.x] == "PAREDE":
            return 1000 # Total cover
        if is_occupied_by_creature(pt) and pt != from and pt != to:
            soft_cover = true
    return 2 if soft_cover else 0
```

---

## 7. Migration Checklist & Parity Validation Criteria

1. **Grid & Geometry**:
   - [ ] 20x20 coordinate system matches `Vector2i(0, 0)` to `Vector2i(19, 19)`.
   - [ ] Chebyshev distance used for all range checks.
   - [ ] Bresenham line algorithm matches reference raycasts.
   - [ ] AStar2D accurately reflects 8-way diagonal costs and weight 2.0 for difficult terrain.
2. **Combat Math**:
   - [ ] Attack roll d20 cancellation rule verified.
   - [ ] Critical hit dice doubling verified (dice doubled, flat bonuses not doubled).
   - [ ] Automatic critical on paralyzed/unconscious targets within 1.5m verified.
   - [ ] Death saving throws state transitions (20 revive, 1 double fail, 10+ success, 3 fail dead, 3 succ stabilized) pass 100% in GUT.
3. **Cerco Engine**:
   - [ ] Custom D6 probabilities and face tables match `FACES_D6`.
   - [ ] Flanking grants +1 D6 in melee.
   - [ ] Tower elevation grants +1 D6 / -1 D6 in ranged attacks.
   - [ ] Brutamonte 3-circle HP and per-turn unspent damage reset validated.
