---
name: prevencao_execucao_infinita
description: Diretrizes, padrões arquiteturais e ferramentas de verificação para prevenir execuções infinitas, travamentos silenciosos e deadlocks em scripts Godot, Python e ferramentas de automação.
---

# Skill de Prevenção de Execução Infinita & Timeouts (RPG-battle)

Esta Skill estabelece padrões obrigatórios de engenharia de software para impedir que scripts de testes, geradores, capturas de tela e rotinas de automação fiquem presos em **execução infinita** (*hangs*), deadlocks ou loops sem saída.

---

## 🛑 1. Diagnóstico: Por que scripts ficam rodando eternamente?

No ecossistema Godot Engine e Python, execuções infinitas ocorrem principalmente por 4 causas:

1. **Ausência de `quit()` no Fluxo de Execução:**
   - Em scripts standalone do Godot (`SceneTree` executados via `-s script.gd`), o processo da engine continua ativo indefinidamente até que `quit(code)` seja chamado explicitamente.
2. **Erros de Runtime que Abortam Callbacks sem Chamar `quit()`:**
   - Se uma exceção ou erro de tipagem estática ocorrer antes da chamada de `quit()`, a execução daquela função é abortada, o timer de saída nunca é disparado e o processo fica órfão em execução.
3. **Loops `while` sem Condição de Saída Garantida:**
   - Laços de busca, pathfinding ou geração procedural sem contador limite de tentativas (*max attempts*).
4. **Chamadas de Terminal sem Timeout do Sistema Operacional:**
   - Execução de comandos no shell sem o utilitário `timeout` como barreira externa de contenção.

---

## 🛡️ 2. Padrões Obrigatórios de Implementação

### 2.1. Padrão Watchdog Timer Obrigatório (Godot GDScript)

Todo script executado via Godot CLI (`-s tools/*.gd`) **DEVE** registrar um **Watchdog Timer** incondicional logo no `_init()`:

```gdscript
extends SceneTree

func _init() -> void:
    # ── Watchdog Fail-Safe Obrigatório ─────────────────────────────────────
    # Garante encerramento forçado do processo caso qualquer erro ou travamento ocorra
    var watchdog: SceneTreeTimer = create_timer(4.0)
    watchdog.timeout.connect(func():
        push_error("[WATCHDOG TIMEOUT] Forçando encerramento para evitar execução infinita!")
        quit(1)
    )

    # Fluxo principal protegido
    change_scene_to_file("res://scenes/main/Main.tscn")
    var timer: SceneTreeTimer = create_timer(1.5)
    timer.timeout.connect(_on_executar_tarefa)

func _on_executar_tarefa() -> void:
    # Sempre garantir que o quit(0) seja alcançado
    # ... executa a tarefa ...
    quit(0)
```

### 2.2. Barreira Externa de Timeout no Terminal (Linux / Bash)

**NUNCA** execute binários do Godot ou scripts longos sem o utilitário `timeout`:

```bash
# ❌ Incorreto: Pode rodar infinitamente se o driver gráfico ou script engasgar
godot_project/bin/godot --display-driver x11 -s tools/capture.gd

# ✅ Correto: Garante término do processo pelo SO após 10 segundos
timeout 10s godot_project/bin/godot --display-driver x11 --rendering-driver opengl3 -s tools/capture.gd
```

### 2.3. Blindagem de Loops `while` (Max Iterations Guard)

Todo loop `while` deve ter um teto estático de iterações:

```gdscript
# ✅ Correto: Impede travamento por condições não convergentes
var attempts: int = 0
const MAX_ATTEMPTS: int = 50
while condicao and attempts < MAX_ATTEMPTS:
    attempts += 1
    # ... processa passo ...
```

---

## 🔍 3. Ferramenta de Verificação Automática (`tools/verificar_timeout_scripts.py`)

A skill disponibiliza um verificador estático que inspeciona todos os scripts de `tools/` e `godot_project/tools/` para assegurar que:
- Contêm chamadas a `quit()` ou `sys.exit()`.
- Implementam o padrão de Watchdog Timer ou timeout defensivo.
- Não possuem `while True` sem contador de saída.

Execute a verificação com:
```bash
python3 tools/verificar_timeout_scripts.py
```

---

## 🧪 4. Diretriz de Testes Unitários

Conforme a diretriz de qualidade do projeto:
- Todos os scripts utilitários de verificação devem ser acompanhados de testes unitários com padrão **Arrange-Act-Assert (AAA)**, cobrindo caminho feliz, casos de borda e tratamento de erros.
