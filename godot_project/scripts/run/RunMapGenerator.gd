# res://scripts/run/RunMapGenerator.gd
class_name RunMapGenerator
extends RefCounted

## Gera o mapa ramificado de um Ato de forma determinística a partir de um RNG injetado.
## Regras:
##  - Andar 0: sempre Combate (aquecimento).
##  - Penúltimo andar: sempre Fogueira (preparação para o chefe).
##  - Último andar: um único nó de Chefe ligado a todos os caminhos.
##  - Elites só a partir de MIN_ELITE_FLOOR.
##  - Caminhos nunca se cruzam visualmente.

const DEFAULT_FLOORS: int = 12
const DEFAULT_COLUMNS: int = 4
const DEFAULT_PATHS: int = 3
const MIN_FLOORS: int = 3
const MIN_ELITE_FLOOR: int = 4

const TYPE_WEIGHTS: Dictionary = {
	RunNode.NodeType.COMBAT: 45,
	RunNode.NodeType.ELITE: 12,
	RunNode.NodeType.SIEGE: 10,
	RunNode.NodeType.EVENT: 15,
	RunNode.NodeType.CAMPFIRE: 10,
	RunNode.NodeType.FORGE: 8,
}

var floor_count: int
var column_count: int
var path_count: int

func _init(p_floors: int = DEFAULT_FLOORS, p_columns: int = DEFAULT_COLUMNS, p_paths: int = DEFAULT_PATHS) -> void:
	if p_floors < MIN_FLOORS:
		push_warning("[RunMapGenerator] floors < %d; usando %d" % [MIN_FLOORS, MIN_FLOORS])
	floor_count = maxi(p_floors, MIN_FLOORS)
	column_count = maxi(p_columns, 1)
	path_count = maxi(p_paths, 1)

## Retorna null se rng for nulo ou act < 1.
func generate(act: int, rng: RandomNumberGenerator) -> RunMap:
	if rng == null:
		push_error("[RunMapGenerator] RNG nulo")
		return null
	if act < 1:
		push_error("[RunMapGenerator] Ato inválido: %d" % act)
		return null

	var map: RunMap = RunMap.new(act, floor_count)
	var grid: Dictionary = {} # Vector2i(floor, col) -> RunNode
	var last_nodes: Array[RunNode] = []
	var last_floor: int = floor_count - 2

	for p in path_count:
		# Espalha pontos de partida; o primeiro caminho é aleatório.
		var col: int = rng.randi_range(0, column_count - 1)
		if p > 0 and path_count <= column_count:
			col = _pick_unused_start_col(grid, rng, col)
		var prev: RunNode = null
		for f in range(last_floor + 1):
			var node: RunNode = _get_or_create(grid, map, act, f, col, rng)
			if prev != null:
				prev.connect_to(node.id)
			prev = node
			if f < last_floor:
				col = _choose_next_col(grid, map, f, col, rng)
		if not last_nodes.has(prev):
			last_nodes.append(prev)

	var boss: RunNode = RunNode.new(map.size(), act, floor_count - 1, column_count / 2, RunNode.NodeType.BOSS)
	map.add_node(boss)
	for n in last_nodes:
		n.connect_to(boss.id)
	return map

## Escolhe o tipo de um nó segundo as regras do andar.
func roll_type(floor_idx: int, rng: RandomNumberGenerator) -> int:
	if floor_idx == 0:
		return RunNode.NodeType.COMBAT
	if floor_idx == floor_count - 2:
		return RunNode.NodeType.CAMPFIRE
	if floor_idx >= floor_count - 1:
		return RunNode.NodeType.BOSS
	var allowed: Dictionary = TYPE_WEIGHTS.duplicate()
	if floor_idx < MIN_ELITE_FLOOR:
		allowed.erase(RunNode.NodeType.ELITE)
	# Evita fogueira logo antes da fogueira obrigatória.
	if floor_idx == floor_count - 3:
		allowed.erase(RunNode.NodeType.CAMPFIRE)
	var total: int = 0
	for w in allowed.values():
		total += int(w)
	var roll: int = rng.randi_range(1, total)
	for t in allowed.keys():
		roll -= int(allowed[t])
		if roll <= 0:
			return int(t)
	return RunNode.NodeType.COMBAT

func _get_or_create(grid: Dictionary, map: RunMap, act: int, f: int, col: int, rng: RandomNumberGenerator) -> RunNode:
	var key: Vector2i = Vector2i(f, col)
	if grid.has(key):
		return grid[key]
	var node: RunNode = RunNode.new(map.size(), act, f, col, roll_type(f, rng))
	map.add_node(node)
	grid[key] = node
	return node

func _pick_unused_start_col(grid: Dictionary, rng: RandomNumberGenerator, fallback: int) -> int:
	var free: Array[int] = []
	for c in column_count:
		if not grid.has(Vector2i(0, c)):
			free.append(c)
	if free.is_empty():
		return fallback
	return free[rng.randi_range(0, free.size() - 1)]

func _choose_next_col(grid: Dictionary, map: RunMap, f: int, col: int, rng: RandomNumberGenerator) -> int:
	var deltas: Array[int] = [-1, 0, 1]
	# Fisher-Yates determinístico com o RNG injetado
	for i in range(deltas.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp: int = deltas[i]
		deltas[i] = deltas[j]
		deltas[j] = tmp
	for d in deltas:
		var target: int = col + d
		if target < 0 or target >= column_count:
			continue
		if not _creates_crossing(grid, map, f, col, target):
			return target
	return col

## Uma aresta (f,a)->(f+1,b) cruza (f,c)->(f+1,d) se (a<c e b>d) ou (a>c e b<d).
func _creates_crossing(grid: Dictionary, map: RunMap, f: int, from_col: int, to_col: int) -> bool:
	for c in column_count:
		if c == from_col:
			continue
		var other: RunNode = grid.get(Vector2i(f, c), null)
		if other == null:
			continue
		for nid in other.next_ids:
			var dest: RunNode = map.get_node_by_id(nid)
			if dest == null:
				continue
			var d: int = dest.column
			if (from_col < c and to_col > d) or (from_col > c and to_col < d):
				return true
	return false
