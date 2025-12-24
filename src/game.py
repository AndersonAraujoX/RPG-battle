import pygame
import sys
from collections import deque
from src.config import *
from src.perks import PERKS
from .motor_combate import MotorCombate
from .map_generator import MapGenerator
from .campanha import CampaignManager
from .cutscene import CutsceneManager
from .personagens import *
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
    ESTADO_JOGO_DEV, ESTADO_JOGO_LEVEL_UP,
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
        self.cutscene_manager = CutsceneManager(self.fim_cutscene)
        self.unidade_selecionada = None
        self.habilidade_selecionada = None # Estado para guardar qual habilidade está selecionada para uso
        self.skill_menu_open = False # [NEW] Controls visibility of skill buttons vs main actions
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

        self.setup_ui()
        self.tocar_musica('menu')
        
        # Optimization Trackers
        self.last_char_id = None
        self.last_menu_open = False

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
        
        # --- Botoes de Combate (Action Bar - Bottom Left) ---
        # Area: 600x168 (RECT_BARRA_ACOES) [0-600, 600-768]
        
        btn_width = 250
        btn_height = 60
        margin_x = 20
        margin_y = 15
        
        # Centralizar na area de 600px
        total_width = (btn_width * 2) + margin_x
        start_x = (600 - total_width) // 2
        start_y = 600 + 20
        
        self.botoes_combate['atacar'] = Botao(start_x, start_y, btn_width, btn_height, "Atacar", self.fonte_menu)
        self.botoes_combate['habilidade'] = Botao(start_x + btn_width + margin_x, start_y, btn_width, btn_height, "Habilidade", self.fonte_menu)
        
        self.botoes_combate['item'] = Botao(start_x, start_y + btn_height + margin_y, btn_width, btn_height, "Item", self.fonte_menu)
        self.botoes_combate['proxima_acao'] = Botao(start_x + btn_width + margin_x, start_y + btn_height + margin_y, btn_width, btn_height, "Defender", self.fonte_menu)
        
        # System Buttons (Painel Direito) - [600-1024] Center ~812
        x_sys_center = 600 + (LARGURA_LOG // 2) 
        # Buttons width 80+90 = 170. Start around center - 85.
        
        self.botoes_combate['salvar'] = Botao(x_sys_center - 90, 720, 80, 30, "Salvar", self.fonte_info)
        self.botoes_combate['carregar'] = Botao(x_sys_center + 10, 720, 80, 30, "Carregar", self.fonte_info)
        # Cheat
        self.botoes_combate['cheat_win'] = Botao(x_sys_center - 85, 755, 170, 20, "VENCER (CHEAT)", self.fonte_personagem)

        
        # Botões de aba do painel
        self.botoes_combate['aba_log'] = Botao(LARGURA_TABULEIRO, 60, 80, 30, "Log", self.fonte_menu)
        self.botoes_combate['aba_info'] = Botao(LARGURA_TABULEIRO + 80, 60, 80, 30, "Info", self.fonte_menu)
        self.botoes_combate['aba_inventario'] = Botao(LARGURA_TABULEIRO + 160, 60, 100, 30, "Inventário", self.fonte_menu)
        self.botoes_combate['cancelar'] = Botao(LARGURA_TABULEIRO + 260, ALTURA_TELA - 90, 100, 30, "Cancelar", self.fonte_menu)

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
        
        # --- UI do Gerador de Mapas ---
        self.map_gen_width = 20
        self.map_gen_height = 20
        y_gen = 600
        x_gen = LARGURA_TABULEIRO + 20
        
        self.botoes_gerador = {
            'w_dec': Botao(x_gen, y_gen, 30, 30, "-", self.fonte_menu),
            'w_inc': Botao(x_gen + 80, y_gen, 30, 30, "+", self.fonte_menu),
            'h_dec': Botao(x_gen, y_gen + 40, 30, 30, "-", self.fonte_menu),
            'h_inc': Botao(x_gen + 80, y_gen + 40, 30, 30, "+", self.fonte_menu),
            'gerar': Botao(x_gen, y_gen + 80, 150, 40, "Gerar Aleatório", self.fonte_menu)
        }

        # --- Menu DEV (Grid 2 Colunas) ---
        y_dev = 150
        w_btn = 250
        h_btn = 50
        gap_x = 40
        gap_y = 20
        col1_x = LARGURA_TELA // 2 - w_btn - gap_x // 2
        col2_x = LARGURA_TELA // 2 + gap_x // 2
        
        self.botoes_dev = {
            # Coluna 1
            'teste_combate': Botao(col1_x, y_dev, w_btn, h_btn, "Teste 1v1", self.fonte_menu),
            'teste_editor': Botao(col1_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Editor de Mapas", self.fonte_menu),
            'teste_dialogo': Botao(col1_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Teste Diálogo", self.fonte_menu),
            'teste_levelup': Botao(col1_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Teste Level Up", self.fonte_menu),
            
            # Coluna 2
            'teste_boss': Botao(col2_x, y_dev, w_btn, h_btn, "Teste Boss (Sienna)", self.fonte_menu),
            'teste_mapa': Botao(col2_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Teste Mapa Mundo", self.fonte_menu),
            'teste_cutscene': Botao(col2_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Teste Final (Cutscene)", self.fonte_menu),
            'teste_fim': Botao(col2_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Teste Vitória", self.fonte_menu),

            # Coluna 3 (Skill Tree Debug)
            'tree_warrior': Botao(col2_x + w_btn + gap_x, y_dev, w_btn, h_btn, "Tree: Warrior", self.fonte_menu),
            'tree_mage': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Tree: Mage", self.fonte_menu),
            'tree_rogue': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Tree: Rogue", self.fonte_menu),
            'tree_cleric': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Tree: Cleric", self.fonte_menu),

            # Coluna 4 (Misc) - Linha 5 (Actually Row 4 idx)
            'selecao_capitulos': Botao(col1_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "Seleção de Fases", self.fonte_menu),
            'jogar_campanha': Botao(col2_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "Jogar Campanha", self.fonte_menu, cor_fundo=(60, 100, 60)),
            'toggle_god_mode': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "God Mode: OFF", self.fonte_menu, cor_fundo=(100, 50, 50)),
            
            # Linha 6 (Extras)
            'add_resources': Botao(col1_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "+1000 XP/Ouro", self.fonte_menu, cor_fundo=(218, 165, 32), cor_texto=(0,0,0)),
            'unlock_all': Botao(col2_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "Desbloquear Tudo", self.fonte_menu, cor_fundo=(100, 200, 200), cor_texto=(0,0,0)),
            'teste_particulas': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "Teste Partículas", self.fonte_menu),

            # Voltar
            'voltar': Botao(LARGURA_TELA // 2 - 100, y_dev + (h_btn + gap_y)*6 + 10, 200, 50, "Voltar", self.fonte_menu, cor_fundo=(80, 20, 20))
        }
        
        self.god_mode = False # Inicializa estado
        
        # --- Botões de Seleção de Capítulos (Dynamically Generated) ---
        self.botoes_capitulos = {}
        y_cap = 100
        x_cap = 50
        cols = 3
        w_cap = 300
        h_cap = 60
        gap_cap_x = 20
        gap_cap_y = 20
        
        if hasattr(self.campaign_manager, 'campaign_data') and self.campaign_manager.campaign_data:
            for i, fase_data in enumerate(self.campaign_manager.campaign_data):
                col = i % cols
                row = i // cols
                x = x_cap + col * (w_cap + gap_cap_x)
                y = y_cap + row * (h_cap + gap_cap_y)
                
                titulo = f"{fase_data.get('titulo', f'Fase {i+1}')}"
                key = f"fase_{i}"
                self.botoes_capitulos[key] = Botao(x, y, w_cap, h_cap, titulo, self.fonte_menu)

        self.botoes_capitulos['voltar_dev'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA - 80, 200, 50, "Voltar", self.fonte_menu, cor_fundo=(80, 20, 20))

        self.modo_level_up = 'stat' # 'stat' or 'perk'
        self.previous_state = ESTADO_JOGO_MENU_PRINCIPAL # To store state before level up or menus

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
                if event.button in (1, 3): # Left or Right click
                    if self.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
                        if event.button == 1: # Menu is Left Click only
                            for nome, botao in self.botoes_menu_principal.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    if nome == 'nova_batalha':
                                        self.estado_jogo = ESTADO_JOGO_SETUP
                                        self.active_tab_id = "times"
                                        for t in self.menu_tabs.values(): t.selected = False
                                        self.menu_tabs["times"].selected = True
                                    elif nome == 'nova_campanha':
                                        self.checkbox_campanha.checked = True
                                        self.checkbox_chefe.checked = False
                                        
                                        # Initialize Campaign
                                        self.campaign_manager.reset()
                                        
                                        # Start Custom Campaign (Sienna Tower)
                                        self.iniciar_batalha_campanha_custom()
                                    elif nome == 'continuar':
                                        if self.campaign_manager.carregar_campanha():
                                            self.checkbox_campanha.checked = True
                                            self.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
                                        else:
                                            # TODO: Feedback visual se não houver save
                                            print("Nenhum save encontrado!")
                                    elif nome == 'opcoes':
                                        self.estado_jogo = ESTADO_JOGO_SETUP
                                        self.active_tab_id = "configuracoes"
                                        for t in self.menu_tabs.values(): t.selected = False
                                        self.menu_tabs["configuracoes"].selected = True
                                        
                                    elif nome == 'sair':
                                        self.rodando = False
                                    elif nome == 'dev':
                                        self.estado_jogo = ESTADO_JOGO_DEV

                    elif self.estado_jogo == ESTADO_JOGO_DEV:
                        if event.button == 1:
                            for nome, botao in self.botoes_dev.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    if nome == 'voltar':
                                        self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                                    elif nome == 'teste_combate':
                                        # Inicia combate simples 1x1
                                        try:
                                            # Arg list needs 24 items (12 classes Team A + 12 classes Team B)
                                            # Team A: 1 Guerreiro (index 0)
                                            # Team B: 1 Goblin (index 9)
                                            # List: [1, 0... (11 zeros)] + [0... (9 zeros), 1, 0, 0]
                                            args_a = [0] * 12
                                            args_a[0] = 1 # Guerreiro
                                            args_b = [0] * 12
                                            args_b[9] = 1 # Goblin
                                            
                                            self.motor = MotorCombate(args_a + args_b, sound_player=self.play_sound, gerar_terreno=True)
                                            self.estado_jogo = ESTADO_JOGO_COMBATE
                                            self.log_combate.clear()
                                            self.log_combate.append(("--- MODO DEV: TESTE COMBATE ---", COR_CRITICO))
                                            self.tocar_musica('batalha')
                                        except Exception as e:
                                            print(f"Erro dev combate: {e}")
                                    elif nome == 'teste_boss':
                                        # Inicia Sienna
                                        self.campaign_manager.reset()
                                        self.iniciar_batalha_campanha_custom()
                                    elif nome == 'teste_editor':
                                        self.estado_jogo = ESTADO_JOGO_EDITOR
                                    elif nome == 'teste_mapa':
                                        self.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
                                    elif nome == 'teste_cutscene':
                                        # Inicia a sequência final como teste
                                        self.iniciar_sequencia_final()
                                    elif nome == 'teste_fim':
                                        self.motor.vencedor = "Time A (Dev)"
                                        self.estado_jogo = ESTADO_JOGO_FIM
                                    elif nome == 'selecao_capitulos':
                                        self.estado_jogo = ESTADO_JOGO_DEV_CHAPTERS
                                    elif nome == 'jogar_campanha':
                                        self.checkbox_campanha.checked = True
                                        self.campaign_manager.reset()
                                        self.iniciar_proxima_batalha_campanha()
                                    elif nome == 'teste_dialogo':
                                        self.dialogo.iniciar_dialogo([
                                            ("Dev", "Testando sistema de diálogo completo.", None),
                                            ("Heroi", "Tudo parece operacional, comandante.", "guerreiro"),
                                            ("Vilão", "Não por muito tempo...", "lich"),
                                            ("Sistema", "Fim do teste.", None)
                                        ])
                                        self.estado_jogo = ESTADO_JOGO_NARRATIVA
                                        
                                    elif nome == 'toggle_god_mode':
                                        self.god_mode = not self.god_mode
                                        status = "ON" if self.god_mode else "OFF"
                                        bg = (50, 200, 50) if self.god_mode else (100, 50, 50)
                                        self.botoes_dev['toggle_god_mode'].texto = f"God Mode: {status}"
                                        self.botoes_dev['toggle_god_mode'].cor_fundo = bg
                                        
                                        # Apply immediately if in battle (unlikely from menu, but safe to check)
                                        if self.motor:
                                            for p in self.motor.personagens:
                                                if p.time == TIME_A:
                                                    p.invulneravel = self.god_mode

                                    elif nome == 'add_resources':
                                        self.campaign_manager.ganhar_xp(1000)
                                        self.campaign_manager.gold += 1000
                                        print("Dev: +1000 XP/Gold added.")

                                    elif nome == 'unlock_all':
                                        for pid in PERKS.keys():
                                            if pid not in self.campaign_manager.perks_desbloqueados:
                                                self.campaign_manager.perks_desbloqueados.append(pid)
                                        print("Dev: All Perks unlocked.")
                                        
                                    elif nome == 'teste_particulas':
                                        # Create some random explosions for visual test
                                        for _ in range(5):
                                            import random
                                            x = random.randint(100, LARGURA_TELA-100)
                                            y = random.randint(100, ALTURA_TELA-100)
                                            # Assuming direct animation access or using a dummy event
                                            # self.eventos_animacao.append(...) - handled in render loop usually?
                                            # Let's create a dummy combat just for effects if needed, 
                                            # or just spawn effects if renderer supports it.
                                            # renderer_combate supports 'explosao'.
                                            # self.animacao_atual is global animation list.
                                            pass # TODO: Hook into particle system properly

                                    elif nome == 'teste_levelup':
                                        # Cria um personagem dummy Nível 5 para testar árvore
                                        dummy = Guerreiro("Teste", "A")
                                        dummy.nivel = 5
                                        dummy.xp = 0
                                        self.personagem_level_up = dummy
                                        self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                                        self.modo_level_up = 'stat'
                                        self.verificar_opcoes_level_up()
                                    
                                    # Handlers de Debug Skill Tree
                                    elif nome == 'tree_warrior':
                                        dummy = Novak("Novak Debug", "A")
                                        dummy.nivel = 10
                                        self.personagem_level_up = dummy
                                        self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                                        self.modo_level_up = 'perk'
                                        self.verificar_opcoes_level_up()
                                    elif nome == 'tree_mage':
                                        dummy = Yukito("Yukito Debug", "A")
                                        dummy.nivel = 10
                                        self.personagem_level_up = dummy
                                        self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                                        self.modo_level_up = 'perk'
                                        self.verificar_opcoes_level_up()
                                    elif nome == 'tree_rogue':
                                        dummy = Rilem("Rilem Debug", "A")
                                        dummy.nivel = 10
                                        self.personagem_level_up = dummy
                                        self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                                        self.modo_level_up = 'perk'
                                        self.verificar_opcoes_level_up()
                                    elif nome == 'tree_cleric':
                                        dummy = Koema("Koema Debug", "A")
                                        dummy.nivel = 10
                                        self.personagem_level_up = dummy
                                        self.estado_jogo = ESTADO_JOGO_LEVEL_UP
                                        self.modo_level_up = 'perk'
                                        self.verificar_opcoes_level_up()

                    elif self.estado_jogo == ESTADO_JOGO_DEV_CHAPTERS:
                         if event.button == 1:
                            for key, botao in self.botoes_capitulos.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    if key == 'voltar_dev':
                                        self.estado_jogo = ESTADO_JOGO_DEV
                                    elif key.startswith('cap_'):
                                        idx = int(key.split('_')[1])
                                        self.iniciar_capitulo_dev(idx)

                    elif self.estado_jogo == ESTADO_JOGO_LEVEL_UP:
                        # Handle clicks on level up buttons (Stat or Perk)
                        if event.button == 1:
                            clicked_btn_name = None
                            for nome, botao in self.botoes_level_up.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    clicked_btn_name = nome
                                    break
                            
                            if clicked_btn_name:
                                personagem = self.personagem_level_up
                                
                                if self.modo_level_up == 'stat':
                                    if clicked_btn_name == 'forca': personagem._forca += 1
                                    elif clicked_btn_name == 'destreza': personagem._destreza += 1
                                    elif clicked_btn_name == 'constituicao': personagem._constituicao += 1
                                    elif clicked_btn_name == 'inteligencia': personagem._inteligencia += 1
                                    elif clicked_btn_name == 'sabedoria': personagem._sabedoria += 1
                                    elif clicked_btn_name == 'carisma': personagem._carisma += 1
                                    print(f"Stat aumentado: {clicked_btn_name}")
                                    
                                    # Após escolher um stat, o próximo passo é escolher um perk se disponível
                                    self.modo_level_up = 'perk'
                                    self.verificar_opcoes_level_up() # Tenta mudar para perk mode
                                    
                                    # Se não houver perks (verificar_opcoes setaria modo='perk', senao mantem 'stat' mas sem botoes?)
                                    # A lógica de verificar_opcoes vai limpar botoes se não houver perk?
                                    # Preciso ajustar isso. Se verificar retornar false/empty, sai.
                                    if self.modo_level_up == 'stat': # Significa que não achou perks
                                        self.estado_jogo = self.previous_state if self.previous_state else ESTADO_JOGO_COMBATE
                                        self.personagem_level_up = None

                                elif self.modo_level_up == 'perk':
                                    if clicked_btn_name == 'concluir':
                                         self.estado_jogo = self.previous_state if self.previous_state else ESTADO_JOGO_COMBATE
                                         self.personagem_level_up = None
                                    
                                    elif clicked_btn_name.startswith("perk_"):
                                        perk_id = clicked_btn_name.replace("perk_", "")
                                        
                                        # Encontrar dados do perk para validação
                                        classe = personagem.classe_nome
                                        perk_data = next((p for p in PERKS.get(classe, []) if p['id'] == perk_id), None)
                                        
                                        if perk_data:
                                            if personagem.pode_desbloquear_perk(perk_data):
                                                personagem.adquirir_perk(perk_id)
                                                self.play_sound('level_up') # Confirm sound
                                                print(f"Perk escolhido: {perk_id}")
                                                
                                                # Sai da tela após escolher (Assumindo 1 perk por level)
                                                self.estado_jogo = self.previous_state if self.previous_state else ESTADO_JOGO_COMBATE
                                                self.personagem_level_up = None
                                            else:
                                                print("Requisitos não atendidos ou já possui.")
                                                # Opcional: Tocar som de erro
                                                pass
                        
                        # Hack to exit level up screen in dev mode (Right click)
                        if event.button == 3: 
                            self.estado_jogo = ESTADO_JOGO_DEV



                    elif self.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
                        if event.button == 1:
                            # Botão Voltar
                            if self.botoes_ui['voltar_menu'].rect.collidepoint(mouse_pos):
                             self.play_sound('button_click')
                             self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                        
                        # Movimentação no Mapa Mundi
                        # Se clicar no mapa (e não no botão voltar), define destino
                        if mouse_pos[1] > 50: # Ignora clique na barra superior (título/voltar)
                            self.campaign_manager.destino_movimento = mouse_pos
                            
                        # Verificar interação com locais (Ao clicar ou chegar perto?)
                        # Vamos fazer ao clicar para simplificar, ou verificar colisão a cada frame
                        for local in self.campaign_manager.locais:
                            dist = ((local['pos'][0] - mouse_pos[0])**2 + (local['pos'][1] - mouse_pos[1])**2)**0.5
                            if dist < local['raio']:
                                # Clicou no local
                                self.play_sound('button_click')
                                self.checkbox_campanha.checked = True
                                self.campaign_manager.nivel_atual = local['evento_id']
                                self.iniciar_proxima_batalha_campanha()

                    elif self.estado_jogo == ESTADO_JOGO_SETUP:
                        # Handle tabs
                        if event.button == 1:
                            for tab_id, tab in self.menu_tabs.items():
                                if tab.rect.collidepoint(mouse_pos):
                                    self.active_tab_id = tab_id
                                    for t in self.menu_tabs.values(): t.selected = False
                                    tab.selected = True
                                    self.play_sound('button_click')
                                    return
    
                        # Handle buttons
                        if event.button == 1:
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
                                    if nome in ['sfx_vol_down', 'sfx_vol_up'] or nome.startswith('res_'):
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
                                                self.game_over_processed = False
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
                                    elif nome == 'sfx_vol_down':
                                        self.volume_sfx = max(0.0, self.volume_sfx - 0.1)
                                        pygame.mixer.music.set_volume(self.volume_sfx)
                                    elif nome == 'sfx_vol_up':
                                        self.volume_sfx = min(1.0, self.volume_sfx + 0.1)
                                        pygame.mixer.music.set_volume(self.volume_sfx)
                                    
                                    # Lógica de Resolução
                                    elif nome.startswith('res_'):
                                        import json
                                        w, h = 1024, 768
                                        if nome == 'res_800': w, h = 800, 600
                                        elif nome == 'res_1024': w, h = 1024, 768
                                        elif nome == 'res_1280': w, h = 1280, 720
                                        
                                        settings = {"width": w, "height": h}
                                        try:
                                            with open("settings.json", "w") as f:
                                                json.dump(settings, f)
                                            print(f"Resolução salva: {w}x{h}. Reinicie o jogo.")
                                            # Feedback visual simples (pode ser melhorado)
                                            if nome != 'res_fullscreen': # O "Salvar & Sair" fecha o jogo
                                                 pass 
                                            else:
                                                 self.rodando = False
                                        except Exception as e:
                                            print(f"Erro ao salvar settings: {e}")
                                            
                                        if nome == 'res_fullscreen':
                                             self.rodando = False # Sair para reiniciar

                        # Handle clicks on unit lists for adding/removing units (Left click to add, Right click to remove)
                        if self.active_tab_id == "times" and event.type == pygame.MOUSEBUTTONDOWN:
                            # Layout Constants (Must match drawing)
                            coluna_a_x = LARGURA_TELA // 4 - 150
                            coluna_b_x = LARGURA_TELA * 3 // 4 - 150
                            y_start = 200 # content_y_start
                            espacamento_y = 45
                            largura_linha = 350
                            altura_linha = 40
                            
                            # Check Clicks on Team A List
                            for i, (classe, nome_classe) in enumerate(self.config_times['classes']):
                                y_pos = y_start + i * espacamento_y
                                rect = pygame.Rect(coluna_a_x, y_pos, largura_linha, altura_linha)
                                
                                if rect.collidepoint(mouse_pos):
                                    if event.button == 1: # Left Click: Add
                                        self.config_times['A'][classe] += 1
                                        self.play_sound('button_click')
                                    elif event.button == 3: # Right Click: Remove
                                        if self.config_times['A'][classe] > 0:
                                            self.config_times['A'][classe] -= 1
                                            self.play_sound('button_click')
                            
                            # Check Clicks on Team B List (if not Boss)
                            if not self.checkbox_chefe.checked:
                                for i, (classe, nome_classe) in enumerate(self.config_times['classes']):
                                    y_pos = y_start + i * espacamento_y
                                    rect = pygame.Rect(coluna_b_x, y_pos, largura_linha, altura_linha)
                                    
                                    if rect.collidepoint(mouse_pos):
                                        if event.button == 1: # Left Click: Add
                                            self.config_times['B'][classe] += 1
                                            self.play_sound('button_click')
                                        elif event.button == 3: # Right Click: Remove
                                            if self.config_times['B'][classe] > 0:
                                                self.config_times['B'][classe] -= 1
                                                self.play_sound('button_click')
                            
                            # Boss Buttons (Keep existing logic if buttons exist)
                            if self.checkbox_chefe.checked:
                                # These are handled by the general button loop above, but if they were not,
                                # this is where specific click handling for them would go.
                                # The provided snippet has a redundant check for prev_boss/next_boss and stat buttons here.
                                # The existing `for nome, botao in self.botoes_ui.items():` loop already handles these.
                                # To avoid duplicate logic, we'll assume the existing button handling is sufficient
                                # for these specific boss buttons and stats.
                                pass # Existing button loop handles these.

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
                        # Handle End Game Buttons
                        if self.motor and self.motor.vencedor:
                            for nome, botao in self.botoes_fim.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    self.play_sound('button_click')
                                    if nome == 'reiniciar':
                                         if self.checkbox_campanha.checked:
                                             self.iniciar_proxima_batalha_campanha()
                                         else:
                                             self.estado_jogo = ESTADO_JOGO_SETUP
                                    elif nome == 'voltar_menu':
                                         self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                            return # Block other inputs on end screen

                        # Handle Combat Buttons
                        for nome, botao in list(self.botoes_combate.items()):
                            # Visibility check based on skill_menu_open
                            is_skill_btn = nome.startswith('habilidade_') or nome == 'voltar_skills'
                            is_main_btn = nome in ['atacar', 'habilidade', 'item', 'proxima_acao']
                            
                            if self.skill_menu_open:
                                if is_main_btn: continue
                            else:
                                if is_skill_btn: continue

                            if botao.rect.collidepoint(mouse_pos):
                                print(f"DEBUG: Clicked button '{nome}' | MenuOpen: {self.skill_menu_open} | Active: {personagem_ativo}")
                                self.play_sound('button_click')
                                
                                if nome == 'proxima_acao':
                                        self.log_combate.append((f"{personagem_ativo.nome} passou a vez.", COR_TEXTO))
                                        self.habilidade_selecionada = None
                                        self.skill_menu_open = False
                                        
                                elif nome == 'habilidade': # Open Skill Menu
                                     if personagem_ativo and personagem_ativo.time == TIME_A:
                                         self.skill_menu_open = True
                                         self.play_sound('button_click')
                                         # (Re)Generate buttons for safety/update
                                         self.atualizar_botoes_habilidade(personagem_ativo)

                                elif nome == 'voltar_skills': # Close Skill Menu
                                     print("DEBUG: Voltar Skills Clicked")
                                     self.skill_menu_open = False
                                     self.habilidade_selecionada = None
                                     self.play_sound('button_click')

                                elif nome.startswith('habilidade_'):
                                    hab_key = nome.split('habilidade_')[1]
                                    if self.habilidade_selecionada == hab_key:
                                        self.habilidade_selecionada = None # Toggle off
                                    else:
                                        self.habilidade_selecionada = hab_key
                                        self.log_combate.append((f"Habilidade selecionada: {personagem_ativo.habilidades[hab_key]['nome']}", COR_TEXTO))
                                
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
                                elif nome == 'cheat_win':
                                    self.iniciar_sequencia_final()

                        # Handle Grid Interaction (Movement/Attack)
                        if mouse_pos[1] > ALTURA_BARRA_INICIATIVA and mouse_pos[0] < LARGURA_TABULEIRO:
                            grid_x = mouse_pos[0] // TAMANHO_CELULA
                            grid_y = (mouse_pos[1] - ALTURA_BARRA_INICIATIVA) // TAMANHO_CELULA
                            
                            if 0 <= grid_x < 20 and 0 <= grid_y < 20 and self.motor:
                                # Select unit on click (optional, for info panel)
                                clicked_unit = self.motor.tabuleiro.get_personagem_em(grid_x, grid_y)
                                if clicked_unit:
                                    self.unidade_selecionada = clicked_unit

                                # Player Action Logic
                                if personagem_ativo and personagem_ativo.time == TIME_A and not self.animacao_atual and not self.fila_animacoes:
                                    
                                    # 1. Habilidade Selecionada
                                    if self.habilidade_selecionada:
                                        # Verifica se o tile clicado é válido
                                        valid_tiles, tipo = self.motor.get_alcance_habilidade(personagem_ativo, self.habilidade_selecionada)
                                        if (grid_x, grid_y) in valid_tiles:
                                            eventos, logs = self.motor.jogador_usar_habilidade(
                                                personagem_ativo, 
                                                self.habilidade_selecionada, 
                                                alvo=clicked_unit, 
                                                pos_alvo=(grid_x, grid_y)
                                            )
                                            if eventos or logs:
                                                self.fila_animacoes.extend(eventos)
                                                self.log_combate.extend(logs)
                                                # Só avança turno se realmente usou (eventos gerados ou gasto de mana confirmado)
                                                # A função jogador_usar_habilidade retorna eventos se sucesso.
                                                if eventos:
                                                    self.motor.avancar_turno()
                                                    self.habilidade_selecionada = None
                                        else:
                                            self.log_combate.append(("Alvo inválido para habilidade!", COR_DANO))
                                            self.play_sound('invalid_action')
                                            
                                    # 2. Ataque Normal (clique em inimigo)
                                    elif clicked_unit and clicked_unit.time == TIME_B:
                                        dist = calcular_distancia(personagem_ativo, clicked_unit)
                                        if dist <= personagem_ativo.alcance:
                                            eventos, logs = self.motor.jogador_ataca_personagem(personagem_ativo, clicked_unit)
                                            self.fila_animacoes.extend(eventos)
                                            self.log_combate.extend(logs)
                                            self.motor.avancar_turno()
                                        else:
                                            self.log_combate.append(("Alvo fora de alcance!", COR_DANO))
                                            self.play_sound('invalid_action')
                                            
                                    # 3. Movimento (clique em vazio ou aliado - para mover apenas)
                                    elif not clicked_unit:
                                        eventos, logs = self.motor.jogador_move_personagem(personagem_ativo, grid_x, grid_y)
                                        if eventos: # If move was successful (valid path)
                                            self.fila_animacoes.extend(eventos)
                                            self.log_combate.extend(logs)
                                            self.motor.avancar_turno()
                                            self.atualizar_visibilidade()
                                        else:
                                            if not logs: self.play_sound('invalid_action')
                                            self.log_combate.extend(logs)
                                else:
                                    # Not player turn or busy
                                    pass

                    elif self.estado_jogo == ESTADO_JOGO_EDITOR:
                        if mouse_pos[0] > LARGURA_TABULEIRO:
                            print(f"DEBUG: Click in Editor UI area. Pos: {mouse_pos}")
                            # Handle Generator Buttons
                            for nome, botao in self.botoes_gerador.items():
                                if botao.rect.collidepoint(mouse_pos):
                                    print(f"DEBUG: Button {nome} clicked. Current size: {self.map_gen_width}x{self.map_gen_height}")
                                    self.play_sound('button_click')
                                    if nome == 'w_dec' and self.map_gen_width > 10: self.map_gen_width -= 1
                                    elif nome == 'w_inc' and self.map_gen_width < 30: self.map_gen_width += 1
                                    elif nome == 'h_dec' and self.map_gen_height > 10: self.map_gen_height -= 1
                                    elif nome == 'h_inc' and self.map_gen_height < 22: self.map_gen_height += 1
                                    if nome == 'gerar':
                                        self.editor_mapa = MapGenerator.gerar_aleatorio(self.map_gen_width, self.map_gen_height)
                                        # Update UI positions
                                        largura_mapa_pixels = self.map_gen_width * TAMANHO_CELULA
                                        x_ui = max(LARGURA_TABULEIRO, largura_mapa_pixels) + 20
                                        # Recalcula posição dos botões do gerador
                                        base_y_gen = 600
                                        self.botoes_gerador['w_dec'].rect.x = x_ui
                                        self.botoes_gerador['w_inc'].rect.x = x_ui + 80
                                        self.botoes_gerador['h_dec'].rect.x = x_ui
                                        self.botoes_gerador['h_inc'].rect.x = x_ui + 80
                                        self.botoes_gerador['gerar'].rect.x = x_ui
                                        
                                        # Recalcula posição dos botões de terreno
                                        for i, t_nome in enumerate([TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_FOGO, TERRENO_AGUA, TERRENO_ROCHA, TERRENO_BARRIL]):
                                            if t_nome in self.botoes_editor:
                                                self.botoes_editor[t_nome].rect.x = x_ui
                                        
                                        # Update editor map dimensions text pos (handled in draw)
                                    else:
                                        # Update width/height buttons
                                        pass 
                                        
                        # Handle Terrain Selection
                        for nome, botao in self.botoes_editor.items():
                            if botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                if nome in [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]:
                                    self.editor_terreno_selecionado = nome

                        # Handle Editor Buttons
                        for nome, botao in self.botoes_editor.items():
                            if botao.rect.collidepoint(mouse_pos):
                                self.play_sound('button_click')
                                if nome in [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]:
                                    self.editor_terreno_selecionado = nome
                                elif nome == 'salvar':
                                    if salvar_mapa_json(self.editor_mapa):
                                        print("Mapa Salvo com Sucesso!")
                                        self.play_sound('level_up') # Feedback sonoro
                                elif nome == 'carregar':
                                    mapa_carregado = carregar_mapa_json()
                                    if mapa_carregado:
                                        self.editor_mapa = mapa_carregado
                                        # Update dimensions for generator UI
                                        self.map_gen_height = len(self.editor_mapa)
                                        self.map_gen_width = len(self.editor_mapa[0]) if self.map_gen_height > 0 else 20
                                        print("Mapa Carregado com Sucesso!")
                                        self.play_sound('level_up')
                                elif nome == 'voltar':
                                    self.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL

                        # Handle Grid Interaction (Paint Terrain)
                        if mouse_pos[1] > ALTURA_BARRA_INICIATIVA and mouse_pos[0] < LARGURA_TABULEIRO:
                            grid_x = mouse_pos[0] // TAMANHO_CELULA
                            grid_y = (mouse_pos[1] - ALTURA_BARRA_INICIATIVA) // TAMANHO_CELULA
                            
                            if 0 <= grid_x < 20 and 0 <= grid_y < 20:
                                self.editor_mapa[grid_y][grid_x] = self.editor_terreno_selecionado
                    
                    elif self.estado_jogo == ESTADO_JOGO_CUTSCENE:
                        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                            self.cutscene_manager.pular()

    def update_game_logic(self, agora, personagem_ativo):
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
            state_changed = (current_char_id != self.last_char_id) or (self.skill_menu_open != self.last_menu_open)
            
            if state_changed:
                 self.atualizar_botoes_habilidade(personagem_ativo)
                 self.last_char_id = current_char_id
                 self.last_menu_open = self.skill_menu_open
            
            # Fallback: if not player turn, ensure menu is closed (handled in atualizar_botoes_habilidade, but we must call it if turn changed)
            if personagem_ativo and personagem_ativo.time != TIME_A and self.skill_menu_open:
                 self.skill_menu_open = False
                 self.atualizar_botoes_habilidade(personagem_ativo)
                 self.last_menu_open = False

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
            self.botoes_combate['voltar_skills'] = Botao(start_x + 2*(btn_width + margin_x), 550, 100, 50, "Voltar", self.fonte_menu)

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

    def draw_elements(self, tick, mouse_pos, personagem_ativo=None):
        self.tela.fill(COR_FUNDO)
        
        if self.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
            desenhar_menu_principal(self.tela, self.fonte_menu, self.botoes_menu_principal, mouse_pos)
        
        elif self.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
            from .campanha import CAMPAIGN_DATA
            desenhar_mapa_mundo(self.tela, self.fonte_menu, self.botoes_ui, self.campaign_manager, self.campaign_manager.nivel_atual, self.imagens, mouse_pos)

        elif self.estado_jogo == ESTADO_JOGO_SETUP:
            desenhar_setup_batalha(self.tela, self.fonte_menu, self.config_times, self.config_chefe, self.botoes_ui, 
                                   self.checkbox_terreno, self.checkbox_auto, self.checkbox_chefe, self.checkbox_autoplay, 
                                   self.checkbox_mapa_custom, self.checkbox_campanha, self.checkbox_limitadores, self.bosses, self.selected_boss_index, 
                                   self.imagens, self.volume_sfx, self.menu_tabs, self.active_tab_id, mouse_pos)
        
        elif self.estado_jogo == ESTADO_JOGO_COMBATE:
             # 1. Background / Interface Retro
            desenhar_interface_retro(self.tela, self.fonte_menu)
            
            # 2. Cenário (Tabuleiro) - Tabuleiro começa em (0,0)
            if self.motor:
                visibilidade = self.motor.visibilidade_map
                desenhar_cenario(self.tela, self.motor, self.imagens, ALTURA_BARRA_INICIATIVA, visibilidade)
                
                desenhar_itens_no_chao(self.tela, self.motor.tabuleiro, ALTURA_BARRA_INICIATIVA, visibilidade)
                desenhar_personagens(self.tela, self.motor, self.fonte_personagem, personagem_ativo, tick, self.animacao_atual, self.imagens, ALTURA_BARRA_INICIATIVA, visibilidade)
                
                # Visualize Movement or Ability Range
                if self.habilidade_selecionada:
                    desenhar_alcance_habilidade(self.tela, self.motor, personagem_ativo, self.habilidade_selecionada, ALTURA_BARRA_INICIATIVA, mouse_pos)
                else:
                    desenhar_alcance_movimento(self.tela, self.motor, personagem_ativo, ALTURA_BARRA_INICIATIVA)
                    desenhar_pre_visualizacao_ataque(self.tela, self.motor, self.motor.tabuleiro.get_personagem_em(mouse_pos[0] // TAMANHO_CELULA, (mouse_pos[1] - ALTURA_BARRA_INICIATIVA) // TAMANHO_CELULA) if mouse_pos[1] > ALTURA_BARRA_INICIATIVA and mouse_pos[0] < LARGURA_TABULEIRO else None, self.imagens, ALTURA_BARRA_INICIATIVA)

                desenhar_projeteis_e_efeitos(self.tela, self.animacao_atual, ALTURA_BARRA_INICIATIVA, self.imagens)
                desenhar_barra_iniciativa(self.tela, self.motor.ordem_de_combate, personagem_ativo, self.imagens)
                desenhar_log(self.tela, self.fonte_log, self.log_combate, ALTURA_TELA, ALTURA_BARRA_INICIATIVA)
                
                if self.unidade_selecionada:
                    desenhar_info_personagem(self.tela, self.fonte_info, self.unidade_selecionada, ALTURA_BARRA_INICIATIVA)
                
                desenhar_comandos(self.tela, self.fonte_info, 0, self.botoes_combate, mouse_pos, personagem_ativo)
                desenhar_floating_texts(self.tela, self.floating_texts)
                
                desenhar_dialogo(self.tela, self.fonte_menu, self.dialogo, self.imagens)

                if self.motor.vencedor:
                    desenhar_tela_fim(self.tela, self.fonte_titulo, self.fonte_menu, self.motor.vencedor, self.botoes_fim, mouse_pos)
        
        elif self.estado_jogo == ESTADO_JOGO_CUTSCENE:
             self.cutscene_manager.desenhar(self.tela)
        
        elif self.estado_jogo == ESTADO_JOGO_LEVEL_UP:
             self.tela.fill((0, 0, 0)) # Limpa a tela para remover UI de combate anterior
             if self.personagem_level_up:
                 desenhar_tela_level_up(self.tela, self.fonte_titulo, self.fonte_menu, self.personagem_level_up, self.botoes_level_up, mouse_pos)

        
        elif self.estado_jogo == ESTADO_JOGO_DEV:
            self.tela.fill((10, 0, 0)) # Fundo avermelhado escuro
            texto_dev = self.fonte_titulo.render("MENU DO DESENVOLVEDOR", True, (255, 50, 50))
            self.tela.blit(texto_dev, (LARGURA_TELA // 2 - texto_dev.get_width() // 2, 80))
            
            for botao in self.botoes_dev.values():
                botao.desenhar(self.tela, self.fonte_menu, mouse_pos)

        elif self.estado_jogo == ESTADO_JOGO_DEV_CHAPTERS:
            self.tela.fill((10, 0, 20)) # Fundo roxo escuro
            texto_cap = self.fonte_titulo.render("SELEÇÃO DE FASES - DEV MODE", True, (150, 100, 255))
            self.tela.blit(texto_cap, (LARGURA_TELA // 2 - texto_cap.get_width() // 2, 40))
            
            for botao in self.botoes_capitulos.values():
                botao.desenhar(self.tela, self.fonte_menu, mouse_pos)

        elif self.estado_jogo == ESTADO_JOGO_EDITOR:
            # Draw Grid Lines
            for y in range(len(self.editor_mapa)):
                for x in range(len(self.editor_mapa[y])):
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
            
            # Draw Generator UI
            for nome, botao in self.botoes_gerador.items():
                botao.update_hover(mouse_pos)
                botao.desenhar(self.tela, self.fonte_menu)
                
            # Draw Generator Text
            largura_mapa_pixels = len(self.editor_mapa[0]) * TAMANHO_CELULA
            x_ui = max(LARGURA_TABULEIRO, largura_mapa_pixels)
            txt_x = x_ui + 130
            
            txt_w = self.fonte_menu.render(f"Largura: {self.map_gen_width}", True, COR_TEXTO)
            self.tela.blit(txt_w, (txt_x, 605))
            txt_h = self.fonte_menu.render(f"Altura: {self.map_gen_height}", True, COR_TEXTO)
            self.tela.blit(txt_h, (txt_x, 645))
            
            # Draw Title
            titulo = self.fonte_menu.render("Editor de Mapas", True, (255, 215, 0))
            self.tela.blit(titulo, (x_ui + 20, 20))

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


