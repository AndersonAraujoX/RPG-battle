import random
import math
from src.config import TIME_A, TIME_B, TERRENO_FLORESTA, TERRENO_ROCHA, TERRENO_BARRIL, PROPRIEDADES_STATUS_EFEITO, DANO_FISICO
from ..utils import calcular_distancia, rolar_d20
from .status_efeito import StatusEfeito
from src.itens.item import HealthPotion, ManaPotion, Antidote, SmokeBomb

from ..utils import carregar_dados_personagens

DADOS_PERSONAGENS = carregar_dados_personagens()

class Personagem:
    def __init__(self, nome, time, nivel=1, sound_player=None, stats=None):
        self.nome = nome
        self.time = time
        self.nivel = nivel
        self.xp = 0
        self.xp_para_upar = 2 ** self.nivel
        self.kills = 0
        
        # Initialize equipment early as stats calculation depends on it
        self.arma_equipada = None
        self.armadura_equipada = None
        self.acessorios_equipados = []

        class_name = self.__class__.__name__
        if class_name in DADOS_PERSONAGENS:
            data = DADOS_PERSONAGENS[class_name]
            stats_data = data.get("stats", {})
            self._forca = stats_data.get("forca", 10)
            self._destreza = stats_data.get("destreza", 10)
            self._constituicao = stats_data.get("constituicao", 10)
            self._inteligencia = stats_data.get("inteligencia", 10)
            self._sabedoria = stats_data.get("sabedoria", 10)
            self._carisma = stats_data.get("carisma", 10)
            
            self.ac_base = data.get("ac", 10)
            self.dado_dano = tuple(data.get("dado_dano", [1, 4]))
            self.dado_vida = tuple(data.get("dado_vida", [1, 6]))
            self.alcance = data.get("alcance", 1)
            self.tipo_dano_base = data.get("tipo_dano", DANO_FISICO)
            
            # Calculate hp_max based on provided value or formula
            base_hp = data.get("hp", (self.dado_vida[1] + self.mod_con))
            self.hp_max = base_hp + ((nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))
        else:
            # Default stats if not found in JSON
            self._forca, self._destreza, self._constituicao, self._inteligencia, self._sabedoria, self._carisma = 10, 10, 10, 10, 10, 10
            # Damage Resilience System
            self.resistencias = [] # Take half damage (integer division)
            self.vulnerabilidades = [] # Take double damage
            self.imunidades = [] # Take no damage
            
            self.ac_base = 10
            self.dado_dano = (1, 4)
            self.dado_vida = (1, 6)
            self._velocidade = 4
            self.alcance = 1
            self.tipo_dano_base = DANO_FISICO
            self.hp_max = 10 + self.mod_con

        # Initialize imunity/resistance BEFORE using data
        
        if class_name in DADOS_PERSONAGENS:
             self.imunidades = DADOS_PERSONAGENS[class_name].get("imunidades", {})
             self.resistencias = DADOS_PERSONAGENS[class_name].get("resistencias", {})
             self.vulnerabilidades = DADOS_PERSONAGENS[class_name].get("vulnerabilidades", {})

        # Override with custom stats if provided
        if stats:
            if 'hp' in stats: self.hp_max = stats['hp']
            if 'ac' in stats: self.ac_base = stats['ac']
            if 'ataque' in stats: 
                # Bonus de ataque é calculado, não setado diretamente. 
                # Podemos ajustar a força/destreza para corresponder ou criar um override.
                # Como bonus_ataque é uma property, vamos criar um atributo _bonus_ataque_override
                self._bonus_ataque_override = stats['ataque']
            if 'forca' in stats: self._forca = stats['forca']
            # ... outros stats se necessário

        self.hp_atual = self.hp_max
        self.mana_atual, self.mana_max = 0, 0
        self.energia_atual, self.energia_max = 0, 0
        self.iniciativa = 0
        self.esta_vivo = True
        self.pos_x, self.pos_y = -1, -1
        self.cooldowns = {}
        self.cooldown_max = {}
        self.sound_player = sound_player
        self.eventos_animacao = []
        self.status_efeitos = []
        # Removed redundant data.get calls here
        self.inventario = [HealthPotion()]
        self.elevacao = 0
        self.threat_level = 1
        self.loot_table = [] # Lista de tuplas (ItemClass, chance 0.0-1.0)
        
        # Death Saves & State System
        self.death_saves_successes = 0
        self.death_saves_failures = 0
        self.estado = "NORMAL" # NORMAL, INCONSCIENTE, MORTO, ESTABILIZADO
        
        self.habilidades = {}
        self.custo_habilidades = {}

    def equipar_arma(self, arma):
        self.arma_equipada = arma

    def equipar_armadura(self, armadura):
        self.armadura_equipada = armadura

    def equipar_acessorio(self, acessorio):
        self.acessorios_equipados.append(acessorio)

    def tick_cooldowns(self):
        for key in self.cooldowns:
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1

    def tick_recursos(self):
        # Regenerate a small amount of resources each turn
        if self.mana_max > 0:
            self.mana_atual = min(self.mana_max, self.mana_atual + 1)
        if self.energia_max > 0:
            self.energia_atual = min(self.energia_max, self.energia_atual + 1)

    def aplicar_status_efeito(self, nome_efeito, duracao_turnos=1, logger=print, **kwargs):
        from src.config import COR_STATUS, COR_TEXTO
        if nome_efeito in self.imunidades:
            logger((f"  {self.nome} é imune a {nome_efeito}!", COR_TEXTO))
            return

        if nome_efeito not in PROPRIEDADES_STATUS_EFEITO:
            logger((f"  ERRO: Efeito de status '{nome_efeito}' não encontrado.", COR_DANO))
            return

        for efeito in self.status_efeitos:
            if efeito.nome == nome_efeito:
                efeito.duracao_restante += duracao_turnos
                # Update extra data if provided
                if kwargs: efeito.dados_extra.update(kwargs)
                logger((f"  {self.nome} teve a duração de {nome_efeito} estendida para {efeito.duracao_restante} turnos.", COR_STATUS))
                return

        novo_efeito = StatusEfeito(nome_efeito, duracao_turnos, **kwargs)
        self.status_efeitos.append(novo_efeito)
        logger((f"  {self.nome} foi afetado por {novo_efeito.nome} por {novo_efeito.duracao_restante} turnos.", COR_STATUS))
        self.eventos_animacao.append({'tipo': 'status_aplicado', 'personagem': self, 'efeito': novo_efeito.nome})

    def remover_status_efeito(self, nome_efeito, logger=print):
        from src.config import COR_TEXTO
        self.status_efeitos = [e for e in self.status_efeitos if e.nome != nome_efeito]
        logger((f"  {self.nome} não está mais sob efeito de {nome_efeito}.", COR_TEXTO))
        self.eventos_animacao.append({'tipo': 'status_removido', 'personagem': self, 'efeito': nome_efeito})

    def tick_status_efeitos(self, tabuleiro, logger=print):
        efeitos_a_remover = []
        for efeito in self.status_efeitos:
            efeito.aplicar_efeito_por_turno(self, tabuleiro, logger)
            if not efeito.tick():
                efeitos_a_remover.append(efeito.nome)
        
        for nome_efeito in efeitos_a_remover:
            self.remover_status_efeito(nome_efeito, logger)

    @property
    def pode_agir(self):
        for efeito in self.status_efeitos:
            if not efeito.propriedades.get("pode_agir", True):
                return False
        return True

    @property
    def pode_fugir(self):
        for efeito in self.status_efeitos:
            if efeito.nome == "Fuga Garantida": return True
            if not efeito.propriedades.get("pode_fugir", True):
                return False
        return True

    def ganhar_xp(self, quantidade, logger=print):
        from src.config import COR_XP
        if not self.esta_vivo: return
        self.xp += quantidade
        logger((f"  {self.nome} ganha {quantidade} XP!", COR_XP))
        if self.xp >= self.xp_para_upar:
            self.subir_de_nivel(logger)

    def subir_de_nivel(self, logger=print):
        from src.config import COR_LEVEL_UP
        self.nivel += 1
        self.xp = 0
        self.xp_para_upar = 2 ** self.nivel
        
        aumento_hp = random.randint(1, self.dado_vida[1]) + self.mod_con
        if aumento_hp < 1: aumento_hp = 1
        
        self.hp_max += aumento_hp
        self.hp_atual += aumento_hp
        
        logger((f"  *** {self.nome} SUBIU PARA O NÍVEL {self.nivel}! ***", COR_LEVEL_UP))
        logger((f"  (HP máximo aumentado em {aumento_hp})", COR_LEVEL_UP))
        if self.sound_player: self.sound_player('level_up')
        self.eventos_animacao.append({'tipo': 'level_up', 'personagem': self})

        # A lógica de escolha de atributos será tratada na classe Game
        self.eventos_animacao.append({'tipo': 'escolha_atributo', 'personagem': self})

    def get_bonus_acessorio(self, stat):
        bonus = 0
        for acessorio in self.acessorios_equipados:
            if stat in acessorio.bonus:
                bonus += acessorio.bonus[stat]
        return bonus

    @property
    def forca(self): return self._forca + self.get_bonus_acessorio('forca')
    @property
    def destreza(self): return self._destreza + self.get_bonus_acessorio('destreza')
    @property
    def constituicao(self): return self._constituicao + self.get_bonus_acessorio('constituicao')
    @property
    def inteligencia(self): return self._inteligencia + self.get_bonus_acessorio('inteligencia')
    @property
    def sabedoria(self): return self._sabedoria + self.get_bonus_acessorio('sabedoria')
    @property
    def carisma(self): return self._carisma + self.get_bonus_acessorio('carisma')
    @property
    def velocidade(self): return self._velocidade + self.get_bonus_acessorio('velocidade')

    @property
    def ac(self):
        if self.armadura_equipada:
            return self.armadura_equipada.bonus_ac
        return self.ac_base

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
    def mod_car(self): return (self.carisma - 10) // 2
    
    @property
    def bonus_proficiencia(self): return 1 + math.ceil(self.nivel / 4)

    @property
    def bonus_ataque(self):
        if hasattr(self, '_bonus_ataque_override'):
            return self._bonus_ataque_override
        bonus = self.bonus_proficiencia
        for efeito in self.status_efeitos:
            if efeito.propriedades.get("bonus_ataque_fixo"):
                bonus += efeito.propriedades["bonus_ataque_fixo"]
        return bonus

    @property
    def bonus_dano(self):
        bonus = 0
        for efeito in self.status_efeitos:
            if efeito.propriedades.get("bonus_dano_ataque"):
                bonus += efeito.propriedades["bonus_dano_ataque"]
        return bonus

    def rolar_iniciativa(self):
        self.iniciativa = random.randint(1, 20) + self.mod_des
        return self.iniciativa

    def pode_atacar(self, alvo, tabuleiro):
        if not alvo or not alvo.esta_vivo:
            return False
        dist = calcular_distancia(self, alvo)
        if dist > self.alcance:
            return False
        # Check Line of Sight
        if not tabuleiro.calcular_linha_visao(self.pos_x, self.pos_y, alvo.pos_x, alvo.pos_y):
            return False
        return True

    def decidir_acao(self, inimigos, aliados, tabuleiro, logs_turno):
        from src.config import COR_TEXTO
        if not self.pode_agir:
            logs_turno.append((f"  {self.nome} está impedido de agir devido a um efeito de status.", COR_TEXTO))
            return {'acao': 'passar'}
            
        # Check for Provoked Status
        status_provocado = next((e for e in self.status_efeitos if e.nome == "Provocado"), None)
        if status_provocado:
            provocador = status_provocado.dados_extra.get("provocador")
            if provocador and provocador.esta_vivo and provocador in inimigos:
                 logs_turno.append((f"  {self.nome} está FURIOSO e foca seus ataques em {provocador.nome}!", COR_TEXTO))
                 # Se estiver ao alcance, ataca
                 if calcular_distancia(self, provocador) <= self.alcance:
                     return {'acao': 'atacar', 'alvo': provocador}
                 # Se não, move-se em direção a ele
                 return {'acao': 'mover', 'alvo': provocador}

        # 0. Pegar item se estiver em cima de um
        item_no_chao = tabuleiro.get_item_em(self.pos_x, self.pos_y)
        if item_no_chao:
            return {'acao': 'pegar_item', 'item': item_no_chao}

        # 1. Usar Poção de Cura se com pouca vida
            for item in self.inventario:
                if isinstance(item, HealthPotion):
                    logs_turno.append((f"  {self.nome} está com pouca vida e usa uma Poção de Cura!", COR_TEXTO))
                    item.usar(self, logs_turno.append)
                    self.inventario.remove(item)
                    return {'acao': 'usar_item', 'item': item}
        
        # 1.1 Usar Poção de Mana se com pouco mana
        if self.mana_max > 0 and self.mana_atual / self.mana_max < 0.3:
             for item in self.inventario:
                if isinstance(item, ManaPotion):
                    logs_turno.append((f"  {self.nome} está com pouco mana e usa uma Poção de Mana!", COR_TEXTO))
                    item.usar(self, logs_turno.append)
                    self.inventario.remove(item)
                    return {'acao': 'usar_item', 'item': item}

        # 1.2 Usar Antídoto se envenenado
        from src.config import STATUS_ENVENENADO
        if any(e.nome == STATUS_ENVENENADO for e in self.status_efeitos):
             for item in self.inventario:
                if isinstance(item, Antidote):
                    logs_turno.append((f"  {self.nome} usa um Antídoto para curar o veneno!", COR_TEXTO))
                    item.usar(self, logs_turno.append)
                    self.inventario.remove(item)
                    return {'acao': 'usar_item', 'item': item}

        # 1.3 Usar Bomba de Fumaça se precisar fugir e não puder (ou para garantir)
        if self.hp_atual / self.hp_max < 0.2 and inimigos:
             for item in self.inventario:
                if isinstance(item, SmokeBomb):
                    logs_turno.append((f"  {self.nome} usa uma Bomba de Fumaça para escapar!", COR_TEXTO))
                    item.usar(self, logs_turno.append)
                    self.inventario.remove(item)
                    return {'acao': 'fugir'} # Tenta fugir imediatamente após usar
        
        # 2. Tentar fugir se com pouca vida
        if self.hp_atual / self.hp_max < 0.25 and inimigos and self.pode_fugir:
            return {'acao': 'fugir'}

        if not inimigos:
            return {'acao': 'passar'}

        # 3. Lógica de seleção de alvo aprimorada
        avg_damage = (self.dado_dano[0] * (self.dado_dano[1] + 1) / 2) + self.bonus_dano
        
        inimigos_em_range = [p for p in inimigos if calcular_distancia(self, p) <= self.alcance]
        
        # Prioridade 1: Inimigos que podem ser finalizados neste turno
        alvos_finalizaveis = [p for p in inimigos_em_range if p.hp_atual <= avg_damage]
        if alvos_finalizaveis:
            alvo = max(alvos_finalizaveis, key=lambda p: p.threat_level)
            logs_turno.append((f"  ({self.nome} identifica uma oportunidade de finalizar {alvo.nome}!)", COR_TEXTO))
            return {'acao': 'atacar', 'alvo': alvo}
        
        # Prioridade 2: Atacar o inimigo mais próximo em range
        if inimigos_em_range:
            alvo = min(inimigos_em_range, key=lambda p: calcular_distancia(self,p))
            logs_turno.append((f"  ({self.nome} ataca o inimigo mais próximo ao seu alcance: {alvo.nome}.)", COR_TEXTO))
            return {'acao': 'atacar', 'alvo': alvo}

        # Prioridade 3: Mover-se em direção ao inimigo com menor HP
        alvo = min(inimigos, key=lambda p: p.hp_atual)
        logs_turno.append((f"  ({self.nome} se move em direção a {alvo.nome}, o inimigo com menos vida.)", COR_TEXTO))
        return {'acao': 'mover', 'alvo': alvo}
        
        return {'acao': 'passar'}

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print, tipo_dano_override=None, habilidade=None):
        from src.config import COR_TEXTO, COR_CRITICO
        if not self.esta_vivo: return
        
        self.eventos_animacao.append({'tipo': 'ataque', 'atacante': self, 'alvo': alvo, 'habilidade': habilidade})
        if self.sound_player: self.sound_player('attack')

        if self.sound_player: self.sound_player('attack')

        vantagem = False
        desvantagem = False
        msg_modificadores = []

        # 1. Flanking (Grants Advantage)
        if self.alcance == 1 and time_aliado:
            for aliado in time_aliado:
                if aliado is not self and aliado.esta_vivo and aliado.alcance == 1 and calcular_distancia(aliado, alvo) <= 1:
                     dx_self = self.pos_x - alvo.pos_x
                     dy_self = self.pos_y - alvo.pos_y
                     dx_ally = aliado.pos_x - alvo.pos_x
                     dy_ally = aliado.pos_y - alvo.pos_y
                     
                     if dx_self == -dx_ally and dy_self == -dy_ally:
                         vantagem = True
                         msg_modificadores.append(f"Flanqueando com {aliado.nome}")
                         break

        # 2. Elevation (Higher Ground grants Advantage)
        if self.elevacao > alvo.elevacao and self.alcance > 1:
            vantagem = True
            msg_modificadores.append("Terreno Alto")
            
        logger((f"{self.nome} (Lvl {self.nivel}) ataca {alvo.nome} (Lvl {alvo.nivel}).", COR_TEXTO))
        
        # Calculate Cover
        # Need to import calcular_cobertura inside method to avoid circular import if utils imports Personagem (it doesn't, but safe)
        from src.utils import calcular_cobertura
        bonus_cobertura = calcular_cobertura(self, alvo, tabuleiro)
        
        ac_alvo = alvo.ac + bonus_cobertura
        
        if bonus_cobertura > 0:
            if bonus_cobertura >= 1000: # Blocked functionality in future? Currently just massive AC
                logger((f"  Alvo tem COBERTURA TOTAL! (Linha de visão bloqueada)", (255, 100, 100)))
            elif bonus_cobertura >= 5:
                logger((f"  Alvo tem +5 AC por Cobertura 3/4!", (200, 200, 255)))
            else:
                 logger((f"  Alvo tem +2 AC por Meia Cobertura!", (200, 200, 255)))
            
        terreno_alvo = tabuleiro.get_terrain_em(alvo.pos_x, alvo.pos_y)
        if terreno_alvo == TERRENO_FLORESTA:
            if self.alcance > 1: # Ranged attack
                # Forest grants cover against ranged -> Disadvantage? Or keep Miss Chance?
                # 5e Rules: Cover grants +AC. Obscurement grants Disadvantage.
                # Let's simple use Cover (+2 AC) for now as implemented, or swap to Disadvantage?
                # Let's keep Cover +2 AC for consistency with "Cover" system task.
                # But user asked for Mechanics. Let's make it Disadvantage to test the system?
                # No, Cover is typically AC. Let's stick to AC for terrain.
                pass 
                
        # Execute Attack Roll
        rolagem_ataque, msg_dado = rolar_d20(vantagem=vantagem, desvantagem=desvantagem)
        
        total_ataque = rolagem_ataque + self.bonus_ataque
        
        mod_str = f" ({', '.join(msg_modificadores)})" if msg_modificadores else ""
        log_ataque = f"  Ataque: {rolagem_ataque}{msg_dado} + {self.bonus_ataque} = {total_ataque}{mod_str} vs AC {ac_alvo}."

        if rolagem_ataque == 20: # Critical Hit
            logger((f"{log_ataque} Acerto CRÍTICO!", COR_CRITICO))
            if self.sound_player: self.sound_player('critical_hit')
            self.causar_dano(alvo, tabuleiro, logger, is_critico=True, tipo_dano_override=tipo_dano_override)
        elif total_ataque >= ac_alvo:
            logger((f"{log_ataque} Acerta!", COR_TEXTO))
            self.causar_dano(alvo, tabuleiro, logger, tipo_dano_override=tipo_dano_override)
        else:
            logger((f"{log_ataque} Erra (AC do alvo é {ac_alvo}).", COR_TEXTO))
            if self.sound_player: self.sound_player('miss')
            self.eventos_animacao.append({'tipo': 'dano', 'alvo': alvo, 'dano': 'ERROU!'})

    def causar_dano(self, alvo, tabuleiro, logger=print, is_critico=False, tipo_dano_override=None):
        from src.config import COR_DANO, COR_CRITICO
        if self.arma_equipada:
            dado_dano = self.arma_equipada.dado_dano
            tipo_dano = self.arma_equipada.tipo_dano
        else:
            dado_dano = self.dado_dano
            tipo_dano = self.tipo_dano_base

        if tipo_dano_override:
            tipo_dano = tipo_dano_override
            
        num_rolagens = dado_dano[0] * 2 if is_critico else dado_dano[0]
        dano_rolado = sum(random.randint(1, dado_dano[1]) for _ in range(num_rolagens))
        
        if is_critico: logger((f"  Dano CRÍTICO!", COR_CRITICO))

        dano_total = max(1, dano_rolado + self.bonus_dano)
        logger((f"  Rolagem de Dano: {dano_rolado} ({num_rolagens}d{dado_dano[1]}) + {self.bonus_dano} (bônus) = {dano_total} de dano {tipo_dano}.", COR_DANO))
        
        alvo.receber_dano(dano_total, self, tabuleiro, logger, tipo_dano=tipo_dano)
        
        if self.sound_player: self.sound_player('hit')

    def receber_dano(self, quantidade, atacante=None, tabuleiro=None, logger=print, tipo_dano=DANO_FISICO):
        from src.config import COR_DANO, COR_TEXTO
        if tipo_dano in self.imunidades:
            logger((f"  {self.nome} é imune a dano do tipo '{tipo_dano}'!", COR_TEXTO))
            self.eventos_animacao.append({'tipo': 'dano', 'alvo': self, 'dano': 'IMUNE'})
            self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'IMUNE', 'cor': (200, 200, 200)})
            return 0, " (Imune)"

        dano_final = float(quantidade)
        msg_eficacia = ""

        # Aplica vulnerabilidades (dano dobrado)
        if tipo_dano in self.vulnerabilidades:
            dano_final *= 2.0
            msg_eficacia = " (Vulnerável!)"
            logger((f"  Dano dobrado! {self.nome} é vulnerável a '{tipo_dano}'.", COR_DANO))

        # Aplica resistências (meio dano)
        if tipo_dano in self.resistencias:
            dano_final *= 0.5
            msg_eficacia = " (Resistente!)"
            logger((f"  Dano reduzido! {self.nome} é resistente a '{tipo_dano}'.", COR_TEXTO))
        
        dano_final = int(round(dano_final))

        for efeito in self.status_efeitos:
            if efeito.propriedades.get("resistencia_dano_percentual"):
                dano_final -= int(dano_final * efeito.propriedades["resistencia_dano_percentual"])
        
        self.hp_atual -= dano_final
        self.eventos_animacao.append({'tipo': 'dano', 'alvo': self, 'dano': dano_final})
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': f'-{dano_final}', 'cor': COR_DANO})

        if self.hp_atual <= 0:
            self.hp_atual = 0
            
            if self.estado != "MORTO":
                if self.estado != "INCONSCIENTE":
                    self.estado = "INCONSCIENTE"
                    self.death_saves_successes = 0
                    self.death_saves_failures = 0
                    logger((f"  {self.nome} caiu INCONSCIENTE!", COR_DANO))
                    self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'INCONSCIENTE', 'cor': (100, 100, 100)})
                else: 
                     # Already unconscious, taking damage = 1 death save failure
                     self.death_saves_failures += 1
                     logger((f"  {self.nome} (Inconsciente) recebe dano: 1 Falha no Teste de Morte. ({self.death_saves_failures}/3)", COR_DANO))
                     if self.death_saves_failures >= 3:
                         self.morrer(tabuleiro, logger, atacante)
            
        else:
            logger((f"  {self.nome} está com {self.hp_atual}/{self.hp_max} HP.", COR_TEXTO))
            
        return dano_final, msg_eficacia

    def realizar_teste_morte(self, logger=print):
        from src.config import COR_TEXTO, COR_XP, COR_DANO, COR_CURA
        
        rolagem = rolar_d20()[0]
        msg = f"Teste de Morte: {rolagem}"
        
        if rolagem == 20: 
            self.hp_atual = 1
            self.estado = "NORMAL"
            self.death_saves_successes = 0
            self.death_saves_failures = 0
            logger((f"  {msg} -> CRÍTICO! {self.nome} recupera 1 HP e acorda!", COR_CURA))
            self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'RENASCEU!', 'cor': COR_CURA})
            return
            
        elif rolagem == 1: 
            self.death_saves_failures += 2
            logger((f"  {msg} -> FALHA CRÍTICA! 2 Falhas adicionadas.", COR_DANO))
            
        elif rolagem >= 10: 
            self.death_saves_successes += 1
            logger((f"  {msg} -> Sucesso. ({self.death_saves_successes}/3)", COR_XP))
            
        else: 
            self.death_saves_failures += 1
            logger((f"  {msg} -> Falha. ({self.death_saves_failures}/3)", COR_DANO))
            
        if self.death_saves_successes >= 3:
            self.estado = "ESTABILIZADO"
            self.death_saves_successes = 0
            self.death_saves_failures = 0
            logger((f"  {self.nome} está ESTABILIZADO.", COR_XP))
            
        if self.death_saves_failures >= 3:
            self.morrer(None, logger, None) 

    def morrer(self, tabuleiro, logger, atacante):
        from src.config import COR_DANO
        self.estado = "MORTO"
        self.esta_vivo = False
        logger((f"  {self.nome} MORREU!", COR_DANO))
        self.eventos_animacao.append({'tipo': 'morte', 'personagem': self})
        
        if atacante:
             atacante.kills += 1
             atacante.ganhar_xp(1, logger)

        if tabuleiro:
            # Drop items logic
            if self.inventario and random.random() < 0.5:
                item_dropado = random.choice(self.inventario)
                tabuleiro.itens_no_chao[self.pos_y][self.pos_x] = item_dropado
                logger((f"  {self.nome} dropou {item_dropado.nome}!", (255, 215, 0)))



    def receber_cura(self, quantidade, logger=print):
        from src.config import COR_CURA
        self.hp_atual = min(self.hp_max, self.hp_atual + quantidade)
        logger((f"  {self.nome} é curado em {quantidade} e agora tem {self.hp_atual}/{self.hp_max} HP.", COR_CURA))
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': f'+{quantidade}', 'cor': COR_CURA})
        if self.sound_player: self.sound_player('heal')

    def fazer_teste_resistencia(self, atributo, dificuldade, logger=print):
        from src.config import COR_TEXTO, COR_XP
        
        modificadores = {
            'forca': self.mod_for,
            'destreza': self.mod_des,
            'constituicao': self.mod_con,
            'inteligencia': self.mod_int,
            'sabedoria': self.mod_sab,
            'carisma': self.mod_car
        }
        
        mod = modificadores.get(atributo.lower(), 0)
        rolagem = rolar_d20()[0] # Standard roll, NO advantage/disadvantage implemented for saves yet
        total = rolagem + mod + self.bonus_proficiencia # Assuming proficient? Or just mod? 
        # 5e: Saves use proficiency ONLY if class is proficient in that save.
        # For simplicity in this project, let's add proficiency to all saves OR checks?
        # Let's keep it simple: Just Attribute Mod for now, unless we define "Save Proficiencies".
        # Re-reading plan: "Roll d20 + Attribute Modifier". Okay.
        
        total = rolagem + mod
        # Note: Some classes might have proficiency in saves. Feature for later.
        
        sucesso = total >= dificuldade
        resultado_str = "SUCESSO" if sucesso else "FALHA"
        cor = COR_XP if sucesso else COR_TEXTO
        
        logger((f"  {self.nome} faz teste de {atributo.capitalize()}: {rolagem} (d20) + {mod} (mod) = {total} vs DC {dificuldade}. -> {resultado_str}", cor))
        
        return sucesso, f" ({resultado_str})"
        self.eventos_animacao.append({'tipo': 'cura', 'alvo': self, 'cura': quantidade})

    def to_dict(self):
        return {
            "nivel": self.nivel,
            "xp": self.xp,
            "hp_atual": self.hp_atual,
            "mana_atual": self.mana_atual,
            "inventario": [item.__class__.__name__ for item in self.inventario],
            "stats": {
                "_forca": self._forca,
                "_destreza": self._destreza,
                "_constituicao": self._constituicao,
                "_inteligencia": self._inteligencia,
                "_sabedoria": self._sabedoria,
                "_carisma": self._carisma,
            }
        }

    def from_dict(self, data):
        self.nivel = data.get("nivel", self.nivel)
        self.xp = data.get("xp", self.xp)
        self.hp_atual = data.get("hp_atual", self.hp_atual)
        self.mana_atual = data.get("mana_atual", self.mana_atual)
        
        # Recria o inventário a partir dos nomes das classes
        # (Isso requer um mapeamento de nome de classe para classe)
        # Por simplicidade, vamos pular a recriação do inventário por enquanto

        stats = data.get("stats", {})
        self._forca = stats.get("_forca", self._forca)
        self._destreza = stats.get("_destreza", self._destreza)
        self._constituicao = stats.get("_constituicao", self._constituicao)
        self._inteligencia = stats.get("_inteligencia", self._inteligencia)
        self._sabedoria = stats.get("_sabedoria", self._sabedoria)
        self._carisma = stats.get("_carisma", self._carisma)
        
        # Recalcula os atributos derivados
        self.xp_para_upar = 2 ** self.nivel
        base_hp = DADOS_PERSONAGENS.get(self.__class__.__name__, {}).get("hp", (self.dado_vida[1] + self.mod_con))
        self.hp_max = base_hp + ((self.nivel - 1) * (random.randint(1, self.dado_vida[1]) + self.mod_con))

