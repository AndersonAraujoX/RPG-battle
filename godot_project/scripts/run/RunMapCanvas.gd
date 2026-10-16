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

			var color: Color
			var width: float
			if is_active_branch:
				color = Color(1.0, 0.82, 0.25, 0.9)
				width = 3.0
			elif is_visited_path:
				color = Color(0.45, 0.5, 0.55, 0.6)
				width = 2.0
			else:
				color = Color(0.2, 0.22, 0.28, 0.5)
				width = 1.5

			draw_line(from_center, to_center, color, width, true)
