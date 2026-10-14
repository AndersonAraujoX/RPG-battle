# Tactical Grid Explorer Report (Milestone 2)

## 1. Observation

### 1.1 Files Examined
The reference implementation for tactical grid, terrain, pathfinding, Line of Sight, and cover in RPG-battle was inspected across the following files:
- `src/tabuleiro.py` (lines 1–321): Board representation, cell grids, adjacent cover bonuses, destructible structure HP, BFS pathfinding, border walls, line of sight, and terrain elemental transformations.
- `src/utils.py` (lines 99–101, 152–219): Distance calculation (`calcular_distancia`, Chebyshev metric `max(|dx|, |dy|)`), Bresenham raycasting (`bresenham_line`), and raycast cover calculation (`calcular_cobertura`).
- `src/motor_combate.py` (lines 20–35, 78–95, 140–152, 353–460, 815–864): Board instantiation, A* 8-way pathfinding (`_astar_pathfinding`), movement cost evaluation, opportunity attack triggers, ice slipping hazard, fire terrain tick damage, and visibility/fog of war.
- `src/personagens/personagem_base.py` (lines 472–482, 620–645): Attack range checks, line of sight validation, elevation advantage, and AC augmentation via raycast cover (`bonus_cobertura`).
- `src/config.py` (lines 72–79, 158–183): Grid dimensions (`TAMANHO_CELULA = 30`, 20x20 cells = 600x600 px), terrain enum constants (`TERRENO_NORMAL`, `TERRENO_FLORESTA`, `TERRENO_DIFICIL`, `TERRENO_PAREDE`, `TERRENO_GELO`, `TERRENO_FOGO`, `TERRENO_AGUA`, `TERRENO_ROCHA`, `TERRENO_BARRIL`).
- `tests/test_tabuleiro.py` (lines 1–53): Unit tests for unit placement, grid boundaries, and unit relocation.
- `tests/test_cover.py` (lines 1–55): Unit tests for +3 AC (forest), +5 AC (rock), and structure destruction transforming to `TERRENO_DIFICIL`.
- `dados/fases/fase_02/mapa.json` (and `mapa_torre.json`): 20x20 2D string arrays representing stage terrain maps.
- `godot_project/project.godot` & `godot_project/run_gut_tests.sh`: Godot 4 project configuration and GUT test runner infra.

---

### 1.2 Grid Dimensions & Coordinate System
Direct observation from `src/tabuleiro.py` and `src/config.py`:
- **Default Dimensions**: Width = 20, Height = 20 (`largura=20, altura=20`). Total cells = 400.
- **Coordinate Space**: 0-indexed integer coordinates `(x, y)`:
  - $x \in [0, \text{largura} - 1] \implies [0, 19]$ (columns, horizontal axis).
  - $y \in [0, \text{altura} - 1] \implies [0, 19]$ (rows, vertical axis).
  - Origin `(0, 0)` is Top-Left; `(19, 19)` is Bottom-Right.
- **Pixel Scale (Pygame reference)**: `TAMANHO_CELULA = 30` px, rendering the 20x20 board into a $600 \times 600$ viewport area (`RECT_TABULEIRO = (0, 0, 600, 600)`).
- **Internal Data Grids in Tabuleiro**:
  - `self.grid`: 2D array of character references `[y][x]`, stores `Personagem` or `None`.
  - `self.terrain_grid`: 2D array of string terrain constants `[y][x]`.
  - `self.elevation_grid`: 2D array of integer elevation levels `[y][x]` (0, 1, or 2).
  - `self.estrutura_hp_grid`: 2D array of structure hit points `[y][x]` (initialized to 20 for destructible props).
  - `self.itens_no_chao`: 2D array of ground items `[y][x]`.

---

### 1.3 Cell Types, Terrain Costs & Obstacles
Exact constants from `src/config.py`:
```python
TERRENO_NORMAL = "NORMAL"
TERRENO_FLORESTA = "FLORESTA"
TERRENO_DIFICIL = "DIFICIL"
TERRENO_PAREDE = "PAREDE"
TERRENO_GELO = "GELO"
TERRENO_FOGO = "FOGO"
TERRENO_AGUA = "AGUA"
TERRENO_ROCHA = "ROCHA"
TERRENO_BARRIL = "BARRIL"
```
Auxiliary terrain types in `dados/`: `TERRENO_CAMPO`, `TERRENO_EXTERIOR`, `TERRENO_CORREDOR`, `TERRENO_MURALHA_LO`, `TERRENO_SUBSOLO`.

Detailed properties extracted from `src/tabuleiro.py` and `src/motor_combate.py`:

