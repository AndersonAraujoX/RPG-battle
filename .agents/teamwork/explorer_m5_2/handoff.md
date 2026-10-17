# Handoff Report — Milestone M5: Cigarra Ressonante & Rainha do Enxame

**Agent**: Explorer M5-2  
**Target Milestone**: M5 (Conteúdo Ato II: Túneis Vivos — Chefes e Mini-Chefes)  
**Assigned Scope**: Design completo de classes GDScript, métodos, máquina de estados e especificações de testes GUT para:
1. `godot_project/scripts/entities/bosses/CigarraRessonante.gd` (Elite Mini-Boss)
2. `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd` (Chefe do Ato II)
3. Suítes de testes unitários GUT com padrão estrito Arrange-Act-Assert (AAA), segurança headless (bare-node) e zero memory leaks.

---

## 1. Observation

A análise minuciosa da base de código e da documentação canônica revelou os seguintes fatos estruturais e mecânicos:

1. **Documento de Game Design (`CAMPANHA_ROGUELIKE.md`)**:
   - Linha 75: *"Mini-Chefe de Elite: 🦗 **Cigarra Ressonante** (`cigarra_ressonante`) — emite ondas sônicas que aplicam Atordoado em área se os heróis ficarem agrupados."*
   - Linhas 76–78: *"Chefe do Ato II: 👑 **Rainha do Enxame** (`rainha_do_enxame`) — Possui habilidade `chamado_da_rainha` (reabastece ninhadas continuamente a cada 2 turnos) e protege-se atrás de guardas reais. O jogador precisa dividir o grupo entre conter a ninhada e focar dano pesado na Rainha."*
   - Linha 78: *"Gancho de Transição (Ato II ➔ Ato III): Antes de morrer, a Rainha libera um grito psíquico: 'Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!'."*

2. **Requisitos de Despacho do Orquestrador (`DISPATCH.md`)**:
   - `CigarraRessonante.gd`: Mini-chefe de elite com 70–90 PV, alta mobilidade (`move_speed >= 4` ou `5`, voadora), habilidade `pulso_sonico` disparando se `>= 2` heróis estiverem agrupados em distância Chebyshev `<= 2`, causando dano em área e infligindo a condição `Atordoado` (`stunned`) por 1 rodada.
   - `RainhaDoEnxame.gd`: Chefe do Ato II com 180–220 PV, passiva de Guarda Real concedendo 50% de redução de dano sofrido enquanto qualquer Guarda Real (`royal_guard`) estiver viva, habilidade `chamado_da_rainha` invocando ninhadas a cada 2 turnos, e gancho narrativo de transição disparado ao ser abatida.

3. **Catálogo Canônico de Castas (`godot_project/scripts/cerco/IsectumCastes.gd`)**:
   - `ID_RAINHA_DO_ENXAME = "rainha_do_enxame"` (Linha 32, 58). Símbolo 👑, Trait `chamado_da_rainha`, ameaça 6, voadora, alcance 2.
   - Aliases mapeiam `cigarra_ressonante` para `ID_GRILO_ATORDOANTE = "grilo_atordoante"` (Linha 30, 56) com trait `pulso_sonico`.
   - Guardas reais canônicos: `ID_ESCARAVELHO_COURACADO = "escaravelho_couracado"` (Linha 40) e `ID_BESOURO_RINOCERONTE = "besouro_rinoceronte"` (Linha 44).
   - Castas de ninhada rápida para invocação: `ID_VESPA_FURTIVA` ("vespa_furtiva"), `ID_LARVA_NECROTICA` ("larva_necrotica"), `ID_ZANGAO_INVASOR` ("zangao_invasor").

4. **Entidade Base de Combate (`godot_project/scripts/entities/Character.gd`)**:
   - Herda de `CharacterBody2D`. Fornece sinais padronizados (`hp_changed`, `damaged`, `healed`, `died`, `status_effect_applied`, `status_effect_removed`, `grid_position_changed`).
   - Gerencia PV de forma estrita com `take_damage(amount: int) -> int` e `heal(amount: int) -> int`.
   - Suporta status conditions via `add_status_effect(effect: String)`, `has_status_effect(effect: String)`, `remove_status_effect(effect: String)`.
   - Métodos visuais (`update_hp_bar`, `_update_selection_tween`) possuem checagens defensivas `if hp_fill == null: return` e `if is_inside_tree()`, tornando classes derivadas totalmente seguras para instanciação direta via `.new()` sem árvore de nós nos testes GUT (*headless bare-node safe*).

