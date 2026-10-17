# Skill de Prevenção de Execução Infinita & Timeouts (RPG-battle)
(Local copy in challenger_m4_1)

Key Takeaways:
1. Always use timeouts on CLI executions (`timeout 30s ...`).
2. Verify while loops have static bounds (`MAX_ATTEMPTS`).
3. Scripts running under Godot CLI need graceful termination.
4. Stress-test generators for infinite loop potential under empty/invalid input.
