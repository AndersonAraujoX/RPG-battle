import random
from .personagem_base import Personagem, calcular_distancia

class DragaoAnciao(Personagem):
    def __init__(self, nome, time, nivel=15, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player, stats=stats)
        self.threat_level = 6.0
        
        self.cooldowns['sopro_de_fogo'] = 0
        self.cooldown_max['sopro_de_fogo'] = 4
        self.imunidades = ["Atordoado"]

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        if self.cooldowns['sopro_de_fogo'] == 0:
            logger(f"O {self.nome} usa SOPRO DE FOGO!")
            self.cooldowns['sopro_de_fogo'] = self.cooldown_max['sopro_de_fogo']
            
            # Affect all enemies within breath range (6)
            alvos_afetados = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= 6]

            dano = sum(random.randint(1, 6) for _ in range(8))
            logger(f"  O fogo consome uma área, causando {dano} de dano!")
            
            self.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': self, 'x': self.pos_x, 'y': self.pos_y, 'raio': 4})
            if self.sound_player: self.sound_player('attack')

            for vitima in alvos_afetados:
                vitima.receber_dano(dano, self, tabuleiro, logger)
                self.eventos_animacao.append({'tipo': 'dano', 'alvo': vitima, 'dano': dano})
            return

        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
