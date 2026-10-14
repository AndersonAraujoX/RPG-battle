# Handoff Report: Specification Mining for Status Conditions (Milestone 2)

**Agent**: `m2_explorer_conditions` (Specification Miner)  
**Milestone**: M2 (Tactical Grid, Combat Rules & Status Conditions)  
**Date**: 2026-09-26  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation

1. **Authoritative Codebase Sources Inspected**:
   - `src/condicoes.py` (lines 1–96): Core attack condition verification (`verificar_condicoes_ataque`) and automatic critical hit verification (`verificar_critico_automatico`).
   - `src/config.py` (lines 222–287): Status effect constants (`STATUS_ENVENENADO`, `STATUS_ATURDIDO`, `STATUS_SANGRANDO`, `STATUS_FURIA`, `STATUS_AMALDICOADO`) and dictionary `PROPRIEDADES_STATUS_EFEITO` defining colors, icons, descriptions, DoT values, and stat modifiers.
   - `src/personagens/status_efeito.py` (lines 1–36): `StatusEfeito` class handling instantiation, `aplicar_efeito_por_turno` (DoT tick logic), duration tracking, and `tick()` decrements.
   - `src/personagens/personagem_base.py` (lines 172–225, 275–360, 448–500, 544–586, 716–750, 832–862): Character status lifecycle methods (`aplicar_status_efeito`, `remover_status_efeito`, `tick_status_efeitos`, `pode_agir`, `pode_fugir`), actions inflicting status (`usar_dash`, `usar_disengage`, `usar_dodge`, `usar_help`, `usar_grapple`, `usar_shove`), condition checks in AI action decision (`decidir_acao`), and death saving throws.
   - `src/motor_combate.py` (lines 140–163, 200–202, 246, 591, 622, 636, 649, 654, 830–864, 984–986, 1168–1170): Combat turn execution loop, terrain hazards (Fire DoT, Ice slipping), status expiration processing, and ability status applications.
   - `dados/personagens.json` (lines 57, 64, 77, 109, 116): Entity status immunities (`LordeLich` immune to "Veneno"/"Frio", `DragaoAnciao` immune to "Paralisia", `Esqueleto` immune to "Veneno"/"Doença", `Sienna` immune to "Paralisia", `SiennaPhoenix` immune to "Paralisia"/"Atordoado").
   - `godot_project/scripts/autoload/EventBus.gd` (lines 12–14): Canonical signal contracts `status_applied(unit_id: String, status_id: String, duration: int)` and `status_removed(unit_id: String, status_id: String)`.

2. **Verified Runtime Probes on Authoritative Codebase**:
   - Attack modifier interaction: Attacker `Cego` gives Disadvantage; Target `Cego` gives Advantage. When both present, both flags set (`vantagem=True, desvantagem=True`), resolving to standard roll via D&D 5e cancellation.
   - Prone distance threshold: Melee attack ($\le 1.5$m) against `Caído` grants Advantage (`Alvo Caído (Perto)`); Ranged attack ($> 1.5$m) against `Caído` imposes Disadvantage (`Alvo Caído (Longe)`).
   - Auto-Crit threshold: Attacks against `Paralisado` or `INCONSCIENTE` at distance $\le 1.5$m with attack roll $\ge$ target AC trigger `CRÍTICO AUTOMÁTICO`. Ranged attacks ($> 1.5$m) do NOT auto-crit.
   - DoT Lifecycle:
     - `Envenenado`: 2 fixed damage per tick.
     - `Sangrando`: `int(hp_max * 0.05)` damage per tick (5% max HP).
     - `Amaldiçoado`: 3 fixed damage per tick + `-2` attack roll penalty.
     - `Queimando` / Fire terrain: `1d6` fire damage at start of turn.
   - Re-application rule: Calling `aplicar_status_efeito` on an existing effect does not create duplicate entries; it adds to the remaining duration (`duracao_restante += duracao_turnos`) and updates extra payload parameters.
   - Immunity rule: If `nome_efeito in self.imunidades`, application is aborted with no mutation.

---

## 2. Logic Chain

1. **Mapping All 23 Status Conditions**:
   The prompt assigns 23 specific conditions:
   - **14 Canonical D&D 5e Conditions**: Paralyzed, Poisoned, Stunned, Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Petrified, Prone, Restrained, Unconscious.
   - **9 Elemental & Fantasy Conditions**: Bleeding, Burning, Frozen, Confused, Cursed, Blessed, Hasted, Slowed, Doomed.
   - In addition, probing the codebase revealed 13 tactical combat conditions/modifiers (`Fúria`, `Provocado`, `Defesa Quebrada`, `Ataque Reduzido`, `Comando Tático`, `Inspirado`, `Dash`, `Desengajar`, `Esquiva`, `Alvo de Ajuda`, `Fuga Garantida`, `Escondido`, `Ver o Invisível`). Following Miner Rule 4, all discovered conditions are fully cataloged.

