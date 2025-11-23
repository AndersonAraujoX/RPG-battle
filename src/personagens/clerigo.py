import random
from .personagem_base import Personagem, calcular_distancia

class Clerigo(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.sabedoria, self.constituicao, self.forca = 16, 14, 14
        self.dado_vida = (1, 8)
        self.hp_max = 8 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 18
        self.dado_dano = (1, 6)
        self.velocidade, self.alcance = 3, 1
        self.alcance_cura = 5
        self.cooldowns['canalizar_divindade'] = 0
        self.cooldown_max['canalizar_divindade'] = 4

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for
    @property
    def threat_level(self): return 4

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        # A lógica de cura foi movida para o MotorCombate para uma IA mais inteligente.
        # O Clérigo agora decide curar ANTES de se mover.
        # Se ele chega aqui, é porque decidiu atacar.
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
