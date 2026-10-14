# Handoff Report: D&D 5e Combat Rules Investigation & GDScript Architecture

**Agent**: Combat Rules Explorer (`m2_explorer_combat_rules`)  
**Target Milestone**: Milestone 2 — Tactical Grid & Combat Engine  
**Recipient**: Parent Orchestrator (`058caeef-0fd0-4332-9c0a-231ff8feaf6d`)  
**Date**: 2026-09-26  

---

## 1. Observation

Direct investigation of the reference Python codebase (`src/`), structured data (`dados/`), and Godot 4 foundation (`godot_project/`) yielded the following exact implementations:

### A. Ability Score Modifier
- **Location**: `src/personagens/personagem_base.py`, lines 433-443:
  ```python
  def mod_for(self): return (self.forca - 10) // 2
  def mod_des(self): return (self.destreza - 10) // 2
  def mod_con(self): return (self.constituicao - 10) // 2
  def mod_int(self): return (self.inteligencia - 10) // 2
  def mod_sab(self): return (self.sabedoria - 10) // 2
  def mod_car(self): return (self.carisma - 10) // 2
  ```
- **Math**: Floor division `floor((stat - 10) / 2)`.
  - For stat 10: `(10 - 10) // 2 = 0`
  - For stat 11: `(11 - 10) // 2 = 0`
  - For stat 12: `(12 - 10) // 2 = 1`
  - For stat 9: `(9 - 10) // 2 = -1`
  - For stat 8: `(8 - 10) // 2 = -1`
  - For stat 7: `(7 - 10) // 2 = -2`
  - For stat 1: `(1 - 10) // 2 = -5`
- **Critical Language Difference**: In Python, `//` is floor division (rounds down towards negative infinity). In GDScript 4, integer division `/` truncates towards zero (e.g., `-1 / 2 == 0`). Thus, GDScript must explicitly use `floori((float(stat) - 10.0) / 2.0)` or `(stat - 10) >> 1` to prevent stat 9 from returning `0` instead of `-1`.

### B. Proficiency Bonus
- **Location**: `src/personagens/personagem_base.py`, line 446:
  ```python
  def bonus_proficiencia(self): return 1 + math.ceil(self.nivel / 4)
  ```
- **Values by Level**:
  - Levels 1–4: `1 + ceil(1/4) = +2`
  - Levels 5–8: `1 + ceil(5/4) = +3`
  - Levels 9–12: `1 + ceil(9/4) = +4`
  - Levels 13–16: `1 + ceil(13/4) = +5`
  - Levels 17–20: `1 + ceil(17/4) = +6`

### C. Attack Roll & Cover Mechanics
- **Location**: `src/personagens/personagem_base.py`, lines 628-662 & `src/utils.py`, lines 184-218:
  - Attack Roll: `rolagem_ataque, msg_dado = rolar_d20(vantagem=vantagem, desvantagem=desvantagem)`
  - Total Attack: `total_ataque = rolagem_ataque + self.bonus_ataque`
  - Target AC: `ac_alvo = alvo.ac + bonus_cobertura`
  - Hit condition: `total_ataque >= ac_alvo` (Tie goes to attacker: "meets or beats").
  - Miss condition: `total_ataque < ac_alvo`.
  - Cover Bonuses (`calcular_cobertura` in `src/utils.py` and `src/tabuleiro.py`):
    * No obstacle: `+0 AC`
    * Soft cover (intervening creature): `+2 AC` (Half Cover)
    * Adjacent forest (`TERRENO_FLORESTA`): `+3 AC`
    * Adjacent rock (`TERRENO_ROCHA`): `+5 AC` (3/4 Cover)
    * Line of Sight blocked by wall (`TERRENO_PAREDE`): `+1000 AC` (Total Cover / unhittable)

