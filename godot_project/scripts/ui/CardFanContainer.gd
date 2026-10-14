# res://scripts/ui/CardFanContainer.gd
class_name CardFanContainer
extends Control

## Container Control holding multiple CardUI instances in an interactive fan arc.
## Manages card additions, removals, selections, hover effects, and uses CardFanLayoutCalculator.

signal card_selected(card: CardData, index: int)
signal card_deselected(card: CardData, index: int)
signal card_played_requested(card_data: CardData, target_zone: String)
signal card_hovered(card: CardData, index: int)
signal card_unhovered(card: CardData, index: int)

# ── References & State ───────────────────────────────────────────────────────
var calculator: CardFanLayoutCalculator = null
var cards: Array[CardData] = []
var card_nodes: Array[CardUI] = []
var selected_index: int = -1
var hovered_index: int = -1

func _init() -> void:
	calculator = CardFanLayoutCalculator.new()
	custom_minimum_size = Vector2(400.0, 160.0)
	mouse_filter = MOUSE_FILTER_IGNORE

func _ready() -> void:
	resized.connect(_on_resized)
	recalculate_layout()

func _on_resized() -> void:
	recalculate_layout()

## Sets the entire hand of cards and rebuilds CardUI instances
func set_hand(new_cards: Array) -> void:
	clear_hand()
	for item in new_cards:
		if item is CardData:
			add_card(item)

## Adds a single card to hand and recalculates layout
func add_card(card: CardData) -> CardUI:
	if card == null:
		return null
	
	var idx: int = cards.size()
	cards.append(card)
	
	var card_ui: CardUI = CardUI.new()
	card_ui.setup(card, idx)
	add_child(card_ui)
	card_nodes.append(card_ui)
	
	# Connect signals
	card_ui.card_selected.connect(_on_card_selected)
	card_ui.card_deselected.connect(_on_card_deselected)
	card_ui.card_hovered.connect(_on_card_hovered)
	card_ui.card_unhovered.connect(_on_card_unhovered)
	card_ui.card_played_requested.connect(_on_card_played_requested)
	
	recalculate_layout()
	return card_ui

## Removes a card by index and returns its CardData
func remove_card(index: int) -> CardData:
	if index < 0 or index >= cards.size():
		return null
	
	var removed_card: CardData = cards[index]
	cards.remove_at(index)
	
	var card_ui: CardUI = card_nodes[index]
	card_nodes.remove_at(index)
	
	if is_instance_valid(card_ui):
		card_ui.card_selected.disconnect(_on_card_selected)
		card_ui.card_deselected.disconnect(_on_card_deselected)
		card_ui.card_hovered.disconnect(_on_card_hovered)
		card_ui.card_unhovered.disconnect(_on_card_unhovered)
		card_ui.card_played_requested.disconnect(_on_card_played_requested)
		card_ui.queue_free()
	
	# Update indices on remaining card nodes
	for i in range(card_nodes.size()):
		card_nodes[i].card_index = i
	
	if selected_index == index:
		selected_index = -1
	elif selected_index > index:
		selected_index -= 1
	
	if hovered_index == index:
		hovered_index = -1
	elif hovered_index > index:
		hovered_index -= 1
	
	recalculate_layout()
	return removed_card

## Removes a card by its ID string
func remove_card_by_id(card_id: String) -> CardData:
	for i in range(cards.size()):
		if cards[i].id == card_id:
			return remove_card(i)
	return null

## Removes a card by CardData reference
func remove_card_by_data(card: CardData) -> CardData:
	if card == null:
		return null
	return remove_card_by_id(card.id)

## Returns the CardData of the currently selected card (or null)
func get_selected_card() -> CardData:
	if selected_index >= 0 and selected_index < cards.size():
		return cards[selected_index]
	return null

## Returns the CardUI node of the currently selected card (or null)
func get_selected_ui() -> CardUI:
	if selected_index >= 0 and selected_index < card_nodes.size():
		return card_nodes[selected_index]
	return null

## Plays the currently selected card (if any) and requests emission
func play_selected_card(target_zone: String = "") -> CardData:
	if selected_index < 0 or selected_index >= card_nodes.size():
		return null
	var card_ui: CardUI = card_nodes[selected_index]
	var data: CardData = cards[selected_index]
	card_ui.request_play(target_zone)
	return data

