import random
from .personagem_base import Personagem

class Ladino(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        
        # Energy system
        self.energia_max = 10 + nivel
        self.energia_atual = self.energia_max
        self.custo_habilidades = {'ataque_furtivo': 5}

        from ..itens.armas_comuns import Adaga
        from ..itens.armaduras_comuns import CouracaDeCouro
        from ..itens.acessorios_comuns import BotasDaVelocidade
        self.equipar_arma(Adaga())
        self.equipar_armadura(CouracaDeCouro())
        self.equipar_acessorio(BotasDaVelocidade())

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des
    @property
    def threat_level(self): return 3

    def causar_dano(self, alvo, logger=print, is_critico=False):
        if 'ataque_furtivo' in self.custo_habilidades and self.energia_atual >= self.custo_habilidades['ataque_furtivo']:
            logger(f"  {self.nome} consegue um Ataque Furtivo!")
            self.energia_atual -= self.custo_habilidades['ataque_furtivo']
            dado_original = self.dado_dano
            self.dado_dano = (self.dado_dano[0] + 1, self.dado_dano[1])
            super().causar_dano(alvo, logger, is_critico)
            self.dado_dano = dado_original
        else:
            super().causar_dano(alvo, logger, is_critico)
