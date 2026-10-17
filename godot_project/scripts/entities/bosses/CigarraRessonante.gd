# res://scripts/entities/bosses/CigarraRessonante.gd
class_name CigarraRessonante
extends Character

## Elite Mini-Boss: Cigarra Ressonante (Ato II: Túneis Vivos)
## Monstro de elite com alta mobilidade e ataque sônico em área (pulso_sonico).
## Aplica a condição Atordoado (Stun) por 1 rodada caso 2 ou mais heróis estejam
## agrupados em distância Chebyshev <= 2. Possui imunidade nativa a Atordoamento.

# ── Sinais de Combate ─────────────────────────────────────────────────────────
signal pulso_sonico_triggered(center_pos: Vector2i, affected_targets: Array, damage: int, stunned: bool)
signal hero_stunned(hero_id: String, duration: int)
signal mobility_dash_executed(from_pos: Vector2i, to_pos: Vector2i)

# ── Constantes Canônicas ─────────────────────────────────────────────────────
const DEFAULT_MAX_HP: int = 80
const MIN_ALLOWED_HP: int = 70
const MAX_ALLOWED_HP: int = 90
const DEFAULT_AC: int = 15
const DEFAULT_SPEED: int = 5
const DEFAULT_ATTACK_RANGE: int = 3
const SONIC_PULSE_RADIUS: int = 2
const SONIC_PULSE_CLUSTER_THRESHOLD: int = 2
const SONIC_PULSE_STUN_DURATION: int = 1
const SONIC_PULSE_BASE_DAMAGE: int = 10

# ── Propriedades Específicas de Elite ─────────────────────────────────────────
@export var is_flyer: bool = true
@export var is_elite: bool = true
@export var sonic_pulse_radius: int = SONIC_PULSE_RADIUS
@export var sonic_pulse_cluster_min: int = SONIC_PULSE_CLUSTER_THRESHOLD
@export var sonic_pulse_damage: int = SONIC_PULSE_BASE_DAMAGE
@export var caste_id: String = "cigarra_ressonante"

# ── Inicialização & Lifecycle ────────────────────────────────────────────────

func _init() -> void:
	character_id = "cigarra_ressonante"
	character_name = "Cigarra Ressonante"
	team = "B"
	max_hp = DEFAULT_MAX_HP
	current_hp = DEFAULT_MAX_HP
	ac = DEFAULT_AC
	move_speed = DEFAULT_SPEED
	attack_range = DEFAULT_ATTACK_RANGE
	damage_type = "Trovão"
	is_alive = true

func _ready() -> void:
	super._ready()
	if sprite_2d != null and sprite_2d.texture == null:
		load_texture_for_character("cigarra_ressonante")

# ── Imunidade a Atordoamento ─────────────────────────────────────────────────

## Sobrescreve add_status_effect para garantir imunidade a Atordoado / Stunned.
func add_status_effect(effect: String) -> bool:
	var eff: String = effect.to_lower().strip_edges()
	if eff == "stunned" or eff == "atordoado":
		return false
	return super.add_status_effect(effect)

# ── Lógica de Agrupamento Espacial (Clustering) ──────────────────────────────

## Calcula a distância de Chebyshev entre duas coordenadas do grid 20x20.
func calculate_chebyshev_distance(p1: Vector2i, p2: Vector2i) -> int:
	return maxi(abs(p1.x - p2.x), abs(p1.y - p2.y))

## Extrai a posição no grid de um objeto herói (Character, Dictionary ou Vector2i).
func _extract_position(hero: Variant) -> Vector2i:
	if hero is Vector2i:
		return hero
	elif hero is Character:
		return hero.grid_position
	elif hero is Dictionary:
		if hero.has("grid_position") and hero["grid_position"] is Vector2i:
			return hero["grid_position"]
		elif hero.has("spawn_pos") and hero["spawn_pos"] is Vector2i:
			return hero["spawn_pos"]
		elif hero.has("pos") and hero["pos"] is Vector2i:
			return hero["pos"]
		elif hero.has("x") and hero.has("y"):
			return Vector2i(int(hero["x"]), int(hero["y"]))
	return Vector2i(-1, -1)

## Verifica se o herói está vivo para fins de alvo.
func _is_hero_alive(hero: Variant) -> bool:
	if hero is Character:
		return hero.is_alive and hero.current_hp > 0
	elif hero is Dictionary:
		return int(hero.get("hp", hero.get("current_hp", 1))) > 0
	return true

## Localiza todos os heróis vivos que estão a uma distância <= radius de center_pos.
func find_clustered_heroes(center_pos: Vector2i, heroes: Array, radius: int = SONIC_PULSE_RADIUS) -> Array:
	var result: Array = []
	for h in heroes:
		if not _is_hero_alive(h):
			continue
		var pos: Vector2i = _extract_position(h)
		if pos == Vector2i(-1, -1):
			continue
		if calculate_chebyshev_distance(center_pos, pos) <= radius:
			result.append(h)
	return result

