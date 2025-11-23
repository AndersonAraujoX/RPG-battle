import random
import math

# Importar a função calcular_distancia que será movida para um módulo de utilidades
# from ..utils import calcular_distancia 
# Por enquanto, vamos redefinir aqui para evitar erros de importação circular
def calcular_distancia(p1, p2):
    return abs(p1.pos_x - p2.pos_x) + abs(p1.pos_y - p2.pos_y)

class Personagem:
    def __init__(self, nome, time, nivel=1, sound_player=None):
        self.nome = nome
        self.time = time
        self.nivel = nivel
        self.xp = 0
        self.xp_para_upar = 2 ** self.nivel
        self.kills = 0
        
        self.forca, self.destreza, self.constituicao, self.inteligencia, self.sabedoria, self.carisma = 10, 10, 10, 10, 10, 10
        self.hp_max, self.hp_atual, self.ac = 0, 0, 0
        self.dado_dano = (1, 1)
        self.dado_vida = (1, 6)
        self.iniciativa = 0
        self.esta_vivo = True
        self.pos_x, self.pos_y = -1, -1
        self.velocidade, self.alcance = 0, 0
        self.cooldowns = {}
        self.cooldown_max = {}
        self.sound_player = sound_player
        self.eventos_animacao = []

    def tick_cooldowns(self):
        for key in self.cooldowns:
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1

    def ganhar_xp(self, quantidade, logger=print):
        if not self.esta_vivo: return
        self.xp += quantidade
        logger(f"  {self.nome} ganha {quantidade} XP!")
        if self.xp >= self.xp_para_upar:
            self.subir_de_nivel(logger)

    def subir_de_nivel(self, logger=print):
        self.nivel += 1
        self.xp = 0 
        self.xp_para_upar = 2 ** self.nivel
        
        aumento_hp = random.randint(1, self.dado_vida[1]) + self.mod_con
        if aumento_hp < 1: aumento_hp = 1
        
        self.hp_max += aumento_hp
        self.hp_atual += aumento_hp
        
        logger(f"  *** {self.nome} SUBIU PARA O NÍVEL {self.nivel}! ***")
        logger(f"  (HP máximo aumentado em {aumento_hp})")
        if self.sound_player: self.sound_player('level_up')
        self.eventos_animacao.append({'tipo': 'level_up', 'personagem': self})

    @property
    def mod_for(self): return (self.forca - 10) // 2
    @property
    def mod_des(self): return (self.destreza - 10) // 2
    @property
    def mod_con(self): return (self.constituicao - 10) // 2
    @property
    def mod_int(self): return (self.inteligencia - 10) // 2
    @property
    def mod_sab(self): return (self.sabedoria - 10) // 2
    
    @property
    def bonus_proficiencia(self): return 1 + math.ceil(self.nivel / 4)

    @property
    def bonus_ataque(self): return self.bonus_proficiencia
    @property
    def bonus_dano(self): return 0

    @property
    def threat_level(self): return 1

    def rolar_iniciativa(self):
        self.iniciativa = random.randint(1, 20) + self.mod_des
        return self.iniciativa

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        if not self.esta_vivo: return
        
        self.eventos_animacao.append({'tipo': 'ataque', 'atacante': self, 'alvo': alvo})
        if self.sound_player: self.sound_player('attack')

        flanking_bonus = 0
        if self.alcance == 1 and time_aliado:
            for aliado in time_aliado:
                if aliado is not self and aliado.esta_vivo and aliado.alcance == 1 and calcular_distancia(aliado, alvo) <= aliado.alcance:
                    flanking_bonus = 2
                    logger(f"  {self.nome} está flanqueando {alvo.nome} com um aliado! (+2 para atacar)")
                    break

        logger(f"{self.nome} (Lvl {self.nivel}) ataca {alvo.nome} (Lvl {alvo.nivel}).")
        
        ac_alvo = alvo.ac
        terreno_alvo = tabuleiro.get_terrain_em(alvo.pos_x, alvo.pos_y)
        if terreno_alvo == "FLORESTA":
            ac_alvo += 2
            logger(f"  {alvo.nome} recebe cobertura da floresta (+2 AC)!")

        rolagem_ataque = random.randint(1, 20)
        total_ataque = rolagem_ataque + self.bonus_ataque + flanking_bonus
        log_ataque = f"  Rolagem de Ataque: {rolagem_ataque} (d20) + {self.bonus_ataque} (bônus) + {flanking_bonus} (flanco) = {total_ataque}."

        if rolagem_ataque == 20:
            logger(f"{log_ataque} Acerto CRÍTICO!")
            self.causar_dano(alvo, logger, is_critico=True)
        elif total_ataque >= ac_alvo:
            logger(f"{log_ataque} Acerta (AC do alvo é {ac_alvo})!")
            self.causar_dano(alvo, logger)
        else:
            logger(f"{log_ataque} Erra (AC do alvo é {ac_alvo}).")
            if self.sound_player: self.sound_player('miss')
            self.eventos_animacao.append({'tipo': 'dano', 'alvo': alvo, 'dano': 'ERROU!'})

    def causar_dano(self, alvo, logger=print, is_critico=False):
        num_rolagens = self.dado_dano[0] * 2 if is_critico else self.dado_dano[0]
        dano_rolado = sum(random.randint(1, self.dado_dano[1]) for _ in range(num_rolagens))
        
        if is_critico: logger(f"  Dano CRÍTICO!")

        dano_total = max(1, dano_rolado + self.bonus_dano)
        logger(f"  Rolagem de Dano: {dano_rolado} ({num_rolagens}d{self.dado_dano[1]}) + {self.bonus_dano} (bônus) = {dano_total} de dano.")
        
        alvo.receber_dano(dano_total, self, logger)
        
        if self.sound_player: self.sound_player('hit')
        self.eventos_animacao.append({'tipo': 'dano', 'alvo': alvo, 'dano': dano_total})

    def receber_dano(self, quantidade, atacante, logger=print):
        self.hp_atual -= quantidade
        if self.hp_atual <= 0:
            self.hp_atual = 0
            self.esta_vivo = False
            logger(f"  {self.nome} foi derrotado por {atacante.nome}!")
            if atacante:
                atacante.kills += 1
                atacante.ganhar_xp(1, logger)
            self.eventos_animacao.append({'tipo': 'morte', 'personagem': self})
        else:
            logger(f"  {self.nome} está com {self.hp_atual}/{self.hp_max} HP.")

    def receber_cura(self, quantidade, logger=print):
        self.hp_atual = min(self.hp_max, self.hp_atual + quantidade)
        logger(f"  {self.nome} é curado em {quantidade} e agora tem {self.hp_atual}/{self.hp_max} HP.")
        if self.sound_player: self.sound_player('heal')
        self.eventos_animacao.append({'tipo': 'cura', 'alvo': self, 'cura': quantidade})

    def __str__(self):
        return f"{self.nome} (HP: {self.hp_atual}/{self.hp_max}, AC: {self.ac})"
