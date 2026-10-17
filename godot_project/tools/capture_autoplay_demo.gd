extends SceneTree

## Script para captura de screenshots de demonstração do botão de Auto-Play:
## 1. Mapa com Auto-Play ativado (estado dourado pulsante)
## 2. Combate Tático (HUD) com botão Auto-Play em destaque

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(10.0)
	watchdog.timeout.connect(func():
		printerr("TIMEOUT FAIL-SAFE: capture_autoplay_demo.gd excedeu 10s!")
		quit(1)
	)

	_run_step_1_map_active()

func _run_step_1_map_active() -> void:
	RunSession.start_new(9876)
	change_scene_to_file("res://scenes/run/RunMapScreen.tscn")
	var t1: SceneTreeTimer = create_timer(0.6)
	t1.timeout.connect(func():
		var screen = current_scene as RunMapScreen
		if screen != null:
			# Ativa o modo autoplay para exibir o estado ativo com borda dourada
			screen.autoplay_active = true
			screen._update_autoplay_button_ui()
		var t2: SceneTreeTimer = create_timer(0.3)
		t2.timeout.connect(func():
			var img: Image = root.get_viewport().get_texture().get_image()
			if img != null:
				var path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_mapa_autoplay_ativo.png"
				img.save_png(path)
				print("Salvo screenshot mapa ativo em: ", path)
			_run_step_2_combat_hud()
		)
	)

func _run_step_2_combat_hud() -> void:
	change_scene_to_file("res://scenes/main/Main.tscn")
	var t1: SceneTreeTimer = create_timer(0.8)
	t1.timeout.connect(func():
		var img: Image = root.get_viewport().get_texture().get_image()
		if img != null:
			var path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_combate_autoplay.png"
			img.save_png(path)
			print("Salvo screenshot combate autoplay em: ", path)
		quit(0)
	)
