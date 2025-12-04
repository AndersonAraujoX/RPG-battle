import pygame
import sys
from collections import deque
from .config import *
from .motor_combate import MotorCombate
from .personagens import *
from .ui.menu import setup_menu_ui, desenhar_setup_batalha, desenhar_menu_principal, setup_menu_principal_ui
from .ui.desenho import (
    desenhar_barra_iniciativa, desenhar_cenario, desenhar_itens_no_chao,
    desenhar_personagens, desenhar_pre_visualizacao_ataque,
    desenhar_projeteis_e_efeitos, desenhar_floating_texts, desenhar_log,
    desenhar_info_personagem, desenhar_inventario, desenhar_comandos,
    desenhar_tela_fim, desenhar_tela_level_up, desenhar_tela_salvando,
    desenhar_tela_carregando, desenhar_editor
)
from .salvar_carregar import salvar_jogo, carregar_jogo
from .utils import calcular_distancia
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
        self.estado_jogo = ESTADO_JOGO_MENU
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
        self.bosses = []
        self.selected_boss_index = 0
        self.hovered_enemy = None
        self.volume_sfx = 0.5

        self.feedback_invalido_timer = 0
        self.visibilidade_map = [[0] * 20 for _ in range(20)]
        self.personagem_level_up = None
        self.save_filename = ""
        self.save_files = []
        self.floating_texts = []
        self.editor_mapa = [[TERRENO_NORMAL for _ in range(20)] for _ in range(20)]
        self.editor_terreno_selecionado = TERRENO_NORMAL

        self.setup_ui()
        self.tocar_musica('menu')

    def tocar_musica(self, tipo):
        try:
            if tipo == 'menu':
                pygame.mixer.music.load('assets/sounds/menu.wav')
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1) # Loop infinito
            elif tipo == 'batalha':
                pygame.mixer.music.load('assets/sounds/battle1.wav')
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Erro ao tocar música ({tipo}): {e}")

    def atualizar_visibilidade(self):
        if not self.motor:
            return

        # 1. Reduz a visibilidade de todas as células que estavam visíveis
        for y in range(self.motor.tabuleiro.altura):
            for x in range(self.motor.tabuleiro.largura):
                if self.visibilidade_map[y][x] == 2:
                    self.visibilidade_map[y][x] = 1 # Marcar como "visto, mas não na visão atual"
        
        # 2. Calcula a nova visibilidade para o time A
        for p in self.motor.time_a:
            if p.esta_vivo:
                for y in range(self.motor.tabuleiro.altura):
                    for x in range(self.motor.tabuleiro.largura):
                        # Usar um raio de visão, por exemplo, 10
                        if calcular_distancia(p, type('obj', (object,), {'pos_x': x, 'pos_y': y})) <= 10:
                            if self.motor.tabuleiro.calcular_linha_visao(p.pos_x, p.pos_y, x, y):
                                self.visibilidade_map[y][x] = 2 # Marcar como "atualmente visível"

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
            'invalid_action': 'assets/sounds/invalid_action.wav',
        }

        for name, path in sound_paths.items():
            try:
                sounds[name] = pygame.mixer.Sound(path)
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
                imagens[f"personagem_{nome_personagem.lower()}"] = pygame.image.load(caminho).convert_alpha()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do personagem {nome_personagem} em {caminho}: {e}")
                imagens[f"personagem_{nome_personagem.lower()}"] = None

        # Carregar imagens de terreno
        for tipo_terreno, caminho in IMAGE_TERRENOS.items():
            try:
                imagens[f"terreno_{tipo_terreno.lower()}"] = pygame.image.load(caminho).convert()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do terreno {tipo_terreno} em {caminho}: {e}")
                imagens[f"terreno_{tipo_terreno.lower()}"] = None
        return imagens

    def setup_ui(self):
        config_times_init, config_chefe_init, botoes_ui_init, checkbox_terreno_init, checkbox_auto_init, checkbox_chefe_init, checkbox_autoplay_init, bosses_init = setup_menu_ui()
    
        self.config_times.update(config_times_init)
        self.config_chefe.update(config_chefe_init)
        self.botoes_ui.update(botoes_ui_init)
        self.botoes_ui['editor_mapas'] = Botao(LARGURA_TELA // 2 - 100, 460, 200, 50, "Editor de Mapas", self.fonte_menu)
        self.checkbox_terreno = checkbox_terreno_init
        self.checkbox_auto = checkbox_auto_init
        self.checkbox_chefe = checkbox_chefe_init
        self.checkbox_autoplay = checkbox_autoplay_init
        self.checkbox_mapa_custom = Checkbox(LARGURA_TELA // 2 - 100, 520, 20, "Usar Mapa Customizado", self.fonte_menu)
        self.checkbox_campanha = Checkbox(LARGURA_TELA // 2 - 100, 550, 20, "Modo Campanha", self.fonte_menu)
        self.bosses = bosses_init
        self.botoes_combate['proxima_acao'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, LARGURA_LOG - 40, 50, "Próxima Ação", self.fonte_menu)
        self.botoes_combate['salvar'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 130, 100, 30, "Salvar", self.fonte_menu)
        self.botoes_combate['carregar'] = Botao(LARGURA_TABULEIRO + 140, ALTURA_TELA - 130, 100, 30, "Carregar", self.fonte_menu)
        
        # Botões de aba do painel
        self.botoes_combate['aba_log'] = Botao(LARGURA_TABULEIRO, 60, 80, 30, "Log", self.fonte_menu)
        self.botoes_combate['aba_info'] = Botao(LARGURA_TABULEIRO + 80, 60, 80, 30, "Info", self.fonte_menu)
        self.botoes_combate['aba_inventario'] = Botao(LARGURA_TABULEIRO + 160, 60, 100, 30, "Inventário", self.fonte_menu)
        self.botoes_combate['reiniciar'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 50, 200, 50, "Reiniciar Batalha", self.fonte_menu)
        self.botoes_combate['voltar_menu'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 120, 200, 50, "Voltar ao Menu", self.fonte_menu)

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
        terrenos = [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO]
        for i, terreno in enumerate(terrenos):
            self.botoes_editor[terreno] = Botao(LARGURA_TABULEIRO + 20, 100 + i * 60, LARGURA_LOG - 40, 50, terreno.title(), self.fonte_menu)

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
            
            self.draw_elements(tick, mouse_pos)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


