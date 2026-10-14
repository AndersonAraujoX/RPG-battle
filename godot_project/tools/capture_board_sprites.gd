extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer = create_timer(0.8)
	timer.timeout.connect(_on_capture)

func _on_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/tactical_board_sprites.png")
		print("Saved tactical_board_sprites.png successfully")
	quit(0)
