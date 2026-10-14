# res://scripts/resources/CardData.gd
class_name CardData
extends Resource

## CardData: Typed Custom Resource representing a card in Cerco da Fortaleza contra Isectum.
## Models tactical action cards, upgrades, runes, and defense cards with badges and resource costs.

# ── Card Types ────────────────────────────────────────────────────────────────
const TYPE_ACAO: String = "ACAO"
const TYPE_UPGRADE: String = "UPGRADE"
const TYPE_RUNA: String = "RUNA"
const TYPE_DEFESA: String = "DEFESA"

# ── Badges (Sincronia Co-op) ──────────────────────────────────────────────────
const BADGE_MARCHA: String = "MARCHA"
const BADGE_TRABALHO: String = "TRABALHO"
const BADGE_ESCAVACAO: String = "ESCAVACAO"
const BADGE_COMBATE: String = "COMBATE"
const BADGE_ESPECIAL: String = "ESPECIAL"

# ── Canonical Exported Fields ─────────────────────────────────────────────────
@export var id: String = ""
@export var card_name: String = ""
@export var card_type: String = TYPE_ACAO       # ACAO, UPGRADE, RUNA, DEFESA
@export var badge: String = BADGE_MARCHA        # MARCHA, TRABALHO, ESCAVACAO, COMBATE, ESPECIAL
@export var description: String = ""

# Resource Costs
@export var cost_wood: int = 0
@export var cost_leather: int = 0
@export var cost_metal: int = 0
@export var cost_crystal: int = 0
@export var cost_ap: int = 0

# Tactical & Target Properties
@export var effect_value: int = 0
@export var target_zone: String = ""

# ── Legacy & Compatibility Fields ─────────────────────────────────────────────
@export var symbol: String = "⚔"
@export var subtype: String = "acao"
@export var cost: Dictionary = {}
@export var effect: String = ""
@export var movement: int = 0
@export var work: int = 0
@export var excavation: int = 0

# ── Property Getters / Setters for Legacy Compatibility ───────────────────────
var name: String:
	get:
		return card_name if not card_name.is_empty() else _legacy_name
	set(val):
		card_name = val
		_legacy_name = val

var _legacy_name: String = ""

var escavacao: int:
	get:
		return excavation
	set(val):
		excavation = val

var movimento: int:
	get:
		return movement
	set(val):
		movement = val

var trabalho: int:
	get:
		return work
	set(val):
		work = val

# ── Utility Methods ───────────────────────────────────────────────────────────

## Returns a normalized dictionary of all non-zero resource costs.
func get_cost_dict() -> Dictionary:
	var result: Dictionary = {}
	if cost_wood > 0:
		result["wood"] = cost_wood
	if cost_leather > 0:
		result["leather"] = cost_leather
	if cost_metal > 0:
		result["metal"] = cost_metal
	if cost_crystal > 0:
		result["crystal"] = cost_crystal
	if cost_ap > 0:
		result["ap"] = cost_ap

	for k in cost:
		var norm_k: String = String(k).to_lower()
		var v: int = int(cost[k])
		if v > 0:
			result[norm_k] = v
	return result

## Verifies if the provided fortress economy has enough resources to play/buy this card.
func can_afford(economy: Variant) -> bool:
	if economy == null:
		return false

	if cost_wood > 0 and economy.get_resource("wood") < cost_wood:
		return false
	if cost_leather > 0 and economy.get_resource("leather") < cost_leather:
		return false
	if cost_metal > 0 and economy.get_resource("metal") < cost_metal:
		return false
	if cost_crystal > 0 and economy.get_resource("crystal") < cost_crystal:
		return false
	if cost_ap > 0 and economy.get_resource("ap") < cost_ap:
		return false

	if not cost.is_empty():
		if not economy.can_afford(cost):
			return false

	return true

## Deep clone of this card resource instance.
func clone() -> CardData:
	var c: CardData = CardData.new()
	c.id = id
	c.card_name = card_name
	c._legacy_name = _legacy_name
	c.card_type = card_type
	c.badge = badge
	c.description = description
	c.cost_wood = cost_wood
	c.cost_leather = cost_leather
	c.cost_metal = cost_metal
	c.cost_crystal = cost_crystal
	c.cost_ap = cost_ap
	c.effect_value = effect_value
	c.target_zone = target_zone
	c.symbol = symbol
	c.subtype = subtype
	c.cost = cost.duplicate(true)
	c.effect = effect
	c.movement = movement
	c.work = work
	c.excavation = excavation
	return c
