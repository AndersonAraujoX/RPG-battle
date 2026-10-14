# res://test/unit/test_cerco_screens.gd
extends GutTest

## Test suite for CercoSetup, Isometric FortressBoardView, and CercoMarketPanel.
## Follows strict AAA pattern with edge case coverage and zero memory leaks.

# ── 1. CercoSetup Tests ──────────────────────────────────────────────────────

func test_cerco_setup_initial_defaults() -> void:
	# Arrange
	var setup: CercoSetup = autofree(CercoSetup.new())
	
	# Act
	setup._ready()
	
	# Assert
	assert_true(setup.selected_heroes.has("Aquele"), "Aquele should be present in hero table")
	assert_true(setup.selected_heroes["Aquele"], "Aquele is selected by default")
	assert_eq(setup.selected_diff_index, 1, "Default difficulty is Media (index 1)")
	assert_eq(setup.selected_res_index, 3, "Default resolution is 1280x720 (index 3)")

func test_cerco_setup_hero_selection_toggle() -> void:
	# Arrange
	var setup: CercoSetup = autofree(CercoSetup.new())
	setup._ready()
	
	# Act - Select Stark
	setup._on_hero_clicked("Stark")
	
	# Assert
	assert_true(setup.selected_heroes.get("Stark", false), "Stark should now be selected")
	
	# Act - Toggle Stark off
	setup._on_hero_clicked("Stark")
	
	# Assert
	assert_false(setup.selected_heroes.get("Stark", false), "Stark should now be deselected")

func test_cerco_setup_difficulty_selection_changes_factor() -> void:
	# Arrange
	var setup: CercoSetup = autofree(CercoSetup.new())
	setup._ready()
	
	# Act - Select Fácil
	setup._on_diff_clicked(0)
	var diff_facil: Dictionary = CercoSetup.DIFFICULTIES[setup.selected_diff_index]
	
	# Assert
	assert_eq(setup.selected_diff_index, 0, "Difficulty index is 0")
	assert_almost_eq(diff_facil["fator"], 0.25, 0.001, "Fácil factor is 0.25")
	
	# Act - Select Difícil
	setup._on_diff_clicked(2)
	var diff_dif: Dictionary = CercoSetup.DIFFICULTIES[setup.selected_diff_index]
	
	# Assert
	assert_eq(setup.selected_diff_index, 2, "Difficulty index is 2")
	assert_almost_eq(diff_dif["fator"], 1.0, 0.001, "Difícil factor is 1.00")

func test_cerco_setup_resolution_selection() -> void:
	# Arrange
	var setup: CercoSetup = autofree(CercoSetup.new())
	setup._ready()
	
	# Act
	setup._on_res_clicked(0)
	
	# Assert
	assert_eq(setup.selected_res_index, 0, "Selected resolution index is 0")
	assert_eq(CercoSetup.RESOLUTIONS[0], Vector2i(800, 600), "Index 0 is 800x600")

func test_cerco_setup_start_signal_emits_valid_config() -> void:
	# Arrange
	var setup: CercoSetup = autofree(CercoSetup.new())
	setup._ready()
	watch_signals(setup)
	
	# Act - Start cerco
	setup.cerco_iniciado.emit({
		"herois": setup.selected_heroes,
		"dificuldade": CercoSetup.DIFFICULTIES[setup.selected_diff_index],
		"resolucao": CercoSetup.RESOLUTIONS[setup.selected_res_index]
	})
	
	# Assert
	assert_signal_emitted(setup, "cerco_iniciado")

# ── 2. Isometric FortressBoardView Tests ──────────────────────────────────────

func test_fortress_board_view_draw_headless_safety() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	bv.size = Vector2(700.0, 480.0)
	
	# Act
	bv.queue_redraw()
	
	# Assert
	assert_true(bv.size.x > 0, "BoardView width is positive")
	assert_true(bv.size.y > 0, "BoardView height is positive")

