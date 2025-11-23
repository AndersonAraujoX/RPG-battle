import random
from .personagem_base import Personagem, calcular_distancia

class Arqueiro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.destreza, self.constituicao = 16, 12
        self.dado_vida = (1, 10)
        self.hp_max = 10 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 15
        self.dado_dano = (1, 8)
        self.velocidade, self.alcance = 4, 10
        self.cooldowns['tiro_duplo'] = 0
        self.cooldown_max['tiro_duplo'] = 3

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des
    @property
    def threat_level(self): return 2

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
        if self.esta_vivo and self.cooldowns['tiro_duplo'] == 0:
            logger(f"  {self.nome} usa Tiro Duplo para um ataque extra!")
            self.cooldowns['tiro_duplo'] = self.cooldown_max['tiro_duplo']
            alvos_vivos = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= self.alcance]
            if alvos_vivos:
                alvo_extra = min(alvos_vivos, key=lambda p: p.hp_atual)
                super().atacar(alvo_extra, time_inimigo, time_aliado, tabuleiro, logger)
            else:
                logger("  Mas não há ninguém ao alcance para o segundo tiro.")
