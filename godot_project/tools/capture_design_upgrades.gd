extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer = create_timer(1.8)
	timer.timeout.connect(_on_capture)

func _on_capture() -> void:
	var root_node = root.get_node_or_null("Main")
	if root_node != null:
		var cgc = root_node.get_node_or_null("CercoGameController")
		if cgc != null and cgc.hud_instance != null and cgc.hud_instance.board_view != null:
			var bv = cgc.hud_instance.board_view
			# Seleciona o primeiro herói e coloca hover sobre um inimigo/célula
			bv.select_unit("aquele")
			bv.hovered_cell = Vector2i(9, 10)
			bv.trigger_screen_shake(4.0, 0.4)
			bv.spawn_impact_particles(Vector2(400, 300), "spark", 6)
			bv.queue_redraw()

	# Aguarda mais 0.2s para renderizar o frame com efeitos
	var timer2 = create_timer(0.2)
	timer2.timeout.connect(func():
		var img: Image = root.get_viewport().get_texture().get_image()
		if img != null:
			var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_design_upgrades.png"
			img.save_png(target_path)
			print("Showcase de design upgrades salvo com sucesso em: ", target_path)
		quit(0)
	)