| Terrain Type | Walkable | Movement Cost | Cover Bonus | Destructible | Elemental Reaction / Hazard |
|---|---|---|---|---|---|
| `NORMAL` | Yes | 1.0 | None (0) | No | Default base terrain. |
| `FLORESTA` | Yes | 1.0 (or 2.0 if treated as rough) | +3 AC (Adjacent) | Yes (20 HP) | Catches fire with Fire damage $\to$ `TERRENO_FOGO`. When HP $\le 0 \to$ `TERRENO_DIFICIL`. |
| `DIFICIL` | Yes | 2.0 | None (0) | No | Rubble/debris. Doubles movement cost. |
| `PAREDE` | **No** | $\infty$ (Blocked) | +5 AC (Adjacent) / Total (1000) | No | Permanent barrier. Completely blocks movement and Line of Sight. |
| `GELO` | Yes | 1.0 | None (0) | No | Hazard: 50% chance to slip to free neighbor. Melts with Fire $\to$ `TERRENO_AGUA`. |
| `FOGO` | Yes | 1.0 | None (0) | No | Hazard: Units tick 1d6 fire damage at turn start. Extinguished by Ice $\to$ `TERRENO_NORMAL`. |
| `AGUA` | Yes | 1.0 | None (0) | No | Freezes with Ice damage $\to$ `TERRENO_GELO`. |
| `ROCHA` | **No** (Obstacle) | $\infty$ (Blocked) | +5 AC (Adjacent) | Yes (20 HP) | Heavy cover obstacle. When HP $\le 0 \to$ `TERRENO_DIFICIL`. |
| `BARRIL` | **No** (Obstacle) | $\infty$ (Blocked) | +3 AC (Adjacent) | Yes (20 HP) | Light cover prop. When HP $\le 0 \to$ `TERRENO_DIFICIL`. |

#### Border Limiters (`adicionar_limitadores`)
`src/tabuleiro.py:105-118`:
```python
for x in range(self.largura):
    self.terrain_grid[0][x] = TERRENO_PAREDE
    self.terrain_grid[self.altura - 1][x] = TERRENO_PAREDE
for y in range(self.altura):
    self.terrain_grid[y][0] = TERRENO_PAREDE
    self.terrain_grid[y][self.largura - 1] = TERRENO_PAREDE
```
Sets coordinates $x \in \{0, 19\}$ and $y \in \{0, 19\}$ to `TERRENO_PAREDE`, clearing any units occupying those edge tiles.

#### Destructible Structures (`aplicar_dano_estrutura`)
`src/tabuleiro.py:31-39`:
- Any cell initialized as `TERRENO_FLORESTA`, `TERRENO_ROCHA`, or `TERRENO_BARRIL` starts with 20 HP in `self.estrutura_hp_grid`.
- When damaged via `aplicar_dano_estrutura(x, y, dano)`:
  - If remaining $\text{HP} \le 0$: `self.terrain_grid[y][x] = TERRENO_DIFICIL` and returns `True`.
  - Debris remains walkable at cost 2.0.

---

### 1.4 Pathfinding Mechanics: BFS vs A*
The Python codebase contains two pathfinding implementations:
1. `Tabuleiro.encontrar_caminho` (`src/tabuleiro.py:41-78`):
   - Uses Breadth-First Search (BFS) with 4-way orthogonal directions: `((0, -1), (0, 1), (-1, 0), (1, 0))`.
   - Used primarily by the Cerco mode and Server session.
   - Ignores diagonal steps; skips `TERRENO_PAREDE` and cells occupied by other characters.
2. `MotorCombate._astar_pathfinding` (`src/motor_combate.py:353-385`):
   - Uses A* algorithm with a priority queue (`heapq`).
   - Supports 8-way movement: `[(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]`.
   - Dynamic movement cost:
     `move_cost = 2 if self.tabuleiro.terrain_grid[neighbor_pos[1]][neighbor_pos[0]] == TERRENO_DIFICIL else 1`
   - Stops expanding if accumulated `tentative_g_cost > max_cost`.
   - Heuristic used: Manhattan distance (`h_cost = abs(dx) + abs(dy)`).
   - Skips `TERRENO_PAREDE` and occupied cells (`personagem_no_alvo is not None and neighbor_pos != end_pos`).

---

### 1.5 Line of Sight & Cover Mechanics
Direct observation of raycasting and cover code:
1. **Line of Sight Algorithm (`calcular_linha_visao`, `src/tabuleiro.py:217-250`)**:
   - Uses standard 2D integer Bresenham algorithm:
     ```python
     dx = abs(x2 - x1); dy = abs(y2 - y1)
     sx = 1 if x1 < x2 else -1; sy = 1 if y1 < y2 else -1
     err = dx - dy
     ```
   - Checks every cell along the ray between `(x1, y1)` and `(x2, y2)`.
   - Returns `False` if an intermediate cell contains `TERRENO_PAREDE`.
   - If `ignorar_personagens == False`, returns `False` if an intermediate cell contains a unit.
   - *Observation of Reference Quirk*: In Python line 230, the starting cell was not skipped if `x1 != x2 or y1 != y2`, causing raycasts to evaluate the origin character unless `ignorar_personagens=True`. In GDScript, raycast point generation explicitly excludes the origin tile.
