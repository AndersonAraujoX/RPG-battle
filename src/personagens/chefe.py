import random
from src.config import COR_TEXTO, COR_DANO, COR_CRITICO
from .personagem_base import Personagem, calcular_distancia

class Chefe(Personagem):
    def __init__(self, nome, time, nivel=10, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player, stats=stats)
        self.threat_level = 5.0
        
        self.hp_atual = self.hp_max
        self.cooldowns['pisao_trovejante'] = 0
        self.cooldown_max['pisao_trovejante'] = 3

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        if self.cooldowns['pisao_trovejante'] == 0:
            logger((f"O {self.nome} usa PISÃO TROVEJANTE!", COR_CRITICO))
            self.cooldowns['pisao_trovejante'] = self.cooldown_max['pisao_trovejante']
            alvos_afetados = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= 2]
            dano = sum(random.randint(1, 8) for _ in range(3))
            logger((f"  A onda de choque causa {dano} de dano em área!", COR_DANO))
            
            self.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': self, 'x': self.pos_x, 'y': self.pos_y, 'raio': 2})
            if self.sound_player: self.sound_player('attack')

            for vitima in alvos_afetados:
                vitima.receber_dano(dano, self, tabuleiro, logger)
                self.eventos_animacao.append({'tipo': 'dano', 'alvo': vitima, 'dano': dano})
            return

        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
        if self.esta_vivo:
            alvos_adjacentes = [p for p in time_inimigo if p.esta_vivo and p is not alvo and calcular_distancia(self, p) <= self.alcance]
            if alvos_adjacentes:
                alvo_extra = random.choice(alvos_adjacentes)
                logger((f"  {self.nome} aproveita o embalo e ataca {alvo_extra.nome} também!", COR_TEXTO))
                super().atacar(alvo_extra, time_inimigo, time_aliado, tabuleiro, logger)
