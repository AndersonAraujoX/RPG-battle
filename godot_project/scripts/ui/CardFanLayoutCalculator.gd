# res://scripts/ui/CardFanLayoutCalculator.gd
class_name CardFanLayoutCalculator
extends RefCounted

## Pure mathematical calculator for fan-shaped card hand layout.
## Decoupled from UI/Control nodes for 100% headless testability with zero leaks.

# ── Configuration Constants & Defaults ───────────────────────────────────────
var card_size: Vector2 = Vector2(96.0, 130.0)
var max_arc_spread_deg: float = 24.0
var max_step_angle_deg: float = 4.0
var hover_lift_px: float = 30.0
var selected_lift_px: float = 45.0
var arc_curvature_factor: float = 1.6
var max_spread_width: float = 650.0
var base_y: float = 10.0

## Calculates layout transforms for all N cards in hand within the specified container dimensions.
## Returns an Array of Dictionaries with keys: "position", "rotation_deg", "rotation_rad", "scale", "z_index".
func calculate_fan_transforms(card_count: int, container_width: float, container_height: float = 0.0) -> Array[Dictionary]:
	var transforms: Array[Dictionary] = []
	if card_count <= 0:
		return transforms
	
	for i in range(card_count):
		var trans: Dictionary = get_card_transform(i, card_count, container_width, container_height, false, false)
		transforms.append(trans)
	
	return transforms

## Calculates the transform for a single card at the given index in a hand of card_count.
func get_card_transform(index: int, card_count: int, container_width: float, _container_height: float = 0.0, is_hovered: bool = false, is_selected: bool = false) -> Dictionary:
	if card_count <= 0 or index < 0 or index >= card_count:
		return {
			"position": Vector2.ZERO,
			"rotation_deg": 0.0,
			"rotation_rad": 0.0,
			"scale": Vector2.ONE,
			"z_index": 0
		}
	
	var w: float = maxf(container_width, card_size.x)
	var mid_idx: float = float(card_count - 1) / 2.0
	var offset_center: float = float(index) - mid_idx
	
	# Horizontal step and distribution
	var pos_x: float = 0.0
	if card_count == 1:
		pos_x = (w - card_size.x) / 2.0
	else:
		var available_w: float = minf(w - card_size.x, max_spread_width)
		var step_x: float = available_w / float(card_count - 1)
		# Clamp step_x so cards don't spread excessively wide if hand is small
		step_x = minf(step_x, card_size.x + 8.0)
		var total_span: float = float(card_count - 1) * step_x + card_size.x
		var start_x: float = (w - total_span) / 2.0
		pos_x = start_x + float(index) * step_x
	
	# Vertical arc (parabolic curvature approximating circular arc)
	var fan_arc_y: float = (offset_center * offset_center) * arc_curvature_factor
	var pos_y: float = base_y + fan_arc_y
	
	# Rotation angle
	var rot_deg: float = 0.0
	if card_count > 1:
		var step_angle: float = minf(max_step_angle_deg, max_arc_spread_deg / float(card_count - 1))
		rot_deg = clampf(offset_center * step_angle, -max_arc_spread_deg / 2.0, max_arc_spread_deg / 2.0)
	
	var transform_data: Dictionary = {
		"position": Vector2(pos_x, pos_y),
		"rotation_deg": rot_deg,
		"rotation_rad": deg_to_rad(rot_deg),
		"scale": Vector2.ONE,
		"z_index": index
	}
	
	if is_selected:
		return calculate_selection_transform(transform_data)
	elif is_hovered:
		return calculate_hover_transform(transform_data)
	
	return transform_data

## Transforms a resting card dictionary into its hovered state:
## lifts by hover_lift_px, straightens to 0 degrees, slightly scales up, and brings forward.
func calculate_hover_transform(base_transform: Dictionary) -> Dictionary:
	var trans: Dictionary = base_transform.duplicate(true)
	var pos: Vector2 = trans.get("position", Vector2.ZERO)
	pos.y -= hover_lift_px
	trans["position"] = pos
	trans["rotation_deg"] = 0.0
	trans["rotation_rad"] = 0.0
	trans["scale"] = Vector2(1.08, 1.08)
	trans["z_index"] = 20
	return trans

## Transforms a resting card dictionary into its selected state:
## lifts by selected_lift_px, straightens to 0 degrees, scales up, and brings to top.
func calculate_selection_transform(base_transform: Dictionary) -> Dictionary:
	var trans: Dictionary = base_transform.duplicate(true)
	var pos: Vector2 = trans.get("position", Vector2.ZERO)
	pos.y -= selected_lift_px
	trans["position"] = pos
	trans["rotation_deg"] = 0.0
	trans["rotation_rad"] = 0.0
	trans["scale"] = Vector2(1.10, 1.10)
	trans["z_index"] = 25
	return trans
