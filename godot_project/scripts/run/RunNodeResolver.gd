# res://scripts/run/RunNodeResolver.gd
class_name RunNodeResolver
extends RefCounted

## Estratégia que resolve o conteúdo de um nó do mapa.
## IMPORTANTE: combates aqui são *auto-resolvidos* (placeholder do M1/M2).
## No marco M4, uma subclasse/estratégia que abre o combate tático real substituirá
## resolve_combat() — por isso o resolver é injetado no RunMapScreen.

const CAMPFIRE_HEAL_PCT: float = 0.30
const EVENT_GOLD: int = 20
const EVENT_DAMAGE: int = 5

## Tabela: tipo -> [dano_min, dano_max, ouro, abates]
const COMBAT_TABLE: Dictionary = {
	RunNode.NodeType.COMBAT: [2, 8, 15, 3],
	RunNode.NodeType.SIEGE: [3, 10, 20, 5],
	RunNode.NodeType.ELITE: [5, 12, 30, 1],
	RunNode.NodeType.BOSS: [8, 15, 50, 1],
}

## Resolve o nó atual do state e o marca como concluído.
## Retorna { ok: bool, log: Array[String] }.
func resolve(state: RunState, rng: RandomNumberGenerator) -> Dictionary:
	var result: Dictionary = {"ok": false, "log": []}
	if state == null or rng == null or not state.is_active():
		result["log"].append("Nada a resolver.")
		return result
	var node: RunNode = state.get_current_node()
	if node == null or node.visited:
		result["log"].append("Nenhum nó pendente.")
		return result

	var log_lines: Array = result["log"]
	match node.type:
		RunNode.NodeType.CAMPFIRE:
			state.heal_party_percent(CAMPFIRE_HEAL_PCT)
			log_lines.append("Fogueira: o grupo descansa e recupera 30% do HP.")
		RunNode.NodeType.FORGE:
			log_lines.append("Forja anã: o mercado abrirá no próximo marco (M3).")
		RunNode.NodeType.EVENT:
			_resolve_event(state, rng, log_lines)
		_:
			resolve_combat(state, node, rng, log_lines)

	# O combate pode ter derrotado o grupo; só conclui se a run segue ativa.
	if state.is_active():
		state.complete_current_node()
	result["ok"] = true
	return result

## Ponto de extensão para o combate tático real.
func resolve_combat(state: RunState, node: RunNode, rng: RandomNumberGenerator, log_lines: Array) -> void:
	var row: Array = COMBAT_TABLE.get(node.type, COMBAT_TABLE[RunNode.NodeType.COMBAT])
	var living: Array[String] = state.get_living_heroes()
	if living.is_empty():
		return
	var target: String = living[rng.randi_range(0, living.size() - 1)]
	var dmg: int = rng.randi_range(int(row[0]), int(row[1]))
	state.damage_hero(target, dmg)
	log_lines.append("%s: %s sofreu %d de dano." % [node.get_type_name(), target, dmg])
	if not state.is_active():
		log_lines.append("O grupo caiu...")
		return
	state.add_gold(int(row[2]))
	state.register_kills(int(row[3]))
	log_lines.append("Vitória! +%d ouro." % int(row[2]))
	if node.type == RunNode.NodeType.ELITE:
		var relic_id: String = "reliquia_elite_a%d_%d" % [node.act, node.id]
		if state.add_relic(relic_id):
			log_lines.append("Relíquia obtida: %s" % relic_id)

func _resolve_event(state: RunState, rng: RandomNumberGenerator, log_lines: Array) -> void:
	if rng.randi_range(0, 1) == 0:
		state.add_gold(EVENT_GOLD)
		log_lines.append("Evento: um anão resgatado entrega %d de ouro." % EVENT_GOLD)
	else:
		var living: Array[String] = state.get_living_heroes()
		var target: String = living[rng.randi_range(0, living.size() - 1)]
		state.damage_hero(target, EVENT_DAMAGE)
		log_lines.append("Evento: armadilha de seda! %s sofre %d de dano." % [target, EVENT_DAMAGE])
