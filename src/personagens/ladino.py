import random
from .personagem_base import Personagem

class Ladino(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.destreza, self.constituicao = 16, 12
        self.dado_vida = (1, 8)
        self.hp_max = 8 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 12 + self.mod_des
        self.dado_dano = (1, 6)
        self.velocidade, self.alcance = 4, 1
        self.cooldowns['ataque_furtivo'] = 0
        self.cooldown_max['ataque_furtivo'] = 2

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des
    @property
    def threat_level(self): return 3

    def causar_dano(self, alvo, logger=print, is_critico=False):
        if self.cooldowns['ataque_furtivo'] == 0:
            logger(f"  {self.nome} consegue um Ataque Furtivo!")
            self.cooldowns['ataque_furtivo'] = self.cooldown_max['ataque_furtivo']
            dado_original = self.dado_dano
            self.dado_dano = (self.dado_dano[0] + 1, self.dado_dano[1])
            super().causar_dano(alvo, logger, is_critico)
            self.dado_dano = dado_original
        else:
            super().causar_dano(alvo, logger, is_critico)
