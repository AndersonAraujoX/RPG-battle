# res://test/unit/test_sprite_rendering.gd
extends GutTest

## Comprehensive GUT Unit Test Suite for Tactical Sprites & Tokens (SOLID + AAA)
## Tests FortressBoardView texture resolution and caching, Character.gd spritesheet frame slicing,
## and HUD.gd active hero avatar portrait binding with 0 leaks and strict AAA pattern.

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
const CHARACTER_SCENE: PackedScene = preload("res://scenes/entities/Character.tscn")

# ── 1. FortressBoardView Texture Resolution & Cache Tests ─────────────────────

func test_board_view_resolves_hero_portrait_texture() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())

	# Act
	var tex_aquele: Texture2D = bv.get_unit_texture("aquele", {"name": "?????", "class": "Guerreiro", "team": "A"})
	var tex_stark: Texture2D = bv.get_unit_texture("stark", {"name": "Stark", "class": "Paladino", "team": "A"})
	var tex_lysander: Texture2D = bv.get_unit_texture("lysander", {"name": "Pr. Lysander", "class": "Comandante", "team": "A"})

	# Assert
	assert_not_null(tex_aquele, "Aquele hero portrait resolved")
	assert_not_null(tex_stark, "Stark hero portrait resolved")
	assert_not_null(tex_lysander, "Lysander hero portrait resolved")
	assert_gt(tex_aquele.get_width(), 0, "Aquele portrait has valid positive width")
	assert_gt(tex_stark.get_width(), 0, "Stark portrait has valid positive width")

func test_board_view_texture_caching_idempotent() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	bv.clear_texture_cache()

	# Act
	var first_call: Texture2D = bv.get_unit_texture("stark")
	var second_call: Texture2D = bv.get_unit_texture("stark")

	# Assert
	assert_not_null(first_call, "First call returned texture")
	assert_eq(first_call, second_call, "Second call returns identical cached instance")

func test_board_view_resolves_isectum_caste_sprites() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())

	# Act
	var tex_vespa: Texture2D = bv.get_unit_texture("vespa_1", {"name": "Vespa Caçadora", "class": "Vespa", "team": "B"})
	var tex_besouro: Texture2D = bv.get_unit_texture("besouro_1", {"name": "Besouro Blindado", "class": "Besouro", "team": "B"})
	var tex_batedor: Texture2D = bv.get_unit_texture("batedor_1", {"name": "Batedor Isectum", "class": "Batedor", "team": "B"})
	var tex_soldado: Texture2D = bv.get_unit_texture("soldado_1", {"name": "Soldado Isectum", "class": "Soldado", "team": "B"})

	# Assert
	assert_not_null(tex_vespa, "Vespa caste sprite resolved")
	assert_not_null(tex_besouro, "Besouro caste sprite resolved")
	assert_not_null(tex_batedor, "Batedor caste sprite resolved")
	assert_not_null(tex_soldado, "Soldado caste sprite resolved")
	assert_eq(tex_vespa.get_width(), 32, "Caste sprite width is 32")
	assert_eq(tex_vespa.get_height(), 32, "Caste sprite height is 32")

func test_board_view_unknown_unit_returns_null_and_caches_safely() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())

	# Act
	var tex_unknown: Texture2D = bv.get_unit_texture("non_existent_entity_xyz_99")

	# Assert
	assert_null(tex_unknown, "Unknown unit safely returns null")
	var cached_lookup: Texture2D = bv.get_unit_texture("non_existent_entity_xyz_99")
	assert_null(cached_lookup, "Subsequent lookup uses cached null safely")

func test_board_view_clear_texture_cache_empties_dictionary() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var _t: Texture2D = bv.get_unit_texture("stark")

	# Act
	bv.clear_texture_cache()

	# Assert
	assert_eq(bv._unit_texture_cache.size(), 0, "Cache emptied after clear_texture_cache()")

