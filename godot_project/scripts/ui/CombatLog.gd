# res://scripts/ui/CombatLog.gd
class_name CombatLog
extends RichTextLabel

## Scrollable Dark Fantasy combat and Cerco event log using RichTextLabel with BBCode formatting.
## Listens to EventBus signals (combat_log_entry_added, damage_dealt, dice_rolled, wall_breached,
## synergy_triggered, supreme_synchrony_triggered) and enforces a bounded entry limit.

const MAX_ENTRIES: int = 100

# ── Prefix Colors ────────────────────────────────────────────────────────────
const COLOR_SISTEMA: String = "#94a3b8"
const COLOR_CARTA: String = "#38bdf8"
const COLOR_DADOS: String = "#facc15"
const COLOR_DANO: String = "#f87171"
const COLOR_BRECHA: String = "#ef4444"
const COLOR_PRODUCAO: String = "#4ade80"
const COLOR_SINERGIA: String = "#c084fc"
const COLOR_SUPREMA: String = "#f472b6"

var _entries: Array[String] = []

func _init() -> void:
	bbcode_enabled = true
	scroll_following = true
	autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	custom_minimum_size = Vector2(240.0, 160.0)

func _ready() -> void:
	_connect_event_bus()

func _connect_event_bus() -> void:
	if not Engine.is_editor_hint():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("combat_log_entry_added") and not eb.combat_log_entry_added.is_connected(_on_combat_log_entry_added):
				eb.combat_log_entry_added.connect(_on_combat_log_entry_added)
			if eb.has_signal("damage_dealt") and not eb.damage_dealt.is_connected(_on_damage_dealt):
				eb.damage_dealt.connect(_on_damage_dealt)
			if eb.has_signal("dice_rolled") and not eb.dice_rolled.is_connected(_on_dice_rolled):
				eb.dice_rolled.connect(_on_dice_rolled)
			if eb.has_signal("wall_breached") and not eb.wall_breached.is_connected(_on_wall_breached):
				eb.wall_breached.connect(_on_wall_breached)
			if eb.has_signal("synergy_triggered") and not eb.synergy_triggered.is_connected(_on_synergy_triggered):
				eb.synergy_triggered.connect(_on_synergy_triggered)
			if eb.has_signal("supreme_synchrony_triggered") and not eb.supreme_synchrony_triggered.is_connected(_on_supreme_synchrony_triggered):
				eb.supreme_synchrony_triggered.connect(_on_supreme_synchrony_triggered)

# ── Static Emoji & Glyph Sanitization ─────────────────────────────────────────
static var _regex_emojis: RegEx = null

## Substitui emojis Unicode de 4 bytes e caracteres exóticos por tags limpas de texto
## para evitar tofu ou corrupção de cluster/wrap no HarfBuzz/ICU do Linux.
static func sanitizar_texto(p_text: String) -> String:
	var res: String = p_text
	res = res.replace("🃏", "[Carta]")
	res = res.replace("⚔️", "[ATK]")
	res = res.replace("🛡️", "[DEF]")
	res = res.replace("🚨", "[AMEAÇA]")
	res = res.replace("🧱", "[MURALHA]")
	res = res.replace("💥", "[CRÍTICO]")
	res = res.replace("💀", "[K.O.]")
	res = res.replace("💎", "[CRISTAL]")
	res = res.replace("📦", "[BAÚ]")
	res = res.replace("🧪", "[POÇÃO]")
	res = res.replace("🪵", "[MADEIRA]")
	res = res.replace("✨", "[RUNA]")
	res = res.replace("📜", "[GRIMÓRIO]")
	res = res.replace("🔮", "[VISÃO]")
	res = res.replace("📐", "[PLANO]")
	res = res.replace("🔨", "[OFICINA]")
	res = res.replace("⚙️", "[METAL]")
	res = res.replace("⛏️", "[MINA]")
	res = res.replace("⚡", "[MARCHA]")
	res = res.replace("🛒", "[MERCADO]")
	res = res.replace("🚶", "[MOV]")
	res = res.replace("🎯", "[ALVO]")
	res = res.replace("🐝", "[VESPA]")
	res = res.replace("🐜", "[SOLDADO]")
	res = res.replace("🪲", "[BESOURO]")
	res = res.replace("🕷️", "[ARANHA]")
	res = res.replace("💣", "[LIBÉLULA]")
	res = res.replace("💡", "[VAGALUME]")
	res = res.replace("👑", "[RAINHA]")
	res = res.replace("🗿", "[COLOSSO]")
	res = res.replace("🦗", "[INSETO]")

	if _regex_emojis == null:
		_regex_emojis = RegEx.new()
		_regex_emojis.compile("[\\x{1F000}-\\x{1FFFF}]")
	if _regex_emojis.is_valid():
		res = _regex_emojis.sub(res, "", true)
	return res

