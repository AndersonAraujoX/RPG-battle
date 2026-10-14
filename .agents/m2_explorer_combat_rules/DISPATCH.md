## 2026-09-26T16:36:31Z
You are the Combat Rules Explorer for Milestone 2 of RPG-battle Godot 4 migration.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_combat_rules

Read these files first:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md

Your Mission:
Investigate the reference Python codebase for D&D 5e combat rules:
- Inspect `src/engine/motor_combate.py`, `src/engine/juiz_combate.py`, and related files.
- Document exact D&D 5e formulas used:
  - Ability modifier: floor((stat - 10) / 2)
  - Proficiency bonus: 1 + ceil(level / 4)
  - Attack roll: d20 + attack_mod vs AC + cover_bonus
  - Advantage / Disadvantage mechanics and cancellation
  - Critical hits (Nat 20) and Critical misses (Nat 1)
  - Damage resolution: dice roll + modifier vs resistances/vulnerabilities/immunities
  - Death Saving Throws: Nat 1 (2 fails), 2-9 (1 fail), 10-19 (1 success), Nat 20 (revive 1 HP). Damage at 0 HP rules.
- Propose GDScript class structure for `godot_project/scripts/combat/CombatRules.gd` and helper data structures (`AttackResult.gd`, `DamageResult.gd`, `DeathSaveResult.gd`), with GUT test plan.
- Deliver your report in `handoff.md` and notify parent.
