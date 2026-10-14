# res://scripts/main/CercoGameController.gd
class_name CercoGameController
extends Node2D

## Main Game Scene Controller for Cerco da Fortaleza contra Isectum.
## Initializes game subsystems (Board, Economy, Deck, Judge, Threat) and connects them to the HUD.

const HUD_SCENE: PackedScene = preload("res://scenes/ui/HUD.tscn")
const GAME_OVER_MODAL_SCENE: PackedScene = preload("res://scenes/ui/GameOverModal.tscn")
const GameOverModalScript = preload("res://scripts/ui/GameOverModal.gd")

var board: FortressBoard = null
var economy: WorkshopEconomy = null
var deck: CercoDeck = null
var judge: CercoCombatJudge = null
var sync_round: CercoSyncRound = null
var threat_deck: ThreatDeck = null

var hud_instance: HUD = null
var current_round: int = 1
var max_rounds: int = 10
var is_game_over: bool = false
var enemies_defeated_count: int = 0
var game_over_modal_instance: Control = null

func _ready() -> void:
	_initialize_models()
	_setup_hud()
	_start_first_wave()
	_start_bgm()

func _initialize_models() -> void:
	board = FortressBoard.new()
	if not board.wall_breached.is_connected(_on_wall_breached_event):
		board.wall_breached.connect(_on_wall_breached_event)
	
	# Espalha cristais de mana, baús, poções e materiais pelo mapa da fortaleza
	board.spawn_default_map_items()

	# Inicializa heróis canônicos no pátio e câmara central com espaçamento amplo
	board.place_unit("aquele", Vector2i(9, 10))
	board.register_unit("aquele", {
		"name": "Aquele", "class": "Guerreiro", "team": "A",
		"hp": 48, "max_hp": 48, "ac": 17, "move_range": 4,
		"attack_range": 1, "attack_bonus": 4
	})

	board.place_unit("stark", Vector2i(10, 9))
	board.register_unit("stark", {
		"name": "Stark", "class": "Paladino", "team": "A",
		"hp": 52, "max_hp": 52, "ac": 18, "move_range": 3,
		"attack_range": 1, "attack_bonus": 3
	})

	board.place_unit("lysander", Vector2i(10, 11))
	board.register_unit("lysander", {
		"name": "Pr. Lysander", "class": "Comandante", "team": "A",
		"hp": 36, "max_hp": 36, "ac": 14, "move_range": 3,
		"attack_range": 2, "attack_bonus": 5
	})

	economy = WorkshopEconomy.new()
	economy.set_resources(15, 12, 10, 5, 4) # Madeira, Couro, Metal, Cristal, PA iniciais
	
	deck = CercoDeck.new()
	deck.build_starter_deck()
	deck.populate_default_market()
	deck.draw_cards(5)
	
	judge = CercoCombatJudge.new()
	sync_round = CercoSyncRound.new()
	threat_deck = ThreatDeck.new()

	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		if gm.has_meta("cerco_config"):
			var cfg: Dictionary = gm.get_meta("cerco_config")
			var diff: Dictionary = cfg.get("dificuldade", {})
			var diff_id: String = str(diff.get("id", "media")).to_lower()
			match diff_id:
				"facil":
					max_rounds = 6
				"dificil":
					max_rounds = 15
				_:
					max_rounds = 10

func _setup_hud() -> void:
	# Procura por HUD existente ou instancia o HUD completo
	hud_instance = find_child("HUD", true, false) as HUD
	if hud_instance == null:
		hud_instance = HUD_SCENE.instantiate() as HUD
		add_child(hud_instance)
	
	# Faz a amarração hermética de todos os modelos ao HUD
	hud_instance.bind_board(board)
	hud_instance.bind_economy(economy)
	hud_instance.bind_deck(deck)
	hud_instance.bind_judge(judge)
	hud_instance.bind_sync_round(sync_round)
	
	# Conecta sinais do HUD
	if not hud_instance.card_played.is_connected(_on_hud_card_played):
		hud_instance.card_played.connect(_on_hud_card_played)
	if not hud_instance.sync_round_requested.is_connected(_on_hud_sync_round_requested):
		hud_instance.sync_round_requested.connect(_on_hud_sync_round_requested)
	if hud_instance.market_panel != null and not hud_instance.market_panel.upgrade_purchased.is_connected(_on_market_upgrade_purchased):
		hud_instance.market_panel.upgrade_purchased.connect(_on_market_upgrade_purchased)
	
	# Conecta sinais táticos de Final Fantasy Tactics da visão do tabuleiro
	if hud_instance.board_view != null:
		if not hud_instance.board_view.unit_selected.is_connected(_on_board_view_unit_selected):
			hud_instance.board_view.unit_selected.connect(_on_board_view_unit_selected)
		if not hud_instance.board_view.unit_moved_to_cell.is_connected(_on_board_view_unit_moved):
			hud_instance.board_view.unit_moved_to_cell.connect(_on_board_view_unit_moved)
		if not hud_instance.board_view.item_pickup_requested.is_connected(_on_board_view_item_pickup):
			hud_instance.board_view.item_pickup_requested.connect(_on_board_view_item_pickup)
		if not hud_instance.board_view.unit_attack_requested.is_connected(_on_board_view_unit_attack):
			hud_instance.board_view.unit_attack_requested.connect(_on_board_view_unit_attack)

		# Seleciona o primeiro herói inicialmente no estilo FFT
		hud_instance.board_view.select_unit("aquele")
		hud_instance.update_active_hero(board.get_unit_data("aquele"))

	# Log inicial explicativo no HUD
	if hud_instance.combat_log != null:
		hud_instance.combat_log.append_entry("CERCO INICIADO", "⚔️ A Fortaleza de Kuar-Tor está sob ataque do Enxame Isectum!")
		hud_instance.combat_log.append_entry("TÁTICA FFT", "🎯 Clique em um herói para ver seu alcance azul (PM) e vermelho (ATK)!")
		hud_instance.combat_log.append_entry("ITENS NO MAPA", "💎 Ande sobre Cristais, Baús e Poções para coletá-los automaticamente.")

func _on_board_view_unit_selected(_unit_id: String, unit_data: Dictionary) -> void:
	if hud_instance != null:
		hud_instance.update_active_hero(unit_data)
		if hud_instance.combat_log != null:
			var uname: String = str(unit_data.get("name", _unit_id))
			var pm: int = int(unit_data.get("move_range", 3))
			var hp: int = int(unit_data.get("hp", 10))
			var max_hp: int = int(unit_data.get("max_hp", 10))
			hud_instance.combat_log.append_entry("SELEÇÃO", "🎯 %s selecionado! (PM: %d, HP: %d/%d)" % [uname, pm, hp, max_hp])

