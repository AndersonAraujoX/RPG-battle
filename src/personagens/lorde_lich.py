import random
from .personagem_base import Personagem

class LordeLich(Personagem):
    def __init__(self, nome, time, nivel=12, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 5.0
        
        self.cooldowns['toque_drenante'] = 0
        self.cooldown_max['toque_drenante'] = 3
        self.imunidades = ["Envenenado", "Sangrando"]

    @property
    def bonus_ataque(self): return self.mod_int + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_int

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        if self.cooldowns['toque_drenante'] == 0 and self.hp_atual < self.hp_max:
            logger(f"O {self.nome} usa TOQUE DRENANTE em {alvo.nome}!")
            self.cooldowns['toque_drenante'] = self.cooldown_max['toque_drenante']
            
            dano = sum(random.randint(1, 6) for _ in range(4)) + self.bonus_dano
            logger(f"  {alvo.nome} sofre {dano} de dano necrótico.")
            alvo.receber_dano(dano, self, tabuleiro, logger)
            
            cura = dano // 2
            self.hp_atual = min(self.hp_max, self.hp_atual + cura)
            logger(f"  {self.nome} drena {cura} de vida!")
            
            self.eventos_animacao.append({'tipo': 'ataque', 'atacante': self, 'alvo': alvo})
            if self.sound_player: self.sound_player('heal') # Using heal sound for drain
            return

        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