5. **Grid Tático e Distância (`godot_project/scripts/tactical/TacticalGrid.gd`)**:
   - A métrica padrão do projeto em combates 20x20 é a distância Chebyshev (`calculate_chebyshev_distance(p1, p2) = maxi(abs(p1.x - p2.x), abs(p1.y - p2.y))`), compatível com as regras de grade do D&D 5e.
   - Fornece métodos de ocupação (`is_cell_occupied`, `place_unit`, `get_unit_at`) e verificação de células caminháveis (`is_cell_walkable`).

6. **Gerenciador de Condições (`godot_project/scripts/combat/StatusManager.gd`)**:
   - Condição canônica registrada: `"stunned"` (Display Name: `"Atordoado"`).
   - Efeito: `blocks_action: true`, `blocks_movement: true`, `grants_attacker_advantage: true`, `auto_fail_str_dex_saves: true`.
   - Duração padrão de controle de grupo rápido: 1 turno (`duration_turns = 1`).

7. **Estrutura de Diretórios (`PROJECT.md`)**:
   - `godot_project/scripts/entities/bosses/` é a pasta oficial para os chefes do jogo (`ReiIsectumBoss.gd`, `CigarraRessonante.gd`, `RainhaDoEnxame.gd`).

---

## 2. Logic Chain

A partir das observações acima, a arquitetura dos dois chefes foi construída segundo a seguinte cadeia lógica:

```
[Character.gd como Base]
   │  (Fornece take_damage, grid_position, signals e status_effects sem duplicar código)
   ├──► [CigarraRessonante.gd]
   │       ├── Atributos: max_hp (70-90, def: 80), move_speed: 5, is_flyer: true, AC: 15
   │       ├── Imunidade: Bloqueia add_status_effect("stunned") e ("atordoado")
   │       └── pulso_sonico():
   │             ├── Varre posições dos heróis vivos
   │             ├── Calcula distância Chebyshev <= 2 em relação ao epicentro
   │             ├── SE contagem >= 2 heróis:
   │             │     ├── Dano em área (2d6 / 10 sônico)
   │             │     └── Aplica status "stunned" (1 rodada) em TODOS os afetados
   │             └── SENÃO (1 herói isolado):
   │                   ├── Dano normal (sem stun)
   │                   └── Retorna relatório tático com status clustered: false
   │
   └──► [RainhaDoEnxame.gd]
           ├── Atributos: max_hp (180-220, def: 200), AC: 16, move_speed: 3, is_boss: true
           ├── Proteção da Guarda Real:
           │     ├── register_royal_guard(guard) e has_living_royal_guard() -> bool
           │     └── take_damage(amount):
           │           SE has_living_royal_guard():
           │               effective_amount = maxi(1, int(amount * 0.5))
           │               emite royal_guard_damage_mitigated(amount, effective_amount)
           │           SENÃO:
           │               effective_amount = amount (100% de dano)
           │           super.take_damage(effective_amount)
           ├── chamado_da_rainha():
           │     ├── Contador de turnos: invoca a cada 2 turnos (turn_counter % 2 == 0)
           │     ├── Localiza células livres adjacentes no TacticalGrid
           │     └── Instancia/configura 2 unidades aladas/ninhadas (Vespa Furtiva / Larva)
           └── Gancho Narrativo na Derrota:
                 ├── Quando current_hp <= 0:
                 │     emite transition_narrative_triggered(quote, hook_data)
                 │     emite boss_defeated(hook_data)
                 └── Frase canônica: "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!"
```

### Justificativas de Design e Princípios SOLID:
1. **Single Responsibility (SRP)**:
   - `CigarraRessonante`: gerencia o estado do mini-boss, a verificação de agrupamento espacial e a execução da habilidade sônica.
   - `RainhaDoEnxame`: gerencia a integridade da monarca, a mitigação por guardas reais, o ciclo temporal de desova da colmeia e o gancho narrativo de epílogo do Ato II.
2. **Open/Closed (OCP)**:
   - Ambas estendem `Character.gd`. Qualquer nova mecânica (como relíquias que alterem a duração de atordoamento ou resistência a dano) conecta-se via polimorfismo ou sinais sem necessidade de alterar o código de infraestrutura do tabuleiro.