2. **Raycast Cover Calculation (`calcular_cobertura`, `src/utils.py:184-219`)**:
   - Raycasts via `bresenham_line(x0, y0, x1, y1)` (points excluding origin and destination).
   - If ray intersects `TERRENO_PAREDE`: returns `1000` (Total Cover / blocked LoS).
   - If ray intersects another creature (`char != atacante and char != alvo`): returns `2` (Half Cover / soft creature cover, granting +2 AC).
   - If no obstacle on ray: returns `0` (No Cover).
3. **Adjacent Tactical Cover (`obter_bonificacao_cobertura`, `src/tabuleiro.py:15-30`)**:
   - Checks all 8 neighboring cells $(x + dx, y + dy)$ for $dx, dy \in \{-1, 0, 1\} \setminus \{(0, 0)\}$.
   - If neighbor is `TERRENO_FLORESTA` or `TERRENO_BARRIL`: awards `+3` AC.
   - If neighbor is `TERRENO_ROCHA` or `TERRENO_PAREDE`: awards `+5` AC.
   - Returns the maximum bonus found across all 8 neighbors (`0`, `3`, or `5`).
4. **Integration in Attack Resolution (`src/personagens/personagem_base.py:620-640`)**:
   - High Ground Advantage: `if self.elevacao > alvo.elevacao and self.alcance > 1: vantagem = True`.
   - Cover Application: `ac_alvo = alvo.ac + bonus_cobertura`.
   - Classification:
     - `bonus_cobertura >= 1000`: Target has Total Cover (Line of sight blocked, unhittable).
     - `bonus_cobertura >= 5`: Target has +5 AC (Three-quarters Cover).
     - `bonus_cobertura >= 2`: Target has +2 AC (Half Cover).

---

## 2. Logic Chain

1. **Grid Architecture Mapping**:
   - The reference Python board is a 20x20 discrete grid with multi-layered state (`terrain_grid`, `elevation_grid`, `estrutura_hp_grid`, and `grid` for units).
   - In Godot 4, this maps cleanly to a dedicated class `TacticalGrid` maintaining 2D arrays (`Array[Array]`) or flat 1D packed arrays indexed by `y * width + x`.
   - Exposing typed `Vector2i` coordinates ensures compile-time safety and prevents coordinate inversion bugs (`(x, y)` vs `[y][x]`).

2. **AStar2D Native Integration & Movement Metrics**:
   - Godot 4 provides `AStar2D`, a native C++ A* graph pathfinder.
   - To support 8-way movement:
     - Each cell $(x, y)$ is assigned a unique point ID: `id = y * width + x`.
     - Connections are added to up to 8 valid neighbors: 4 orthogonal `((0, 1), (0, -1), (1, 0), (-1, 0))` and 4 diagonal `((1, 1), (1, -1), (-1, 1), (-1, -1))`.
   - **Diagonal Costs & Distance Models**:
     - *Euclidean (Default AStar2D)*: Orthogonal distance is 1.0; diagonal distance is $\sqrt{2} \approx 1.4142$. When combined with `weight_scale`, difficult terrain costs $2.0$ orthogonally and $2.828$ diagonally.
     - *Chebyshev (D&D 5e Standard)*: Both orthogonal and diagonal steps cost 1.0 movement unit ($1 \text{ square} = 5 \text{ ft}$).
     - By subclassing `AStar2D` or providing cost overrides (`_compute_cost` and `_estimate_cost`), `TacticalGrid` can support both Euclidean and Chebyshev rules configurable via an enum (`DistanceMetric.EUCLIDEAN` vs `DistanceMetric.CHEBYSHEV`).
   - **Corner Cutting Prevention (Strict Wall Corner Rule)**:
     - When moving diagonally from $(x, y)$ to $(x+1, y+1)$, if both $(x+1, y)$ and $(x, y+1)$ are walls or obstacles, the character cannot cut through the corner of two touching barriers.
     - `TacticalGrid` must validate diagonal connections: a diagonal link between $A$ and $B$ is only valid if at least one (or both in strict mode) shared orthogonal neighbors are walkable.

3. **Dynamic Unit Occupancy**:
   - Static obstacles (walls, undestroyed rocks) have their `AStar2D` points permanently disabled or disconnected.
   - Dynamic obstacles (combatants) occupy cells temporarily.
   - During `find_path(from_pos, to_pos, ignore_units)`:
     - Points containing other units (except `from_pos` and optionally `to_pos` if targeting an enemy) are disabled via `astar.set_point_disabled(id, true)`.
     - The path is calculated via `astar.get_point_path(start_id, end_id)`.
     - Disabled points are restored immediately afterward.

4. **Line of Sight & Cover Resolution**:
   - `TacticalGrid` implements an integer Bresenham raycaster returning an array of intermediate `Vector2i` points.
   - `has_line_of_sight(from_pos, to_pos, ignore_units)` returns `false` if any intermediate cell has `TERRENO_PAREDE` (or a unit when `ignore_units == false`).
   - Cover evaluation combines two complimentary systems:
     - `get_raycast_cover(attacker_pos, target_pos)` evaluates soft cover from intervening units (+2 AC) and hard obstruction from walls (1000 AC).
     - `get_adjacent_cover_bonus(pos)` evaluates bunker/cover bonuses (+3 for forest/barrel, +5 for rock/wall).
     - Combat rules apply the maximum applicable cover: `total_cover = max(raycast_cover, adjacent_cover)`.