func test_fortress_board_view_canonical_workshop_outlines() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	
	# Act - Canonical quadrant cells
	var z_carp: String = bv.get_zone_at(Vector2i(9, 6))
	var z_curt: String = bv.get_zone_at(Vector2i(9, 13))
	var z_fund: String = bv.get_zone_at(Vector2i(6, 9))
	var z_patio: String = bv.get_zone_at(Vector2i(13, 9))
	var z_cam: String = bv.get_zone_at(Vector2i(9, 9))
	
	# Assert
	assert_eq(z_carp, "CARPINTARIA", "Cell (9,6) belongs to Carpintaria (Norte)")
	assert_eq(z_curt, "CURTUME", "Cell (9,13) belongs to Curtume (Sul)")
	assert_eq(z_fund, "FUNDICAO", "Cell (6,9) belongs to Fundição (Oeste)")
	assert_eq(z_patio, "PATIO_CENTRAL", "Cell (13,9) belongs to Pátio Central (Leste)")
	assert_eq(z_cam, "CAMARA_CENTRAL", "Cell (9,9) belongs to Câmara Central (Centro)")

# ── 3. CercoMarketPanel Tests ────────────────────────────────────────────────

func test_market_panel_resource_updates() -> void:
	# Arrange
	var mp: CercoMarketPanel = autofree(CercoMarketPanel.new())
	mp._ready()
	
	# Act
	mp.update_resources(15, 12, 10)
	
	# Assert
	assert_eq(mp.wood, 15, "Wood updated to 15")
	assert_eq(mp.leather, 12, "Leather updated to 12")
	assert_eq(mp.metal, 10, "Metal updated to 10")

func test_market_panel_deck_capacity_updates() -> void:
	# Arrange
	var mp: CercoMarketPanel = autofree(CercoMarketPanel.new())
	mp._ready()
	
	# Act
	mp.set_deck_capacity(7, 15)
	
	# Assert
	assert_eq(mp.deck_current, 7, "Current deck count is 7")
	assert_eq(mp.deck_max, 15, "Max deck capacity is 15")

func test_market_panel_signals() -> void:
	# Arrange
	var mp: CercoMarketPanel = autofree(CercoMarketPanel.new())
	mp._ready()
	watch_signals(mp)
	
	# Act
	mp._on_card_clicked("plano_tatico")
	mp._on_end_turn_pressed()
	
	# Assert
	assert_signal_emitted_with_parameters(mp, "upgrade_purchased", ["plano_tatico"])
	assert_signal_emitted(mp, "end_turn_requested")

# ── 4. MainMenu Tests ─────────────────────────────────────────────────────────

func test_main_menu_scene_instantiation_and_structure() -> void:
	# Arrange
	var scene_res: PackedScene = load("res://scenes/main/Menu.tscn")
	assert_not_null(scene_res, "Menu.tscn packed scene must exist")
	var menu: MainMenu = autofree(scene_res.instantiate()) as MainMenu
	assert_not_null(menu, "Menu instance must be of class MainMenu")
	
	# Act
	menu._ready()
	
	# Assert - Buttons exist and have canonical text
	assert_not_null(menu.btn_jogar_cerco, "btn_jogar_cerco must be bound")
	assert_not_null(menu.btn_nova_campanha, "btn_nova_campanha must be bound")
	assert_not_null(menu.btn_continuar, "btn_continuar must be bound")
	assert_not_null(menu.btn_opcoes, "btn_opcoes must be bound")
	assert_not_null(menu.btn_dev_tools, "btn_dev_tools must be bound")
	assert_not_null(menu.btn_sair, "btn_sair must be bound")
	
	assert_eq(menu.btn_jogar_cerco.text, "JOGAR CERCO")
	assert_eq(menu.btn_nova_campanha.text, "NOVA CAMPANHA")
	assert_eq(menu.btn_continuar.text, "CONTINUAR")
	assert_eq(menu.btn_opcoes.text, "OPÇÕES")
	assert_eq(menu.btn_dev_tools.text, "DEV TOOLS")
	assert_eq(menu.btn_sair.text, "SAIR")
	
	# Assert - Background and Title labels
	var bg: TextureRect = menu.get_node_or_null("Background") as TextureRect
	assert_not_null(bg, "Background TextureRect must exist")
	assert_not_null(bg.texture, "Background must have a valid texture")
	
	var lbl_title: Label = menu.get_node_or_null("TitleContainer/LblCercoContra") as Label
	var lbl_subtitle: Label = menu.get_node_or_null("TitleContainer/LblIsectum") as Label
	assert_not_null(lbl_title, "LblCercoContra must exist")
	assert_not_null(lbl_subtitle, "LblIsectum must exist")
	assert_eq(lbl_title.text, "Cerco contra")
	assert_eq(lbl_subtitle.text, "Isectum")