3. **Liskov Substitution (LSP)**:
   - Instâncias de `CigarraRessonante` e `RainhaDoEnxame` podem ser passadas para qualquer método que espere `Character` (no `TacticalGrid`, `CercoGameController` ou `RunCombatBridge`).
4. **Interface Segregation & Dependency Injection (ISP & DIP)**:
   - Os métodos `pulso_sonico` e `chamado_da_rainha` aceitam parâmetros opcionais (`grid: TacticalGrid = null`, `rng: RandomNumberGenerator = null`, `heroes: Array = []`). Isso permite que os testes unitários os executem de forma 100% pura e determinística em memória sem precisar carregar a cena inteira do jogo.

---

## 3. Caveats

1. **Dependência de Nós Gráficos nos Testes**:
   `Character.gd` herda de `CharacterBody2D` e define variáveis `@onready var sprite_2d` etc. Quando instanciado de forma bare-node com `.new()`, os nós filhos ainda não foram criados pelo Godot. Tanto `CigarraRessonante` quanto `RainhaDoEnxame` foram desenhados para proteger todas as chamadas visuais com checagens defensivas `if sprite_2d != null:`, permitindo testes ultrarrápidos e sem overhead visual no GUT.
2. **Arredondamento da Redução de 50% de Dano**:
   Para valores ímpares de dano recebido pela Rainha com guardas vivas (ex: 15 de dano), adota-se `int(float(amount) * 0.5)` (ou seja, 7 de dano) com garantia de pelo menos 1 de dano (`maxi(1, ...)`). Dano de 1 resulta em 1 (ou 0 se mitigado totalmente). Isso é testado explicitamente em casos de borda.
3. **Morte Simultânea de Guardas**:
   A lista de guardas reais mantém referências a nós `Character` ou dicionários. O método `get_living_royal_guards()` valida `is_instance_valid(g) and g.is_alive and g.current_hp > 0`. Se uma guarda for liberada (`queue_free()`) ou morrer no mesmo turno, a Rainha reavalia seu estado dinamicamente no momento exato do impacto.

---

## 4. Conclusion & Complete GDScript Implementations

Abaixo estão os códigos GDScript completos, prontos para produção e conformes às diretrizes de qualidade do projeto.

### 4.1. Código da Solução: `godot_project/scripts/entities/bosses/CigarraRessonante.gd`

```gdscript
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
	# Tenta carregar textura específica caso o nó de sprite exista
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
		# Pequena variação determinística: 2d6 (2..12) ou dano base +/- 2
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
				emit_signal("hero_stunned", target.character_id, SONIC_PULSE_STUN_DURATION)
			elif target is Dictionary:
				target["is_stunned"] = true
				target["stun_duration"] = SONIC_PULSE_STUN_DURATION
				targets_stunned.append(str(target.get("id", target.get("name", "alvo"))))
				emit_signal("hero_stunned", str(target.get("id", "alvo")), SONIC_PULSE_STUN_DURATION)

	emit_signal("pulso_sonico_triggered", target_pos, affected, final_damage, is_clustered)

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
	emit_signal("mobility_dash_executed", old_pos, target_cell)
	return true
```

---

### 4.2. Código da Solução: `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd`

