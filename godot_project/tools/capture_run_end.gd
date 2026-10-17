extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento!")
		quit(1)
	)
	var state: RunState = RunState.new()
	state.status = RunState.Status.VICTORY
	state.floors_cleared = 12
	state.bosses_defeated = 3
	state.enemies_killed = 38
	state.destroyed_hearts = []

	var meta: MetaProgression = MetaProgression.new("user://preview_meta2.json")
	meta.amber_balance = 254

	change_scene_to_file("res://scenes/run/meta/RunEndScreen.tscn")
	var timer: SceneTreeTimer = create_timer(0.6)
	timer.timeout.connect(func():
		var scene: RunEndScreen = current_scene as RunEndScreen
		if scene != null:
			scene.setup(true, state, meta)
		var timer2: SceneTreeTimer = create_timer(0.5)
		timer2.timeout.connect(_on_capture)
	)

func _on_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_vitoria_suprema.png"
		img.save_png(target_path)
		print("Snapshot Vitoria salvo em: ", target_path)
	quit(0)