func _on_board_view_unit_moved(unit_id: String, to_pos: Vector2i) -> void:
	if hud_instance != null and hud_instance.board_view != null:
		var wpos: Vector2 = hud_instance.board_view.get_cell_screen_coords(to_pos.x, to_pos.y)
		hud_instance.board_view.spawn_impact_particles(wpos, "dust", 4)
	if hud_instance != null and hud_instance.combat_log != null:
		var udata: Dictionary = board.get_unit_data(unit_id) if board != null else {}
		var uname: String = str(udata.get("name", unit_id))
		hud_instance.combat_log.append_entry("MOVIMENTO", "🚶 %s avançou para (%d, %d)." % [uname, to_pos.x, to_pos.y])

func _on_board_view_item_pickup(unit_id: String, _pos: Vector2i, item_data: Dictionary) -> void:
	var itype: String = str(item_data.get("type", "CRISTAL")).to_upper()
	var iname: String = str(item_data.get("name", "Item"))
	var udata: Dictionary = board.get_unit_data(unit_id) if board != null else {}
	var uname: String = str(udata.get("name", unit_id))

	match itype:
		"CRISTAL":
			var amt: int = int(item_data.get("amount", item_data.get("crystal", 1)))
			if economy != null:
				economy.add_resource("crystal", amt)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "💎 %s coletou %s (+%d Cristal)!" % [uname, iname, amt])

		"GOLD", "OURO":
			var g_amt: int = int(item_data.get("gold", item_data.get("crystal", item_data.get("amount", 10))))
			if economy != null:
				economy.add_resource("crystal", g_amt)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "🪙 %s recolheu %s (+%d Ouro)!" % [uname, iname, g_amt])

		"LEATHER", "COURO":
			var l_amt: int = int(item_data.get("leather", item_data.get("amount", 10)))
			if economy != null:
				economy.add_resource("leather", l_amt)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "👞 %s recolheu %s (+%d Couro)!" % [uname, iname, l_amt])

		"CHEST", "BAU":
			var w: int = int(item_data.get("wood", 6))
			var l: int = int(item_data.get("leather", 4))
			var m: int = int(item_data.get("metal", 3))
			var c: int = int(item_data.get("crystal", item_data.get("gold", 0)))
			if economy != null:
				if w > 0: economy.add_resource("wood", w)
				if l > 0: economy.add_resource("leather", l)
				if m > 0: economy.add_resource("metal", m)
				if c > 0: economy.add_resource("crystal", c)
			if hud_instance != null and hud_instance.combat_log != null:
				var c_str: String = ", +%d Ouro" % c if c > 0 else ""
				hud_instance.combat_log.append_entry("ITEM", "📦 %s abriu %s (+%d Mad, +%d Cou, +%d Met%s)!" % [uname, iname, w, l, m, c_str])

		"POTION":
			var heal_amt: int = int(item_data.get("heal", 15))
			var new_hp: int = board.heal_unit(unit_id, heal_amt) if board != null else 10
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "🧪 %s bebeu %s (Curou +%d HP, Total: %d)!" % [uname, iname, heal_amt, new_hp])

		"METAL":
			var met: int = int(item_data.get("metal", item_data.get("amount", 5)))
			if economy != null:
				economy.add_resource("metal", met)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "⚙️ %s recolheu %s (+%d Metal)!" % [uname, iname, met])

		"WOOD":
			var wd: int = int(item_data.get("wood", item_data.get("amount", 5)))
			if economy != null:
				economy.add_resource("wood", wd)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("ITEM", "🪵 %s recolheu %s (+%d Madeira)!" % [uname, iname, wd])

	# Se múltiplos recursos foram empilhados na mesma célula, garante entrega de todos os recursos acumulados
	if itype != "CHEST" and itype != "BAU":
		var extra_w: int = int(item_data.get("wood", 0)) if itype != "WOOD" else 0
		var extra_l: int = int(item_data.get("leather", 0)) if (itype != "LEATHER" and itype != "COURO") else 0
		var extra_m: int = int(item_data.get("metal", 0)) if itype != "METAL" else 0
		var extra_g: int = int(item_data.get("gold", 0)) if (itype != "GOLD" and itype != "OURO") else 0
		if extra_w > 0 and economy != null: economy.add_resource("wood", extra_w)
		if extra_l > 0 and economy != null: economy.add_resource("leather", extra_l)
		if extra_m > 0 and economy != null: economy.add_resource("metal", extra_m)
		if extra_g > 0 and economy != null: economy.add_resource("crystal", extra_g)