```gdscript
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

# ── Sistema de Proteção da Guarda Real (Guarda Real) ─────────────────────────

## Registra uma Guarda Real vinculada à proteção da Rainha.
func register_royal_guard(guard: Variant) -> void:
	if guard == null:
		return
	if not royal_guards.has(guard):
		royal_guards.append(guard)
		emit_signal("royal_guard_registered", guard)
		if guard is Character:
			if not guard.is_connected("died", Callable(self, "_on_royal_guard_died")):
				guard.connect("died", Callable(self, "_on_royal_guard_died").bind(guard))

## Desregistra uma Guarda Real (caso seja removida ou destruída).
func unregister_royal_guard(guard: Variant) -> void:
	if royal_guards.has(guard):
		royal_guards.erase(guard)
		emit_signal("royal_guard_unregistered", guard)

## Limpa todas as guardas registradas.
func clear_royal_guards() -> void:
	royal_guards.clear()

## Callback invocado quando uma Guarda Real perece.
func _on_royal_guard_died(guard: Variant) -> void:
	# Apenas emite notificação ou atualiza estado interno
	emit_signal("royal_guard_unregistered", guard)

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
		# 50% de redução de dano (arredondado para baixo, mínimo 1 de dano se entrada > 1)
		effective_damage = maxi(1, int(float(amount) * ROYAL_GUARD_DAMAGE_MULTIPLIER)) if amount > 1 else maxi(0, int(float(amount) * ROYAL_GUARD_DAMAGE_MULTIPLIER))
		emit_signal("royal_guard_damage_mitigated", amount, effective_damage)

	var actual_damage: int = super.take_damage(effective_damage)

	# Se atingiu 0 PV, dispara o gancho narrativo de transição do Ato II
	if current_hp <= 0 and not narrative_hook_triggered:
		_trigger_transition_narrative()

	return actual_damage

# ── Invocação de Ninhada: Chamado da Rainha (chamado_da_rainha) ───────────────

## Avança o contador de turnos da Rainha.
## A cada 2 turnos (turn_counter % 2 == 0), invoca ninhadas automaticamente.
func advance_turn(grid: TacticalGrid = null, rng: RandomNumberGenerator = null) -> Dictionary:
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
func chamado_da_rainha(grid: TacticalGrid = null, count: int = 2, rng: RandomNumberGenerator = null) -> Array:
	var spawned_brood: Array = []
	var brood_pool: Array[String] = [
		IsectumCastes.ID_VESPA_FURTIVA,
		IsectumCastes.ID_LARVA_NECROTICA,
		IsectumCastes.ID_ZANGAO_INVASOR
	]

	var candidate_cells: Array[Vector2i] = []
	if grid != null and grid_position != Vector2i(-1, -1):
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

	emit_signal("brood_summoned", spawned_brood)

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
	emit_signal("transition_narrative_triggered", NARRATIVE_QUOTE, hook_data)
	emit_signal("boss_defeated", hook_data)

	if is_inside_tree():
		var tree: SceneTree = get_tree()
		if tree != null and tree.root.has_node("EventBus"):
			var eb: Node = tree.root.get_node("EventBus")
			if eb.has_signal("combat_log_entry_added"):
				var log_entry: String = "[b][color=#e74c3c]GRITO PSÍQUICO DA RAINHA:[/color][/b] \"%s\"" % NARRATIVE_QUOTE
				eb.emit_signal("combat_log_entry_added", log_entry)
```

---

### 4.3. Especificação de Testes GUT: `godot_project/test/unit/test_boss_swarm_queen.gd`

