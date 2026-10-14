## 2026-09-26T16:36:31Z
You are the Status Conditions Spec Miner for Milestone 2 of RPG-battle Godot 4 migration.

Your working directory is:
/home/anderson/Documents/projeto/RPG-battle/.agents/m2_explorer_conditions

Read these files first:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md

Your Mission:
Probe the authoritative Python codebase (`src/engine/`, `src/entities/`, `dados/`) to discover and document all 23 status conditions:
- Enumerate every condition (e.g. Paralyzed, Poisoned, Stunned, Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Petrified, Prone, Restrained, Unconscious, Bleeding, Burning, Frozen, Confused, Cursed, Blessed, Hasted, Slowed, Doomed).
- Document their exact mechanical effects:
  - Movement restrictions (0 speed, half speed)
  - Action restrictions (cannot act, disadvantage on attacks)
  - Attack modifiers (attacks against target have advantage, melee within 5ft are auto-crits)
  - Damage over time (ticks at start/end of turn)
  - Saving throw effects
  - Duration and expiration handling
- Propose GDScript architecture for status management in `godot_project/scripts/combat/StatusManager.gd` or `StatusCondition.gd` and GUT test plan.
- Deliver your report in `handoff.md` and notify parent.