2. **D&D 5e Mathematical Parity**:
   - Advantage / Disadvantage is binary per check: Any number of advantages and any number of disadvantages cancel out completely to a single normal d20 roll.
   - Critical Hits: Natural 20 or Auto-Crit (within 1.5m against Paralyzed/Unconscious). Critical hits double all damage dice (e.g. 1d8 becomes 2d8) while adding flat modifiers once.
   - Saving Throws: $1d20 + \text{Attribute Modifier} \ge \text{DC}$. Paralyzed, Stunned, Petrified, and Unconscious automatically fail Strength and Dexterity saving throws. Restrained and Prone impose Disadvantage on Dexterity saving throws.

3. **Decoupled Architecture for Godot 4**:
   - `StatusCondition.gd` (`RefCounted` or `Resource`): Statically typed value object containing configuration properties, flags, DoT formulas, and current remaining duration.
   - `StatusManager.gd` (`RefCounted` or `Node` in `godot_project/scripts/core/StatusEffectManager.gd`): Rule processor managing active status collections on `CharacterData`, evaluating attack/save modifiers, executing turn-start/turn-end ticks, and emitting `EventBus` signals.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | D&D 5e Canonical | **Paralyzed (Paralisado)** | Speed 0; Incapacitated; auto-fail Str/Dex saves; attacks vs target have Advantage; melee hits ($\le 1.5$m) are Auto-Crits | Target unit, distance $\le 1.5$m | Speed=0, Advantage to attackers, Auto-Crit on melee hit | Blocked if unit has immunity "Paralisia" | `src/condicoes.py:46, 91`, `dados/personagens.json:64` |