```gdscript
# res://test/unit/test_boss_swarm_queen.gd
extends GutTest

## Suíte de Testes Unitários: Chefe Rainha do Enxame (RainhaDoEnxame.gd)
## Marco M5: Valida atributos de boss (180-220 PV), mitigação de 50% por Guardas Reais,
## invocação periódica de ninhada a cada 2 turnos e gancho narrativo de transição.
## Padrão estrito Arrange-Act-Assert (AAA), segurança headless bare-node e zero leaks.

var _queen: RainhaDoEnxame
var _rng: RandomNumberGenerator

func before_each() -> void:
	_queen = autofree(RainhaDoEnxame.new())
	_rng = RandomNumberGenerator.new()
	_rng.seed = 4242

func after_each() -> void:
	_queen = null
	_rng = null

# ── 1. Inicialização & Atributos de Chefe ─────────────────────────────────────

func test_queen_initialization_defaults() -> void:
	# Arrange & Act: já executado no before_each
	
	# Assert
	assert_not_null(_queen, "Rainha instanciada com sucesso")
	assert_gte(_queen.max_hp, 180, "HP máximo deve ser pelo menos 180")
	assert_lte(_queen.max_hp, 220, "HP máximo deve ser no máximo 220")
	assert_eq(_queen.current_hp, _queen.max_hp, "HP atual igual ao máximo")
	assert_eq(_queen.ac, 16, "CA padrão da Rainha é 16")
	assert_eq(_queen.team, "B", "Rainha pertence ao time B (inimigos)")
	assert_true(_queen.is_boss, "Flag is_boss deve ser verdadeira")
	assert_true(_queen.is_alive, "Rainha inicia viva")
	assert_false(_queen.has_living_royal_guard(), "Sem guardas reais inicialmente")

# ── 2. Mecânica de Proteção da Guarda Real (50% de Redução) ──────────────────

func test_royal_guard_registration_and_status() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 30)

	# Act
	_queen.register_royal_guard(guard)

	# Assert
	assert_true(_queen.has_living_royal_guard(), "Deve detectar guarda real viva")
	assert_eq(_queen.get_living_royal_guards().size(), 1, "Exatamente 1 guarda viva")

func test_royal_guard_50_percent_damage_mitigation_when_guard_alive() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 30)
	_queen.register_royal_guard(guard)
	var initial_hp: int = _queen.current_hp
	watch_signals(_queen)

	# Act: Dano de 20 recebido com guarda viva (redução para 10)
	var dealt: int = _queen.take_damage(20)

	# Assert
	assert_eq(dealt, 10, "Dano efetivo deve ser reduzido em 50% (20 -> 10)")
	assert_eq(_queen.current_hp, initial_hp - 10, "HP da Rainha decresce exatamente 10")
	assert_signal_emitted(_queen, "royal_guard_damage_mitigated")

func test_royal_guard_odd_damage_mitigation_edge_case() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 30)
	_queen.register_royal_guard(guard)
	var initial_hp: int = _queen.current_hp

	# Act: Dano ímpar de 15 recebido
	var dealt: int = _queen.take_damage(15)

	# Assert: int(15 * 0.5) = 7
	assert_eq(dealt, 7, "Dano ímpar 15 reduzido em 50% arredonda para 7")
	assert_eq(_queen.current_hp, initial_hp - 7)

func test_normal_100_percent_damage_when_all_guards_are_dead() -> void:
	# Arrange
	var guard: Character = autofree(Character.new())
	guard.setup("guard_1", "Guarda Couraçado", 30)
	_queen.register_royal_guard(guard)
	# Guarda é derrotada
	guard.take_damage(30)
	assert_false(guard.is_alive, "Guarda deve estar morta")
	assert_false(_queen.has_living_royal_guard(), "Rainha não tem guardas vivas")
	var initial_hp: int = _queen.current_hp

	# Act: Dano de 20 recebido sem guardas
	var dealt: int = _queen.take_damage(20)

	# Assert
	assert_eq(dealt, 20, "Dano integral (100%) deve ser aplicado na ausência de guardas")
	assert_eq(_queen.current_hp, initial_hp - 20, "HP decresce em 20")

# ── 3. Chamado da Rainha (chamado_da_rainha) a Cada 2 Turnos ────────────────

func test_chamado_da_rainha_periodic_every_two_turns() -> void:
	# Arrange
	_queen.grid_position = Vector2i(10, 2)
	watch_signals(_queen)

	# Act & Assert - Turno 1 (não invoca)
	var t1: Dictionary = _queen.advance_turn(null, _rng)
	assert_false(t1["summoned"], "Turno 1 não deve invocar ninhadas")
	assert_eq(t1["brood_spawned"].size(), 0)

	# Act & Assert - Turno 2 (invoca!)
	var t2: Dictionary = _queen.advance_turn(null, _rng)
	assert_true(t2["summoned"], "Turno 2 deve disparar o Chamado da Rainha")
	assert_gte(t2["brood_spawned"].size(), 2, "Pelo menos 2 insetos invocados")
	assert_signal_emitted(_queen, "brood_summoned")

	# Act & Assert - Turno 3 (não invoca)
	var t3: Dictionary = _queen.advance_turn(null, _rng)
	assert_false(t3["summoned"], "Turno 3 não deve invocar ninhadas")

	# Act & Assert - Turno 4 (invoca novamente)
	var t4: Dictionary = _queen.advance_turn(null, _rng)
	assert_true(t4["summoned"], "Turno 4 deve disparar invocação")

# ── 4. Gancho Narrativo de Transição (Ato II ➔ Ato III) ──────────────────────

func test_transition_narrative_hook_triggered_upon_defeat() -> void:
	# Arrange
	_queen.clear_royal_guards()
	watch_signals(_queen)

	# Act: Dano letal
	_queen.take_damage(_queen.max_hp + 50)

	# Assert
	assert_false(_queen.is_alive, "Rainha deve estar morta")
	assert_eq(_queen.current_hp, 0, "HP zerado e grampeado")
	assert_true(_queen.narrative_hook_triggered, "Flag de gancho narrativo ativada")
	assert_signal_emitted(_queen, "transition_narrative_triggered")
	assert_signal_emitted(_queen, "boss_defeated")

	var hook: Dictionary = _queen.get_transition_narrative_hook()
	assert_eq(hook["quote"], "Vocês matam a carne, mas a Mente é eterna! Enquanto os Três Corações baterem, o Rei jamais cairá!")
	assert_eq(hook["act_to"], 3, "Transição desbloqueia o Ato III")
```

