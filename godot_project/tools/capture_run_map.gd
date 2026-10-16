extends SceneTree

## Script de captura de tela do Mapa Roguelike (M1 & M2)
## Protegido com Watchdog de acordo com a Skill prevencao_execucao_infinita.

func _init() -> void:
	# Watchdog fail-safe
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		printerr("TIMEOUT FAIL-SAFE: capture_run_map.gd excedeu 5s!")
		quit(1)
	)

	# Iniciar uma sessão de run para teste
	RunSession.start_new(9876)

	change_scene_to_file("res://scenes/run/RunMapScreen.tscn")
	var timer: SceneTreeTimer = create_timer(0.6)
	timer.timeout.connect(_on_step_capture)

func _on_step_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_mapa_roguelike.png"
		var err: Error = img.save_png(target_path)
		if err == OK:
			print("Salvo screenshot em: ", target_path)
		else:
			printerr("Erro ao salvar png: ", err)
	quit(0)
