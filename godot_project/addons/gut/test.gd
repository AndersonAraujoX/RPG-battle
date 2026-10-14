# res://addons/gut/test.gd
class_name GutTest
extends Node

## Base Test Class for GUT (Godot Unit Test) in Godot 4.
## Provides assertion primitives, lifecycle hooks, and signal monitoring.

class SignalReceiver:
	var target: Object
	var signal_name: String
	var emissions: Array = []

	func _init(t: Object, s: String) -> void:
		target = t
		signal_name = s

	func emit_0() -> void:
		emissions.append([])

	func emit_1(a) -> void:
		emissions.append([a])

	func emit_2(a, b) -> void:
		emissions.append([a, b])

	func emit_3(a, b, c) -> void:
		emissions.append([a, b, c])

	func emit_4(a, b, c, d) -> void:
		emissions.append([a, b, c, d])

	func emit_5(a, b, c, d, e) -> void:
		emissions.append([a, b, c, d, e])

	func emit_6(a, b, c, d, e, f) -> void:
		emissions.append([a, b, c, d, e, f])

var _autofree_nodes: Array[Node] = []
var _signal_receivers: Dictionary = {} # Dictionary[Object, Dictionary[String, SignalReceiver]]
var _current_test_name: String = ""
var _assertion_count: int = 0
var _passed_count: int = 0
var _failed_count: int = 0
var _failure_messages: Array[String] = []

func before_all() -> void:
	pass

func before_each() -> void:
	pass

func after_each() -> void:
	pass

func after_all() -> void:
	pass

# ── Lifecycle Internal Hooks ────────────────────────────────────────────────

func _internal_before_each(test_name: String) -> void:
	_current_test_name = test_name
	_signal_receivers.clear()
	_autofree_nodes.clear()

func _internal_after_each() -> void:
	# Clean up autofreed nodes
	for node in _autofree_nodes:
		if is_instance_valid(node):
			if node.get_parent() != null:
				node.get_parent().remove_child(node)
			node.free()
	_autofree_nodes.clear()

	# Disconnect any remaining signal receivers
	for target in _signal_receivers.keys():
		if is_instance_valid(target):
			var sig_dict: Dictionary = _signal_receivers[target]
			for sig_name in sig_dict.keys():
				var receiver: SignalReceiver = sig_dict[sig_name]
				for method in ["emit_0", "emit_1", "emit_2", "emit_3", "emit_4", "emit_5", "emit_6"]:
					var c: Callable = Callable(receiver, method)
					if target.is_connected(sig_name, c):
						target.disconnect(sig_name, c)
	_signal_receivers.clear()

# ── Node Memory Management ──────────────────────────────────────────────────

func autofree(node: Node) -> Node:
	if node != null and not _autofree_nodes.has(node):
		_autofree_nodes.append(node)
		if not node.is_inside_tree() and is_inside_tree():
			add_child(node)
	return node

func add_child_autofree(node: Node) -> Node:
	add_child(node)
	return autofree(node)

# ── Signal Watching ─────────────────────────────────────────────────────────

func watch_signals(target: Object) -> void:
	if target == null:
		return
	if not _signal_receivers.has(target):
		_signal_receivers[target] = {}

	for sig in target.get_signal_list():
		var sig_name: String = sig["name"]
		if _signal_receivers[target].has(sig_name):
			continue

		var receiver: SignalReceiver = SignalReceiver.new(target, sig_name)
		_signal_receivers[target][sig_name] = receiver

		var arg_count: int = sig["args"].size()
		var callable: Callable
		match arg_count:
			0: callable = Callable(receiver, "emit_0")
			1: callable = Callable(receiver, "emit_1")
			2: callable = Callable(receiver, "emit_2")
			3: callable = Callable(receiver, "emit_3")
			4: callable = Callable(receiver, "emit_4")
			5: callable = Callable(receiver, "emit_5")
			_: callable = Callable(receiver, "emit_6")

		if not target.is_connected(sig_name, callable):
			target.connect(sig_name, callable)

func _get_receiver(target: Object, sig_name: String) -> SignalReceiver:
	if _signal_receivers.has(target) and _signal_receivers[target].has(sig_name):
		return _signal_receivers[target][sig_name]
	return null

func assert_signal_emitted(target: Object, sig_name: String, text: String = "") -> void:
	var receiver: SignalReceiver = _get_receiver(target, sig_name)
	if receiver == null:
		_fail_assertion("Signal '%s' is not being watched on target." % sig_name, text)
		return
	if receiver.emissions.size() > 0:
		_pass_assertion()
	else:
		_fail_assertion("Expected signal '%s' to be emitted, but it was not." % sig_name, text)

func assert_signal_not_emitted(target: Object, sig_name: String, text: String = "") -> void:
	var receiver: SignalReceiver = _get_receiver(target, sig_name)
	if receiver == null or receiver.emissions.size() == 0:
		_pass_assertion()
	else:
		_fail_assertion("Expected signal '%s' NOT to be emitted, but was emitted %d times." % [
			sig_name, receiver.emissions.size()
		], text)