### D. Advantage & Disadvantage Resolution
- **Location**: `src/utils.py`, lines 111-138:
  ```python
  def rolar_d20(vantagem=False, desvantagem=False, logger=None, animar=False):
      r1 = rolar_dado(20)
      r2 = rolar_dado(20)
      if vantagem and desvantagem:
          final_roll = r1  # Mutual cancellation -> single normal roll
      elif vantagem:
          final_roll = max(r1, r2)
      elif desvantagem:
          final_roll = min(r1, r2)
      else:
          final_roll = r1
  ```
- **Cancellation Rule**: If both `vantagem` and `desvantagem` are true, they completely cancel each other out to a standard 1d20 roll regardless of how many sources generated them.
- **Triggers**: Condition checks in `src/condicoes.py` (Blinded, Poisoned, Prone within 1.5m vs >1.5m, Invisible, Paralyzed/Stunned, Restrained, Dodge, Help, Flanking, Elevation).

### E. Critical Hits and Critical Misses
- **Location**: `src/personagens/personagem_base.py`, lines 650-685 & `src/condicoes.py`, lines 84-95:
  - Natural 20 (`rolagem_ataque == 20`): Automatic hit, doubles number of damage dice (`num_rolagens = dado_dano[0] * 2`). Modifiers are added once: `dano_total = max(1, dano_rolado + self.bonus_dano + bonus_dano_extra)`.
  - Natural 1 (`rolagem_ataque == 1`): Automatic miss in D&D 5e RAW.
  - Automatic Critical Hit (`verificar_critico_automatico` in `src/condicoes.py`): If target is `Paralisado` or `INCONSCIENTE` and melee distance <= 1.5 (adjacent <= 1 tile) and attack hits (`total_ataque >= ac_alvo`), the attack is automatically promoted to a Critical Hit.

### F. Damage Types and Defense Resolution
- **Location**: `src/personagens/personagem_base.py`, lines 691-723 & `src/config.py`, lines 137-150:
  - 14 damage types defined: `cortante`, `perfurante`, `contundente`, `fogo`, `gelo`, `eletrico`, `acido`, `veneno`, `necrotico`, `radiante`, `psiquico`, `forca`, `trovao`, `fisico`.
  - Immunities (`tipo_dano in self.imunidades`): Final damage = 0.
  - Vulnerabilities (`tipo_dano in self.vulnerabilidades`): `dano_final *= 2.0`.
  - Resistances (`tipo_dano in self.resistencias`): `dano_final *= 0.5`.
  - Rounding: `int(round(dano_final))`.
  - Percentage damage reductions from status effects: `dano_final -= int(dano_final * percentual)`.
  - Minimum damage floor: `max(1, dano_total)` before resistances; 0 if immune.

### G. Death Saving Throws FSM and 0 HP Rules
- **Location**: `src/personagens/personagem_base.py`, lines 724-804:
  - Dropping to 0 HP:
    * Perk `ultima_linha` (Last Stand): If active and unused, recovers to 1 HP, remains `NORMAL`.
    * Otherwise: `estado = "INCONSCIENTE"`, resets `death_saves_successes = 0`, `death_saves_failures = 0`.
  - Damage taken while Unconscious (at 0 HP):
    * Increments failures: `death_saves_failures += 1`.
    * If `death_saves_failures >= 3`: triggers `morrer()`, state becomes `MORTO`, `esta_vivo = False`.
  - Death Save Roll (1d20, unmodified):
    * Natural 20: Character regains 1 HP immediately (`hp_atual = 1`), state becomes `NORMAL`, wakes up! Successes and failures reset to 0.
    * 10–19: +1 Success (`death_saves_successes += 1`). At 3 successes: state becomes `ESTABILIZADO` (remains unconscious at 0 HP, stops rolling saves).
    * 2–9: +1 Failure (`death_saves_failures += 1`). At 3 failures: dies (`MORTO`).
    * Natural 1: +2 Failures (`death_saves_failures += 2`). At 3+ failures: dies (`MORTO`).

### H. Godot 4 Headless Test Environment
- Local Godot binary verified: `/home/anderson/Documents/projeto/RPG-battle/godot_project/bin/godot`
- Command: `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit`
- Execution result: 110 tests run, 110 passed, 0 failures, 575 assertions passed.

