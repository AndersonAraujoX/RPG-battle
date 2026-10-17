# res://scripts/entities/bosses/RainhaDoEnxame.gd
class_name RainhaDoEnxame
extends Character

## Chefe do Ato II: Rainha do Enxame (Túneis Vivos)
## Monarca da colmeia subterrânea. Possui:
## 1. 180 a 220 PV e carapaça protegida por Guardas Reais (50% de redução de dano).
## 2. Invocação periódica de ninhada a cada 2 turnos (chamado_da_rainha).
## 3. Disparo do gancho narrativo de transição para o Ato III ao ser abatida.

# ── Sinais de Combate & Eventos Narrativos ────────────────────────────────────
signal royal_guard_registered(guard: Variant)
signal royal_guard_unregistered(guard: Variant)
signal royal_guard_damage_mitigated(incoming_damage: int, reduced_damage: int)
signal brood_summoned(spawned_units: Array)
signal transition_narrative_triggered(quote: String, hook_data: Dictionary)
signal boss_defeated(hook_data: Dictionary)

# ── Constantes Canônicas ─────────────────────────────────────────────────────
const DEFAULT_MAX_HP: int = 200
const MIN_ALLOWED_HP: int = 180
const MAX_ALLOWED_HP: int = 220
const DEFAULT_AC: int = 16
const DEFAULT_SPEED: int = 3
const DEFAULT_ATTACK_RANGE: int = 2
const SUMMON_INTERVAL_TURNS: int = 2
const ROYAL_GUARD_DAMAGE_MULTIPLIER: float = 0.5
const NARRATIVE_QUOTE: String = "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"

# ── Propriedades do Chefe ────────────────────────────────────────────────────
@export var is_boss: bool = true
@export var summon_cooldown_max: int = SUMMON_INTERVAL_TURNS
@export var turn_counter: int = 0
@export var caste_id: String = "rainha_do_enxame"
@export var narrative_hook_triggered: bool = false

# Coleção de instâncias de Guardas Reais sob comando da Rainha
var royal_guards: Array = []

# ── Inicialização & Lifecycle ────────────────────────────────────────────────

func _init() -> void:
	character_id = "rainha_do_enxame"
	character_name = "Rainha do Enxame"
	team = "B"
	max_hp = DEFAULT_MAX_HP
	current_hp = DEFAULT_MAX_HP
	ac = DEFAULT_AC
	move_speed = DEFAULT_SPEED
	attack_range = DEFAULT_ATTACK_RANGE
	damage_type = "Ácido"
	is_alive = true
	turn_counter = 0
	narrative_hook_triggered = false
	royal_guards.clear()

func _ready() -> void:
	super._ready()
	if sprite_2d != null and sprite_2d.texture == null:
		load_texture_for_character("rainha_do_enxame")

# ── Sistema de Proteção da Guarda Real ───────────────────────────────────────

## Registra uma Guarda Real vinculada à proteção da Rainha.
func register_royal_guard(guard: Variant) -> void:
	if guard == null:
		return
	if not royal_guards.has(guard):
		royal_guards.append(guard)
		royal_guard_registered.emit(guard)
		if guard is Character:
			if not guard.is_connected("died", Callable(self, "_on_royal_guard_died")):
				guard.connect("died", Callable(self, "_on_royal_guard_died").bind(guard))

## Desregistra uma Guarda Real (caso seja removida ou destruída).
func unregister_royal_guard(guard: Variant) -> void:
	if royal_guards.has(guard):
		royal_guards.erase(guard)
		royal_guard_unregistered.emit(guard)

## Limpa todas as guardas registradas.
func clear_royal_guards() -> void:
	royal_guards.clear()

## Callback invocado quando uma Guarda Real perece.
func _on_royal_guard_died(guard: Variant) -> void:
	royal_guard_unregistered.emit(guard)

## Retorna a lista de todas as Guardas Reais que ainda estão vivas.
func get_living_royal_guards() -> Array:
	var living: Array = []
	for g in royal_guards:
		if g == null:
			continue
		if g is Character:
			if is_instance_valid(g) and g.is_alive and g.current_hp > 0:
				living.append(g)
		elif g is Dictionary:
			if int(g.get("hp", g.get("current_hp", 0))) > 0:
				living.append(g)
	return living

## Retorna verdadeiro se houver pelo menos uma Guarda Real viva no tabuleiro.
func has_living_royal_guard() -> bool:
	return get_living_royal_guards().size() > 0

# ── Resolução de Dano com Proteção da Guarda Real ─────────────────────────────

## Aplica dano com redução de 50% se houver Guarda Real viva.
func take_damage(amount: int) -> int:
	if amount <= 0 or not is_alive or current_hp <= 0:
		return 0

	var effective_damage: int = amount
	var guard_present: bool = has_living_royal_guard()

	if guard_present:
		# 50% de redução de dano (arredondado para baixo)
		effective_damage = int(float(amount) * ROYAL_GUARD_DAMAGE_MULTIPLIER)
		royal_guard_damage_mitigated.emit(amount, effective_damage)

	var actual_damage: int = super.take_damage(effective_damage)

	# Se atingiu 0 PV, dispara o gancho narrativo de transição do Ato II
	if current_hp <= 0 and not narrative_hook_triggered:
		_trigger_transition_narrative()

	return actual_damage