func _on_board_view_unit_attack(attacker_id: String, target_id: String) -> void:
	if is_game_over or board == null:
		return
	var atk_data: Dictionary = board.get_unit_data(attacker_id)
	var tgt_data: Dictionary = board.get_unit_data(target_id)
	var atk_name: String = str(atk_data.get("name", attacker_id))
	var tgt_name: String = str(tgt_data.get("name", target_id))
	var atk_bonus: int = int(atk_data.get("attack_bonus", 3))
	var atk_range: int = int(atk_data.get("attack_range", 1))
	var tgt_ac: int = int(tgt_data.get("ac", 13))

	var atk_cell: Vector2i = board.get_unit_position(attacker_id)
	var tgt_cell: Vector2i = board.get_unit_position(target_id)

	# Animação de ataque (Avanço físico corpo a corpo ou projétil balístico)
	if hud_instance != null and hud_instance.board_view != null:
		if atk_range > 1 or (atk_cell != Vector2i(-1, -1) and tgt_cell != Vector2i(-1, -1) and atk_cell.distance_to(tgt_cell) > 1.5):
			hud_instance.board_view.launch_projectile(atk_cell, tgt_cell, "arrow", Color(1.0, 0.85, 0.2), 0.30)
		else:
			hud_instance.board_view.animate_melee_attack(attacker_id, tgt_cell, 0.28)

	var d20: int = randi_range(1, 20)
	var total_atk: int = d20 + atk_bonus
	var is_crit: bool = (d20 == 20)
	var is_hit: bool = is_crit or (total_atk >= tgt_ac)

	if is_hit:
		var dmg: int = randi_range(6, 12) + (randi_range(6, 12) if is_crit else 0)
		var remaining_hp: int = board.damage_unit(target_id, dmg)

		# VFX de impacto: flash carmesim no defensor, texto flutuante, partículas de combate e tremor de tela
		if hud_instance != null and hud_instance.board_view != null:
			hud_instance.board_view.trigger_unit_damage_flash(target_id, Color(1.0, 0.2, 0.2, 0.9), 0.25)
			var txt_tag: String = "-%d 💥" % dmg if is_crit else "-%d" % dmg
			var txt_col: Color = Color(1.0, 0.85, 0.15) if is_crit else Color(1.0, 0.25, 0.25)
			hud_instance.board_view.spawn_floating_combat_text(txt_tag, tgt_cell, txt_col, is_crit)
			var tgt_wpos: Vector2 = hud_instance.board_view.get_cell_screen_coords(tgt_cell.x, tgt_cell.y)
			hud_instance.board_view.spawn_impact_particles(tgt_wpos, "acid", 10 if is_crit else 6)
			if is_crit:
				hud_instance.board_view.trigger_screen_shake(8.5, 0.40)
				hud_instance.board_view.spawn_impact_particles(tgt_wpos, "spark", 8)

		if hud_instance != null and hud_instance.combat_log != null:
			var hit_tag: String = "💥 ACERTO CRÍTICO" if is_crit else "ACERTOU"
			hud_instance.combat_log.append_entry("COMBATE", "⚔️ %s atacou %s: d20(%d)+%d=%d vs CA %d -> %s! Causou %d dano (HP restante: %d)" % [atk_name, tgt_name, d20, atk_bonus, total_atk, tgt_ac, hit_tag, dmg, remaining_hp])
			if remaining_hp <= 0:
				enemies_defeated_count += 1
				var drop_pos: Vector2i = tgt_cell
				board.remove_unit(target_id)
				board.place_item(drop_pos, FortressBoard.ITEM_CRISTAL, {"name": "Espólios de %s" % tgt_name, "amount": 2})
				hud_instance.combat_log.append_entry("VITÓRIA", "💀 %s foi derrotado e dropou Cristais de Mana no chão!" % tgt_name)
				var go_check: Dictionary = check_game_over_conditions()
				if bool(go_check.get("game_over", false)):
					trigger_game_over(bool(go_check.get("victory", false)), str(go_check.get("reason", "")))
					return
	else:
		# VFX de Defesa/Miss
		if hud_instance != null and hud_instance.board_view != null:
			hud_instance.board_view.spawn_floating_combat_text("ESQUIVA 🛡️", tgt_cell, Color(0.65, 0.8, 1.0), false)

		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("COMBATE", "🛡️ %s atacou %s: d20(%d)+%d=%d vs CA %d -> ERROU!" % [atk_name, tgt_name, d20, atk_bonus, total_atk, tgt_ac])

var total_cards_played: int = 0

## Spawns an invasion wave from the perimeter spawn zones (SPAWN_NORTE, SPAWN_SUL, SPAWN_LESTE, SPAWN_OESTE)
func spawn_enemy_wave(wave_num: int) -> Array[String]:
	var spawned_ids: Array[String] = []
	if board == null:
		return spawned_ids
	
	var wave_defs: Array[Dictionary] = []
	if threat_deck != null:
		wave_defs = threat_deck.generate_wave(wave_num)
	
	if wave_defs.is_empty():
		wave_defs = [
			{"caste_id": "batedor", "name": "Batedor Isectum", "target_zone": "SPAWN_NORTE", "hp": 18, "ac": 13, "move": 4, "atk": 2},
			{"caste_id": "soldado", "name": "Soldado Isectum", "target_zone": "SPAWN_OESTE", "hp": 28, "ac": 14, "move": 3, "atk": 3},
			{"caste_id": "vespa", "name": "Vespa Caçadora", "target_zone": "SPAWN_LESTE", "hp": 22, "ac": 15, "move": 5, "atk": 4},
			{"caste_id": "besouro", "name": "Besouro Blindado", "target_zone": "SPAWN_SUL", "hp": 40, "ac": 18, "move": 2, "atk": 3}
		]
	
	var wave_unit_idx: int = 1
	for threat in wave_defs:
		var zname: String = str(threat.get("target_zone", threat.get("zone", "SPAWN_NORTE"))).to_upper()
		var cells: Array[Vector2i] = board.get_cells_in_zone(zname)
		if cells.is_empty():
			match zname:
				"SPAWN_NORTE": cells = [Vector2i(9, 1), Vector2i(10, 1), Vector2i(11, 1)]
				"SPAWN_SUL": cells = [Vector2i(9, 18), Vector2i(10, 18), Vector2i(11, 18)]
				"SPAWN_LESTE": cells = [Vector2i(18, 9), Vector2i(18, 10), Vector2i(18, 11)]
				"SPAWN_OESTE": cells = [Vector2i(1, 9), Vector2i(1, 10), Vector2i(1, 11)]
				_: cells = [Vector2i(10, 1)]

		var cid: String = str(threat.get("caste_id", "batedor")).to_lower()
		var count: int = int(threat.get("count", 1))
		var desc: String = str(threat.get("description", str(threat.get("name", cid.capitalize()))))
		
		# Consulta catálogo canônico de Castas para obter stats fidedignos
		var caste_data: IsectumCasteData = IsectumCastes.get_caste(cid)
		var base_hp: int = int(threat.get("hp", caste_data.hp if caste_data != null else 20))
		var base_move: int = int(threat.get("move", caste_data.speed if caste_data != null else 3))
		var base_atk_bonus: int = int(threat.get("atk", caste_data.attack_dice if caste_data != null else 3))
		var base_atk_range: int = int(threat.get("attack_range", caste_data.attack_range if caste_data != null else 1))
		var base_ac: int = int(threat.get("ac", 15 if (caste_data != null and caste_data.is_brutamontes) else 13))

		for _c_idx in range(mini(count, 3)):
			var spawn_cell: Vector2i = Vector2i(-1, -1)
			for candidate in cells:
				if board.get_units_at_cell(candidate).is_empty():
					spawn_cell = candidate
					break
			if spawn_cell == Vector2i(-1, -1):
				if not cells.is_empty():
					spawn_cell = cells[randi() % cells.size()]
				else:
					spawn_cell = Vector2i(10, 1)

			var unit_uid: String = "%s_w%d_%d" % [cid, wave_num, wave_unit_idx]
			wave_unit_idx += 1
			
			var udata: Dictionary = {
				"name": desc,
				"class": cid.capitalize(),
				"caste_id": cid,
				"team": "B",
				"hp": base_hp,
				"max_hp": base_hp,
				"ac": base_ac,
				"move_range": base_move,
				"attack_range": base_atk_range,
				"attack_bonus": base_atk_bonus
			}
			
			board.place_unit(unit_uid, spawn_cell)
			board.register_unit(unit_uid, udata)
			spawned_ids.append(unit_uid)

	if hud_instance != null and hud_instance.combat_log != null:
		hud_instance.combat_log.append_entry("AMEAÇA", "🚨 Onda %d de Invasores Isectum surgiu nos campos externos (%d insetos)!" % [wave_num, spawned_ids.size()])
	
	if hud_instance != null and hud_instance.board_view != null:
		hud_instance.board_view.queue_redraw()

	return spawned_ids

