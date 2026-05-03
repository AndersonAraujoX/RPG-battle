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
        self.em_forma_de_urso = False
        
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['forma_de_urso'] = {
            "nome": "Forma de Urso",
            "descricao": "Transforma-se em Urso (Vida e Dano aumentados).",
            "custo": 1, # Furia
            "tipo": "bonus",
            "alvo": "si_mesmo",
            "alcance": 0
        }
        self.habilidades['vinhas'] = {
            "nome": "Vinhas Esmagadoras",
            "descricao": "Causa dano e pode prender o alvo.",
            "custo": 1,
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 6,
            "dano": "1d6",
            "tipo_dano": "Fisico" #"Magico"?
        }
        
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        
        self.em_forma_de_urso = False
        self.stats_originais = {}

    def usar_forma_de_urso(self, logger):
        if not self.em_forma_de_urso:
            if self.furia_atual >= self.custo_habilidades['forma_de_urso']:
                logger(f"  {self.nome} se transforma em um urso!")
                self.furia_atual -= self.custo_habilidades['forma_de_urso']
                
                # Store original stats
                self.stats_originais = {
                    'forca': self._forca,
                    'constituicao': self._constituicao,
                    'ac': self.ac_base,
                }
                
                # Apply bear form stats
                self._forca += 4
                self._constituicao += 4
                self.ac_base += 2
                self.em_forma_de_urso = True
            else:
                logger(f"  {self.nome} não tem fúria suficiente para se transformar!")
        else:
            logger(f"  {self.nome} volta à sua forma normal.")
            # Revert to original stats
            self._forca = self.stats_originais['forca']
            self._constituicao = self.stats_originais['constituicao']
            self.ac_base = self.stats_originais['ac']
            self.em_forma_de_urso = False
            
    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # Simple AI: transform if there are enemies nearby and not already transformed
        if not self.em_forma_de_urso and 'forma_de_urso' in self.custo_habilidades and self.furia_atual >= self.custo_habilidades['forma_de_urso']:
            inimigos_proximos = [e for e in inimigos if calcular_distancia(self, e) <= 3]
            if inimigos_proximos:
                return {'acao': 'usar_habilidade', 'habilidade': 'forma_de_urso'}
        
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)
