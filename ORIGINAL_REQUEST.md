# Original User Request

## Initial Request — 2026-09-26T12:28:36Z

Use a multi-agent team with specialized tracks (Architecture, Rules, Entities, Deckbuilder, UI/UX, Multiplayer, QA/GUT)

Migração completa do RPG-battle para Godot Engine 4 (GDScript tipado estaticamente), mantendo 100% de paridade das regras táticas de combate (D&D 5e), tabuleiro, modo Cerco contra Isectum, Duelo de Castas, assets e cliente multiplayer co-op com suíte de testes automatizados via GUT.

Working directory: /home/anderson/Documents/projeto/RPG-battle/godot_project
Integrity mode: demo

## Reference Material
- Implementação de referência e regras de combate: `src/motor_combate.py`, `src/tabuleiro.py`, `src/juiz_combate.py`, `src/cerco_isectum.py`, `src/castas_isectum.py`.
- Suíte canônica de testes de validação: `tests/`.
- Assets visuais e áudio: `assets/images/`, `assets/sounds/`.
- Dados estruturados de classes e fases: `dados/personagens.json`, `dados/fases/`.
- Protocolo WebSocket Co-op: `src/server/protocol.py`, `src/server/room_manager.py`.

## Requirements

### R1. Estrutura do Projeto Godot 4 & Arquitetura Modular
Inicializar o projeto Godot 4 em `godot_project/` com viewport 1280x720, modo 2D e renderizador Compatibility (permitindo exportação WebAssembly e Desktop). Configurar os Autoloads / Singletons globais:
- `GameManager.gd`: Máquina de estados do jogo (Menu Principal, Batalha Tática, Cerco contra Isectum, Fim de Jogo).
- `EventBus.gd`: Barramento de sinais globais desacoplados (`unit_moved`, `damage_dealt`, `card_played`, `round_resolved`, etc.).
- `DataManager.gd`: Parser e repositório centralizado dos arquivos JSON de `dados/`.

### R2. Tabuleiro Tático 2D & Motor de Regras de Combate (D&D 5e)
Portar as regras táticas para scripts GDScript puros e desacoplados da renderização:
- Grid tático 20x20 utilizando AStar2D nativo para cálculo de caminhos, custos de terreno e bloqueio por paredes.
- Sistema de elevação, linha de visão e cálculo de coberturas (meia cobertura +2 AC, cobertura total).
- Resolução de combate D&D 5e: rolagem de d20 + modificadores vs Classe de Armadura (AC), Vantagem / Desvantagem, Acerto Crítico (20 natural), Testes de Resistência contra a Morte (*Death Saving Throws*) e Efeitos de Status (Envenenado, Atordoado, Foco, Sangramento).

### R3. Entidades, Classes de Personagens & Castas Isectum
- Cena base `scenes/entities/Character.tscn` com suporte a `AnimatedSprite2D` / `Sprite2D` mapeando os PNGs de `assets/images/characters/`, barra de vida com contorno retro e highlight de seleção.
- `Custom Resources` (`CharacterData.gd`) com paridade para todos os heróis (Aquele, Stark, Elden, Doom, Gruu, Kuro, Darwin, Novak, Rilem, Yukito, Koema) e os 24 insetos Isectum descritos em `src/castas_isectum.py` com seus efeitos únicos.

### R4. Modo Cerco contra Isectum & Deckbuilding de Sincronia
Portar as regras do modo Cerco:
- Cena `Card.tscn` interativa com animação em leque na mão, custos e badges de Movimento, Trabalho e Escavação.
- Turno de Sincronia Simultânea Co-op com cálculo de combos de Sinergia (Suprema e de Equipe).
- Ações Livres no tabuleiro da fortaleza: gastar pontos de movimento, atacar alvos e escavar rochas para materiais (Madeira, Metal, Cristal).

### R5. Interface Gráfica (HUD Dark Fantasy) & Áudio
- Interface gráfica construída em Control Nodes (CanvasLayer): barra superior de recursos, roster lateral de heróis com HP dinâmico e log de combate rolável colorido (`RichTextLabel`).
- Efeitos visuais: Floating Combat Text para dano/cura com interpolação `Tween`, flashes de impacto e integração dos efeitos sonoros e músicas de `assets/sounds/` via `AudioStreamPlayer`.