---

## 3. Caveats

1. **Path Location Specification**:
   - The user mission prompt asks for `godot_project/scripts/tactical/TacticalGrid.gd`.
   - `PROJECT.md` line 171 lists `godot_project/scripts/core/TacticalGrid.gd`.
   - *Resolution*: Propose the canonical script at `godot_project/scripts/core/TacticalGrid.gd` with a forwarder/alias or symmetrical path in `scripts/tactical/TacticalGrid.gd` so any dependency resolves without error.
2. **Chebyshev vs Euclidean Diagonal Movement**:
   - In Python `motor_combate.py`, `calcular_distancia` is Chebyshev (`max(|dx|, |dy|)`), but A* used Manhattan heuristic (`abs(dx) + abs(dy)`), while Godot's `AStar2D` uses Euclidean by default.
   - *Resolution*: Implement a configurable distance mode in `TacticalGrid` defaulting to Chebyshev for D&D 5e rule consistency while preserving Euclidean capabilities.
3. **Destructible Structures vs Walkability**:
   - In Python, `TERRENO_FLORESTA` is walkable while having 20 HP, whereas `TERRENO_ROCHA` and `TERRENO_BARRIL` are obstacles (impassable). When destroyed, all three become `TERRENO_DIFICIL` (walkable, cost 2.0). The GDScript implementation must distinguish walkable destructibles from non-walkable destructibles.

---

## 4. Conclusion & Proposed Architecture

### 4.1 GDScript Class Design (`TacticalGrid.gd`)

