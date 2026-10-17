# res://scripts/entities/bosses/ReiIsectum.gd
class_name ReiIsectum
extends Character

## Chefe Final do Ato III: O REI DOS ISECTUM (Colmeia-Mãe)
## Ocupa 3x3 tiles, imune a empurrões e condições mentais/venenosas.
## Batalha épica estruturada em 3 fases (450 PV total):
##   - Fase 1 (450 -> 300 PV): O Soberano no Trono (Vantagem de elevação, Comando Absoluto, Lança de Âmbar).
##   - Fase 2 (300 -> 150 PV): A Muralha Viva (Miasma nas bordas, Rugido Feromônico, Esmagamento Colossal).
##   - Fase 3 (150 -> 0 PV): Coroa Quebrada (Frenesi 2 ações/turno, Fraqueza 2x a Fogo, Devorar Essência).
##
## Responde diretamente à destruição dos 3 Corações da Colmeia:
##   - coracao_da_mente: Desativa controle mental no início.
##   - coracao_da_carapaca: Reduz CA de 19 para 16.
##   - coracao_da_ninhada: Impede invocar guardas na Fase 2.

# ── Sinais de Combate & Eventos de Fase ───────────────────────────────────────
signal phase_changed(new_phase: int, old_phase: int)
signal screen_shake_requested(intensity: float, duration: float)
signal miasma_expanded(affected_cells: Array)
signal absolute_command_executed(target_guards: Array)
signal amber_spear_fired(origin: Vector2i, target: Vector2i, obstacle_created: Vector2i)
signal pheromonic_roar_executed(affected_heroes: Array)
signal colossal_slam_executed(center: Vector2i, damaged_cells: Array, damage: int)
signal devour_essence_attempted(target_hero: Character, healed: int)
signal heart_debuffs_applied(debuff_info: Dictionary)
signal boss_defeated(victory_data: Dictionary)
signal throne_pillars_damaged(damage: int, remaining_hp: int)
signal throne_collapsed()

# ── Fases da Batalha ──────────────────────────────────────────────────────────
enum Phase {
	THRONE_PHASE_1 = 1,
	LIVING_WALL_PHASE_2 = 2,
	BROKEN_CROWN_PHASE_3 = 3,
}

# ── Constantes Canônicas ──────────────────────────────────────────────────────
const DEFAULT_MAX_HP: int = 450
const PHASE_1_HP_THRESHOLD: int = 300
const PHASE_2_HP_THRESHOLD: int = 150
const DEFAULT_AC: int = 19
const HEART_CARAPACE_AC: int = 16
const PHASE_3_AC_PENALTY: int = 3
const DEFAULT_SPEED: int = 2
const DEFAULT_ATTACK_RANGE: int = 2
const THRONE_PILLARS_MAX_HP: int = 60
const DEVOUR_ESSENCE_HEAL: int = 40
const COLOSSAL_SLAM_BASE_DAMAGE: int = 25
const PHEROMONIC_ROAR_DC: int = 14
const GRID_SIZE: Vector2i = Vector2i(3, 3)

const IMMUNE_STATUSES: Array[String] = [
	"envenenado",
	"poisoned",
	"atordoado",
	"stunned",
]

# ── Propriedades do Chefe ─────────────────────────────────────────────────────
@export var is_boss: bool = true
@export var caste_id: String = "rei_isectum"
@export var current_phase: int = Phase.THRONE_PHASE_1
@export var has_elevation_advantage: bool = true
@export var throne_pillars_hp: int = THRONE_PILLARS_MAX_HP
@export var throne_collapsed_flag: bool = false
@export var actions_per_turn: int = 1
@export var actions_remaining_this_turn: int = 1
@export var turn_counter: int = 0
@export var immune_to_displacement: bool = true

# Modificadores dos 3 Corações
@export var heart_mind_destroyed: bool = false
@export var heart_carapace_destroyed: bool = false
@export var heart_brood_destroyed: bool = false

var royal_guards: Array = []

