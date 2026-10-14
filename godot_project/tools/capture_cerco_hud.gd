extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer: SceneTreeTimer = create_timer(1.0)
	timer.timeout.connect(_on_timeout)

func _on_timeout() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var err = img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/cerco_game_screenshot.png")
		print("Screenshot saved err=", err)
	quit(0)
