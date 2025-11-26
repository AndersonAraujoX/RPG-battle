# Simulador de Batalha Tático - Projeto Gemini

Este documento resume o desenvolvimento de um simulador de batalha baseado em turnos, com foco em mecânicas de RPG de mesa, como iniciativa, classes de personagens e habilidades especiais, culminando na implementação de um tabuleiro 2D para combate tático e uma interface gráfica.

## Ideia Central

O projeto começou com a ideia de um simulador de combate por turnos, onde personagens com atributos básicos (HP, AC, Bônus de Ataque) lutariam com base na iniciativa. O objetivo era simular um combate tático até que um dos times fosse derrotado, agora com uma interface gráfica rica.

## Evolução e Arquitetura Atual

O projeto evoluiu significativamente, passando de uma simulação puramente em console para uma aplicação Pygame completa. Diversas melhorias arquitetônicas foram implementadas para aumentar a modularidade, manutenibilidade e extensibilidade do código.

### 1. Estrutura Básica de Combate & Personagens
-   **Engine:** O jogo agora utiliza `Pygame` para renderização gráfica, áudio e tratamento de eventos.
-   **Classes de Personagem:** `Personagem` (base), `Guerreiro`, `Mago`, `Ladino`, `Arqueiro`, `Bárbaro`, `Clérigo` e `Chefe` com atributos e dados de dano distintos.
-   **Configuração de Times:** A composição dos times é configurada via UI no menu principal.
-   **Iniciativa:** Rolagem de d20 + modificador de destreza para determinar a ordem de combate.
-   **Loop de Combate:** Iteração por turnos, onde cada personagem vivo executa uma ação.
-   **Mecânica de Ataque:** Rolagem de d20 + bônus de ataque vs. AC do alvo, seguida por rolagem de dano.
-   **Condição de Fim:** O combate termina quando todos os membros de um time são derrotados.

### 2. Melhorias Arquitetônicas e Refinamentos

-   **Modularização do `visualizador.py`:** O loop principal do jogo foi refatorado e dividido em funções menores (`handle_events`, `update_game_logic`, `draw_elements`) para melhor organização e legibilidade. Variáveis de estado globais foram centralizadas.
-   **Refatoração do Módulo de IA:** A lógica de Inteligência Artificial foi desacoplada de `motor_combate.py` e integrada diretamente nas classes de personagem através do método `decidir_acao()`. Cada personagem agora decide sua própria ação (curar, atacar, mover, fugir, usar habilidade) com base no contexto do combate.
-   **Módulo de Utilidades (`src/utils.py`):** Funções genéricas, como `calcular_distancia`, foram movidas para um módulo dedicado, evitando duplicação de código.
-   **Centralização de Constantes:** Strings "mágicas" e valores fixos foram movidos para `src/config.py`, melhorando a manutenibilidade.
-   **Efeitos de Status:** Implementado um sistema robusto para aplicar, gerenciar e processar efeitos de status (e.g., "Envenenado", "Atordoado", "Sangrando", "Fúria") nos personagens, impactando suas ações e atributos.
-   **Log de Combate Detalhado:** O console exibe informações ricas sobre cada ação, incluindo rolagens de dados (d20 + bônus) para ataque e dano, e o resultado (acerto/erro, dano causado, HP restante).
-   **IA de Alvos Inteligente:** Os personagens priorizam atacar o inimigo com o menor HP atual ou a maior ameaça.

### 3. Habilidades Especiais por Classe (Baseado em Cooldown)
As habilidades especiais foram refinadas e agora operam com um sistema de *cooldown* (tempo de recarga) em vez de chances percentuais aleatórias, adicionando uma camada estratégica mais profunda.
-   **Guerreiro:** **"Surto de Ação"** (possibilidade de um ataque extra no mesmo turno, baseado em cooldown).
-   **Mago:** **"Bola de Fogo"** (conjura uma magia de área que causa dano a múltiplos personagens, baseada em cooldown. A IA do Mago tenta maximizar o número de alvos atingidos).
-   **Ladino:** **"Ataque Furtivo"** (adiciona dano extra ao ataque quando o cooldown permite).
-   **Clérigo:** **"Canalizar Divindade"** (habilidade de cura para aliados, baseada em cooldown. A IA do Clérigo prioriza curar aliados com baixa vida).

### 4. Implementação do Tabuleiro 2D (Tático)

A maior evolução do projeto foi a introdução de um tabuleiro 2D, transformando o simulador em um ambiente tático com visualização gráfica:
-   **Classe `Tabuleiro`:** Gerencia a grade (20x20), a posição dos personagens, movimentação e detecção de personagens em área. Suporta diferentes tipos de terreno (NORMAL, FLORESTA, DIFICIL, PAREDE).
-   **Posicionamento:** Personagens possuem coordenadas `pos_x` e `pos_y`. No setup, os times são posicionados em lados opostos do tabuleiro.
-   **Movimento:** Cada personagem tem uma `velocidade` e se move em direção ao alvo (ou foge), considerando o custo de movimento do terreno e evitando quadrados ocupados.
-   **Alcance de Ataque:** Personagens possuem um `alcance` definido (ex: 1 para corpo a corpo, 6 para magos), e só podem atacar alvos dentro desse raio.

## Como Executar

Para executar o simulador, utilize o seguinte comando no terminal na pasta raiz do projeto:

```bash
python main.py
```

O jogo iniciará no menu principal, onde você poderá configurar os times e iniciar a batalha.

## Próximos Passos Potenciais

-   **Melhorias na UI/UX:** Exibição da ordem de iniciativa, indicadores de cooldown, feedback visual para ações inválidas e *indicadores visuais para efeitos de status*.
-   **Refinamento da IA:** Lógicas mais avançadas para evitar fogo amigo do Mago, foco estratégico em alvos específicos, etc.
-   **Novas Classes e Habilidades:** Expandir a variedade de personagens e suas capacidades.
-   **Sistema de Itens:** Introduzir consumíveis e equipamentos.
-   **Níveis de Personagem:** Permitir escolhas de habilidades ou atributos ao subir de nível.
-   **Salvar/Carregar Jogo:** Implementar a funcionalidade de persistência do estado do jogo.
-   **Balanceamento:** Ajustar os valores de HP, AC, dano e probabilidades de habilidades para otimizar a experiência de jogo.
