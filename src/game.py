import pygame
import sys
from collections import deque
from .config import *
from .motor_combate import MotorCombate
from .personagens import *
from .ui.menu import setup_menu_ui, setup_menu_principal_ui
from .ui.desenho import (
    desenhar_barra_iniciativa, desenhar_cenario, desenhar_itens_no_chao,
    desenhar_personagens, desenhar_pre_visualizacao_ataque,
    desenhar_projeteis_e_efeitos, desenhar_floating_texts, desenhar_log,
    desenhar_info_personagem, desenhar_inventario, desenhar_comandos,
    desenhar_tela_fim, desenhar_tela_level_up, desenhar_tela_salvando,
    desenhar_tela_carregando, desenhar_editor, desenhar_dialogo,
    desenhar_menu_principal, desenhar_setup_batalha, desenhar_mapa_mundo
)
from .sistema_dialogo import Dialogo
from .salvar_carregar import salvar_jogo, carregar_jogo
from .utils import calcular_distancia, resource_path
from .ui.componentes import Botao, FloatingText, Checkbox, Tab
from .campanha import CampaignManager
from .personagens.rei_goblin import ReiGoblin
from .personagens.lorde_lich import LordeLich
from .personagens.dragao_anciao import DragaoAnciao
from .personagens.minions import Esqueleto, Goblin, Kobold

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Simulador de Batalha Tático")
        self.fonte_personagem = pygame.font.Font(None, 18)
        self.fonte_log = pygame.font.Font(None, 20)
        self.fonte_info = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 28)
        self.fonte_titulo = pygame.font.Font(None, 48)
        self.clock = pygame.time.Clock()

        self.sounds = self.carregar_sons()
        self.imagens = self.carregar_imagens()
        
        self.rodando = True
        self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
        self.botoes_menu_principal = setup_menu_principal_ui()
        self.estado_combate = None
        self.motor = None
        self.campaign_manager = CampaignManager()
        self.unidade_selecionada = None
        self.personagem_info_painel = None
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

        self.setup_ui()
        self.tocar_musica('menu')

    def tocar_musica(self, tipo):
        try:
            if tipo == 'menu':
                pygame.mixer.music.load(resource_path('assets/sounds/menu.wav'))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1) # Loop infinito
            elif tipo == 'batalha':
                pygame.mixer.music.load(resource_path('assets/sounds/battle1.wav'))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Erro ao tocar música ({tipo}): {e}")

    def atualizar_visibilidade(self):
        # Fog of War removido: Tudo sempre visível (2)
        for y in range(20):
            for x in range(20):
                self.visibilidade_map[y][x] = 2

    def carregar_sons(self):
        sounds = {}
        sound_paths = {
            'attack': 'assets/sounds/attack.wav',
            'button_click': 'assets/sounds/button_click.wav',
            'heal': 'assets/sounds/heal.wav',
            'hit': 'assets/sounds/hit.wav',
            'level_up': 'assets/sounds/level_up.wav',
            'miss': 'assets/sounds/miss.wav',
            'critical_hit': 'assets/sounds/critical_hit.wav',
            'invalid_action': 'assets/sounds/miss.wav',
        }

        for name, path in sound_paths.items():
            try:
                sounds[name] = pygame.mixer.Sound(resource_path(path))
            except pygame.error as e:
                print(f"Não foi possível carregar o som {path}: {e}")
                sounds[name] = None 

        return sounds



    def play_sound(self, nome):
        if nome in self.sounds and self.sounds[nome]:
            sound = self.sounds[nome]
            sound.set_volume(self.volume_sfx)
            sound.play()

    def carregar_imagens(self):
        imagens = {}
        # Carregar imagens de personagens
        for nome_personagem, caminho in IMAGE_PERSONAGENS.items():
            try:
                imagens[f"personagem_{nome_personagem.lower()}"] = pygame.image.load(resource_path(caminho)).convert_alpha()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do personagem {nome_personagem} em {caminho}: {e}")
                imagens[f"personagem_{nome_personagem.lower()}"] = None

        # Carregar imagens de terreno
        for tipo_terreno, caminho in IMAGE_TERRENOS.items():
            try:
                imagens[f"terreno_{tipo_terreno.lower()}"] = pygame.image.load(resource_path(caminho)).convert()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do terreno {tipo_terreno} em {caminho}: {e}")
                imagens[f"terreno_{tipo_terreno.lower()}"] = None
        return imagens

    def setup_ui(self):
        config_times_init, config_chefe_init, botoes_ui_init, checkbox_terreno_init, checkbox_auto_init, checkbox_chefe_init, checkbox_autoplay_init, checkbox_mapa_custom_init, checkbox_campanha_init, checkbox_limitadores_init, bosses_init = setup_menu_ui()
    
        self.config_times.update(config_times_init)
        self.config_chefe.update(config_chefe_init)
        self.botoes_ui.update(botoes_ui_init)
        self.botoes_ui['editor_mapas'] = Botao(LARGURA_TELA // 2 - 100, 460, 200, 50, "Editor de Mapas", self.fonte_menu)
        self.checkbox_terreno = checkbox_terreno_init
        self.checkbox_auto = checkbox_auto_init
        self.checkbox_chefe = checkbox_chefe_init
        self.checkbox_autoplay = checkbox_autoplay_init
        self.checkbox_mapa_custom = checkbox_mapa_custom_init
        self.checkbox_campanha = checkbox_campanha_init
        self.checkbox_limitadores = checkbox_limitadores_init
        self.bosses = bosses_init
        self.botoes_combate['proxima_acao'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, LARGURA_LOG - 40, 50, "Próxima Ação", self.fonte_menu)
        self.botoes_combate['salvar'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 130, 100, 30, "Salvar", self.fonte_menu)
        self.botoes_combate['carregar'] = Botao(LARGURA_TABULEIRO + 140, ALTURA_TELA - 130, 100, 30, "Carregar", self.fonte_menu)
        
        # Botões de aba do painel
        self.botoes_combate['aba_log'] = Botao(LARGURA_TABULEIRO, 60, 80, 30, "Log", self.fonte_menu)
        self.botoes_combate['aba_info'] = Botao(LARGURA_TABULEIRO + 80, 60, 80, 30, "Info", self.fonte_menu)
        self.botoes_combate['aba_inventario'] = Botao(LARGURA_TABULEIRO + 160, 60, 100, 30, "Inventário", self.fonte_menu)
        self.botoes_combate['cancelar'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 190, 100, 30, "Cancelar", self.fonte_menu)

        # Botões da tela de Fim de Jogo (Posicionados no painel lateral)
        x_painel = LARGURA_TABULEIRO + (LARGURA_LOG // 2) - 100
        y_painel = ALTURA_TELA // 2
        self.botoes_fim = {
            'reiniciar': Botao(x_painel, y_painel, 200, 50, "Reiniciar Batalha", self.fonte_menu),
            'voltar_menu': Botao(x_painel, y_painel + 60, 200, 50, "Voltar ao Menu", self.fonte_menu)
        }
        # Botões da tela de Level Up
        self.botoes_level_up = {
            'forca': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 60, 200, 40, "+1 Força", self.fonte_menu),
            'destreza': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 10, 200, 40, "+1 Destreza", self.fonte_menu),
            'constituicao': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 40, 200, 40, "+1 Constituição", self.fonte_menu),
            'inteligencia': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 90, 200, 40, "+1 Inteligência", self.fonte_menu),
            'sabedoria': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 140, 200, 40, "+1 Sabedoria", self.fonte_menu),
            'carisma': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 190, 200, 40, "+1 Carisma", self.fonte_menu),
        }

        # Botões do Editor de Mapas
        self.botoes_editor = {
            'salvar': Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, 120, 50, "Salvar Mapa", self.fonte_menu),
            'carregar': Botao(LARGURA_TABULEIRO + 160, ALTURA_TELA - 70, 140, 50, "Carregar Mapa", self.fonte_menu),
            'voltar': Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 130, LARGURA_LOG - 40, 50, "Voltar ao Menu", self.fonte_menu),
        }
        terrenos = [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]
        for i, terreno in enumerate(terrenos):
            self.botoes_editor[terreno] = Botao(LARGURA_TABULEIRO + 20, 100 + i * 50, LARGURA_LOG - 40, 40, terreno.title(), self.fonte_menu)

        # Inicializa abas do menu
        self.menu_tabs = {
            "times": Tab(LARGURA_TELA // 2 - 110, 100, 100, 40, "Times", self.fonte_menu, "times"),
            "configuracoes": Tab(LARGURA_TELA // 2 + 10, 100, 150, 40, "Configurações", self.fonte_menu, "configuracoes")
        }
        self.active_tab_id = "times"
        self.menu_tabs["times"].selected = True




    def iniciar_proxima_batalha_campanha(self):
        self.tocar_musica('batalha')
        battle_config = self.campaign_manager.get_battle_config()
        if not battle_config:
            self.log_combate.append(("CAMPANHA CONCLUÍDA!", COR_CRITICO))
            self.estado_jogo = ESTADO_JOGO_MENU
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

        try:
            self.motor = MotorCombate(args, 
                                      sound_player=self.play_sound, 
                                      gerar_terreno=True) # Terreno aleatório para cada batalha da campanha
            
            # Carrega o progresso dos personagens do jogador
            self.campaign_manager.carregar_progresso_personagens(self.motor.time_a)

            for p in self.motor.combatentes: p.dano_timer = 0
            self.log_combate.clear()
            self.log_combate.append((f"--- Campanha: Nível {self.campaign_manager.nivel_atual + 1} ---", COR_CRITICO))
            self.log_combate.append((battle_config["mensagem_inicio"], COR_TEXTO))

            # Iniciar Diálogo da Campanha
            if "dialogo_inicio" in battle_config:
                self.dialogo.iniciar_dialogo(battle_config["dialogo_inicio"])

        except ValueError as e:
            print(f"Erro ao iniciar batalha da campanha: {e}")
            self.estado_jogo = ESTADO_JOGO_MENU

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


    def handle_events(self, mouse_pos, personagem_ativo):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            
            # Se o diálogo estiver ativo, apenas ele recebe input
            if self.dialogo.ativo:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                        self.dialogo.processar_input()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.dialogo.processar_input()
                continue # Impede outros eventos

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if self.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
                        for nome, botao in self.botoes_menu_principal.items():
                            if botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                if nome == 'nova_batalha':
                                    self.estado_jogo = ESTADO_JOGO_SETUP
                                elif nome == 'campanha':
                                    self.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
                                elif nome == 'opcoes':
                                    # self.estado_jogo = ESTADO_JOGO_OPCOES # Futuro
                                    pass
                                elif nome == 'sair':
                                    self.rodando = False

                    elif self.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
                        # Botão Voltar
                        if self.botoes_ui['voltar_menu'].rect.collidepoint(mouse_pos):
                             self.play_sound('button_click')
                             self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                        
                        # Níveis da Campanha
                        from .campanha import CAMPAIGN_DATA
                        # Coordenadas dos nós (Hardcoded por enquanto para visualização)
                        nodes = [
                            (200, 400), (400, 300), (600, 400), (800, 250)
                        ]
                        
                        for i, (cx, cy) in enumerate(nodes):
                            if i < len(CAMPAIGN_DATA):
                                rect = pygame.Rect(cx - 30, cy - 30, 60, 60)
                                if rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    # Iniciar Batalha da Campanha
                                    self.checkbox_campanha.checked = True
                                    self.campaign_manager.nivel_atual = i
                                    self.iniciar_proxima_batalha_campanha()

                    elif self.estado_jogo == ESTADO_JOGO_SETUP:
                        # Handle tabs
                        for tab_id, tab in self.menu_tabs.items():
                            if tab.rect.collidepoint(mouse_pos):
                                self.active_tab_id = tab_id
                                for t in self.menu_tabs.values(): t.selected = False
                                tab.selected = True
                                self.play_sound('button_click')
                                return

                        # Handle buttons
                        for nome, botao in self.botoes_ui.items():
                            # Check visibility logic (same as drawing)
                            is_botao_chefe_attr = nome.startswith('chefe_')
                            is_botao_time_b = nome.startswith('B_')
                            is_boss_nav = nome in ['next_boss', 'prev_boss']
                            
                            visible = True
                            if self.active_tab_id == "times":
                                if is_botao_chefe_attr or is_boss_nav or is_botao_time_b or nome.startswith('A_'):
                                    if self.checkbox_chefe.checked:
                                        if is_botao_time_b: visible = False
                                    else:
                                        if is_boss_nav or is_botao_chefe_attr: visible = False
                                else:
                                    visible = False # Hide other buttons in times tab? No, wait.
                            elif self.active_tab_id == "configuracoes":
                                if nome in ['sfx_vol_down', 'sfx_vol_up']:
                                    visible = True
                                else:
                                    visible = False # Hide setup buttons in config tab

                            # Always visible buttons
                            if nome in ['iniciar', 'editor_mapas', 'voltar_menu']:
                                visible = True

                            if visible and botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                
                                if nome == 'iniciar':
                                    # Lógica para iniciar a batalha
                                    if self.checkbox_campanha.checked:
                                        self.iniciar_proxima_batalha_campanha()
                                    else:
                                        try:
                                            args = []
                                            # Time A
                                            for cls, _ in self.config_times['classes']:
                                                args.append(self.config_times[TIME_A].get(cls, 0))

                                            # Time B
                                            if not self.checkbox_chefe.checked:
                                                for cls, _ in self.config_times['classes']:
                                                    args.append(self.config_times[TIME_B].get(cls, 0))
                                            
                                            self.motor = MotorCombate(
                                                args,
                                                gerar_terreno=self.checkbox_terreno.checked,
                                                mapa_custom=self.editor_mapa if self.checkbox_mapa_custom.checked else None,
                                                sound_player=self.play_sound,
                                                modo_chefe=self.checkbox_chefe.checked,
                                                stats_chefe=self.config_chefe if self.checkbox_chefe.checked else None,
                                                boss_class=self.bosses[self.selected_boss_index]["classe"] if self.checkbox_chefe.checked else None
                                            )
                                            
                                            self.estado_jogo = ESTADO_JOGO_COMBATE
                                            self.tocar_musica('batalha')
                                            self.log_combate.clear()
                                            self.log_combate.clear()
                                            self.log_combate.append(("A batalha começou!", COR_TEXTO))
                                            
                                            # Teste de Diálogo
                                            self.dialogo.iniciar_dialogo([
                                                ("Narrador", "A batalha está prestes a começar!", None),
                                                ("Guerreiro", "Preparem-se para lutar!", "guerreiro"),
                                                ("Inimigo", "Vocês não passarão!", "goblin")
                                            ])

                                            if self.checkbox_limitadores.checked:
                                                self.motor.tabuleiro.adicionar_limitadores()
                                                
                                            self.atualizar_visibilidade() 

                                        except ValueError as e:
                                            print(f"Erro ao iniciar batalha: {e}")
                                            self.log_combate.append((f"Erro: {e}", COR_DANO))
                                elif nome == 'voltar_menu':
                                    self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                                elif nome == 'editor_mapas':
                                    self.estado_jogo = ESTADO_JOGO_EDITOR
                                elif nome.startswith('A_add_'):
                                    idx = int(nome.split('_')[-1])
                                    classe = self.config_times['classes'][idx][0]
                                    self.config_times[TIME_A][classe] += 1
                                elif nome.startswith('A_sub_'):
                                    idx = int(nome.split('_')[-1])
                                    classe = self.config_times['classes'][idx][0]
                                    if self.config_times[TIME_A][classe] > 0:
                                        self.config_times[TIME_A][classe] -= 1
                                elif nome.startswith('B_add_'):
                                    idx = int(nome.split('_')[-1])
                                    classe = self.config_times['classes'][idx][0]
                                    self.config_times[TIME_B][classe] += 1
                                elif nome.startswith('B_sub_'):
                                    idx = int(nome.split('_')[-1])
                                    classe = self.config_times['classes'][idx][0]
                                    if self.config_times[TIME_B][classe] > 0:
                                        self.config_times[TIME_B][classe] -= 1
                                elif nome == 'chefe_add_hp':
                                    self.config_chefe['hp'] += 10
                                elif nome == 'chefe_sub_hp':
                                    if self.config_chefe['hp'] > 10: self.config_chefe['hp'] -= 10
                                elif nome == 'chefe_add_ataque':
                                    self.config_chefe['ataque'] += 1
                                elif nome == 'chefe_sub_ataque':
                                    if self.config_chefe['ataque'] > 0: self.config_chefe['ataque'] -= 1
                                elif nome == 'chefe_add_ac':
                                    self.config_chefe['ac'] += 1
                                elif nome == 'chefe_sub_ac':
                                    if self.config_chefe['ac'] > 0: self.config_chefe['ac'] -= 1
                                elif nome == 'next_boss':
                                    self.selected_boss_index = (self.selected_boss_index + 1) % len(self.bosses)
                                elif nome == 'prev_boss':
                                    self.selected_boss_index = (self.selected_boss_index - 1) % len(self.bosses)

                        # Handle checkboxes
                        if self.active_tab_id == "configuracoes":
                            if self.checkbox_terreno.rect.collidepoint(mouse_pos): self.checkbox_terreno.toggle()
                            if self.checkbox_auto.rect.collidepoint(mouse_pos): self.checkbox_auto.toggle()
                            if self.checkbox_chefe.rect.collidepoint(mouse_pos): self.checkbox_chefe.toggle()
                            if self.checkbox_autoplay.rect.collidepoint(mouse_pos): self.checkbox_autoplay.toggle()
                            if self.checkbox_mapa_custom.rect.collidepoint(mouse_pos): self.checkbox_mapa_custom.toggle()
                            if self.checkbox_campanha.rect.collidepoint(mouse_pos): self.checkbox_campanha.toggle()
                            if self.checkbox_limitadores.rect.collidepoint(mouse_pos): self.checkbox_limitadores.toggle()

                    elif self.estado_jogo == ESTADO_JOGO_COMBATE:
                        # Handle Combat Buttons
                        for nome, botao in self.botoes_combate.items():
                            if botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                if nome == 'proxima_acao':
                                    if personagem_ativo and personagem_ativo.time == TIME_A:
                                        self.motor.avancar_turno()
                                        self.log_combate.append((f"{personagem_ativo.nome} passou a vez.", COR_TEXTO))
                                elif nome == 'salvar':
                                    self.motor.salvar_jogo()
                                    self.log_combate.append(("Jogo salvo!", COR_XP))
                                elif nome == 'carregar':
                                    if self.motor.carregar_jogo():
                                        self.log_combate.append(("Jogo carregado!", COR_XP))
                                        self.atualizar_visibilidade()
                                elif nome == 'voltar_menu':
                                    self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                                elif nome == 'reiniciar':
                                    # Logic to restart would go here, maybe just go back to setup
                                    self.estado_jogo = ESTADO_JOGO_SETUP
                                elif nome == 'cancelar':
                                    self.estado_jogo = ESTADO_JOGO_SETUP
                                    self.tocar_musica('menu')

                        # Handle Grid Interaction (Movement/Attack)
                        if mouse_pos[1] > ALTURA_BARRA_INICIATIVA and mouse_pos[0] < LARGURA_TABULEIRO:
                            grid_x = mouse_pos[0] // TAMANHO_CELULA
                            grid_y = (mouse_pos[1] - ALTURA_BARRA_INICIATIVA) // TAMANHO_CELULA
                            
                            if 0 <= grid_x < 20 and 0 <= grid_y < 20:
                                # Select unit on click (optional, for info panel)
                                clicked_unit = self.motor.tabuleiro.get_personagem_em(grid_x, grid_y)
                                if clicked_unit:
                                    self.unidade_selecionada = clicked_unit

                                # Player Action Logic
                                if personagem_ativo and personagem_ativo.time == TIME_A and not self.animacao_atual and not self.fila_animacoes:
                                    if clicked_unit and clicked_unit.time == TIME_B:
                                        # Attack Enemy
                                        dist = calcular_distancia(personagem_ativo, clicked_unit)
                                        if dist <= personagem_ativo.alcance:
                                            eventos, logs = self.motor.jogador_ataca_personagem(personagem_ativo, clicked_unit)
                                            self.fila_animacoes.extend(eventos)
                                            self.log_combate.extend(logs)
                                            self.motor.avancar_turno()
                                        else:
                                            self.log_combate.append(("Alvo fora de alcance!", COR_DANO))
                                            self.play_sound('invalid_action')
                                    elif not clicked_unit:
                                        # Move to empty tile
                                        eventos, logs = self.motor.jogador_move_personagem(personagem_ativo, grid_x, grid_y)
                                        if eventos: # If move was successful (valid path)
                                            self.fila_animacoes.extend(eventos)
                                            self.log_combate.extend(logs)
                                            self.motor.avancar_turno()
                                            self.atualizar_visibilidade()
                                        else:
                                            if not logs: self.play_sound('invalid_action')
                                            self.log_combate.extend(logs)

                    elif self.estado_jogo == ESTADO_JOGO_EDITOR:
                        # Handle Editor Buttons
                        for nome, botao in self.botoes_editor.items():
                            if botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                if nome in [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]:
                                    self.editor_terreno_selecionado = nome
                                elif nome == 'salvar':
                                    print("Salvar Mapa clicado (Implementar lógica de arquivo)")
                                    # Implementar lógica real de salvar mapa aqui
                                elif nome == 'carregar':
                                    print("Carregar Mapa clicado (Implementar lógica de arquivo)")
                                    # Implementar lógica real de carregar mapa aqui
                                elif nome == 'voltar':
                                    self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL

                        # Handle Grid Interaction (Paint Terrain)
                        if mouse_pos[1] > ALTURA_BARRA_INICIATIVA and mouse_pos[0] < LARGURA_TABULEIRO:
                            grid_x = mouse_pos[0] // TAMANHO_CELULA
                            grid_y = (mouse_pos[1] - ALTURA_BARRA_INICIATIVA) // TAMANHO_CELULA
                            
                            if 0 <= grid_x < 20 and 0 <= grid_y < 20:
                                self.editor_mapa[grid_y][grid_x] = self.editor_terreno_selecionado

    def update_game_logic(self, agora, personagem_ativo):
        if self.dialogo.ativo:
            self.dialogo.atualizar()
            return # Pausa o jogo atrás do diálogo

        if self.estado_jogo == ESTADO_JOGO_COMBATE:
            # Animation Handling
            if self.animacao_atual:
                # Check if animation finished (this logic depends on how animations are implemented in drawing)
                # For now, let's assume animations are visual only and we just wait a bit or check a timer
                # But looking at drawing code, it uses self.animacao_atual to draw. 
                # We need a way to expire animations.
                # Let's assume a simple timer for now if the animation dict doesn't have one.
                if 'inicio' not in self.animacao_atual:
                    self.animacao_atual['inicio'] = agora
                    self.animacao_atual['duracao'] = 500 # Default 500ms
                    if self.animacao_atual['tipo'] == 'ataque': self.play_sound('attack')
                    elif self.animacao_atual['tipo'] == 'movimento': pass # Sound handled elsewhere or continuous
                    elif self.animacao_atual['tipo'] == 'dano': self.play_sound('hit')
                    
                if agora - self.animacao_atual['inicio'] > self.animacao_atual['duracao']:
                    self.animacao_atual = None
                else:
                    self.animacao_atual['progresso'] = (agora - self.animacao_atual['inicio']) / self.animacao_atual['duracao']
            
            elif self.fila_animacoes:
                self.animacao_atual = self.fila_animacoes.popleft()
                self.animacao_atual['inicio'] = agora
                self.animacao_atual['duracao'] = 500
                self.animacao_atual['progresso'] = 0.0
                
                if self.animacao_atual['tipo'] == 'ataque': self.play_sound('attack')
                elif self.animacao_atual['tipo'] == 'dano': self.play_sound('hit')
            
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
                        self.atualizar_visibilidade()

    def draw_elements(self, tick, mouse_pos, personagem_ativo=None):
        self.tela.fill(COR_FUNDO)
        
        if self.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
            desenhar_menu_principal(self.tela, self.fonte_menu, self.botoes_menu_principal, mouse_pos)
        
        elif self.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
            from .campanha import CAMPAIGN_DATA
            desenhar_mapa_mundo(self.tela, self.fonte_menu, self.botoes_ui, CAMPAIGN_DATA, self.campaign_manager.nivel_atual, self.imagens, mouse_pos)

        elif self.estado_jogo == ESTADO_JOGO_SETUP:
            desenhar_setup_batalha(self.tela, self.fonte_menu, self.config_times, self.config_chefe, self.botoes_ui, 
                                   self.checkbox_terreno, self.checkbox_auto, self.checkbox_chefe, self.checkbox_autoplay, 
                                   self.checkbox_mapa_custom, self.checkbox_campanha, self.checkbox_limitadores, self.bosses, self.selected_boss_index, 
                                   self.imagens, self.volume_sfx, self.menu_tabs, self.active_tab_id, mouse_pos)
        
        elif self.estado_jogo == ESTADO_JOGO_COMBATE:
            if self.motor:
                visibilidade = self.motor.visibilidade_map
                desenhar_cenario(self.tela, self.motor, self.imagens, ALTURA_BARRA_INICIATIVA, visibilidade)
                desenhar_itens_no_chao(self.tela, self.motor.tabuleiro, ALTURA_BARRA_INICIATIVA, visibilidade)
                desenhar_personagens(self.tela, self.motor, self.fonte_personagem, personagem_ativo, tick, self.animacao_atual, self.imagens, ALTURA_BARRA_INICIATIVA, visibilidade)
                desenhar_projeteis_e_efeitos(self.tela, self.animacao_atual, ALTURA_BARRA_INICIATIVA, self.imagens)
                desenhar_barra_iniciativa(self.tela, self.motor.ordem_de_combate, personagem_ativo, self.imagens)
                desenhar_log(self.tela, self.fonte_log, self.log_combate, ALTURA_TELA, ALTURA_BARRA_INICIATIVA)
                
                if self.unidade_selecionada:
                    desenhar_info_personagem(self.tela, self.fonte_info, self.unidade_selecionada, ALTURA_TELA, ALTURA_BARRA_INICIATIVA)
                
                desenhar_comandos(self.tela, self.fonte_info, 0, self.botoes_combate, mouse_pos)
                desenhar_floating_texts(self.tela, self.floating_texts)
                
                desenhar_dialogo(self.tela, self.fonte_menu, self.dialogo, self.imagens)

        elif self.estado_jogo == ESTADO_JOGO_EDITOR:
            # Draw Grid Lines
            for y in range(20):
                for x in range(20):
                    rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA + ALTURA_BARRA_INICIATIVA, TAMANHO_CELULA, TAMANHO_CELULA)
                    
                    # Draw terrain from editor_mapa
                    terreno = self.editor_mapa[y][x]
                    terreno_img_key = f"terreno_{terreno.lower()}"
                    if terreno_img_key in self.imagens:
                        img = pygame.transform.scale(self.imagens[terreno_img_key], (TAMANHO_CELULA, TAMANHO_CELULA))
                        self.tela.blit(img, rect)
                    else:
                        pygame.draw.rect(self.tela, CORES_TERRENO.get(terreno, (0,0,0)), rect)
                        
                    pygame.draw.rect(self.tela, (50, 50, 50), rect, 1)
            
            # Draw Editor Panel Background
            area_editor = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, ALTURA_TELA)
            s = pygame.Surface((area_editor.width, area_editor.height), pygame.SRCALPHA)
            s.fill((40, 30, 20, 230))
            self.tela.blit(s, area_editor.topleft)
            pygame.draw.rect(self.tela, (218, 165, 32), area_editor, 3, border_radius=5)

            # Draw Buttons
            for nome, botao in self.botoes_editor.items():
                # Highlight selected terrain button
                if nome == self.editor_terreno_selecionado:
                    pygame.draw.rect(self.tela, (255, 215, 0), botao.rect.inflate(4, 4), 2, border_radius=5)
                botao.desenhar(self.tela, self.fonte_menu, mouse_pos)
            
            # Draw Title
            titulo = self.fonte_menu.render("Editor de Mapas", True, (255, 215, 0))
            self.tela.blit(titulo, (LARGURA_TABULEIRO + 20, 20))