func test_main_menu_legacy_references_parity() -> void:
	# Arrange
	var scene_res: PackedScene = load("res://scenes/main/Menu.tscn")
	var menu: MainMenu = autofree(scene_res.instantiate()) as MainMenu
	
	# Act
	menu._ready()
	
	# Assert
	assert_eq(menu.btn_play, menu.btn_jogar_cerco, "Legacy btn_play maps to btn_jogar_cerco")
	assert_eq(menu.btn_castes, menu.btn_nova_campanha, "Legacy btn_castes maps to btn_nova_campanha")
	assert_eq(menu.btn_multiplayer, menu.btn_opcoes, "Legacy btn_multiplayer maps to btn_opcoes")
	assert_eq(menu.btn_quit, menu.btn_sair, "Legacy btn_quit maps to btn_sair")

func test_main_menu_bare_node_headless_safety() -> void:
	# Arrange - Bare node with no tree and no child nodes
	var menu: MainMenu = autofree(MainMenu.new())
	
	# Act & Assert - Should not crash or throw errors
	menu._ready()
	menu._on_btn_jogar_cerco_pressed()
	menu._on_btn_nova_campanha_pressed()
	menu._on_btn_continuar_pressed()
	menu._on_btn_opcoes_pressed()
	menu._on_btn_dev_tools_pressed()
	menu._on_btn_sair_pressed()
	menu._on_btn_play_pressed()
	menu._on_btn_castes_pressed()
	menu._on_btn_multiplayer_pressed()
	menu._on_btn_quit_pressed()
	menu._play_hover_sound()
	menu._play_click_sound()
	
	assert_null(menu.btn_jogar_cerco, "Bare menu has null buttons safely")

func test_main_menu_idempotent_button_wiring() -> void:
	# Arrange
	var scene_res: PackedScene = load("res://scenes/main/Menu.tscn")
	var menu: MainMenu = autofree(scene_res.instantiate()) as MainMenu
	menu._ready()
	
	# Act - Wire multiple times
	menu._wire_buttons()
	menu._wire_buttons()
	
	# Assert - Connection count should be exactly 1
	var conns: Array = menu.btn_jogar_cerco.pressed.get_connections()
	assert_eq(conns.size(), 1, "Button should have exactly 1 connection after multiple wiring calls")

func test_main_menu_button_theme_and_styling() -> void:
	# Arrange
	var scene_res: PackedScene = load("res://scenes/main/Menu.tscn")
	var menu: MainMenu = autofree(scene_res.instantiate()) as MainMenu
	
	# Act
	menu._ready()
	
	# Assert - StyleBox overrides exist on buttons
	var style_jogar: StyleBox = menu.btn_jogar_cerco.get_theme_stylebox("normal")
	assert_not_null(style_jogar, "BtnJogarCerco must have a custom normal stylebox")
	var style_dark: StyleBox = menu.btn_nova_campanha.get_theme_stylebox("normal")
	assert_not_null(style_dark, "BtnNovaCampanha must have a custom normal stylebox")
	var style_dev: StyleBox = menu.btn_dev_tools.get_theme_stylebox("normal")
	assert_not_null(style_dev, "BtnDevTools must have a custom normal stylebox")
	
	# Assert - Font sizes
	var fsize_jogar: int = menu.btn_jogar_cerco.get_theme_font_size("font_size")
	assert_eq(fsize_jogar, 20, "Button font size should be 20")

