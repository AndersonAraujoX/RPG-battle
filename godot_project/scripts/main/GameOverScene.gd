# res://scripts/main/GameOverScene.gd
class_name GameOverScene
extends Control

## Standalone Game Over Scene for GameManager.GameState.FIM_DE_JOGO.
## Embeds the GameOverModal and routes return to Menu or Restart.

@onready var modal: Control = get_node_or_null("GameOverModal")

func _ready() -> void:
	if modal != null:
		modal.restart_requested.connect(_on_restart_requested)
		modal.menu_requested.connect(_on_menu_requested)
		
		# Check if GameManager provided a payload
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("GameManager"):
			var gm: Node = tree.root.get_node("GameManager")
			var payload: Dictionary = gm.get("state_payload") if "state_payload" in gm else {}
			var is_win: bool = bool(payload.get("victory", false))
			var reason: String = str(payload.get("reason", ""))
			var stats: Dictionary = payload.get("stats", {})
			modal.setup(is_win, reason, stats)
			if tree.root.has_node("AudioManager"):
				var am: Node = tree.root.get_node("AudioManager")
				if am.has_method("play_bgm"):
					am.play_bgm("vitoria" if is_win else "derrota", 1.0)

func _on_restart_requested() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		if gm.has_method("change_state_and_scene"):
			gm.change_state_and_scene(2) # GameState.CERCO_ISECTUM
			return
	get_tree().change_scene_to_file("res://scenes/cerco/FortressBoard.tscn")

func _on_menu_requested() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		if gm.has_method("change_state_and_scene"):
			gm.change_state_and_scene(0) # GameState.MENU
			return
	get_tree().change_scene_to_file("res://scenes/main/Menu.tscn")
