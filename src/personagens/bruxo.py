import random
from .personagem_base import Personagem
from ..utils import calcular_distancia

class Bruxo(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.threat_level = 1.5
        
        # Mana system
        self.mana_max = 15 + (nivel * 2)
        self.mana_atual = self.mana_max
        self.custo_habilidades = {} # Handled below
        
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['rajada_mistica'] = {
            "nome": "Rajada Mística",
            "descricao": "Disparo de energia pura.",
            "custo": 0, # Cantrip
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 12,
            "dano": "1d10",
            "tipo_dano": "Energia"
        }
        self.habilidades['maldicao_de_agonia'] = {
            "nome": "Maldição de Agonia",
            "descricao": "Causa dano periódico e reduz atributos.",
            "custo": 6, # Mana
            "tipo": "acao", # Or bonus?
            "alvo": "inimigo",
            "alcance": 8,
            "efeito": "maldicao"
        }
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})

    @property
    def bonus_ataque(self): return self.mod_car + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_car

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # 1. Tentar amaldiçoar um inimigo sem o debuff
        if 'maldicao_de_agonia' in self.custo_habilidades and self.mana_atual >= self.custo_habilidades['maldicao_de_agonia']:
            alvos_sem_maldicao = [
                p for p in inimigos 
                if calcular_distancia(self, p) <= self.alcance and 
                "Amaldiçoado" not in [e.nome for e in p.status_efeitos]
            ]
            if alvos_sem_maldicao:
                alvo = max(alvos_sem_maldicao, key=lambda p: p.hp_max) # Target the tankiest
                logs_turno.append(f"  {self.nome} lança Maldição de Agonia em {alvo.nome}!")
                return {'acao': 'usar_habilidade', 'habilidade': 'maldicao_de_agonia', 'alvo': alvo}

        # 2. Lógica padrão da classe base
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)