# ── Invocação de Ninhada: Chamado da Rainha (chamado_da_rainha) ───────────────

## Avança o contador de turnos da Rainha.
## A cada 2 turnos (turn_counter % 2 == 0), invoca ninhadas automaticamente.
func advance_turn(grid: Variant = null, rng: RandomNumberGenerator = null) -> Dictionary:
	turn_counter += 1
	var should_summon: bool = (turn_counter % summon_cooldown_max == 0)
	var spawned: Array = []

	if should_summon:
		spawned = chamado_da_rainha(grid, 2, rng)

	return {
		"turn": turn_counter,
		"summoned": should_summon,
		"brood_spawned": spawned,
		"turns_until_next": 1 if not should_summon else summon_cooldown_max
	}

## Executa a invocação de ninhada da Rainha, instanciando até `count` novos insetos.
func chamado_da_rainha(grid: Variant = null, count: int = 2, rng: RandomNumberGenerator = null) -> Array:
	var spawned_brood: Array = []
	var brood_pool: Array[String] = [
		IsectumCastes.ID_VESPA_FURTIVA,
		IsectumCastes.ID_LARVA_NECROTICA,
		IsectumCastes.ID_ZANGAO_INVASOR
	]

	var candidate_cells: Array[Vector2i] = []
	if grid != null and grid_position != Vector2i(-1, -1) and grid.has_method("is_valid_cell"):
		# Varre células adjacentes livres em raio Chebyshev 1 e 2
		for dx in [-2, -1, 0, 1, 2]:
			for dy in [-2, -1, 0, 1, 2]:
				if dx == 0 and dy == 0:
					continue
				var check_pos: Vector2i = grid_position + Vector2i(dx, dy)
				if grid.is_valid_cell(check_pos) and grid.is_cell_walkable(check_pos) and not grid.is_cell_occupied(check_pos):
					candidate_cells.append(check_pos)
	else:
		# Posições de fallback determinísticas
		candidate_cells = [
			grid_position + Vector2i(-1, 0),
			grid_position + Vector2i(1, 0),
			grid_position + Vector2i(0, -1),
			grid_position + Vector2i(0, 1)
		]

	for i in range(count):
		var caste: String = brood_pool[i % brood_pool.size()]
		if rng != null:
			caste = brood_pool[rng.randi() % brood_pool.size()]

		var spawn_pos: Vector2i = grid_position
		if not candidate_cells.is_empty():
			spawn_pos = candidate_cells.pop_front()

		var unit_dict: Dictionary = {
			"id": "brood_t%d_%d" % [turn_counter, i + 1],
			"caste_id": caste,
			"name": "Ninhada da Rainha",
			"team": "B",
			"hp": 4,
			"max_hp": 4,
			"ac": 12,
			"move_range": 3,
			"attack_range": 1,
			"attack_bonus": 2,
			"spawn_pos": spawn_pos,
			"is_brood": true
		}
		spawned_brood.append(unit_dict)

	brood_summoned.emit(spawned_brood)

	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("combat_log_entry_added"):
				eb.emit_signal(
					"combat_log_entry_added",
					"[color=#e74c3c]👑 A Rainha do Enxame emite seu CHAMADO DA RAINHA! %d novas ninhadas eclodem![/color]" % spawned_brood.size()
				)

	return spawned_brood

# ── Gancho Narrativo de Transição (Ato II ➔ Ato III) ─────────────────────────

## Retorna os metadados do gancho narrativo de transição.
func get_transition_narrative_hook() -> Dictionary:
	return {
		"boss_id": "rainha_do_enxame",
		"boss_name": character_name,
		"quote": NARRATIVE_QUOTE,
		"act_from": 2,
		"act_to": 3,
		"narrative_trigger": "psionic_shriek_death",
		"target_mechanic": "tres_coracoes_colmeia",
		"dialogue_entries": [
			{
				"speaker": "Rainha do Enxame",
				"style": "grito_psiquico",
				"text": NARRATIVE_QUOTE
			}
		]
	}

## Dispara os sinais de vitória e transição narrativa ao zerar os PVs.
func _trigger_transition_narrative() -> void:
	narrative_hook_triggered = true
	var hook_data: Dictionary = get_transition_narrative_hook()
	transition_narrative_triggered.emit(NARRATIVE_QUOTE, hook_data)
	boss_defeated.emit(hook_data)

	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("combat_log_entry_added"):
				var log_entry: String = "[b][color=#e74c3c]GRITO PSÍQUICO DA RAINHA:[/color][/b] \"%s\"" % NARRATIVE_QUOTE
				eb.emit_signal("combat_log_entry_added", log_entry)