# ── Inicialização & Lifecycle ─────────────────────────────────────────────────

func _init() -> void:
	character_id = "rei_isectum"
	character_name = "Rei dos Isectum"
	team = "B"
	max_hp = DEFAULT_MAX_HP
	current_hp = DEFAULT_MAX_HP
	ac = DEFAULT_AC
	move_speed = DEFAULT_SPEED
	attack_range = DEFAULT_ATTACK_RANGE
	damage_type = "Contundente"
	is_alive = true
	current_phase = Phase.THRONE_PHASE_1
	has_elevation_advantage = true
	throne_pillars_hp = THRONE_PILLARS_MAX_HP
	throne_collapsed_flag = false
	actions_per_turn = 1
	actions_remaining_this_turn = 1
	turn_counter = 0
	immune_to_displacement = true
	royal_guards.clear()

func _ready() -> void:
	super._ready()
	if sprite_2d != null and sprite_2d.texture == null:
		load_texture_for_character("rei_isectum")

# ── Tamanho 3x3 & Imunidade a Empurrões ────────────────────────────────────────

func is_immune_to_push() -> bool:
	return immune_to_displacement

func get_occupied_tiles(origin: Vector2i = Vector2i(-1, -1)) -> Array[Vector2i]:
	var base_pos: Vector2i = origin if origin != Vector2i(-1, -1) else grid_position
	var tiles: Array[Vector2i] = []
	for dx in range(GRID_SIZE.x):
		for dy in range(GRID_SIZE.y):
			tiles.append(Vector2i(base_pos.x + dx, base_pos.y + dy))
	return tiles

func is_point_inside(pt: Vector2i) -> bool:
	var occupied: Array[Vector2i] = get_occupied_tiles()
	return occupied.has(pt)

# ── Imunidades a Condições ────────────────────────────────────────────────────

func is_immune_to_condition(condition_name: String) -> bool:
	return IMMUNE_STATUSES.has(condition_name.to_lower().strip_edges())

func add_status_effect(effect: String) -> bool:
	if is_immune_to_condition(effect):
		return false
	return super.add_status_effect(effect)

# ── Modificadores dos 3 Corações ──────────────────────────────────────────────

## Aplica os efeitos permanentes da destruição prévia dos 3 Corações da Colmeia.
func apply_heart_debuffs(destroyed_hearts: Array) -> Dictionary:
	heart_mind_destroyed = destroyed_hearts.has("coracao_da_mente")
	heart_carapace_destroyed = destroyed_hearts.has("coracao_da_carapaca")
	heart_brood_destroyed = destroyed_hearts.has("coracao_da_ninhada")

	# Coração da Carapaça: Reduz CA de 19 para 16
	if heart_carapace_destroyed:
		ac = HEART_CARAPACE_AC

	var summary: Dictionary = {
		"mind_disabled": heart_mind_destroyed,
		"carapace_weakened": heart_carapace_destroyed,
		"brood_blocked": heart_brood_destroyed,
		"current_ac": ac,
	}
	heart_debuffs_applied.emit(summary)
	return summary

# ── Resolução de Dano & Transição de Fases ─────────────────────────────────────

func take_damage(amount: int, damage_element: String = "") -> int:
	if amount <= 0 or not is_alive or current_hp <= 0:
		return 0

	var effective_damage: int = amount

	# Fraqueza Elemental: Na Fase 3 (Coroa Quebrada), o núcleo exposto sofre 2x de dano por Fogo
	if current_phase == Phase.BROKEN_CROWN_PHASE_3:
		var elem_norm: String = damage_element.to_lower().strip_edges()
		if elem_norm == "fogo" or elem_norm == "fire":
			effective_damage *= 2

	var actual_damage: int = mini(effective_damage, current_hp)
	current_hp -= actual_damage

	update_hp_bar()
	hp_changed.emit(current_hp, max_hp)
	damaged.emit(actual_damage, current_hp)

	# Global EventBus
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("unit_damaged"):
				eb.emit_signal("unit_damaged", character_id, actual_damage, current_hp, max_hp)

	_evaluate_phase_transitions()

	if current_hp <= 0:
		is_alive = false
		current_hp = 0
		died.emit()
		boss_defeated.emit({
			"boss_id": "rei_isectum",
			"amber_reward": 25,
			"victory": true,
		})
		if is_inside_tree():
			var tree: SceneTree = get_tree()
			if tree != null and tree.root.has_node("EventBus"):
				var eb: Node = tree.root.get_node("EventBus")
				if eb.has_signal("unit_died"):
					eb.emit_signal("unit_died", character_id)

	return actual_damage