### R6. Cliente de Rede Co-op WebSocket
- Cliente WebSocket integrado em GDScript conectando ao backend FastAPI existente em `/ws/{room_id}/{player_id}`.
- Serialização e desserialização tipada de todos os eventos do protocolo (`SELECT_HERO`, `SELECT_CARD`, `MOVE_HERO`, `ATTACK_TARGET`, `WORK_ACTION`, `STATE_UPDATE`).

### R7. Suíte de Testes Automatizados via GUT (Godot Unit Testing)
- Instalar e configurar o framework GUT em `godot_project/addons/gut/` e `godot_project/test/`.
- Portar e implementar testes unitários cobrindo as regras fundamentais equivalentes à suíte Python (`tests/`):
  * Testes de movimentação A*, limites do tabuleiro e colisões.
  * Testes de acerto, dano, AC, death saves e condições de status.
  * Testes de regras de cartas, sinergias e economia de ações do Cerco.
- Todos os testes devem rodar via linha de comando em modo headless (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`) com 100% de sucesso.

## Acceptance Criteria

### Integridade do Projeto
- [ ] O projeto Godot 4 é inicializado em `godot_project/project.godot` com renderizador Compatibility e resolução base 1280x720.
- [ ] O projeto abre e roda sem erros no editor ou via CLI.
- [ ] Os assets visuais e sonoros originais de `assets/` são carregados sem arquivos faltantes ou placeholders quebrados.

### Paridade de Regras e Lógica
- [ ] O motor tático reproduz a mesma resolução matemática de combate D&D 5e e custos de terreno do projeto original.
- [ ] Todos os 24 insetos Isectum e cartas de Ação/Upgrade/Runa do modo Cerco estão implementados e funcionais.
- [ ] O cliente WebSocket envia e recebe mensagens no mesmo formato JSON esperado pelo servidor FastAPI (`src/server/protocol.py`).

### Verificação Automatizada (Forcing Function)
- [ ] A suíte de testes GUT é executável de forma autônoma via CLI em modo headless.
- [ ] 100% dos testes unitários portados passam com código de saída 0 e sem warnings críticos.

## Follow-up — 2026-09-26T16:53:31Z

[DECISÃO DO USUÁRIO — PIVOT ESTRATÉGICO DE ESCOPO]

O usuário redefiniu oficialmente o escopo do projeto:
FOCO EXCLUSIVO NO "CERCO DA FORTALEZA CONTRA ISECTUM" (o jogo de tabuleiro tático de deckbuilding, fortaleza, zonas de produção, dados D6 customizados, 24 castas de insetos e co-op).

DIRETRIZES DE PIVOTAGEM:
1. PODAR REGRAS D&D TRADICIONAIS:
   - Remover dependência de regras complexas de D&D 5e tradicional (14 tipos de dano D&D, d20 de combate padrão, Death Saves tradicionais, atributos de D&D fora do contexto do Cerco).
2. PRIORIDADE ABSOLUTA PARA O CERCO:
   - Tabuleiro da Fortaleza: 17 zonas lógicas mapeadas na grade 20x20 (Câmara Central, Carpintaria, Curtume, Fundição, Pátio, 4 Muralhas, 4 Torres, 4 Campos de Spawn), com elevações e fluxo de invasão.
   - Motor do Cerco (CercoCombatJudge / juiz_combate.py): Dado D6 customizado (Impactos e Disparos de Balestra), combate Melee (2 impactos = 1 dano), combate Ranged das Torres (1 disparo = 1 dano), Brutamontes (3 círculos de HP), Infiltradores e Catapulta.
   - 24 Castas Isectum (castas_isectum.py): Insetos com habilidades únicas, cartas de Runa e Defesa.
   - Deckbuilder & Economia (cerco_isectum.py): Cartas básicas (Marcha, Trabalho, Escavação), mercado de upgrades, produção nas oficinas (Madeira, Couro, Metal, Cristal) e Turno de Sincronia Co-op com combos de Sinergia.
   - HUD & Cena do Cerco: Mão de cartas em leque, tabuleiro com highlight de zonas, placar de recursos e log do cerco.
   - Suíte GUT: Testes focados 100% nas regras do Cerco, tabuleiro, dados D6 e castas Isectum.

## Follow-up — 2026-10-01T00:38:03Z

O servidor foi reiniciado. Por favor, retome a execução contínua do projeto com foco exclusivo no Cerco da Fortaleza contra Isectum (Tabuleiro das 17 zonas da fortaleza, Juiz de Combate com dados D6 customizados, 24 Castas Isectum, Deckbuilder e Sincronia Co-op). Avance com os marcos e testes GUT!
