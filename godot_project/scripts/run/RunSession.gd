# res://scripts/run/RunSession.gd
class_name RunSession
extends RefCounted

## Contêiner estático da run em andamento, compartilhado entre cenas
## (evita adicionar um novo Autoload ao projeto).

const DEFAULT_PARTY: Dictionary = {"aquele": 30, "stark": 34, "elden": 26}
const DEFAULT_DECK: Array[String] = [
	"movimento", "movimento", "movimento",
	"trabalho", "trabalho",
	"escavacao", "escavacao",
	"ataque", "ataque", "defesa",
]

static var current: RunState = null

static func has_active_run() -> bool:
	return current != null and current.is_active()

static func start_new(p_seed: int, party: Dictionary = DEFAULT_PARTY, deck: Array[String] = DEFAULT_DECK) -> RunState:
	var state: RunState = RunState.new()
	if not state.start_run(party, deck, p_seed):
		return null
	current = state
	return state

static func clear() -> void:
	current = null
