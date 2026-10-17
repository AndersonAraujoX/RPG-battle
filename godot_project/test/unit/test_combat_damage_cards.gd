# res://test/unit/test_combat_damage_cards.gd
extends GutTest

## Test suite verifying tactical direct damage cards (Ataque, Golpe Pesado, Tiro Balista, Lâmina Ígnea, Martelo do Trovão, etc.)
## Follows strict Arrange-Act-Assert (AAA) pattern with comprehensive edge case and boundary condition coverage.

var _controller: CercoGameController
var _board: FortressBoard

func before_each() -> void:
	_controller = autofree(CercoGameController.new())
	_board = FortressBoard.new()
	_controller.board = _board

	# Setup herói aliado ("team A")
	_board.place_unit("aquele", Vector2i(9, 10))
	_board.register_unit("aquele", {
		"name": "Aquele",
		"team": "A",
		"hp": 50,
		"max_hp": 50,
		"move_range": 4
	})

func after_each() -> void:
	_board = null
	_controller = null

# ── 1. Caminho Feliz: Carta Básica de Ataque Reduz HP do Alvo ────────────────

func test_card_ataque_deals_damage_to_nearest_enemy() -> void:
	# Arrange
	_board.place_unit("soldado_1", Vector2i(9, 11))
	_board.register_unit("soldado_1", {
		"name": "Soldado Isectum",
		"team": "B",
		"hp": 30,
		"max_hp": 30
	})

	var card: CardData = RunCombatBridge.card_id_to_card_data("ataque")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")
	var target_data: Dictionary = _board.get_unit_data("soldado_1")

	# Assert
	assert_eq(card.card_name, "Ataque Tático", "Nome da carta deve ser transparente e claro")
	assert_true(result["targets_hit"].has("soldado_1"), "Inimigo soldado_1 deve ser atingido")
	assert_gt(result["total_damage"], 0, "Dano total deve ser maior que 0")
	assert_lt(int(target_data["hp"]), 30, "HP do inimigo deve ter sido reduzido")

# ── 2. Cartas Avançadas de Combate (Golpe Pesado & Tiro de Balista) ───────────

func test_card_golpe_pesado_deals_high_damage() -> void:
	# Arrange
	_board.place_unit("invasor_forte", Vector2i(9, 11))
	_board.register_unit("invasor_forte", {
		"name": "Invasor Brutal",
		"team": "B",
		"hp": 40,
		"max_hp": 40
	})

	var card: CardData = RunCombatBridge.card_id_to_card_data("golpe_pesado")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")
	var target_data: Dictionary = _board.get_unit_data("invasor_forte")

	# Assert
	assert_gte(result["total_damage"], 14, "Golpe pesado deve causar no mínimo 14 de dano")
	assert_lte(int(target_data["hp"]), 26, "HP do alvo deve refletir o golpe pesado")

func test_card_tiro_balista_hits_enemy_at_distance() -> void:
	# Arrange
	_board.place_unit("vespa_distante", Vector2i(15, 15))
	_board.register_unit("vespa_distante", {
		"name": "Vespa Distante",
		"team": "B",
		"hp": 25,
		"max_hp": 25
	})

	var card: CardData = RunCombatBridge.card_id_to_card_data("tiro_balista")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	assert_true(result["targets_hit"].has("vespa_distante"), "Tiro de balista atinge alvo à distância")
	assert_gte(result["total_damage"], 12, "Tiro de balista causa dano perfurante consistente")

# ── 3. Mecânica Especial: Lâmina Ígnea Causa 2x Dano em Carapaça ─────────────

func test_card_lamina_ignea_doubles_damage_against_carapace() -> void:
	# Arrange
	_board.place_unit("besouro_carapaca", Vector2i(9, 11))
	_board.register_unit("besouro_carapaca", {
		"name": "Besouro Blindado",
		"caste_id": "besouro_casca_dura",
		"team": "B",
		"hp": 50,
		"max_hp": 50
	})

	var card: CardData = RunCombatBridge.card_id_to_card_data("lamina_ignea")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	# Dano base 12-18 duplicado contra carapaça resulta em 24-36 de dano!
	assert_gte(result["total_damage"], 24, "Lâmina Ígnea deve aplicar dano dobrado contra besouro/carapaça")

# ── 4. Carta de Dano em Área: Martelo do Trovão ───────────────────────────────

func test_card_martelo_do_trovao_hits_multiple_targets() -> void:
	# Arrange
	_board.place_unit("inimigo_1", Vector2i(9, 11))
	_board.register_unit("inimigo_1", {"name": "Inimigo 1", "team": "B", "hp": 30})
	_board.place_unit("inimigo_2", Vector2i(10, 11))
	_board.register_unit("inimigo_2", {"name": "Inimigo 2", "team": "B", "hp": 30})

	var card: CardData = RunCombatBridge.card_id_to_card_data("martelo_do_trovao")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	assert_gte(result["targets_hit"].size(), 2, "Martelo do Trovão deve atingir múltiplos alvos")
	assert_true(result["targets_hit"].has("inimigo_1"), "Inimigo 1 foi atingido")
	assert_true(result["targets_hit"].has("inimigo_2"), "Inimigo 2 foi atingido")

# ── 5. Dano Letal: Eliminação e Espólios ─────────────────────────────────────

func test_card_damage_kills_unit_and_drops_loot() -> void:
	# Arrange
	_board.place_unit("fraco", Vector2i(9, 11))
	_board.register_unit("fraco", {
		"name": "Batedor Fragil",
		"team": "B",
		"hp": 4,
		"max_hp": 10
	})

	var card: CardData = RunCombatBridge.card_id_to_card_data("ataque")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	assert_eq(result["enemies_defeated"], 1, "Exatamente 1 inimigo derrotado")
	assert_eq(_controller.enemies_defeated_count, 1, "Contador global de derrotados incrementado")
	assert_false(_board.has_unit("fraco"), "Unidade morta deve ser removida do tabuleiro")
	assert_true(_board.has_item_at(Vector2i(9, 11)), "Espólios de mana/cristal devem cair no chão")

# ── 6. Casos de Borda (Edge Cases) ───────────────────────────────────────────

func test_card_damage_with_no_enemies_safe_fallback() -> void:
	# Arrange - Nenhum inimigo no tabuleiro
	var card: CardData = RunCombatBridge.card_id_to_card_data("ataque")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	assert_eq(result["targets_hit"].size(), 0, "Sem alvos atingidos quando não há inimigos")
	assert_eq(result["total_damage"], 0, "Dano total é 0")

func test_card_damage_with_null_board_safe_fallback() -> void:
	# Arrange
	_controller.board = null
	var card: CardData = RunCombatBridge.card_id_to_card_data("ataque")

	# Act
	var result: Dictionary = _controller._apply_combat_card_damage(card, "")

	# Assert
	assert_eq(result["total_damage"], 0, "Board nulo retorna seguro sem crash")