## Logs an entry with BBCode text, ensuring atomic lines and clean glyphs
func log_message(bbcode_text: String) -> void:
	if bbcode_text.is_empty():
		return
	
	var sanitized: String = sanitizar_texto(bbcode_text)
	_entries.append(sanitized)
	if _entries.size() > MAX_ENTRIES:
		_entries.pop_front()
		_rebuild_text()
	else:
		if _entries.size() == 1:
			clear()
			append_text(sanitized)
		else:
			append_text("\n" + sanitized)

## Logs a message with a formatted category tag
func append_entry(entry_type: String, message: String) -> void:
	var color_tag: String = COLOR_SISTEMA
	var tag_name: String = entry_type.to_upper()
	
	match tag_name:
		"CARTA": color_tag = COLOR_CARTA
		"DADOS": color_tag = COLOR_DADOS
		"DANO": color_tag = COLOR_DANO
		"BRECHA!", "BRECHA": color_tag = COLOR_BRECHA
		"PRODUÇÃO", "PRODUCAO": color_tag = COLOR_PRODUCAO
		"SINERGIA": color_tag = COLOR_SINERGIA
		"SUPREMA", "SINCRONIA SUPREMA": color_tag = COLOR_SUPREMA
		_: color_tag = COLOR_SISTEMA
	
	var clean_msg: String = sanitizar_texto(message)
	var formatted: String = "[color=%s][%s][/color] %s" % [color_tag, tag_name, clean_msg]
	log_message(formatted)

## Clears all entries from log
func clear_log() -> void:
	_entries.clear()
	clear()

## Returns copies of all stored log entries
func get_entries() -> Array[String]:
	return _entries.duplicate()

## Returns count of active entries
func get_entry_count() -> int:
	return _entries.size()

## Returns raw text of the most recent entry
func get_last_entry_text() -> String:
	if _entries.is_empty():
		return ""
	return _entries[_entries.size() - 1]

func _rebuild_text() -> void:
	clear()
	for i in range(_entries.size()):
		if i > 0:
			append_text("\n")
		append_text(_entries[i])

# ── EventBus Handlers ────────────────────────────────────────────────────────
func _on_combat_log_entry_added(bbcode_text: String) -> void:
	log_message(bbcode_text)

func _on_damage_dealt(target_id: String, amount: int, current_hp: int) -> void:
	append_entry("DANO", "%s sofreu %d de dano! (HP restante: %d)" % [target_id, amount, current_hp])

func _on_dice_rolled(source_id: String, dice_type: String, results: Array) -> void:
	append_entry("DADOS", "%s rolou %s: %s" % [source_id, dice_type, str(results)])

func _on_wall_breached(wall_id: String) -> void:
	append_entry("BRECHA!", "A muralha %s foi destruída! Invasão liberada!" % wall_id)

func _on_synergy_triggered(synergy_type: String, bonus_description: String) -> void:
	append_entry("SINERGIA", "Sinergia de %s ativada: %s" % [synergy_type, bonus_description])

func _on_supreme_synchrony_triggered(crystals_awarded: int) -> void:
	append_entry("SUPREMA", "SINCRONIA SUPREMA ALCANÇADA! +%d Cristais concedidos à Fortaleza!" % crystals_awarded)

func _exit_tree() -> void:
	var tree: SceneTree = get_tree()
	if tree != null and tree.root.has_node("EventBus"):
		var eb: Node = tree.root.get_node("EventBus")
		if eb.has_signal("combat_log_entry_added") and eb.combat_log_entry_added.is_connected(_on_combat_log_entry_added):
			eb.combat_log_entry_added.disconnect(_on_combat_log_entry_added)
		if eb.has_signal("damage_dealt") and eb.damage_dealt.is_connected(_on_damage_dealt):
			eb.damage_dealt.disconnect(_on_damage_dealt)
		if eb.has_signal("dice_rolled") and eb.dice_rolled.is_connected(_on_dice_rolled):
			eb.dice_rolled.disconnect(_on_dice_rolled)
		if eb.has_signal("wall_breached") and eb.wall_breached.is_connected(_on_wall_breached):
			eb.wall_breached.disconnect(_on_wall_breached)
		if eb.has_signal("synergy_triggered") and eb.synergy_triggered.is_connected(_on_synergy_triggered):
			eb.synergy_triggered.disconnect(_on_synergy_triggered)
		if eb.has_signal("supreme_synchrony_triggered") and eb.supreme_synchrony_triggered.is_connected(_on_supreme_synchrony_triggered):
			eb.supreme_synchrony_triggered.disconnect(_on_supreme_synchrony_triggered)
