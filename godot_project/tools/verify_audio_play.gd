extends SceneTree

var am: Node

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(6.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	change_scene_to_file("res://scenes/main/Menu.tscn")
	var timer = create_timer(0.2)
	timer.timeout.connect(_on_menu_loaded)

func _on_menu_loaded() -> void:
	am = root.get_node_or_null("AudioManager")
	if am == null:
		print("FAIL: AudioManager not found in root")
		quit(1)
		return
	
	print("[VERIFY] Menu loaded. Current BGM: ", am.get_current_bgm(), " Playing: ", am.is_bgm_playing())
	if not am.is_bgm_playing() or am.get_current_bgm() != "menu":
		print("FAIL: Menu BGM not playing properly")
		quit(1)
		return
	
	# Wait 1.2s to exceed 1.0s crossfade duration and verify stream was NOT cleared
	var timer2 = create_timer(1.2)
	timer2.timeout.connect(_after_menu_fade)

func _after_menu_fade() -> void:
	print("[VERIFY] After 1.2s menu BGM: playing=", am.is_bgm_playing(), " stream=", am._active_bgm_player.stream, " volume_db=", am._active_bgm_player.volume_db)
	if am._active_bgm_player.stream == null or not am.is_bgm_playing():
		print("FAIL: Menu BGM was nullified after crossfade!")
		quit(1)
		return
	
	# Transition to Battle
	print("[VERIFY] Starting crossfade to battle1...")
	am.play_bgm("battle1", 1.0)
	
	var timer3 = create_timer(1.2)
	timer3.timeout.connect(_after_battle_fade)

func _after_battle_fade() -> void:
	print("[VERIFY] After 1.2s battle1 BGM: playing=", am.is_bgm_playing(), " stream=", am._active_bgm_player.stream, " volume_db=", am._active_bgm_player.volume_db)
	if am._active_bgm_player.stream == null or not am.is_bgm_playing():
		print("FAIL: Battle1 BGM was nullified after crossfade!")
		quit(1)
		return
	
	print("SUCCESS: All BGM transitions, crossfades, and streams preserved!")
	quit(0)