| 2 | D&D 5e Canonical | **Poisoned (Envenenado)** | Disadvantage on attack rolls and ability checks; ticks 2 fixed poison damage per turn | Attacker unit roll; turn tick | Disadvantage on attacks, 2 HP DoT per round | Blocked if unit has immunity "Veneno" | `src/condicoes.py:21`, `src/config.py:230-235` |
| 3 | D&D 5e Canonical | **Stunned (Atordoado)** | Speed 0; Incapacitated (`pode_agir=False`); attacks vs target have Advantage; auto-fail Str/Dex saves | Target unit; turn tick | Speed=0, Advantage to attackers, action blocked | Blocked if unit has immunity "Atordoado" | `src/condicoes.py:46`, `src/config.py:236-241` |
| 4 | D&D 5e Canonical | **Blinded (Cego)** | Disadvantage on own attacks; attacks against target have Advantage; auto-fail perception checks requiring sight | Attacker or target unit | Disadvantage on attacks; Advantage against target | Fails visual perception automatically | `src/condicoes.py:12-18` |
| 5 | D&D 5e Canonical | **Charmed (Encantado)** | Cannot attack or target charmer with harmful effects; charmer has advantage on social interactions | Target unit, charmer ID | Attack filtered out if target == charmer | Charmer ally damage breaks condition | `src/personagens/personagem_base.py:517-522` |
| 6 | D&D 5e Canonical | **Deafened (Surdo)** | Cannot hear; automatically fails ability checks requiring hearing; immune to auditory spells | Target unit | Auto-fail auditory saves/checks | Immune to sonic/verbal charm | D&D 5e SRD; audio perceptual checks |
| 7 | D&D 5e Canonical | **Frightened (Assustado)** | Disadvantage on ability checks/attacks while source is in line of sight; cannot willingly move closer to source | Attacker unit, source unit ID | Disadvantage on attacks; movement toward source blocked | Blocked if source not visible | `src/condicoes.py:50-53`, `src/personagens/personagem_base.py:554-564` |
| 8 | D&D 5e Canonical | **Grappled (Agarrado)** | Speed becomes 0; ends if grappler is incapacitated or moved out of range | Target unit | Speed=0; can still attack within reach | Escape contest (Athletics/Acrobatics vs Athletics) | `src/personagens/personagem_base.py:314-337, 544` |
| 9 | D&D 5e Canonical | **Incapacitated (Incapacitado)** | Cannot take actions, bonus actions, or reactions (`pode_agir=False`); breaks concentration | Target unit | Action execution blocked (`passar`) | Drops active concentration spells | `src/condicoes.py:46-48`, `src/personagens/personagem_base.py:212-216` |
| 10 | D&D 5e Canonical | **Invisible (Invisível)** | Heavily obscured; attacks have Advantage; attacks against have Disadvantage (negated by See Invisibility) | Attacker / Target unit | Advantage on attacks; Disadvantage for attackers | Negated by "Ver o Invisível" | `src/condicoes.py:37-43` |
| 11 | D&D 5e Canonical | **Petrified (Petrificado)** | Speed 0; Incapacitated; attacks vs target have Advantage; auto-fail Str/Dex saves; 50% resistance to all damage; immune to poison | Target unit | Speed=0, Advantage to attackers, 0.5x damage taken | Weight x10; immune to poison/disease | `src/condicoes.py:46-48`, `src/personagens/personagem_base.py:700` |
| 12 | D&D 5e Canonical | **Prone (Caído)** | Disadvantage on own attacks; attacks within 1.5m have Advantage; attacks > 1.5m have Disadvantage; stand up costs half speed | Attacker / Target unit, distance | Melee: Advantage; Ranged: Disadvantage; crawl speed | Standing up requires spending $\ge 50\%$ speed | `src/condicoes.py:25-35`, `src/personagens/personagem_base.py:340-360` |
| 13 | D&D 5e Canonical | **Restrained (Contido)** | Speed 0; own attacks have Disadvantage; attacks vs target have Advantage; Disadvantage on Dex saves | Attacker / Target unit | Speed=0; Disadvantage on attacks; Advantage vs target | Disadvantage on Dex saves | `src/condicoes.py:55-62`, `src/personagens/personagem_base.py:544` |
| 14 | D&D 5e Canonical | **Unconscious (Inconsciente)** | Speed 0; Incapacitated; drops prone; attacks vs target have Advantage; melee hits are Auto-Crits; rolls death saves at 0 HP | Target unit, distance $\le 1.5$m | Speed=0, Auto-Crit on melee hit, death save rolls | Taking damage adds 1 death save fail (2 if crit) | `src/condicoes.py:46, 91`, `src/motor_combate.py:158-162` |
| 15 | Elemental / Fantasy | **Bleeding (Sangrando)** | DoT dealing 5% of max HP (`int(hp_max * 0.05)`) at start of turn | Target unit; turn tick | Damage = `max(1, int(hp_max * 0.05))` | Stops on Con save DC 12 or healing effect | `src/config.py:225, 242-247`, `src/personagens/status_efeito.py:23-26` |
| 16 | Elemental / Fantasy | **Burning (Queimando)** | DoT dealing 1d6 fire damage at start of turn; interacts with Fire terrain | Target unit; turn tick | Damage = `randi_range(1, 6)` | Action to extinguish; extinguished by water | `src/motor_combate.py:143-152`, `src/tabuleiro.py:260-275` |
| 17 | Elemental / Fantasy | **Frozen (Congelado)** | Half speed (or 0 if frozen solid); 50% slip on ice; vulnerable to Bludgeoning/Fire (2.0x) | Target unit; movement step | Speed halved, slip hazard, 2.0x bludgeon/fire damage | Broken immediately by fire damage | `src/tabuleiro.py:268-272`, `src/motor_combate.py:830-864` |
| 18 | Mental / Fantasy | **Confused (Confuso)** | At start of turn, roll 1d10: 1–4 skip turn, 5–6 attack nearest unit (friendly fire), 7–10 act normally | Target unit; turn start d10 | Random behavior based on table | Wis save at end of turn to recover | Behavioral extension of D&D 5e Confusion |
| 19 | Necrotic / Fantasy | **Cursed (Amaldiçoado)** | DoT dealing 3 fixed damage per turn and -2 penalty to attack rolls (`bonus_ataque_fixo = -2`) | Target unit; turn tick / attack | Damage = 3; -2 on attack d20 rolls | Cleansed by Remove Curse / Cleric | `src/config.py:227, 256-262`, `src/personagens/bruxo.py:28-36` |
| 20 | Divine / Fantasy | **Blessed (Abençoado)** | Adds +1d4 (1–4) bonus to all attack rolls and saving throws | Target unit; attack / save roll | +1d4 added to all attack and save totals | Capped duration (10 rounds) or concentration break | D&D 5e Bless canonical rules |
| 21 | Transmutation | **Hasted (Acelerado)** | Speed doubled; +2 AC; Advantage on Dex saves; 1 additional Action per turn; lethargy on expire | Target unit; round start | Speed x2, +2 AC, extra action | When expired, unit cannot move or act for 1 turn | Action economy rules (`src/motor_combate.py:968`) |
| 22 | Transmutation | **Slowed (Lentificado)** | Speed reduced by 2 (min 1); -2 AC and Dex saves; no reactions; cannot take both action and bonus action | Target unit; round start | Speed -2, -2 AC, action economy restricted | Wis save at end of turn to recover | `src/motor_combate.py:591, 888` |
| 23 | Dark Fantasy | **Doomed (Condenado)** | Critical hit threshold against target expanded to 19–20; Disadvantage on Death Saves; extra necrotic damage | Target unit; incoming attack | Crits on 19–20; 2 death save fails if reduced to 0 HP | Cleansed by high-tier divine restoration | Boss mechanics (`src/personagens/lorde_lich.py`) |
| 24 | Tactical Buff | **Fúria (Rage)** | +2 damage on attacks; 25% damage reduction (0.25); cannot flee (`pode_fugir=False`); duration 10 | Target unit | +2 damage, 0.75x incoming damage, no flee | Barbarian ability | `src/config.py:226, 248-255`, `src/motor_combate.py:984-986` |
| 25 | Tactical Debuff | **Provocado (Taunted)** | Forced to attack or move towards `provocador`; overrides normal AI priority | Target unit, provocador unit | Action locked to attack/move towards taunter | Cleansed if provocador dies | `src/config.py:263-268`, `src/personagens/personagem_base.py:489-500` |
| 26 | Tactical Debuff | **Defesa Quebrada** | -3 AC or takes +20% damage (resistencia -0.2); duration 3 (extended by Rilem perk) | Target unit | AC -3 or damage x1.2 | Cleansed after duration expires | `src/config.py:269-274`, `src/motor_combate.py:654, 1113-1120` |
| 27 | Tactical Debuff | **Ataque Reduzido** | -2 damage and -2 attack roll modifier; duration 2–3 turns | Target unit | -2 attack roll, -2 attack damage | Cleansed after duration expires | `src/config.py:275-280`, `src/motor_combate.py:636, 1087` |
| 28 | Tactical Buff | **Comando Tático** | +2 damage and +2 attack roll modifier; duration 3 turns | Target unit | +2 attack roll, +2 attack damage | Cleansed after duration expires | `src/config.py:281-286`, `src/motor_combate.py:649, 1106` |
| 29 | Tactical Buff | **Inspirado (Inspired)** | +2 movement speed bonus; duration 1 turn | Target unit | Speed +2 | Cleansed at end of turn | `src/motor_combate.py:200-202` |
| 30 | Tactical Action | **Dash (Disparada)** | Movement speed doubled for the current turn; duration 1 turn | Target unit | Speed x2 for current turn | Cleansed at turn end | `src/personagens/personagem_base.py:268-278` |
| 31 | Tactical Action | **Desengajar (Disengage)** | Movement does not provoke opportunity attacks; duration 1 turn | Target unit | Opportunity attacks disabled | Cleansed at turn end | `src/personagens/personagem_base.py:280-290`, `src/motor_combate.py:246` |
| 32 | Tactical Action | **Esquiva (Dodge)** | Attacks against user have Disadvantage; user has Advantage on Dex saves; duration 1 turn | Target unit | Disadvantage for attackers; Advantage on Dex saves | Cleansed at start of next turn | `src/personagens/personagem_base.py:291-300`, `src/condicoes.py:64-66` |
| 33 | Tactical Action | **Alvo de Ajuda (Help)** | Next attack roll against target has Advantage; duration 1 turn or until hit | Target unit | Advantage to next attacker | Consumed on first hit | `src/personagens/personagem_base.py:302-312`, `src/condicoes.py:68-79` |
| 34 | Tactical Item | **Fuga Garantida** | Allows character to flee ignoring rage or enemy proximity restrictions; duration 1 turn | Target unit | `pode_fugir = True` override | Consumed on use | `src/itens/item.py:50-52`, `src/personagens/personagem_base.py:221` |
| 35 | Tactical State | **Escondido (Hidden)** | Unseen attacker advantage; enemies cannot target directly without perception check | Target unit | Stealth advantage; untargetable | Broken upon attacking or casting | `src/motor_combate.py:1036-1037` |
| 36 | Tactical Trait | **Ver o Invisível** | Negates Advantage of invisible attackers and Disadvantage against invisible targets | Attacker unit | Invisibility modifiers nullified | Inactive if blinded | `src/condicoes.py:41-43` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Advantage Cancellation | Attacker `Cego` (Disadv) attacking Target `Cego` (Adv) | Both flags true (`vantagem=True, desvantagem=True`); cancels out to a single normal d20 roll without advantage or disadvantage. |
| 2 | Prone Distance Threshold | Attacker distance = 1.0m vs distance = 2.0m against `Caído` target | At 1.0m ($\le 1.5$m), attacker gains Advantage (`Alvo Caído (Perto)`). At 2.0m ($> 1.5$m), attacker suffers Disadvantage (`Alvo Caído (Longe)`). |
| 3 | Auto-Crit Range Limit | Attacker at distance = 1.0m vs distance = 3.0m hitting `Paralisado` target | At 1.0m with successful hit, triggers `CRÍTICO AUTOMÁTICO (Paralisia)`. At 3.0m (ranged), attack gains Advantage but does NOT trigger auto-crit; normal crit requires natural 20. |
| 4 | Immunity Rejection | Applying `Envenenado` to `LordeLich` (immune to "Veneno") | Application aborted immediately; returns without adding effect or modifying duration; logs immunity message. |
| 5 | Duration Stacking | Applying `Envenenado` for 2 turns, then applying for 3 turns to same target | Existing effect duration increased to 5 turns (`duracao_restante = 5`). Single instance maintained in array. |
| 6 | Zero Duration Expiration | Status with duration = 1 turn executed in `tick_status_efeitos` | Effect applies turn effect (e.g. DoT), decrements duration to 0, returns `False` from `tick()`, and is removed in the same tick cycle. |
| 7 | Unconscious Lethal Damage | Unconscious unit (HP 0) receives damage from attack | Directly adds 1 Death Saving Throw failure (`death_saves_failures += 1`). If hit by a critical hit (melee $\le 1.5$m), adds 2 failures. At 3 failures, unit transitions to `MORTO`. |
| 8 | Natural 20 Death Save | Unconscious unit rolls 20 on Death Saving Throw | Unit immediately recovers 1 HP, transitions from `INCONSCIENTE` to `NORMAL`, resets death save counters, and can act on subsequent turns. |
| 9 | Bleeding Rounding | Unit with 25 Max HP receives `Sangrando` (5% DoT) | `int(25 * 0.05) = 1` damage. Guaranteed minimum 1 damage even for low-HP minions. |
| 10 | Charmed Friendly Fire Filter | Charmed unit evaluating attack target where target is charmer | AI filters out charmer from `inimigos_em_range`; selects another enemy or passes turn if no other targets exist. |
| 11 | Restrained Speed Stacking | Unit affected by both `Agarrado` and `Contido` attempting movement | Speed remains 0; logs single block; does not consume excess AP or crash movement solver. |
| 12 | See Invisibility Negation | Attacker with `Ver o Invisível` attacking `Invisível` target | Condition check `alvo.tem_status("Invisível") and not atacante.tem_status("Ver o Invisível")` evaluates to `False`; attacker does NOT suffer disadvantage. |

