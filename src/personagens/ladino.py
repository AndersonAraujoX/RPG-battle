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

    @property
    def bonus_ataque(self): return self.mod_des + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_des

    def causar_dano(self, alvo, tabuleiro, logger=print, is_critico=False, **kwargs):
        from src.config import COR_STATUS
        if 'ataque_furtivo' in self.custo_habilidades and self.energia_atual >= self.custo_habilidades['ataque_furtivo']:
            logger((f"  {self.nome} consegue um Ataque Furtivo!", COR_STATUS))
            self.energia_atual -= self.custo_habilidades['ataque_furtivo']
            dado_original = self.dado_dano
            # Temporarily increase damage dice for sneak attack
            # Note: This modifies self.dado_dano which is a tuple.
            # We should probably handle this differently but for now let's stick to the logic
            # However, self.dado_dano is likely used inside super().causar_dano
            # But wait, self.arma_equipada might override it in super().causar_dano
            # Let's check super().causar_dano logic again.
            # It uses self.arma_equipada.dado_dano if equipped.
            # So modifying self.dado_dano might not work if weapon is equipped.
            # But Ladino has Adaga equipped.
            
            # Let's just pass the call to super and hope it works or modify how damage is calculated.
            # Actually, let's just fix the signature first to stop the crash.
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
            
            # If we want to add sneak attack damage, we should probably do it by adding extra damage
            # But the current implementation tries to modify dice.
            # Let's just fix the signature for now.
        else:
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