func _start_first_wave() -> void:
	if hud_instance != null and hud_instance.combat_log != null:
		hud_instance.combat_log.append_entry("PREPARAÇÃO", "🛡️ Rodada 1: A Fortaleza de Kuar-Tor está guarnecida. Planeje suas cartas e ordens antes do ataque!")

func _start_bgm() -> void:
	if not is_inside_tree():
		return
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_bgm"):
			am.play_bgm("battle1")

func _on_hud_card_played(_player_id: String, card_id: String, target_zone: String) -> void:
	if is_game_over:
		return
	var played_card: CardData = null
	if deck != null:
		played_card = deck.play_card(card_id)
		# Se a carta foi jogada da mão, garante que a UI remova a carta visualmente
		if hud_instance != null and hud_instance.card_fan != null and played_card != null:
			hud_instance.card_fan.remove_card_by_id(played_card.id)
	
	if played_card == null:
		played_card = CardData.new()
		played_card.id = card_id
		played_card.card_name = card_id
	
	total_cards_played += 1
	
	# Registra ação no turno simultâneo de sincronia
	if sync_round != null:
		sync_round.register_player_action("player_1", played_card, {"target_zone": target_zone})
	
	# Aplica efeitos imediatos da carta no tabuleiro e economia
	_apply_card_effects(played_card, target_zone)
	
	# Atualiza o banner do HUD com a quantidade de ordens
	if hud_instance != null:
		var cname: String = played_card.card_name if not played_card.card_name.is_empty() else card_id
		hud_instance.update_banner_orders(total_cards_played, cname)
	
	# Notifica o EventBus global se disponível
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("card_played"):
				eb.card_played.emit("player_1", card_id, target_zone)

func _apply_card_effects(card: CardData, target_zone: String) -> void:
	if card == null:
		return

	var cid: String = card.id.to_lower().strip_edges()
	var ctype: String = card.card_type.to_upper().strip_edges()
	var cbadge: String = card.badge.to_upper().strip_edges()

	# ── 1. Habilidades Especiais de Cartas de Runa ─────────────────────────────
	if ctype == CardData.TYPE_RUNA or cid.begins_with("runa_"):
		match cid:
			"runa_haste":
				if board != null:
					for hero_id in ["aquele", "stark", "lysander"]:
						var udata: Dictionary = board.get_unit_data(hero_id)
						if not udata.is_empty():
							udata["move_range"] = int(udata.get("move_range", 3)) + 5
							board.set_unit_data(hero_id, udata)
				if economy != null:
					economy.add_resource("ap", 2)
				if hud_instance != null and hud_instance.combat_log != null:
					hud_instance.combat_log.append_entry("RUNA", "✨ Runa da Haste ativada! +5 PM para todos os heróis e +2 PA!")
				return

			"runa_recuperacao":
				if deck != null:
					deck.draw_cards(2)
				if hud_instance != null and hud_instance.combat_log != null:
					hud_instance.combat_log.append_entry("RUNA", "📜 Runa de Recuperação ativada! +2 Cartas sacadas do grimório.")
				return

			"runa_fortaleza":
				if board != null:
					for wz in [FortressBoard.ZONE_MURALHA_NORTE, FortressBoard.ZONE_MURALHA_SUL, FortressBoard.ZONE_MURALHA_LESTE, FortressBoard.ZONE_MURALHA_OESTE]:
						board.repair_wall(wz, 15)
				if economy != null:
					economy.add_resource("wood", 4)
					economy.add_resource("metal", 2)
				if hud_instance != null and hud_instance.combat_log != null:
					hud_instance.combat_log.append_entry("RUNA", "🛡️ Runa da Fortaleza! Todas as 4 muralhas fortificadas (+15 HP cada)!")
				return

			"runa_visao":
				if threat_deck != null:
					var peeked: Array[Dictionary] = threat_deck.peek_threats(3)
					var titles: Array[String] = []
					for t in peeked:
						titles.append(str(t.get("title", t.get("name", "Ameaça"))))
					if hud_instance != null and hud_instance.combat_log != null:
						hud_instance.combat_log.append_entry("RUNA", "🔮 Runa da Visão! Próximas ameaças avistadas: %s" % ", ".join(titles))
				return

	# ── 2. Habilidades de Cartas de Defesa / Reação ────────────────────────────
	if ctype == CardData.TYPE_DEFESA or cid in ["escudo_quitina", "teia_endurecida", "antidoto_alquimico", "amuleto_resistencia"]:
		if threat_deck != null:
			var res_def: Dictionary = threat_deck.resolve_defense_card(cid)
			var msg: String = str(res_def.get("message", "Defesa executada."))
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("DEFESA", "🛡️ %s" % msg)

		match cid:
			"escudo_quitina":
				if board != null:
					board.repair_wall(FortressBoard.ZONE_MURALHA_NORTE, 15)
			"antidoto_alquimico":
				if board != null:
					for hid in ["aquele", "stark", "lysander"]:
						board.heal_unit(hid, 15)
			"amuleto_resistencia":
				if economy != null:
					economy.add_resource("crystal", 2)
					economy.add_resource("wood", 4)
					economy.add_resource("leather", 4)
		return

	# ── 3. Habilidades Especiais de Cartas de Upgrade do Mercado ───────────────
	if cid == "plano_tatico":
		if deck != null:
			deck.max_hand_size = mini(7, deck.max_hand_size + 1)
			deck.draw_cards(1)
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("UPGRADE", "📐 Plano Tático! Capacidade da mão aumentada para %d e +1 carta sacada!" % (deck.max_hand_size if deck != null else 6))

	elif cid == "mestre_artesao":
		if deck != null:
			deck.draw_cards(1)
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("UPGRADE", "🔨 Mestre Artesão! Compra 1 carta extra de ação!")

	elif cid == "grande_forjador":
		if economy != null:
			economy.add_resource("metal", 2)
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("UPGRADE", "⚙️ Grande Forjador! Forjou +2 Lingotes de Metal de alta qualidade!")

	# ── 4. Efeitos Canônicos por Badge (Trabalho, Escavação, Marcha, Combate) ───
	# 4.1. Trabalho e Reparo de Muralhas
	var work_power: int = maxi(1, card.work)
	if economy != null:
		if target_zone in ["CARPINTARIA", "CURTUME", "FUNDICAO", "PATIO_CENTRAL"]:
			economy.produce(target_zone, work_power)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("TRABALHO", "🔨 Produção na %s gerou suprimentos (Força: %d)!" % [target_zone, work_power])
		elif target_zone in ["MURALHA_NORTE", "MURALHA_SUL", "MURALHA_LESTE", "MURALHA_OESTE", "NORTE", "SUL", "LESTE", "OESTE"]:
			if board != null:
				var new_hp: int = economy.repair_wall(target_zone, board, work_power, 0)
				if hud_instance != null and hud_instance.combat_log != null:
					hud_instance.combat_log.append_entry("REPARO", "🛡️ Muralha %s reparada! Integridade atual: %d HP" % [target_zone, new_hp])
		elif cbadge == CardData.BADGE_TRABALHO or card.work > 0:
			economy.produce("CARPINTARIA", work_power)
			economy.add_resource("ap", work_power)
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("TRABALHO", "🔨 Artesãos produziram +%d Madeira, Couro e Metal!" % work_power)

	# 4.2. Escavação e Rubble
	if cbadge == CardData.BADGE_ESCAVACAO or card.excavation > 0:
		var crystals_gained: int = maxi(1, floori(float(card.excavation) / 2.0))
		var metal_gained: int = maxi(1, floori(float(card.excavation) / 3.0))
		if economy != null:
			economy.add_resource("crystal", crystals_gained)
			economy.add_resource("metal", metal_gained)
		if board != null and board.has_method("damage_rubble"):
			board.damage_rubble("CENTRO", 1)
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("ESCAVAÇÃO", "⛏️ Escavação profunda: +%d Cristais de Mana e +%d Metal obtidos!" % [crystals_gained, metal_gained])

	# 4.3. Marcha / Movimento
	if cbadge == CardData.BADGE_MARCHA or card.movement > 0:
		var bonus_pm: int = maxi(1, floori(float(card.movement) / 5.0)) if card.movement > 0 else 3
		if board != null:
			for hero_id in ["aquele", "stark", "lysander"]:
				var udata: Dictionary = board.get_unit_data(hero_id)
				if not udata.is_empty():
					var cur_pm: int = int(udata.get("move_range", 3))
					udata["move_range"] = cur_pm + bonus_pm
					board.set_unit_data(hero_id, udata)
			
			if hud_instance != null and hud_instance.board_view != null:
				var sel_uid: String = hud_instance.board_view.get_selected_unit()
				if sel_uid.is_empty():
					sel_uid = "aquele"
				hud_instance.board_view.select_unit(sel_uid)
				hud_instance.update_active_hero(board.get_unit_data(sel_uid))
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("MARCHA", "⚡ Heróis marcharam: +%d Pontos de Movimento (Alcance Tático ampliado)!" % bonus_pm)

	# 4.4. Combate / Força Anã
	if cbadge == CardData.BADGE_COMBATE:
		if judge != null:
			var rolls: Array = judge.roll_cerco_dice(maxi(2, card.work))
			var impacts: int = judge.count_face(rolls, CercoCombatJudge.D6Face.IMPACTO)
			var crits: int = judge.count_face(rolls, CercoCombatJudge.D6Face.CRITICO)
			var total_dmg: int = impacts * 5 + crits * 10
			if hud_instance != null and hud_instance.combat_log != null:
				hud_instance.combat_log.append_entry("COMBATE", "⚔️ Força Anã disparada! Dano concentrado contra o cerco: %d de dano!" % total_dmg)