## Avalia se a condição de agrupamento (>= cluster_threshold heróis num raio <= radius) é satisfeita.
func is_hero_clustered(center_pos: Vector2i, heroes: Array, radius: int = SONIC_PULSE_RADIUS, min_cluster: int = SONIC_PULSE_CLUSTER_THRESHOLD) -> bool:
	var clustered: Array = find_clustered_heroes(center_pos, heroes, radius)
	return clustered.size() >= min_cluster

## Varre todos os heróis vivos para encontrar o epicentro que atinge o maior número de alvos agrupados.
func scan_best_pulse_target(heroes: Array, radius: int = SONIC_PULSE_RADIUS, min_cluster: int = SONIC_PULSE_CLUSTER_THRESHOLD) -> Dictionary:
	var best_epicenter: Vector2i = Vector2i(-1, -1)
	var best_targets: Array = []
	var max_count: int = 0

	for candidate in heroes:
		if not _is_hero_alive(candidate):
			continue
		var center: Vector2i = _extract_position(candidate)
		if center == Vector2i(-1, -1):
			continue
		var cluster: Array = find_clustered_heroes(center, heroes, radius)
		if cluster.size() > max_count:
			max_count = cluster.size()
			best_epicenter = center
			best_targets = cluster

	var is_valid: bool = max_count >= min_cluster
	return {
		"valid_cluster": is_valid,
		"epicenter": best_epicenter,
		"targets": best_targets,
		"count": max_count
	}

# ── Habilidade Principal: Pulso Sônico (pulso_sonico) ────────────────────────

## Executa o Pulso Sônico contra um ponto focal.
## Se houver >= 2 heróis vivos num raio <= 2:
##   - Causa dano em área (sonic_pulse_damage)
##   - Aplica a condição 'stunned' por 1 rodada em todos os atingidos.
## Se houver apenas 1 herói isolado:
##   - Causa dano simples, mas NÃO aplica atordoamento.
## Se houver 0 heróis:
##   - Retorna falha sem dano ou atordoamento.
func pulso_sonico(target_pos: Vector2i, heroes: Array, rng: RandomNumberGenerator = null) -> Dictionary:
	var affected: Array = find_clustered_heroes(target_pos, heroes, sonic_pulse_radius)
	var count: int = affected.size()

	if count == 0:
		return {
			"success": false,
			"clustered": false,
			"targets_hit": [],
			"damage_dealt": 0,
			"stun_applied": false,
			"duration": 0,
			"message": "Nenhum alvo no raio do Pulso Sônico."
		}

	var is_clustered: bool = count >= sonic_pulse_cluster_min
	var final_damage: int = sonic_pulse_damage
	if rng != null:
		final_damage = rng.randi_range(maxi(1, sonic_pulse_damage - 2), sonic_pulse_damage + 2)

	var targets_damaged: Array = []
	var targets_stunned: Array = []

	for target in affected:
		# Aplicação de Dano
		if target is Character:
			target.take_damage(final_damage)
			targets_damaged.append(target.character_id if not target.character_id.is_empty() else target.character_name)
		elif target is Dictionary:
			var cur_hp: int = int(target.get("hp", target.get("current_hp", 0)))
			target["hp"] = maxi(0, cur_hp - final_damage)
			target["current_hp"] = target["hp"]
			targets_damaged.append(str(target.get("id", target.get("name", "alvo"))))

		# Aplicação de Atordoamento (Apenas se agrupados)
		if is_clustered:
			if target is Character:
				target.add_status_effect("stunned")
				targets_stunned.append(target.character_id if not target.character_id.is_empty() else target.character_name)
				hero_stunned.emit(target.character_id, SONIC_PULSE_STUN_DURATION)
			elif target is Dictionary:
				target["is_stunned"] = true
				target["stun_duration"] = SONIC_PULSE_STUN_DURATION
				targets_stunned.append(str(target.get("id", target.get("name", "alvo"))))
				hero_stunned.emit(str(target.get("id", "alvo")), SONIC_PULSE_STUN_DURATION)

	pulso_sonico_triggered.emit(target_pos, affected, final_damage, is_clustered)

	# Notificação no EventBus se disponível
	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("combat_log_entry_added"):
				var log_text: String = "[color=#f1c40f]🦗 Cigarra Ressonante disparou PULSO SÔNICO! %d heróis atingidos (%d de dano). %s[/color]" % [
					count,
					final_damage,
					"Atordoado por 1 rodada!" if is_clustered else "Alvo isolado (sem atordoamento)."
				]
				eb.emit_signal("combat_log_entry_added", log_text)

	return {
		"success": true,
		"clustered": is_clustered,
		"epicenter": target_pos,
		"targets_hit": targets_damaged,
		"damage_dealt": final_damage,
		"stun_applied": is_clustered,
		"targets_stunned": targets_stunned,
		"duration": SONIC_PULSE_STUN_DURATION if is_clustered else 0,
		"message": "Pulso sônico executado com sucesso."
	}

# ── Alta Mobilidade: Revoada & Salto Cinético ────────────────────────────────

## Reposiciona a Cigarra no grid mantendo alcance 3 para ataque sônico.
func reposition_high_mobility(target_cell: Vector2i) -> bool:
	if grid_position == target_cell:
		return false
	var old_pos: Vector2i = grid_position
	set_grid_position(target_cell)
	mobility_dash_executed.emit(old_pos, target_cell)
	return true