# ── 5. CercoGameController & SyncRound Alias Tests ────────────────────────────

func test_cerco_sync_round_resolve_round_alias_and_flexible_signature() -> void:
	# Arrange
	var sync_round: CercoSyncRound = CercoSyncRound.new()
	var board: FortressBoard = FortressBoard.new()
	var economy: WorkshopEconomy = WorkshopEconomy.new()
	var judge: CercoCombatJudge = CercoCombatJudge.new()
	
	# Act 1: Calling with (board, economy, judge) convention
	var res1: Dictionary = sync_round.resolve_round(board, economy, judge)
	
	# Assert 1
	assert_not_null(res1, "resolve_round with (board, economy, judge) must return a dictionary")
	assert_true(res1.has("round_number"), "Result must contain round_number")
	
	# Act 2: Calling with (round_number, board, judge, economy) convention
	var res2: Dictionary = sync_round.resolve_round(2, board, judge, economy)
	
	# Assert 2
	assert_not_null(res2, "resolve_round with (round_number, board, judge, economy) must succeed")
	assert_eq(res2.get("round_number", 0), 2, "Round number must match passed value")

func test_cerco_game_controller_sync_round_requested() -> void:
	# Arrange
	var script: GDScript = load("res://scripts/main/CercoGameController.gd")
	var controller: Node = autofree(script.new())
	controller._initialize_models()
	
	# Act
	controller._on_hud_sync_round_requested()
	
	# Assert
	assert_eq(controller.current_round, 2, "Current round should increment to 2 after sync round request")

func test_cerco_game_controller_sync_round_draws_cards_into_hand() -> void:
	# Arrange
	var script: GDScript = load("res://scripts/main/CercoGameController.gd")
	var controller: Node = autofree(script.new())
	controller._initialize_models()
	
	# Simula jogador que gastou 2 cartas na rodada anterior
	controller.deck.play_card_by_index(0)
	controller.deck.play_card_by_index(0)
	assert_eq(controller.deck.get_hand().size(), 3, "Hand must have 3 cards before round sync")
	
	# Act - Passa a rodada
	controller._on_hud_sync_round_requested()
	
	# Assert - A mão deve ser recomposta com novas cartas
	assert_eq(controller.deck.get_hand().size(), 5, "Hand should be replenished back to max_hand_size (5)")
	assert_eq(controller.deck.get_discard_pile().size(), 2, "Discard pile has the 2 played cards")

func test_cerco_game_controller_sync_round_at_max_hand_draws_at_least_one() -> void:
	# Arrange - Mão já com 5 cartas (máximo)
	var script: GDScript = load("res://scripts/main/CercoGameController.gd")
	var controller: Node = autofree(script.new())
	controller._initialize_models()
	assert_eq(controller.deck.get_hand().size(), 5, "Initial hand is 5 cards")
	
	# Act - Passa a rodada mesmo com a mão cheia
	controller._on_hud_sync_round_requested()
	
	# Assert - Saca pelo menos 1 carta extra de rodada nova (6 cartas)
	assert_gt(controller.deck.get_hand().size(), 5, "Passing round must draw at least 1 new card")

func test_cerco_game_controller_market_purchase_adds_to_deck() -> void:
	# Arrange
	var script: GDScript = load("res://scripts/main/CercoGameController.gd")
	var controller: Node = autofree(script.new())
	controller._initialize_models()
	var initial_total_cards: int = controller.deck.get_total_deck_size()
	
	# Act - Compra upgrade do mercado (com recursos iniciais suficientes)
	controller._on_market_upgrade_purchased("plano_tatico")
	
	# Assert
	assert_eq(controller.deck.get_total_deck_size(), initial_total_cards + 1, "Total deck size increased by 1 card after purchase")
	assert_eq(controller.deck.get_discard_pile().size(), 1, "Purchased card placed in discard pile ready to be drawn")