func assert_signal_emit_count(target: Object, sig_name: String, expected_count: int, text: String = "") -> void:
	var receiver: SignalReceiver = _get_receiver(target, sig_name)
	var count: int = receiver.emissions.size() if receiver != null else 0
	if count == expected_count:
		_pass_assertion()
	else:
		_fail_assertion("Expected signal '%s' to be emitted %d times, but was emitted %d times." % [
			sig_name, expected_count, count
		], text)

func assert_signal_emitted_with_parameters(target: Object, sig_name: String, expected_params: Array, text: String = "") -> void:
	var receiver: SignalReceiver = _get_receiver(target, sig_name)
	if receiver == null or receiver.emissions.is_empty():
		_fail_assertion("Signal '%s' was never emitted." % sig_name, text)
		return

	var found: bool = false
	for emission in receiver.emissions:
		if _compare_param_arrays(emission, expected_params):
			found = true
			break

	if found:
		_pass_assertion()
	else:
		_fail_assertion("Signal '%s' emitted, but parameters %s were not matched. Received: %s" % [
			sig_name, str(expected_params), str(receiver.emissions)
		], text)

func _compare_param_arrays(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for i in range(actual.size()):
		var a = actual[i]
		var e = expected[i]
		if typeof(a) != typeof(e):
			# Allow float/int equality
			if (typeof(a) == TYPE_INT or typeof(a) == TYPE_FLOAT) and (typeof(e) == TYPE_INT or typeof(e) == TYPE_FLOAT):
				if not is_equal_approx(float(a), float(e)):
					return false
			else:
				return false
		elif a != e:
			return false
	return true

# ── Assertion Primitives ────────────────────────────────────────────────────

func assert_eq(actual, expected, text: String = "") -> void:
	if actual == expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] == [%s]" % [str(actual), str(expected)], text)

func assert_ne(actual, expected, text: String = "") -> void:
	if actual != expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] != [%s]" % [str(actual), str(expected)], text)

func assert_true(actual, text: String = "") -> void:
	if actual == true:
		_pass_assertion()
	else:
		_fail_assertion("Expected true, got [%s]" % str(actual), text)

func assert_false(actual, text: String = "") -> void:
	if actual == false:
		_pass_assertion()
	else:
		_fail_assertion("Expected false, got [%s]" % str(actual), text)

func assert_null(actual, text: String = "") -> void:
	if actual == null:
		_pass_assertion()
	else:
		_fail_assertion("Expected null, got [%s]" % str(actual), text)

func assert_not_null(actual, text: String = "") -> void:
	if actual != null:
		_pass_assertion()
	else:
		_fail_assertion("Expected not null, got null", text)

func assert_gt(actual, expected, text: String = "") -> void:
	if actual > expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] > [%s]" % [str(actual), str(expected)], text)

func assert_gte(actual, expected, text: String = "") -> void:
	if actual >= expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] >= [%s]" % [str(actual), str(expected)], text)

func assert_lt(actual, expected, text: String = "") -> void:
	if actual < expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] < [%s]" % [str(actual), str(expected)], text)

func assert_lte(actual, expected, text: String = "") -> void:
	if actual <= expected:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] <= [%s]" % [str(actual), str(expected)], text)

func assert_between(actual, min_val, max_val, text: String = "") -> void:
	if actual >= min_val and actual <= max_val:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] between [%s, %s]" % [str(actual), str(min_val), str(max_val)], text)

func assert_almost_eq(actual: float, expected: float, error_interval: float, text: String = "") -> void:
	if abs(actual - expected) <= error_interval:
		_pass_assertion()
	else:
		_fail_assertion("Expected [%s] almost eq [%s] (±%s)" % [str(actual), str(expected), str(error_interval)], text)

func assert_has(collection, element, text: String = "") -> void:
	var has_item: bool = false
	if collection is Array or collection is PackedStringArray or collection is PackedInt32Array:
		has_item = collection.has(element)
	elif collection is Dictionary:
		has_item = collection.has(element)
	elif collection is String:
		has_item = collection.contains(str(element))

	if has_item:
		_pass_assertion()
	else:
		_fail_assertion("Expected collection to contain [%s]" % str(element), text)

func assert_does_not_have(collection, element, text: String = "") -> void:
	var has_item: bool = false
	if collection is Array or collection is PackedStringArray or collection is PackedInt32Array:
		has_item = collection.has(element)
	elif collection is Dictionary:
		has_item = collection.has(element)
	elif collection is String:
		has_item = collection.contains(str(element))

	if not has_item:
		_pass_assertion()
	else:
		_fail_assertion("Expected collection to NOT contain [%s]" % str(element), text)


func pass_test(text: String = "") -> void:
	_pass_assertion()

func fail_test(text: String = "") -> void:
	_fail_assertion("Explicit fail_test called.", text)

func _pass_assertion() -> void:
	_assertion_count += 1
	_passed_count += 1

func _fail_assertion(details: String, custom_text: String) -> void:
	_assertion_count += 1
	_failed_count += 1
	var msg: String = "  FAILED: %s - %s" % [_current_test_name, details]
	if not custom_text.is_empty():
		msg += " ('%s')" % custom_text
	_failure_messages.append(msg)
	push_error(msg)