func _evaluate_phase_transitions() -> void:
	if current_hp <= 0:
		return

	if current_hp <= PHASE_2_HP_THRESHOLD and current_phase != Phase.BROKEN_CROWN_PHASE_3:
		_transition_to_phase(Phase.BROKEN_CROWN_PHASE_3)
	elif current_hp <= PHASE_1_HP_THRESHOLD and current_phase == Phase.THRONE_PHASE_1:
		_transition_to_phase(Phase.LIVING_WALL_PHASE_2)

func _transition_to_phase(target_phase: int) -> void:
	var old_phase: int = current_phase
	current_phase = target_phase

	match target_phase:
		Phase.LIVING_WALL_PHASE_2:
			has_elevation_advantage = false
			screen_shake_requested.emit(12.0, 0.6)
		Phase.BROKEN_CROWN_PHASE_3:
			has_elevation_advantage = false
			ac = maxi(ac - PHASE_3_AC_PENALTY, 10)
			actions_per_turn = 2
			actions_remaining_this_turn = 2
			screen_shake_requested.emit(16.0, 0.8)

	phase_changed.emit(current_phase, old_phase)

# ── Habilidades da Fase 1: Trono de Âmbar ─────────────────────────────────────

## Escavação dos pilares de sustentação do Trono (via cartas ou ações dos heróis).
func excavate_throne_pillars(damage: int) -> bool:
	if throne_collapsed_flag or current_phase != Phase.THRONE_PHASE_1:
		return false
	if damage <= 0:
		return false

	throne_pillars_hp = maxi(throne_pillars_hp - damage, 0)
	throne_pillars_damaged.emit(damage, throne_pillars_hp)

	if throne_pillars_hp <= 0:
		throne_collapsed_flag = true
		has_elevation_advantage = false
		throne_collapsed.emit()
		screen_shake_requested.emit(8.0, 0.5)
		return true
	return false

## Habilidade: Comando Absoluto
## Ordena que até 2 Guardas Reais realizem um ataque imediato.
func execute_absolute_command(guards: Array) -> Array:
	var ordered: Array = []
	for g in guards:
		if g == null:
			continue
		var alive: bool = false
		if g is Character:
			alive = is_instance_valid(g) and g.is_alive and g.current_hp > 0
		elif g is Dictionary:
			alive = int(g.get("hp", g.get("current_hp", 0))) > 0
		if alive:
			ordered.append(g)
			if ordered.size() >= 2:
				break

	absolute_command_executed.emit(ordered)
	return ordered

## Habilidade: Lança de Âmbar
## Disparo que cristaliza o tile atingido, gerando um obstáculo no tabuleiro.
func execute_amber_spear(target_pos: Vector2i) -> Dictionary:
	var result: Dictionary = {
		"origin": grid_position,
		"target": target_pos,
		"obstacle_created": target_pos,
		"damage": 15,
	}
	amber_spear_fired.emit(grid_position, target_pos, target_pos)
	return result

# ── Habilidades da Fase 2: Muralha Viva ───────────────────────────────────────

