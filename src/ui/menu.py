import pygame
import os
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
        logo_img = pygame.image.load(resource_path("assets/images/ui/logo.png")).convert_alpha()
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



def setup_menu_principal_ui():
    fonte_menu = pygame.font.Font(None, 48) # Fonte maior
    botoes = {}
    
    # Layout Principal em Grid (2 Colunas x 3 Linhas)
    # Total botoes: 6
    # Col 1: JOGAR, CONTINUAR, DEV
    # Col 2: NOVA CAMPANHA, OPÇÕES, SAIR
    
    w_btn = 300
    h_btn = 60
    gap_x = 40
    gap_y = 30
    
    y_start = 380 # Um pouco mais baixo por causa do logotipo
    
    col1_x = LARGURA_TELA // 2 - w_btn - gap_x // 2
    col2_x = LARGURA_TELA // 2 + gap_x // 2
    
    # Linha 1
    botoes['nova_batalha'] = Botao(col1_x, y_start, w_btn, h_btn, "JOGAR CERCO", fonte_menu, icone=False, cor_fundo=(50, 20, 80))
    botoes['nova_campanha'] = Botao(col2_x, y_start, w_btn, h_btn, "NOVA CAMPANHA", fonte_menu, icone=False, cor_fundo=COR_BOTAO_MENU)
    
    # Linha 2
    botoes['continuar'] = Botao(col1_x, y_start + h_btn + gap_y, w_btn, h_btn, "CONTINUAR", fonte_menu, icone=False, cor_fundo=COR_BOTAO_MENU)
    if not os.path.exists("campaign_save.json"):
        botoes['continuar'].desabilitado = True
        
    botoes['opcoes'] = Botao(col2_x, y_start + h_btn + gap_y, w_btn, h_btn, "OPÇÕES", fonte_menu, icone=False, cor_fundo=COR_BOTAO_MENU)

    # Linha 3
    botoes['dev'] = Botao(col1_x, y_start + (h_btn + gap_y)*2, w_btn, h_btn, "DEV TOOLS", fonte_menu, cor_fundo=(80, 20, 20))
    botoes['sair'] = Botao(col2_x, y_start + (h_btn + gap_y)*2, w_btn, h_btn, "SAIR", fonte_menu, icone=False, cor_fundo=COR_BOTAO_MENU)
    
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
    
    # Layout Constants
    painel_x = 100
    painel_y = 50
    painel_largura = LARGURA_TELA - 200
    painel_altura = ALTURA_TELA - 100
    
    coluna_a_x = painel_x + 50
    coluna_b_x = painel_x + painel_largura - 350 # Alinhado à direita do painel
    y_start_units = painel_y + 120
    espacamento_y = 45
    
    # Botões Time A e B (REMOVIDOS - Nova interação direta na lista)
    # for i, (classe, nome_classe) in enumerate(config_times['classes']):
    #     ...

    # Botões Chefe (Ajustados para ficar na coluna B quando ativo, ou ocultos)
    # Vamos manter a lógica de visibilidade no Game.handle_events/draw, mas posicionar aqui
    y_chefe = y_start_units # Começa no topo da lista
    
    # Botões de Navegação de Boss (Centralizados na coluna B)
    botoes_ui['prev_boss'] = Botao(coluna_b_x, y_chefe + 50, 40, 40, "<", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['next_boss'] = Botao(coluna_b_x + 200, y_chefe + 50, 40, 40, ">", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    
    # Stats do Chefe
    y_stats = y_chefe + 150
    botoes_ui['chefe_add_hp'] = Botao(coluna_b_x + 150, y_stats, 30, 25, "+", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['chefe_sub_hp'] = Botao(coluna_b_x + 190, y_stats, 30, 25, "-", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    
    botoes_ui['chefe_add_ac'] = Botao(coluna_b_x + 150, y_stats + 30, 30, 25, "+", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['chefe_sub_ac'] = Botao(coluna_b_x + 190, y_stats + 30, 30, 25, "-", fonte_menu, cor_fundo=COR_BOTAO_MENU)

    botoes_ui['chefe_add_ataque'] = Botao(coluna_b_x + 150, y_stats + 60, 30, 25, "+", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['chefe_sub_ataque'] = Botao(coluna_b_x + 190, y_stats + 60, 30, 25, "-", fonte_menu, cor_fundo=COR_BOTAO_MENU)

    # Botões Gerais (Rodapé)
    centro_x = LARGURA_TELA // 2
    botoes_ui['editor_mapas'] = Botao(centro_x - 120, painel_y + painel_altura - 130, 240, 50, "Editor de Mapas", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['iniciar'] = Botao(centro_x - 120, painel_y + painel_altura - 70, 240, 60, "INICIAR BATALHA", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    
    # Botão Voltar (Topo Esquerdo)
    botoes_ui['voltar_menu'] = Botao(20, 20, 100, 40, "Voltar", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    
    # Checkboxes (Aba Configurações - Centralizados)
    check_x = centro_x - 150
    y_check = y_start_units
    checkbox_terreno = Checkbox(check_x, y_check, 20, "Gerar Terreno Aleatório", fonte_menu, checked=True)
    checkbox_auto = Checkbox(check_x, y_check + 40, 20, "Auto-Batalha (IA vs IA)", fonte_menu)
    checkbox_chefe = Checkbox(check_x, y_check + 80, 20, "Modo Chefe (Time B)", fonte_menu)
    checkbox_autoplay = Checkbox(check_x, y_check + 120, 20, "Auto-Play (IA joga por você)", fonte_menu)
    checkbox_mapa_custom = Checkbox(check_x, y_check + 160, 20, "Usar Mapa Customizado", fonte_menu)
    checkbox_campanha = Checkbox(check_x, y_check + 200, 20, "Modo Campanha", fonte_menu)
    checkbox_limitadores = Checkbox(check_x, y_check + 240, 20, "Adicionar Limitadores", fonte_menu)
    
    # Volume Controls
    botoes_ui['sfx_vol_down'] = Botao(0, 0, 40, 40, "-", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['sfx_vol_up'] = Botao(0, 0, 40, 40, "+", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    
    # Resolução (Abaixo dos checkboxes)
    y_res = y_check + 280
    botoes_ui['res_800'] = Botao(check_x, y_res, 100, 30, "800x600", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['res_1024'] = Botao(check_x + 110, y_res, 100, 30, "1024x768", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['res_1280'] = Botao(check_x + 220, y_res, 100, 30, "1280x720", fonte_menu, cor_fundo=COR_BOTAO_MENU)
    botoes_ui['res_fullscreen'] = Botao(check_x, y_res + 40, 320, 30, "Salvar Resolução & Sair", fonte_menu, cor_fundo=COR_BOTAO_MENU) # Botão para aplicar? Não, melhor aplicar ao clicar.

    
    bosses = [
        {"classe": ReiGoblin, "nome": "Rei Goblin"},
        {"classe": LordeLich, "nome": "Lorde Lich"},
        {"classe": DragaoAnciao, "nome": "Dragão Ancião"}
    ]

    return config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, checkbox_mapa_custom, checkbox_campanha, checkbox_limitadores, bosses