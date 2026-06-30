import pygame
import math
from src.config import (
    LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_FUNDO, COR_LINHA, COR_HP_BAR_FUNDO, 
    COR_MANA_BAR, COR_ENERGIA_BAR,
    TIME_A, TIME_B, TAMANHO_CELULA, CORES_TERRENO, CORES_TIME, PROPRIEDADES_STATUS_EFEITO, 
    TERRENO_PAREDE, LARGURA_TABULEIRO, LARGURA_LOG, COR_BOTAO_HOVER, COR_BOTAO,
    COR_DANO, COR_CURA, ALTURA_BARRA_INICIATIVA
)
from src.personagens import (
    Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe, Paladino,
    ReiGoblin, LordeLich, DragaoAnciao, Druida, Bruxo
)
from src.utils import calcular_distancia, resource_path

# --- Constantes Isométricas ---
TILE_WIDTH = 26
TILE_HEIGHT = 13
ELEVATION_SCALE = 8
OFFSET_X = 300
OFFSET_Y = 200

def get_iso_coords(x, y, elevation=0, y_offset=0, theta=0.0):
    rx = x - 9.5
    ry = y - 9.5
    rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
    rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
    
    iso_x = (rot_x - rot_y) * (TILE_WIDTH // 2) + OFFSET_X
    iso_y = (rot_x + rot_y) * (TILE_HEIGHT // 2) - elevation * ELEVATION_SCALE + OFFSET_Y + y_offset
    return int(iso_x), int(iso_y)

def screen_to_grid(mx, my, motor):
    w = motor.tabuleiro.largura
    h = motor.tabuleiro.altura
    elev_grid = motor.tabuleiro.elevation_grid
    theta = getattr(motor, 'angulo_rotacao', 0.0)
    
    cells = []
    for y in range(h):
        for x in range(w):
            el = elev_grid[y][x]
            rx = x - 9.5
            ry = y - 9.5
            rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
            rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
            cx = (rot_x - rot_y) * (TILE_WIDTH // 2) + OFFSET_X
            cy = (rot_x + rot_y) * (TILE_HEIGHT // 2) - el * ELEVATION_SCALE + OFFSET_Y + ALTURA_BARRA_INICIATIVA
            proj_y = (rot_x + rot_y) * (TILE_HEIGHT // 2)
            cells.append((proj_y, x, y, cx, cy))
            
    cells.sort(key=lambda item: item[0], reverse=True)
    
    for _, x, y, cx, cy in cells:
        if (abs(mx - cx) * 2 / TILE_WIDTH) + (abs(my - cy) * 2 / TILE_HEIGHT) <= 1.0:
            return x, y
    return None

def draw_alpha_polygon(tela, color, points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x + 1
    h = max_y - min_y + 1
    
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    translated_points = [(p[0] - min_x, p[1] - min_y) for p in points]
    pygame.draw.polygon(surf, color, translated_points)
    tela.blit(surf, (min_x, min_y))

def desenhar_celula_tactica(tela, cx, cy, w, h, cor_base, cor_borda, estilo='movimento'):
    t = pygame.time.get_ticks()
    # Fator de pulsação suave
    pulso = (math.sin(t * 0.007) + 1.0) / 2.0  # 0.0 a 1.0
    
    # Calcular alpha pulsante
    alpha_base = cor_base[3] if len(cor_base) > 3 else 70
    alpha = int(alpha_base - 20 + 40 * pulso)
    alpha = max(20, min(230, alpha))
    
    fill_color = (cor_base[0], cor_base[1], cor_base[2], alpha)
    
    # 1. Desenhar o preenchimento semi-transparente
    pts_outer = [
        (cx, cy - h // 2),
        (cx + w // 2, cy),
        (cx, cy + h // 2),
        (cx - w // 2, cy)
    ]
    draw_alpha_polygon(tela, fill_color, pts_outer)
    
    # 2. Desenhar a borda externa brilhante com largura 2
    r_b, g_b, b_b = cor_borda[:3]
    cor_borda_pulsante = (
        max(0, min(255, int(r_b * (0.8 + 0.3 * pulso)))),
        max(0, min(255, int(g_b * (0.8 + 0.3 * pulso)))),
        max(0, min(255, int(b_b * (0.8 + 0.3 * pulso))))
    )
    pygame.draw.polygon(tela, cor_borda_pulsante, pts_outer, 2)
    
    # 3. Desenhar losango interno concêntrico de grade de energia
    w_inner = int(w * 0.7)
    h_inner = int(h * 0.7)
    pts_inner = [
        (cx, cy - h_inner // 2),
        (cx + w_inner // 2, cy),
        (cx, cy + h_inner // 2),
        (cx - w_inner // 2, cy)
    ]
    cor_inner = (cor_borda[0], cor_borda[1], cor_borda[2], int(40 + 20 * pulso))
    draw_alpha_polygon(tela, cor_inner, pts_inner)
    pygame.draw.polygon(tela, cor_borda, pts_inner, 1)

    # 4. Desenhar cantoneiras
    bracket_w = max(2, w // 7)
    bracket_h = max(1, h // 7)
    
    # Canto superior (cx, cy - h//2)
    pygame.draw.line(tela, (255, 255, 255), (cx, cy - h // 2), (cx - bracket_w, cy - h // 2 + bracket_h), 2)
    pygame.draw.line(tela, (255, 255, 255), (cx, cy - h // 2), (cx + bracket_w, cy - h // 2 + bracket_h), 2)
    
    # Canto inferior (cx, cy + h//2)
    pygame.draw.line(tela, (255, 255, 255), (cx, cy + h // 2), (cx - bracket_w, cy + h // 2 - bracket_h), 2)
    pygame.draw.line(tela, (255, 255, 255), (cx, cy + h // 2), (cx + bracket_w, cy + h // 2 - bracket_h), 2)
    
    # Canto esquerdo (cx - w//2, cy)
    pygame.draw.line(tela, (255, 255, 255), (cx - w // 2, cy), (cx - w // 2 + bracket_w, cy - bracket_h), 2)
    pygame.draw.line(tela, (255, 255, 255), (cx - w // 2, cy), (cx - w // 2 + bracket_w, cy + bracket_h), 2)
    
    # Canto direito (cx + w//2, cy)
    pygame.draw.line(tela, (255, 255, 255), (cx + w // 2, cy), (cx + w // 2 - bracket_w, cy - bracket_h), 2)
    pygame.draw.line(tela, (255, 255, 255), (cx + w // 2, cy), (cx + w // 2 - bracket_w, cy + bracket_h), 2)

def desenhar_cenario(tela, motor, game_images, y_offset, visibilidade_map):
    w = motor.tabuleiro.largura
    h = motor.tabuleiro.altura
    theta = getattr(motor, 'angulo_rotacao', 0.0)
    
    cells = []
    for y in range(h):
        for x in range(w):
            rx = x - 9.5
            ry = y - 9.5
            rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
            rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
            proj_y = (rot_x + rot_y) * (TILE_HEIGHT / 2)
            cells.append((proj_y, x, y))
            
    cells.sort(key=lambda item: item[0])

    for _, x, y in cells:
        visibilidade = visibilidade_map[y][x]
        if visibilidade == 0:
            cx, cy = get_iso_coords(x, y, 0, y_offset, theta)
            points = [
                (cx, cy - TILE_HEIGHT // 2),
                (cx + TILE_WIDTH // 2, cy),
                (cx, cy + TILE_HEIGHT // 2),
                (cx - TILE_WIDTH // 2, cy)
            ]
            pygame.draw.polygon(tela, (10, 10, 10), points)
            pygame.draw.polygon(tela, (25, 25, 25), points, 1)
            continue

        terreno = motor.tabuleiro.get_terrain_em(x, y)
        el = motor.tabuleiro.get_elevation_em(x, y)
        cor_base = CORES_TERRENO.get(terreno, COR_FUNDO)
        
        if visibilidade == 1:
            r, g, b = cor_base
            cor_base = (int(r * 0.45), int(g * 0.45), int(b * 0.45))
        
        cx, cy = get_iso_coords(x, y, el, y_offset, theta)
        thickness = el * ELEVATION_SCALE
        
        if terreno == TERRENO_PAREDE:
            thickness += 12
            cy -= 12
        
        top_points = [
            (cx, cy - TILE_HEIGHT // 2),
            (cx + TILE_WIDTH // 2, cy),
            (cx, cy + TILE_HEIGHT // 2),
            (cx - TILE_WIDTH // 2, cy)
        ]
        
        if thickness > 0:
            r, g, b = cor_base
            cor_left = (int(r * 0.7), int(g * 0.7), int(b * 0.7))
            cor_right = (int(r * 0.5), int(g * 0.5), int(b * 0.5))
            
            left_points = [
                (cx - TILE_WIDTH // 2, cy),
                (cx, cy + TILE_HEIGHT // 2),
                (cx, cy + TILE_HEIGHT // 2 + thickness),
                (cx - TILE_WIDTH // 2, cy + thickness)
            ]
            right_points = [
                (cx, cy + TILE_HEIGHT // 2),
                (cx + TILE_WIDTH // 2, cy),
                (cx + TILE_WIDTH // 2, cy + thickness),
                (cx, cy + TILE_HEIGHT // 2 + thickness)
            ]
            pygame.draw.polygon(tela, cor_left, left_points)
            pygame.draw.polygon(tela, cor_right, right_points)
            pygame.draw.polygon(tela, (20, 20, 20), left_points, 1)
            pygame.draw.polygon(tela, (20, 20, 20), right_points, 1)

        pygame.draw.polygon(tela, cor_base, top_points)
        pygame.draw.polygon(tela, (60, 60, 60) if visibilidade == 2 else (35, 35, 35), top_points, 1)

def desenhar_sprite(tela, personagem, rect, cor, game_images, mostrar=True, animacoes_sprites=None, estado_animacao=None):
    personagem_img_key = f"personagem_{personagem.__class__.__name__.lower()}"
    classe_nome = personagem.__class__.__name__

    if animacoes_sprites and classe_nome in animacoes_sprites:
        p_id = id(personagem)
        if estado_animacao and p_id in estado_animacao and estado_animacao[p_id]["andando"]:
            estado = estado_animacao[p_id]
            anim_data = animacoes_sprites[classe_nome]
            cols = anim_data["cols"]
            frame_idx = estado["direcao"] * cols + estado["quadro"]
            if frame_idx < len(anim_data["frames"]):
                frame = anim_data["frames"][frame_idx]
                if mostrar:
                    scaled = pygame.transform.scale(frame, (rect.width, rect.height))
                    tela.blit(scaled, rect.topleft)
                return

    if mostrar and personagem_img_key in game_images and game_images[personagem_img_key]:
        scaled_img = pygame.transform.scale(game_images[personagem_img_key], (rect.width, rect.height))
        tela.blit(scaled_img, rect.topleft)
    else:
        center = rect.center
        radius = rect.width // 2
        if isinstance(personagem, Chefe):
            cor_chefe = (80, 60, 90)
            points = [
                (center[0], rect.top - 5), (rect.right + 3, rect.top + 12),
                (rect.right - 5, rect.bottom + 3), (rect.left + 5, rect.bottom + 3),
                (rect.left - 3, rect.top + 12)
            ]
            pygame.draw.polygon(tela, cor_chefe, points)
            pygame.draw.polygon(tela, (200, 200, 220), points, 2)
        elif isinstance(personagem, ReiGoblin):
            pygame.draw.rect(tela, (0, 100, 0), rect, border_radius=3)
        elif isinstance(personagem, LordeLich):
            pygame.draw.rect(tela, (138, 43, 226), rect, border_radius=3)
        elif isinstance(personagem, DragaoAnciao):
            pygame.draw.rect(tela, (139, 0, 0), rect, border_radius=3)
        elif isinstance(personagem, Druida):
            if personagem.em_forma_de_urso:
                pygame.draw.rect(tela, (139, 69, 19), rect, border_radius=5)
            else:
                pygame.draw.rect(tela, (0, 100, 0), rect, border_radius=3)
        elif isinstance(personagem, Bruxo):
            pygame.draw.rect(tela, (75, 0, 130), rect, border_radius=3)
        elif isinstance(personagem, Guerreiro): pygame.draw.rect(tela, cor, rect, border_radius=3)
        elif isinstance(personagem, Mago): pygame.draw.circle(tela, cor, center, radius)
        elif isinstance(personagem, Ladino): pygame.draw.polygon(tela, cor, [(center[0], rect.top), (rect.left, rect.bottom), (rect.right, rect.bottom)])
        elif isinstance(personagem, Arqueiro): pygame.draw.polygon(tela, cor, [(center[0], rect.top), (rect.right, center[1]), (center[0], rect.bottom), (rect.left, center[1])])
        elif isinstance(personagem, Barbaro): pygame.draw.polygon(tela, cor, [(rect.left + radius * 0.5, rect.top), (rect.right - radius * 0.5, rect.top), (rect.right, center[1]), (rect.right - radius * 0.5, rect.bottom), (rect.left + radius * 0.5, rect.bottom), (rect.left, center[1])])
        elif isinstance(personagem, Clerigo):
            pygame.draw.rect(tela, cor, (rect.left + radius * 0.4, rect.top, radius, rect.height))
            pygame.draw.rect(tela, cor, (rect.left, rect.top + radius * 0.4, rect.width, radius))
        elif isinstance(personagem, Paladino):
            points = [
                (center[0], rect.top), (rect.right, center[1]),
                (center[0], rect.bottom), (rect.left, center[1])
            ]
            pygame.draw.polygon(tela, cor, points)
        else: pygame.draw.rect(tela, cor, rect)

def desenhar_personagens(tela, motor, fonte, personagem_ativo, tick, animacao_atual, imagens, offset_y, visibilidade_map=None, mostrar=True, animacoes_sprites=None, estado_animacao=None):
    theta = getattr(motor, 'angulo_rotacao', 0.0)
    
    # Dead characters first
    for p in motor.combatentes:
        if not p.esta_vivo:
            if visibilidade_map and visibilidade_map[p.pos_y][p.pos_x] != 2: continue

            cx, cy = get_iso_coords(p.pos_x, p.pos_y, p.elevacao, offset_y, theta)
            pygame.draw.line(tela, (100, 0, 0), (cx - 10, cy - 5), (cx + 10, cy + 5), 3)
            pygame.draw.line(tela, (100, 0, 0), (cx + 10, cy - 5), (cx - 10, cy + 5), 3)
            pygame.draw.circle(tela, (50, 50, 50), (cx, cy), 6)

    # Alive characters sorted by visual Y (back-to-front sorting)
    alive_characters = []
    for p in motor.combatentes:
        if p.esta_vivo:
            if visibilidade_map and visibilidade_map[p.pos_y][p.pos_x] != 2: continue
            
            if animacao_atual and animacao_atual['tipo'] == 'movimento' and animacao_atual['personagem'] == p:
                progresso = animacao_atual['progresso']
                start_el = motor.tabuleiro.get_elevation_em(animacao_atual['start_pos'][0], animacao_atual['start_pos'][1])
                start_x, start_y = get_iso_coords(animacao_atual['start_pos'][0], animacao_atual['start_pos'][1], start_el, offset_y, theta)
                end_x, end_y = get_iso_coords(p.pos_x, p.pos_y, p.elevacao, offset_y, theta)
                
                curr_x = start_x + (end_x - start_x) * progresso
                curr_y = start_y + (end_y - start_y) * progresso
                curr_y -= math.sin(progresso * math.pi) * 15
                proj_y = curr_y
                rect = pygame.Rect(curr_x - 15, curr_y - 25, 30, 30)
            else:
                cx, cy = get_iso_coords(p.pos_x, p.pos_y, p.elevacao, offset_y, theta)
                proj_y = cy
                rect = pygame.Rect(cx - 15, cy - 25, 30, 30)
                
            alive_characters.append((proj_y, p, rect))
            
    alive_characters.sort(key=lambda item: item[0])
    atacante_animacao = animacao_atual['atacante'] if animacao_atual and 'atacante' in animacao_atual else None

    for _, p, rect in alive_characters:
        cor = CORES_TIME.get(p.time, (200, 200, 200))
        if hasattr(p, 'dano_timer') and p.dano_timer > 0:
            fator = p.dano_timer / 15.0
            cor = (int(cor[0]*(1-fator) + 255*fator), int(cor[1]*(1-fator) + 50*fator), int(cor[2]*(1-fator) + 50*fator))
            p.dano_timer -= 1

        if p != atacante_animacao:
            if p == personagem_ativo and not animacao_atual:
                escala = 1.0 + 0.15 * abs(math.sin(tick * 0.1))
                largura, altura = int(30 * escala), int(30 * escala)
                sprite_rect = pygame.Rect(rect.centerx - largura // 2, rect.centery - altura // 2, largura, altura)
                desenhar_sprite(tela, p, sprite_rect, cor, imagens, mostrar, animacoes_sprites, estado_animacao)
            else:
                desenhar_sprite(tela, p, rect, cor, imagens, mostrar, animacoes_sprites, estado_animacao)

            if p.status_efeitos:
                status_x_offset = 0
                for efeito in p.status_efeitos:
                    prop = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome)
                    if prop:
                        cor_status = prop.get("cor", (255, 255, 255))
                        status_rect = pygame.Rect(rect.right - 6 - status_x_offset, rect.top + 2, 6, 6)
                        pygame.draw.rect(tela, cor_status, status_rect)
                        status_x_offset += 8
        else:
            progresso = animacao_atual['progresso']
            alvo = animacao_atual.get('alvo')
            if animacao_atual['tipo'] == 'ataque' and p.alcance == 1 and alvo:
                p_inicial = pygame.Vector2(rect.center)
                alvo_cx, alvo_cy = get_iso_coords(alvo.pos_x, alvo.pos_y, alvo.elevacao, offset_y, theta)
                p_final = pygame.Vector2(alvo_cx, alvo_cy - 10)
                pos_interp = p_inicial.lerp(p_final, progresso * 2) if progresso <= 0.5 else p_final.lerp(p_inicial, (progresso - 0.5) * 2)
                rect.center = pos_interp
            desenhar_sprite(tela, p, rect, cor, imagens, mostrar, animacoes_sprites, estado_animacao)

        hp_percent = p.hp_atual / p.hp_max
        hp_bar_bg = pygame.Rect(rect.left, rect.top - 8, 30, 4)
        pygame.draw.rect(tela, (30, 30, 30), hp_bar_bg)
        hp_color = (60, 200, 60) if hp_percent > 0.5 else (200, 200, 60) if hp_percent > 0.25 else (200, 60, 60)
        hp_bar_fg = pygame.Rect(rect.left, rect.top - 8, int(30 * hp_percent), 4)
        pygame.draw.rect(tela, hp_color, hp_bar_fg)
        pygame.draw.rect(tela, (0, 0, 0), hp_bar_bg, 1)

        bar_y = rect.top - 4
        if p.mana_max > 0:
            mana_percent = p.mana_atual / p.mana_max
            mana_bar_fundo = pygame.Rect(rect.left, bar_y, 30, 2)
            mana_bar_frente = pygame.Rect(rect.left, bar_y, int(30 * mana_percent), 2)
            pygame.draw.rect(tela, COR_HP_BAR_FUNDO, mana_bar_fundo)
            pygame.draw.rect(tela, COR_MANA_BAR, mana_bar_frente)
            bar_y += 3
        
        if p.energia_max > 0:
            energia_percent = p.energia_atual / p.energia_max
            energia_bar_fundo = pygame.Rect(rect.left, bar_y, 30, 2)
            energia_bar_frente = pygame.Rect(rect.left, bar_y, int(30 * energia_percent), 2)
            pygame.draw.rect(tela, COR_HP_BAR_FUNDO, energia_bar_fundo)
            pygame.draw.rect(tela, COR_ENERGIA_BAR, energia_bar_frente)

        level_render = fonte.render(str(p.nivel), True, COR_TEXTO)
        pygame.draw.circle(tela, (0,0,0), (rect.left + 3, rect.top + 3), 6)
        tela.blit(level_render, (rect.left, rect.top - 3))

def desenhar_pre_visualizacao_ataque(tela, motor, hovered_enemy, game_images, y_offset):
    if not hovered_enemy:
        return
    theta = getattr(motor, 'angulo_rotacao', 0.0)

    for p in motor.combatentes:
        if p.esta_vivo and p.time == TIME_A:
            if calcular_distancia(p, hovered_enemy) <= p.alcance:
                cx, cy = get_iso_coords(p.pos_x, p.pos_y, p.elevacao, y_offset, theta)
                desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (255, 200, 0, 60), (255, 215, 0), estilo='ataque')

def desenhar_alcance_movimento(tela, motor, personagem_ativo, y_offset):
    if not personagem_ativo or personagem_ativo.time != TIME_A:
        return
    theta = getattr(motor, 'angulo_rotacao', 0.0)

    movimentos_validos = motor.get_movimento_valido(personagem_ativo)
    for x, y in movimentos_validos:
        el = motor.tabuleiro.get_elevation_em(x, y)
        cx, cy = get_iso_coords(x, y, el, y_offset, theta)
        desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (0, 100, 255, 50), (0, 180, 255), estilo='movimento')

def desenhar_alcance_habilidade(tela, motor, personagem_ativo, habilidade_key, y_offset, mouse_pos=None):
    tiles, tipo = motor.get_alcance_habilidade(personagem_ativo, habilidade_key)
    theta = getattr(motor, 'angulo_rotacao', 0.0)
    
    for x, y in tiles:
        el = motor.tabuleiro.get_elevation_em(x, y)
        cx, cy = get_iso_coords(x, y, el, y_offset, theta)
        desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (138, 43, 226, 60), (180, 120, 255), estilo='habilidade')
        
    if mouse_pos:
        grid_pos = screen_to_grid(mouse_pos[0], mouse_pos[1], motor)
        if grid_pos:
            gx, gy = grid_pos
            if (gx, gy) in tiles:
                dados = personagem_ativo.habilidades[habilidade_key]
                raio = dados.get('area', 0)
                if raio > 0:
                     for dy in range(-raio, raio + 1):
                          for dx in range(-raio, raio + 1):
                              tx, ty = gx + dx, gy + dy
                              if 0 <= tx < 20 and 0 <= ty < 20:
                                  el = motor.tabuleiro.get_elevation_em(tx, ty)
                                  cx, cy = get_iso_coords(tx, ty, el, y_offset, theta)
                                  desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (255, 100, 0, 70), (255, 150, 0), estilo='ataque')

def desenhar_barra_iniciativa(tela, ordem_de_combate, personagem_ativo, game_images, mostrar=True):
    BARRA_ALTURA = 80 
    SPRITE_SIZE = 50 
    SPRITE_PADDING = 20 
    
    pygame.draw.rect(tela, (20, 20, 30), (0, 0, LARGURA_TELA, BARRA_ALTURA))
    pygame.draw.line(tela, COR_LINHA, (0, BARRA_ALTURA), (LARGURA_TELA, BARRA_ALTURA), 2)

    x_offset = SPRITE_PADDING
    for personagem in ordem_de_combate:
        if not personagem.esta_vivo:
            continue
        
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, (255, 255, 0, 150), (x_offset - 4, BARRA_ALTURA // 2 - SPRITE_SIZE // 2 - 4, SPRITE_SIZE + 8, SPRITE_SIZE + 8), border_radius=5)

        sprite_rect = pygame.Rect(x_offset, BARRA_ALTURA // 2 - SPRITE_SIZE // 2, SPRITE_SIZE, SPRITE_SIZE)
        cor = CORES_TIME.get(personagem.time, (200, 200, 200))
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images, mostrar)
        
        x_offset += SPRITE_SIZE + SPRITE_PADDING

def desenhar_ordem_iniciativa(tela, fonte, ordem, personagem_ativo, game_images, mostrar=True): 
    area_iniciativa = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 250, LARGURA_LOG, 100)
    s = pygame.Surface((area_iniciativa.width, area_iniciativa.height), pygame.SRCALPHA)
    s.fill((30, 20, 10, 230))
    tela.blit(s, area_iniciativa.topleft)
    
    pygame.draw.rect(tela, (218, 165, 32), area_iniciativa, 3, border_radius=5)
    titulo_render = fonte.render("Ordem de Iniciativa:", True, (255, 215, 0))
    tela.blit(titulo_render, (area_iniciativa.x + 10, area_iniciativa.y + 5))
    
    x_offset = area_iniciativa.x + 10
    y_offset = area_iniciativa.y + 30
    
    for personagem in ordem:
        if not personagem.esta_vivo:
            continue
            
        cor = CORES_TIME.get(personagem.time)
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, COR_BOTAO_HOVER, (x_offset - 2, y_offset - 2, 24, 24), border_radius=4)

        sprite_rect = pygame.Rect(x_offset, y_offset, 20, 20)
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images, mostrar)
        
        x_offset += 25
        if x_offset > area_iniciativa.right - 25:
            x_offset = area_iniciativa.x + 10
            y_offset += 25

def desenhar_projeteis_e_efeitos(tela, animacao_atual, y_offset, game_images, theta=0.0):
    if not animacao_atual: return
    progresso = animacao_atual['progresso']
    
    if animacao_atual['tipo'] == 'ataque':
        atacante = animacao_atual['atacante']
        alvo = animacao_atual.get('alvo')
        if not alvo: return

        start_x, start_y = get_iso_coords(atacante.pos_x, atacante.pos_y, atacante.elevacao, y_offset, theta)
        end_x, end_y = get_iso_coords(alvo.pos_x, alvo.pos_y, alvo.elevacao, y_offset, theta)
        
        start_pos = pygame.Vector2(start_x, start_y - 10)
        end_pos = pygame.Vector2(end_x, end_y - 10)

        if progresso <= 0.5:
            pos_interp = start_pos.lerp(end_pos, progresso * 2)
            if isinstance(atacante, Arqueiro):
                vetor_direcao = (end_pos - start_pos).normalize() if (end_pos - start_pos).length() > 0 else pygame.Vector2(1, 0)
                ponta = pos_interp
                base1 = pos_interp - vetor_direcao * 15 + vetor_direcao.rotate(90) * 4
                base2 = pos_interp - vetor_direcao * 15 - vetor_direcao.rotate(90) * 4
                pygame.draw.line(tela, (139, 69, 19), pos_interp, pos_interp - vetor_direcao * 15, 2)
                pygame.draw.polygon(tela, (200, 200, 200), [ponta, base1, base2])
            elif animacao_atual.get('habilidade') == 'raio_de_gelo':
                raio = 5 + 3 * math.sin(progresso * 20)
                pygame.draw.circle(tela, (173, 216, 230), (int(pos_interp.x), int(pos_interp.y)), int(raio))
            elif atacante.alcance > 1:
                pygame.draw.circle(tela, (255, 255, 0), (int(pos_interp.x), int(pos_interp.y)), 5)
        
        if atacante.alcance == 1 and progresso > 0.4 and progresso < 0.8:
            meio_anim = (progresso - 0.4) / 0.4
            ponto1 = end_pos + pygame.Vector2(-15, -15).lerp(pygame.Vector2(15, 15), meio_anim)
            ponto2 = end_pos + pygame.Vector2(15, -15).lerp(pygame.Vector2(-15, 15), meio_anim)
            pygame.draw.line(tela, (255, 255, 255), (int(ponto1.x), int(ponto1.y)), (int(ponto2.x), int(ponto2.y)), 3)

    elif animacao_atual['tipo'] == 'ataque_area':
        cx, cy = get_iso_coords(animacao_atual['x'], animacao_atual['y'], 0, y_offset, theta)
        raio_max = animacao_atual['raio'] * TILE_WIDTH
        raio_atual = raio_max * progresso
        
        surf = pygame.Surface((raio_atual * 2, raio_atual), pygame.SRCALPHA)
        cor = (255, 100, 0, int(200 * (1 - progresso)))
        pygame.draw.ellipse(surf, cor, (0, 0, raio_atual * 2, raio_atual))
        tela.blit(surf, (int(cx - raio_atual), int(cy - raio_atual // 2)))

def desenhar_log(tela, fonte, logs, max_altura, y_offset):
    area_log = pygame.Rect(LARGURA_TABULEIRO, y_offset, LARGURA_LOG, max_altura - y_offset)
    pygame.draw.rect(tela, (10, 10, 10), area_log)
    titulo = fonte.render("LOG DE COMBATE", True, COR_TEXTO)
    tela.blit(titulo, (LARGURA_TABULEIRO + 20, y_offset + 20))
    y_offset_texto = y_offset + 50
    for log_msg, cor in logs:
        if y_offset_texto + 20 > max_altura:
            break
        log_render = fonte.render(''.join(c for c in log_msg if c.isprintable()), True, cor)
        tela.blit(log_render, (LARGURA_TABULEIRO + 20, y_offset_texto))
        y_offset_texto += 20

def desenhar_info_personagem(tela, fonte, unidade, y_offset):
    area_info = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, ALTURA_TELA - 250)
    s = pygame.Surface((area_info.width, area_info.height), pygame.SRCALPHA)
    s.fill((40, 30, 20, 230))
    tela.blit(s, area_info.topleft)
    
    pygame.draw.rect(tela, (218, 165, 32), area_info, 3, border_radius=5)
    
    if not unidade:
        texto = fonte.render("Selecione uma unidade", True, (150, 150, 150))
        tela.blit(texto, (LARGURA_TABULEIRO + 20, 100))
        return

    y = 100
    nome_render = fonte.render(f"{unidade.nome} ({unidade.__class__.__name__})", True, (255, 215, 0))
    tela.blit(nome_render, (LARGURA_TABULEIRO + 20, y))
    y += 30
    
    stats = [
        f"HP: {unidade.hp_atual}/{unidade.hp_max}",
        f"AC: {unidade.ac}",
        f"Ataque: +{unidade.bonus_ataque}",
        f"Dano: {unidade.dado_dano[0]}d{unidade.dado_dano[1]} +{unidade.bonus_dano}",
        f"Movimento: {unidade.velocidade}",
        f"Alcance: {unidade.alcance}"
    ]
    
    for stat in stats:
        tela.blit(fonte.render(stat, True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y))
        y += 25
        
    y += 10
    if unidade.status_efeitos:
        tela.blit(fonte.render("Status:", True, (150, 150, 255)), (LARGURA_TABULEIRO + 20, y))
        y += 25
        for efeito in unidade.status_efeitos:
            cor_status = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome, {}).get("cor", COR_TEXTO)
            tela.blit(fonte.render(f"- {efeito.nome} ({efeito.duracao_restante} turnos)", True, cor_status), (LARGURA_TABULEIRO + 30, y))
            y += 25
    
    y += 15
    tela.blit(fonte.render("Habilidades:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 30
    if not unidade.cooldowns: tela.blit(fonte.render("  Nenhuma", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for nome, cd in unidade.cooldowns.items():
        if y + 25 > area_info.bottom:
            break
        status, cor = ("Pronta!", (60,220,60)) if cd == 0 else (f"{cd} turnos", (220,180,60))
        tela.blit(fonte.render(f"  - {nome.replace('_', ' ').title()}:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y))
        tela.blit(fonte.render(status, True, cor), (LARGURA_TABULEIRO + 200, y)); y += 30

def desenhar_inventario(tela, fonte, personagem, max_altura, y_offset, mouse_pos):
    area_inventario = pygame.Rect(LARGURA_TABULEIRO, y_offset, LARGURA_LOG, max_altura - y_offset)
    pygame.draw.rect(tela, (15, 15, 25), area_inventario) 
    
    y = y_offset + 20
    titulo = fonte.render(f"Inventário de {personagem.nome}", True, COR_TEXTO)
    tela.blit(titulo, (LARGURA_TABULEIRO + 20, y)); y += 40

    if not personagem.inventario:
        tela.blit(fonte.render("  Vazio", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
        return

    for i, item in enumerate(personagem.inventario):
        if y + 40 > max_altura:
            break
        
        item_rect = pygame.Rect(LARGURA_TABULEIRO + 20, y, LARGURA_LOG - 40, 35)
        cor_fundo_item = COR_BOTAO_HOVER if item_rect.collidepoint(mouse_pos) else COR_BOTAO
        pygame.draw.rect(tela, cor_fundo_item, item_rect, border_radius=5)
        
        nome_item_render = fonte.render(item.nome, True, COR_TEXTO)
        tela.blit(nome_item_render, (item_rect.x + 10, item_rect.y + 10))
        y += 40

def desenhar_feedback_jogador(tela, unidade, motor, y_offset):
    if not unidade: return
    x, y = unidade.pos_x, unidade.pos_y
    theta = getattr(motor, 'angulo_rotacao', 0.0)
    
    for r in range(-unidade.velocidade, unidade.velocidade + 1):
        for c in range(-unidade.velocidade, unidade.velocidade + 1):
            nx, ny = x + c, y + r
            if 0 <= nx < motor.tabuleiro.largura and 0 <= ny < motor.tabuleiro.altura:
                if motor.tabuleiro.get_personagem_em(nx, ny) is None and motor.tabuleiro.get_terrain_em(nx, ny) != TERRENO_PAREDE:
                    el = motor.tabuleiro.get_elevation_em(nx, ny)
                    cx, cy = get_iso_coords(nx, ny, el, y_offset, theta)
                    desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (0, 100, 255, 40), (0, 180, 255), estilo='movimento')

    for inimigo in motor.combatentes:
        if inimigo.time != unidade.time and inimigo.esta_vivo:
            dist = abs(x - inimigo.pos_x) + abs(y - inimigo.pos_y)
            if dist <= unidade.alcance:
                el = motor.tabuleiro.get_elevation_em(inimigo.pos_x, inimigo.pos_y)
                cx, cy = get_iso_coords(inimigo.pos_x, inimigo.pos_y, el, y_offset, theta)
                desenhar_celula_tactica(tela, cx, cy, TILE_WIDTH, TILE_HEIGHT, (255, 50, 0, 70), (255, 100, 100), estilo='ataque')

def desenhar_comandos(tela, fonte, y_offset, botoes, mouse_pos, personagem_ativo=None):
    skill_menu_open = any(k == 'voltar_skills' for k in botoes.keys())
    actions_menu_open = any(k == 'voltar_acoes' for k in botoes.keys())
    fonte_retro = pygame.font.SysFont("Courier New", 16, bold=True)

    for nome, botao in botoes.items():
        is_skill_btn = nome.startswith('habilidade_') or nome == 'voltar_skills'
        is_action_btn = nome.startswith('acao_') or nome == 'voltar_acoes'
        is_main_btn = nome in ['atacar', 'habilidade', 'item', 'acoes', 'proxima_acao']
        
        if skill_menu_open:
            if is_main_btn or is_action_btn: continue
        elif actions_menu_open:
            if is_main_btn or is_skill_btn: continue
        else:
            if is_skill_btn or is_action_btn: continue
            
        if is_main_btn or is_skill_btn or is_action_btn:
            rect = botao.rect
            hover = rect.collidepoint(mouse_pos)
            
            cor_fundo = (60, 40, 20) if not hover else (80, 60, 40)
            cor_borda = (218, 165, 32)
            
            pygame.draw.rect(tela, (20, 10, 5), rect.move(2, 2))
            pygame.draw.rect(tela, cor_fundo, rect)
            pygame.draw.rect(tela, cor_borda, rect, 2)
            pygame.draw.rect(tela, (40, 30, 10), rect.inflate(-6, -6), 1)
            
            cor_texto = (255, 255, 255) if hover else (200, 200, 180)
            txt_surf = fonte_retro.render(botao.texto, True, cor_texto)
            txt_rect = txt_surf.get_rect(center=rect.center)
            tela.blit(txt_surf, txt_rect)
        else:
            botao.desenhar(tela, fonte, mouse_pos)

    for nome, botao in botoes.items():
        if nome.startswith('habilidade_'):
             botao.desenhar(tela, fonte, mouse_pos)
             
    area_comandos = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 240 + y_offset, LARGURA_LOG, 240)
    s = pygame.Surface((area_comandos.width, area_comandos.height), pygame.SRCALPHA)
    s.fill((40, 30, 20, 230))
    tela.blit(s, area_comandos.topleft)
    
    pygame.draw.rect(tela, (218, 165, 32), area_comandos, 3, border_radius=5)
    
    y_offset_texto = ALTURA_TELA - 240 + y_offset
    comandos = [
        "Comandos:",
        "  - Clique em sua unidade para selecionar.",
        "  - Clique em azul para mover.",
        "  - Clique em vermelho para atacar.",
        "  - Clique fora para cancelar.",
        "  - Pressione Q / E para girar 90°."
    ]
    for cmd in comandos:
        cmd_render = fonte.render(cmd, True, COR_TEXTO)
        tela.blit(cmd_render, (LARGURA_TABULEIRO + 10, y_offset_texto))
        y_offset_texto += 20
        
    for botao in botoes.values():
        botao.update_hover(mouse_pos)
        botao.desenhar(tela, fonte, mouse_pos)

def desenhar_floating_texts(tela, floating_texts):
    for texto in floating_texts:
        texto.draw(tela)

def desenhar_feedback_invalido(tela, alpha, y_offset):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA - y_offset), pygame.SRCALPHA)
    overlay.fill((255, 0, 0, alpha))
    tela.blit(overlay, (0, y_offset))

def desenhar_itens_no_chao(tela, tabuleiro, y_offset, visibilidade_map, theta=0.0):
    for y in range(tabuleiro.altura):
        for x in range(tabuleiro.largura):
            if visibilidade_map[y][x] > 0: 
                item = tabuleiro.get_item_em(x, y)
                if item:
                    el = tabuleiro.get_elevation_em(x, y)
                    cx, cy = get_iso_coords(x, y, el, y_offset, theta)
                    if visibilidade_map[y][x] == 1:
                         pygame.draw.circle(tela, (120, 100, 0), (cx, cy), 5)
                    else:
                         pygame.draw.circle(tela, (255, 215, 0), (cx, cy), 5)
