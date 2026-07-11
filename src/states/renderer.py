import pygame
from src.config import *
from src.ui.desenho import (
    desenhar_menu_principal, desenhar_setup_batalha, desenhar_cenario, desenhar_personagens, desenhar_barra_iniciativa,
    desenhar_log, desenhar_comandos, desenhar_info_personagem, desenhar_pre_visualizacao_ataque,
    desenhar_floating_texts, desenhar_itens_no_chao, desenhar_dialogo, desenhar_tela_fim, desenhar_projeteis_e_efeitos,
    desenhar_mapa_mundo,
    desenhar_tela_level_up, desenhar_tela_salvando, desenhar_tela_carregando, desenhar_editor,
    desenhar_alcance_movimento, desenhar_alcance_habilidade, desenhar_interface_retro
)

class GameRenderer:
    def __init__(self, game):
        self.game = game

    def draw_elements(self, tick, mouse_pos, personagem_ativo=None):
        g = self.game
        g.tela.fill(COR_FUNDO)
        
        if g.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
            desenhar_menu_principal(g.tela, g.fonte_menu, g.botoes_menu_principal, mouse_pos)
        
        elif g.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
            from src.campanha import CAMPAIGN_DATA
            desenhar_mapa_mundo(g.tela, g.fonte_menu, g.botoes_ui, g.campaign_manager, g.campaign_manager.nivel_atual, g.imagens, mouse_pos)

        elif g.estado_jogo == ESTADO_JOGO_SETUP:
            desenhar_setup_batalha(g.tela, g.fonte_menu, g.config_times, g.config_chefe, g.botoes_ui, 
                                   g.checkbox_terreno, g.checkbox_auto, g.checkbox_chefe, g.checkbox_autoplay, 
                                   g.checkbox_mapa_custom, g.checkbox_campanha, g.checkbox_limitadores, g.checkbox_sprites, g.bosses, g.selected_boss_index, 
                                   g.imagens, g.volume_sfx, g.menu_tabs, g.active_tab_id, mouse_pos)
        
        elif g.estado_jogo == ESTADO_JOGO_COMBATE:
            desenhar_interface_retro(g.tela, g.fonte_menu)
            
            if g.motor:
                visibilidade = g.motor.visibilidade_map
                desenhar_cenario(g.tela, g.motor, g.imagens, ALTURA_BARRA_INICIATIVA, visibilidade)
                
                desenhar_itens_no_chao(g.tela, g.motor.tabuleiro, ALTURA_BARRA_INICIATIVA, visibilidade, g.angulo_rotacao)
                desenhar_personagens(g.tela, g.motor, g.fonte_personagem, personagem_ativo, tick, g.animacao_atual, g.imagens, ALTURA_BARRA_INICIATIVA, visibilidade, mostrar=g.sprites_visiveis, animacoes_sprites=g.animacoes_sprites, estado_animacao=g.estado_animacao_personagem)
                
                if g.habilidade_selecionada:
                    desenhar_alcance_habilidade(g.tela, g.motor, personagem_ativo, g.habilidade_selecionada, ALTURA_BARRA_INICIATIVA, mouse_pos)
                else:
                    desenhar_alcance_movimento(g.tela, g.motor, personagem_ativo, ALTURA_BARRA_INICIATIVA)
                    grid_pos = g.screen_to_grid(mouse_pos[0], mouse_pos[1])
                    hovered = g.motor.tabuleiro.get_personagem_em(grid_pos[0], grid_pos[1]) if grid_pos is not None else None
                    desenhar_pre_visualizacao_ataque(g.tela, g.motor, hovered, g.imagens, ALTURA_BARRA_INICIATIVA)

                desenhar_projeteis_e_efeitos(g.tela, g.animacao_atual, ALTURA_BARRA_INICIATIVA, g.imagens, g.angulo_rotacao)
                desenhar_barra_iniciativa(g.tela, g.motor.ordem_de_combate, personagem_ativo, g.imagens, mostrar=g.sprites_visiveis)
                desenhar_log(g.tela, g.fonte_log, g.log_combate, ALTURA_TELA, ALTURA_BARRA_INICIATIVA)
                
                if g.unidade_selecionada:
                    desenhar_info_personagem(g.tela, g.fonte_info, g.unidade_selecionada, ALTURA_BARRA_INICIATIVA)
                
                desenhar_comandos(g.tela, g.fonte_info, 0, g.botoes_combate, mouse_pos, personagem_ativo)
                desenhar_floating_texts(g.tela, g.floating_texts)
                
                desenhar_dialogo(g.tela, g.fonte_menu, g.dialogo, g.imagens)

                if g.motor.vencedor:
                    desenhar_tela_fim(g.tela, g.fonte_titulo, g.fonte_menu, g.motor.vencedor, g.botoes_fim, mouse_pos)
        
        elif g.estado_jogo == ESTADO_JOGO_CUTSCENE:
             g.cutscene_manager.desenhar(g.tela)
        
        elif g.estado_jogo == ESTADO_JOGO_LEVEL_UP:
             g.tela.fill((0, 0, 0)) 
             if g.personagem_level_up:
                 desenhar_tela_level_up(g.tela, g.fonte_titulo, g.fonte_menu, g.personagem_level_up, g.botoes_level_up, mouse_pos)

        
        elif g.estado_jogo == ESTADO_JOGO_DEV:
            g.tela.fill((10, 0, 0)) 
            texto_dev = g.fonte_titulo.render("MENU DO DESENVOLVEDOR", True, (255, 50, 50))
            g.tela.blit(texto_dev, (LARGURA_TELA // 2 - texto_dev.get_width() // 2, 80))
            
            for botao in g.botoes_dev.values():
                botao.desenhar(g.tela, g.fonte_menu, mouse_pos)

        elif g.estado_jogo == ESTADO_JOGO_DEV_CHAPTERS:
            g.tela.fill((10, 0, 20)) 
            texto_cap = g.fonte_titulo.render("SELEÇÃO DE FASES - DEV MODE", True, (150, 100, 255))
            g.tela.blit(texto_cap, (LARGURA_TELA // 2 - texto_cap.get_width() // 2, 40))
            
            for botao in g.botoes_capitulos.values():
                botao.desenhar(g.tela, g.fonte_menu, mouse_pos)

        elif g.estado_jogo == ESTADO_JOGO_EDITOR:
            import math
            tile_w = 26
            tile_h = 13
            offset_x = 300
            offset_y = 200 + ALTURA_BARRA_INICIATIVA
            w = len(g.editor_mapa[0]) if len(g.editor_mapa) > 0 else 20
            h = len(g.editor_mapa)
            theta = g.angulo_rotacao
            
            cells = []
            for y in range(h):
                for x in range(w):
                    rx = x - 9.5
                    ry = y - 9.5
                    rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
                    rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
                    proj_y = (rot_x + rot_y) * (tile_h / 2)
                    cells.append((proj_y, x, y))
                    
            cells.sort(key=lambda item: item[0])
            
            for _, x, y in cells:
                terreno = g.editor_mapa[y][x]
                rx = x - 9.5
                ry = y - 9.5
                rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
                rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
                cx = (rot_x - rot_y) * (tile_w // 2) + offset_x
                cy = (rot_x + rot_y) * (tile_h // 2) + offset_y
                
                points = [
                    (cx, cy - tile_h // 2),
                    (cx + tile_w // 2, cy),
                    (cx, cy + tile_h // 2),
                    (cx - tile_w // 2, cy)
                ]
                
                cor_terreno = CORES_TERRENO.get(terreno, (30, 30, 30))
                pygame.draw.polygon(g.tela, cor_terreno, points)
                pygame.draw.polygon(g.tela, (50, 50, 50), points, 1)
            
            area_editor = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, ALTURA_TELA)
            s = pygame.Surface((area_editor.width, area_editor.height), pygame.SRCALPHA)
            s.fill((40, 30, 20, 230))
            g.tela.blit(s, area_editor.topleft)
            pygame.draw.rect(g.tela, (218, 165, 32), area_editor, 3, border_radius=5)

            for nome, botao in g.botoes_editor.items():
                if nome == g.editor_terreno_selecionado:
                    pygame.draw.rect(g.tela, (255, 215, 0), botao.rect.inflate(4, 4), 2, border_radius=5)
                botao.desenhar(g.tela, g.fonte_menu, mouse_pos)
            
            for nome, botao in g.botoes_gerador.items():
                botao.update_hover(mouse_pos)
                botao.desenhar(g.tela, g.fonte_menu)
                
            largura_mapa_pixels = len(g.editor_mapa[0]) * TAMANHO_CELULA
            x_ui = max(LARGURA_TABULEIRO, largura_mapa_pixels)
            txt_x = x_ui + 130
            
            txt_w = g.fonte_menu.render(f"Largura: {g.map_gen_width}", True, COR_TEXTO)
            g.tela.blit(txt_w, (txt_x, 605))
            txt_h = g.fonte_menu.render(f"Altura: {g.map_gen_height}", True, COR_TEXTO)
            g.tela.blit(txt_h, (txt_x, 645))
            
            titulo = g.fonte_menu.render("Editor de Mapas", True, (255, 215, 0))
            g.tela.blit(titulo, (x_ui + 20, 20))

        elif g.estado_jogo == ESTADO_JOGO_CERCO:
            if hasattr(g, 'cerco_state') and g.cerco_state:
                g.cerco_state.update()
                g.cerco_state.draw(g.tela)

        elif g.estado_jogo == ESTADO_JOGO_CERCO_SETUP:
            if not g.cerco_setup_state:
                from .cerco_setup import CercoSetupState
                g.cerco_setup_state = CercoSetupState(g)
            g.cerco_setup_state.update()
            g.cerco_setup_state.draw(g.tela)

        elif g.estado_jogo == "castas_setup":
            if not getattr(g, 'castas_setup_state', None):
                from .castas_setup import CastasSetupState
                g.castas_setup_state = CastasSetupState(g)
            g.castas_setup_state.update()
            g.castas_setup_state.draw(g.tela)

        elif g.estado_jogo == "castas":
            if not getattr(g, 'castas_state', None):
                from .castas_setup import CastasSetupState
                g.castas_setup_state = CastasSetupState(g)
                g.estado_jogo = "castas_setup"
            else:
                g.castas_state.update()
                g.castas_state.draw(g.tela)

        elif g.estado_jogo == ESTADO_JOGO_DUELO:
            if getattr(g, 'duelo_state', None):
                g.duelo_state.update()
                g.duelo_state.draw(g.tela)
