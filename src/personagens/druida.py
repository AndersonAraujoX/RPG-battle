import random
from .personagem_base import Personagem
from ..utils import calcular_distancia

class Druida(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        
        self.ac_base = 11 + self.mod_des

        # Nature's Fury resource system
        self.furia_max = 2 + nivel // 2
        self.furia_atual = self.furia_max
        self.custo_habilidades = {'forma_de_urso': 1}
        
        self.em_forma_de_urso = False
        self.stats_originais = {}

    def usar_forma_de_urso(self, logger):
        if not self.em_forma_de_urso:
            if self.furia_atual >= self.custo_habilidades['forma_de_urso']:
                logger(f"  {self.nome} se transforma em um urso!")
                self.furia_atual -= self.custo_habilidades['forma_de_urso']
                
                # Store original stats
                self.stats_originais = {
                    'forca': self.forca,
                    'constituicao': self.constituicao,
                    'ac': self.ac,
                }
                
                # Apply bear form stats
                self.forca += 4
                self.constituicao += 4
                self.ac += 2
                self.em_forma_de_urso = True
            else:
                logger(f"  {self.nome} não tem fúria suficiente para se transformar!")
        else:
            logger(f"  {self.nome} volta à sua forma normal.")
            # Revert to original stats
            self.forca = self.stats_originais['forca']
            self.constituicao = self.stats_originais['constituicao']
            self.ac = self.stats_originais['ac']
            self.em_forma_de_urso = False
            
    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # Simple AI: transform if there are enemies nearby and not already transformed
        if not self.em_forma_de_urso and 'forma_de_urso' in self.custo_habilidades and self.furia_atual >= self.custo_habilidades['forma_de_urso']:
            inimigos_proximos = [e for e in inimigos if self.calcular_distancia(self, e) <= 3]
            if inimigos_proximos:
                return {'acao': 'usar_habilidade', 'habilidade': 'forma_de_urso'}
        
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)
