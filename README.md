# RPG-battle - Simulador de Batalha Tático com Pygame

Este projeto é um simulador de batalha por turnos com elementos de RPG de mesa, implementado utilizando a biblioteca Pygame para uma interface gráfica interativa. O objetivo principal é simular combates táticos entre diferentes classes de personagens, cada um com atributos e habilidades únicas.

## Funcionalidades Principais

-   **Interface Gráfica (Pygame):** O simulador conta com uma interface visual rica que exibe o tabuleiro 2D, a movimentação dos personagens, efeitos de combate e um log detalhado das ações.
-   **Classes de Personagem:** Inclui classes como Guerreiro, Mago, Ladino, Arqueiro, Bárbaro, Clérigo, Paladino, Druida, Bruxo e diversos inimigos (Rei Goblin, Lorde Lich, Dragão Ancião), cada um com atributos e habilidades especiais.
-   **Combate Tático em Turnos:** Os personagens agem em uma ordem definida por iniciativa. O combate ocorre em um tabuleiro 2D, onde o posicionamento e a movimentação são cruciais.
-   **Habilidades Especiais:** Personagens possuem habilidades únicas baseadas em recursos (Mana, Energia, Fé) e cooldowns, como "Bola de Fogo", "Ataque Furtivo", "Canalizar Divindade" e "Forma de Urso".
-   **Inteligência Artificial (IA):** Inimigos controlados pela IA decidem suas ações (atacar, mover, usar habilidades, fugir) de forma estratégica.
-   **Sistema de Terreno:** O tabuleiro suporta diferentes tipos de terreno (normal, floresta, difícil, parede, gelo) que afetam a movimentação e a defesa.
-   **Efeitos de Status:** Sistema robusto de status (Envenenado, Atordoado, Sangrando, etc.) com indicadores visuais.
-   **Modo Campanha:** Sistema de progressão onde o jogador enfrenta batalhas de dificuldade crescente.
-   **Editor de Mapas:** Ferramenta para criar e salvar mapas personalizados.
-   **Sistema de Equipamentos:** Armas, armaduras e acessórios que alteram os atributos dos personagens.

## Estrutura do Projeto

-   **`main.py`:** Ponto de entrada da aplicação.
-   **`src/game.py`:** Gerencia o loop principal do jogo e estados.
-   **`src/ui/`:** Módulos de interface gráfica (`menu.py`, `desenho.py`, `componentes.py`).
-   **`src/motor_combate.py`:** Lógica central do combate.
-   **`src/personagens/`:** Definições das classes de personagem e IA.
-   **`src/tabuleiro.py`:** Gerenciamento do tabuleiro e terrenos.
-   **`src/itens/`:** Implementação de armas, armaduras e acessórios.
-   **`src/config.py`:** Constantes e configurações globais.
-   **`src/utils.py`:** Funções utilitárias.

## Como Executar

### Versão Compilada (Recomendado)
Para jogar sem precisar instalar nada, basta executar o arquivo binário gerado:

1.  Navegue até a pasta `dist`:
    ```bash
    cd dist
    ```
2.  Execute o jogo:
    ```bash
    ./OsEsquecidos
    ```

### Rodando do Código Fonte
Se preferir rodar via Python:

1.  **Pré-requisitos:** Python 3 instalado.
2.  **Instalar Dependências:**
    ```bash
    pip install pygame
    ```
3.  **Executar o Jogo:**
    ```bash
    python main.py
    ```

## Compilando o Projeto
Para gerar o executável você mesmo:
```bash
./build.sh
```
Isso criará o arquivo `OsEsquecidos` na pasta `dist/`.

## Próximos Passos

-   **Melhorias na UI/UX:** Mais animações e feedback visual.
-   **Refinamento da IA:** Comportamentos de grupo mais complexos.
-   **Expansão de Conteúdo:** Novas classes (Necromante, Bardo) e itens consumíveis.