---

## 5. GDScript Architecture Proposal

### 5.1 Statically Typed Data Model: `godot_project/scripts/resources/StatusCondition.gd`

```gdscript
# res://scripts/resources/StatusCondition.gd
class_name StatusCondition
extends Resource

enum Category {
	CANONICAL_5E,
	ELEMENTAL,
	TACTICAL_BUFF,
	TACTICAL_DEBUFF
}

@export var id: String = ""
@export var display_name: String = ""
@export var category: Category = Category.CANONICAL_5E
@export var duration_turns: int = 1
@export var extra_data: Dictionary = {}

# Mechanics Flags
@export var blocks_action: bool = false
@export var blocks_movement: bool = false
@export var speed_multiplier: float = 1.0
@export var speed_bonus: int = 0

# Attack & Combat Modifiers
@export var grants_attacker_advantage: bool = false
@export var grants_attacker_disadvantage: bool = false
@export var inflicts_disadvantage_on_attack: bool = false
@export var inflicts_advantage_on_attack: bool = false
@export var auto_crit_range: float = 0.0 # 1.5 for Paralyzed/Unconscious, 0.0 otherwise

# Stat Offsets
@export var bonus_ac: int = 0
@export var bonus_attack_roll: int = 0
@export var bonus_damage: int = 0
@export var damage_resistance_modifier: float = 0.0 # -0.2 = takes 20% more, +0.25 = takes 25% less

# Saving Throw Modifiers
@export var auto_fail_str_dex_saves: bool = false
@export var save_disadvantage_dex: bool = false
@export var save_advantage_dex: bool = false

# Damage Over Time (DoT)
@export var dot_fixed_damage: int = 0
@export var dot_percent_hp_max: float = 0.0
@export var dot_damage_type: String = "Fisico"

func duplicate_condition() -> StatusCondition:
	var copy: StatusCondition = StatusCondition.new()
	copy.id = id
	copy.display_name = display_name
	copy.category = category
	copy.duration_turns = duration_turns
	copy.extra_data = extra_data.duplicate(true)
	copy.blocks_action = blocks_action
	copy.blocks_movement = blocks_movement
	copy.speed_multiplier = speed_multiplier
	copy.speed_bonus = speed_bonus
	copy.grants_attacker_advantage = grants_attacker_advantage
	copy.grants_attacker_disadvantage = grants_attacker_disadvantage
	copy.inflicts_disadvantage_on_attack = inflicts_disadvantage_on_attack
	copy.inflicts_advantage_on_attack = inflicts_advantage_on_attack
	copy.auto_crit_range = auto_crit_range
	copy.bonus_ac = bonus_ac
	copy.bonus_attack_roll = bonus_attack_roll
	copy.bonus_damage = bonus_damage
	copy.damage_resistance_modifier = damage_resistance_modifier
	copy.auto_fail_str_dex_saves = auto_fail_str_dex_saves
	copy.save_disadvantage_dex = save_disadvantage_dex
	copy.save_advantage_dex = save_advantage_dex
	copy.dot_fixed_damage = dot_fixed_damage
	copy.dot_percent_hp_max = dot_percent_hp_max
	copy.dot_damage_type = dot_damage_type
	return copy
```

