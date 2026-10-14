extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/cerco/CercoSetup.tscn")
	var timer: SceneTreeTimer = create_timer(0.4)
	timer.timeout.connect(_on_step1)

func _on_step1() -> void:
	var setup = root.get_node_or_null("CercoSetup")
	if setup != null:
		setup._on_hero_clicked("Stark")
		setup._on_hero_clicked("Lysander")
	
	var timer2: SceneTreeTimer = create_timer(0.3)
	timer2.timeout.connect(_on_step2)

func _on_step2() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/cerco_setup_portraits.png")
		print("Saved cerco_setup_portraits.png successfully")
	quit(0)
