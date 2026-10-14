extends SceneTree

func _init() -> void:
	var watchdog: SceneTreeTimer = create_timer(5.0)
	watchdog.timeout.connect(func():
		push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
		quit(1)
	)
	var root_control: Control = Control.new()
	root_control.position = Vector2.ZERO
	root_control.size = Vector2(1280, 720)
	root_control.custom_minimum_size = Vector2(1280, 720)
	root.add_child(root_control)

	# Fundo temático Dark Fantasy rico
	var bg: ColorRect = ColorRect.new()
	bg.position = Vector2.ZERO
	bg.size = Vector2(1280, 720)
	bg.color = Color(0.06, 0.07, 0.11, 1.0)
	root_control.add_child(bg)

	# Moldura principal
	var main_panel: Panel = Panel.new()
	main_panel.position = Vector2(24, 20)
	main_panel.size = Vector2(1232, 680)
	var mp_style: StyleBoxFlat = StyleBoxFlat.new()
	mp_style.bg_color = Color(0.08, 0.09, 0.14, 0.96)
	mp_style.set_border_width_all(2)
	mp_style.border_color = Color(0.24, 0.30, 0.44, 0.8)
	mp_style.set_corner_radius_all(10)
	mp_style.shadow_size = 8
	mp_style.shadow_color = Color(0.0, 0.0, 0.0, 0.6)
	main_panel.add_theme_stylebox_override("panel", mp_style)
	root_control.add_child(main_panel)

	var main_vbox: VBoxContainer = VBoxContainer.new()
	main_vbox.position = Vector2(16, 16)
	main_vbox.size = Vector2(1200, 648)
	main_vbox.add_theme_constant_override("separation", 14)
	main_panel.add_child(main_vbox)

	# Cabeçalho Showcase
	var header_box: VBoxContainer = VBoxContainer.new()
	header_box.alignment = BoxContainer.ALIGNMENT_CENTER
	var title_lbl: Label = Label.new()
	title_lbl.text = "⚔ CERCO CONTRA ISECTUM — DESIGN DAS CARTAS TÁTICAS ⚔"
	title_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_lbl.add_theme_font_size_override("font_size", 21)
	title_lbl.add_theme_color_override("font_color", Color(1.0, 0.88, 0.35))
	header_box.add_child(title_lbl)

	var sub_lbl: Label = Label.new()
	sub_lbl.text = "Fidelidade Dark Fantasy: Molduras com Drop Shadow • Badges de Arquétipos • Chips de Recursos • Estados (Hover, Seleção, Bloqueada)"
	sub_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub_lbl.add_theme_font_size_override("font_size", 12)
	sub_lbl.add_theme_color_override("font_color", Color(0.72, 0.80, 0.94))
	header_box.add_child(sub_lbl)
	main_vbox.add_child(header_box)

	# Seção 1: Vitrine de Arquétipos e Estados
	var sec1_lbl: Label = Label.new()
	sec1_lbl.text = "— ARQUÉTIPOS & ESTADOS VISUAIS (NORMAL, HOVER, SELEÇÃO, BLOQUEADA) —"
	sec1_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sec1_lbl.add_theme_font_size_override("font_size", 12)
	sec1_lbl.add_theme_color_override("font_color", Color(0.85, 0.9, 1.0))
	main_vbox.add_child(sec1_lbl)

	var cards_row: HBoxContainer = HBoxContainer.new()
	cards_row.alignment = BoxContainer.ALIGNMENT_CENTER
	cards_row.add_theme_constant_override("separation", 24)
	main_vbox.add_child(cards_row)

	# Carta 1: Marcha (Normal)
	var c1_data: CardData = CardData.new()
	c1_data.id = "c1"
	c1_data.card_name = "Marcha Rápida"
	c1_data.badge = CardData.BADGE_MARCHA
	c1_data.cost_wood = 1
	c1_data.cost_ap = 1
	c1_data.movement = 3
	c1_data.description = "Move o herói rapidamente até a brecha da muralha."
	var c1_ui: CardUI = CardUI.new()
	c1_ui.setup(c1_data, 0)
	cards_row.add_child(c1_ui)

	# Carta 2: Trabalho (Hovered / Borda Ouro Reluzente)
	var c2_data: CardData = CardData.new()
	c2_data.id = "c2"
	c2_data.card_name = "Martelo da Forja"
	c2_data.badge = CardData.BADGE_TRABALHO
	c2_data.cost_wood = 2
	c2_data.cost_metal = 2
	c2_data.work = 3
	c2_data.description = "Repara 25 HP da muralha ou forja reforços defensivos."
	var c2_ui: CardUI = CardUI.new()
	c2_ui.setup(c2_data, 1)
	c2_ui.set_hovered(true)
	cards_row.add_child(c2_ui)

	# Carta 3: Escavação (Selecionada / Aura Arcana Violeta)
	var c3_data: CardData = CardData.new()
	c3_data.id = "c3"
	c3_data.card_name = "Escavação de Fuga"
	c3_data.badge = CardData.BADGE_ESCAVACAO
	c3_data.cost_wood = 2
	c3_data.cost_leather = 1
	c3_data.excavation = 3
	c3_data.description = "Escava passagens subterrâneas e colhe materiais brutos."
	var c3_ui: CardUI = CardUI.new()
	c3_ui.setup(c3_data, 2)
	c3_ui.set_selected(true)
	cards_row.add_child(c3_ui)

	# Carta 4: Combate (Normal)
	var c4_data: CardData = CardData.new()
	c4_data.id = "c4"
	c4_data.card_name = "Vanguarda de Aço"
	c4_data.badge = CardData.BADGE_COMBATE
	c4_data.cost_metal = 3
	c4_data.cost_ap = 2
	c4_data.movement = 1
	c4_data.description = "Ataque impetuoso causando 2d8 de dano contra o invasor."
	var c4_ui: CardUI = CardUI.new()
	c4_ui.setup(c4_data, 3)
	cards_row.add_child(c4_ui)

	# Carta 5: Especial / Upgrade (Normal)
	var c5_data: CardData = CardData.new()
	c5_data.id = "c5"
	c5_data.card_name = "Bênção Arcana"
	c5_data.badge = CardData.BADGE_ESPECIAL
	c5_data.cost_crystal = 2
	c5_data.cost_ap = 1
	c5_data.description = "Canaliza a energia dos cristais para energizar todos aliados."
	var c5_ui: CardUI = CardUI.new()
	c5_ui.setup(c5_data, 4)
	cards_row.add_child(c5_ui)

	# Carta 6: Bloqueada / Custo Insuficiente
	var c6_data: CardData = CardData.new()
	c6_data.id = "c6"
	c6_data.card_name = "Defesa Sagrada"
	c6_data.badge = CardData.BADGE_TRABALHO
	c6_data.cost_wood = 5
	c6_data.cost_metal = 4
	c6_data.work = 4
	c6_data.description = "Fortifica os portões principais com barreira inexpugnável."
	var c6_ui: CardUI = CardUI.new()
	c6_ui.setup(c6_data, 5)
	c6_ui.set_disabled(true)
	cards_row.add_child(c6_ui)

	# Seção 2: Exibição no Leque Dinâmico da Mão
	var sec2_lbl: Label = Label.new()
	sec2_lbl.text = "— DISPOSIÇÃO EM LEQUE DINÂMICO NA MÃO DO JOGADOR —"
	sec2_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sec2_lbl.add_theme_font_size_override("font_size", 12)
	sec2_lbl.add_theme_color_override("font_color", Color(0.85, 0.9, 1.0))
	main_vbox.add_child(sec2_lbl)

	var fan_wrapper: CenterContainer = CenterContainer.new()
	main_vbox.add_child(fan_wrapper)

	var fan_container: CardFanContainer = CardFanContainer.new()
	fan_container.custom_minimum_size = Vector2(700.0, 180.0)
	fan_wrapper.add_child(fan_container)

	fan_container.add_card(c1_data)
	fan_container.add_card(c2_data)
	fan_container.add_card(c3_data)
	fan_container.add_card(c4_data)
	fan_container.add_card(c5_data)

	var timer: SceneTreeTimer = create_timer(0.5)
	timer.timeout.connect(_on_capture)

func _on_capture() -> void:
	var img: Image = root.get_viewport().get_texture().get_image()
	if img != null:
		var target_path: String = "/home/anderson/.gemini/antigravity/brain/2948efb9-2f48-449b-bd70-605905f7f99d/showcase_cartas.png"
		var err = img.save_png(target_path)
		print("Cards showcase saved to %s (code=%d)" % [target_path, err])
	quit(0)