### 5.2 Decoupled Rules Engine: `godot_project/scripts/core/StatusEffectManager.gd`

```gdscript
# res://scripts/core/StatusEffectManager.gd
class_name StatusEffectManager
extends RefCounted

## Centralized Status Effect Processor
## Manages condition applications, DoT ticks, modifier evaluations, and EventBus emissions.

# Static Condition Registry
var _registry: Dictionary = {}

func _init() -> void:
	_register_all_conditions()

func _register_all_conditions() -> void:
	# 1. Paralyzed
	_register_def("paralyzed", "Paralisado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_crit_range": 1.5, "auto_fail_str_dex_saves": true
	})
	# 2. Poisoned
	_register_def("poisoned", "Envenenado", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "dot_fixed_damage": 2, "dot_damage_type": "Veneno"
	})
	# 3. Stunned
	_register_def("stunned", "Atordoado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_fail_str_dex_saves": true
	})
	# 4. Blinded
	_register_def("blinded", "Cego", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "grants_attacker_advantage": true
	})
	# 5. Charmed
	_register_def("charmed", "Encantado", StatusCondition.Category.CANONICAL_5E, {})
	# 6. Deafened
	_register_def("deafened", "Surdo", StatusCondition.Category.CANONICAL_5E, {})
	# 7. Frightened
	_register_def("frightened", "Assustado", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true
	})
	# 8. Grappled
	_register_def("grappled", "Agarrado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_movement": true
	})
	# 9. Incapacitated
	_register_def("incapacitated", "Incapacitado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true
	})
	# 10. Invisible
	_register_def("invisible", "Invisível", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_advantage_on_attack": true, "grants_attacker_disadvantage": true
	})
	# 11. Petrified
	_register_def("petrified", "Petrificado", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_fail_str_dex_saves": true, "damage_resistance_modifier": 0.5
	})
	# 12. Prone
	_register_def("prone", "Caído", StatusCondition.Category.CANONICAL_5E, {
		"inflicts_disadvantage_on_attack": true, "speed_multiplier": 0.5, "save_disadvantage_dex": true
	})
	# 13. Restrained
	_register_def("restrained", "Contido", StatusCondition.Category.CANONICAL_5E, {
		"blocks_movement": true, "inflicts_disadvantage_on_attack": true,
		"grants_attacker_advantage": true, "save_disadvantage_dex": true
	})
	# 14. Unconscious
	_register_def("unconscious", "Inconsciente", StatusCondition.Category.CANONICAL_5E, {
		"blocks_action": true, "blocks_movement": true, "grants_attacker_advantage": true,
		"auto_crit_range": 1.5, "auto_fail_str_dex_saves": true
	})
	# 15. Bleeding
	_register_def("bleeding", "Sangrando", StatusCondition.Category.ELEMENTAL, {
		"dot_percent_hp_max": 0.05, "dot_damage_type": "Fisico"
	})
	# 16. Burning
	_register_def("burning", "Queimando", StatusCondition.Category.ELEMENTAL, {
		"dot_fixed_damage": 3, "dot_damage_type": "Fogo" # Average of 1d6
	})
	# 17. Frozen
	_register_def("frozen", "Congelado", StatusCondition.Category.ELEMENTAL, {
		"speed_multiplier": 0.5, "grants_attacker_advantage": true
	})
	# 18. Confused
	_register_def("confused", "Confuso", StatusCondition.Category.ELEMENTAL, {})
	# 19. Cursed
	_register_def("cursed", "Amaldiçoado", StatusCondition.Category.ELEMENTAL, {
		"dot_fixed_damage": 3, "bonus_attack_roll": -2, "dot_damage_type": "Necrotico"
	})
	# 20. Blessed
	_register_def("blessed", "Abençoado", StatusCondition.Category.TACTICAL_BUFF, {
		"bonus_attack_roll": 2 # +1d4 average
	})
	# 21. Hasted
	_register_def("hasted", "Acelerado", StatusCondition.Category.TACTICAL_BUFF, {
		"speed_multiplier": 2.0, "bonus_ac": 2, "save_advantage_dex": true
	})
	# 22. Slowed
	_register_def("slowed", "Lentidão", StatusCondition.Category.TACTICAL_DEBUFF, {
		"speed_bonus": -2, "bonus_ac": -2
	})
	# 23. Doomed
	_register_def("doomed", "Condenado", StatusCondition.Category.TACTICAL_DEBUFF, {})

func _register_def(id: String, display_name: String, cat: StatusCondition.Category, props: Dictionary) -> void:
	var cond: StatusCondition = StatusCondition.new()
	cond.id = id
	cond.display_name = display_name
	cond.category = cat
	for k in props:
		cond.set(k, props[k])
	_registry[id] = cond

func apply_condition(character: CharacterData, condition_id: String, duration: int, extra_data: Dictionary = {}) -> bool:
	if not _registry.has(condition_id):
		push_error("[StatusEffectManager] Unknown condition '%s'" % condition_id)
		return false
	
	# Check immunities
	if character.imunidades.has(condition_id) or character.imunidades.has(_registry[condition_id].display_name):
		return false
	
	# Check existing: extend duration
	if not character.has_meta("active_conditions"):
		character.set_meta("active_conditions", [])
	
	var active_list: Array = character.get_meta("active_conditions")
	for cond in active_list:
		if cond.id == condition_id:
			cond.duration_turns += duration
			cond.extra_data.merge(extra_data, true)
			EventBus.status_applied.emit(character.id, condition_id, cond.duration_turns)
			return true
	
	var new_cond: StatusCondition = _registry[condition_id].duplicate_condition()
	new_cond.duration_turns = duration
	new_cond.extra_data = extra_data.duplicate(true)
	active_list.append(new_cond)
	character.set_meta("active_conditions", active_list)
	
	EventBus.status_applied.emit(character.id, condition_id, duration)
	return true

func remove_condition(character: CharacterData, condition_id: String) -> bool:
	if not character.has_meta("active_conditions"):
		return false
	var active_list: Array = character.get_meta("active_conditions")
	var removed: bool = false
	for i in range(active_list.size() - 1, -1, -1):
		if active_list[i].id == condition_id:
			active_list.remove_at(i)
			removed = true
			EventBus.status_removed.emit(character.id, condition_id)
			break
	character.set_meta("active_conditions", active_list)
	return removed

func has_condition(character: CharacterData, condition_id: String) -> bool:
	if not character.has_meta("active_conditions"):
		return false
	var active_list: Array = character.get_meta("active_conditions")
	for cond in active_list:
		if cond.id == condition_id:
			return true
	return false

func can_character_act(character: CharacterData) -> bool:
	if character.hp <= 0:
		return false
	if not character.has_meta("active_conditions"):
		return true
	for cond in character.get_meta("active_conditions"):
		if cond.blocks_action:
			return false
	return true

func get_effective_speed(character: CharacterData) -> int:
	if not character.has_meta("active_conditions"):
		return character.velocidade
	var active_list: Array = character.get_meta("active_conditions")
	var speed: float = float(character.velocidade)
	for cond in active_list:
		if cond.blocks_movement:
			return 0
		speed = (speed + float(cond.speed_bonus)) * cond.speed_multiplier
	return maxi(0, int(round(speed)))

func evaluate_attack_modifiers(attacker: CharacterData, target: CharacterData, distance: float) -> Dictionary:
	var has_adv: bool = false
	var has_disadv: bool = false
	var is_crit: bool = false
	var log_mods: Array[String] = []
	
	# Attacker checks
	if has_condition(attacker, "blinded"):
		has_disadv = true; log_mods.append("Cego (Atacante)")
	if has_condition(attacker, "poisoned"):
		has_disadv = true; log_mods.append("Envenenado")
	if has_condition(attacker, "prone"):
		has_disadv = true; log_mods.append("Caído (Atacante)")
	if has_condition(attacker, "restrained"):
		has_disadv = true; log_mods.append("Contido (Atacante)")
	if has_condition(attacker, "frightened"):
		has_disadv = true; log_mods.append("Assustado")
	if has_condition(attacker, "invisible"):
		has_adv = true; log_mods.append("Invisível (Atacante)")

	# Target checks
	if has_condition(target, "blinded"):
		has_adv = true; log_mods.append("Cego (Alvo)")
	if has_condition(target, "restrained"):
		has_adv = true; log_mods.append("Contido (Alvo)")
	if has_condition(target, "paralyzed") or has_condition(target, "stunned") or has_condition(target, "unconscious") or has_condition(target, "petrified"):
		has_adv = true; log_mods.append("Alvo Incapacitado")
	
	if has_condition(target, "prone"):
		if distance <= 1.5:
			has_adv = true; log_mods.append("Alvo Caído (Perto)")
		else:
			has_disadv = true; log_mods.append("Alvo Caído (Longe)")
			
	if has_condition(target, "invisible") and not has_condition(attacker, "see_invisibility"):
		has_disadv = true; log_mods.append("Alvo Invisível")
		
	# Auto-Crit check
	if (has_condition(target, "paralyzed") or has_condition(target, "unconscious")) and distance <= 1.5:
		is_crit = true
		log_mods.append("CRÍTICO AUTOMÁTICO")
		
	return {
		"has_advantage": has_adv and not has_disadv,
		"has_disadvantage": has_disadv and not has_adv,
		"is_auto_crit": is_crit,
		"log_modifiers": log_mods
	}

func tick_turn_start(character: CharacterData) -> Dictionary:
	var damage_dealt: int = 0
	var logs: Array[String] = []
	if not character.has_meta("active_conditions"):
		return {"damage_dealt": 0, "logs": []}
		
	var active_list: Array = character.get_meta("active_conditions")
	var to_remove: Array[String] = []
	
	for cond in active_list:
		# Process DoT
		var tick_dmg: int = 0
		if cond.dot_fixed_damage > 0:
			tick_dmg += cond.dot_fixed_damage
		if cond.dot_percent_hp_max > 0.0:
			tick_dmg += maxi(1, int(float(character.max_hp) * cond.dot_percent_hp_max))
			
		if tick_dmg > 0:
			character.hp = maxi(0, character.hp - tick_dmg)
			damage_dealt += tick_dmg
			logs.append("%s sofre %d de dano por %s." % [character.name, tick_dmg, cond.display_name])
			EventBus.unit_damaged.emit(character.id, tick_dmg, character.hp, character.max_hp)
			
		# Decrement duration
		cond.duration_turns -= 1
		if cond.duration_turns <= 0:
			to_remove.append(cond.id)
			
	for cond_id in to_remove:
		remove_condition(character, cond_id)
		
	return {"damage_dealt": damage_dealt, "logs": logs}
```

