import pygame
import sys
import math
from collections import deque
from src.config import *
from src.perks import PERKS
from .motor_combate import MotorCombate
from .map_generator import MapGenerator
from .campanha import CampaignManager
from .cutscene import CutsceneManager
from .personagens import *
from .states.event_handler import EventHandler
from .states.game_setup import GameSetup
from .states.renderer import GameRenderer
from .ui.menu import setup_menu_ui, setup_menu_principal_ui
from .ui.desenho import (
    desenhar_menu_principal, desenhar_setup_batalha, desenhar_cenario,
    desenhar_personagens, desenhar_barra_iniciativa, desenhar_comandos,
    desenhar_log, desenhar_info_personagem, desenhar_projeteis_e_efeitos,
    desenhar_itens_no_chao, desenhar_mapa_mundo, desenhar_floating_texts,
    desenhar_dialogo, desenhar_tela_fim, desenhar_inventario, desenhar_pre_visualizacao_ataque,
    desenhar_tela_level_up, desenhar_tela_salvando, desenhar_tela_carregando, desenhar_editor,
    desenhar_alcance_movimento, desenhar_alcance_habilidade, desenhar_interface_retro
)
from .config import (
    LARGURA_TELA, ALTURA_TELA, COR_FUNDO, COR_TEXTO, COR_GRID, COR_CRITICO, COR_XP, COR_DANO,
    TAMANHO_CELULA, ALTURA_BARRA_INICIATIVA, LARGURA_TABULEIRO, LARGURA_LOG,
    ESTADO_JOGO_SETUP, ESTADO_JOGO_COMBATE, ESTADO_JOGO_FIM,
    ESTADO_JOGO_MENU_PRINCIPAL, ESTADO_JOGO_MAPA_MUNDO, ESTADO_JOGO_EDITOR, ESTADO_JOGO_CUTSCENE, ESTADO_JOGO_NARRATIVA,
    ESTADO_JOGO_DEV, ESTADO_JOGO_LEVEL_UP, ESTADO_JOGO_CERCO,
    TIME_A, TIME_B, CORES_TERRENO,
    TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL, TERRENO_FOGO, TERRENO_AGUA,
    IMAGE_PERSONAGENS, IMAGE_TERRENOS, PAINEL_MODO_LOG, PAINEL_MODO_INFO,
    COR_BOTAO_DESABILITADO
)
from .sistema_dialogo import Dialogo
from .salvar_carregar import salvar_jogo, carregar_jogo, salvar_mapa_json, carregar_mapa_json
from .utils import calcular_distancia, resource_path
from .ui.componentes import Botao, FloatingText, Checkbox, Tab
from .personagens.rei_goblin import ReiGoblin
from .personagens.lorde_lich import LordeLich
from .personagens.dragao_anciao import DragaoAnciao
from .personagens.minions import Esqueleto, Goblin, Kobold
from .states.cerco_state import CercoState

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
        pygame.display.set_caption("Cerco contra Isectum")
        self.fonte_personagem = pygame.font.Font(None, 18)
        self.fonte_log = pygame.font.Font(None, 20)
        self.fonte_info = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 28)
        self.fonte_titulo = pygame.font.Font(None, 48)
        self.clock = pygame.time.Clock()

        self.sounds = GameSetup.carregar_sons()
        self.imagens = GameSetup.carregar_imagens()
        self.animacoes_sprites = GameSetup.carregar_animacoes()
        self.estado_animacao_personagem = {}
        
        self.event_handler = EventHandler(self)
        self.renderer = GameRenderer(self)
        
        self.rodando = True
        self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
        self.botoes_menu_principal = setup_menu_principal_ui()
        self.estado_combate = None
        self.motor = None
        self.campaign_manager = CampaignManager()
        self.cutscene_manager = CutsceneManager(self.fim_cutscene)
        self.unidade_selecionada = None
        self.habilidade_selecionada = None # Estado para guardar qual habilidade está selecionada para uso
        self.skill_menu_open = False # [NEW] Controls visibility of skill buttons vs main actions
        self.actions_menu_open = False # [NEW] Controls visibility of generic actions menu
        self.acao_action_selecionada = None # [NEW] Stores selected generic action (Help, Grapple, Shove)
        self.personagem_info_painel = None
        self.checkbox_campanha = None # Will be initialized in setup_ui
        self.painel_modo = PAINEL_MODO_LOG
        self.fila_animacoes = deque()
        self.animacao_atual = None
        self.tempo_proxima_acao_auto = 0
        self.log_combate = deque(maxlen=35)
        self.log_combate.append(("Bem-vindo ao Simulador de Batalha!", COR_TEXTO))

        self.botoes_combate = {}
        self.config_times = {}
        self.config_chefe = {}
        self.botoes_ui = {}
        self.checkbox_terreno = None
        self.checkbox_auto = None
        self.checkbox_chefe = None
        self.checkbox_autoplay = None
        self.checkbox_limitadores = None
        self.bosses = []
        self.selected_boss_index = 0
        self.hovered_enemy = None
        self.volume_sfx = 0.5

        self.feedback_invalido_timer = 0
        self.visibilidade_map = [[2] * 20 for _ in range(20)]
        self.personagem_level_up = None
        self.save_filename = ""
        self.save_files = []
        self.floating_texts = []
        self.editor_mapa = [[TERRENO_NORMAL for _ in range(20)] for _ in range(20)]
        self.editor_terreno_selecionado = TERRENO_NORMAL
        self.dialogo = Dialogo()
        self.game_over_processed = False
        self.angulo_rotacao = 0.0
        self.target_angulo_rotacao = 0.0
        self.key_q_pressed = False
        self.key_e_pressed = False

        GameSetup.setup_ui(self)
        self.tocar_musica('menu')
        
        self.cerco_state = None
        self.cerco_setup_state = None
        
        # Optimization Trackers
        self.last_char_id = None
        self.last_menu_open = False

    def tocar_musica(self, tipo):
        GameSetup.tocar_musica(tipo)

    def play_sound(self, nome, volume=1.0):
        GameSetup.play_sound(self.sounds, nome, volume)

    def iniciar_capitulo_dev(self, idx):
        """Método auxiliar para iniciar um capítulo específico via Menu Dev"""
        if idx < 0 or idx >= len(self.campaign_manager.campaign_data):
            print(f"Fase inválida: {idx}")
            return
            
        self.campaign_manager.nivel_atual = idx
        self.iniciar_proxima_batalha_campanha()

    def iniciar_proxima_batalha_campanha(self):
        self.tocar_musica('batalha')
        battle_config = self.campaign_manager.get_battle_config()
        if not battle_config:
            self.log_combate.append(("CAMPANHA CONCLUÍDA!", COR_CRITICO))
            self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            return

        self.estado_jogo = ESTADO_JOGO_COMBATE
        
        # Configuração do Time A (mantém o mesmo do menu)
        time_a_config = [self.config_times[TIME_A][c] for c, _ in self.config_times['classes']]
        
        # Configuração do Time B (vem da campanha)
        time_b_classes = [Goblin, Esqueleto, Kobold, ReiGoblin, LordeLich, DragaoAnciao]
        time_b_map = {cls: 0 for cls in time_b_classes}
        for inimigo_class, count in battle_config["inimigos"]:
            time_b_map[inimigo_class] = count
        time_b_config = [time_b_map[cls] for cls in time_b_classes]

        args = time_a_config + time_b_config

        mapa_arquivo = battle_config.get("mapa")
        # Se tiver mapa definido, não gera terreno aleatório
        gerar_terreno = True if not mapa_arquivo else False

        try:
            self.motor = MotorCombate(args, 
                                      sound_player=self.play_sound, 
                                      gerar_terreno=gerar_terreno,
                                      custom_mapa_arquivo=mapa_arquivo) 
            
            # Carrega o progresso dos personagens do jogador
            self.campaign_manager.carregar_progresso_personagens(self.motor.time_a)

            # God Mode Check
            if self.god_mode:
                for p in self.motor.personagens:
                     if p.time == TIME_A:
                         p.invulneravel = True
                         
            for p in self.motor.combatentes: p.dano_timer = 0
            self.game_over_processed = False
            self.log_combate.clear()
            self.log_combate.append((f"--- Campanha: Nível {self.campaign_manager.nivel_atual + 1} ---", COR_CRITICO))
            self.log_combate.append((battle_config["mensagem_inicio"], COR_TEXTO))

            # Iniciar Diálogo da Campanha
            if "dialogo_inicio" in battle_config:
                self.dialogo.iniciar_dialogo(battle_config["dialogo_inicio"])

        except ValueError as e:
            print(f"Erro ao iniciar batalha da campanha: {e}")
            self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL

    def iniciar_batalha_campanha_custom(self):
        self.tocar_musica('batalha')
        battle_config = self.campaign_manager.get_battle_config()
        if not battle_config:
            return

        self.estado_jogo = ESTADO_JOGO_COMBATE
        
        # Create Protagonists explicitly
        time_a_instances = [
            Novak("Novak", "A", sound_player=self.play_sound),
            Koema("Koema", "A", sound_player=self.play_sound),
            Rilem("Rilem", "A", sound_player=self.play_sound),
            Yukito("Yukito", "A", sound_player=self.play_sound)
        ]
        
        # Time B (Sienna) comes from config, but let's handle specifically to ensure boss flag?
        # Actually MotorCombate handles list of classes or instances?
        # Standard MotorCombate takes counts. We need to pass instances or modify MotorCombate to accept instances in args.
        # Let's check MotorCombate.
        pass # Placeholder for thought
        
        # MotorCombate constructor:
        # def __init__(self, args_times, ...)
        # It expects args_times to be a list of COUNTS corresponding to classes.
        # This is bad for custom instances.
        
        # Force Custom Instances requires a change in MotorCombate or a Hack.
        # Let's Modify MotorCombate to accept `custom_time_a` and `custom_time_b` kwargs.
        
        try:
            self.motor = MotorCombate(
                [],  # Empty args
                gerar_terreno=False, 
                mapa_custom=None, # Will load from file
                sound_player=self.play_sound,
                custom_time_a=time_a_instances,
                custom_mapa_arquivo=battle_config.get("mapa")
            )
            
            # Setup Enemies from Config
            enemies_config = battle_config["inimigos"]
            # enemies_config is [(Class, count), ...]
            # We want to instantiate them.
            time_b_instances = []
            for cls, count in enemies_config:
                for i in range(count):
                    nome = f"{cls.__name__}" if count == 1 else f"{cls.__name__}_{i+1}"
                    # Check if it's Sienna to pass stats? Sienna class handles itself default.
                    inst = cls(nome, "B", sound_player=self.play_sound)
                    time_b_instances.append(inst)
            
            self.motor.set_time_b_custom(time_b_instances) # Helper we will add
            self.motor.start_battle_custom() # Helper to init positions/initiative
            
            self.game_over_processed = False
            self.log_combate.clear()
            self.log_combate.append((f"--- O Confronto Final ---", COR_CRITICO))
            self.log_combate.append((battle_config["mensagem_inicio"], COR_TEXTO))

            # Iniciar Diálogo da Campanha
            if "dialogo_inicio" in battle_config:
                self.dialogo.iniciar_dialogo(battle_config["dialogo_inicio"])

        except ValueError as e:
            print(f"Erro ao iniciar batalha custom: {e}")
            self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL

    def run(self):
        while self.rodando:
            mouse_pos = pygame.mouse.get_pos()
            tick = pygame.time.get_ticks()
            agora = pygame.time.get_ticks()
            
            personagem_ativo = self.motor.get_personagem_ativo() if self.motor and not self.motor.vencedor else None

            self.handle_events(mouse_pos, personagem_ativo)
            if not self.rodando: break

            self.update_game_logic(agora, personagem_ativo)
            
            self.draw_elements(tick, mouse_pos, personagem_ativo)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


    def verificar_opcoes_level_up(self):
        # Limpa os botões de level up existentes
        self.botoes_level_up.clear()

        if not self.personagem_level_up:
            return

        if self.modo_level_up == 'stat':
            # Botões de atributos
            self.botoes_level_up = {
                'forca': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 60, 200, 40, "+1 Força", self.fonte_menu),
                'destreza': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 10, 200, 40, "+1 Destreza", self.fonte_menu),
                'constituicao': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 40, 200, 40, "+1 Constituição", self.fonte_menu),
                'inteligencia': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 90, 200, 40, "+1 Inteligência", self.fonte_menu),
                'sabedoria': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 140, 200, 40, "+1 Sabedoria", self.fonte_menu),
                'carisma': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 190, 200, 40, "+1 Carisma", self.fonte_menu),
            }
        elif self.modo_level_up == 'perk':
            # Botões de perks
            perks_disponiveis = self.personagem_level_up.get_perks_disponiveis()
            
            # Posições para os botões de perk
            y_start = ALTURA_TELA // 2 - (len(perks_disponiveis) * 50) // 2
            for i, perk_id in enumerate(perks_disponiveis):
                perk_info = PERKS.get(perk_id, {"nome": "Perk Desconhecido"})
                self.botoes_level_up[f"perk_{perk_id}"] = Botao(
                    LARGURA_TELA // 2 - 150, y_start + i * 60, 300, 50,
                    perk_info["nome"], self.fonte_menu
                )


    def handle_events(self, mouse_pos, personagem_ativo):
        self.event_handler.handle_events(mouse_pos, personagem_ativo)

    def update_game_logic(self, agora, personagem_ativo):
        # Keyboard rotation control (Q/E) with smooth 90-degree interpolation
        keys = pygame.key.get_pressed()
        
        # Debounce Q key (Rotate Counter-Clockwise 90 degrees)
        if keys[pygame.K_q]:
            if not self.key_q_pressed:
                self.target_angulo_rotacao -= math.pi / 2
                self.key_q_pressed = True
        else:
            self.key_q_pressed = False
            
        # Debounce E key (Rotate Clockwise 90 degrees)
        if keys[pygame.K_e]:
            if not self.key_e_pressed:
                self.target_angulo_rotacao += math.pi / 2
                self.key_e_pressed = True
        else:
            self.key_e_pressed = False
            
        # Keep target_angulo_rotacao within range to avoid floating overflow
        self.target_angulo_rotacao = self.target_angulo_rotacao % (2 * math.pi)
        
        # Smoothly interpolate angulo_rotacao towards target_angulo_rotacao
        diff = (self.target_angulo_rotacao - self.angulo_rotacao)
        # Normalize diff to range [-pi, pi] to take shortest path
        diff = (diff + math.pi) % (2 * math.pi) - math.pi
        
        if abs(diff) > 0.01:
            step = 0.08  # speed of rotation animation
            if abs(diff) < step:
                self.angulo_rotacao = self.target_angulo_rotacao
            else:
                self.angulo_rotacao = (self.angulo_rotacao + (step if diff > 0 else -step)) % (2 * math.pi)
        else:
            self.angulo_rotacao = self.target_angulo_rotacao

        if self.motor:
            self.motor.angulo_rotacao = self.angulo_rotacao

        if self.dialogo.ativo:
            self.dialogo.atualizar()
            return # Pausa o jogo atrás do diálogo

        if self.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
            self.campaign_manager.atualizar_movimento()
            self.campaign_manager.update(agora)
            if self.campaign_manager.evento_mapa:
                evento = self.campaign_manager.evento_mapa.popleft()
                if evento.tipo == 'batalha':
                    self.iniciar_proxima_batalha_campanha()
                elif evento.tipo == 'cutscene':
                    self.cutscene_manager.iniciar_cutscene(evento.cutscene_id)
                    self.estado_jogo = ESTADO_JOGO_CUTSCENE
                elif evento.tipo == 'dialogo':
                    self.dialogo.iniciar_dialogo(evento.dialogo_data)
                    self.estado_jogo = ESTADO_JOGO_NARRATIVA
                elif evento.tipo == 'level_up':
                    self.personagem_level_up = evento.personagem
                    self.previous_state = self.estado_jogo
                    self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                    self.modo_level_up = 'stat'
                    self.play_sound('level_up')
                    self.verificar_opcoes_level_up()

        if self.estado_jogo == ESTADO_JOGO_CUTSCENE:
            self.cutscene_manager.update()

        if self.estado_jogo == ESTADO_JOGO_COMBATE:
            # Check for Battle End
            if self.motor and self.motor.vencedor and not self.game_over_processed:
                self.game_over_processed = True
                
                if self.motor.vencedor == "Time A":
                    # Check if it was Sienna Boss Fight
                    # Heuristic: Check if Time B had Sienna
                    boss_fight = any(p.classe_nome == "Sienna" for p in self.motor.time_b)
                    
                    if boss_fight or self.checkbox_campanha.checked: # Assuming boss test sets this too or we just detect boss
                         if boss_fight:
                             self.iniciar_sequencia_final()
                             return

                    # Regular Campaign Logic
                    if self.checkbox_campanha.checked:
                        self.campaign_manager.avancar_nivel()
                        self.campaign_manager.salvar_progresso_personagens(self.motor.time_a)
                        if self.campaign_manager.salvar_campanha():
                            self.log_combate.append(("Progresso da Campanha Salvo!", COR_CRITICO))
                        else:
                            self.log_combate.append(("Erro ao salvar campanha!", COR_DANO))

            # Animation Handling
            if self.animacao_atual:
                if 'inicio' not in self.animacao_atual:
                    self.animacao_atual['inicio'] = agora
                    self.animacao_atual['duracao'] = 500
                    if self.animacao_atual['tipo'] == 'ataque': self.play_sound('attack')
                    elif self.animacao_atual['tipo'] == 'dano': self.play_sound('hit')

                if agora - self.animacao_atual['inicio'] > self.animacao_atual['duracao']:
                    if self.animacao_atual['tipo'] == 'movimento':
                        p = self.animacao_atual['personagem']
                        p_id = id(p)
                        if p_id in self.estado_animacao_personagem:
                            self.estado_animacao_personagem[p_id]["andando"] = False
                            self.estado_animacao_personagem[p_id]["quadro"] = 0
                    self.animacao_atual = None
                else:
                    self.animacao_atual['progresso'] = (agora - self.animacao_atual['inicio']) / self.animacao_atual['duracao']

                if self.animacao_atual and self.animacao_atual['tipo'] == 'movimento':
                    p = self.animacao_atual['personagem']
                    p_id = id(p)
                    classe_nome = p.__class__.__name__
                    if classe_nome in self.animacoes_sprites:
                        if p_id not in self.estado_animacao_personagem:
                            self.estado_animacao_personagem[p_id] = {"direcao": 0, "quadro": 0, "timer": 0, "andando": False}
                        estado = self.estado_animacao_personagem[p_id]
                        estado["andando"] = True

                        dx = self.animacao_atual['end_pos'][0] - self.animacao_atual['start_pos'][0]
                        dy = self.animacao_atual['end_pos'][1] - self.animacao_atual['start_pos'][1]
                        if abs(dx) > abs(dy):
                            estado["direcao"] = 1 if dx < 0 else 2
                        else:
                            estado["direcao"] = 0 if dy > 0 else 3

                        estado["timer"] += 1
                        if estado["timer"] >= 6:
                            estado["timer"] = 0
                            estado["quadro"] = (estado["quadro"] % 3) + 1
            
            elif self.fila_animacoes:
                self.animacao_atual = self.fila_animacoes.popleft()
                self.animacao_atual['inicio'] = agora
                self.animacao_atual['duracao'] = 500
                self.animacao_atual['progresso'] = 0.0
                
                if self.animacao_atual['tipo'] == 'ataque': self.play_sound('attack')
                elif self.animacao_atual['tipo'] == 'dano': self.play_sound('hit')
                elif self.animacao_atual['tipo'] == 'dialogo':
                     self.dialogo.iniciar_dialogo(self.animacao_atual['mensagens'])
                     self.animacao_atual = None # Ends animation step immediately
                elif self.animacao_atual['tipo'] == 'escolha_atributo':
                     self.personagem_level_up = self.animacao_atual['personagem']
                     self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                     self.verificar_opcoes_level_up(self.personagem_level_up)
                     self.animacao_atual = None

            
            # AI Turn Logic
            elif self.motor and not self.motor.vencedor:
                if personagem_ativo and (personagem_ativo.time == TIME_B or (self.checkbox_autoplay.checked and personagem_ativo.time == TIME_A)):
                    if self.tempo_proxima_acao_auto == 0:
                        self.tempo_proxima_acao_auto = agora + 1000 # Wait 1 second before acting
                    
                    if agora >= self.tempo_proxima_acao_auto:
                        resultado = self.motor.proximo_passo()
                        self.log_combate.extend(resultado['logs'])
                        self.fila_animacoes.extend(resultado['eventos'])
                        self.tempo_proxima_acao_auto = 0 # Reset
                        self.tempo_proxima_acao_auto = 0 # Reset
                        self.tempo_proxima_acao_auto = 0 # Reset
                        self.atualizar_visibilidade()
            
            # Update Ability Buttons (Optimized)
            current_char_id = id(personagem_ativo) if personagem_ativo else None
            state_changed = (current_char_id != self.last_char_id) or (self.skill_menu_open != self.last_menu_open) or (self.actions_menu_open != self.last_menu_open) # [MODIFIED]
            
            if state_changed:
                 self.atualizar_botoes_habilidade(personagem_ativo)
                 self.atualizar_botoes_acoes(personagem_ativo) # [NEW]
                 self.last_char_id = current_char_id
                 self.last_menu_open = self.skill_menu_open or self.actions_menu_open # [MODIFIED]
            
            # Fallback: if not player turn, ensure menu is closed (handled in atualizar_botoes_habilidade, but we must call it if turn changed)
            if personagem_ativo and personagem_ativo.time != TIME_A and (self.skill_menu_open or self.actions_menu_open):
                 self.skill_menu_open = False
                 self.actions_menu_open = False
                 self.atualizar_botoes_habilidade(personagem_ativo)
                 self.atualizar_botoes_acoes(personagem_ativo)
                 self.last_menu_open = False

    def atualizar_botoes_acoes(self, personagem_ativo):
        """Atualiza botões de ações genéricas (Dash, Dodge, etc)"""
        # Remove old action buttons
        keys_to_remove = [k for k in self.botoes_combate if k.startswith('acao_') or k == 'voltar_acoes']
        for k in keys_to_remove:
            del self.botoes_combate[k]
            
        if not personagem_ativo or personagem_ativo.time != TIME_A:
            self.actions_menu_open = False
            return

        if self.actions_menu_open:
            # Layout similar to skills
            btn_width = 150
            btn_height = 45
            margin_x = 10
            margin_y = 10
            start_x = 30
            start_y = 620
            
            # Add Back Button
            self.botoes_combate['voltar_acoes'] = Botao(start_x + 3*(btn_width + margin_x), 650, 80, 45, "Voltar", self.fonte_menu)

            actions = [
                ('acao_dash', 'Dash (Mv x2)'),
                ('acao_disengage', 'Disengage'),
                ('acao_dodge', 'Dodge (Def)'),
                ('acao_help', 'Help (Adv)'),
                ('acao_grapple', 'Grapple'),
                ('acao_shove', 'Shove')
            ]
            
            for i, (key, label) in enumerate(actions):
                col = i % 3
                row = i // 3
                
                x = start_x + col * (btn_width + margin_x)
                y = start_y + row * (btn_height + margin_y)
                
                self.botoes_combate[key] = Botao(x, y, btn_width, btn_height, label, self.fonte_info)

    def atualizar_botoes_habilidade(self, personagem_ativo):
        # Remove old ability buttons
        keys_to_remove = [k for k in self.botoes_combate if k.startswith('habilidade_') or k == 'voltar_skills']
        for k in keys_to_remove:
            del self.botoes_combate[k]
            
        if not personagem_ativo or personagem_ativo.time != TIME_A:
            self.skill_menu_open = False
            return

        if self.skill_menu_open:
            # Layout: Display skills in 2 columns within the Action Bar area
            
            btn_width = 180
            btn_height = 50
            margin_x = 20
            margin_y = 10
            start_x = 30
            start_y = 620
            
            # LIGHTWEIGHT FIX: Always add Back button first
            self.botoes_combate['voltar_skills'] = Botao(start_x + 2*(btn_width + margin_x), 650, 100, 50, "Voltar", self.fonte_menu)

            if hasattr(personagem_ativo, 'habilidades') and personagem_ativo.habilidades:
                i = 0
                for key, dados in personagem_ativo.habilidades.items():
                    col = i % 2
                    row = i // 2
                    
                    x = start_x + col * (btn_width + margin_x)
                    y = start_y + row * (btn_height + margin_y)
                    
                    # Check bounds
                    if row > 2: break # Limit to 6 skills for now
                    
                    btn = Botao(x, y, btn_width, btn_height, dados['nome'], self.fonte_info)
                    self.botoes_combate[f'habilidade_{key}'] = btn
                    i += 1
        
        if self.motor and self.motor.vencedor and not self.game_over_processed:
            self.game_over_processed = True
            
            if self.motor.vencedor == "Time A":
                # Check for Boss Kill (Sienna)
                # We assume if we played specific campaign or boss test, this is triggered.
                # Let's check update_game_logic instead for cleaner flow.
                pass
            
            if self.motor.vencedor == "Time B" and self.checkbox_campanha.checked:
                 self.log_combate.append(("A campanha falhou...", COR_DANO))

    def atualizar_visibilidade(self):
        if self.motor:
            self.motor.atualizar_visibilidade()

    def screen_to_grid(self, mx, my):
        if self.motor:
            elev_grid = self.motor.tabuleiro.elevation_grid
            w = self.motor.tabuleiro.largura
            h = self.motor.tabuleiro.altura
        else:
            h = len(self.editor_mapa) if self.editor_mapa else 20
            w = len(self.editor_mapa[0]) if (self.editor_mapa and h > 0) else 20
            elev_grid = [[0 for _ in range(w)] for _ in range(h)]
            
        tile_w = 26
        tile_h = 13
        elev_scale = 8
        offset_x = 300
        offset_y = 200 + ALTURA_BARRA_INICIATIVA
        theta = self.angulo_rotacao
        
        cells = []
        for y in range(h):
            for x in range(w):
                el = elev_grid[y][x]
                rx = x - 9.5
                ry = y - 9.5
                rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
                rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
                cx = (rot_x - rot_y) * (tile_w // 2) + offset_x
                cy = (rot_x + rot_y) * (tile_h // 2) - el * elev_scale + offset_y
                proj_y = (rot_x + rot_y) * (tile_h // 2)
                cells.append((proj_y, x, y, cx, cy))
                
        # Sort by screen Y descending to check front cells first
        cells.sort(key=lambda item: item[0], reverse=True)
        
        for _, x, y, cx, cy in cells:
            if (abs(mx - cx) * 2 / tile_w) + (abs(my - cy) * 2 / tile_h) <= 1.0:
                return x, y
        return None

    def draw_elements(self, tick, mouse_pos, personagem_ativo=None):
        self.renderer.draw_elements(tick, mouse_pos, personagem_ativo)

    def iniciar_sequencia_final(self):
        # 1. Start "History" Cutscene
        slides_history = [
            {"imagem": "world", "texto": "A batalha terminou. O silêncio retornou ao vazio.", "duracao": 180},
            {"imagem": "destruction", "texto": "A Fênix, outrora símbolo de renascimento, agora repousa em cinzas.", "duracao": 180},
            {"imagem": "heroes", "texto": "Mas a vitória teve seu preço. E o destino de Ornallus ainda é incerto.", "duracao": 200},
            {"imagem": "gathering", "texto": "FINAL DE KAPITULO 1", "duracao": 240} # Title Card
        ]
        
        self.estado_jogo = ESTADO_JOGO_CUTSCENE
        self.cutscene_manager.iniciar(slides=slides_history, callback_fim=self.iniciar_cena_ornallus)

    def iniciar_cena_ornallus(self):
        # 2. Start Narrative Scene
        self.estado_jogo = ESTADO_JOGO_NARRATIVA
        
        # Setup Dialogue
        dialogo_ornallus = [
            ("Mestre Kayron", "Vocês retornaram... Eu senti a perturbação no éter.", "kayron"),
            ("Koema", "Ela se transformou, Mestre. O poder dela era... instável.", "koema"),
            ("Eryn", "Instável? Ou corrompido? As leituras que tivemos aqui foram caóticas.", "eryn"),
            ("Novak", "Não importa agora. Ela caiu. Mas disse algo sobre o 'Vazio' antes do fim.", "novak"),
            ("Mestre Kayron", "O Vazio... Se ela tocou o Vazio, então isso é apenas o começo.", "kayron"),
            ("Rilem", "Ótimo. Mais problemas. Eu preciso de um aumento.", "rilem"),
            ("Yukito", "A luz nos guiará, não importa a escuridão.", "yukito"),
            ("Mestre Kayron", "Descansem agora. Amanhã, discutiremos o que isso significa para Ornallus.", "kayron")
        ]
        
        self.dialogo.iniciar_dialogo(dialogo_ornallus)

    def fim_cutscene(self):
        self.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
        self.tocar_musica('menu') # Ou outra música de mapa

    def verificar_opcoes_level_up(self, personagem=None):
        if personagem:
            self.personagem_level_up = personagem
            
        if not self.personagem_level_up:
             return

        # Limpa os botões de level up existentes
        self.botoes_level_up.clear()
        
        # 1. Modo Stat (Default)
        if self.modo_level_up == 'stat':
            self.botoes_level_up = {
                'forca': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 60, 200, 40, "+1 Força", self.fonte_menu),
                'destreza': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 10, 200, 40, "+1 Destreza", self.fonte_menu),
                'constituicao': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 40, 200, 40, "+1 Constituição", self.fonte_menu),
                'inteligencia': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 90, 200, 40, "+1 Inteligência", self.fonte_menu),
                'sabedoria': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 140, 200, 40, "+1 Sabedoria", self.fonte_menu),
                'carisma': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 190, 200, 40, "+1 Carisma", self.fonte_menu),
            }
            
        # 2. Modo Perk (Check availability)
        # 2. Modo Perk (Check availability)
        elif self.modo_level_up == 'perk':
            classe = self.personagem_level_up.classe_nome
            
            if classe in PERKS:
                # Dimensões da Grade
                # Centraliza horizontalmente baseado no maior col? Por enquanto fixo.
                # Considerando 2 colunas x 3 linhas aprox.
                start_x = LARGURA_TELA // 2 - 150
                start_y = ALTURA_TELA // 2 - 150
                cell_w = 220
                cell_h = 100

                for perk in PERKS[classe]:
                    # Calcula posição baseada na grade (pos[0]=col, pos[1]=row)
                    px, py = perk.get('pos', (0, 0))
                    
                    x = start_x + (px * cell_w)
                    y = start_y + (py * cell_h)
                    
                    # Define estado visual (apenas texto aqui, cor desenhada depois)
                    pode = self.personagem_level_up.pode_desbloquear_perk(perk)
                    tem = self.personagem_level_up.tem_perk(perk['id'])
                    
                    texto = f"{perk['nome']}"
                    
                    # Cria botão
                    btn_id = f"perk_{perk['id']}"
                    
                    # Adiciona botao
                    self.botoes_level_up[btn_id] = Botao(x, y, 200, 60, texto, self.fonte_menu)
            
            # Botão de Concluir (caso não queira pegar nada ou só visualizar)
            self.botoes_level_up['concluir'] = Botao(LARGURA_TELA - 160, ALTURA_TELA - 80, 140, 50, "Concluir", self.fonte_menu)


