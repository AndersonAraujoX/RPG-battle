# res://scripts/cerco/CercoDeck.gd
class_name CercoDeck
extends RefCounted

## CercoDeck: Manages player deck piles (draw pile, hand, discard pile),
## drawing mechanics with automatic reshuffle, card play, and the Upgrade Market
## for Cerco da Fortaleza contra Isectum.

# ── Signals ──────────────────────────────────────────────────────────────────
signal card_drawn(card: CardData)
signal card_played(card: CardData)
signal card_discarded(card: CardData)
signal deck_reshuffled(discard_count: int)
signal card_bought(card: CardData, cost: Dictionary)
signal market_refreshed(count: int)

# ── Properties ───────────────────────────────────────────────────────────────
var draw_pile: Array[CardData] = []
var hand: Array[CardData] = []
var discard_pile: Array[CardData] = []
var market_cards: Array[CardData] = []
var max_hand_size: int = 5

# ── Initialization ───────────────────────────────────────────────────────────
func _init(auto_build_starter: bool = false, auto_populate_market: bool = false) -> void:
	if auto_build_starter:
		build_starter_deck()
	if auto_populate_market:
		populate_default_market()

func clear() -> void:
	draw_pile.clear()
	hand.clear()
	discard_pile.clear()
	market_cards.clear()

# ── Starter Deck Builder ─────────────────────────────────────────────────────

## Builds the canonical 10-card starter deck:
## 4x Marcha, 3x Trabalho, 2x Escavação, 1x Combate/Força.
func build_starter_deck() -> Array[CardData]:
	draw_pile.clear()
	var new_cards: Array[CardData] = []

	# 1. Marcha (Movement)
	for i in range(1, 5):
		var c: CardData = CardData.new()
		c.id = "marcha_%d" % i
		c.card_name = "Marcha"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_MARCHA
		c.movement = 15
		c.effect_value = 15
		c.description = "+15 Movimento"
		new_cards.append(c)

	# 2. Trabalho (Work)
	for i in range(1, 4):
		var c: CardData = CardData.new()
		c.id = "trabalho_%d" % i
		c.card_name = "Trabalho"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_TRABALHO
		c.work = 3
		c.effect_value = 3
		c.description = "+3 Trabalho"
		new_cards.append(c)

	# 3. Escavação (Excavation)
	for i in range(1, 3):
		var c: CardData = CardData.new()
		c.id = "escavacao_%d" % i
		c.card_name = "Escavação"
		c.card_type = CardData.TYPE_ACAO
		c.badge = CardData.BADGE_ESCAVACAO
		c.excavation = 4
		c.effect_value = 4
		c.description = "+4 Escavação"
		new_cards.append(c)

	# 4. Combate / Força Anã
	var c_comb: CardData = CardData.new()
	c_comb.id = "forca_ana_1"
	c_comb.card_name = "Força Anã"
	c_comb.card_type = CardData.TYPE_ACAO
	c_comb.badge = CardData.BADGE_COMBATE
	c_comb.work = 4
	c_comb.movement = 15
	c_comb.effect_value = 4
	c_comb.description = "+15 Mov +4 Trab / Combate"
	new_cards.append(c_comb)

	draw_pile.append_array(new_cards)
	return new_cards

# ── Deck & Hand Operations ───────────────────────────────────────────────────

## Draws up to `count` cards from draw_pile into hand.
## If draw_pile becomes empty, automatically reshuffles discard_pile into draw_pile.
func draw_cards(count: int) -> Array[CardData]:
	var drawn: Array[CardData] = []
	for i in range(count):
		if draw_pile.is_empty():
			if discard_pile.is_empty():
				break
			reshuffle_discard_into_draw()

		if not draw_pile.is_empty():
			var card: CardData = draw_pile.pop_back()
			hand.append(card)
			drawn.append(card)
			card_drawn.emit(card)
	return drawn

## Plays a card from hand by ID, moving it to discard_pile and emitting card_played.
func play_card(card_id: String) -> CardData:
	for i in range(hand.size()):
		if hand[i].id == card_id:
			var card: CardData = hand[i]
			hand.remove_at(i)
			discard_pile.append(card)
			card_played.emit(card)
			return card
	return null

## Plays a card from hand by index.
func play_card_by_index(index: int) -> CardData:
	if index < 0 or index >= hand.size():
		return null
	var card: CardData = hand[index]
	hand.remove_at(index)
	discard_pile.append(card)
	card_played.emit(card)
	return card

func get_hand() -> Array[CardData]:
	return hand

func get_draw_pile() -> Array[CardData]:
	return draw_pile

func get_discard_pile() -> Array[CardData]:
	return discard_pile

func get_market_cards() -> Array[CardData]:
	return market_cards

func get_card_by_id(card_id: String) -> CardData:
	for c in hand:
		if c.id == card_id:
			return c
	return null

func get_first_card_by_badge(badge_name: String) -> CardData:
	var norm: String = badge_name.strip_edges().to_upper()
	for c in hand:
		if c.badge.strip_edges().to_upper() == norm:
			return c
	return null