```gdscript
# res://scripts/core/TacticalGrid.gd
# (Also aliased as res://scripts/tactical/TacticalGrid.gd)
class_name TacticalGrid
extends RefCounted

## Signals
signal terrain_changed(pos: Vector2i, old_type: String, new_type: String)
signal structure_damaged(pos: Vector2i, current_hp: int, max_hp: int)
signal structure_destroyed(pos: Vector2i, new_terrain: String)
signal unit_placed(unit: Variant, pos: Vector2i)
signal unit_removed(unit: Variant, pos: Vector2i)
signal unit_moved(unit: Variant, from_pos: Vector2i, to_pos: Vector2i)
signal hazard_triggered(pos: Vector2i, hazard_type: String, unit: Variant)

## Constants: Terrain Types
const TERRENO_NORMAL: String = "NORMAL"
const TERRENO_FLORESTA: String = "FLORESTA"
const TERRENO_DIFICIL: String = "DIFICIL"
const TERRENO_PAREDE: String = "PAREDE"
const TERRENO_GELO: String = "GELO"
const TERRENO_FOGO: String = "FOGO"
const TERRENO_AGUA: String = "AGUA"
const TERRENO_ROCHA: String = "ROCHA"
const TERRENO_BARRIL: String = "BARRIL"

## Constants: Cover Values
const COVER_NONE: int = 0
const COVER_HALF: int = 2          # Creature soft cover / low prop
const COVER_LIGHT_ADJACENT: int = 3 # Adjacent forest / barrel
const COVER_THREE_QUARTERS: int = 5 # Adjacent rock / wall
const COVER_TOTAL: int = 1000       # Wall on LoS / impassable barrier

## Constants: Movement Costs
const COST_NORMAL: float = 1.0
const COST_DIFFICULT: float = 2.0
const COST_IMPASSABLE: float = 9999.0

## Enums
enum DistanceMetric {
	CHEBYSHEV, # D&D 5e standard (diagonal = 1.0)
	EUCLIDEAN, # Real distance (diagonal = sqrt(2) ≈ 1.414)
	MANHATTAN  # 4-way grid distance (|dx| + |dy|)
}

## Grid Configuration
var width: int = 20
var height: int = 20
var metric: DistanceMetric = DistanceMetric.CHEBYSHEV
var allow_corner_cutting: bool = false

## Internal Grids
var _terrain_grid: Array[Array] = []
var _elevation_grid: Array[Array] = []
var _structure_hp_grid: Array[Array] = []
var _units_grid: Array[Array] = []

## Native Godot AStar2D Instance
var _astar: AStar2D = AStar2D.new()

## Initialization
func _init(p_width: int = 20, p_height: int = 20, p_metric: DistanceMetric = DistanceMetric.CHEBYSHEV) -> void:
	width = p_width
	height = p_height
	metric = p_metric
	_allocate_grids()
	rebuild_astar()

## Grid Allocation & Clearing
func _allocate_grids() -> void:
	_terrain_grid.clear()
	_elevation_grid.clear()
	_structure_hp_grid.clear()
	_units_grid.clear()
	for y in range(height):
		var row_terrain: Array[String] = []
		var row_elev: Array[int] = []
		var row_hp: Array[int] = []
		var row_units: Array[Variant] = []
		for x in range(width):
			row_terrain.append(TERRENO_NORMAL)
			row_elev.append(0)
			row_hp.append(0)
			row_units.append(null)
		_terrain_grid.append(row_terrain)
		_elevation_grid.append(row_elev)
		_structure_hp_grid.append(row_hp)
		_units_grid.append(row_units)

## Coordinate & Bounds Methods
func is_valid_cell(pos: Vector2i) -> bool:
	return pos.x >= 0 and pos.x < width and pos.y >= 0 and pos.y < height

func point_to_id(pos: Vector2i) -> int:
	return pos.y * width + pos.x

func id_to_point(id: int) -> Vector2i:
	return Vector2i(id % width, id / width)

## Terrain & Walkability
func get_cell_type(pos: Vector2i) -> String:
	if not is_valid_cell(pos): return TERRENO_PAREDE
	return _terrain_grid[pos.y][pos.x]

func set_cell_type(pos: Vector2i, type: String) -> void:
	if not is_valid_cell(pos): return
	var old = _terrain_grid[pos.y][pos.x]
	_terrain_grid[pos.y][pos.x] = type
	if type in [TERRENO_FLORESTA, TERRENO_ROCHA, TERRENO_BARRIL]:
		_structure_hp_grid[pos.y][pos.x] = 20
	else:
		_structure_hp_grid[pos.y][pos.x] = 0
	_update_astar_cell(pos)
	terrain_changed.emit(pos, old, type)

func is_cell_walkable(pos: Vector2i) -> bool:
	if not is_valid_cell(pos): return false
	var t = _terrain_grid[pos.y][pos.x]
	return t != TERRENO_PAREDE and t != TERRENO_ROCHA and t != TERRENO_BARRIL

func get_terrain_cost(pos: Vector2i) -> float:
	if not is_valid_cell(pos): return COST_IMPASSABLE
	var t = _terrain_grid[pos.y][pos.x]
	if t == TERRENO_DIFICIL: return COST_DIFFICULT
	if not is_cell_walkable(pos): return COST_IMPASSABLE
	return COST_NORMAL

## Destructible Structures
func apply_structure_damage(pos: Vector2i, damage: int) -> bool:
	if not is_valid_cell(pos): return false
	if _structure_hp_grid[pos.y][pos.x] <= 0: return false
	_structure_hp_grid[pos.y][pos.x] = max(0, _structure_hp_grid[pos.y][pos.x] - damage)
	var current_hp = _structure_hp_grid[pos.y][pos.x]
	structure_damaged.emit(pos, current_hp, 20)
	if current_hp <= 0:
		set_cell_type(pos, TERRENO_DIFICIL)
		structure_destroyed.emit(pos, TERRENO_DIFICIL)
		return true
	return false

## Border Limiters
func add_border_walls() -> void:
	for x in range(width):
		set_cell_type(Vector2i(x, 0), TERRENO_PAREDE)
		set_cell_type(Vector2i(x, height - 1), TERRENO_PAREDE)
		_units_grid[0][x] = null
		_units_grid[height - 1][x] = null
	for y in range(height):
		set_cell_type(Vector2i(0, y), TERRENO_PAREDE)
		set_cell_type(Vector2i(width - 1, y), TERRENO_PAREDE)
		_units_grid[y][0] = null
		_units_grid[y][width - 1] = null
	rebuild_astar()

## Elemental Terrain Reactions
func apply_terrain_damage(pos: Vector2i, damage_type: String) -> void:
	if not is_valid_cell(pos): return
	var cur = _terrain_grid[pos.y][pos.x]
	var dmg = damage_type.to_lower()
	if dmg == "fogo" or dmg == "fire":
		if cur == TERRENO_FLORESTA: set_cell_type(pos, TERRENO_FOGO)
		elif cur == TERRENO_GELO: set_cell_type(pos, TERRENO_AGUA)
	elif dmg == "gelo" or dmg == "ice":
		if cur == TERRENO_AGUA: set_cell_type(pos, TERRENO_GELO)
		elif cur == TERRENO_FOGO: set_cell_type(pos, TERRENO_NORMAL)

## Unit Occupancy Management
func place_unit(unit: Variant, pos: Vector2i) -> bool:
	if not is_valid_cell(pos) or not is_cell_walkable(pos): return false
	if _units_grid[pos.y][pos.x] != null: return false
	_units_grid[pos.y][pos.x] = unit
	unit_placed.emit(unit, pos)
	return true

func remove_unit(pos: Vector2i) -> Variant:
	if not is_valid_cell(pos): return null
	var u = _units_grid[pos.y][pos.x]
	_units_grid[pos.y][pos.x] = null
	if u != null: unit_removed.emit(u, pos)
	return u

func move_unit(from_pos: Vector2i, to_pos: Vector2i) -> bool:
	if not is_valid_cell(from_pos) or not is_valid_cell(to_pos): return false
	var u = _units_grid[from_pos.y][from_pos.x]
	if u == null: return false
	if not is_cell_walkable(to_pos) or (_units_grid[to_pos.y][to_pos.x] != null and _units_grid[to_pos.y][to_pos.x] != u):
		return false
	_units_grid[from_pos.y][from_pos.x] = null
	_units_grid[to_pos.y][to_pos.x] = u
	unit_moved.emit(u, from_pos, to_pos)
	return true

func get_unit_at(pos: Vector2i) -> Variant:
	if not is_valid_cell(pos): return null
	return _units_grid[pos.y][pos.x]

## AStar2D Graph Construction
func rebuild_astar() -> void:
	_astar.clear()
	for y in range(height):
		for x in range(width):
			var pos = Vector2i(x, y)
			var id = point_to_id(pos)
			_astar.add_point(id, Vector2(x, y), get_terrain_cost(pos))
			if not is_cell_walkable(pos):
				_astar.set_point_disabled(id, true)
	
	# Connect 8-way neighbors
	for y in range(height):
		for x in range(width):
			var pos = Vector2i(x, y)
			var id = point_to_id(pos)
			if not is_cell_walkable(pos): continue
			_connect_neighbors(pos)

func _connect_neighbors(pos: Vector2i) -> void:
	var id = point_to_id(pos)
	var dirs = [
		Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0),
		Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)
	]
	for d in dirs:
		var n_pos = pos + d
		if not is_valid_cell(n_pos) or not is_cell_walkable(n_pos): continue
		# Diagonal corner cutting check
		if abs(d.x) == 1 and abs(d.y) == 1 and not allow_corner_cutting:
			var ortho1 = Vector2i(pos.x + d.x, pos.y)
			var ortho2 = Vector2i(pos.x, pos.y + d.y)
			if not is_cell_walkable(ortho1) and not is_cell_walkable(ortho2):
				continue # Block cutting through two solid diagonal corners
		var n_id = point_to_id(n_pos)
		if not _astar.are_points_connected(id, n_id):
			_astar.connect_points(id, n_id, true)

func _update_astar_cell(pos: Vector2i) -> void:
	var id = point_to_id(pos)
	_astar.set_point_weight_scale(id, get_terrain_cost(pos))
	_astar.set_point_disabled(id, not is_cell_walkable(pos))

## Pathfinding Execution
func find_path(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false, max_movement: float = -1.0) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if from_pos == to_pos or not is_valid_cell(from_pos) or not is_valid_cell(to_pos):
		return result
	if not is_cell_walkable(to_pos):
		return result
	
	var disabled_ids: Array[int] = []
	if not ignore_units:
		for y in range(height):
			for x in range(width):
				var p = Vector2i(x, y)
				if p == from_pos or p == to_pos: continue
				if _units_grid[y][x] != null:
					var uid = point_to_id(p)
					if not _astar.is_point_disabled(uid):
						_astar.set_point_disabled(uid, true)
						disabled_ids.append(uid)
	
	var from_id = point_to_id(from_pos)
	var to_id = point_to_id(to_pos)
	var raw_path = _astar.get_point_path(from_id, to_id)
	
	# Restore disabled units
	for uid in disabled_ids:
		_astar.set_point_disabled(uid, false)
	
	if raw_path.size() <= 1:
		return result
	
	# Skip the starting cell (standard path definition: steps to take)
	var accumulated_cost: float = 0.0
	for i in range(1, raw_path.size()):
		var step = Vector2i(round(raw_path[i].x), round(raw_path[i].y))
		var step_cost = get_terrain_cost(step)
		if max_movement > 0.0 and (accumulated_cost + step_cost) > max_movement:
			break
		accumulated_cost += step_cost
		result.append(step)
		
	return result

## Line of Sight & Bresenham Raycasting
func get_bresenham_line(from_pos: Vector2i, to_pos: Vector2i) -> Array[Vector2i]:
	var points: Array[Vector2i] = []
	var x0 = from_pos.x
	var y0 = from_pos.y
	var x1 = to_pos.x
	var y1 = to_pos.y
	var dx = abs(x1 - x0)
	var dy = abs(y1 - y0)
	var sx = 1 if x0 < x1 else -1
	var sy = 1 if y0 < y1 else -1
	var err = dx - dy
	var cx = x0
	var cy = y0
	
	while true:
		if not (cx == x0 and cy == y0):
			points.append(Vector2i(cx, cy))
		if cx == x1 and cy == y1:
			break
		var e2 = 2 * err
		if e2 > -dy:
			err -= dy
			cx += sx
		if e2 < dx:
			err += dx
			cy += sy
	return points

func has_line_of_sight(from_pos: Vector2i, to_pos: Vector2i, ignore_units: bool = false) -> bool:
	if from_pos == to_pos: return true
	var line = get_bresenham_line(from_pos, to_pos)
	for i in range(line.size()):
		var pt = line[i]
		# Walls block LoS entirely
		if _terrain_grid[pt.y][pt.x] == TERRENO_PAREDE or _terrain_grid[pt.y][pt.x] == TERRENO_ROCHA:
			return false
		# Units block LoS on intermediate cells unless ignored
		if not ignore_units and i < (line.size() - 1):
			if _units_grid[pt.y][pt.x] != null:
				return false
	return true

## Cover Calculation
func get_raycast_cover(attacker_pos: Vector2i, target_pos: Vector2i) -> int:
	if attacker_pos == target_pos: return COVER_NONE
	var line = get_bresenham_line(attacker_pos, target_pos)
	var has_creature_soft_cover = false
	
	for i in range(line.size()):
		var pt = line[i]
		if _terrain_grid[pt.y][pt.x] == TERRENO_PAREDE:
			return COVER_TOTAL
		if i < (line.size() - 1): # Exclude target cell itself
			if _units_grid[pt.y][pt.x] != null:
				has_creature_soft_cover = true
	
	if has_creature_soft_cover:
		return COVER_HALF
	return COVER_NONE

func get_adjacent_cover_bonus(pos: Vector2i) -> int:
	if not is_valid_cell(pos): return COVER_NONE
	var max_bonus = 0
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			if dx == 0 and dy == 0: continue
			var n = pos + Vector2i(dx, dy)
			if is_valid_cell(n):
				var t = _terrain_grid[n.y][n.x]
				if t == TERRENO_FLORESTA or t == TERRENO_BARRIL:
					max_bonus = max(max_bonus, COVER_LIGHT_ADJACENT)
				elif t == TERRENO_ROCHA or t == TERRENO_PAREDE:
					max_bonus = max(max_bonus, COVER_THREE_QUARTERS)
	return max_bonus

## Distance Helpers
func calculate_chebyshev_distance(p1: Vector2i, p2: Vector2i) -> int:
	return max(abs(p1.x - p2.x), abs(p1.y - p2.y))

func calculate_manhattan_distance(p1: Vector2i, p2: Vector2i) -> int:
	return abs(p1.x - p2.x) + abs(p1.y - p2.y)

func calculate_euclidean_distance(p1: Vector2i, p2: Vector2i) -> float:
	return Vector2(p1).distance_to(Vector2(p2))
```

