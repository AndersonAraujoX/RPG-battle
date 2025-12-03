import random
from .personagem_base import Personagem, calcular_distancia

class Paladino(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        
        self.usos_lay_on_hands = self.mod_car + 1
        self.cooldowns['smite_evil'] = 0
        self.cooldown_max['smite_evil'] = 3

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for
    @property
    def threat_level(self): return 5

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # 1. Usar Lay on Hands para se curar se com pouca vida
        if self.usos_lay_on_hands > 0 and self.hp_atual < self.hp_max * 0.5:
            cura = self.nivel * 5
            logs_turno.append(f"  {self.nome} usa Lay on Hands em si mesmo!")
            self.receber_cura(cura, logs_turno.append)
            self.usos_lay_on_hands -= 1
            return {'acao': 'usar_habilidade', 'habilidade': 'lay_on_hands', 'alvo': self}
            
        # 2. Usar Smite Evil em um inimigo
        if self.cooldowns['smite_evil'] == 0 and inimigos:
            inimigos_em_range = [p for p in inimigos if calcular_distancia(self, p) <= self.alcance]
            if inimigos_em_range:
                alvo = max(inimigos_em_range, key=lambda p: p.threat_level)
                logs_turno.append(f"  {self.nome} usa Smite Evil em {alvo.nome}!")
                self.cooldowns['smite_evil'] = self.cooldown_max['smite_evil']
                # O dano extra será adicionado no ataque
                return {'acao': 'atacar', 'alvo': alvo, 'habilidade': 'smite_evil'}

        # 3. Lógica padrão da classe base
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print, habilidade=None):
        if habilidade == 'smite_evil':
            dano_extra = sum(random.randint(1, 8) for _ in range(self.nivel // 2 + 1))
            logger(f"  {self.nome} adiciona {dano_extra} de dano radiante com Smite Evil!")
            super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
            alvo.receber_dano(dano_extra, self, logger)
        else:
            super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)

