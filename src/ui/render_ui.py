import pygame
from src.config import (
    LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_FUNDO, COR_LINHA, COR_BOTAO, COR_BOTAO_HOVER,
    COR_BORDA_DOURADA, COR_FUNDO_PEDRA, COR_FUNDO_RETRO, COR_TEXTO_RETRO, COR_TITULO_RETRO,
    RECT_BARRA_ACOES, RECT_PAINEL_INFO, RECT_LOG, RECT_INVENTARIO
)
from src.perks import PERKS
from src.utils import resource_path

# Helper para desenhar caixas estilo Retro
class PainelUI:
    @staticmethod
    def desenhar_painel(tela, rect, titulo=None, fonte_titulo=None):
        # Fundo
        pygame.draw.rect(tela, COR_FUNDO_RETRO, rect)
        pygame.draw.rect(tela, COR_FUNDO_PEDRA, rect, border_radius=5)
        
        # Borda Dourada Interna/Externa
        pygame.draw.rect(tela, COR_BORDA_DOURADA, rect, 4, border_radius=5)
        pygame.draw.rect(tela, (100, 80, 20), rect, 2, border_radius=5) # Sombra
        
        # Titulo
        if titulo and fonte_titulo:
            texto = fonte_titulo.render(titulo, True, COR_TITULO_RETRO)
            # Fundo Titulo
            bg_rect = texto.get_rect(topleft=(rect.x + 10, rect.y - 10))
            bg_rect.inflate_ip(10, 4)
            pygame.draw.rect(tela, COR_FUNDO_RETRO, bg_rect)
            pygame.draw.rect(tela, COR_BORDA_DOURADA, bg_rect, 2)
            tela.blit(texto, (rect.x + 15, rect.y - 12))

def desenhar_interface_retro(tela, fonte_titulo):
    # Desenhar os painéis fixos
    PainelUI.desenhar_painel(tela, RECT_PAINEL_INFO, "Info", fonte_titulo)
    PainelUI.desenhar_painel(tela, RECT_LOG, "Log", fonte_titulo)
    PainelUI.desenhar_painel(tela, RECT_INVENTARIO, "Inventário", fonte_titulo)
    PainelUI.desenhar_painel(tela, RECT_BARRA_ACOES, "Ações", fonte_titulo)

def draw_text_with_outline(surface, text, font, color, pos, outline_color=(0,0,0), outline_width=3):
    text_surface = font.render(text, True, color)
    
    # Outline (Draw multiple times around)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                outline_surface = font.render(text, True, outline_color)
                surface.blit(outline_surface, (pos[0] + dx, pos[1] + dy))
    
    # Main text
    surface.blit(text_surface, pos)