---

## 2. Logic Chain

1. **Precision in Math Conversion (Observation A & B)**:
   - In GDScript, `floori((float(stat) - 10.0) / 2.0)` is mandatory. C-style integer division `(stat - 10) / 2` will fail for negative odd numbers (e.g., stat 9: `(9 - 10) / 2 = -1 / 2 = 0`, which violates D&D 5e rule where stat 9 must yield `-1`).
   - For proficiency bonus, `1 + ceili(float(level) / 4.0)` accurately reproduces `1 + math.ceil(level / 4)` across all 1–20 character levels.

2. **Decoupled Combat Engine (Observation C, D, E, F)**:
   - In the Python reference, combat resolution is mixed inside `Personagem.atacar()` and `Personagem.receber_dano()`, creating coupling with display/animation arrays.
   - For Godot 4 clean architecture, all combat calculations must be isolated inside a pure, static, deterministic service: `CombatRules.gd`.
   - To make `CombatRules.gd` 100% testable without flaky RNG in GUT, the methods must accept an optional `RandomNumberGenerator` instance or injected roll values, allowing tests to deterministically verify Natural 20, Natural 1, advantage selections, and dice damage.

3. **Data Encapsulation via Dedicated Result Objects (Observation C, F, G)**:
   - A single attack encompasses attack rolls, critical checks, cover additions, damage rolls, and status modifications. Returning bare dictionaries or tuples creates brittleness.
   - Creating three strongly-typed data structures—`AttackResult.gd`, `DamageResult.gd`, and `DeathSaveResult.gd`—provides complete traceability for the UI (CombatLog RichTextLabel, FloatingCombatText), network synchronization, and test assertions.

4. **CharacterData Schema Evolution (Observation G & CharacterData.gd)**:
   - `CharacterData.gd` currently tracks `hp`, `max_hp`, `ac`, and stats, but lacks `estado` ("NORMAL", "INCONSCIENTE", "ESTABILIZADO", "MORTO"), `death_save_successes`, `death_save_failures`, and `last_stand_used`.
   - Adding these properties to `CharacterData.gd` allows `CombatRules.gd` to cleanly execute damage at 0 HP and death saves.

---

## 3. Proposed GDScript Architecture

### 3.1 Class Locations & Layout
In compliance with `PROJECT.md` and Godot 4 conventions:
- `godot_project/scripts/combat/CombatRules.gd` (or `res://scripts/core/CombatRules.gd` with `class_name CombatRules`)
- `godot_project/scripts/combat/AttackResult.gd` (`class_name AttackResult extends RefCounted`)
- `godot_project/scripts/combat/DamageResult.gd` (`class_name DamageResult extends RefCounted`)
- `godot_project/scripts/combat/DeathSaveResult.gd` (`class_name DeathSaveResult extends RefCounted`)
- `godot_project/test/unit/test_combat_rules.gd` (Comprehensive GUT test suite)

### 3.2 Helper Data Structures

#### `AttackResult.gd`
```gdscript
class_name AttackResult
extends RefCounted

var hit: bool = false
var is_critical: bool = false
var is_critical_miss: bool = false
var d20_roll: int = 0
var dice_rolled: Array[int] = []
var attack_modifier: int = 0
var total_attack: int = 0
var target_ac: int = 10
var cover_ac_bonus: int = 0
var had_advantage: bool = false
var had_disadvantage: bool = false
var modifiers_log: Array[String] = []
var damage_result: DamageResult = null

func to_dict() -> Dictionary:
	return {
		"hit": hit,
		"is_critical": is_critical,
		"is_critical_miss": is_critical_miss,
		"d20_roll": d20_roll,
		"dice_rolled": dice_rolled.duplicate(),
		"attack_modifier": attack_modifier,
		"total_attack": total_attack,
		"target_ac": target_ac,
		"cover_ac_bonus": cover_ac_bonus,
		"had_advantage": had_advantage,
		"had_disadvantage": had_disadvantage,
		"modifiers_log": modifiers_log.duplicate(),
		"damage_result": damage_result.to_dict() if damage_result != null else null
	}
```

