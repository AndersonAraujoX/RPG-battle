# ⚔️ Os Esquecidos: Simulador de Batalha Tático

![Banner do Jogo](https://via.placeholder.com/1000x400?text=Os+Esquecidos+-+Tactical+Battle+RPG)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg?style=for-the-badge&logo=pygame&logoColor=white)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Os Esquecidos** é um simulador de combate por turnos de alta fidelidade, que transporta a complexidade dos RPGs de mesa (como D&D 5e) para um ambiente digital tático. Com foco em estratégia posicional, gerenciamento de recursos e uma IA desafiadora, cada batalha é um quebra-cabeça de sobrevivência e poder.

---

## 🚀 Funcionalidades Principais

### 🎲 Sistema de Combate inspirado em D&D 5e
O motor de regras foi construído para replicar a experiência de um RPG de mesa real:
- **Rolagens de Dados:** Tudo é decidido pelo destino (d20).
- **Atributos Dinâmicos:** Força, Destreza, Constituição, Inteligência, Sabedoria e Carisma impactam cada ação.
- **Progressão Realista:** Bônus de proficiência e modificadores de atributos calculados matematicamente.
- **Classe de Armadura (AC):** Sistema de acerto vs. defesa baseado em equipamentos.

### 🗺️ Tabuleiro Tático 2D
O campo de batalha não é apenas estético, ele é parte da estratégia:
- **Grid de 20x20:** Amplo espaço para manobras e flanqueamento.
- **Ecossistema de Terrenos:**
    - 🌲 **Floresta:** Oferece cobertura (+2 AC) contra ataques à distância.
    - 🪨 **Dificultoso:** Dobra o custo de movimento.
    - 🧊 **Gelo:** Risco de escorregar e perder o equilíbrio.
    - 🧱 **Paredes:** Bloqueiam linha de visão e movimento.
- **Sistema de Elevação:** Vantagens táticas para quem domina o terreno alto.

### 🧠 IA Estratégica e Avançada
Não espere inimigos que apenas "batem":
- **Decisões Inteligentes:** A IA avalia o HP dos alvos, proximidade de aliados e custo de terreno.
- **Gestão de Recursos:** Inimigos usam Mana, Energia e Fé de forma parcimoniosa.
- **Táticas de Combate:** Uso de **Flanqueamento** para ganhar bônus de ataque e execução de **Ataques de Oportunidade**.

---

## 🛡️ Classes e Heróis

| Classe | Recurso Principal | Habilidade de Destaque |
| :--- | :--- | :--- |
| **Guerreiro** | Cooldown | **Surto de Ação:** Um segundo ataque devastador no mesmo turno. |
| **Mago** | Mana | **Bola de Fogo:** Dano massivo em área (cuidado com o fogo amigo!). |
| **Ladino** | Energia | **Ataque Furtivo:** Dano extra crítico se o alvo estiver distraído. |
| **Arqueiro** | Flechas | **Tiro Duplo:** Precisão fatal à longa distância. |
| **Bárbaro** | Fúria | **Ataque Descuidado:** Troca defesa por um dano brutal. |
| **Clérigo** | Fé | **Canalizar Divindade:** Cura sagrada para manter o time vivo. |
| **Druida** | Natureza | **Forma de Urso:** Transformação para absorver dano. |
| **Bruxo** | Pacto | **Maldição de Agonia:** Debuffs que corroem o inimigo. |

### 👹 Desafios Lendários
Enfrente chefes únicos com mecânicas próprias:
- **Rei Goblin:** Convoca hordas de lacaios.
- **Lorde Lich:** Mestre da necromancia e controle de área.
- **Dragão Ancião:** O desafio supremo de poder.

---

## 🛠️ Instalação e Execução

### Pré-requisitos
- Python 3.8 ou superior.
- Pip instalado.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/AndersonAraujoX/RPG-battle.git
   cd RPG-battle
   ```

2. **Instale as dependências:**
   ```bash
   pip install pygame
   ```

3. **Inicie a batalha:**
   ```bash
   python main.py
   ```

---

## 🎮 Modos de Jogo

- **⚔️ Modo Campanha:** Uma jornada de progressão onde seus heróis ganham XP, sobem de nível e enfrentam batalhas cada vez mais complexas.
- **🛠️ Editor de Mapas:** Crie seus próprios cenários táticos, defina terrenos e posições iniciais para testar suas estratégias.

---

## 🧪 Tecnologias

- **Linguagem:** [Python](https://www.python.org/)
- **Engine Gráfica:** [Pygame](https://www.pygame.org/)
- **Persistência:** JSON para dados de personagens e mapas.

---

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
*Desenvolvido com ⚔️ e 🎲 por [Anderson Araújo](https://github.com/AndersonAraujoX)*