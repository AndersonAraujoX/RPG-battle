# res://test/unit/test_meta_screens.gd
extends GutTest

## Testes Unitários: Telas de Quartel (BarracksScreen) e Fim de Expedição (RunEndScreen)
## Valida renderização headless-safe, interação com MetaProgression e disparo de sinais.

const TEST_SAVE_PATH: String = "user://test_meta_screens_save.json"

var _meta: MetaProgression
var _barracks: BarracksScreen
var _end_screen: RunEndScreen

func before_each() -> void:
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)
	_meta = MetaProgression.new(TEST_SAVE_PATH)
	_barracks = BarracksScreen.new()
	_end_screen = RunEndScreen.new()

func after_each() -> void:
	if _barracks != null:
		_barracks.free()
		_barracks = null
	if _end_screen != null:
		_end_screen.free()
		_end_screen = null
	if _meta != null:
		_meta = null
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)

# ── 1. BarracksScreen ─────────────────────────────────────────────────────────

func test_barracks_headless_safe_instantiation() -> void:
	# Assert
	assert_not_null(_barracks)
	_barracks.setup(_meta)
	_barracks.refresh_ui()
	pass_test("BarracksScreen instancia e atualiza sem erros em modo headless")

func test_barracks_unlock_hero_interaction() -> void:
	# Arrange
	_meta.deposit_amber(100)
	_barracks.setup(_meta)
	watch_signals(_barracks)

	# Act
	_barracks._on_unlock_hero_clicked("doom")

	# Assert
	assert_true(_meta.is_hero_unlocked("doom"))
	assert_signal_emitted_with_parameters(_barracks, "hero_unlocked_ui", ["doom"])

func test_barracks_ascension_controls() -> void:
	# Arrange: Desbloqueia ascensão via vitória
	_meta.total_victories = 1
	_meta.max_unlocked_ascension = 2
	_barracks.setup(_meta)
	watch_signals(_barracks)

	# Act 1: Sobe ascensão
	_barracks._on_ascension_up()

	# Assert 1
	assert_eq(_meta.current_ascension, 1)
	assert_signal_emitted_with_parameters(_barracks, "ascension_selected_ui", [1])

	# Act 2: Desce ascensão
	_barracks._on_ascension_down()

	# Assert 2
	assert_eq(_meta.current_ascension, 0)
	assert_signal_emitted_with_parameters(_barracks, "ascension_selected_ui", [0])

func test_barracks_back_button_signal() -> void:
	# Arrange
	watch_signals(_barracks)

	# Act
	_barracks._on_back_pressed()

	# Assert
	assert_signal_emitted(_barracks, "back_requested")

# ── 2. RunEndScreen ───────────────────────────────────────────────────────────

func test_run_end_screen_victory_with_hearts_spared() -> void:
	# Arrange
	var state: RunState = RunState.new()
	state.status = RunState.Status.VICTORY
	state.floors_cleared = 12
	state.bosses_defeated = 3
	state.enemies_killed = 25
	# destroyed_hearts está vazio -> bônus lendário em dobro
	watch_signals(_end_screen)

	# Act
	_end_screen.setup(true, state, _meta)

	# Assert
	assert_true(_end_screen.victory)
	assert_true(_end_screen.summary_data.hearts_spared)
	assert_eq(_end_screen.summary_data.amber_earned, 134)

func test_run_end_screen_defeat() -> void:
	# Arrange
	var state: RunState = RunState.new()
	state.status = RunState.Status.DEFEAT
	state.floors_cleared = 5
	state.bosses_defeated = 0
	state.enemies_killed = 10

	# Act
	_end_screen.setup(false, state, _meta)

	# Assert
	assert_false(_end_screen.victory)
	assert_eq(_end_screen.summary_data.amber_earned, 5)

func test_run_end_screen_buttons_signals() -> void:
	# Arrange
	watch_signals(_end_screen)

	# Act & Assert
	_end_screen._on_menu_pressed()
	assert_signal_emitted(_end_screen, "return_to_menu_requested")

	_end_screen._on_barracks_pressed()
	assert_signal_emitted(_end_screen, "open_barracks_requested")
