import random
from .personagem_base import Personagem

class Mago(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.inteligencia, self.constituicao, self.destreza = 16, 12, 14
        self.dado_vida = (1, 6)
        self.hp_max = 6 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 10 + self.mod_des
        self.dado_dano = (1, 6)
        self.velocidade, self.alcance = 3, 6
        self.cooldowns['bola_de_fogo'] = 0
        self.cooldown_max['bola_de_fogo'] = 4

    @property
    def bonus_ataque(self): return self.mod_int + self.bonus_proficiencia
    @property
    def threat_level(self): return 4

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        # A lógica da Bola de Fogo foi movida para o MotorCombate para uma IA mais inteligente.
        # Se o Mago chega aqui, é porque decidiu fazer um ataque normal.
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
