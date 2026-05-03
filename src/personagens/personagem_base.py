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
            self.dado_vida = tuple(data.get("dado_vida", [1, 6]))
            self.alcance = data.get("alcance", 1)
            self.tipo_dano_base = data.get("tipo_dano", DANO_FISICO)
            self._velocidade = data.get("speed", 6)
            
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
        self.classe_nome = self.__class__.__name__
        self.death_saves_successes = 0
        self.death_saves_failures = 0
        self.estado = "NORMAL" # NORMAL, INCONSCIENTE, MORTO, ESTABILIZADO
        
        # Turn State (Action Economy)
        self.movimento_realizado = False
        self.acao_realizada = False
        self.movimento_realizado = False
        self.acao_realizada = False
        self.acao_bonus_realizada = False
        self.invulneravel = False # God Mode support
        
        self.habilidades = {}
        self.custo_habilidades = {}
        self.perks_adquiridos = []

    def adquirir_perk(self, perk_id):
        if perk_id not in self.perks_adquiridos:
            self.perks_adquiridos.append(perk_id)
            print(f"{self.nome} adquiriu o perk: {perk_id}")

    def tem_perk(self, perk_id):
        return perk_id in self.perks_adquiridos

    def pode_desbloquear_perk(self, perk_data):
        """Verifica se o personagem atende aos requisitos para desbloquear um perk."""
        # 1. Já possui?
        if self.tem_perk(perk_data['id']):
            return False
        # 2. Nível suficiente?
        if self.nivel < perk_data['nivel_req']:
            return False
        # 3. Pré-requisito atendido?
        req = perk_data.get('req_perk')
        if req and not self.tem_perk(req):
            return False
        
        return True


    def iniciar_turno(self):
        self.movimento_realizado = False
        self.acao_realizada = False
        self.acao_bonus_realizada = False
        self.tick_cooldowns()
        self.tick_recursos()

    def equipar_arma(self, arma):
        self.arma_equipada = arma
        if hasattr(arma, 'dado_dano'):
            self.dado_dano = arma.dado_dano

    def equipar_armadura(self, armadura):
        self.armadura_equipada = armadura

    def equipar_acessorio(self, acessorio):
        self.acessorios_equipados.append(acessorio)

    # Removed tick_cooldowns/tick_recursos from here (moved to iniciar_turno or keep as helpers called by it)
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
        from src.config import COR_STATUS, COR_TEXTO, COR_DANO
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

    def receber_dano(self, dano, atacante, tabuleiro, logger=print, tipo_dano="Fisico"):
        from src.config import COR_DANO, COR_TEXTO
        
        if self.invulneravel:
            logger((f"  {self.nome} é invulnerável!", COR_TEXTO))
            return

        if not self.esta_vivo: return

        self.hp_atual -= dano
        if self.hp_atual < 0: self.hp_atual = 0
        
        logger((f"  {self.nome} sofreu {dano} de dano ({tipo_dano})! [HP: {self.hp_atual}/{self.hp_max}]", COR_DANO))
        
        if self.sound_player: self.sound_player('hit')
        self.eventos_animacao.append({'tipo': 'dano', 'alvo': self, 'valor': dano})

        if self.hp_atual == 0:
            self.morrer(logger)

    def morrer(self, logger=print):
        from src.config import COR_CRITICO
        if self.estado != "MORTO":
            self.estado = "MORTO"
            logger((f"  {self.nome} foi derrotado!", COR_CRITICO))
            self.eventos_animacao.append({'tipo': 'morte', 'alvo': self})

    def ganhar_xp(self, quantidade, logger=print):
        from src.config import COR_XP
        if not self.esta_vivo: return
        self.xp += quantidade
        logger((f"  {self.nome} ganha {quantidade} XP!", COR_XP))
        if self.xp >= self.xp_para_upar:
            self.subir_de_nivel(logger)

    def usar_dash(self, logs_turno):
        from src.config import COR_STATUS
        if self.acao_realizada:
            logs_turno.append((f"  {self.nome} já realizou uma ação neste turno.", (200, 200, 200)))
            return False
            
        self.acao_realizada = True
        # Dash doubles movement for the turn. 
        # Since we don't have a rigid movement counter decrementing, 
        # we can just apply a temporary speed buff or handle it in logic.
        # But 'Movimento' is usually handled by `movimento_realizado` flag.
        # If Dash is used, maybe we allow `movimento_realizado` to be reset?
        # Or simplistic: Apply "Dash" status which affects movement logic.
        
        self.aplicar_status_efeito("Dash", 1, logs_turno.append)
        logs_turno.append((f"  {self.nome} usa Ação de Disparada (Dash)! (Movimento Dobrado)", COR_STATUS))
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'DASH', 'cor': (255, 255, 0)})
        return True

    def usar_disengage(self, logs_turno):
        from src.config import COR_STATUS
        if self.acao_realizada:
            return False
        
        self.acao_realizada = True
        self.aplicar_status_efeito("Desengajar", 1, logs_turno.append)
        logs_turno.append((f"  {self.nome} usa Desengajar! (Imune a Ataques de Oportunidade)", COR_STATUS))
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'DISENGAGE', 'cor': (100, 255, 100)})
        return True
        
    def usar_dodge(self, logs_turno):
        from src.config import COR_STATUS
        if self.acao_realizada:
            return False
            
        self.acao_realizada = True
        self.aplicar_status_efeito("Esquiva", 1, logs_turno.append)
        logs_turno.append((f"  {self.nome} entra em Esquiva (Dodge)! (Desvantagem para atacantes)", COR_STATUS))
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'DODGE', 'cor': (100, 100, 255)})
        return True
        
    def usar_help(self, alvo, logs_turno):
        from src.config import COR_STATUS
        if self.acao_realizada:
            return False
            
        self.acao_realizada = True
        # Grant Advantage to next attack against target
        alvo.aplicar_status_efeito("Alvo de Ajuda", 1, logs_turno.append) # 1 turn or until hit?
        logs_turno.append((f"  {self.nome} Ajuda contra {alvo.nome}! (Vantagem no próximo ataque)", COR_STATUS))
        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'HELP', 'cor': (255, 255, 255)})
        return True

    def usar_grapple(self, alvo, logs_turno):
        """Agarrar (Grapple): Athletics (For) vs Athletics/Acrobatics (For/Des)"""
        from src.config import COR_STATUS
        if self.acao_realizada: return False
        
        self.acao_realizada = True
        
        # Roll Contest
        roll_atk = random.randint(1, 20) + self.mod_for
        # Target resists with better of Str or Dex
        mod_def = max(alvo.mod_for, alvo.mod_des)
        roll_def = random.randint(1, 20) + mod_def
        
        logs_turno.append((f"  {self.nome} tenta AGARRAR (Grapple) {alvo.nome}...", COR_STATUS))
        logs_turno.append((f"  Rolagem: {roll_atk} (For) vs {roll_def} (For/Des)", COR_STATUS))
        
        if roll_atk >= roll_def:
            logs_turno.append((f"  SUCESSO! {alvo.nome} está Agarrado!", COR_STATUS))
            alvo.aplicar_status_efeito("Agarrado", 100, logs_turno.append) # Until escaped
            self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': alvo, 'texto': 'GRAPPLED', 'cor': (255, 165, 0)})
        else:
            logs_turno.append((f"  FALHA! {alvo.nome} escapou do agarrao.", COR_STATUS))
            self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': alvo, 'texto': 'ESCAPED', 'cor': (200, 200, 200)})
        return True

    def usar_shove(self, alvo, logs_turno):
        """Empurrar (Shove): Knock Prone. Athletics vs Athletics/Acrobatics"""
        from src.config import COR_STATUS
        if self.acao_realizada: return False
        
        self.acao_realizada = True
        
        # Roll Contest
        roll_atk = random.randint(1, 20) + self.mod_for
        mod_def = max(alvo.mod_for, alvo.mod_des)
        roll_def = random.randint(1, 20) + mod_def
        
        logs_turno.append((f"  {self.nome} tenta DERRUBAR (Shove) {alvo.nome}...", COR_STATUS))
        logs_turno.append((f"  Rolagem: {roll_atk} (For) vs {roll_def} (For/Des)", COR_STATUS))
        
        if roll_atk >= roll_def:
            logs_turno.append((f"  SUCESSO! {alvo.nome} foi derrubado (Caído)!", COR_STATUS))
            alvo.aplicar_status_efeito("Caído", 100, logs_turno.append) # Until stands up
            self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': alvo, 'texto': 'PRONE', 'cor': (255, 165, 0)})
        else:
            logs_turno.append((f"  FALHA! {alvo.nome} se manteve de pé.", COR_STATUS))
        return True

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
        ac_final = self.ac_base
        if self.armadura_equipada:
            ac_final = self.armadura_equipada.bonus_ac
        
        # Passive Perks that don't need context (or we assume standard context if strictly necessary, but better to use calculate_ac_dynamic)
        return ac_final

    def calcular_ac_dinamico(self, tabuleiro, aliados):
        total_ac = self.ac
        
        # 1. Perk: Muralha de Escudos
        # +2 AC se tiver 1+ aliado adjacente
        if self.tem_perk("muralha_escudos") and aliados:
            tem_aliado_perto = any(a for a in aliados if a.esta_vivo and a is not self and calcular_distancia(self, a) <= 1.5)
            if tem_aliado_perto:
                total_ac += 2
        
        # 2. Perk: Mimetismo
        # +4 AC se em Terreno Floresta, Barril, Rocha ou Parede (Cobertura natural)
        if self.tem_perk("mimetismo") and tabuleiro:
            terreno = tabuleiro.get_terrain_em(self.pos_x, self.pos_y)
            if terreno in [TERRENO_FLORESTA, TERRENO_ROCHA, TERRENO_BARRIL]:
                 total_ac += 4
                 
        return total_ac

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

        # 1. Usar Item (Action) - Only if Action not taken
        if not self.acao_realizada:
            # 1.1 Cura
            for item in self.inventario:
                if isinstance(item, HealthPotion) and self.hp_atual / self.hp_max < 0.3:
                    logs_turno.append((f"  {self.nome} usa Poção de Cura!", COR_TEXTO))
                    item.usar(self, logs_turno.append)
                    self.inventario.remove(item)
                    return {'acao': 'usar_item', 'item': item} # Item use counts as Action for now

        # 2. Main Action: Attack
        inimigos_possiveis = []
        for p in inimigos:
            dist = calcular_distancia(self, p)
            if dist <= self.alcance:
                # Check Charmed
                status_charmed = next((e for e in self.status_efeitos if e.nome == "Enfeitiçado"), None)
                if status_charmed:
                    encantador = status_charmed.dados_extra.get("encantador")
                    if encantador and p == encantador:
                         # Cannot attack charmer
                         continue
                inimigos_possiveis.append(p)

        inimigos_em_range = inimigos_possiveis
        
        if not self.acao_realizada:
            if inimigos_em_range:
                # Select target
                # Prioridade: Finalizável > Ameaça > Próximo
                avg_damage = (self.dado_dano[0] * (self.dado_dano[1] + 1) / 2) + self.bonus_dano
                alvos_finalizaveis = [p for p in inimigos_em_range if p.hp_atual <= avg_damage]
                
                if alvos_finalizaveis:
                    alvo = max(alvos_finalizaveis, key=lambda p: p.threat_level)
                    return {'acao': 'atacar', 'alvo': alvo}
                else:
                    alvo = min(inimigos_em_range, key=lambda p: calcular_distancia(self, p))
                    return {'acao': 'atacar', 'alvo': alvo}

        # 3. Movement
        if not self.movimento_realizado:
            # Check Grappled / Restrained (Speed 0)
            if self.tem_status("Agarrado") or self.tem_status("Contido"):
                logs_turno.append((f"  {self.nome} não pode se mover (Agarrado/Contido).", COR_TEXTO))
                return {'acao': 'passar'} # Can still attack, but logic below returns move. Stop here if moving.
                # Actually, if we can attack, we should have already returned 'atacar' above. 
                # This block only runs if we need to move. So we return pass.

            # If we haven't attacked yet (because out of range), move to closest enemy
            if not self.acao_realizada and not inimigos_em_range:
                alvo = min(inimigos, key=lambda p: calcular_distancia(self, p))
                
                # Check Frightened (Can't move closer to source)
                status_assustado = next((e for e in self.status_efeitos if e.nome == "Assustado"), None)
                if status_assustado:
                    fonte_medo = status_assustado.dados_extra.get("fonte")
                    # If target is the source of fear, we cannot move closer.
                    # Or generic: Can't move closer to source.
                    # Simplification: If targeting the source, skip move or flee?
                    if fonte_medo and alvo == fonte_medo:
                         logs_turno.append((f"  {self.nome} está com MEDO de {alvo.nome} e não pode se aproximar!", COR_TEXTO))
                         return {'acao': 'passar'} # Or pick another target? For now, pass.

                # Only return move if we actually are far
                if calcular_distancia(self, alvo) > self.alcance:
                     return {'acao': 'mover', 'alvo': alvo}
            
            # If we already attacked, maybe move away (Kiting)? 
            # Ranged Kiting logic:
            if self.alcance > 1 and inimigos_em_range and self.acao_realizada:
                 # Try to move away from closest enemy if adjacent
                 closest = min(inimigos_em_range, key=lambda p: calcular_distancia(self, p))
                 if calcular_distancia(self, closest) <= 1:
                     # Check Grappled again just in case Kiting relies on move
                     if self.tem_status("Agarrado") or self.tem_status("Contido"):
                         return {'acao': 'passar'}
                     return {'acao': 'fugir'} # Using Standard Move to run away

        return {'acao': 'passar'}
        
        return {'acao': 'passar'}

    def tem_status(self, nome):
        return any(e.nome == nome for e in self.status_efeitos)

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print, tipo_dano_override=None, habilidade=None, vantagem=False, desvantagem=False, bonus_dano_extra=0):
        from src.config import COR_TEXTO, COR_CRITICO
        if not self.esta_vivo: return
        
        self.eventos_animacao.append({'tipo': 'ataque', 'atacante': self, 'alvo': alvo, 'habilidade': habilidade})
        if self.sound_player: self.sound_player('attack')

        msg_modificadores = []
        if vantagem: msg_modificadores.append("Bin (Hab.)")
        if desvantagem: msg_modificadores.append("Mal (Hab.)")

        # --- D&D 5e CONDITIONS (Refactored) ---
        from src.condicoes import verificar_condicoes_ataque, verificar_critico_automatico
        distancia = calcular_distancia(self, alvo)
        
        vantagem, desvantagem, mods_condicoes = verificar_condicoes_ataque(self, alvo, distancia, vantagem, desvantagem)
        msg_modificadores.extend(mods_condicoes)

        # 6. Flanking (Grants Advantage)
        if self.alcance == 1 and time_aliado and not desvantagem: # Flanking is optional rule, kept here.
            for aliado in time_aliado:
                if aliado is not self and aliado.esta_vivo and aliado.alcance == 1 and calcular_distancia(aliado, alvo) <= 1:
                     dx_self = self.pos_x - alvo.pos_x
                     dy_self = self.pos_y - alvo.pos_y
                     dx_ally = aliado.pos_x - alvo.pos_x
                     dy_ally = aliado.pos_y - alvo.pos_y
                     
                     if dx_self == -dx_ally and dy_self == -dy_ally:
                         vantagem = True
                         msg_modificadores.append(f"Flanqueando ({aliado.nome})")
                         break

        # 7. Elevation (Higher Ground grants Advantage)
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
        
        # Execute Attack Roll
        rolagem_ataque, msg_dado = rolar_d20(vantagem=vantagem, desvantagem=desvantagem)
        
        total_ataque = rolagem_ataque + self.bonus_ataque
        
        mod_str = f" ({', '.join(msg_modificadores)})" if msg_modificadores else ""
        log_ataque = f"  Ataque: {rolagem_ataque}{msg_dado} + {self.bonus_ataque} = {total_ataque}{mod_str} vs AC {ac_alvo}."
        
        # Auto Crit for Paralyzed/Unconscious within 5ft (Refactored)
        is_critico, msg_critico = verificar_critico_automatico(self, alvo, distancia, rolagem_ataque, total_ataque, ac_alvo)
        if msg_critico:
             msg_modificadores.append(msg_critico)

        if is_critico: # Critical Hit
            logger((f"{log_ataque} Acerto CRÍTICO!", COR_CRITICO))
            if self.sound_player: self.sound_player('critical_hit')
            self.causar_dano(alvo, tabuleiro, logger, is_critico=True, tipo_dano_override=tipo_dano_override, bonus_dano_extra=bonus_dano_extra)
        elif total_ataque >= ac_alvo:
            logger((f"{log_ataque} Acerta!", COR_TEXTO))
            self.causar_dano(alvo, tabuleiro, logger, tipo_dano_override=tipo_dano_override, bonus_dano_extra=bonus_dano_extra)
        else:
            logger((f"{log_ataque} Erra (AC do alvo é {ac_alvo}).", COR_TEXTO))
            if self.sound_player: self.sound_player('miss')
            self.eventos_animacao.append({'tipo': 'dano', 'alvo': alvo, 'dano': 'ERROU!'})

    def causar_dano(self, alvo, tabuleiro, logger=print, is_critico=False, tipo_dano_override=None, bonus_dano_extra=0):
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

        dano_total = max(1, dano_rolado + self.bonus_dano + bonus_dano_extra)
        msg_extra = f" + {bonus_dano_extra} (extra)" if bonus_dano_extra > 0 else ""
        logger((f"  Rolagem de Dano: {dano_rolado} ({num_rolagens}d{dado_dano[1]}) + {self.bonus_dano} (bônus){msg_extra} = {dano_total} de dano {tipo_dano}.", COR_DANO))
        
        alvo.receber_dano(dano_total, self, tabuleiro, logger, tipo_dano=tipo_dano)
        
        if self.sound_player: self.sound_player('hit')

    def receber_dano(self, quantidade, atacante=None, tabuleiro=None, logger=print, tipo_dano=DANO_FISICO):
        from src.config import COR_DANO, COR_TEXTO, COR_CURA
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
                     
                    # 3. Perk: Última Linha (Last Stand)
                    if self.tem_perk("ultima_linha") and not getattr(self, "_ultima_linha_usada", False):
                        self.hp_atual = 1
                        self.estado = "NORMAL" # Resiste!
                        self._ultima_linha_usada = True
                        logger((f"  PERK ATIVADO: {self.nome} usa ÚLTIMA LINHA e recusa a cair! (1 HP)", (255, 215, 0)))
                        self.eventos_animacao.append({'tipo': 'floating_text', 'personagem': self, 'texto': 'LAST STAND!', 'cor': (255, 215, 0)})
                        return dano_final, msg_eficacia # Retorna, não cai inconsciente
                     
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

            # Lógica de Recompensa de Kill (Perks do Atacante)
            if self.estado in ["MORTO", "INCONSCIENTE"] and atacante:
                 if atacante.tem_perk("sede_sangue"):
                     cura = 5 + atacante.nivel
                     logger((f"  [Sede de Sangue] {atacante.nome} se revigora com a morte de {self.nome}!", COR_CURA))
                     atacante.receber_cura(cura, logger)
                 
                 if atacante.tem_perk("ressonancia_arcana") and hasattr(atacante, 'mana_atual'):
                     rec_mana = 5
                     atacante.mana_atual = min(atacante.mana_max, atacante.mana_atual + rec_mana)
                     logger((f"  [Ressonância Arcana] {atacante.nome} absorve energia! (+{rec_mana} Mana)", (150, 0, 200)))
                     atacante.eventos_animacao.append({'tipo': 'floating_text', 'personagem': atacante, 'texto': f'+{rec_mana} MP', 'cor': (150, 0, 200)})
            
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
            },
            "perks": self.perks_adquiridos
        }

    def from_dict(self, data):
        self.perks_adquiridos = data.get("perks", [])
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

