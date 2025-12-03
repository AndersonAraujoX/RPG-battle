# Simulador de Batalha Tático - Projeto Gemini

Este documento resume o desenvolvimento de um simulador de batalha baseado em turnos, com foco em mecânicas de RPG de mesa, como iniciativa, classes de personagens e habilidades especiais, culminando na implementação de um tabuleiro 2D para combate tático e uma interface gráfica.

## Ideia Central

O projeto começou com a ideia de um simulador de combate por turnos, onde personagens com atributos básicos (HP, AC, Bônus de Ataque) lutariam com base na iniciativa. O objetivo era simular um combate tático até que um dos times fosse derrotado, agora com uma interface gráfica rica.

## Evolução e Arquitetura Atual

O projeto evoluiu significativamente, passando de uma simulação puramente em console para uma aplicação Pygame completa. Diversas melhorias arquitetônicas foram implementadas para aumentar a modularidade, manutenibilidade e extensibilidade do código.

### 1. Estrutura Básica de Combate & Personagens
-   **Engine:** O jogo agora utiliza `Pygame` para renderização gráfica, áudio e tratamento de eventos.
-   **Classes de Personagem:** `Personagem` (base), `Guerreiro`, `Mago`, `Ladino`, `Arqueiro`, `Bárbaro`, `Clérigo`, `Paladino`, `Druida`, `Bruxo` e `Chefe`, `ReiGoblin`, `LordeLich`, `DragaoAnciao`, `Goblin`, `Esqueleto`, `Kobold` com atributos e dados de dano distintos.
-   **Configuração de Times:** A composição dos times é configurada via UI no menu principal, incluindo seleção de chefes.
-   **Iniciativa:** Rolagem de d20 + modificador de destreza para determinar a ordem de combate.
-   **Loop de Combate:** Iteração por turnos, onde cada personagem vivo executa uma ação.
-   **Mecânica de Ataque:** Rolagem de d20 + bônus de ataque vs. AC do alvo, seguida por rolagem de dano. Inclui bônus por flanqueamento, vantagens de elevação e chance de erro por cobertura.
-   **Condição de Fim:** O combate termina quando todos os membros de um time são derrotados.

### 2. Melhorias Arquitetônicas e Refinamentos

-   **Modularização do `visualizador.py`:** O loop principal do jogo foi refatorado e dividido em funções menores (`handle_events`, `update_game_logic`, `draw_elements`) para melhor organização e legibilidade. Variáveis de estado globais foram centralizadas.
-   **Refatoração do Módulo de IA:** A lógica de Inteligência Artificial foi desacoplada de `motor_combate.py` e integrada diretamente nas classes de personagem através do método `decidir_acao()`. Cada personagem agora decide sua própria ação (curar, atacar, mover, fugir, usar habilidade) com base no contexto do combate. A IA foi aprimorada para uso inteligente de cobertura e ataques de oportunidade, e para coordenação de ataques entre unidades.
-   **Módulo de Utilidades (`src/utils.py`):** Funções genéricas, como `calcular_distancia`, e carregamento de dados JSON para personagens, foram movidas para um módulo dedicado, evitando duplicação de código.
-   **Centralização de Constantes:** Strings "mágicas" e valores fixos foram movidos para `src/config.py`, melhorando a manutenibilidade.
-   **Efeitos de Status:** Implementado um sistema robusto para aplicar, gerenciar e processar efeitos de status (e.g., "Envenenado", "Atordoado", "Sangrando", "Fúria", "Amaldiçoado") nos personagens, impactando suas ações e atributos, incluindo imunidades a status específicos.
-   **Log de Combate Detalhado:** O console exibe informações ricas sobre cada ação, incluindo rolagens de dados (d20 + bônus) para ataque e dano, e o resultado (acerto/erro, dano causado, HP restante).
-   **Sistema de Recursos (Mana/Energia/Fé):** Habilidades agora consomem recursos específicos da classe (Mana para Magos, Energia para Ladinos, Fé para Clérigos), com regeneração por turno.

### 3. Habilidades Especiais por Classe (Baseado em Recursos)
As habilidades especiais foram refinadas e agora operam com um sistema de *recursos* (mana/energia/fé) em vez de *cooldown* (tempo de recarga) em alguns casos, adicionando uma camada estratégica mais profunda.
-   **Guerreiro:** **"Surto de Ação"** (possibilidade de um ataque extra no mesmo turno, baseado em cooldown).
-   **Mago:** **"Bola de Fogo"** (conjura uma magia de área que causa dano a múltiplos personagens, baseada em mana. A IA do Mago tenta maximizar o número de alvos atingidos) e **"Raio de Gelo"** (causa dano e tem chance de criar terreno de Gelo).
-   **Ladino:** **"Ataque Furtivo"** (adiciona dano extra ao ataque quando há energia disponível).
-   **Clérigo:** **"Canalizar Divindade"** (habilidade de cura para aliados, baseada em fé. A IA do Clérigo prioriza curar aliados com baixa vida).
-   **Druida:** **"Forma de Urso"** (transforma o Druida em uma forma mais resistente e forte, consumindo Fúria da Natureza).
-   **Bruxo:** **"Maldição de Agonia"** (aplica um efeito de status "Amaldiçoado" que causa dano ao longo do tempo e reduz atributos, consumindo mana).
-   **ReiGoblin:** **"Convocar Goblin"** (convoca um minion Goblin para o combate).
-   **Chefe:** **"Pisão Trovejante"** (causa dano em área).

