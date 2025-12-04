import random
from .personagem_base import Personagem, calcular_distancia

class Arqueiro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.3
        
        self.cooldowns['tiro_duplo'] = 0
        self.cooldown_max['tiro_duplo'] = 3

        from ..itens.armas_comuns import ArcoCurto
        self.equipar_arma(ArcoCurto())

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des

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
