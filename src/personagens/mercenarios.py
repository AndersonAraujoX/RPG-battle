"""
mercenarios.py — Classes de Mercenários recrutáveis com Cristais Roxos.

Três variações:
1. MercenarioMelee (Corpo a Corpo): Ataca insetos em alcance 1 (2d6+3 Dano). Custo: 5 Cristais.
2. MercenarioArqueiro (Distância): Atira em insetos em alcance 5 (1d10+4 Dano). Custo: 7 Cristais.
3. MercenarioMinerador (Escavador): Minera rochas e extrai +2 Cristais Roxos a cada rodada. Custo: 4 Cristais.
"""
from .personagem_base import Personagem
from .guerreiro import Guerreiro
from .arqueiro import Arqueiro

class MercenarioMelee(Guerreiro):
    """Guarda Mercenário (Corpo a Corpo): Custo 5 Cristais Roxos."""
    def __init__(self, nome="Guarda Mercenário", time="A", nivel=3):
        super().__init__(nome, time, nivel)
        self.hp_max = 45
        self.hp_atual = 45
        self.ac_base = 15
        self.bonus_ataque = 4
        self.dado_dano = (2, 6)
        self.bonus_dano = 3
        self.alcance = 1
        self.tipo_mercenario = "melee"
        self._is_mercenario = True

class MercenarioArqueiro(Arqueiro):
    """Arqueiro Mercenário (Distância): Custo 7 Cristais Roxos."""
    def __init__(self, nome="Arqueiro Mercenário", time="A", nivel=3):
        super().__init__(nome, time, nivel)
        self.hp_max = 30
        self.hp_atual = 30
        self.ac_base = 13
        self.bonus_ataque = 5
        self.dado_dano = (1, 10)
        self.bonus_dano = 4
        self.alcance = 5
        self.tipo_mercenario = "arqueiro"
        self._is_mercenario = True

class MercenarioMinerador(Personagem):
    """Minerador Mercenário (Escavador): Custo 4 Cristais Roxos. Extrai +2 Cristais Roxos por rodada."""
    def __init__(self, nome="Minerador Mercenário", time="A", nivel=3):
        super().__init__(nome, time, nivel)
        self.hp_max = 35
        self.hp_atual = 35
        self.ac_base = 12
        self.bonus_ataque = 2
        self.dado_dano = (1, 6)
        self.bonus_dano = 1
        self.alcance = 1
        self.tipo_mercenario = "minerador"
        self._is_mercenario = True
