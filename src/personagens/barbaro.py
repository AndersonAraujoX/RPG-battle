import random
from .personagem_base import Personagem

class Barbaro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.forca, self.constituicao = 16, 16
        self.dado_vida = (1, 12)
        self.hp_max = 12 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 10 + self.mod_des + self.mod_con
        self.dado_dano = (1, 12)
        self.velocidade, self.alcance = 4, 1
        self.cooldowns['ataque_descuidado'] = 0
        self.cooldown_max['ataque_descuidado'] = 3

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for
    @property
    def threat_level(self): return 3

    def causar_dano(self, alvo, logger=print, is_critico=False):
        if self.cooldowns['ataque_descuidado'] == 0:
            logger(f"  {self.nome} usa Ataque Descuidado para causar mais dano!")
            self.cooldowns['ataque_descuidado'] = self.cooldown_max['ataque_descuidado']
            dano_extra = random.randint(1, 8)
            logger(f"  Dano extra do Ataque Descuidado: {dano_extra}")
            super().causar_dano(alvo, logger, is_critico)
            if alvo.esta_vivo:
                alvo.receber_dano(dano_extra, self, logger)
        else:
            super().causar_dano(alvo, logger, is_critico)
