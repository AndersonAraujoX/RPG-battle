import pygame
from src.config import *
from src.ui.menu import setup_menu_ui
from src.ui.componentes import Botao, Tab
from src.utils import resource_path

class GameSetup:
    @staticmethod
    def tocar_musica(tipo):
        try:
            if tipo == 'menu':
                pygame.mixer.music.load(resource_path('assets/sounds/menu.wav'))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            elif tipo == 'batalha':
                pygame.mixer.music.load(resource_path('assets/sounds/battle1.wav'))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Erro ao tocar música ({tipo}): {e}")

    @staticmethod
    def carregar_sons():
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

    @staticmethod
    def play_sound(sounds_dict, nome, volume):
        if nome in sounds_dict and sounds_dict[nome]:
            sound = sounds_dict[nome]
            sound.set_volume(volume)
            sound.play()

    @staticmethod
    def carregar_imagens():
        imagens = {}
        for nome_personagem, caminho in IMAGE_PERSONAGENS.items():
            try:
                imagens[f"personagem_{nome_personagem.lower()}"] = pygame.image.load(resource_path(caminho)).convert_alpha()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do personagem {nome_personagem} em {caminho}: {e}")
                imagens[f"personagem_{nome_personagem.lower()}"] = None

        for tipo_terreno, caminho in IMAGE_TERRENOS.items():
            try:
                imagens[f"terreno_{tipo_terreno.lower()}"] = pygame.image.load(resource_path(caminho)).convert()
            except pygame.error as e:
                print(f"Não foi possível carregar a imagem do terreno {tipo_terreno} em {caminho}: {e}")
                imagens[f"terreno_{tipo_terreno.lower()}"] = None
        return imagens

    @staticmethod
    def setup_ui(game):
        config_times_init, config_chefe_init, botoes_ui_init, checkbox_terreno_init, checkbox_auto_init, checkbox_chefe_init, checkbox_autoplay_init, checkbox_mapa_custom_init, checkbox_campanha_init, checkbox_limitadores_init, bosses_init = setup_menu_ui()
    
        game.config_times.update(config_times_init)
        game.config_chefe.update(config_chefe_init)
        game.botoes_ui.update(botoes_ui_init)
        game.botoes_ui['editor_mapas'] = Botao(LARGURA_TELA // 2 - 100, 460, 200, 50, "Editor de Mapas", game.fonte_menu)
        game.checkbox_terreno = checkbox_terreno_init
        game.checkbox_auto = checkbox_auto_init
        game.checkbox_chefe = checkbox_chefe_init
        game.checkbox_autoplay = checkbox_autoplay_init
        game.checkbox_mapa_custom = checkbox_mapa_custom_init
        game.checkbox_campanha = checkbox_campanha_init
        game.checkbox_limitadores = checkbox_limitadores_init
        game.bosses = bosses_init
        
        btn_width = 250
        btn_height = 60
        margin_x = 20
        margin_y = 15
        
        total_width = (btn_width * 2) + margin_x
        start_x = (600 - total_width) // 2
        start_y = 600 + 20
        
        game.botoes_combate['atacar'] = Botao(start_x, start_y, btn_width, btn_height, "Atacar", game.fonte_menu)
        game.botoes_combate['habilidade'] = Botao(start_x + btn_width + margin_x, start_y, btn_width, btn_height, "Habilidade", game.fonte_menu)
        game.botoes_combate['item'] = Botao(start_x, start_y + btn_height + margin_y, btn_width, btn_height, "Item", game.fonte_menu)
        game.botoes_combate['acoes'] = Botao(start_x + btn_width + margin_x, start_y + btn_height + margin_y, btn_width, btn_height, "Ações", game.fonte_menu)
        game.botoes_combate['proxima_acao'] = Botao(start_x + (btn_width//2) + margin_x, start_y + (btn_height*2) + margin_y*2, btn_width, btn_height, "Passar Vez", game.fonte_menu)
        
        x_sys_center = 600 + (LARGURA_LOG // 2) 
        game.botoes_combate['salvar'] = Botao(x_sys_center - 90, 720, 80, 30, "Salvar", game.fonte_info)
        game.botoes_combate['carregar'] = Botao(x_sys_center + 10, 720, 80, 30, "Carregar", game.fonte_info)
        game.botoes_combate['cheat_win'] = Botao(x_sys_center - 85, 755, 170, 20, "VENCER (CHEAT)", game.fonte_personagem)

        game.botoes_combate['aba_log'] = Botao(LARGURA_TABULEIRO, 60, 80, 30, "Log", game.fonte_menu)
        game.botoes_combate['aba_info'] = Botao(LARGURA_TABULEIRO + 80, 60, 80, 30, "Info", game.fonte_menu)
        game.botoes_combate['aba_inventario'] = Botao(LARGURA_TABULEIRO + 160, 60, 100, 30, "Inventário", game.fonte_menu)
        game.botoes_combate['cancelar'] = Botao(LARGURA_TABULEIRO + 260, ALTURA_TELA - 90, 100, 30, "Cancelar", game.fonte_menu)

        x_painel = LARGURA_TABULEIRO + (LARGURA_LOG // 2) - 100
        y_painel = ALTURA_TELA // 2
        game.botoes_fim = {
            'reiniciar': Botao(x_painel, y_painel, 200, 50, "Reiniciar Batalha", game.fonte_menu),
            'voltar_menu': Botao(x_painel, y_painel + 60, 200, 50, "Voltar ao Menu", game.fonte_menu)
        }
        
        game.botoes_level_up = {
            'forca': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 60, 200, 40, "+1 Força", game.fonte_menu),
            'destreza': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 - 10, 200, 40, "+1 Destreza", game.fonte_menu),
            'constituicao': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 40, 200, 40, "+1 Constituição", game.fonte_menu),
            'inteligencia': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 90, 200, 40, "+1 Inteligência", game.fonte_menu),
            'sabedoria': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 140, 200, 40, "+1 Sabedoria", game.fonte_menu),
            'carisma': Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 190, 200, 40, "+1 Carisma", game.fonte_menu),
        }

        game.botoes_editor = {
            'salvar': Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, 120, 50, "Salvar Mapa", game.fonte_menu),
            'carregar': Botao(LARGURA_TABULEIRO + 160, ALTURA_TELA - 70, 140, 50, "Carregar Mapa", game.fonte_menu),
            'voltar': Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 130, LARGURA_LOG - 40, 50, "Voltar ao Menu", game.fonte_menu),
        }
        terrenos = [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]
        for i, terreno in enumerate(terrenos):
            game.botoes_editor[terreno] = Botao(LARGURA_TABULEIRO + 20, 100 + i * 50, LARGURA_LOG - 40, 40, terreno.title(), game.fonte_menu)

        game.menu_tabs = {
            "times": Tab(LARGURA_TELA // 2 - 110, 100, 100, 40, "Times", game.fonte_menu, "times"),
            "configuracoes": Tab(LARGURA_TELA // 2 + 10, 100, 150, 40, "Configurações", game.fonte_menu, "configuracoes")
        }
        game.active_tab_id = "times"
        game.menu_tabs["times"].selected = True
        
        game.map_gen_width = 20
        game.map_gen_height = 20
        y_gen = 600
        x_gen = LARGURA_TABULEIRO + 20
        
        game.botoes_gerador = {
            'w_dec': Botao(x_gen, y_gen, 30, 30, "-", game.fonte_menu),
            'w_inc': Botao(x_gen + 80, y_gen, 30, 30, "+", game.fonte_menu),
            'h_dec': Botao(x_gen, y_gen + 40, 30, 30, "-", game.fonte_menu),
            'h_inc': Botao(x_gen + 80, y_gen + 40, 30, 30, "+", game.fonte_menu),
            'gerar': Botao(x_gen, y_gen + 80, 150, 40, "Gerar Aleatório", game.fonte_menu)
        }

        y_dev = 150
        w_btn = 250
        h_btn = 50
        gap_x = 40
        gap_y = 20
        col1_x = LARGURA_TELA // 2 - w_btn - gap_x // 2
        col2_x = LARGURA_TELA // 2 + gap_x // 2
        
        game.botoes_dev = {
            'teste_combate': Botao(col1_x, y_dev, w_btn, h_btn, "Teste 1v1", game.fonte_menu),
            'teste_editor': Botao(col1_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Editor de Mapas", game.fonte_menu),
            'teste_dialogo': Botao(col1_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Teste Diálogo", game.fonte_menu),
            'teste_levelup': Botao(col1_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Teste Level Up", game.fonte_menu),
            
            'teste_boss': Botao(col2_x, y_dev, w_btn, h_btn, "Teste Boss (Sienna)", game.fonte_menu),
            'teste_mapa': Botao(col2_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Teste Mapa Mundo", game.fonte_menu),
            'teste_cutscene': Botao(col2_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Teste Final (Cutscene)", game.fonte_menu),
            'teste_fim': Botao(col2_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Teste Vitória", game.fonte_menu),

            'tree_warrior': Botao(col2_x + w_btn + gap_x, y_dev, w_btn, h_btn, "Tree: Warrior", game.fonte_menu),
            'tree_mage': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y), w_btn, h_btn, "Tree: Mage", game.fonte_menu),
            'tree_rogue': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*2, w_btn, h_btn, "Tree: Rogue", game.fonte_menu),
            'tree_cleric': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*3, w_btn, h_btn, "Tree: Cleric", game.fonte_menu),

            'selecao_capitulos': Botao(col1_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "Seleção de Fases", game.fonte_menu),
            'jogar_campanha': Botao(col2_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "Jogar Campanha", game.fonte_menu, cor_fundo=(60, 100, 60)),
            'toggle_god_mode': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*4, w_btn, h_btn, "God Mode: OFF", game.fonte_menu, cor_fundo=(100, 50, 50)),
            
            'add_resources': Botao(col1_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "+1000 XP/Ouro", game.fonte_menu, cor_fundo=(218, 165, 32), cor_texto=(0,0,0)),
            'unlock_all': Botao(col2_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "Desbloquear Tudo", game.fonte_menu, cor_fundo=(100, 200, 200), cor_texto=(0,0,0)),
            'teste_particulas': Botao(col2_x + w_btn + gap_x, y_dev + (h_btn + gap_y)*5, w_btn, h_btn, "Teste Partículas", game.fonte_menu),

            'voltar': Botao(LARGURA_TELA // 2 - 100, y_dev + (h_btn + gap_y)*6 + 10, 200, 50, "Voltar", game.fonte_menu, cor_fundo=(80, 20, 20))
        }
        
        game.god_mode = False 
        
        game.botoes_capitulos = {}
        y_cap = 100
        x_cap = 50
        cols = 3
        w_cap = 300
        h_cap = 60
        gap_cap_x = 20
        gap_cap_y = 20
        
        if hasattr(game.campaign_manager, 'campaign_data') and game.campaign_manager.campaign_data:
            for i, fase_data in enumerate(game.campaign_manager.campaign_data):
                col = i % cols
                row = i // cols
                x = x_cap + col * (w_cap + gap_cap_x)
                y = y_cap + row * (h_cap + gap_cap_y)
                
                titulo = f"{fase_data.get('titulo', f'Fase {i+1}')}"
                key = f"fase_{i}"
                game.botoes_capitulos[key] = Botao(x, y, w_cap, h_cap, titulo, game.fonte_menu)

        game.botoes_capitulos['voltar_dev'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA - 80, 200, 50, "Voltar", game.fonte_menu, cor_fundo=(80, 20, 20))

        game.modo_level_up = 'stat' 
        game.previous_state = ESTADO_JOGO_MENU_PRINCIPAL
