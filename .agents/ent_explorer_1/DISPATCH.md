# Task Assignment: ent_explorer_1

## Objective
Investigate character assets in `assets/images/characters/`, data definitions in `dados/personagens.json` and `godot_project/scripts/`, and design the scene hierarchy and script architecture for `godot_project/scenes/entities/Character.tscn` and `godot_project/scripts/entities/Character.gd`.

## Inputs & Context Files (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/dados/personagens.json
- /home/anderson/Documents/projeto/RPG-battle/assets/images/characters/

## Detailed Scope
1. Survey Character Assets:
   - Check available character images and textures in `assets/images/characters/` (e.g. Guerreiro, Mago, Arqueiro, Ladino, Clerigo, etc.).
   - Verify file formats, resolutions, and naming conventions.
2. Design `Character.tscn` Hierarchy:
   - Root: `CharacterBody2D` (or `Node2D`) with `class_name Character`.
   - Visual nodes:
     * `Sprite2D`: Main character sprite (with texture loading and fallback safety).
     * `SelectionHighlight`: Visual highlight (e.g. Line2D, circle, or modulated highlight sprite/rect) for selection state.
     * `RetroHPBar`: Retro pixel-style health bar (background border, fill bar, color shift green -> yellow -> red based on HP percentage).
     * `StatusContainer`: Container (HBoxContainer or Node2D) displaying active status effect icons/badges (Envenenado, Atordoado, Foco, Sangramento, etc.).
3. Design `Character.gd` API:
   - Statically typed GDScript with `@export` and strict typing.
   - Methods:
     * `initialize_from_data(data: Dictionary)` or `set_character_name(name: String, max_hp: int)`
     * `take_damage(amount: int) -> int`
     * `heal(amount: int) -> int`
     * `set_selected(selected: bool)`
     * `add_status_effect(effect_name: String)`
     * `remove_status_effect(effect_name: String)`
     * `has_status_effect(effect_name: String) -> bool`
   - Signals: `hp_changed(current_hp, max_hp)`, `died()`, `selection_changed(is_selected)`, `status_effect_applied(effect_name)`, `status_effect_removed(effect_name)`.

## Output Requirements
- Write your exploration report to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/exploration_report.md`
- Write your completion handoff to:
  `/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/handoff.md`
- Update `progress.md` with timestamps during your work.
- Send a completion message via `send_message` back to orchestrator (`parent`).

## 2026-10-01T06:03:00Z
You are ent_explorer_1. Your working directory is /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1.

Read your task instructions at:
/home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/DISPATCH.md

Also read:
- /home/anderson/Documents/projeto/RPG-battle/.agents/ORIGINAL_REQUEST.md (MANDATORY: read first)
- /home/anderson/Documents/projeto/RPG-battle/PROJECT.md
- /home/anderson/Documents/projeto/RPG-battle/.agents/skills/organizacao_refatoracao/SKILL.md
- /home/anderson/Documents/projeto/RPG-battle/dados/personagens.json
- /home/anderson/Documents/projeto/RPG-battle/assets/images/characters/

Investigate character assets, data definitions, and design the scene hierarchy and script architecture for Character.tscn and Character.gd.
Write:
1. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/exploration_report.md
2. /home/anderson/Documents/projeto/RPG-battle/.agents/ent_explorer_1/handoff.md

Update progress.md as you work. Send a message to parent (5dbb519a-f6c3-4b1f-b7e0-6ec494d60de9) with your summary and handoff path.