---

### 4.2 GUT Test Plan (`test_tactical_grid.gd`)

Test script to be created at `godot_project/test/unit/test_tactical_grid.gd`:

#### Test Suite Architecture
- Extends `GutTest`.
- Strict **Arrange-Act-Assert (AAA)** structure for every test method.
- 100% autonomous, headless executable via `./run_gut_tests.sh`.

#### Method Coverage Breakdown (30 Test Cases)

1. **Grid Bounds & Initial State**:
   - `test_grid_dimensions_default_20x20()`: Verify default width=20, height=20, all cells initialized to `NORMAL`.
   - `test_is_valid_cell_boundaries()`: Assert valid for `(0, 0)`, `(19, 19)`, `(10, 10)`; invalid for `(-1, 0)`, `(20, 10)`, `(0, 25)`.
   - `test_point_to_id_and_reverse_mapping()`: Roundtrip bijective consistency: `id_to_point(point_to_id(pos)) == pos`.

2. **Border Limiters & Walls**:
   - `test_add_border_walls_applies_perimeter_walls()`: Call `add_border_walls()`, assert `(0, y)`, `(19, y)`, `(x, 0)`, `(x, 19)` are `PAREDE`, center `(10, 10)` remains `NORMAL`.
   - `test_border_walls_clear_occupants()`: Place unit at `(0, 5)`, run `add_border_walls()`, assert unit was evacuated/removed.

