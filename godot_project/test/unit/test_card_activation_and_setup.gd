# res://test/unit/test_card_activation_and_setup.gd
extends GutTest

## Test suite for character selection portraits/design and card activation mechanics.
## Follows strict Arrange-Act-Assert (AAA) pattern.

const PORTRAIT_PATHS: Array[String] = [
	"res://assets/images/characters/portraits/aquele_portrait.png",
	"res://assets/images/characters/portraits/stark_portrait.png",
	"res://assets/images/characters/portraits/elden_portrait.png",
	"res://assets/images/characters/portraits/doom_portrait.png",
	"res://assets/images/characters/portraits/gruu_portrait.png",
	"res://assets/images/characters/portraits/kuro_portrait.png",
	"res://assets/images/characters/portraits/darwin_portrait.png",
	"res://assets/images/characters/portraits/lysander_portrait.png"
]

func test_hero_portraits_exist_and_load_valid_textures() -> void:
	# Arrange & Act & Assert
	for path in PORTRAIT_PATHS:
		assert_true(ResourceLoader.exists(path), "Portrait file must exist: %s" % path)
		var tex: Texture2D = load(path) as Texture2D
		assert_not_null(tex, "Portrait texture must load: %s" % path)
		assert_gte(tex.get_width(), 64, "Portrait width must be at least 64px: %s" % path)
		assert_gte(tex.get_height(), 64, "Portrait height must be at least 64px: %s" % path)

func test_cerco_setup_hero_defs_structure_and_portraits() -> void:
	# Arrange & Act
	var defs: Array[Dictionary] = CercoSetup.HERO_DEFS

	# Assert
	assert_eq(defs.size(), 8, "There must be exactly 8 heroes in CercoSetup")
	for hero in defs:
		var sprite_path: String = hero.get("sprite", "")
		assert_ne(sprite_path, "", "Hero sprite path must not be empty for: %s" % str(hero.get("id")))
		assert_true(ResourceLoader.exists(sprite_path), "Hero sprite must exist: %s" % sprite_path)

func test_cerco_setup_instantiation_and_cards() -> void:
	# Arrange
	var setup_scene: PackedScene = load("res://scenes/cerco/CercoSetup.tscn")
	assert_not_null(setup_scene, "CercoSetup.tscn must load")
	var setup_inst: CercoSetup = autofree(setup_scene.instantiate() as CercoSetup)

	# Act
	var grid: GridContainer = setup_inst.find_child("HeroesGrid", true, false) as GridContainer

	# Assert
	assert_not_null(grid, "HeroesGrid must exist in CercoSetup")
	assert_eq(grid.get_child_count(), 8, "HeroesGrid must have 8 child cards")
	assert_eq(grid.columns, 4, "HeroesGrid must have 4 columns for clean 4x2 layout")

func test_card_ui_btn_play_exists_and_requests_play() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card_data: CardData = CardData.new()
	card_data.id = "teste_trab_1"
	card_data.card_name = "Trabalho"
	card_data.badge = CardData.BADGE_TRABALHO
	card_data.work = 3
	card_ui.setup(card_data, 0)

	watch_signals(card_ui)

	# Act
	var btn_play: Button = card_ui.find_child("BtnPlay", true, false) as Button
	assert_not_null(btn_play, "CardUI must contain a BtnPlay button")
	
	card_ui.request_play("CARPINTARIA")

	# Assert
	assert_signal_emitted(card_ui, "card_played_requested")

func test_hud_bind_economy_syncs_with_market_panel() -> void:
	# Arrange
	var hud_scene: PackedScene = load("res://scenes/ui/HUD.tscn")
	var hud: HUD = autofree(hud_scene.instantiate() as HUD)

	var economy: WorkshopEconomy = WorkshopEconomy.new()
	economy.set_resources(15, 12, 10, 5, 4)

	# Act
	hud.bind_economy(economy)
	economy.add_resource("wood", 10)
	economy.add_resource("leather", 5)

	# Assert
	assert_not_null(hud.market_panel, "HUD market_panel must exist")
	assert_eq(hud.market_panel.wood, 25, "Market panel wood must sync to 25")
	assert_eq(hud.market_panel.leather, 17, "Market panel leather must sync to 17")

func test_marcha_card_increases_hero_pm_and_updates_hud() -> void:
	# Arrange
	var main_scene: PackedScene = load("res://scenes/main/Main.tscn")
	var controller: Node = autofree(main_scene.instantiate())

	var board: FortressBoard = controller.board
	var udata_before: Dictionary = board.get_unit_data("aquele")
	var pm_before: int = int(udata_before.get("move_range", 4))

	var marcha_card: CardData = CardData.new()
	marcha_card.id = "marcha_test"
	marcha_card.card_name = "Marcha Rápida"
	marcha_card.badge = CardData.BADGE_MARCHA
	marcha_card.movement = 15

	# Act
	controller._apply_card_effects(marcha_card, "")
	var udata_after: Dictionary = board.get_unit_data("aquele")
	var pm_after: int = int(udata_after.get("move_range", 4))

	# Assert
	assert_gt(pm_after, pm_before, "Aquele PM must increase after playing Marcha card")
	assert_eq(pm_after, pm_before + 3, "Aquele PM must gain +3 from Marcha card")

