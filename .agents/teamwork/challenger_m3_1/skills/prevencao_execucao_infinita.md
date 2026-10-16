# Skill: prevencao_execucao_infinita (Local Copy)
Source: /home/anderson/Documents/projeto/RPG-battle/.agents/skills/prevencao_execucao_infinita/SKILL.md

Diretrizes, padrões arquiteturais e ferramentas de verificação para prevenir execuções infinitas, travamentos silenciosos e deadlocks em scripts Godot, Python e ferramentas de automação.
- Always use `timeout <seconds>` on Godot/Python shell invocations.
- Always use Watchdog Timer in standalone Godot scripts (`_init()` with `create_timer()` -> `quit(1)`).
- Ensure explicit `quit(0)` or `quit(code)` on completion and errors.
- Blind while loops with max iterations guards.