### 4. Implementação do Tabuleiro 2D (Tático)

A maior evolução do projeto foi a introdução de um tabuleiro 2D, transformando o simulador em um ambiente tático com visualização gráfica:
-   **Classe `Tabuleiro`:** Gerencia a grade (20x20), a posição dos personagens, movimentação e detecção de personagens em área. Suporta diferentes tipos de terreno (NORMAL, FLORESTA, DIFICIL, PAREDE, GELO) e elevação (Eixo Z).
-   **Posicionamento:** Personagens possuem coordenadas `pos_x`, `pos_y` e `elevacao`. No setup, os times são posicionados em lados opostos do tabuleiro.
-   **Movimento:** Cada personagem tem uma `velocidade` e se move em direção ao alvo (ou foge), considerando o custo de movimento do terreno e evitando quadrados ocupados. Implementado Ataques de Oportunidade e o efeito de escorregão em Terreno de Gelo.
-   **Alcance de Ataque:** Personagens possuem um `alcance` definido (ex: 1 para corpo a corpo, 6 para magos), e só podem atacar alvos dentro desse raio. Linha de Visão é verificada antes de ataques.

### 5. Sistema de Equipamentos
-   **Armas:** Implementado sistema de armas (Espada Longa, Adaga, Arco Curto, Machado Grande), que alteram os dados de dano do personagem.
-   **Armaduras:** Implementado sistema de armaduras (Couraça de Couro, Cota de Malha, Placas de Aço), que alteram a AC base do personagem.
-   **Acessórios:** Implementado sistema de acessórios (Anel de Força, Amuleto de Vitalidade, Botas da Velocidade), que fornecem bônus passivos aos atributos dos personagens.

### 6. Melhorias de UI/UX
-   **Indicadores Visuais de Status:** Exibição de ícones para efeitos de status.
-   **Pré-visualização de Movimento e Ataque:** Destaque de unidades aliadas que podem atacar um inimigo sob o mouse.
-   **Ordem de Turnos Visual:** Barra de iniciativa no topo da tela com retratos dos personagens.
-   **Feedback de Ação Inválida:** Som e visual "X" vermelho para ações impossíveis.
-   **Controles de Volume:** Opções no menu principal para ajustar o volume dos efeitos sonoros.

### 7. Melhorias Técnicas
-   **Salvar/Carregar Jogo:** Funcionalidade completa para salvar e carregar o estado atual do combate usando `pickle`.
-   **Definições em Arquivos Externos:** Estatísticas de todos os personagens carregadas dinamicamente de `dados/personagens.json`, facilitando a configuração e o balanceamento.

## Como Executar

Para executar o simulador, utilize o seguinte comando no terminal na pasta raiz do projeto:

```bash
python3 main.py
```

O jogo iniciará no menu principal, onde você poderá configurar os times e iniciar a batalha.

## Próximos Passos Potenciais

Estas são as ideias para o futuro do projeto, agrupadas por categoria:

### Mecânicas de Gameplay Avançadas
-   **IA Mais Complexa:**
    -   Coordenação de ataques entre unidades (combos mais elaborados).
    -   Comportamento de fuga/cura em desvantagem mais sofisticado.

### Polimento de UI/UX
-   **Tooltips Detalhados:** Exibir descrições ao passar o mouse sobre habilidades, itens e status.
-   **Mais Animações:**
    -   Esquiva (movimento ao errar ataque).
    -   Bloqueio (animação de defesa com escudo).
    -   Ataques Críticos (impacto visual maior).
-   **Polimento de Áudio:** Variedade de sons por tipo de arma e elemento mágico.

### Expansão de Conteúdo
-   **Novas Classes Avançadas:**
    -   Necromante: Invocação de mortos-vivos.
    -   Alquimista: Suporte com poções (buffs/debuffs).
    -   Bardo: Buffs e Debuffs em área via música.
-   **Itens Consumíveis:**
    -   Pergaminhos (magias de uso único).
    -   Armadilhas (ativadas por movimento inimigo).
    -   Bombas (dano em área).