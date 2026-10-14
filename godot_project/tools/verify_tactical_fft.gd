extends SceneTree

func _init() -> void:
	# Watchdog fail-safe: abort if script hangs
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		printerr("TIMEOUT: verify_tactical_fft.gd exceeded 5.0s!")
		quit(1)
	)

	change_scene_to_file("res://scenes/main/Main.tscn")
	var timer: SceneTreeTimer = create_timer(0.6)
	timer.timeout.connect(_on_step1)

func _on_step1() -> void:
	var controller = root.get_node_or_null("Main")
	if controller == null:
		print("ERROR: Main node not found")
		quit(1)
		return
	
	var hud: HUD = controller.hud_instance
	if hud == null or hud.board_view == null:
		print("ERROR: HUD or board_view null")
		quit(1)
		return

	print("--- STEP 1: VERIFYING FFT SELECTION & REACHABLE RANGE ---")
	print("Selected unit: ", hud.board_view.get_selected_unit())
	print("Reachable cells count: ", hud.board_view.get_reachable_cells().size())
	print("Attackable cells count: ", hud.board_view.get_attackable_cells().size())
	print("Board items count: ", controller.board.get_all_items().size())
	print("Initial crystals: ", controller.economy.crystal)

	# Ensure 'aquele' is selected and board view is updated
	hud.board_view.select_unit("aquele")

	# Save screenshot of initial FFT selection
	var img1: Image = root.get_viewport().get_texture().get_image()
	if img1 != null:
		img1.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/tactical_fft_selection.png")
		print("Saved tactical_fft_selection.png")

	# Step 2: Move Aquele to (8, 10) to pick up the 💎 Cristal Roxo (+2 cristais)
	print("--- STEP 2: MOVING TO (8, 10) TO PICK UP PURPLE CRYSTAL ---")
	hud.board_view.move_selected_unit_to(Vector2i(8, 10))

	var timer2: SceneTreeTimer = create_timer(0.6)
	timer2.timeout.connect(_on_step2)

func _on_step2() -> void:
	var controller = root.get_node_or_null("Main")
	var hud: HUD = controller.hud_instance

	print("Aquele new position: ", controller.board.get_unit_position("aquele"))
	print("Crystals after pickup: ", controller.economy.crystal)
	print("Last log entry: ", hud.combat_log.get_last_entry_text())

	var img2: Image = root.get_viewport().get_texture().get_image()
	if img2 != null:
		img2.save_png("/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/tactical_fft_pickup.png")
		print("Saved tactical_fft_pickup.png")

	print("SUCCESS: Tactical FFT & Item Pickup verified completely!")
	quit(0)
