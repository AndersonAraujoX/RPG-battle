import random
from .personagem_base import Personagem, calcular_distancia

class Guerreiro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.forca, self.constituicao, self.destreza = 16, 14, 12
        self.dado_vida = (1, 10)
        self.hp_max = 10 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 18
        self.dado_dano = (1, 8)
        self.velocidade, self.alcance = 3, 1
        self.cooldowns['surto_acao'] = 0
        self.cooldown_max['surto_acao'] = 4

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for
    @property
    def threat_level(self): return 2

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
        if self.esta_vivo and self.cooldowns['surto_acao'] == 0:
            logger(f"  {self.nome} usa Surto de Ação para um ataque extra!")
            self.cooldowns['surto_acao'] = self.cooldown_max['surto_acao']
            alvos_vivos = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= self.alcance]
            if alvos_vivos:
                alvo_extra = min(alvos_vivos, key=lambda p: p.hp_atual)
                super().atacar(alvo_extra, time_inimigo, time_aliado, tabuleiro, logger)
            else:
                logger("  Mas não há ninguém ao alcance para o segundo ataque.")
