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
