import random
from .minions import Goblin
from .personagem_base import Personagem, calcular_distancia
from .status_efeito import StatusEfeito

from .minions import Goblin

class ReiGoblin(Personagem):
    def __init__(self, nome, time, nivel=10, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player, stats=stats)
        self.threat_level = 3.0
        
        # Fury system
        self.furia_max = 4
        self.furia_atual = 0
        self.custo_habilidades = {'convocar_goblin': 2}
        
        self.imunidades = ["Atordoado"]

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        if 'convocar_goblin' in self.custo_habilidades and self.furia_atual >= self.custo_habilidades['convocar_goblin']:
            self.furia_atual -= self.custo_habilidades['convocar_goblin']
            logs_turno.append(f"  {self.nome} convoca um Goblin para a batalha!")
            return {'acao': 'usar_habilidade', 'habilidade': 'convocar_goblin'}

        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)
