extends SceneTree

class MockRunState extends RunState:
	var card_purges_count: int = 0
	
	func to_dict() -> Dictionary:
		var d = super.to_dict()
		d["card_purges_count"] = card_purges_count
		return d
		
	func from_dict(data: Dictionary) -> bool:
		var ok = super.from_dict(data)
		if ok:
			card_purges_count = int(data.get("card_purges_count", 0))
		return ok

func _init() -> void:
	print("--- TEST FORGESCREEN MULTI-VISIT PURGE ESCALATION ---")
	var s = MockRunState.new()
	s.start_run({"aquele": 30}, ["c1", "c2", "c3", "c4", "c5", "c6", "c7"], 123)
	s.gold = 500
	
	# Forge visit 1
	var forge1 = ForgeScreen.new()
	forge1.setup(s, null, null)
	print("forge1 initial purge cost: ", forge1.get_current_purge_cost()) # Expected 50
	var ok1 = forge1.purge_card("c7")
	print("forge1 purge ok: ", ok1)
	print("s.card_purges_count after forge1: ", s.card_purges_count) # Expected 1
	forge1.close_forge()
	
	# Forge visit 2 (new ForgeScreen instance with same state)
	var forge2 = ForgeScreen.new()
	forge2.setup(s, null, null)
	print("forge2 initial purge cost: ", forge2.get_current_purge_cost()) # Expected 75
	var ok2 = forge2.purge_card("c6")
	print("forge2 purge ok: ", ok2)
	print("s.card_purges_count after forge2: ", s.card_purges_count) # Expected 2
	forge2.close_forge()
	
	# Forge visit 3
	var forge3 = ForgeScreen.new()
	forge3.setup(s, null, null)
	print("forge3 initial purge cost: ", forge3.get_current_purge_cost()) # Expected 100
	
	# Test roundtrip serialization
	var dict = s.to_dict()
	var restored = MockRunState.new()
	restored.from_dict(dict)
	print("restored.card_purges_count: ", restored.card_purges_count) # Expected 2
	
	var forge_restored = ForgeScreen.new()
	forge_restored.setup(restored, null, null)
	print("forge_restored purge cost: ", forge_restored.get_current_purge_cost()) # Expected 100
	
	quit(0)
