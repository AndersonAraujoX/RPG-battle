import random
from .personagem_base import Personagem, calcular_distancia

class Clerigo(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.4
        
        self.alcance_cura = 5
        
        # Faith system
        self.fe_max = 10 + nivel
        self.fe_atual = self.fe_max
        self.custo_habilidades = {'canalizar_divindade': 4}
        self.threat_level = 4

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # 1. Tentar curar aliado ferido
        if 'canalizar_divindade' in self.custo_habilidades and self.fe_atual >= self.custo_habilidades['canalizar_divindade']:
            aliados_feridos = [p for p in aliados if p.esta_vivo and p.hp_atual < p.hp_max * 0.7 and calcular_distancia(self, p) <= self.alcance_cura]
            if aliados_feridos:
                alvo_cura = min(aliados_feridos, key=lambda p: p.hp_atual / p.hp_max)
                logs_turno.append(f"  {self.nome} prioriza a cura e usa Canalizar Divindade em {alvo_cura.nome}!")
                return {'acao': 'usar_habilidade', 'habilidade': 'canalizar_divindade', 'alvo': alvo_cura}

        # 2. Lógica padrão da classe base (fugir ou atacar)
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        # A lógica de cura foi movida para o MotorCombate para uma IA mais inteligente.
        # O Clérigo agora decide curar ANTES de se mover.
        # Se ele chega aqui, é porque decidiu atacar.
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
