# res://scripts/run/RunMap.gd
class_name RunMap
extends RefCounted

## Grafo dirigido (andar a andar) de um Ato da run.

var act: int = 1
var floor_count: int = 0
var nodes: Array[RunNode] = []
var _index: Dictionary = {}

func _init(p_act: int = 1, p_floor_count: int = 0) -> void:
	act = p_act
	floor_count = p_floor_count

func add_node(node: RunNode) -> bool:
	if node == null or _index.has(node.id):
		return false
	nodes.append(node)
	_index[node.id] = node
	return true

func get_node_by_id(node_id: int) -> RunNode:
	return _index.get(node_id, null)

func size() -> int:
	return nodes.size()

func get_nodes_on_floor(floor_idx: int) -> Array[RunNode]:
	var result: Array[RunNode] = []
	for n in nodes:
		if n.floor_index == floor_idx:
			result.append(n)
	return result

func get_start_nodes() -> Array[RunNode]:
	return get_nodes_on_floor(0)

func get_boss_node() -> RunNode:
	for n in nodes:
		if n.is_boss():
			return n
	return null

func get_next_nodes(node_id: int) -> Array[RunNode]:
	var result: Array[RunNode] = []
	var node: RunNode = get_node_by_id(node_id)
	if node == null:
		return result
	for nid in node.next_ids:
		var nxt: RunNode = get_node_by_id(nid)
		if nxt != null:
			result.append(nxt)
	return result

## Verdadeiro se existe aresta direta from -> to.
func has_edge(from_id: int, to_id: int) -> bool:
	var node: RunNode = get_node_by_id(from_id)
	return node != null and node.next_ids.has(to_id)

## BFS: verdadeiro se o chefe é alcançável a partir de node_id.
func can_reach_boss(node_id: int) -> bool:
	var boss: RunNode = get_boss_node()
	if boss == null or get_node_by_id(node_id) == null:
		return false
	var visited_ids: Dictionary = {}
	var queue: Array[int] = [node_id]
	while not queue.is_empty():
		var cur: int = queue.pop_front()
		if cur == boss.id:
			return true
		if visited_ids.has(cur):
			continue
		visited_ids[cur] = true
		queue.append_array(get_node_by_id(cur).next_ids)
	return false

func to_dict() -> Dictionary:
	var arr: Array = []
	for n in nodes:
		arr.append(n.to_dict())
	return {"act": act, "floor_count": floor_count, "nodes": arr}

static func from_dict(data: Dictionary) -> RunMap:
	if not data.has("nodes") or not (data["nodes"] is Array):
		return null
	var map: RunMap = RunMap.new(int(data.get("act", 1)), int(data.get("floor_count", 0)))
	for nd in data["nodes"]:
		if not (nd is Dictionary):
			return null
		var node: RunNode = RunNode.from_dict(nd)
		if node == null or not map.add_node(node):
			return null
	return map