## Calcula os tiles de borda tomados pelo miasma ácido da arena dinâmica.
func get_miasma_border_cells(board_size: int = 20, ring_depth: int = 1) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for depth in range(ring_depth):
		var min_coord: int = depth
		var max_coord: int = board_size - 1 - depth
		for x in range(min_coord, max_coord + 1):
			cells.append(Vector2i(x, min_coord))
			cells.append(Vector2i(x, max_coord))
		for y in range(min_coord + 1, max_coord):
			cells.append(Vector2i(min_coord, y))
			cells.append(Vector2i(max_coord, y))

	miasma_expanded.emit(cells)
	return cells

## Habilidade: Rugido Feromônico
## Afeta heróis em cone; quem falhar no teste de CD sofre redução de mobilidade (Medo).
func execute_pheromonic_roar(heroes: Array, test_dc: int = PHEROMONIC_ROAR_DC) -> Array:
	var affected: Array = []
	for h in heroes:
		if h == null:
			continue
		var is_living: bool = false
		if h is Character:
			is_living = is_instance_valid(h) and h.is_alive and h.current_hp > 0
		elif h is Dictionary:
			is_living = int(h.get("hp", h.get("current_hp", 0))) > 0

		if is_living:
			affected.append(h)
			if h is Character:
				h.add_status_effect("Medo")

	pheromonic_roar_executed.emit(affected)
	return affected

## Habilidade: Esmagamento Colossal
## Salto que racha o piso em área 3x3 em torno de center_pos, causando alto dano contundente.
func execute_colossal_slam(target_center: Vector2i, all_units: Array, damage: int = COLOSSAL_SLAM_BASE_DAMAGE) -> Dictionary:
	var damaged_cells: Array[Vector2i] = []
	for dx in range(-1, 2):
		for dy in range(-1, 2):
			damaged_cells.append(Vector2i(target_center.x + dx, target_center.y + dy))

	var hit_units: Array = []
	for u in all_units:
		if u == null or u == self:
			continue
		var u_pos: Vector2i = Vector2i(-1, -1)
		if u is Character:
			u_pos = u.grid_position
		elif u is Dictionary:
			u_pos = u.get("grid_position", u.get("spawn_pos", Vector2i(-1, -1)))

		if damaged_cells.has(u_pos):
			hit_units.append(u)
			if u is Character and is_instance_valid(u) and u.is_alive:
				u.take_damage(damage)

	colossal_slam_executed.emit(target_center, damaged_cells, damage)
	return {
		"center": target_center,
		"cells": damaged_cells,
		"damage": damage,
		"hit_units": hit_units,
	}

## Invocação de Guardas Reais na Fase 2 (bloqueada se Coração da Ninhada foi destruído).
func summon_royal_guard(spawn_pos: Vector2i) -> Dictionary:
	if heart_brood_destroyed:
		return {}

	var guard: Dictionary = {
		"caste_id": "escaravelho_couracado",
		"name": "Guarda Real do Rei",
		"hp": 30,
		"max_hp": 30,
		"ac": 16,
		"spawn_pos": spawn_pos,
		"is_royal_guard": true,
	}
	royal_guards.append(guard)
	return guard

# ── Habilidades da Fase 3: Coroa Quebrada ──────────────────────────────────────

## Habilidade Letal: Devorar Essência
## Se um herói adjacente estiver caído (0 PV / Death Saves), o Rei o consome curando 40 PV.
func execute_devour_essence(adjacent_heroes: Array) -> Character:
	if current_phase != Phase.BROKEN_CROWN_PHASE_3:
		return null

	var target_to_devour: Character = null
	for h in adjacent_heroes:
		if h is Character and is_instance_valid(h):
			if h.current_hp <= 0 or not h.is_alive:
				target_to_devour = h
				break

	if target_to_devour != null:
		heal(DEVOUR_ESSENCE_HEAL)
		devour_essence_attempted.emit(target_to_devour, DEVOUR_ESSENCE_HEAL)

	return target_to_devour

## Reseta o contador de ações no início do turno do chefe.
func start_turn() -> void:
	turn_counter += 1
	actions_remaining_this_turn = actions_per_turn

func consume_action() -> bool:
	if actions_remaining_this_turn > 0:
		actions_remaining_this_turn -= 1
		return true
	return false
