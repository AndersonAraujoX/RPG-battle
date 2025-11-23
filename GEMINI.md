# Simulador de Batalha - Projeto Gemini

Este documento resume o desenvolvimento de um simulador de batalha baseado em turnos, com foco em mecânicas de RPG de mesa, como iniciativa, classes de personagens e habilidades especiais, culminando na implementação de um tabuleiro 2D para combate tático.

## Ideia Central

O projeto começou com a ideia de um simulador de combate por turnos, onde personagens (Guerreiro, Mago, Ladino) com atributos básicos (HP, AC, Bônus de Ataque) lutariam com base na iniciativa. O objetivo era simular um combate até que um dos times fosse derrotado.

## Funcionalidades Implementadas

### 1. Estrutura Básica de Combate
-   **Classes de Personagem:** `Personagem` (base), `Guerreiro`, `Mago`, `Ladino` com atributos e dados de dano distintos.
-   **Setup de Combate:** O usuário define a quantidade de personagens de cada classe por time.
-   **Iniciativa:** Rolagem de d20 para determinar a ordem de combate.
-   **Loop de Combate:** Iteração por turnos, com cada personagem vivo atacando um alvo inimigo.
-   **Mecânica de Ataque:** Rolagem de d20 + bônus de ataque vs. AC do alvo, seguida por rolagem de dano.
-   **Condição de Fim:** O combate termina quando todos os membros de um time são derrotados.

### 2. Melhorias e Refinamentos Iniciais

-   **Log de Combate Detalhado:** O console exibe informações ricas sobre cada ação, incluindo rolagens de dados (d20 + bônus) para ataque e dano, e o resultado (acerto/erro, dano causado, HP restante).
-   **IA de Alvos Inteligente:** Em vez de alvos aleatórios, os personagens agora priorizam atacar o inimigo com o menor HP atual, tornando o combate mais estratégico.
-   **Habilidades Especiais por Classe:**
    -   **Guerreiro:** **"Surto de Ação"** (25% de chance de um ataque extra no mesmo turno).
    -   **Mago:** **"Bola de Fogo"** (25% de chance de conjurar uma magia de área que causa dano a todos os personagens em um raio de 1 quadrado do alvo, incluindo aliados - "fogo amigo").
    -   **Ladino:** **"Ataque Furtivo"** (50% de chance de adicionar 1d6 de dano extra ao ataque).

### 3. Implementação do Tabuleiro 2D (Tático)

A maior evolução do projeto foi a introdução de um tabuleiro 2D, transformando o simulador em um ambiente tático:
-   **Classe `Tabuleiro`:** Gerencia a grade (20x20), a posição dos personagens, movimentação e detecção de personagens em área.
-   **Posicionamento:** Personagens agora possuem coordenadas `pos_x` e `pos_y`. No setup, os times são posicionados em lados opostos do tabuleiro.
-   **Movimento:** Cada personagem tem uma `velocidade` e, no seu turno, se move em direção ao inimigo com menor HP até ficar ao alcance de ataque. O movimento evita quadrados ocupados.
-   **Alcance de Ataque:** Personagens possuem um `alcance` definido (ex: 1 para corpo a corpo, 6 para magos), e só podem atacar alvos dentro desse raio.
-   **Visualização do Tabuleiro:** O estado do tabuleiro é impresso no console a cada turno, mostrando a localização dos personagens e seus HPs.
-   **Cálculo de Distância:** Utiliza a distância de Manhattan para determinar a proximidade entre personagens.

### 4. Entrada de Dados via Terminal

Para maior agilidade, a composição dos times agora é fornecida diretamente como argumentos de linha de comando, eliminando a necessidade de interação via `input()` durante a execução.

## Como Executar

Para executar o simulador, utilize o seguinte comando no terminal:

```bash
python simulador_de_batalha.py [G_A] [M_A] [L_A] [G_B] [M_B] [L_B]
```
Onde:
-   `[G_A]`: Número de Guerreiros para o Time A
-   `[M_A]`: Número de Magos para o Time A
-   `[L_A]`: Número de Ladinos para o Time A
-   `[G_B]`, `[M_B]`, `[L_B]`: O mesmo para o Time B.

**Exemplo:**
```bash
python simulador_de_batalha.py 1 1 1 1 1 1
```
(Simula uma batalha entre dois times com 1 Guerreiro, 1 Mago e 1 Ladino cada.)

## Próximos Passos Potenciais

-   **Refinamento da IA de Movimento:** Implementar lógicas mais avançadas para evitar fogo amigo ou buscar flanqueamento.
-   **Sistema de Atributos 5e:** Integrar Força, Destreza, Constituição, etc., para um sistema de personagem mais robusto.
-   **Níveis de Personagem:** Permitir que os personagens subam de nível, ganhando mais HP, bônus e novas habilidades.
-   **Novas Classes e Habilidades:** Expandir a variedade de personagens e suas capacidades.
-   **Balanceamento:** Ajustar os valores de HP, AC, dano e probabilidades de habilidades para otimizar a experiência de jogo.
-   **Interface Gráfica:** Desenvolver uma interface visual para o tabuleiro e o log de combate.
