import random
from .personagem_base import Personagem, calcular_distancia

class Guerreiro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.2
        
        self.cooldowns['surto_acao'] = 0
        self.cooldown_max['surto_acao'] = 4

        from ..itens.armas_comuns import EspadaLonga
        from ..itens.armaduras_comuns import CotaDeMalha
        from ..itens.acessorios_comuns import AnelDeForca
        self.equipar_arma(EspadaLonga())
        self.equipar_armadura(CotaDeMalha())
        self.equipar_acessorio(AnelDeForca())
        
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['surto_acao'] = {
            "nome": "Surto de Ação",
            "descricao": "Ganha uma ação extra neste turno.",
            "custo": 0,
            "cooldown": 4,
            "tipo": "livre", # Special
            "alvo": "si_mesmo",
            "alcance": 0
        }
        self.habilidades['ataque_giratorio'] = {
            "nome": "Ataque Giratório",
            "descricao": "Ataca todos inimigos adjacentes.",
            "custo": 0,
            "cooldown": 3,
            "tipo": "acao",
            "alvo": "area_pessoal", # Radius 1 self
            "alcance": 1,
            "dano": "arma",
            "efeito": "ataque_area"
        }
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print, **kwargs):
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger, **kwargs)
        if self.esta_vivo and self.cooldowns['surto_acao'] == 0:
            logger(f"  {self.nome} usa Surto de Ação para um ataque extra!")
            self.cooldowns['surto_acao'] = self.cooldown_max['surto_acao']
            alvos_vivos = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= self.alcance]
            if alvos_vivos:
                alvo_extra = min(alvos_vivos, key=lambda p: p.hp_atual)
                super().atacar(alvo_extra, time_inimigo, time_aliado, tabuleiro, logger, **kwargs)
            else:
                logger("  Mas não há ninguém ao alcance para o segundo ataque.")
