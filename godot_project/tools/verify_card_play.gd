extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer: SceneTreeTimer = create_timer(0.5)
	timer.timeout.connect(_on_step1)

func _on_step1() -> void:
	var controller = root.get_node_or_null("Main")
	if controller == null:
		print("ERROR: Main node not found")
		quit(1)
		return
	
	var hud: HUD = controller.hud_instance
	if hud == null or hud.card_fan == null:
		print("ERROR: HUD or CardFan null")
		quit(1)
		return
	
	print("Cards in fan before play: ", hud.card_fan.get_card_count())
	print("Wood before play: ", controller.economy.wood)
	
	# Select card 1 (Trabalho or Escavação)
	hud.card_fan.select_card(1)
	var sel_card: CardData = hud.card_fan.get_selected_card()
	print("Selected card: ", sel_card.id, " - ", sel_card.card_name)
	
	# Play targeting Carpintaria
	hud._on_board_zone_clicked("CARPINTARIA")
	
	var timer2: SceneTreeTimer = create_timer(0.5)
	timer2.timeout.connect(_on_step2)

func _on_step2() -> void:
	var controller = root.get_node_or_null("Main")
	var hud: HUD = controller.hud_instance
	print("Cards in fan after play: ", hud.card_fan.get_card_count())
	print("Wood after play: ", controller.economy.wood)
	print("Last log: ", hud.combat_log.get_last_entry_text())
	
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		img.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/card_activated_screenshot.png")
	
	quit(0)