---

### 4.4. Especificação de Testes GUT: `godot_project/test/unit/test_cigarra_ressonante.gd`

```gdscript
# res://test/unit/test_cigarra_ressonante.gd
extends GutTest

## Suíte de Testes Unitários: Mini-Chefe Cigarra Ressonante (CigarraRessonante.gd)
## Marco M5: Valida HP 70-90, alta mobilidade, imunidade a Atordoamento,
## e pulso_sonico com trigger de agrupamento (>= 2 heróis em distância <= 2).
## Padrão estrito Arrange-Act-Assert (AAA), segurança headless bare-node e zero leaks.

var _cigarra: CigarraRessonante
var _rng: RandomNumberGenerator

func before_each() -> void:
	_cigarra = autofree(CigarraRessonante.new())
	_rng = RandomNumberGenerator.new()
	_rng.seed = 9999

func after_each() -> void:
	_cigarra = null
	_rng = null

# ── 1. Atributos de Elite & Imunidade ─────────────────────────────────────────

func test_cigarra_initialization_defaults() -> void:
	# Arrange & Act: no before_each
	
	# Assert
	assert_not_null(_cigarra, "Cigarra instanciada com sucesso")
	assert_gte(_cigarra.max_hp, 70, "HP mínimo de elite é 70")
	assert_lte(_cigarra.max_hp, 90, "HP máximo de elite é 90")
	assert_gte(_cigarra.move_speed, 4, "Alta mobilidade (velocidade >= 4)")
	assert_true(_cigarra.is_flyer, "Cigarra é unidade voadora")
	assert_true(_cigarra.is_elite, "Flag is_elite deve ser verdadeira")
	assert_eq(_cigarra.team, "B", "Time B (inimigo)")

func test_cigarra_immunity_to_stun_and_atordoado() -> void:
	# Arrange & Act
	var ok_stun: bool = _cigarra.add_status_effect("stunned")
	var ok_ator: bool = _cigarra.add_status_effect("atordoado")
	var ok_burn: bool = _cigarra.add_status_effect("burning")

	# Assert
	assert_false(ok_stun, "Imune a 'stunned'")
	assert_false(ok_ator, "Imune a 'atordoado'")
	assert_false(_cigarra.has_status_effect("stunned"), "Não deve possuir stunned ativo")
	assert_true(ok_burn, "Outras condições (ex: burning) devem funcionar normalmente")

# ── 2. Detecção Espacial de Agrupamento (Chebyshev) ──────────────────────────

func test_clustering_detection_chebyshev_distance() -> void:
	# Arrange
	var center: Vector2i = Vector2i(5, 5)
	var hero_near: Vector2i = Vector2i(7, 6) # dx=2, dy=1 -> chebyshev = 2 (dentro)
	var hero_far: Vector2i = Vector2i(8, 5)  # dx=3, dy=0 -> chebyshev = 3 (fora)

	# Act
	var clustered_heroes: Array = _cigarra.find_clustered_heroes(center, [hero_near, hero_far], 2)

	# Assert
	assert_eq(clustered_heroes.size(), 1, "Apenas o herói dentro do raio 2 é retornado")
	assert_eq(clustered_heroes[0], hero_near)

func test_is_hero_clustered_requires_at_least_two_heroes() -> void:
	# Arrange
	var center: Vector2i = Vector2i(5, 5)
	var h1: Vector2i = Vector2i(5, 6) # d = 1
	var h2: Vector2i = Vector2i(6, 7) # d = 2
	var h3_far: Vector2i = Vector2i(10, 10) # d = 5

	# Act & Assert
	assert_true(_cigarra.is_hero_clustered(center, [h1, h2], 2, 2), "2 heróis no raio = agrupado")
	assert_false(_cigarra.is_hero_clustered(center, [h1, h3_far], 2, 2), "1 herói no raio = não agrupado")

# ── 3. Pulso Sônico: Dano em Área e Atordoamento ──────────────────────────────

func test_pulso_sonico_clustered_applies_aoe_damage_and_stun() -> void:
	# Arrange
	var hero1: Character = autofree(Character.new())
	hero1.setup("aquele", "Aquele", 30)
	hero1.set_grid_position(Vector2i(5, 5))

	var hero2: Character = autofree(Character.new())
	hero2.setup("stark", "Stark", 30)
	hero2.set_grid_position(Vector2i(6, 6))

	watch_signals(_cigarra)

	# Act: Pulso disparado no centro (5, 5) pegando ambos
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [hero1, hero2], _rng)

	# Assert
	assert_true(res["success"], "Ataque sônico bem sucedido")
	assert_true(res["clustered"], "Detectou agrupamento (>= 2 heróis)")
	assert_true(res["stun_applied"], "Aplicou atordoamento")
	assert_eq(res["duration"], 1, "Duração do atordoamento é 1 rodada")
	assert_gt(res["damage_dealt"], 0, "Dano positivo")

	assert_lt(hero1.current_hp, 30, "Hero 1 sofreu dano")
	assert_lt(hero2.current_hp, 30, "Hero 2 sofreu dano")
	assert_true(hero1.has_status_effect("stunned"), "Hero 1 está atordoado")
	assert_true(hero2.has_status_effect("stunned"), "Hero 2 está atordoado")
	assert_signal_emitted(_cigarra, "pulso_sonico_triggered")

func test_pulso_sonico_unclustered_deals_damage_without_stun() -> void:
	# Arrange: Apenas 1 herói isolado
	var hero_solo: Character = autofree(Character.new())
	hero_solo.setup("elden", "Elden", 30)
	hero_solo.set_grid_position(Vector2i(5, 5))

	# Act
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [hero_solo], _rng)

	# Assert
	assert_true(res["success"], "Ataque sônico disparado")
	assert_false(res["clustered"], "Não agrupado (apenas 1 herói)")
	assert_false(res["stun_applied"], "NÃO aplica atordoamento em herói isolado")
	assert_false(hero_solo.has_status_effect("stunned"), "Herói isolado livre de stun")
	assert_lt(hero_solo.current_hp, 30, "Herói isolado ainda recebe o dano")

func test_pulso_sonico_empty_or_dead_heroes_edge_case() -> void:
	# Arrange: Herói morto
	var dead_hero: Character = autofree(Character.new())
	dead_hero.setup("morto", "Herói Caído", 30)
	dead_hero.take_damage(30)
	dead_hero.set_grid_position(Vector2i(5, 5))

	# Act
	var res: Dictionary = _cigarra.pulso_sonico(Vector2i(5, 5), [dead_hero], _rng)

	# Assert
	assert_false(res["success"], "Herói morto não constitui alvo válido")
	assert_eq(res["targets_hit"].size(), 0)
```