## Discards a card from hand to discard_pile without playing its effect.
func discard_card(card_id: String) -> bool:
	for i in range(hand.size()):
		if hand[i].id == card_id:
			var card: CardData = hand[i]
			hand.remove_at(i)
			discard_pile.append(card)
			card_discarded.emit(card)
			return true
	return false

## Reshuffles all cards from discard_pile into draw_pile.
func reshuffle_discard_into_draw() -> void:
	if discard_pile.is_empty():
		return
	var count: int = discard_pile.size()
	draw_pile.append_array(discard_pile)
	discard_pile.clear()
	draw_pile.shuffle()
	deck_reshuffled.emit(count)

# ── Upgrade Market Operations ────────────────────────────────────────────────

## Populates the Upgrade Market with standard upgrade cards.
func populate_default_market() -> Array[CardData]:
	market_cards.clear()
	var list: Array[CardData] = []

	# 1. Plano Tático (Work / Strategy)
	var c1: CardData = CardData.new()
	c1.id = "plano_tatico"
	c1.card_name = "Plano Tático"
	c1.card_type = CardData.TYPE_UPGRADE
	c1.badge = CardData.BADGE_TRABALHO
	c1.cost_leather = 2
	c1.cost_wood = 1
	c1.work = 4
	c1.effect_value = 4
	c1.description = "+4 Trabalho, +1 Carta Mão/Turno"
	list.append(c1)

	# 2. Mestre Artesão (High Work)
	var c2: CardData = CardData.new()
	c2.id = "mestre_artesao"
	c2.card_name = "Mestre Artesão"
	c2.card_type = CardData.TYPE_UPGRADE
	c2.badge = CardData.BADGE_TRABALHO
	c2.cost_wood = 2
	c2.work = 5
	c2.effect_value = 5
	c2.description = "+5 Trabalho, compra 1 carta"
	list.append(c2)

	# 3. Corrida Livre (High Movement)
	var c3: CardData = CardData.new()
	c3.id = "corrida_livre"
	c3.card_name = "Corrida Livre"
	c3.card_type = CardData.TYPE_UPGRADE
	c3.badge = CardData.BADGE_MARCHA
	c3.cost_leather = 2
	c3.movement = 30
	c3.effect_value = 30
	c3.description = "+30 Movimento"
	list.append(c3)

	# 4. Perfurador (Excavation)
	var c4: CardData = CardData.new()
	c4.id = "perfurador"
	c4.card_name = "Perfurador"
	c4.card_type = CardData.TYPE_UPGRADE
	c4.badge = CardData.BADGE_ESCAVACAO
	c4.cost_metal = 2
	c4.excavation = 5
	c4.effect_value = 5
	c4.description = "+5 Escavação"
	list.append(c4)

	# 5. Grande Forjador (Heavy Work & Metal)
	var c5: CardData = CardData.new()
	c5.id = "grande_forjador"
	c5.card_name = "Grande Forjador"
	c5.card_type = CardData.TYPE_UPGRADE
	c5.badge = CardData.BADGE_COMBATE
	c5.cost_wood = 2
	c5.cost_metal = 1
	c5.work = 6
	c5.movement = 15
	c5.effect_value = 6
	c5.description = "+15 Mov +6 Trab"
	list.append(c5)

	# 6. Perfuratriz Real (Deep Mining)
	var c6: CardData = CardData.new()
	c6.id = "perfuratriz_real"
	c6.card_name = "Perfuratriz Real"
	c6.card_type = CardData.TYPE_UPGRADE
	c6.badge = CardData.BADGE_ESCAVACAO
	c6.cost_metal = 3
	c6.cost_leather = 1
	c6.excavation = 10
	c6.effect_value = 10
	c6.description = "+10 Escavação"
	list.append(c6)

	market_cards.append_array(list)
	market_refreshed.emit(market_cards.size())
	return list

## Adds a custom card directly into the market pool.
func add_card_to_market(card: CardData) -> void:
	if card != null and not market_cards.has(card):
		market_cards.append(card)
		market_refreshed.emit(market_cards.size())

## Buys a card from the upgrade market using the fortress economy.
## Deducts resources, places the bought card into discard_pile, and returns it.
func buy_card_from_market(card_id: String, economy: WorkshopEconomy) -> CardData:
	if economy == null:
		return null

	var card_idx: int = -1
	for i in range(market_cards.size()):
		if market_cards[i].id == card_id:
			card_idx = i
			break

	if card_idx == -1:
		return null

	var card: CardData = market_cards[card_idx]
	if not card.can_afford(economy):
		return null

	# Deduct costs
	var costs: Dictionary = card.get_cost_dict()
	var success: bool = economy.spend_costs(costs)
	if not success:
		return null

	market_cards.remove_at(card_idx)
	discard_pile.append(card)
	card_bought.emit(card, costs)
	return card

# ── Inspection Helpers ───────────────────────────────────────────────────────

func get_hand_size() -> int:
	return hand.size()

func get_draw_pile_size() -> int:
	return draw_pile.size()

func get_discard_pile_size() -> int:
	return discard_pile.size()

func get_market_size() -> int:
	return market_cards.size()

func get_total_deck_size() -> int:
	return draw_pile.size() + hand.size() + discard_pile.size()
