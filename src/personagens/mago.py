import random
from .personagem_base import Personagem
from ..utils import calcular_distancia
from ..config import TERRENO_PAREDE

class Mago(Personagem):
    def __init__(self, nome, time, nivel=1, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.inteligencia, self.constituicao, self.destreza = 16, 12, 14
        self.dado_vida = (1, 6)
        self.hp_max = 6 + self.mod_con + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        self.hp_atual = self.hp_max
        self.ac = 10 + self.mod_des
        self.dado_dano = (1, 6)
        self.velocidade, self.alcance = 3, 6
        self.cooldowns['bola_de_fogo'] = 0
        self.cooldown_max['bola_de_fogo'] = 4

    @property
    def bonus_ataque(self): return self.mod_int + self.bonus_proficiencia
    @property
    def threat_level(self): return 4

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        # 1. Tentar usar Bola de Fogo
        if self.cooldowns['bola_de_fogo'] == 0 and inimigos:
            melhor_oportunidade = {'alvos_atingidos': 0, 'aliados_atingidos': 999, 'pos_final': None, 'alvo_central': None}
            pos_inicial = (self.pos_x, self.pos_y)

            # Avalia todas as posições alcançáveis para conjurar Bola de Fogo
            for r in range(self.velocidade + 1):
                for dx in range(-r, r + 1):
                    dy = r - abs(dx)
                    for sign_x, sign_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                        if dx == 0 and dy == 0 and (sign_x != 1 or sign_y != 1): continue
                        nova_pos_x, nova_pos_y = pos_inicial[0] + dx*sign_x, pos_inicial[1] + dy*sign_y
                        
                        if not (0 <= nova_pos_x < tabuleiro.largura and 0 <= nova_pos_y < tabuleiro.altura): continue
                        if tabuleiro.get_personagem_em(nova_pos_x, nova_pos_y) is not None and (nova_pos_x, nova_pos_y) != pos_inicial: continue
                        if tabuleiro.get_terrain_em(nova_pos_x, nova_pos_y) == TERRENO_PAREDE: continue

                        mago_simulado_pos = type('obj', (object,), {'pos_x': nova_pos_x, 'pos_y': nova_pos_y})
                        for inimigo in inimigos:
                            if calcular_distancia(mago_simulado_pos, inimigo) <= self.alcance:
                                alvos_na_area = tabuleiro.get_personagens_em_area(inimigo.pos_x, inimigo.pos_y, 1)
                                num_inimigos_na_area = sum(1 for p in alvos_na_area if p.time != self.time and p.esta_vivo)
                                num_aliados_na_area = sum(1 for p in alvos_na_area if p.time == self.time and p.esta_vivo)

                                # Prioriza maximizar inimigos e minimizar aliados
                                if (num_inimigos_na_area > melhor_oportunidade['alvos_atingidos'] and num_aliados_na_area == 0) or \
                                   (num_inimigos_na_area == melhor_oportunidade['alvos_atingidos'] and num_aliados_na_area < melhor_oportunidade['aliados_atingidos']):
                                    melhor_oportunidade = {
                                        'alvos_atingidos': num_inimigos_na_area, 
                                        'aliados_atingidos': num_aliados_na_area,
                                        'pos_final': (nova_pos_x, nova_pos_y), 
                                        'alvo_central': inimigo
                                    }
            
            # Só conjura se atingir pelo menos 2 inimigos e 0 aliados
            if melhor_oportunidade['alvos_atingidos'] >= 2 and melhor_oportunidade['aliados_atingidos'] == 0:
                logs_turno.append(f"  {self.nome} vê uma oportunidade para a Bola de Fogo sem atingir aliados!")
                pos_final = melhor_oportunidade['pos_final']
                alvo_central = melhor_oportunidade['alvo_central']
                return {'acao': 'usar_habilidade', 'habilidade': 'bola_de_fogo', 
                        'pos_conjuracao': pos_final, 'alvo_central': alvo_central}

        # 2. Lógica padrão da classe base (fugir ou atacar)
        return super().decidir_acao(inimigos, aliados, tabuleiro, logs_turno)

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        # A lógica da Bola de Fogo foi movida para o MotorCombate para uma IA mais inteligente.
        # Se o Mago chega aqui, é porque decidiu fazer um ataque normal.
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