---

## 5. Verification Method

Para verificar de forma independente e reproduzível a corretude das especificações e dos códigos propostos:

1. **Inspeção Estática dos Arquivos de Design**:
   - Verificar conformidade das classes com `Character.gd` e `IsectumCastes.gd`.
   - Confirmar que as constantes `DEFAULT_MAX_HP`, `DEFAULT_AC`, `NARRATIVE_QUOTE` e `SONIC_PULSE_RADIUS` conferem exatamente com `CAMPANHA_ROGUELIKE.md` e o despacho.

2. **Execução da Suíte de Testes GUT (Linha de Comando)**:
   Após a criação dos arquivos pelo agente implementador em:
   - `godot_project/scripts/entities/bosses/CigarraRessonante.gd`
   - `godot_project/scripts/entities/bosses/RainhaDoEnxame.gd`
   - `godot_project/test/unit/test_cigarra_ressonante.gd`
   - `godot_project/test/unit/test_boss_swarm_queen.gd`

   Executar:
   ```bash
   bash godot_project/run_gut_tests.sh -gselect=test_boss_swarm_queen.gd
   bash godot_project/run_gut_tests.sh -gselect=test_cigarra_ressonante.gd
   ```

3. **Critérios de Sucesso e Condições de Invalidação**:
   - **Critério 1**: 100% dos testes GUT passam com 0 falhas, 0 warnings críticos e 0 memory leaks (`autofree`).
   - **Critério 2**: A Rainha do Enxame mitiga rigorosamente 50% de dano quando `royal_guard` está viva e 0% (dano integral) quando todas estão mortas.
   - **Critério 3**: A Cigarra Ressonante aplica `stunned` em área **apenas** quando `>= 2` heróis estiverem em distância Chebyshev `<= 2`. Heróis isolados sofrem dano sem atordoamento.
   - **Condição de Invalidação**: Qualquer falha de compilação headless, vazamento de instâncias na ObjectDB do Godot ou divergência na citação do gancho narrativo de epílogo do Ato II invalida esta especificação.
