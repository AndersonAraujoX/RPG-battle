import pygame
from src.config import (
    LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_FUNDO, COR_LINHA, COR_BOTAO_HOVER,
    LARGURA_TABULEIRO, TAMANHO_CELULA, CORES_TERRENO
)
from src.utils import resource_path

def desenhar_editor(tela, fonte_menu, editor_mapa, botoes, terreno_selecionado, game_images, mouse_pos):
    tela.fill(COR_FUNDO)
    
    # Desenha o tabuleiro do editor
    for y, linha in enumerate(editor_mapa):
        for x, terreno in enumerate(linha):
            rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
            terreno_img_key = f"terreno_{terreno.lower()}"
            if terreno_img_key in game_images and game_images[terreno_img_key]:
                scaled_img = pygame.transform.scale(game_images[terreno_img_key], (TAMANHO_CELULA, TAMANHO_CELULA))
                tela.blit(scaled_img, rect.topleft)
            else:
                pygame.draw.rect(tela, CORES_TERRENO.get(terreno, COR_FUNDO), rect)
            pygame.draw.rect(tela, COR_LINHA, rect, 1)
            
    # Desenha a UI do editor na lateral
    largura_mapa_pixels = len(editor_mapa[0]) * TAMANHO_CELULA
    x_ui = max(LARGURA_TABULEIRO, largura_mapa_pixels)
    area_ui = pygame.Rect(x_ui, 0, LARGURA_TELA - x_ui, ALTURA_TELA)
    pygame.draw.rect(tela, (30, 30, 40), area_ui)
    
    titulo_render = fonte_menu.render("Editor de Mapas", True, COR_TEXTO)
    tela.blit(titulo_render, titulo_render.get_rect(center=(x_ui + (LARGURA_TELA - x_ui) // 2, 50)))

    for nome, botao in botoes.items():
        botao.update_hover(mouse_pos)
        # Highlight no terreno selecionado
        if nome == terreno_selecionado:
            pygame.draw.rect(tela, COR_BOTAO_HOVER, botao.rect.inflate(4, 4), border_radius=7)
        botao.desenhar(tela, fonte_menu)

def desenhar_mapa_mundo(tela, fonte, botoes, campaign_manager, nivel_atual, game_images, mouse_pos):
    # Fundo (Mapa Mundi)
    try:
        bg_img = pygame.image.load(resource_path("assets/images/ui/mapa_mundo.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (LARGURA_TELA, ALTURA_TELA))
        tela.blit(bg_img, (0, 0))
    except:
        tela.fill((20, 20, 30))
        texto = fonte.render("Mapa Mundi (Imagem não encontrada)", True, (255, 255, 255))
        tela.blit(texto, (LARGURA_TELA//2 - 100, ALTURA_TELA//2))

    # Título
    fonte_titulo = pygame.font.Font(None, 60)
    titulo = fonte_titulo.render("MAPA DA CAMPANHA", True, (255, 215, 0))
    titulo_rect = titulo.get_rect(center=(LARGURA_TELA // 2, 50))
    titulo_sombra = fonte_titulo.render("MAPA DA CAMPANHA", True, (0, 0, 0))
    tela.blit(titulo_sombra, (titulo_rect.x + 2, titulo_rect.y + 2))
    tela.blit(titulo, titulo_rect)

    # Desenhar Locais
    for local in campaign_manager.locais:
        cx, cy = local['pos']
        cor = local['cor']
        
        # Desenhar Marcador
        pygame.draw.circle(tela, cor, (cx, cy), 15)
        pygame.draw.circle(tela, (255, 255, 255), (cx, cy), 15, 2)
        
        # Nome do Local (se mouse perto)
        dist = ((cx - mouse_pos[0])**2 + (cy - mouse_pos[1])**2)**0.5
        if dist < 40:
            texto_local = fonte.render(local['nome'], True, (255, 255, 255))
            bg_rect = texto_local.get_rect(center=(cx, cy - 30))
            bg_rect.inflate_ip(10, 6)
            pygame.draw.rect(tela, (0, 0, 0, 180), bg_rect, border_radius=5)
            tela.blit(texto_local, texto_local.get_rect(center=(cx, cy - 30)))
            
            # Highlight
            pygame.draw.circle(tela, (255, 215, 0), (cx, cy), 20, 2)

    # Desenhar Jogador (Token/Boneco)
    px, py = campaign_manager.posicao_jogador
    
    # Tentar usar sprite do Guerreiro como avatar
    avatar_img = game_images.get('personagem_guerreiro')
    if avatar_img:
        # Escalar para um tamanho pequeno (ex: 40x40)
        avatar_scaled = pygame.transform.scale(avatar_img, (50, 50))
        # Centralizar na posição
        avatar_rect = avatar_scaled.get_rect(center=(int(px), int(py)))
        
        # Sombra
        pygame.draw.ellipse(tela, (0, 0, 0, 100), (avatar_rect.x, avatar_rect.bottom - 10, 50, 15))
        
        tela.blit(avatar_scaled, avatar_rect)
    else:
        # Fallback para Token
        pygame.draw.circle(tela, (0, 0, 0, 100), (int(px), int(py + 5)), 10)
        pygame.draw.circle(tela, (0, 191, 255), (int(px), int(py)), 10)
        pygame.draw.circle(tela, (255, 255, 255), (int(px), int(py)), 10, 2)
    
    # Desenhar Destino (se houver)
    if campaign_manager.destino_movimento:
        dx, dy = campaign_manager.destino_movimento
        pygame.draw.line(tela, (255, 255, 255, 100), (px, py), (dx, dy), 1)
        pygame.draw.circle(tela, (255, 255, 255, 100), (int(dx), int(dy)), 5, 1)

    # Botão Voltar
    botoes['voltar_menu'].rect.topleft = (20, 20)
    botoes['voltar_menu'].desenhar(tela, fonte, mouse_pos)