3. **Walkability & Movement Costs**:
   - `test_terrain_walkability_flags()`: Assert `NORMAL`, `DIFICIL`, `FLORESTA`, `GELO` are walkable; `PAREDE`, `ROCHA` are not.
   - `test_terrain_cost_values()`: Assert cost of `NORMAL` is 1.0, `DIFICIL` is 2.0, `PAREDE` is $\infty$.

4. **Destructible Structures**:
   - `test_structure_hp_initialized_to_20()`: Setting `FLORESTA`, `ROCHA`, `BARRIL` gives 20 HP; `NORMAL` gives 0 HP.
   - `test_apply_structure_damage_partial()`: Apply 10 damage to rock; assert HP becomes 10 and terrain remains `ROCHA`.
   - `test_apply_structure_damage_destruction_transforms_to_dificil()`: Apply 25 damage to rock; assert returns `true`, HP is 0, terrain becomes `DIFICIL`.
   - `test_structure_damage_emits_signals()`: Verify `structure_damaged` and `structure_destroyed` signals fire with expected payloads.

5. **Elemental Interactions**:
   - `test_elemental_fire_ignites_forest_to_fire()`: Fire on `FLORESTA` converts to `FOGO`.
   - `test_elemental_ice_freezes_water_to_ice()`: Ice on `AGUA` converts to `GELO`.
   - `test_elemental_fire_melts_ice_to_water()`: Fire on `GELO` converts to `AGUA`.
   - `test_elemental_ice_extinguishes_fire_to_normal()`: Ice on `FOGO` converts to `NORMAL`.

