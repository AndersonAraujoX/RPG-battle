# res://scripts/run/RunMapCanvas.gd
class_name RunMapCanvas
extends Control

## Canvas dedicado a desenhar as arestas e conexões entre os nós do mapa.

var screen: RunMapScreen = null

func _ready() -> void:
	screen = get_parent().get_parent() as RunMapScreen

func _draw() -> void:
	if screen == null or screen.state == null or screen.state.map == null:
		return

	var map: RunMap = screen.state.map
	var available_ids: Array[int] = []
	for av in screen.state.get_available_nodes():
		available_ids.append(av.id)

	var current_node: RunNode = screen.state.get_current_node()

	for node in map.nodes:
		if not screen.node_buttons.has(node.id):
			continue
		var btn_from: Button = screen.node_buttons[node.id]
		var from_center: Vector2 = btn_from.position + btn_from.size * 0.5

		for nid in node.next_ids:
			if not screen.node_buttons.has(nid):
				continue
			var btn_to: Button = screen.node_buttons[nid]
			var to_center: Vector2 = btn_to.position + btn_to.size * 0.5

			var is_visited_path: bool = node.visited and screen.state.map.get_node_by_id(nid).visited
			var is_active_branch: bool = (node.visited or (current_node != null and current_node.id == node.id)) and available_ids.has(nid)

			if is_active_branch:
				# Camada 1: Brilho incandescente suave
				draw_line(from_center, to_center, Color(1.0, 0.70, 0.20, 0.40), 7.0, true)
				# Camada 2: Trilha pontilhada dourada brilhante
				draw_dashed_line(from_center, to_center, Color(1.0, 0.92, 0.38, 0.95), 3.0, 6.0, true)
			elif is_visited_path:
				# Trilha percorrida
				draw_dashed_line(from_center, to_center, Color(0.60, 0.65, 0.70, 0.70), 2.5, 6.0, true)
			else:
				# Trilha futura sutil
				draw_dashed_line(from_center, to_center, Color(0.40, 0.42, 0.48, 0.45), 2.0, 5.0, true)
