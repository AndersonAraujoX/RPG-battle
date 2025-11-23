import random
from .personagem_base import Personagem, calcular_distancia

class Chefe(Personagem):
    def __init__(self, nome, time, nivel=10, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player)
        self.forca, self.constituicao = 20, 20
        self.dado_vida = (1, 12)
        
        if stats:
            self.hp_max = stats.get('hp', 300)
            self.ac = stats.get('ac', 20)
            num_dados_dano = stats.get('dado_dano', 2)
            self.dado_dano = (num_dados_dano, 8)
        else:
            self.hp_max = 300
            self.ac = 20
            self.dado_dano = (2, 8)

        self.hp_atual = self.hp_max
        self.velocidade, self.alcance = 4, 1
        self.cooldowns['pisao_trovejante'] = 0
        self.cooldown_max['pisao_trovejante'] = 3

    @property
    def bonus_ataque(self): return self.mod_for + self.bonus_proficiencia
    @property
    def bonus_dano(self): return self.mod_for
    @property
    def threat_level(self): return 10

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        if self.cooldowns['pisao_trovejante'] == 0:
            logger(f"O {self.nome} usa PISÃO TROVEJANTE!")
            self.cooldowns['pisao_trovejante'] = self.cooldown_max['pisao_trovejante']
            alvos_afetados = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(self, p) <= 2]
            dano = sum(random.randint(1, 8) for _ in range(3))
            logger(f"  A onda de choque causa {dano} de dano em área!")
            
            self.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': self, 'x': self.pos_x, 'y': self.pos_y, 'raio': 2})
            if self.sound_player: self.sound_player('attack')

            for vitima in alvos_afetados:
                vitima.receber_dano(dano, self, logger)
                self.eventos_animacao.append({'tipo': 'dano', 'alvo': vitima, 'dano': dano})
            return

        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
        if self.esta_vivo:
            alvos_adjacentes = [p for p in time_inimigo if p.esta_vivo and p is not alvo and calcular_distancia(self, p) <= self.alcance]
            if alvos_adjacentes:
                alvo_extra = random.choice(alvos_adjacentes)
                logger(f"  {self.nome} aproveita o embalo e ataca {alvo_extra.nome} também!")
                super().atacar(alvo_extra, time_inimigo, time_aliado, tabuleiro, logger)