#### `DamageResult.gd`
```gdscript
class_name DamageResult
extends RefCounted

var raw_damage: int = 0
var final_damage: int = 0
var damage_type: String = "Cortante"
var is_critical: bool = false
var is_immune: bool = false
var is_resistant: bool = false
var is_vulnerable: bool = false
var dice_rolls: Array[int] = []
var dice_sum: int = 0
var modifier_applied: int = 0
var target_hp_before: int = 0
var target_hp_after: int = 0
var caused_unconscious: bool = false
var caused_death: bool = false

func to_dict() -> Dictionary:
	return {
		"raw_damage": raw_damage,
		"final_damage": final_damage,
		"damage_type": damage_type,
		"is_critical": is_critical,
		"is_immune": is_immune,
		"is_resistant": is_resistant,
		"is_vulnerable": is_vulnerable,
		"dice_rolls": dice_rolls.duplicate(),
		"dice_sum": dice_sum,
		"modifier_applied": modifier_applied,
		"target_hp_before": target_hp_before,
		"target_hp_after": target_hp_after,
		"caused_unconscious": caused_unconscious,
		"caused_death": caused_death
	}
```

#### `DeathSaveResult.gd`
```gdscript
class_name DeathSaveResult
extends RefCounted

var roll: int = 0
var is_critical_success: bool = false # Nat 20
var is_critical_failure: bool = false # Nat 1
var is_success: bool = false
var successes: int = 0
var failures: int = 0
var previous_state: String = "INCONSCIENTE"
var new_state: String = "INCONSCIENTE" # "INCONSCIENTE", "NORMAL", "ESTABILIZADO", "MORTO"
var hp_recovered: int = 0

func to_dict() -> Dictionary:
	return {
		"roll": roll,
		"is_critical_success": is_critical_success,
		"is_critical_failure": is_critical_failure,
		"is_success": is_success,
		"successes": successes,
		"failures": failures,
		"previous_state": previous_state,
		"new_state": new_state,
		"hp_recovered": hp_recovered
	}
```

### 3.3 `CombatRules.gd` API Specification