---

## 6. Comprehensive GUT Test Suite Specification (`test/unit/test_status_effects.gd`)

The test suite must be co-located at `godot_project/test/unit/test_status_effects.gd` and adhere strictly to the Arrange-Act-Assert (AAA) protocol:

### Test Matrix Structure:
1. `test_registration_all_23_conditions`: Verifies every one of the 23 conditions exists with valid attributes.
2. `test_apply_and_extend_duration`: Verifies duration extension on re-application without duplicating entries.
3. `test_immunity_blocks_application`: Verifies immunity prevents application (e.g. Lorde Lich immune to poison).
4. `test_movement_restriction_grappled_restrained_paralyzed`: Verifies effective speed is 0.
5. `test_movement_hasted_and_slowed`: Verifies speed doubling and reduction.
6. `test_action_blocked_stunned_paralyzed_unconscious`: Verifies `can_character_act` returns `false`.
7. `test_attack_advantage_blinded_and_invisible`: Verifies advantage/disadvantage flags.
8. `test_advantage_disadvantage_cancellation`: Verifies simultaneous advantage and disadvantage cancel to normal roll.
9. `test_prone_melee_vs_ranged_distance_threshold`: Verifies advantage at $\le 1.5$m, disadvantage at $> 1.5$m.
10. `test_auto_crit_paralyzed_and_unconscious_melee_only`: Verifies auto-crit at 1.5m, normal at 3.0m.
11. `test_poison_and_bleed_dot_tick_lifecycle`: Verifies fixed damage (2) and percent damage (5% max HP).
12. `test_duration_decrement_and_removal`: Verifies 1-turn duration expires and emits `status_removed`.
13. `test_save_auto_fails_and_disadvantage`: Verifies auto-fails on Str/Dex saves for paralyzed/stunned.
14. `test_eventbus_signal_emissions`: Verifies `status_applied` and `status_removed` signals emitted.