def desenhar_menu_principal(tela, fonte, botoes, mouse_pos=None):
    # Fundo
    try:
        bg_img = pygame.image.load(resource_path("assets/images/ui/menu_background.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (LARGURA_TELA, ALTURA_TELA))
        tela.blit(bg_img, (0, 0))
    except Exception as e:
        print(f"Erro ao carregar background: {e}")
        tela.fill((20, 20, 30))
    
    # Título "Cerco contra Isectum"
    # Estilo: Épico com Borda Grossa
    fonte_titulo = pygame.font.Font(None, 110)
    fonte_subtitulo = pygame.font.Font(None, 130)
    
    texto_titulo = "Cerco contra"
    texto_subtitulo = "Isectum"
    
    # Posições
    x_titulo = 80
    y_titulo = 80
    x_sub = 80
    y_sub = 160
    
    # Renderizar com Outline
    # "Cerco contra" - Dourado Pálido com borda preta
    draw_text_with_outline(tela, texto_titulo, fonte_titulo, (240, 230, 140), (x_titulo, y_titulo), outline_width=4)
    
    # "Isectum" - Laranja/Dourado Intenso com borda preta grossa
    draw_text_with_outline(tela, texto_subtitulo, fonte_subtitulo, (255, 140, 0), (x_sub, y_sub), outline_width=5)
    
    for botao in botoes.values():
        botao.desenhar(tela, fonte, mouse_pos)

def desenhar_dialogo(tela, fonte, dialogo_sistema, game_images):
    if not dialogo_sistema.ativo or not dialogo_sistema.fala_atual:
        return

    # Configurações da caixa de diálogo
    altura_caixa = 150
    margem = 20
    rect_caixa = pygame.Rect(margem, ALTURA_TELA - altura_caixa - margem, LARGURA_TELA - 2 * margem, altura_caixa)
    
    # Desenha fundo (Azul estilo FF)
    pygame.draw.rect(tela, (0, 0, 139), rect_caixa, border_radius=10) # DarkBlue
    pygame.draw.rect(tela, (255, 255, 255), rect_caixa, 4, border_radius=10) # Borda Branca
    
    nome_personagem, texto, retrato_key = dialogo_sistema.fala_atual
    
    # Desenha Retrato (se houver)
    x_texto = rect_caixa.x + 20
    if retrato_key:
        # Tenta carregar imagem do personagem se for uma chave de imagem válida
        img_key = f"personagem_{retrato_key.lower()}"
        if img_key in game_images and game_images[img_key]:
            img = game_images[img_key]
            scaled_img = pygame.transform.scale(img, (100, 100))
            tela.blit(scaled_img, (rect_caixa.x + 10, rect_caixa.y + 25))
            x_texto += 110 # Desloca texto para direita
    
    # Nome do Personagem
    nome_render = fonte.render(nome_personagem, True, (255, 215, 0)) # Dourado
    tela.blit(nome_render, (x_texto, rect_caixa.y + 15))
    
    # Texto (com efeito de máquina de escrever)
    # Quebra de linha simples
    palavras = texto.split(' ')
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste_linha = linha_atual + palavra + " "
        if fonte.size(teste_linha)[0] < rect_caixa.width - (x_texto - rect_caixa.x) - 20:
            linha_atual = teste_linha
        else:
            linhas.append(linha_atual)
            linha_atual = palavra + " "
    linhas.append(linha_atual)
    
    y_texto = rect_caixa.y + 50
    for linha in linhas:
        texto_render = fonte.render(linha, True, (255, 255, 255))
        tela.blit(texto_render, (x_texto, y_texto))
        y_texto += 25
        
    # Indicador de "Próximo" (piscando)
    if pygame.time.get_ticks() % 1000 < 500:
        pygame.draw.polygon(tela, (255, 255, 255), [
            (rect_caixa.right - 30, rect_caixa.bottom - 30),
            (rect_caixa.right - 20, rect_caixa.bottom - 30),
            (rect_caixa.right - 25, rect_caixa.bottom - 20)
        ])

def desenhar_setup_batalha(tela, fonte, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, checkbox_mapa_custom, checkbox_campanha, checkbox_limitadores, checkbox_sprites, bosses, selected_boss_index, game_images, volume_sfx, menu_tabs, active_tab_id, mouse_pos=None):
    # Fundo (Wallpaper)
    try:
        bg_img = pygame.image.load(resource_path("assets/images/ui/menu_background.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (LARGURA_TELA, ALTURA_TELA))
        # Escurecer um pouco para legibilidade
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        bg_img.blit(overlay, (0,0))
        tela.blit(bg_img, (0, 0))
    except:
        tela.fill(COR_FUNDO)
    
    # Título da Tela de Setup
    titulo_render = fonte.render("CONFIGURAÇÃO DE BATALHA", True, COR_TEXTO)
    tela.blit(titulo_render, (LARGURA_TELA // 2 - titulo_render.get_width() // 2, 30))

    # Draw Tabs
    tab_y_start = 80
    for tab in menu_tabs.values():
        tab.desenhar(tela, fonte, mouse_pos)

    # Base Y position for content, adjusted for tab height
    content_y_start = 200 # Aumentado para evitar sobreposição com as abas
    
    if active_tab_id == "times":
        # Layout Constants
        coluna_a_x = LARGURA_TELA // 4 - 150
        coluna_b_x = LARGURA_TELA * 3 // 4 - 150
        y_start = content_y_start
        espacamento_y = 45
        largura_linha = 350
        altura_linha = 40
        
        # --- Time A ---
        # Header
        header_rect_a = pygame.Rect(coluna_a_x, y_start - 40, largura_linha, 35)
        pygame.draw.rect(tela, (50, 30, 10), header_rect_a, border_radius=5)
        pygame.draw.rect(tela, (218, 165, 32), header_rect_a, 2, border_radius=5)
        tela.blit(fonte.render("Time A (Jogadores)", True, (255, 215, 0)), (coluna_a_x + 10, y_start - 35))

        for i, (classe, nome_classe) in enumerate(config_times['classes']):
            y_pos = y_start + i * espacamento_y
            row_rect = pygame.Rect(coluna_a_x, y_pos, largura_linha, altura_linha)
            
            # Row Interaction (Highlight)
            if row_rect.collidepoint(mouse_pos):
                pygame.draw.rect(tela, (60, 60, 60, 200), row_rect, border_radius=5)
                pygame.draw.rect(tela, (255, 215, 0), row_rect, 1, border_radius=5)
            else:
                cor_fundo_row = (30, 30, 30, 150) if i % 2 == 0 else (40, 40, 40, 150)
                s = pygame.Surface((largura_linha, altura_linha), pygame.SRCALPHA)
                s.fill(cor_fundo_row)
                tela.blit(s, (coluna_a_x, y_pos))
            
            # Name
            tela.blit(fonte.render(f"{nome_classe}", True, COR_TEXTO), (coluna_a_x + 10, y_pos + 10))
            
            # Count
            count = config_times['A'][classe]
            count_text = fonte.render(str(count), True, (255, 255, 255))
            tela.blit(count_text, (coluna_a_x + 280, y_pos + 10)) # Movido para direita

        # --- Time B ---
        # Header
        header_rect_b = pygame.Rect(coluna_b_x, y_start - 40, largura_linha, 35)
        pygame.draw.rect(tela, (50, 30, 10), header_rect_b, border_radius=5)
        pygame.draw.rect(tela, (218, 165, 32), header_rect_b, 2, border_radius=5)
        tela.blit(fonte.render("Time B (Inimigos)", True, (255, 50, 50)), (coluna_b_x + 10, y_start - 35))

        if not checkbox_chefe.checked:
            for i, (classe, nome_classe) in enumerate(config_times['classes']):
                y_pos = y_start + i * espacamento_y
                row_rect = pygame.Rect(coluna_b_x, y_pos, largura_linha, altura_linha)
                
                # Row Interaction (Highlight)
                if row_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(tela, (60, 60, 60, 200), row_rect, border_radius=5)
                    pygame.draw.rect(tela, (255, 215, 0), row_rect, 1, border_radius=5)
                else:
                    cor_fundo_row = (30, 30, 30, 150) if i % 2 == 0 else (40, 40, 40, 150)
                    s = pygame.Surface((largura_linha, altura_linha), pygame.SRCALPHA)
                    s.fill(cor_fundo_row)
                    tela.blit(s, (coluna_b_x, y_pos))
                
                # Name
                tela.blit(fonte.render(f"{nome_classe}", True, COR_TEXTO), (coluna_b_x + 10, y_pos + 10))
                
                # Count
                count = config_times['B'][classe]
                count_text = fonte.render(str(count), True, (255, 255, 255))
                tela.blit(count_text, (coluna_b_x + 280, y_pos + 10))
        else:
            # Boss Mode UI
            y_chefe = y_start
            
            # Boss Name Panel
            boss_panel = pygame.Rect(coluna_b_x, y_chefe, largura_linha, 200)
            pygame.draw.rect(tela, (20, 0, 0), boss_panel, border_radius=10)
            pygame.draw.rect(tela, (255, 0, 0), boss_panel, 2, border_radius=10)
            
            nome_chefe = bosses[selected_boss_index]["nome"]
            texto_chefe = fonte.render(nome_chefe, True, (255, 50, 50))
            tela.blit(texto_chefe, (coluna_b_x + 20, y_chefe + 20))
            
            # Update Boss Nav Buttons
            botoes_ui['prev_boss'].rect.topleft = (coluna_b_x + 20, y_chefe + 60)
            botoes_ui['prev_boss'].desenhar(tela, fonte, mouse_pos)
            
            botoes_ui['next_boss'].rect.topleft = (coluna_b_x + 200, y_chefe + 60)
            botoes_ui['next_boss'].desenhar(tela, fonte, mouse_pos)
            
            # Stats
            y_stats = y_chefe + 120
            tela.blit(fonte.render(f"HP: {config_chefe['hp']}", True, COR_TEXTO), (coluna_b_x + 20, y_stats))
            tela.blit(fonte.render(f"AC: {config_chefe['ac']}", True, COR_TEXTO), (coluna_b_x + 20, y_stats + 30))
            tela.blit(fonte.render(f"Atq: +{config_chefe['ataque']}", True, COR_TEXTO), (coluna_b_x + 20, y_stats + 60))
            
            # Update Boss Stat Buttons (Simplified positioning)
            botoes_ui['chefe_add_hp'].rect.topleft = (coluna_b_x + 150, y_stats - 5)
            botoes_ui['chefe_sub_hp'].rect.topleft = (coluna_b_x + 190, y_stats - 5)
            botoes_ui['chefe_add_hp'].desenhar(tela, fonte, mouse_pos)
            botoes_ui['chefe_sub_hp'].desenhar(tela, fonte, mouse_pos)
            
            # ... (Other stat buttons would need similar updates if visible)

    elif active_tab_id == "configuracoes":
        config_x = LARGURA_TELA // 2 - 150 # Centered for checkboxes
        config_y = content_y_start # Start below the tabs

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
        checkbox_sprites.rect.topleft = (config_x, config_y + 280)
        checkbox_sprites.desenhar(tela)
        
        # Draw volume controls separately
        y_volume = config_y + 320 # Below sprites checkbox
        tela.blit(fonte.render(f"Volume SFX: {int(volume_sfx * 100)}%", True, COR_TEXTO), (config_x, y_volume))
        botoes_ui['sfx_vol_down'].rect.topleft = (config_x + 200, y_volume)
        botoes_ui['sfx_vol_down'].desenhar(tela, fonte, mouse_pos)
        botoes_ui['sfx_vol_up'].rect.topleft = (config_x + 260, y_volume)
        botoes_ui['sfx_vol_up'].desenhar(tela, fonte, mouse_pos)
        
        # Resolução
        from ..config import RESOLUCOES as _RES
        y_res = y_volume + 50
        res_atual = f"{LARGURA_TELA}x{ALTURA_TELA}"
        tela.blit(fonte.render(f"Resolução: {res_atual}", True, COR_TEXTO), (config_x, y_res))
        
        y_res_btns = y_res + 30
        for i, (rw, rh) in enumerate(_RES):
            col = i % 4
            row = i // 4
            btn_name = f"res_{rw}x{rh}"
            if btn_name in botoes_ui:
                bx = config_x + col * 105
                by = y_res_btns + row * 36
                botoes_ui[btn_name].rect.topleft = (bx, by)
                botoes_ui[btn_name].desenhar(tela, fonte, mouse_pos)
                if rw == LARGURA_TELA and rh == ALTURA_TELA:
                    pygame.draw.rect(tela, (100, 200, 255), botoes_ui[btn_name].rect, 2, border_radius=3)

    # Iniciar Batalha button (always visible)
    botoes_ui['iniciar'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 60)
    botoes_ui['iniciar'].desenhar(tela, fonte, mouse_pos)
    
    # Editor de Mapas button (always visible)
    botoes_ui['editor_mapas'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 120)
    botoes_ui['editor_mapas'].desenhar(tela, fonte, mouse_pos)
    
    # Botão Voltar ao Menu Principal
    botoes_ui['voltar_menu'].rect.topleft = (20, 20)
    botoes_ui['voltar_menu'].desenhar(tela, fonte, mouse_pos)

def desenhar_tela_carregando(tela, fonte_titulo, fonte_menu, save_files, mouse_pos):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    tela.blit(overlay, (0, 0))

    titulo_render = fonte_titulo.render("Carregar Jogo", True, COR_TEXTO)
    tela.blit(titulo_render, titulo_render.get_rect(center=(LARGURA_TELA // 2, 100)))

    if not save_files:
        sem_saves_render = fonte_menu.render("Nenhum jogo salvo encontrado.", True, COR_TEXTO)
        tela.blit(sem_saves_render, sem_saves_render.get_rect(center=(LARGURA_TELA // 2, 200)))
        return

    for i, nome_arquivo in enumerate(save_files):
        botao_rect = pygame.Rect(LARGURA_TELA // 2 - 150, 150 + i * 50, 300, 40)
        cor_fundo = COR_BOTAO_HOVER if botao_rect.collidepoint(mouse_pos) else COR_BOTAO
        pygame.draw.rect(tela, cor_fundo, botao_rect, border_radius=5)
        
        nome_render = fonte_menu.render(nome_arquivo, True, COR_TEXTO)
        tela.blit(nome_render, nome_render.get_rect(center=botao_rect.center))

def desenhar_tela_salvando(tela, fonte_titulo, fonte_menu, nome_arquivo):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    tela.blit(overlay, (0, 0))

    titulo_render = fonte_titulo.render("Salvar Jogo", True, COR_TEXTO)
    tela.blit(titulo_render, titulo_render.get_rect(center=(LARGURA_TELA // 2, 200)))
    
    input_box = pygame.Rect(LARGURA_TELA // 2 - 150, 300, 300, 40)
    pygame.draw.rect(tela, (255, 255, 255), input_box, 2)

    nome_render = fonte_menu.render(nome_arquivo, True, COR_TEXTO)
    tela.blit(nome_render, (input_box.x + 5, input_box.y + 5))

    instrucao_render = fonte_menu.render("Pressione Enter para salvar", True, COR_TEXTO)
    tela.blit(instrucao_render, instrucao_render.get_rect(center=(LARGURA_TELA // 2, 400)))

def desenhar_tela_level_up(tela, fonte_titulo, fonte_menu, personagem, botoes, mouse_pos):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    tela.blit(overlay, (0, 0))

    titulo_render = fonte_titulo.render("LEVEL UP!", True, (255, 215, 0))
    tela.blit(titulo_render, titulo_render.get_rect(center=(LARGURA_TELA // 2, 80)))

    nome_render = fonte_menu.render(f"{personagem.nome} subiu para o nível {personagem.nivel}!", True, COR_TEXTO)
    tela.blit(nome_render, nome_render.get_rect(center=(LARGURA_TELA // 2, 140)))
    
    # Verifica se estamos no modo Perk (identificado pela presença de botões com 'perk_')
    tem_perks = any(k.startswith("perk_") for k in botoes.keys())
    
    if tem_perks:
        # --- Desenhar Linhas de Conexão ---
        classe_nome = personagem.classe_nome
        perks_list = PERKS.get(classe_nome, [])
        perk_buttons = {k.replace("perk_", ""): v for k, v in botoes.items() if k.startswith("perk_")}
        
        for perk in perks_list:
            btn_atual = perk_buttons.get(perk['id'])
            parent_id = perk.get('req_perk')
            
            if btn_atual and parent_id:
                btn_pai = perk_buttons.get(parent_id)
                if btn_pai:
                    # Cor da linha
                    cor_linha = (100, 100, 100) # Cinza (Locked)
                    if personagem.tem_perk(parent_id):
                        if personagem.tem_perk(perk['id']):
                            cor_linha = (255, 215, 0) # Dourado (Link Ativo)
                        elif personagem.pode_desbloquear_perk(perk):
                            cor_linha = (200, 200, 100) # Amarelo (Disponível)
                            
                    pygame.draw.line(tela, cor_linha, btn_pai.rect.center, btn_atual.rect.center, 4)

    # --- Desenhar Botões ---
    for nome, botao in botoes.items():
        botao.update_hover(mouse_pos)
        
        # Estilização especial para Perks
        if nome.startswith("perk_"):
            perk_id = nome.replace("perk_", "")
            
            # Determinar estado
            tem = personagem.tem_perk(perk_id)
            # Encontrar dados para checar 'pode' corretamente (precisa da lista)
            # Simplificação: checar texto do botão atual? Não, não é robusto.
            # Vamos buscar na lista PERKS novamente ou assumir logica simples
            pode = False
            # Busca lenta, mas segura para UI
            classe_nome = personagem.classe_nome
            perk_data = next((p for p in PERKS.get(classe_nome, []) if p['id'] == perk_id), None)
            if perk_data:
                pode = personagem.pode_desbloquear_perk(perk_data)

            # Cor da Borda/Glow
            if tem:
                cor_borda = (0, 255, 0) # Verde (Comprado)
                # Fundo um pouco esverdeado
                bg = pygame.Surface((botao.rect.width, botao.rect.height), pygame.SRCALPHA)
                bg.fill((0, 50, 0, 100))
                tela.blit(bg, botao.rect.topleft)
            elif pode:
                cor_borda = (255, 255, 0) # Amarelo (Disponível)
            else:
                cor_borda = (50, 50, 50) # Cinza escuro (Trancado)
                # Escurecer botão
                bg = pygame.Surface((botao.rect.width, botao.rect.height), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 150))
                tela.blit(bg, botao.rect.topleft)

            # Desenha o botão normal
            botao.desenhar(tela, fonte_menu)
            
            # Desenha borda de status POR CIMA
            pygame.draw.rect(tela, cor_borda, botao.rect, 3, border_radius=5)
            
            # Tooltip simples (se mouse em cima)
            if botao.rect.collidepoint(mouse_pos) and perk_data:
                desc = perk_data.get('descricao', '')
                req = f" (Lvl {perk_data['nivel_req']})"
                tooltip = fonte_menu.render(desc + req, True, (200, 200, 255))
                # Caixa do tooltip no topo ou rodapé
                bg_rect = tooltip.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA - 150))
                bg_rect.inflate_ip(20, 10)
                pygame.draw.rect(tela, (20, 20, 30), bg_rect, border_radius=5)
                pygame.draw.rect(tela, (255, 255, 255), bg_rect, 1, border_radius=5)
                tela.blit(tooltip, tooltip.get_rect(center=bg_rect.center))
                
        else:
            # Botões normais (Stats, Concluir)
            botao.desenhar(tela, fonte_menu)

def desenhar_tela_fim(tela, fonte_titulo, fonte_menu, vencedor, botoes, mouse_pos):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 255)) # Fundo preto sólido para cobrir o combate
    tela.blit(overlay, (0, 0))
    
    texto = f"O {vencedor} VENCEU!"
    texto_render = fonte_titulo.render(texto, True, (255, 215, 0)) # Usar fonte título e cor dourada
    tela.blit(texto_render, texto_render.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 - 50)))

    botoes['reiniciar'].update_hover(mouse_pos)
    botoes['reiniciar'].desenhar(tela, fonte_menu)
    botoes['voltar_menu'].update_hover(mouse_pos)
    botoes['voltar_menu'].desenhar(tela, fonte_menu)