## AI Turn: Moves all active enemy units ("team B") toward the nearest heroes or central fortress,
## attacking adjacent heroes or damaging perimeter walls along their path.
func advance_enemy_units() -> Dictionary:
	var summary: Dictionary = {
		"moved_count": 0,
		"attacks_count": 0,
		"wall_hits_count": 0
	}
	if board == null:
		return summary

	var enemy_ids: Array[String] = board.get_units_by_team("B")
	if enemy_ids.is_empty():
		return summary

	# Identifica posições de todos os heróis vivos (time "A")
	var living_heroes: Array[String] = []
	for hid in board.get_units_by_team("A"):
		if board.is_unit_alive(hid):
			living_heroes.append(hid)

	var fortress_center: Vector2i = Vector2i(9, 9)

	for enemy_id in enemy_ids:
		if not board.is_unit_alive(enemy_id):
			continue

		var cur_pos: Vector2i = board.get_unit_position(enemy_id)
		if cur_pos == Vector2i(-1, -1):
			continue

		var edata: Dictionary = board.get_unit_data(enemy_id)
		var enemy_name: String = str(edata.get("name", enemy_id))
		var move_range: int = int(edata.get("move_range", 3))
		var atk_range: int = int(edata.get("attack_range", 1))
		var atk_bonus: int = int(edata.get("attack_bonus", 3))
		var caste_key: String = str(edata.get("caste_id", edata.get("class", enemy_id.split("_")[0]))).to_lower()

		# 1. Se já puder atacar um herói adjacente antes de andar
		var target_hero_id: String = ""
		var attackable: Array[Vector2i] = board.get_attackable_cells(cur_pos, atk_range, "B")
		if not attackable.is_empty():
			target_hero_id = _pick_best_hero_target(attackable, living_heroes, true)

		if not target_hero_id.is_empty():
			_execute_enemy_attack(enemy_id, enemy_name, atk_bonus, target_hero_id)
			summary["attacks_count"] += 1
			continue

		# 2. Movimentação tática inteligente por Arquétipo de Casta
		var target_pos: Vector2i = fortress_center
		var caste_data: IsectumCasteData = IsectumCastes.get_caste(caste_key)
		var is_infiltrator: bool = (caste_data != null and caste_data.is_infiltrator)
		var is_flyer: bool = (caste_data != null and caste_data.is_flyer)

		var is_flanker: bool = is_infiltrator or is_flyer or caste_key.contains("vespa") or caste_key.contains("aranha") or caste_key.contains("libelula") or caste_key.contains("vagalume") or caste_key.contains("pulga")

		var is_siege: bool = false
		if caste_data != null and (caste_data.is_brutamontes or caste_data.is_catapult or caste_data.id == IsectumCastes.ID_OPERARIO_ESCAVADOR or caste_data.id == IsectumCastes.ID_CUPIM_ROEDOR):
			is_siege = true
		elif caste_key.contains("besouro") or caste_key.contains("tatuzinho") or caste_key.contains("escaravelho") or caste_key.contains("operario") or caste_key.contains("colosso") or caste_key.contains("cupim"):
			is_siege = true

		# Seleção de alvo prioritário
		if not living_heroes.is_empty():
			if is_flanker:
				# Flanqueadores caçam o herói mais frágil (menor HP atual)
				var lowest_hp: int = 9999
				for hid in living_heroes:
					var h_data: Dictionary = board.get_unit_data(hid)
					var h_hp: int = int(h_data.get("hp", 10))
					var h_pos: Vector2i = board.get_unit_position(hid)
					if h_pos != Vector2i(-1, -1) and h_hp < lowest_hp:
						lowest_hp = h_hp
						target_pos = h_pos
			else:
				# Combatentes e tanques marcham em direção ao herói mais próximo
				var min_target_dist: int = 999
				for hid in living_heroes:
					var hpos: Vector2i = board.get_unit_position(hid)
					if hpos != Vector2i(-1, -1):
						var d: int = maxi(absi(cur_pos.x - hpos.x), absi(cur_pos.y - hpos.y))
						if d < min_target_dist:
							min_target_dist = d
							target_pos = hpos

		# Apenas castas especializadas em cerco param deliberadamente para golpear muralhas intactas
		var current_zone: String = board.get_zone_at(cur_pos)
		var is_at_intact_wall: bool = is_siege and (current_zone in [FortressBoard.ZONE_MURALHA_NORTE, FortressBoard.ZONE_MURALHA_SUL, FortressBoard.ZONE_MURALHA_LESTE, FortressBoard.ZONE_MURALHA_OESTE]) and not board.is_wall_breached(current_zone)

		if not is_at_intact_wall:
			# Calcula caminho tático usando pathfinding com evasão de obstáculos
			var best_cell: Vector2i = cur_pos
			var full_path: Array[Vector2i] = board.find_path(cur_pos, target_pos, false)

			if not full_path.is_empty():
				var step_limit: int = mini(move_range, full_path.size())
				if atk_range > 1:
					# Unidades à distância avançam apenas até entrar no alcance de ataque
					for s_idx in range(step_limit):
						var candidate_cell: Vector2i = full_path[s_idx]
						if candidate_cell != cur_pos and board.get_units_at_cell(candidate_cell).is_empty():
							var dist_to_tgt: int = maxi(absi(candidate_cell.x - target_pos.x), absi(candidate_cell.y - target_pos.y))
							if dist_to_tgt <= atk_range:
								best_cell = candidate_cell
								break
							best_cell = candidate_cell
				else:
					# Unidades corpo a corpo avançam o máximo possível em direção ao alvo
					for s_idx in range(step_limit - 1, -1, -1):
						var candidate_cell: Vector2i = full_path[s_idx]
						if candidate_cell != cur_pos and board.get_units_at_cell(candidate_cell).is_empty():
							best_cell = candidate_cell
							break

			# Fallback de busca em reachable_cells se o caminho direto estiver congestionado
			if best_cell == cur_pos:
				var reachable_cells: Array[Vector2i] = board.get_reachable_cells(cur_pos, move_range)
				if not reachable_cells.is_empty():
					var best_dist: int = maxi(absi(cur_pos.x - target_pos.x), absi(cur_pos.y - target_pos.y))
					for cell in reachable_cells:
						var d: int = maxi(absi(cell.x - target_pos.x), absi(cell.y - target_pos.y))
						if atk_range > 1 and d <= atk_range:
							best_cell = cell
							break
						if d < best_dist:
							best_dist = d
							best_cell = cell

			if best_cell != cur_pos:
				if hud_instance != null and hud_instance.board_view != null:
					hud_instance.board_view.animate_unit_move(enemy_id, cur_pos, best_cell, 0.22)
				board.move_unit(enemy_id, best_cell)
				cur_pos = best_cell
				summary["moved_count"] += 1

		# 3. Pós-movimento: ataca herói se agora estiver ao alcance, ou golpeia muralha
		attackable = board.get_attackable_cells(cur_pos, atk_range, "B")
		if not attackable.is_empty():
			target_hero_id = _pick_best_hero_target(attackable, living_heroes, is_flanker)
			if not target_hero_id.is_empty():
				_execute_enemy_attack(enemy_id, enemy_name, atk_bonus, target_hero_id)
				summary["attacks_count"] += 1
				continue

		# Se não tiver herói no alcance, checa se está em zona de muralha ainda intacta para danificá-la
		current_zone = board.get_zone_at(cur_pos)
		if current_zone in [FortressBoard.ZONE_MURALHA_NORTE, FortressBoard.ZONE_MURALHA_SUL, FortressBoard.ZONE_MURALHA_LESTE, FortressBoard.ZONE_MURALHA_OESTE]:
			if not board.is_wall_breached(current_zone):
				var wall_dmg: int = randi_range(3, 6)
				if is_siege:
					wall_dmg += 3 # Brutamontes e perfuradores causam bônus contra estruturas
				var new_hp: int = board.damage_wall(current_zone, wall_dmg)
				summary["wall_hits_count"] += 1

				# VFX: Anima golpe contra a muralha, floating text, partículas de pedra e tremor de tela
				if hud_instance != null and hud_instance.board_view != null:
					hud_instance.board_view.animate_melee_attack(enemy_id, cur_pos, 0.25)
					hud_instance.board_view.spawn_floating_combat_text("-%d 🧱" % wall_dmg, cur_pos, Color(1.0, 0.55, 0.2), false)
					hud_instance.board_view.trigger_screen_shake(7.0, 0.35)
					var w_coords: Vector2 = hud_instance.board_view.get_cell_screen_coords(cur_pos.x, cur_pos.y)
					hud_instance.board_view.spawn_impact_particles(w_coords, "stone", 10)

				if hud_instance != null and hud_instance.combat_log != null:
					hud_instance.combat_log.append_entry("CERCO", "🧱 %s investiu contra a %s: %d de dano! (HP restante: %d)" % [enemy_name, current_zone, wall_dmg, new_hp])

	if hud_instance != null and hud_instance.board_view != null:
		hud_instance.board_view.queue_redraw()

	return summary

