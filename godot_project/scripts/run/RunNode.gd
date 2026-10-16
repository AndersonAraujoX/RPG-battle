# res://scripts/run/RunNode.gd
class_name RunNode
extends RefCounted

## Um nó do mapa da run roguelike (estilo Slay the Spire).
## Dados puros, sem renderização — serializável via to_dict()/from_dict().

enum NodeType { COMBAT, ELITE, SIEGE, EVENT, CAMPFIRE, FORGE, BOSS }

const TYPE_NAMES: Dictionary = {
	NodeType.COMBAT: "Combate",
	NodeType.ELITE: "Elite",
	NodeType.SIEGE: "Cerco",
	NodeType.EVENT: "Evento",
	NodeType.CAMPFIRE: "Fogueira",
	NodeType.FORGE: "Forja",
	NodeType.BOSS: "Chefe",
}

const TYPE_SHORT: Dictionary = {
	NodeType.COMBAT: "C",
	NodeType.ELITE: "E",
	NodeType.SIEGE: "S",
	NodeType.EVENT: "?",
	NodeType.CAMPFIRE: "F",
	NodeType.FORGE: "$",
	NodeType.BOSS: "B",
}

var id: int = -1
var act: int = 1
var floor_index: int = 0
var column: int = 0
var type: int = NodeType.COMBAT
var next_ids: Array[int] = []
var visited: bool = false

func _init(p_id: int = -1, p_act: int = 1, p_floor: int = 0, p_column: int = 0, p_type: int = NodeType.COMBAT) -> void:
	id = p_id
	act = p_act
	floor_index = p_floor
	column = p_column
	type = p_type

## Liga este nó a outro (sem duplicatas, sem auto-ligação).
func connect_to(other_id: int) -> bool:
	if other_id < 0 or other_id == id or next_ids.has(other_id):
		return false
	next_ids.append(other_id)
	return true

func is_boss() -> bool:
	return type == NodeType.BOSS

func is_combat_type() -> bool:
	return type in [NodeType.COMBAT, NodeType.ELITE, NodeType.SIEGE, NodeType.BOSS]

func get_type_name() -> String:
	return TYPE_NAMES.get(type, "Desconhecido")

func get_short_label() -> String:
	return TYPE_SHORT.get(type, "?")

func to_dict() -> Dictionary:
	return {
		"id": id,
		"act": act,
		"floor": floor_index,
		"column": column,
		"type": type,
		"next": next_ids.duplicate(),
		"visited": visited,
	}

static func from_dict(data: Dictionary) -> RunNode:
	if not (data.has("id") and data.has("floor") and data.has("column") and data.has("type")):
		return null
	var node: RunNode = RunNode.new(int(data["id"]), int(data.get("act", 1)), int(data["floor"]), int(data["column"]), int(data["type"]))
	for n in data.get("next", []):
		node.connect_to(int(n))
	node.visited = bool(data.get("visited", false))
	return node
