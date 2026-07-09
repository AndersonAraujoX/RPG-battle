import random
from .personagem_base import Personagem
from src.itens.materiais import CouroGoblin, Osso, EscamaKobold

class Goblin(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.loot_table = [(CouroGoblin, 0.4)]
        self.threat_level = 0.5

class Esqueleto(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.loot_table = [(Osso, 0.5)]
        self.imunidades = ["Envenenado"]
        self.threat_level = 0.8

class Kobold(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.loot_table = [(EscamaKobold, 0.3)]
        self.threat_level = 0.6

class Troll(Personagem):
    def __init__(self, nome, time, nivel=3, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Troll"
        self.loot_table = []
        self.threat_level = 1.8
        self.hp_max = 30
        self.hp_atual = 30
        # Círculos de vida do Troll
        self.circulos_total = 3
        self.circulos_marcados = 0
        self.dano_turno_atual = 0