## Dispara trompa de guerra anã e tremor de tela ao romper a muralha da fortaleza
func _on_wall_breached_event(wall_id: String) -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_war_horn_alarm"):
			am.play_war_horn_alarm()
	if hud_instance != null:
		if hud_instance.board_view != null:
			hud_instance.board_view.trigger_screen_shake(12.0, 0.55)
		if hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("🚨 ALARME GERAL", "📯 Trompa de Guerra anã soa! A muralha %s foi ROMPIDA pelo enxame!" % wall_id)

## Helper to pick the best hero target from attackable cells (preferring lowest HP or first found)
func _pick_best_hero_target(attackable_cells: Array[Vector2i], living_heroes: Array[String], prefer_lowest_hp: bool) -> String:
	if attackable_cells.is_empty() or board == null:
		return ""
	var best_hid: String = ""
	var lowest_hp: int = 999999
	for cell in attackable_cells:
		for hid in living_heroes:
			if board.get_unit_position(hid) == cell:
				var h_data: Dictionary = board.get_unit_data(hid)
				var h_hp: int = int(h_data.get("hp", 10))
				if prefer_lowest_hp:
					if h_hp < lowest_hp:
						lowest_hp = h_hp
						best_hid = hid
				else:
					if best_hid.is_empty() or h_hp < lowest_hp:
						lowest_hp = h_hp
						best_hid = hid
				break
	return best_hid

