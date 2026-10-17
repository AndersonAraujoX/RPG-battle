extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento!")
		quit(1)
	)
	var meta: MetaProgression = MetaProgression.new("user://preview_meta.json")
	meta.amber_balance = 120
	meta.current_ascension = 2
	meta.max_unlocked_ascension = 3
	meta.unlocked_heroes.append("doom")

	change_scene_to_file("res://scenes/run/meta/BarracksScreen.tscn")
	var timer: SceneTreeTimer = create_timer(0.6)
	timer.timeout.connect(func():
		var scene: BarracksScreen = current_scene as BarracksScreen
		if scene != null:
			scene.setup(meta)
		var timer2: SceneTreeTimer = create_timer(0.5)
		timer2.timeout.connect(_on_capture)
	)

func _on_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_quartel_herois.png"
		img.save_png(target_path)
		print("Snapshot Quartel salvo em: ", target_path)
	quit(0)