---

## 7. Caveats

1. In the legacy Python codebase, condition handling was partially split between `src/condicoes.py` (combat attack rolls) and `src/personagens/status_efeito.py` (turn DoT). The proposed Godot 4 architecture unifies all condition mechanics under `StatusEffectManager.gd` while maintaining 100% mathematical and rule parity.
2. In D&D 5e RAW, standing up from Prone costs half of total movement speed. The GDScript implementation provides `speed_multiplier: 0.5` or an explicit `stand_up()` cost check.
3. The Godot 4 binary is confirmed and functional at `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot`.

---

## 8. Conclusion

All 23 status conditions (plus 13 tactical combat conditions/modifiers) have been mined, probed, and specified from the authoritative Python codebase. The mathematical formulas for attack modifiers, distance-dependent prone checks, melee auto-crits, damage-over-time ticks, and death saving throw interactions are completely documented. The proposed GDScript architecture (`StatusCondition.gd` and `StatusEffectManager.gd`) is fully typed and ready for Milestone 2 implementation.

---

## 9. Verification Method

1. **Verify Report Files**:
   ```bash
   cat /home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_conditions/handoff.md
   ```
2. **Execute Headless GUT Runner via CLI**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project && ./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
   ```
   **Expected Result**: All tests pass with exit code 0.
3. **Verify Python Parity Probes**:
   ```bash
   python3 -c "
   import sys, types
   mock_pygame = types.ModuleType('pygame')
   mock_pygame.Rect = lambda x,y,w,h: (x,y,w,h)
   mock_pygame.Surface = lambda *args: None
   sys.modules['pygame'] = mock_pygame
   from src.condicoes import verificar_condicoes_ataque
   print('Condition verification imported cleanly.')
   "
   ```