## Plays a card from hand at specific index
func play_card_at(index: int, target_zone: String = "") -> CardData:
	if index < 0 or index >= card_nodes.size():
		return null
	var card_ui: CardUI = card_nodes[index]
	var data: CardData = cards[index]
	card_ui.request_play(target_zone)
	return data

## Plays the first card in hand that matches the given badge
func play_card_by_badge(badge_name: String, target_zone: String = "") -> CardData:
	var norm: String = badge_name.strip_edges().to_upper()
	for i in range(cards.size()):
		if cards[i].badge.strip_edges().to_upper() == norm:
			var card_ui: CardUI = card_nodes[i]
			var data: CardData = cards[i]
			card_ui.request_play(target_zone)
			return data
	return null

## Selects card at index, enforcing mutual exclusion
func select_card(index: int) -> void:
	if index < 0 or index >= card_nodes.size():
		deselect_card()
		return
	
	if selected_index == index:
		return
	
	# Deselect previous
	if selected_index >= 0 and selected_index < card_nodes.size():
		card_nodes[selected_index].set_selected(false)
	
	selected_index = index
	card_nodes[index].set_selected(true)
	recalculate_layout()

## Deselects any currently selected card
func deselect_card() -> void:
	if selected_index >= 0 and selected_index < card_nodes.size():
		var old_idx: int = selected_index
		selected_index = -1
		card_nodes[old_idx].set_selected(false)
		recalculate_layout()
	else:
		selected_index = -1

## Returns CardUI node at index
func get_card_ui(index: int) -> CardUI:
	if index >= 0 and index < card_nodes.size():
		return card_nodes[index]
	return null

## Returns current number of cards
func get_card_count() -> int:
	return card_nodes.size()

## Clears all cards from container
func clear_hand() -> void:
	for ui in card_nodes:
		if is_instance_valid(ui):
			ui.queue_free()
	card_nodes.clear()
	cards.clear()
	selected_index = -1
	hovered_index = -1

## Recalculates positioning, rotation, scale, and z-index for all child cards
func recalculate_layout() -> void:
	if calculator == null:
		calculator = CardFanLayoutCalculator.new()
	
	var count: int = card_nodes.size()
	var w: float = size.x if size.x > 0 else 800.0
	var h: float = size.y if size.y > 0 else 160.0
	
	for i in range(count):
		var card_ui: CardUI = card_nodes[i]
		if not is_instance_valid(card_ui):
			continue
		
		var is_hov: bool = (i == hovered_index)
		var is_sel: bool = (i == selected_index)
		var trans: Dictionary = calculator.get_card_transform(i, count, w, h, is_hov, is_sel)
		
		card_ui.position = trans.get("position", Vector2.ZERO)
		card_ui.rotation = trans.get("rotation_rad", 0.0)
		card_ui.scale = trans.get("scale", Vector2.ONE)
		card_ui.z_index = trans.get("z_index", i)

# ── Signal Relaying ──────────────────────────────────────────────────────────
func _on_card_selected(card: CardData, index: int) -> void:
	# Enforce single selection
	if selected_index != index:
		if selected_index >= 0 and selected_index < card_nodes.size():
			card_nodes[selected_index].set_selected(false)
		selected_index = index
	card_selected.emit(card, index)
	recalculate_layout()

func _on_card_deselected(card: CardData, index: int) -> void:
	if selected_index == index:
		selected_index = -1
	card_deselected.emit(card, index)
	recalculate_layout()

func _on_card_hovered(card: CardData, index: int) -> void:
	hovered_index = index
	card_hovered.emit(card, index)
	recalculate_layout()

func _on_card_unhovered(card: CardData, index: int) -> void:
	if hovered_index == index:
		hovered_index = -1
	card_unhovered.emit(card, index)
	recalculate_layout()

func _on_card_played_requested(card_data: CardData, target_zone: String) -> void:
	card_played_requested.emit(card_data, target_zone)

## Explicit cleanup to avoid any cyclic references or leaks
func cleanup() -> void:
	clear_hand()
	calculator = null