6. **Unit Occupancy**:
   - `test_place_unit_on_free_walkable_cell()`: Returns `true`, unit placed in grid.
   - `test_place_unit_on_wall_fails()`: Placing on `PAREDE` returns `false`.
   - `test_place_unit_on_occupied_cell_fails()`: Placing on another unit returns `false`.
   - `test_move_unit_updates_grid()`: Move unit from `(2, 2)` to `(3, 2)`; assert `(2, 2)` is null, `(3, 2)` has unit.

7. **AStar2D Pathfinding**:
   - `test_find_path_straight_line()`: Find path from `(1, 1)` to `(1, 4)`; assert 3 steps returned: `[(1, 2), (1, 3), (1, 4)]`.
   - `test_find_path_diagonal_8_way()`: Find path from `(1, 1)` to `(3, 3)`; assert direct diagonal steps utilized.
   - `test_find_path_obstacle_detour()`: Place wall obstacle at `(2, 2)`; assert path routes around it.
   - `test_find_path_unit_detour()`: Place blocking unit at `(2, 2)`; assert path routes around when `ignore_units=false`.
   - `test_find_path_unreachable_returns_empty()`: Completely surround target with walls; assert path returns empty array `[]`.
   - `test_find_path_max_movement_truncation()`: Set `max_movement = 2.0`; path through difficult terrain (cost 2.0) only allows 1 cell.
   - `test_diagonal_corner_cutting_prevention()`: With walls at `(1, 2)` and `(2, 1)`, diagonal step from `(1, 1)` to `(2, 2)` is blocked when `allow_corner_cutting=false`.

8. **Line of Sight (LoS)**:
   - `test_has_line_of_sight_clear_orthogonal()`: LoS is `true` between `(2, 2)` and `(2, 6)`.
   - `test_has_line_of_sight_clear_diagonal()`: LoS is `true` between `(2, 2)` and `(6, 6)`.
   - `test_has_line_of_sight_blocked_by_wall()`: Wall at `(2, 4)` makes LoS `false`.
   - `test_has_line_of_sight_blocked_by_unit_when_not_ignored()`: Intermediate unit blocks LoS when `ignore_units=false`, but passes when `ignore_units=true`.

9. **Cover Calculation**:
   - `test_get_adjacent_cover_bonus_forest_concedes_3_ac()`: Cell adjacent to `FLORESTA` receives +3 AC.
   - `test_get_adjacent_cover_bonus_rock_concedes_5_ac()`: Cell adjacent to `ROCHA` receives +5 AC.
   - `test_get_adjacent_cover_bonus_open_field_is_zero()`: Center cell in open field receives 0 AC.
   - `test_raycast_cover_intervening_creature_concedes_half_cover_2_ac()`: Unit in LoS confers +2 AC soft cover.
   - `test_raycast_cover_intervening_wall_concedes_total_cover_1000()`: Wall in LoS confers 1000 AC total cover.

10. **Adversarial & Edge Cases**:
    - `test_pathfinding_start_equals_end()`: Path returns empty array `[]`.
    - `test_los_start_equals_end()`: Returns `true`.
    - `test_out_of_bounds_queries_safe()`: Negative or oversized coordinates gracefully return false / null without crash.
    - `test_structure_overkill_damage_clamps_at_zero()`: Dealing 9999 damage cleanly sets HP to 0 and converts to `DIFICIL`.

---

## 5. Verification Method

To independently verify the observations, references, and proposed architecture:

1. **Verify Python Reference Code**:
   ```bash
   # Run existing Python unit tests for board and cover
   pytest tests/test_tabuleiro.py tests/test_cover.py -v
   ```
   *Expected Output*: 3 passed in `test_tabuleiro.py`, 3 passed in `test_cover.py` with 100% success.

2. **Verify File Layout & Source References**:
   - Confirm `src/tabuleiro.py:15-39` defines `obter_bonificacao_cobertura` (+3 and +5 AC) and `aplicar_dano_estrutura` (20 HP -> `TERRENO_DIFICIL`).
   - Confirm `src/utils.py:184-219` defines `calcular_cobertura` (Half Cover +2, Total Cover 1000).
   - Confirm `src/motor_combate.py:353-385` defines 8-way A* pathfinding.

3. **Verify Godot Project Health & GUT Execution**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./run_gut_tests.sh
   ```
   *Expected Output*: Godot 4 headless runner launches GUT and reports existing unit tests passing with exit code 0.

4. **Invalidation Conditions**:
   - If D&D 5e cover bonus is strictly enforced without adjacent terrain bonuses (+3/+5), `obter_bonificacao_cobertura` would be replaced entirely by `calcular_cobertura`. (However, both are active in the reference game).
   - If diagonal movement cost is mandated as Euclidean rather than Chebyshev, `metric` must default to `DistanceMetric.EUCLIDEAN`.
