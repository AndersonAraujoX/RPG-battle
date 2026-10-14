---
name: organizacao_refatoracao
description: Diretrizes de arquitetura limpa, padrão de refatoração, organização de pastas e testes unitários para o projeto RPG-battle.
---

# Skill de Organização & Refatoração de Código (RPG-battle)

Esta Skill define os padrões de arquitetura, refatoração de código, higienização da estrutura de arquivos e suíte de testes unitários para o projeto **RPG-battle**.

---

## 🏛️ 1. Arquitetura de Pastas Recomendada

Para manter o repositório escalável e despoluído, siga a seguinte estrutura modular:

```text
RPG-battle/
├── .agents/
│   └── skills/                  # Skills do projeto
│       └── organizacao_refatoracao/
│           └── SKILL.md
├── assets/                      # Imagens, sons e fontes do jogo
├── dados/                       # Definições em JSON (personagens, cartas, terrenos)
├── src/                         # Código-fonte principal
│   ├── core/                    # Engine principal, Game loop, Config, Utils
│   │   ├── config.py
│   │   ├── game.py
│   │   └── utils.py
│   ├── engine/                  # Motor de regras e simuladores
│   │   ├── motor_combate.py
│   │   ├── juiz_combate.py
│   │   ├── tabuleiro.py
│   │   └── simulador_ag_real.py
│   ├── entities/                # Personagens, Inimigos e Bosses
│   │   ├── personagens/
│   │   └── castas_isectum.py
│   ├── states/                  # Gerenciador de Estados da Tela
│   │   ├── cerco/               # Módulos isolados do CercoState (state, turn, draw, input)
│   │   ├── menu.py
│   │   └── renderer.py
│   └── ui/                      # Componentes reutilizáveis de interface gráfica
│       ├── componentes.py
│       └── render_combate.py
├── tests/                       # Suíte de testes unitários (pytest)
│   ├── test_motor.py
│   ├── test_tabuleiro.py
│   └── test_cerco_state.py
├── tools/                       # Scripts auxiliares e geradores
│   ├── converter_audio.py
│   └── slice_sprites.py
├── main.py                      # Ponto de entrada do jogo
└── README.md
```

---

## 🧹 2. Regras de Limpeza da Raiz

1. **Arquivos Temporários de Debug**:
   - Mover arquivos no estilo `debug_*.py`, `test_*.txt` e `reproduce_crash.py` para a pasta `tools/` ou `scratch/`.
   - Nunca manter backups (`*.bak`) no diretório `src/`.

2. **Arquivos de Dados e Saves**:
   - Saves locais (`savegame.pkl`, `campaign_save.json`) e mapas customizados devem permanecer na raiz ou em `dados/saves/`.

---

## 🧼 3. Padrão de Sanitização de Fontes e Emojis em Pygame

Como as fontes padrão de bitmap do Linux/Pygame não possuem glifos Unicode emoji de 4 bytes:

1. **Uso Obrigatório de `sanitizar_texto_fonte()`**:
   - Sempre passar qualquer string que possa conter ícones ou símbolos pela função `sanitizar_texto_fonte(texto)` em `src/utils.py` antes de chamar `font.render()`.
   - Exemplo:
     ```python
     from src.utils import sanitizar_texto_fonte
     lbl = fonte.render(sanitizar_texto_fonte("❤️ 50/50  ⚔️ +5  🛡️ 14"), True, (255, 255, 255))
     ```

---

## 🧪 4. Diretriz Obrigatória de Testes Unitários (SOLID + AAA)

Para toda nova funcionalidade ou refatoração implementada:

1. **Estrutura Arrange-Act-Assert (AAA)**:
   ```python
   def test_parry_reduz_dano_e_contra_ataca():
       # Arrange (Preparar)
       heroi = Guerreiro("Guerreiro", pos_x=5, pos_y=5)
       inimigo = Invasor("Invasor", pos_x=5, pos_y=6, hp_atual=20)
       
       # Act (Executar)
       resultado = heroi.executar_parry(inimigo)
       
       # Assert (Verificar)
       assert heroi.hp_atual == 50  # Dano anulado
       assert inimigo.hp_atual < 20  # Recebeu contra-ataque Riposte
   ```

2. **Cobertura Mínima**:
   - Fluxo principal (Caminho feliz).
   - Casos de borda (coleções vazias, limites de tabuleiro, unidades mortas).
   - Validação de exceções e tratamento de erros.
