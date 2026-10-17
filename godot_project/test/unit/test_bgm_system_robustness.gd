# res://test/unit/test_bgm_system_robustness.gd
extends GutTest

## Test suite verifying BGM seamless looping, track aliasing, crossfades,
## and scene transition audio integrity.
## Follows strict Arrange-Act-Assert (AAA) pattern with edge case coverage.

var _am: Node

func before_each() -> void:
	# Cria ou obtém a instância do AudioManager
	if get_tree().root.has_node("AudioManager"):
		_am = get_tree().root.get_node("AudioManager")
	else:
		var am_script = load("res://scripts/autoload/AudioManager.gd")
		_am = autofree(am_script.new())
		get_tree().root.add_child(_am)

func after_each() -> void:
	if _am != null and _am.has_method("cleanup"):
		_am.cleanup()

# ── 1. Aliases e Resolução de Faixas ─────────────────────────────────────────

func test_bgm_new_screen_aliases_resolve_cleanly() -> void:
	# Arrange: Novas faixas de tela
	var aliases: Array[String] = ["mapa", "campanha", "quartel", "vitoria", "derrota"]

	for alias in aliases:
		# Act
		_am.play_bgm(alias, 0.0)

		# Assert
		assert_true(_am.is_bgm_playing(), "BGM deve estar tocando para alias: " + alias)
		assert_eq(_am.get_current_bgm(), alias, "Current BGM key deve corresponder ao alias")
		assert_not_null(_am._active_bgm_player.stream, "Stream deve estar carregado para " + alias)

# ── 2. Looping e Redundância Defensiva ───────────────────────────────────────

func test_bgm_finished_signal_triggers_loop_replay() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	var active_p: AudioStreamPlayer = _am._active_bgm_player
	assert_true(_am.is_bgm_playing())

	# Act: Simula término natural da faixa disparando _on_bgm_finished
	_am._on_bgm_finished(active_p)

	# Assert: Player ativo deve continuar tocando sem perder o stream
	assert_true(active_p.playing, "Player ativo deve reiniciar reprodução imediatamente")
	assert_not_null(active_p.stream, "Stream não pode ser nulo")
	assert_eq(_am.get_current_bgm(), "menu")

func test_bgm_finished_on_inactive_player_does_nothing() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	var inactive_p: AudioStreamPlayer = _am._bgm_player_b if _am._active_bgm_player == _am._bgm_player_a else _am._bgm_player_a
	inactive_p.stop()
	inactive_p.stream = null

	# Act
	_am._on_bgm_finished(inactive_p)

	# Assert
	assert_false(inactive_p.playing, "Player inativo não deve ser iniciado")

# ── 3. Reprodução da Mesma Faixa (Idempotência e Recuperação) ────────────────

func test_bgm_same_track_cancels_fade_out_and_restores_volume() -> void:
	# Arrange
	_am.play_bgm("battle1", 0.0)
	assert_eq(_am._active_bgm_player.volume_db, 0.0)

	# Inicia um stop com fade longo
	_am.stop_bgm(5.0)

	# Act: Mesma faixa é solicitada novamente
	_am.play_bgm("battle1", 1.0)

	# Assert
	assert_eq(_am._active_bgm_player.volume_db, 0.0, "Volume deve ser restaurado para 0.0 dB imediatamente")
	assert_true(_am.is_bgm_playing(), "BGM deve permanecer tocando")

func test_bgm_same_track_restarts_if_stopped() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	_am._active_bgm_player.stop()
	assert_false(_am.is_bgm_playing(), "Player foi pausado/parado manualmente")

	# Act: Chama a mesma faixa que estava parada
	_am.play_bgm("menu", 0.0)

	# Assert
	assert_true(_am.is_bgm_playing(), "Deve reiniciar reprodução se estava parada")
	assert_eq(_am._active_bgm_player.volume_db, 0.0)

# ── 4. Crossfade Concorrente e Integridade de Streams ────────────────────────

func test_bgm_rapid_crossfades_do_not_nullify_active_stream() -> void:
	# Arrange & Act: Múltiplas trocas rápidas de faixa
	_am.play_bgm("menu", 0.5)
	_am.play_bgm("battle1", 0.5)
	_am.play_bgm("mapa", 0.5)
	_am.play_bgm("quartel", 0.0)

	# Assert
	assert_true(_am.is_bgm_playing(), "Última faixa deve estar tocando perfeitamente")
	assert_not_null(_am._active_bgm_player.stream, "Stream do player ativo não pode ser nulo")
	assert_eq(_am.get_current_bgm(), "quartel")
	assert_eq(_am._active_bgm_player.volume_db, 0.0)

# ── 5. Parada Imediata e Limpeza ─────────────────────────────────────────────

func test_bgm_stop_zero_duration_stops_immediately() -> void:
	# Arrange
	_am.play_bgm("menu", 0.0)
	assert_true(_am.is_bgm_playing())

	# Act
	_am.stop_bgm(0.0)

	# Assert
	assert_false(_am.is_bgm_playing(), "BGM deve parar imediatamente com fade 0")
	assert_eq(_am.get_current_bgm(), "", "Current key deve estar vazia")
