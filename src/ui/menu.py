import pygame
from ..config import *
from ..utils import resource_path
from .componentes import Botao, Checkbox, Tab # Import Tab
from ..personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Chefe, Druida, Bruxo
from ..personagens.rei_goblin import ReiGoblin
from ..personagens.lorde_lich import LordeLich
from ..personagens.dragao_anciao import DragaoAnciao
from ..personagens.minions import Goblin, Esqueleto, Kobold

def desenhar_menu_principal(tela, fonte, botoes_menu):
    tela.fill(COR_FUNDO_MENU)
    
    # Logo
    try:
        logo_img = pygame.image.load(resource_path("assets/images/logo.png")).convert_alpha()
        # Scale logo if necessary (e.g., to width 600)
        target_width = 600
        scale_factor = target_width / logo_img.get_width()
        new_height = int(logo_img.get_height() * scale_factor)
        logo_img = pygame.transform.scale(logo_img, (target_width, new_height))
        
        logo_rect = logo_img.get_rect(center=(LARGURA_TELA // 2, 120))
        tela.blit(logo_img, logo_rect)
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        # Fallback to text if logo fails
        fonte_titulo_grande = pygame.font.Font(None, 110)
        titulo_render = fonte_titulo_grande.render("OS ESQUECIDOS", True, (220, 220, 220))
        tela.blit(titulo_render, (LARGURA_TELA // 2 - titulo_render.get_width() // 2, 80))

    # Subtítulo
    fonte_sub = pygame.font.Font(None, 32)
    subtitulo = fonte_sub.render("KUAR-TOR: ECOS DO VAZIO", True, COR_ACCENT)
    tela.blit(subtitulo, (LARGURA_TELA // 2 - subtitulo.get_width() // 2, 220)) # Adjusted Y for logo
    
    # Linhas decorativas com brilho
    pygame.draw.line(tela, COR_ACCENT, (LARGURA_TELA // 2 - 320, 232), (LARGURA_TELA // 2 - 200, 232), 2)
    pygame.draw.line(tela, COR_ACCENT, (LARGURA_TELA // 2 + 200, 232), (LARGURA_TELA // 2 + 320, 232), 2)

    # Desenhar botões do menu principal
    for botao in botoes_menu.values():
        botao.update_hover(pygame.mouse.get_pos())
        botao.desenhar(tela, fonte)

def desenhar_setup_batalha(tela, fonte, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, checkbox_mapa_custom, checkbox_campanha, checkbox_limitadores, bosses, selected_boss_index, game_images, volume_sfx, menu_tabs, active_tab_id): # Renamed from desenhar_menu
    tela.fill(COR_FUNDO)
    
    # Título da Tela de Setup
    titulo_render = fonte.render("CONFIGURAÇÃO DE BATALHA", True, COR_TEXTO)
    tela.blit(titulo_render, (LARGURA_TELA // 2 - titulo_render.get_width() // 2, 30))

    # Draw Tabs
    tab_y_start = 80
    for tab in menu_tabs.values():
        tab.desenhar(tela, fonte)

    # Base Y position for content, adjusted for tab height
    content_y_start = 150 # Adjusted y_start for tab height
    
    if active_tab_id == "times":
        x_time_a = LARGURA_TELA // 4
        x_time_b = LARGURA_TELA * 3 // 4
        # --- Time A ---
        tela.blit(fonte.render("Time A", True, CORES_TIME["A"]), (x_time_a - 80, content_y_start - 40))
        for i, (classe, nome_classe) in enumerate(config_times['classes']):
            y_pos = content_y_start + i * 50
            tela.blit(fonte.render(f"{nome_classe}: {config_times['A'][classe]}", True, COR_TEXTO), (x_time_a - 80, y_pos + 5))

        # --- Time B ou Chefe ---
        tela.blit(fonte.render("Time B", True, CORES_TIME["B"]), (x_time_b - 80, content_y_start - 40))
        if checkbox_chefe.checked:
            # --- Boss Selection UI ---
            selected_boss = bosses[selected_boss_index]
            boss_class = selected_boss["classe"]
            boss_name = selected_boss["nome"]

            # Display boss name
            tela.blit(fonte.render(boss_name, True, COR_TEXTO), (x_time_b - 80, content_y_start))

            # Display boss "print" (image)
            boss_img_key = f"personagem_{boss_class.__name__.lower()}"
            if boss_img_key in game_images and game_images[boss_img_key]:
                img = game_images[boss_img_key]
                # Scale image to a reasonable size for the menu
                scaled_img = pygame.transform.scale(img, (100, 100))
                tela.blit(scaled_img, (x_time_b - 50, content_y_start + 40))

            # Display boss stats and abilities
            # Create a temporary instance to get stats
            temp_boss = boss_class("temp", "B")
            y_offset = content_y_start + 160
            stats_to_show = [
                f"HP: {temp_boss.hp_max}",
                f"AC: {temp_boss.ac}",
                f"Ataque: +{temp_boss.bonus_ataque}",
                f"Dano: {temp_boss.dado_dano[0]}d{temp_boss.dado_dano[1]} +{temp_boss.bonus_dano}",
            ]
            for stat in stats_to_show:
                tela.blit(fonte.render(stat, True, COR_TEXTO), (x_time_b - 80, y_offset))
                y_offset += 30

            y_offset += 10
            tela.blit(fonte.render("Habilidades:", True, COR_TEXTO), (x_time_b - 80, y_offset))
            y_offset += 25
            for ability in temp_boss.cooldowns:
                tela.blit(fonte.render(f"- {ability.replace('_', ' ').title()}", True, COR_TEXTO), (x_time_b - 60, y_offset))
                y_offset += 25
            
            y_offset += 10
            tela.blit(fonte.render("Imunidades:", True, COR_TEXTO), (x_time_b - 80, y_offset))
            y_offset += 25
            for immunity in temp_boss.imunidades:
                tela.blit(fonte.render(f"- {immunity}", True, COR_TEXTO), (x_time_b - 60, y_offset))
                y_offset += 25

        else:
            # Interface Normal do Time B
            for i, (classe, nome_classe) in enumerate(config_times['classes']):
                y_pos = content_y_start + i * 50
                tela.blit(fonte.render(f"{nome_classe}: {config_times['B'][classe]}", True, COR_TEXTO), (x_time_b - 80, y_pos + 5))

        # Draw buttons related to times
        for nome, botao in botoes_ui.items():
            is_botao_chefe_attr = nome.startswith('chefe_')
            is_botao_time_b = nome.startswith('B_')
            is_boss_nav = nome in ['next_boss', 'prev_boss']

            if is_botao_chefe_attr or is_boss_nav or is_botao_time_b or nome.startswith('A_'): # Only draw A_ and B_ and boss_nav buttons for "times" tab
                if checkbox_chefe.checked:
                    if is_botao_time_b: continue
                else:
                    if is_boss_nav or is_botao_chefe_attr: continue
                botao.update_hover(pygame.mouse.get_pos())
                botao.desenhar(tela, fonte)

    elif active_tab_id == "configuracoes":
        config_x = LARGURA_TELA // 2 - 150 # Centered for checkboxes
        config_y = content_y_start # Start below the tabs

        # Draw checkboxes
        checkbox_terreno.rect.topleft = (config_x, config_y)
        checkbox_terreno.desenhar(tela)
        checkbox_auto.rect.topleft = (config_x, config_y + 40)
        checkbox_auto.desenhar(tela)
        checkbox_chefe.rect.topleft = (config_x, config_y + 80)
        checkbox_chefe.desenhar(tela)
        checkbox_autoplay.rect.topleft = (config_x, config_y + 120)
        checkbox_autoplay.desenhar(tela)
        checkbox_mapa_custom.rect.topleft = (config_x, config_y + 160)
        checkbox_mapa_custom.desenhar(tela)
        checkbox_campanha.rect.topleft = (config_x, config_y + 200)
        checkbox_campanha.desenhar(tela)
        checkbox_limitadores.rect.topleft = (config_x, config_y + 240)
        checkbox_limitadores.desenhar(tela)
        
        # Draw volume controls separately
        y_volume = config_y + 280 # Below limiters checkbox
        tela.blit(fonte.render(f"Volume SFX: {int(volume_sfx * 100)}%", True, COR_TEXTO), (config_x, y_volume))
        botoes_ui['sfx_vol_down'].rect.topleft = (config_x + 200, y_volume)
        botoes_ui['sfx_vol_down'].update_hover(pygame.mouse.get_pos())
        botoes_ui['sfx_vol_down'].desenhar(tela, fonte)
        botoes_ui['sfx_vol_up'].rect.topleft = (config_x + 260, y_volume)
        botoes_ui['sfx_vol_up'].update_hover(pygame.mouse.get_pos())
        botoes_ui['sfx_vol_up'].desenhar(tela, fonte)

    # Iniciar Batalha button (always visible)
    botoes_ui['iniciar'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 60)
    botoes_ui['iniciar'].update_hover(pygame.mouse.get_pos())
    botoes_ui['iniciar'].desenhar(tela, fonte)
    
    # Editor de Mapas button (always visible)
    botoes_ui['editor_mapas'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 120)
    botoes_ui['editor_mapas'].update_hover(pygame.mouse.get_pos())
    botoes_ui['editor_mapas'].desenhar(tela, fonte)
    
    # Botão Voltar ao Menu Principal
    botoes_ui['voltar_menu'].rect.topleft = (20, 20)
    botoes_ui['voltar_menu'].update_hover(pygame.mouse.get_pos())
    botoes_ui['voltar_menu'].desenhar(tela, fonte)

def setup_menu_principal_ui():
    fonte_menu = pygame.font.Font(None, 36)
    botoes = {}
    
    largura_btn = 600
    altura_btn = 80
    x_centro = LARGURA_TELA // 2 - largura_btn // 2
    y_start = 250
    espacamento = 100
    
    botoes['nova_batalha'] = Botao(x_centro, y_start, largura_btn, altura_btn, "NOVA BATALHA", fonte_menu, "Inicie uma simulação de combate tático.", icone=True, cor_fundo=COR_BOTAO_MENU)
    botoes['gerenciar'] = Botao(x_centro, y_start + espacamento, largura_btn, altura_btn, "GERENCIAR RECRUTAS", fonte_menu, "Equipe seus criminosos e heróis caídos.", icone=True, cor_fundo=COR_BOTAO_MENU)
    botoes['bestiario'] = Botao(x_centro, y_start + espacamento * 2, largura_btn, altura_btn, "BESTIÁRIO DO VAZIO", fonte_menu, "Dados sobre criaturas e anomalias.", icone=True, cor_fundo=COR_BOTAO_MENU)
    
    # Opções e Sair lado a lado
    largura_pequeno = 290
    botoes['opcoes'] = Botao(x_centro, y_start + espacamento * 3, largura_pequeno, altura_btn, "OPÇÕES", fonte_menu, icone=True, cor_fundo=COR_BOTAO_MENU)
    botoes['sair'] = Botao(x_centro + 310, y_start + espacamento * 3, largura_pequeno, altura_btn, "SAIR", fonte_menu, icone=True, cor_fundo=COR_BOTAO_MENU)
    
    return botoes

def setup_menu_ui():
    fonte_menu = pygame.font.Font(None, 28)
    
    config_times = {
        'A': {
            Guerreiro: 1, Mago: 1, Ladino: 1, Arqueiro: 1, Barbaro: 0, Clerigo: 0, Paladino: 0, Druida: 0, Bruxo: 0,
            Goblin: 0, Esqueleto: 0, Kobold: 0
        },
        'B': {
            Goblin: 2, Esqueleto: 2, Kobold: 2, ReiGoblin: 0, LordeLich: 0, DragaoAnciao: 0,
            Guerreiro: 0, Mago: 0, Ladino: 0, Arqueiro: 0, Barbaro: 0, Clerigo: 0, Paladino: 0, Druida: 0, Bruxo: 0
        },
        'classes': [
            (Guerreiro, "Guerreiro"), (Mago, "Mago"), (Ladino, "Ladino"), (Arqueiro, "Arqueiro"),
            (Barbaro, "Bárbaro"), (Clerigo, "Clérigo"), (Paladino, "Paladino"), (Druida, "Druida"), (Bruxo, "Bruxo"),
            (Goblin, "Goblin"), (Esqueleto, "Esqueleto"), (Kobold, "Kobold")
        ]
    }
    
    config_chefe = {'hp': 250, 'ataque': 5, 'ac': 16}
    
    botoes_ui = {}
    y_start = 150
    
    # Botões Time A
    x_time_a = LARGURA_TELA // 4
    for i, (classe, _) in enumerate(config_times['classes']):
        y_pos = y_start + i * 50
        botoes_ui[f'A_add_{i}'] = Botao(x_time_a + 60, y_pos, 30, 30, "+", fonte_menu)
        botoes_ui[f'A_sub_{i}'] = Botao(x_time_a + 100, y_pos, 30, 30, "-", fonte_menu)

    # Botões Time B
    x_time_b = LARGURA_TELA * 3 // 4
    for i, (classe, _) in enumerate(config_times['classes']):
        y_pos = y_start + i * 50
        botoes_ui[f'B_add_{i}'] = Botao(x_time_b + 60, y_pos, 30, 30, "+", fonte_menu)
        botoes_ui[f'B_sub_{i}'] = Botao(x_time_b + 100, y_pos, 30, 30, "-", fonte_menu)

    # Botões Chefe
    y_chefe = y_start + 160
    # HP
    botoes_ui['chefe_add_hp'] = Botao(x_time_b + 50, y_chefe, 30, 25, "+", fonte_menu)
    botoes_ui['chefe_sub_hp'] = Botao(x_time_b + 90, y_chefe, 30, 25, "-", fonte_menu)
    
    # AC (Next line, +30)
    botoes_ui['chefe_add_ac'] = Botao(x_time_b + 50, y_chefe + 30, 30, 25, "+", fonte_menu)
    botoes_ui['chefe_sub_ac'] = Botao(x_time_b + 90, y_chefe + 30, 30, 25, "-", fonte_menu)

    # Ataque (Next line, +60)
    botoes_ui['chefe_add_ataque'] = Botao(x_time_b + 50, y_chefe + 60, 30, 25, "+", fonte_menu)
    botoes_ui['chefe_sub_ataque'] = Botao(x_time_b + 90, y_chefe + 60, 30, 25, "-", fonte_menu)

    # Botões de Navegação de Boss
    # Image is at x_time_b - 50 to x_time_b + 50. Center Y approx y_start + 90 (150+40+50)
    botoes_ui['prev_boss'] = Botao(x_time_b - 120, y_start + 40, 40, 100, "<", fonte_menu)
    botoes_ui['next_boss'] = Botao(x_time_b + 70, y_start + 40, 40, 100, ">", fonte_menu)

    # Botões Gerais
    botoes_ui['iniciar'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA - 60, 200, 50, "INICIAR BATALHA", fonte_menu)
    botoes_ui['carregar_menu'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA - 180, 200, 40, "Carregar Jogo", fonte_menu)
    botoes_ui['editor_mapas'] = Botao(LARGURA_TELA // 2 - 100, ALTURA_TELA - 120, 200, 40, "Editor de Mapas", fonte_menu)
    botoes_ui['voltar_menu'] = Botao(20, 20, 100, 30, "Voltar", fonte_menu) # Botão para voltar ao menu principal
    
    # Botões de Volume
    botoes_ui['sfx_vol_down'] = Botao(0, 0, 40, 30, "-", fonte_menu)
    botoes_ui['sfx_vol_up'] = Botao(0, 0, 40, 30, "+", fonte_menu)

    checkbox_terreno = Checkbox(LARGURA_TELA // 2 - 100, y_start + 250, 20, "Gerar Terreno Aleatório", fonte_menu, checked=True)
    checkbox_auto = Checkbox(LARGURA_TELA // 2 - 100, y_start + 290, 20, "Auto-Batalha (IA vs IA)", fonte_menu)
    checkbox_chefe = Checkbox(LARGURA_TELA // 2 - 100, y_start + 330, 20, "Modo Chefe (Time B)", fonte_menu)
    checkbox_autoplay = Checkbox(LARGURA_TELA // 2 - 100, y_start + 370, 20, "Auto-Play (IA joga por você)", fonte_menu)
    checkbox_mapa_custom = Checkbox(LARGURA_TELA // 2 - 100, y_start + 410, 20, "Usar Mapa Customizado", fonte_menu)
    checkbox_campanha = Checkbox(LARGURA_TELA // 2 - 100, y_start + 450, 20, "Modo Campanha", fonte_menu)
    checkbox_limitadores = Checkbox(LARGURA_TELA // 2 - 100, y_start + 490, 20, "Adicionar Limitadores (Paredes)", fonte_menu)
    
    bosses = [
        {"classe": ReiGoblin, "nome": "Rei Goblin"},
        {"classe": LordeLich, "nome": "Lorde Lich"},
        {"classe": DragaoAnciao, "nome": "Dragão Ancião"}
    ]

    return config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, checkbox_mapa_custom, checkbox_campanha, checkbox_limitadores, bosses