func _execute_enemy_attack(enemy_id: String, enemy_name: String, atk_bonus: int, target_hero_id: String) -> void:
	if board == null:
		return
	var hdata: Dictionary = board.get_unit_data(target_hero_id)
	var hero_name: String = str(hdata.get("name", target_hero_id))
	var hero_ac: int = int(hdata.get("ac", 15))

	var edata: Dictionary = board.get_unit_data(enemy_id)
	var atk_range: int = int(edata.get("attack_range", 1))
	var e_pos: Vector2i = board.get_unit_position(enemy_id)
	var h_pos: Vector2i = board.get_unit_position(target_hero_id)

	# Animação de ataque (avanço corpo a corpo ou projétil cuspe/ácido)
	if hud_instance != null and hud_instance.board_view != null:
		if atk_range > 1 or (e_pos != Vector2i(-1, -1) and h_pos != Vector2i(-1, -1) and e_pos.distance_to(h_pos) > 1.5):
			hud_instance.board_view.launch_projectile(e_pos, h_pos, "beam", Color(0.4, 0.9, 0.2), 0.30)
		else:
			hud_instance.board_view.animate_melee_attack(enemy_id, h_pos, 0.28)

	var d20: int = randi_range(1, 20)
	var total_atk: int = d20 + atk_bonus
	var is_crit: bool = (d20 == 20)

	if total_atk >= hero_ac or is_crit:
		var dmg: int = randi_range(4, 8) + atk_bonus
		if is_crit:
			dmg *= 2
		var new_hp: int = board.damage_unit(target_hero_id, dmg)

		# VFX de impacto e texto flutuante no herói
		if hud_instance != null and hud_instance.board_view != null:
			hud_instance.board_view.trigger_unit_damage_flash(target_hero_id, Color(1.0, 0.15, 0.15, 0.9), 0.25)
			var txt_tag: String = "-%d 💥" % dmg if is_crit else "-%d" % dmg
			var txt_col: Color = Color(1.0, 0.85, 0.15) if is_crit else Color(1.0, 0.25, 0.25)
			hud_instance.board_view.spawn_floating_combat_text(txt_tag, h_pos, txt_col, is_crit)

		if hud_instance != null and hud_instance.combat_log != null:
			var crit_label: String = " 💥 CRÍTICO!" if is_crit else ""
			hud_instance.combat_log.append_entry("ATAQUE", "⚔️ %s atacou %s: d20(%d)+%d=%d vs CA %d%s -> ACERTOU! Causa %d de dano! (HP restante: %d)" % [
				enemy_name, hero_name, d20, atk_bonus, total_atk, hero_ac, crit_label, dmg, new_hp
			])
		if hud_instance != null and "hero_roster_panel" in hud_instance and hud_instance.hero_roster_panel != null:
			hud_instance.update_hero_stats(target_hero_id, board.get_unit_data(target_hero_id))

		var go_check: Dictionary = check_game_over_conditions()
		if bool(go_check.get("game_over", false)):
			trigger_game_over(bool(go_check.get("victory", false)), str(go_check.get("reason", "")))
			return
	else:
		# VFX de Defesa/Miss
		if hud_instance != null and hud_instance.board_view != null:
			hud_instance.board_view.spawn_floating_combat_text("DEFESA 🛡️", h_pos, Color(0.65, 0.8, 1.0), false)

		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("DEFESA", "🛡️ %s atacou %s: d20(%d)+%d=%d vs CA %d -> ERROU!" % [
				enemy_name, hero_name, d20, atk_bonus, total_atk, hero_ac
			])

func _on_hud_sync_round_requested() -> void:
	if is_game_over:
		return
	if sync_round != null:
		var result: Dictionary = sync_round.resolve_synchrony_round(current_round, board, judge, economy)
		if hud_instance != null and hud_instance.combat_log != null:
			var r_num: int = result.get("round_number", current_round)
			hud_instance.combat_log.append_entry("SINCRONIA", "⚔️ Turno de Sincronia concluído! Rodada %d" % r_num)
		
		# Invasores ativos marcham e atacam antes dos reforços
		advance_enemy_units()

		# Checa se o avanço ou ataques inimigos causaram derrota imediata
		var mid_check: Dictionary = check_game_over_conditions()
		if bool(mid_check.get("game_over", false)):
			trigger_game_over(bool(mid_check.get("victory", false)), str(mid_check.get("reason", "")))
			return

		# Novos invasores chegam aos perímetros de spawn se ainda dentro do limite de rodadas
		if current_round < max_rounds:
			spawn_enemy_wave(current_round)
		current_round += 1
		total_cards_played = 0

		# Checa condição de vitória caso tenha concluído as rodadas e limpado os inimigos
		var end_check: Dictionary = check_game_over_conditions()
		if bool(end_check.get("game_over", false)):
			trigger_game_over(bool(end_check.get("victory", false)), str(end_check.get("reason", "")))
			return

		# Reabastece a mão do jogador para a próxima rodada tática:
		# Sempre saca pelo menos 1 nova carta ao virar a rodada, recompondo até a capacidade máxima.
		if deck != null:
			var needed: int = maxi(1, int(deck.max_hand_size) - deck.hand.size())
			var drawn_cards: Array[CardData] = deck.draw_cards(needed)
			
			# Garante que a interface gráfica (leque de cartas) esteja 100% sincronizada com a mão
			if hud_instance != null:
				if hud_instance.card_fan != null:
					hud_instance.card_fan.set_hand(deck.get_hand())
				hud_instance._update_deck_counts()
				if hud_instance.combat_log != null and not drawn_cards.is_empty():
					hud_instance.combat_log.append_entry("COMPRA", "🃏 Rodada %d: Você comprou %d nova(s) carta(s) para a mão!" % [current_round, drawn_cards.size()])

		if hud_instance != null:
			hud_instance.update_banner_orders(0, "Aguardando ordens")