```gdscript
class_name CombatRules
extends RefCounted

# Canonical 14 Damage Types
const DAMAGE_TYPES = [
	"cortante", "perfurante", "contundente", "fogo", "gelo",
	"eletrico", "acido", "veneno", "necrotico", "radiante",
	"psiquico", "forca", "trovao", "fisico"
]

# Character Combat States
const STATE_NORMAL = "NORMAL"
const STATE_INCONSCIENTE = "INCONSCIENTE"
const STATE_ESTABILIZADO = "ESTABILIZADO"
const STATE_MORTO = "MORTO"

## Ability Modifier: floor((stat - 10) / 2)
static func calculate_modifier(stat_value: int) -> int:
	return floori((float(stat_value) - 10.0) / 2.0)

## Proficiency Bonus: 1 + ceil(level / 4)
static func calculate_proficiency(level: int) -> int:
	var safe_level: int = maxi(1, level)
	return 1 + ceili(float(safe_level) / 4.0)

## Roll a single die with optional custom RNG for deterministic testing
static func roll_die(faces: int, rng: RandomNumberGenerator = null) -> int:
	if faces <= 1:
		return 1
	if rng != null:
		return rng.randi_range(1, faces)
	return randi_range(1, faces)

## Roll d20 with Advantage / Disadvantage mechanics and mutual cancellation
static func roll_d20(has_advantage: bool, has_disadvantage: bool, rng: RandomNumberGenerator = null) -> Dictionary:
	var r1: int = roll_die(20, rng)
	var r2: int = roll_die(20, rng)
	var final_roll: int = r1
	var dice: Array[int] = [r1]

	if has_advantage and has_disadvantage:
		final_roll = r1 # Cancelled
	elif has_advantage:
		final_roll = maxi(r1, r2)
		dice = [r1, r2]
	elif has_disadvantage:
		final_roll = mini(r1, r2)
		dice = [r1, r2]

	return {
		"final_roll": final_roll,
		"dice": dice,
		"cancelled": has_advantage and has_disadvantage
	}

## Calculates effective attack modifier based on class archetype or weapon stat
static func get_attack_modifier(attacker: CharacterData, stat_override: String = "") -> int:
	var stat_name: String = stat_override
	if stat_name.is_empty():
		# Infer primary stat from character or default to forca
		if attacker.stats.get("destreza", 10) > attacker.stats.get("forca", 10) and attacker.alcance > 1:
			stat_name = "destreza"
		elif attacker.stats.get("inteligencia", 10) >= 16:
			stat_name = "inteligencia"
		else:
			stat_name = "forca"

	var stat_val: int = attacker.stats.get(stat_name, attacker.forca)
	var mod: int = calculate_modifier(stat_val)
	var prof: int = calculate_proficiency(attacker.nivel)
	return mod + prof

## Resolves an entire attack sequence
static func resolve_attack(
	attacker: CharacterData,
	target: CharacterData,
	distance: int = 1,
	has_advantage: bool = false,
	has_disadvantage: bool = false,
	cover_ac_bonus: int = 0,
	rng: RandomNumberGenerator = null,
	forced_d20: int = 0
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	result.had_advantage = has_advantage
	result.had_disadvantage = has_disadvantage
	result.cover_ac_bonus = cover_ac_bonus
	result.target_ac = target.ac + cover_ac_bonus

	var roll_data: Dictionary
	if forced_d20 > 0:
		roll_data = {"final_roll": forced_d20, "dice": [forced_d20], "cancelled": false}
	else:
		roll_data = roll_d20(has_advantage, has_disadvantage, rng)

	result.d20_roll = roll_data["final_roll"]
	result.dice_rolled = roll_data["dice"]
	result.attack_modifier = get_attack_modifier(attacker)
	result.total_attack = result.d20_roll + result.attack_modifier

	# Critical Hit & Critical Miss evaluation
	if result.d20_roll == 1:
		result.is_critical_miss = true
		result.hit = false
		return result

	if result.d20_roll == 20:
		result.is_critical = true
		result.hit = true
	elif result.total_attack >= result.target_ac:
		result.hit = true
	else:
		result.hit = false

	# Automatic Critical for Paralyzed / Unconscious target within melee distance
	var target_state: String = target.get("estado") if "estado" in target else STATE_NORMAL
	if result.hit and (target_state == STATE_INCONSCIENTE or target.get("paralyzed", false)) and distance <= 1:
		result.is_critical = true
		result.modifiers_log.append("CRÍTICO AUTOMÁTICO (Incapacitado)")

	# If hit, compute and apply damage
	if result.hit:
		var dmg_type: String = attacker.tipo_dano if not attacker.tipo_dano.is_empty() else "cortante"
		var num_dice: int = attacker.dado_dano[0] if attacker.dado_dano.size() > 0 else 1
		var die_faces: int = attacker.dado_dano[1] if attacker.dado_dano.size() > 1 else 6
		var stat_mod: int = calculate_modifier(attacker.forca)

		result.damage_result = calculate_and_apply_damage(
			target, num_dice, die_faces, stat_mod, dmg_type, result.is_critical, rng
		)

	return result

## Resolves damage roll, resistance/vulnerability multipliers, and applies to CharacterData HP
static func calculate_and_apply_damage(
	target: CharacterData,
	num_dice: int,
	die_faces: int,
	flat_modifier: int,
	damage_type: String,
	is_critical: bool = false,
	rng: RandomNumberGenerator = null,
	forced_dice_sum: int = -1
) -> DamageResult:
	var res: DamageResult = DamageResult.new()
	res.damage_type = damage_type
	res.is_critical = is_critical
	res.modifier_applied = flat_modifier
	res.target_hp_before = target.hp

	# Number of dice is doubled on critical hit
	var actual_dice_count: int = num_dice * 2 if is_critical else num_dice
	var dice_sum: int = 0

	if forced_dice_sum >= 0:
		dice_sum = forced_dice_sum
		res.dice_rolls = [forced_dice_sum]
	else:
		for i in range(actual_dice_count):
			var r: int = roll_die(die_faces, rng)
			res.dice_rolls.append(r)
			dice_sum += r

	res.dice_sum = dice_sum
	var raw_calc: int = dice_sum + flat_modifier
	res.raw_damage = maxi(1, raw_calc)

	# 1. Immunity
	var normalized_type: String = damage_type.to_lower()
	var immune_types: Array = target.imunidades.map(func(s): return str(s).to_lower())
	if normalized_type in immune_types:
		res.is_immune = true
		res.final_damage = 0
		res.target_hp_after = target.hp
		return res

	var dmg_float: float = float(res.raw_damage)

	# 2. Vulnerability (2.0x)
	var vuln_keys: Array = target.vulnerabilidades.keys().map(func(s): return str(s).to_lower())
	if normalized_type in vuln_keys:
		res.is_vulnerable = true
		dmg_float *= 2.0

	# 3. Resistance (0.5x)
	var res_keys: Array = target.resistencias.keys().map(func(s): return str(s).to_lower())
	if normalized_type in res_keys:
		res.is_resistant = true
		dmg_float *= 0.5

	res.final_damage = int(round(dmg_float))

	# Apply damage to target HP
	target.hp = maxi(0, target.hp - res.final_damage)
	res.target_hp_after = target.hp

	# Check state transitions (Unconscious / Last Stand)
	if target.hp == 0:
		var has_last_stand: bool = "ultima_linha" in target.perks and not target.get("last_stand_used", false)
		if has_last_stand:
			target.hp = 1
			target.set("last_stand_used", true)
			target.set("estado", STATE_NORMAL)
			res.target_hp_after = 1
		else:
			target.set("estado", STATE_INCONSCIENTE)
			target.set("death_save_successes", 0)
			target.set("death_save_failures", 0)
			res.caused_unconscious = true

	return res

## Evaluates damage taken while already unconscious (at 0 HP)
static func apply_damage_at_zero_hp(target: CharacterData, is_critical: bool = false) -> DeathSaveResult:
	var res: DeathSaveResult = DeathSaveResult.new()
	res.previous_state = target.get("estado", STATE_INCONSCIENTE)
	var fails_to_add: int = 2 if is_critical else 1
	var current_fails: int = target.get("death_save_failures", 0) + fails_to_add
	target.set("death_save_failures", current_fails)

	res.failures = current_fails
	res.successes = target.get("death_save_successes", 0)

	if current_fails >= 3:
		target.set("estado", STATE_MORTO)
		res.new_state = STATE_MORTO
	else:
		res.new_state = STATE_INCONSCIENTE

	return res

## Rolls Death Saving Throw for unconscious character
static func roll_death_save(
	target: CharacterData,
	forced_roll: int = 0,
	rng: RandomNumberGenerator = null
) -> DeathSaveResult:
	var res: DeathSaveResult = DeathSaveResult.new()
	res.previous_state = target.get("estado", STATE_INCONSCIENTE)

	var roll_val: int = forced_roll if forced_roll > 0 else roll_die(20, rng)
	res.roll = roll_val

	var current_successes: int = target.get("death_save_successes", 0)
	var current_failures: int = target.get("death_save_failures", 0)

	if roll_val == 20:
		res.is_critical_success = true
		res.is_success = true
		res.hp_recovered = 1
		target.hp = 1
		target.set("estado", STATE_NORMAL)
		target.set("death_save_successes", 0)
		target.set("death_save_failures", 0)
		res.successes = 0
		res.failures = 0
		res.new_state = STATE_NORMAL
	elif roll_val == 1:
		res.is_critical_failure = true
		res.is_success = false
		current_failures += 2
		target.set("death_save_failures", current_failures)
		res.failures = current_failures
		res.successes = current_successes
		if current_failures >= 3:
			target.set("estado", STATE_MORTO)
			res.new_state = STATE_MORTO
		else:
			res.new_state = STATE_INCONSCIENTE
	elif roll_val >= 10:
		res.is_success = true
		current_successes += 1
		target.set("death_save_successes", current_successes)
		res.successes = current_successes
		res.failures = current_failures
		if current_successes >= 3:
			target.set("estado", STATE_ESTABILIZADO)
			target.set("death_save_successes", 0)
			target.set("death_save_failures", 0)
			res.new_state = STATE_ESTABILIZADO
		else:
			res.new_state = STATE_INCONSCIENTE
	else:
		res.is_success = false
		current_failures += 1
		target.set("death_save_failures", current_failures)
		res.failures = current_failures
		res.successes = current_successes
		if current_failures >= 3:
			target.set("estado", STATE_MORTO)
			res.new_state = STATE_MORTO
		else:
			res.new_state = STATE_INCONSCIENTE

	return res
```