func test_board_view_draw_unit_entity_headless_safe() -> void:
	# Arrange
	var bv: FortressBoardView = autofree(FortressBoardView.new())
	var ally_data: Dictionary = {"name": "Stark", "class": "Paladino", "team": "A", "hp": 50, "max_hp": 50}
	var enemy_data: Dictionary = {"name": "Vespa", "class": "Vespa", "team": "B", "hp": 20, "max_hp": 20}
	var unknown_data: Dictionary = {"name": "X", "team": "B", "hp": 5, "max_hp": 10}

	# Act & Assert - Execute drawing inside valid NOTIFICATION_DRAW context
	var draw_callable: Callable = func() -> void:
		bv._draw_unit_entity("stark", ally_data, Vector2(100, 100), 1.0, true)
		bv._draw_unit_entity("vespa_1", enemy_data, Vector2(200, 200), 1.0, false)
		bv._draw_unit_entity("unk", unknown_data, Vector2(300, 300), 1.0, false)
		bv._draw_hero_on_board(150, 150, 1.0)
		bv._draw_commander_throne(250, 250, 1.0)
	
	bv.draw.connect(draw_callable)
	bv.notification(CanvasItem.NOTIFICATION_DRAW)

	pass_test("Draw routines executed safely without errors in draw context")

# ── 2. Character Entity Spritesheet Frame Slicing Tests ───────────────────────

func test_character_discovers_portraits_path() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character

	# Act
	var ok: bool = character.load_texture_for_character("aquele")

	# Assert
	assert_true(ok, "Character successfully loads Aquele portrait")
	assert_not_null(character.sprite_2d.texture, "Texture assigned to Sprite2D")
	assert_gt(character.sprite_2d.texture.get_width(), 0, "Portrait texture has positive width")

func test_character_slice_spritesheet_frame_valid() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.target_display_size = Vector2(30.0, 30.0)
	var ok_load: bool = character.load_texture_for_character("guerreiro")
	assert_true(ok_load, "Loaded guerreiro 676x369 spritesheet")

	# Act
	var ok_slice: bool = character.slice_spritesheet_frame(0, 0, 4, 2)

	# Assert
	assert_true(ok_slice, "Spritesheet slice succeeded")
	assert_true(character.sprite_2d.region_enabled, "Region enabled on Sprite2D")
	assert_almost_eq(character.sprite_2d.region_rect.size.x, 169.0, 0.5, "Frame width is approx 169px")
	assert_almost_eq(character.sprite_2d.region_rect.size.y, 184.5, 0.5, "Frame height is approx 184.5px")

	var rendered_w: float = character.sprite_2d.region_rect.size.x * character.sprite_2d.scale.x
	var rendered_h: float = character.sprite_2d.region_rect.size.y * character.sprite_2d.scale.y
	assert_lte(rendered_w, 30.01, "Rendered width fits target display size")
	assert_lte(rendered_h, 30.01, "Rendered height fits target display size")

func test_character_auto_slice_multiframe_676x369() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.load_texture_for_character("guerreiro")

	# Act
	var sliced: bool = character.auto_slice_multiframe()

	# Assert
	assert_true(sliced, "auto_slice_multiframe() detected 676x369 sheet and isolated frame 0")
	assert_true(character.sprite_2d.region_enabled, "Region enabled")
	assert_gt(character.sprite_2d.region_rect.size.x, 0.0, "Region width positive")

func test_character_slice_invalid_parameters_safe() -> void:
	# Arrange
	var character: Character = add_child_autofree(CHARACTER_SCENE.instantiate()) as Character
	character.load_texture_for_character("guerreiro")

	# Act
	var invalid_cols: bool = character.slice_spritesheet_frame(0, 0, 0, 2)
	var invalid_rows: bool = character.slice_spritesheet_frame(0, 0, 4, -1)

	# Assert
	assert_false(invalid_cols, "Zero columns safely rejected")
	assert_false(invalid_rows, "Negative rows safely rejected")

# ── 3. HUD Active Hero Avatar Portrait Binding Tests ─────────────────────────

func test_hud_displays_active_hero_portrait() -> void:
	# Arrange
	var hud: HUD = add_child_autofree(HUD_SCENE.instantiate()) as HUD
	assert_not_null(hud.hero_avatar_icon, "HeroAvatarIcon resolved in HUD")

	# Act
	hud.update_active_hero({
		"id": "stark",
		"name": "Stark",
		"class": "Paladino",
		"hp": 52,
		"max_hp": 52
	})

	# Assert
	assert_not_null(hud.hero_avatar_icon.texture, "Avatar texture updated on hero selection")
	assert_gt(hud.hero_avatar_icon.texture.get_width(), 0, "Avatar texture has positive width")

func test_hud_update_active_hero_empty_dict_edge_case() -> void:
	# Arrange
	var hud: HUD = add_child_autofree(HUD_SCENE.instantiate()) as HUD

	# Act & Assert (Should not crash with empty dict)
	hud.update_active_hero({})
	pass_test("Empty hero dictionary handled safely")
