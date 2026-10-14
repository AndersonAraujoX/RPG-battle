extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer = create_timer(1.2)
	timer.timeout.connect(_on_capture)

func _on_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_sem_sobreposicao.png"
		img.save_png(target_path)
		print("Snapshot salvo com sucesso em: ", target_path)
	quit(0)