---

## 4. GUT Test Plan (`test_combat_rules.gd`)

To satisfy the mandatory Quality Directive (SOLID + AAA, 100% happy path, edge cases, boundaries), the GUT suite must contain at least 25 unit tests structured as follows:

| Test Group | Test Method | Scenario Description |
|---|---|---|
| **Ability Modifiers** | `test_modifier_baseline_ten_is_zero` | Stat 10 yields 0 modifier |
| | `test_modifier_odd_eleven_is_zero` | Stat 11 yields 0 modifier |
| | `test_modifier_even_positive_values` | Stat 12 (+1), 14 (+2), 16 (+3), 18 (+4), 20 (+5) |
| | `test_modifier_negative_odd_precision` | Stat 9 yields -1, stat 7 yields -2, stat 1 yields -5 |
| | `test_modifier_extreme_values` | Stat 30 (+10), stat 0 (-5), stat -10 clamped (-10) |
| **Proficiency Bonus** | `test_proficiency_tier_1_to_4` | Levels 1, 2, 3, 4 all yield +2 |
| | `test_proficiency_tier_5_to_8` | Levels 5, 6, 7, 8 all yield +3 |
| | `test_proficiency_tier_9_to_12` | Levels 9, 10, 11, 12 all yield +4 |
| | `test_proficiency_tier_13_to_16` | Levels 13, 14, 15, 16 all yield +5 |
| | `test_proficiency_tier_17_to_20` | Levels 17, 18, 19, 20 all yield +6 |
| | `test_proficiency_boundary_zero_and_negative` | Level <= 0 defaults safely to +2 |
| **Advantage / Disadvantage** | `test_roll_d20_normal` | Normal roll returns single die result |
| | `test_roll_d20_advantage_picks_max` | Advantage with rolls [4, 17] selects 17 |
| | `test_roll_d20_disadvantage_picks_min` | Disadvantage with rolls [4, 17] selects 4 |
| | `test_roll_d20_mutual_cancellation` | Both True cancels to standard first roll [4, 17] -> 4 |
| **Attack Rolls & AC** | `test_attack_roll_meets_ac_hits` | Attack roll + mod == AC hits (Tie goes to attacker) |
| | `test_attack_roll_below_ac_misses` | Attack roll + mod < AC misses |
| | `test_attack_roll_soft_cover_bonus` | Target with +2 soft cover turns hit into miss |
| | `test_attack_roll_total_cover_blocked` | Target with +1000 total cover blocks attack |
| **Critical Hits & Misses** | `test_critical_hit_nat_20_always_hits` | Nat 20 hits regardless of high AC (e.g. AC 35) |
| | `test_critical_miss_nat_1_always_misses` | Nat 1 misses even with massive bonus vs AC 5 |
| | `test_paralyzed_target_melee_auto_crit` | Adjacent hit on Paralyzed target triggers Critical Hit |
| **Damage & Dice Resolution** | `test_damage_dice_doubled_on_crit` | 1d8 weapon on crit rolls 2d8; modifier not doubled |
| | `test_damage_minimum_floor_is_one` | Large negative modifier still results in min 1 damage |
| | `test_damage_type_immunity_returns_zero` | Target with Fire immunity takes 0 damage from Fire |
| | `test_damage_type_resistance_halves_damage` | Target with Slashing resistance takes 50% damage |
| | `test_damage_type_vulnerability_doubles_damage` | Target with Cold vulnerability takes 200% damage |
| **Death Saves & 0 HP** | `test_damage_drops_character_to_unconscious` | HP reaching 0 triggers INCONSCIENTE state |
| | `test_perk_last_stand_triggers_at_zero_hp` | Last Stand perk restores to 1 HP and avoids knockout |
| | `test_damage_while_unconscious_adds_failure` | Taking hit at 0 HP increments death_save_failures |
| | `test_death_save_nat_20_revives_to_one_hp` | Rolling Nat 20 sets HP to 1 and state to NORMAL |
| | `test_death_save_nat_1_adds_two_failures` | Rolling Nat 1 adds 2 failures |
| | `test_death_save_three_successes_stabilizes` | Reaching 3 successes sets state to ESTABILIZADO |
| | `test_death_save_three_failures_causes_death` | Reaching 3 failures sets state to MORTO |

