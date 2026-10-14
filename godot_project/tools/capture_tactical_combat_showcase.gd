extends SceneTree

func _init() -> void:
	# Watchdog Fail-Safe: Garante encerramento em até 4 segundos caso qualquer etapa trave
	var watchdog: SceneTreeTimer = create_timer(4.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)

	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer = create_timer(1.5)
	timer.timeout.connect(_on_setup_scene)

func _on_setup_scene() -> void:
	var cgc = root.get_node_or_null("Main") as CercoGameController
	if cgc != null and cgc.board != null and cgc.hud_instance != null and cgc.hud_instance.board_view != null:
		var board = cgc.board
		var bv = cgc.hud_instance.board_view

		# 1. Spawna um inimigo perto da muralha norte
		var enemy_pos = Vector2i(9, 7)
		board.place_unit("isectum_batedor", enemy_pos)
		board.register_unit("isectum_batedor", {
			"name": "Vespa Perfuradora",
			"class": "Isectum",
			"team": "B",
			"hp": 22,
			"max_hp": 30,
			"ac": 14,
			"move_range": 4,
			"attack_range": 2,
			"attack_bonus": 3
		})

		# 2. Danifica a muralha norte para exibir as fissuras e rachaduras de pedra
		board.damage_wall(FortressBoard.ZONE_MURALHA_NORTE, 60)
		bv.update_wall_hp("MURALHA_NORTE", 40)

		# 3. Posiciona o herói Aquele e coloca em mira contra a Vespa
		board.place_unit("aquele", Vector2i(9, 9))
		var aquel_data = board.get_unit_data("aquele")
		aquel_data["attack_range"] = 3
		board.set_unit_data("aquele", aquel_data)

		bv.select_unit("aquele")
		var typed_atks: Array[Vector2i] = [enemy_pos]
		bv.attackable_cells = typed_atks
		bv.hovered_cell = enemy_pos

		# 4. Zoom tático centrado para apreciar as tochas, sombras, fissuras e linha de mira
		bv.cam_zoom = 1.25
		bv.pan_to_unit("aquele")

		# 5. Adiciona partículas de faíscas e lascas de pedra
		var w_coords = bv.get_cell_screen_coords(enemy_pos.x, enemy_pos.y)
		bv.spawn_impact_particles(w_coords, "spark", 6)
		bv.spawn_impact_particles(w_coords, "stone", 4)
		bv.queue_redraw()

	var timer2 = create_timer(0.4)
	timer2.timeout.connect(func():
		var img: Image = root.get_viewport().get_texture().get_image()
		if img != null:
			var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_combate_tatica.png"
			img.save_png(target_path)
			print("Tactical combat showcase saved to: ", target_path)
		quit(0)
	)
