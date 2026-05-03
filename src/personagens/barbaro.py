import random
from .personagem_base import Personagem

class Barbaro(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.2
        
    @property
    def ac(self):
        if self.armadura_equipada:
            return self.armadura_equipada.bonus_ac
        return 10 + self.mod_des + self.mod_con
        self.cooldowns['ataque_descuidado'] = 0
        self.cooldown_max['ataque_descuidado'] = 3

        from ..itens.armas_comuns import MachadoGrande
        from ..itens.acessorios_comuns import AmuletoDeVitalidade
        self.equipar_arma(MachadoGrande())
        self.equipar_acessorio(AmuletoDeVitalidade())
        
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['furia'] = {
            "nome": "Entrar em Fúria",
            "descricao": "Aumenta dano e resistência, mas impede magias.",
            "custo": 0,
            "cooldown": 5,
            "tipo": "bonus",
            "alvo": "si_mesmo",
            "alcance": 0
        }
        self.habilidades['ataque_descuidado'] = {
            "nome": "Ataque Descuidado",
            "descricao": "Ataque com vantagem, mas inimigos têm vantagem contra você.",
            "custo": 0,
            "cooldown": 0, # Always avail? Or limited? Logic says cooldown in original code.
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 1
        }
        # Sync cooldowns from legacy if needed, or overwrite logic
        # Original code had 'ataque_descuidado' cooldown. Let's keep it.
        self.habilidades['ataque_descuidado']['cooldown'] = 3
        
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for

    def causar_dano(self, alvo, tabuleiro, logger=print, is_critico=False, **kwargs):
        if self.cooldowns.get('ataque_descuidado', 0) == 0:
            logger(f"  {self.nome} usa Ataque Descuidado para causar mais dano!")
            self.cooldowns['ataque_descuidado'] = self.cooldown_max.get('ataque_descuidado', 3)
            dano_extra = random.randint(1, 8)
            logger(f"  Dano extra do Ataque Descuidado: {dano_extra}")
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
            if alvo.esta_vivo:
                alvo.receber_dano(dano_extra, self, tabuleiro, logger)
        else:
            super().causar_dano(alvo, tabuleiro, logger, is_critico, **kwargs)