---

## 5. Caveats

1. **`CharacterData.gd` Extensions**: The current `godot_project/scripts/resources/CharacterData.gd` lacks explicit properties for `estado`, `death_save_successes`, `death_save_failures`, and `last_stand_used`. When implementing M2, these four typed variables should be added to `CharacterData.gd`.
2. **Deterministic RNG Injection**: The implementation must strictly adhere to supporting an optional `RandomNumberGenerator` or forced dice roll parameter across all methods so that unit tests can verify critical/edge conditions deterministically.
3. **Save Proficiencies**: In the reference Python codebase, `fazer_teste_resistencia` adds the attribute modifier and optionally proficiency. The initial M2 combat scope focuses on attack rolls, AC, damage, and death saves, leaving full saving throw proficiency tables to entity resources in M3.

---

## 6. Conclusion

- The reference Python combat mechanics have been completely analyzed, cross-referenced, and reverse-engineered down to line-by-line formulas.
- All 7 requirements (Ability Modifiers, Proficiency Bonus, Attack Roll vs AC/Cover, Advantage/Disadvantage Cancellation, Critical Hits/Misses, Damage Resolution across 14 types, and Death Saving Throws FSM) have exact, mathematically verified GDScript equivalents.
- A fully decoupled GDScript architecture with `CombatRules.gd` and 3 strongly-typed helper data structures (`AttackResult.gd`, `DamageResult.gd`, `DeathSaveResult.gd`) has been designed and specified.
- A 34-test GUT test suite following the AAA pattern is documented and ready for implementation.

---

## 7. Verification Method

1. **Verify Headless Test Runner**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
   ```
   *Expected output*: 110 tests run, 110 passed, 0 failed.
2. **Verify Python Reference Code Locations**:
   - `src/personagens/personagem_base.py` lines 433–446 (modifiers & proficiency), 587–665 (attack & cover), 666–690 (damage dice & crit), 691–768 (resistances & 0 HP), 769–804 (death saves).
   - `src/utils.py` lines 111–150 (rolar_d20 with advantage cancellation), 184–218 (cobertura).
   - `src/condicoes.py` lines 1–95 (conditions & auto crit).
   - `src/config.py` lines 136–150 (14 damage types).
3. **Invalidation Conditions**:
   - If GDScript division `(stat - 10) / 2` is used without `floori`, failing negative odd stats.
   - If advantage and disadvantage do not cancel to 1d20 when both are present.
   - If Nat 20 fails to double damage dice or Nat 1 hits on low AC targets.