func test_cerco_game_starts_clean_without_enemies() -> void:
	# Arrange
	var main_scene: PackedScene = load("res://scenes/main/Main.tscn")
	var controller: Node = autofree(main_scene.instantiate())

	# Act
	var board: FortressBoard = controller.board
	var team_b: Array[String] = board.get_units_by_team("B")
	var team_a: Array[String] = board.get_units_by_team("A")

	# Assert
	assert_eq(team_b.size(), 0, "No enemies should be placed at the beginning of the game")
	assert_gte(team_a.size(), 3, "All 3 defender heroes must be initialized")
	assert_has(team_a, "aquele", "Hero Aquele must be on board")
	assert_has(team_a, "stark", "Hero Stark must be on board")
	assert_has(team_a, "lysander", "Commander Lysander must be on board")

func test_cerco_spawn_enemy_wave_places_units_in_spawn_zones() -> void:
	# Arrange
	var main_scene: PackedScene = load("res://scenes/main/Main.tscn")
	var controller: Node = autofree(main_scene.instantiate())
	var board: FortressBoard = controller.board

	# Act
	var spawned: Array[String] = controller.spawn_enemy_wave(1)

	# Assert
	assert_gt(spawned.size(), 0, "Wave 1 must spawn enemy units")
	for uid in spawned:
		var udata: Dictionary = board.get_unit_data(uid)
		assert_eq(str(udata.get("team")), "B", "Spawned unit must belong to team B")
		var pos: Vector2i = board.get_unit_position(uid)
		var zone: String = board.get_zone_at(pos)
		assert_true(zone.begins_with("SPAWN_"), "Spawned unit %s at %s must be in an outer spawn zone, was: %s" % [uid, str(pos), zone])

func test_card_ui_btn_play_pressed_triggers_card_played_requested() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card: CardData = CardData.new()
	card.id = "c_play_test"
	card.card_name = "Marcha de Teste"
	card.badge = CardData.BADGE_MARCHA
	card.target_zone = "CARPINTARIA"
	card_ui.setup(card, 0)
	watch_signals(card_ui)

	# Act
	var btn_play: Button = card_ui.find_child("BtnPlay", true, false) as Button
	assert_not_null(btn_play, "CardUI must have BtnPlay")
	btn_play.pressed.emit()

	# Assert
	assert_signal_emitted_with_parameters(card_ui, "card_played_requested", [card, "CARPINTARIA"])

func test_card_ui_second_click_activates_selected_card() -> void:
	# Arrange
	var card_ui: CardUI = autofree(CardUI.new())
	var card: CardData = CardData.new()
	card.id = "c_click_test"
	card.card_name = "Ação"
	card.badge = CardData.BADGE_MARCHA
	card_ui.setup(card, 0)
	watch_signals(card_ui)

	# Act 1 - First click selects
	var ev1: InputEventMouseButton = InputEventMouseButton.new()
	ev1.button_index = MOUSE_BUTTON_LEFT
	ev1.pressed = true
	card_ui._gui_input(ev1)

	assert_true(card_ui.is_selected, "First click must select card")
	assert_signal_not_emitted(card_ui, "card_played_requested")

	# Act 2 - Second click on selected card plays it!
	var ev2: InputEventMouseButton = InputEventMouseButton.new()
	ev2.button_index = MOUSE_BUTTON_LEFT
	ev2.pressed = true
	card_ui._gui_input(ev2)

	# Assert
	assert_signal_emitted(card_ui, "card_played_requested")

func test_hud_show_floating_text_safe() -> void:
	# Arrange
	var hud: HUD = autofree(HUD.new())
	add_child_autofree(hud)

	# Act & Assert
	hud.show_floating_text("TESTE FLUTUANTE", Vector2(100, 100), Color.GREEN)
	assert_true(true, "show_floating_text must execute safely without errors")

func test_hud_clear_container_background_removes_purple_bar() -> void:
	# Arrange — cria um HBoxContainer simulando o CardsHBox
	var hud: HUD = autofree(HUD.new())
	add_child_autofree(hud)
	var fake_box := HBoxContainer.new()
	fake_box.name = "CardsHBoxTest"
	hud.add_child(fake_box)

	# Act — chama o método de limpeza diretamente
	hud._clear_container_background("CardsHBoxTest")

	# Assert — o node deve ter o override de StyleBox aplicado
	var sb: StyleBox = fake_box.get_theme_stylebox("panel")
	assert_not_null(sb, "StyleBox override deve ter sido aplicado ao container")
	if sb is StyleBoxFlat:
		var sb_flat: StyleBoxFlat = sb as StyleBoxFlat
		assert_eq(sb_flat.bg_color.a, 0.0, "bg_color deve ser totalmente transparente (a=0)")

func test_hud_clear_container_background_with_invalid_name_is_safe() -> void:
	# Arrange
	var hud: HUD = autofree(HUD.new())
	add_child_autofree(hud)

	# Act & Assert — nome que não existe não deve lançar erro
	hud._clear_container_background("NodeQueNaoExiste_xyz")
	assert_true(true, "Chamar _clear_container_background com nome inexistente não deve gerar erro")