func _on_market_upgrade_purchased(card_id: String) -> void:
	if is_game_over or deck == null or economy == null:
		return
	var bought_card: CardData = deck.buy_card_from_market(card_id, economy)
	if bought_card != null:
		if hud_instance != null:
			hud_instance._update_deck_counts()
			if hud_instance.market_panel != null:
				hud_instance.market_panel.set_deck_capacity(deck.get_total_deck_size(), 12)
			if hud_instance.combat_log != null:
				var cname: String = bought_card.card_name if not bought_card.card_name.is_empty() else card_id
				hud_instance.combat_log.append_entry("MERCADO", "🛒 Upgrade adquirido: [%s] adicionado ao seu baralho de descarte!" % cname)
			hud_instance.play_sfx("button_click", 0.9, 1.2)
	else:
		if hud_instance != null and hud_instance.combat_log != null:
			hud_instance.combat_log.append_entry("MERCADO", "❌ Recursos insuficientes ou carta indisponível!")

## Checks whether a victory or defeat condition has been reached.
func check_game_over_conditions() -> Dictionary:
	if is_game_over:
		return {"game_over": true, "victory": false}
	if board == null:
		return {"game_over": false}

	# 1. DERROTA: Todos os heróis aliados estão mortos (HP <= 0)
	var living_heroes: Array[String] = []
	for hid in board.get_units_by_team("A"):
		if board.is_unit_alive(hid):
			living_heroes.append(hid)

	if living_heroes.is_empty():
		return {
			"game_over": true,
			"victory": false,
			"reason": "Todos os heróis defensores tombaram em batalha! A fortaleza caiu."
		}

	# 2. DERROTA: Invasores Isectum entraram na Câmara Central (3 ou mais)
	var central_invaders: int = 0
	for uid in board.get_units_by_team("B"):
		if board.is_unit_alive(uid):
			var upos: Vector2i = board.get_unit_position(uid)
			if upos != Vector2i(-1, -1) and board.get_zone_at(upos) == FortressBoard.ZONE_CAMARA_CENTRAL:
				central_invaders += 1

	if central_invaders >= 3:
		return {
			"game_over": true,
			"victory": false,
			"reason": "O Enxame Isectum invadiu a Câmara Central! O coração da fortaleza caiu."
		}

	# 3. VITÓRIA: Sobreviveu a todas as rodadas máximas e eliminou os invasores restantes
	if current_round > max_rounds:
		var living_enemies: Array[String] = []
		for uid in board.get_units_by_team("B"):
			if board.is_unit_alive(uid):
				living_enemies.append(uid)
		if living_enemies.is_empty():
			return {
				"game_over": true,
				"victory": true,
				"reason": "Todas as ondas de cerco foram repelidas e a fortaleza resistiu! VITÓRIA DOS DEFENSORES!"
			}

	return {"game_over": false}

## Triggers the Game Over modal overlay and halts further combat interactions.
func trigger_game_over(victory: bool, reason: String) -> void:
	if is_game_over:
		return
	is_game_over = true

	var rounds_survived: int = mini(current_round, max_rounds)
	var stats: Dictionary = {
		"rounds_survived": rounds_survived,
		"enemies_defeated": enemies_defeated_count,
		"cards_played": total_cards_played,
		"wood": economy.wood if economy != null else 0,
		"leather": economy.leather if economy != null else 0,
		"metal": economy.metal if economy != null else 0,
		"crystals": economy.crystal if economy != null else 0
	}

	if hud_instance != null and hud_instance.combat_log != null:
		var tag: String = "VITÓRIA" if victory else "DERROTA"
		var log_msg: String = "🏆 %s" % reason if victory else "💀 %s" % reason
		hud_instance.combat_log.append_entry(tag, log_msg)

	# Toca SFX temático
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("AudioManager"):
		var am: Node = tree.root.get_node("AudioManager")
		if am.has_method("play_sfx"):
			am.play_sfx("level_up" if victory else "damage", 1.0, 1.0)

	# Atualiza o GameManager singleton caso conectado
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		if "state_payload" in gm:
			gm.state_payload = {
				"victory": victory,
				"reason": reason,
				"stats": stats
			}

	# Instancia e apresenta o modal GameOverModal
	if game_over_modal_instance == null:
		game_over_modal_instance = GAME_OVER_MODAL_SCENE.instantiate() as Control
		if hud_instance != null:
			hud_instance.add_child(game_over_modal_instance)
		else:
			add_child(game_over_modal_instance)

	if game_over_modal_instance != null:
		game_over_modal_instance.setup(victory, reason, stats)
		if not game_over_modal_instance.restart_requested.is_connected(_on_game_over_restart):
			game_over_modal_instance.restart_requested.connect(_on_game_over_restart)
		if not game_over_modal_instance.menu_requested.is_connected(_on_game_over_menu):
			game_over_modal_instance.menu_requested.connect(_on_game_over_menu)
		game_over_modal_instance.show()

func _on_game_over_restart() -> void:
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.reload_current_scene()

func _on_game_over_menu() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("GameManager"):
		var gm: Node = tree.root.get_node("GameManager")
		if gm.has_method("change_state_and_scene"):
			gm.change_state_and_scene(0) # GameState.MENU
			return
	if tree != null:
		tree.change_scene_to_file("res://scenes/main/Menu.tscn")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE and not is_game_over:
			# Retorna ao Menu Principal se ESC for pressionado
			var tree: SceneTree = get_tree()
			if tree != null and tree.root.has_node("GameManager"):
				var gm: Node = tree.root.get_node("GameManager")
				if gm.has_method("change_state_and_scene"):
					gm.change_state_and_scene(0) # GameState.MENU
