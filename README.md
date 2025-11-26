# RPG-battle - Simulador de Batalha Tático com Pygame

Este projeto é um simulador de batalha por turnos com elementos de RPG de mesa, implementado utilizando a biblioteca Pygame para uma interface gráfica interativa. O objetivo principal é simular combates táticos entre diferentes classes de personagens, cada um com atributos e habilidades únicas.

## Funcionalidades Principais

-   **Interface Gráfica (Pygame):** O simulador agora conta com uma interface visual que exibe o tabuleiro 2D, a movimentação dos personagens, efeitos de combate e um log detalhado das ações.
-   **Classes de Personagem:** Inclui classes como Guerreiro, Mago, Ladino, Arqueiro, Bárbaro, Clérigo e um chefe, cada um com atributos (HP, AC, dados de dano) e habilidades especiais.
-   **Combate Tático em Turnos:** Os personagens agem em uma ordem definida por iniciativa. O combate ocorre em um tabuleiro 2D, onde o posicionamento e a movimentação são cruciais.
-   **Habilidades Especiais:** Personagens possuem habilidades únicas baseadas em `cooldowns` (tempo de recarga), como "Surto de Ação" (Guerreiro), "Bola de Fogo" (Mago) e "Ataque Furtivo" (Ladino), e "Canalizar Divindade" (Clérigo).
-   **Inteligência Artificial (IA):** Inimigos controlados pela IA decidem suas ações (atacar, mover, usar habilidades, fugir) de forma estratégica, priorizando alvos e maximizando o impacto de suas habilidades.
-   **Sistema de Terreno:** O tabuleiro pode gerar diferentes tipos de terreno (normal, floresta, difícil, parede) que afetam a movimentação e a defesa dos personagens.
-   **Efeitos de Status:** Implementado um sistema para aplicar, gerenciar e processar efeitos de status (e.g., "Envenenado", "Atordoado", "Sangrando", "Fúria") nos personagens, impactando suas ações e atributos.
-   **Progressão de Personagem:** Personagens ganham XP e podem subir de nível.

## Estrutura do Projeto e Melhorias Arquitetônicas

O projeto foi refatorado para melhorar a modularidade e a manutenibilidade:

-   **`main.py`:** Ponto de entrada da aplicação.
-   **`src/ui/visualizador.py`:** Contém o loop principal do jogo e a lógica de renderização da interface Pygame, agora modularizado em funções para eventos, lógica de jogo e desenho.
-   **`src/motor_combate.py`:** A lógica central do combate. Foi refatorado para integrar as decisões de IA diretamente nos objetos dos personagens.
-   **`src/personagens/`:** Contém as definições de todas as classes de personagem, incluindo seus atributos, habilidades e lógica de IA (`decidir_acao`). Inclui o novo módulo `status_efeito.py` para gerenciamento de efeitos de status.
-   **`src/tabuleiro.py`:** Gerencia o estado do tabuleiro 2D, o posicionamento dos personagens e os tipos de terreno.
-   **`src/config.py`:** Centraliza todas as constantes do jogo (tamanhos de tela, cores, estados de jogo, tipos de terreno, etc.), incluindo as propriedades dos efeitos de status.
-   **`src/utils.py`:** Módulo para funções utilitárias genéricas, como `calcular_distancia`.
-   **`assets/`:** Recursos do jogo, como arquivos de áudio.

## Como Executar

Para executar o simulador, siga os passos abaixo:

1.  **Pré-requisitos:** Certifique-se de ter o Python 3 instalado.
2.  **Instalar Pygame:** Se ainda não tiver, instale a biblioteca Pygame:
    ```bash
    pip install pygame
    ```
3.  **Executar o Jogo:** Navegue até a pasta raiz do projeto no terminal e execute:
    ```bash
    python main.py
    ```
    O jogo iniciará no menu principal, onde você poderá configurar os times e iniciar a batalha.

## Próximos Passos (Potenciais Melhorias)

-   **Melhorias na UI/UX:** Exibição da ordem de iniciativa, indicadores de cooldown, feedback visual para ações inválidas e *indicadores visuais para efeitos de status*.
-   **Refinamento da IA:** Lógicas mais avançadas para evitar fogo amigo do Mago, foco estratégico em alvos específicos, etc.
-   **Novas Classes e Habilidades:** Expandir a variedade de personagens e suas capacidades.
-   **Sistema de Itens:** Introduzir consumíveis e equipamentos.
-   **Níveis de Personagem:** Permitir escolhas de habilidades ou atributos ao subir de nível.
-   **Salvar/Carregar Jogo:** Implementar a funcionalidade de persistência do estado do jogo.
-   **Balanceamento:** Ajustar os valores de HP, AC, dano e probabilidades de habilidades para otimizar a experiência de jogo.