import random
from .personagem_base import Personagem

class Ladino(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.3
        
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
        
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['golpe_sombrio'] = {
            "nome": "Golpe Sombrio",
            "descricao": "Ataque com dano extra se tiver energia.",
            "custo": 5, # Energia
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 1,
            "dano": "arma+2d6",
            "tipo_dano": "Fisico"
        }
        self.habilidades['esconder'] = {
            "nome": "Esconder-se",
            "descricao": "Fica invisível até atacar ou ser descoberto.",
            "custo": 5,
            "tipo": "bonus",
            "alvo": "si_mesmo",
            "alcance": 0
        }
        
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des

    def causar_dano(self, alvo, tabuleiro, logger=print, is_critico=False, **kwargs):
        from src.config import COR_STATUS
        custo = self.custo_habilidades.get('golpe_sombrio', self.custo_habilidades.get('ataque_furtivo', 5))
        if self.energia_atual >= custo:
            logger((f"  {self.nome} consegue um Ataque Furtivo! (+2d6 dano furtivo)", COR_STATUS))
            self.energia_atual -= custo
            dano_furtivo = random.randint(1, 6) + random.randint(1, 6)
            kwargs['bonus_dano_extra'] = kwargs.get('bonus_dano_extra', 0) + dano_furtivo
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
        else:
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
