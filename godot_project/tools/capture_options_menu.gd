extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Menu.tscn")
	var timer = create_timer(0.4)
	timer.timeout.connect(_on_step1)

func _on_step1() -> void:
	var menu = root.get_node_or_null("Menu")
	if menu != null:
		# Open Options modal
		menu._on_btn_opcoes_pressed()
	
	var timer2 = create_timer(0.3)
	timer2.timeout.connect(_on_step2)

func _on_step2() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/options_menu_screenshot.png")
		print("Saved options_menu_screenshot.png successfully")
	
	# Now test in HUD
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer3 = create_timer(0.5)
	timer3.timeout.connect(_on_step3)

func _on_step3() -> void:
	var controller = root.get_node_or_null("Main")
	if controller != null and controller.hud_instance != null:
		# Open options in HUD
		controller.hud_instance._open_options_modal()
	
	var timer4 = create_timer(0.3)
	timer4.timeout.connect(_on_step4)

func _on_step4() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/options_hud_screenshot.png")
		print("Saved options_hud_screenshot.png successfully")
	quit(0)
