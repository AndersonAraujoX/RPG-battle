import pygame
import math
from src.config import (
    LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_FUNDO, COR_LINHA, COR_HP_BAR_FUNDO, 
    COR_MANA_BAR, COR_ENERGIA_BAR,
    TIME_A, TIME_B, TAMANHO_CELULA, CORES_TERRENO, CORES_TIME, PROPRIEDADES_STATUS_EFEITO, 
    TERRENO_PAREDE, LARGURA_TABULEIRO, LARGURA_LOG, COR_BOTAO_HOVER, COR_BOTAO,
    COR_DANO, COR_CURA
)
from src.personagens import (
    Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe, Paladino,
    ReiGoblin, LordeLich, DragaoAnciao, Druida, Bruxo
)
from src.utils import calcular_distancia, resource_path

def desenhar_cenario(tela, motor, game_images, y_offset, visibilidade_map):
    # Crie superfícies para o nevoeiro uma vez para reutilização
    nevoeiro_visto = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    nevoeiro_visto.fill((0, 0, 0, 180))  # Cinza escuro para áreas já vistas
    nevoeiro_nao_visto = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA))
    nevoeiro_nao_visto.fill((0, 0, 0))    # Preto para áreas não exploradas

    for y in range(motor.tabuleiro.altura):
        for x in range(motor.tabuleiro.largura):
            rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
            
            visibilidade = visibilidade_map[y][x]

            if visibilidade == 0: # Não visto
                tela.blit(nevoeiro_nao_visto, rect.topleft)
                continue # Pula o resto do desenho para esta célula

            # Desenha o terreno
            terreno = motor.tabuleiro.get_terrain_em(x, y)
            terreno_img_key = f"terreno_{terreno.lower()}"
            if terreno_img_key in game_images and game_images[terreno_img_key]:
                scaled_img = pygame.transform.scale(game_images[terreno_img_key], (TAMANHO_CELULA, TAMANHO_CELULA))
                tela.blit(scaled_img, rect.topleft)
            else:
                pygame.draw.rect(tela, CORES_TERRENO.get(terreno, COR_FUNDO), rect)
            
            # Desenha a grade
            pygame.draw.rect(tela, COR_LINHA, rect, 1)

            if visibilidade == 1: # Visto, mas não na visão atual
                tela.blit(nevoeiro_visto, rect.topleft)

def desenhar_sprite(tela, personagem, rect, cor, game_images):
    personagem_img_key = f"personagem_{personagem.__class__.__name__.lower()}"
    if personagem_img_key in game_images and game_images[personagem_img_key]:
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
            pygame.draw.rect(tela, (0, 100, 0), rect, border_radius=3) # Dark Green
        elif isinstance(personagem, LordeLich):
            pygame.draw.rect(tela, (138, 43, 226), rect, border_radius=3) # BlueViolet
        elif isinstance(personagem, DragaoAnciao):
            pygame.draw.rect(tela, (139, 0, 0), rect, border_radius=3) # DarkRed
        elif isinstance(personagem, Druida):
            if personagem.em_forma_de_urso:
                pygame.draw.rect(tela, (139, 69, 19), rect, border_radius=5) # Brown for bear
            else:
                pygame.draw.rect(tela, (0, 100, 0), rect, border_radius=3) # Dark Green for normal form
        elif isinstance(personagem, Bruxo):
            pygame.draw.rect(tela, (75, 0, 130), rect, border_radius=3) # Indigo
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

def desenhar_personagens(tela, motor, fonte, personagem_ativo, tick, animacao_atual, imagens, offset_y, visibilidade_map=None):
    tabuleiro = motor.tabuleiro
    
    # Desenha personagens mortos (corpos) primeiro
    for p in motor.combatentes:
        if not p.esta_vivo:
            if visibilidade_map and visibilidade_map[p.pos_y][p.pos_x] != 2: continue # Only visible if in sight

            x, y = p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + offset_y
            pygame.draw.line(tela, (100, 0, 0), (x, y), (x + TAMANHO_CELULA, y + TAMANHO_CELULA), 3)
            pygame.draw.line(tela, (100, 0, 0), (x + TAMANHO_CELULA, y), (x, y + TAMANHO_CELULA), 3)
            pygame.draw.circle(tela, (50, 50, 50), (x + TAMANHO_CELULA // 2, y + TAMANHO_CELULA // 2), TAMANHO_CELULA // 2 - 2)

    personagens_desenhados = set()
    atacante_animacao = animacao_atual['atacante'] if animacao_atual and 'atacante' in animacao_atual else None
    
    # Desenha personagens vivos
    for p in motor.combatentes:
        if p.esta_vivo:
            if visibilidade_map and visibilidade_map[p.pos_y][p.pos_x] != 2: continue # Only visible if in sight

            x, y = p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + offset_y
            
            # Animação de movimento suave
            if animacao_atual and animacao_atual['tipo'] == 'movimento' and animacao_atual['personagem'] == p:
                progresso = animacao_atual['progresso']
                start_pos = pygame.Vector2(animacao_atual['start_pos'][0] * TAMANHO_CELULA, animacao_atual['start_pos'][1] * TAMANHO_CELULA + offset_y)
                end_pos = pygame.Vector2(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + offset_y)
                current_pos = start_pos.lerp(end_pos, progresso)
                rect = pygame.Rect(current_pos.x, current_pos.y, TAMANHO_CELULA, TAMANHO_CELULA)
            else:
                rect = pygame.Rect(x, y, TAMANHO_CELULA, TAMANHO_CELULA)

            if p != atacante_animacao:
                cor = CORES_TIME.get(p.time, (200, 200, 200))
                if hasattr(p, 'dano_timer') and p.dano_timer > 0:
                    fator = p.dano_timer / 15.0
                    cor = (int(cor[0]*(1-fator) + 255*fator), int(cor[1]*(1-fator) + 50*fator), int(cor[2]*(1-fator) + 50*fator))
                    p.dano_timer -= 1
                if p == personagem_ativo and not animacao_atual:
                    escala = 1.0 + 0.15 * abs(math.sin(tick * 0.1))
                    largura, altura = int(TAMANHO_CELULA * escala), int(TAMANHO_CELULA * escala)
                    sprite_rect = pygame.Rect(rect.centerx - largura // 2, rect.centery - altura // 2, largura, altura)
                    desenhar_sprite(tela, p, sprite_rect, cor, imagens)
                else:
                    desenhar_sprite(tela, p, rect, cor, imagens)
                personagens_desenhados.add(p)

                # Desenhar indicadores de status
                if p.status_efeitos:
                    status_x_offset = 0
                    for efeito in p.status_efeitos:
                        prop = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome)
                        if prop:
                            cor_status = prop.get("cor", (255, 255, 255))
                            status_rect = pygame.Rect(rect.right - 10 - status_x_offset, rect.top + 2, 8, 8)
                            pygame.draw.rect(tela, cor_status, status_rect)
                            icone = prop.get("icone")
                            if icone:
                                fonte_icone = pygame.font.Font(None, 10)
                                icone_render = fonte_icone.render(icone, True, COR_TEXTO)
                                icone_rect = icone_render.get_rect(center=status_rect.center)
                                tela.blit(icone_render, icone_rect)
                            status_x_offset += 10
        
    if atacante_animacao and atacante_animacao.esta_vivo:
        p = atacante_animacao
        rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + offset_y, TAMANHO_CELULA, TAMANHO_CELULA)
        progresso = animacao_atual['progresso']
        if animacao_atual['tipo'] == 'ataque' and p.alcance == 1:
            alvo = animacao_atual.get('alvo')
            if alvo:
                p_inicial = pygame.Vector2(rect.center)
                p_final = pygame.Vector2(alvo.pos_x * TAMANHO_CELULA + TAMANHO_CELULA//2, alvo.pos_y * TAMANHO_CELULA + TAMANHO_CELULA//2 + offset_y)
                pos_interp = p_inicial.lerp(p_final, progresso * 2) if progresso <= 0.5 else p_final.lerp(p_inicial, (progresso - 0.5) * 2)
                rect.center = pos_interp
        cor = CORES_TIME.get(p.time, (200, 200, 200))
        desenhar_sprite(tela, p, rect, cor, imagens)
        personagens_desenhados.add(p)
    
    for p in motor.combatentes:
        if p.esta_vivo and (visibilidade_map[p.pos_y][p.pos_x] == 2 or p.time == TIME_A):
            rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + offset_y, TAMANHO_CELULA, TAMANHO_CELULA)
            hp_percent = p.hp_atual / p.hp_max
            
            # HP Bar Background (Darker)
            hp_bar_bg = pygame.Rect(rect.left, rect.top - 8, TAMANHO_CELULA, 6)
            pygame.draw.rect(tela, (30, 30, 30), hp_bar_bg)
            
            # HP Bar Foreground
            hp_color = (60, 200, 60) if hp_percent > 0.5 else (200, 200, 60) if hp_percent > 0.25 else (200, 60, 60)
            hp_bar_fg = pygame.Rect(rect.left, rect.top - 8, int(TAMANHO_CELULA * hp_percent), 6)
            pygame.draw.rect(tela, hp_color, hp_bar_fg)
            
            # Border for HP Bar
            pygame.draw.rect(tela, (0, 0, 0), hp_bar_bg, 1)
            
            bar_y = rect.top - 2
            if p.mana_max > 0:
                mana_percent = p.mana_atual / p.mana_max
                mana_bar_fundo = pygame.Rect(rect.left, bar_y, TAMANHO_CELULA, 3)
                mana_bar_frente = pygame.Rect(rect.left, bar_y, int(TAMANHO_CELULA * mana_percent), 3)
                pygame.draw.rect(tela, COR_HP_BAR_FUNDO, mana_bar_fundo)
                pygame.draw.rect(tela, COR_MANA_BAR, mana_bar_frente)
                bar_y += 4
            
            if p.energia_max > 0:
                energia_percent = p.energia_atual / p.energia_max
                energia_bar_fundo = pygame.Rect(rect.left, bar_y, TAMANHO_CELULA, 3)
                energia_bar_frente = pygame.Rect(rect.left, bar_y, int(TAMANHO_CELULA * energia_percent), 3)
                pygame.draw.rect(tela, COR_HP_BAR_FUNDO, energia_bar_fundo)
                pygame.draw.rect(tela, COR_ENERGIA_BAR, energia_bar_frente)

            level_render = fonte.render(str(p.nivel), True, COR_TEXTO)
            pygame.draw.circle(tela, (0,0,0), (rect.left + 6, rect.top + 6), 8)
            tela.blit(level_render, (rect.left + 2, rect.top))

            if p.cooldowns:
                cooldown_x_offset = 0
                for i, (nome, cd) in enumerate(p.cooldowns.items()):
                    if p.cooldown_max.get(nome, 0) > 0:
                        angle = (cd / p.cooldown_max[nome]) * 2 * math.pi
                        rect_cooldown = pygame.Rect(rect.left + cooldown_x_offset, rect.bottom - 8, 8, 8)
                        pygame.draw.ellipse(tela, (50, 50, 50), rect_cooldown)
                        if angle > 0:
                            start_angle = math.pi / 2
                            end_angle = start_angle + angle
                            arc_surface = pygame.Surface((rect_cooldown.width, rect_cooldown.height), pygame.SRCALPHA)
                            pygame.draw.arc(arc_surface, (200, 200, 50, 200), (0,0,rect_cooldown.width, rect_cooldown.height), start_angle, end_angle, 4)
                            tela.blit(arc_surface, rect_cooldown.topleft)
                        cooldown_x_offset += 10

def desenhar_pre_visualizacao_ataque(tela, motor, hovered_enemy, game_images, y_offset):
    if not hovered_enemy:
        return

    highlight_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    highlight_surf.fill((255, 255, 0, 80)) # Yellow for highlight

    for p in motor.combatentes:
        if p.esta_vivo and p.time == TIME_A:
            if calcular_distancia(p, hovered_enemy) <= p.alcance:
                rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
                tela.blit(highlight_surf, rect.topleft)

def desenhar_alcance_movimento(tela, motor, personagem_ativo, y_offset):
    if not personagem_ativo or personagem_ativo.time != TIME_A:
        return

    movimentos_validos = motor.get_movimento_valido(personagem_ativo)
    
    highlight_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    highlight_surf.fill((0, 100, 255, 60)) # Azul com transparência
    border_color = (0, 150, 255)

    for x, y in movimentos_validos:
        rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
        tela.blit(highlight_surf, rect.topleft)
        pygame.draw.rect(tela, border_color, rect, 1)

def desenhar_alcance_habilidade(tela, motor, personagem_ativo, habilidade_key, y_offset, mouse_pos=None):
    tiles, tipo = motor.get_alcance_habilidade(personagem_ativo, habilidade_key)
    
    color = (255, 50, 50, 80)
    border_color = (255, 0, 0)
    
    highlight_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    highlight_surf.fill(color)
    
    for x, y in tiles:
        rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
        tela.blit(highlight_surf, rect.topleft)
        pygame.draw.rect(tela, border_color, rect, 1)
        
    if mouse_pos and mouse_pos[0] < LARGURA_TABULEIRO and mouse_pos[1] > y_offset:
        gx = mouse_pos[0] // TAMANHO_CELULA
        gy = (mouse_pos[1] - y_offset) // TAMANHO_CELULA
        
        if (gx, gy) in tiles:
            dados = personagem_ativo.habilidades[habilidade_key]
            raio = dados.get('area', 0)
            if raio > 0:
                 aoe_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
                 aoe_surf.fill((255, 200, 0, 100)) # Orange core
                 
                 for dy in range(-raio, raio + 1):
                     for dx in range(-raio, raio + 1):
                         tx, ty = gx + dx, gy + dy
                         if 0 <= tx < 20 and 0 <= ty < 20:
                             r = pygame.Rect(tx * TAMANHO_CELULA, ty * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
                             tela.blit(aoe_surf, r.topleft)

def desenhar_barra_iniciativa(tela, ordem_de_combate, personagem_ativo, game_images):
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
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images)
        
        x_offset += SPRITE_SIZE + SPRITE_PADDING

def desenhar_ordem_iniciativa(tela, fonte, ordem, personagem_ativo, game_images): 
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
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images)
        
        x_offset += 25
        if x_offset > area_iniciativa.right - 25:
            x_offset = area_iniciativa.x + 10
            y_offset += 25

def desenhar_projeteis_e_efeitos(tela, animacao_atual, y_offset, game_images):
    if not animacao_atual: return
    progresso = animacao_atual['progresso']
    
    if animacao_atual['tipo'] == 'ataque':
        atacante = animacao_atual['atacante']
        alvo = animacao_atual.get('alvo')
        
        if not alvo:
            return

        start_pos = pygame.Vector2(atacante.pos_x * TAMANHO_CELULA + 15, atacante.pos_y * TAMANHO_CELULA + 15 + y_offset)
        end_pos = pygame.Vector2(alvo.pos_x * TAMANHO_CELULA + 15, alvo.pos_y * TAMANHO_CELULA + 15 + y_offset)

        if progresso <= 0.5:
            pos_interp = start_pos.lerp(end_pos, progresso * 2)
            
            if isinstance(atacante, Arqueiro):
                # Desenha uma flecha
                vetor_direcao = (end_pos - start_pos).normalize()
                # Placeholder para imagem de flecha
                ponta = pos_interp
                base1 = pos_interp - vetor_direcao * 15 + vetor_direcao.rotate(90) * 4
                base2 = pos_interp - vetor_direcao * 15 - vetor_direcao.rotate(90) * 4
                pygame.draw.line(tela, (139, 69, 19), pos_interp, pos_interp - vetor_direcao * 15, 2)
                pygame.draw.polygon(tela, (200, 200, 200), [ponta, base1, base2])
            elif animacao_atual.get('habilidade') == 'raio_de_gelo':
                raio = 5 + 3 * math.sin(progresso * 20)
                pygame.draw.circle(tela, (173, 216, 230), pos_interp, raio)
            elif atacante.alcance > 1:
                pygame.draw.circle(tela, (255, 255, 0), pos_interp, 5)
        
        if atacante.alcance == 1 and progresso > 0.4 and progresso < 0.8:
            meio_anim = (progresso - 0.4) / 0.4
            ponto1 = end_pos + pygame.Vector2(-15, -15).lerp(pygame.Vector2(15, 15), meio_anim)
            ponto2 = end_pos + pygame.Vector2(15, -15).lerp(pygame.Vector2(-15, 15), meio_anim)
            pygame.draw.line(tela, (255, 255, 255), ponto1, ponto2, 3)

    elif animacao_atual['tipo'] == 'ataque_area':
        raio_max = animacao_atual['raio'] * TAMANHO_CELULA
        raio_atual = raio_max * progresso
        centro = (animacao_atual['x'] * TAMANHO_CELULA + 15, animacao_atual['y'] * TAMANHO_CELULA + 15 + y_offset)
        superficie = pygame.Surface((raio_atual * 2, raio_atual * 2), pygame.SRCALPHA)
        cor = (255, 100, 0, int(200 * (1 - progresso)))
        pygame.draw.circle(superficie, cor, (raio_atual, raio_atual), raio_atual)
        tela.blit(superficie, (centro[0] - raio_atual, centro[1] - raio_atual))

def desenhar_log(tela, fonte, logs, max_altura, y_offset):
    area_log = pygame.Rect(LARGURA_TABULEIRO, y_offset, LARGURA_LOG, max_altura - y_offset)
    pygame.draw.rect(tela, (10, 10, 10), area_log)
    titulo = fonte.render("LOG DE COMBATE", True, COR_TEXTO)
    tela.blit(titulo, (LARGURA_TABULEIRO + 20, y_offset + 20))
    y_offset_texto = y_offset + 50
    for log_msg, cor in logs:
        if y_offset_texto + 20 > max_altura: # Evita desenhar fora da área
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
    
    y += 15
    tela.blit(fonte.render("Efeitos de Status:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 30
    if not unidade.status_efeitos: tela.blit(fonte.render("  Nenhum", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for efeito in unidade.status_efeitos:
        if y + 25 > area_info.bottom:
            break
        cor_status = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome, {}).get("cor", COR_TEXTO)
        tela.blit(fonte.render(f"  - {efeito.nome} ({efeito.duracao_restante} turnos)", True, cor_status), (LARGURA_TABULEIRO + 20, y)); y += 30

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

    movimento_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    movimento_surf.fill((0, 100, 255, 80)) 
    ataque_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    ataque_surf.fill((255, 50, 0, 100))

    x, y = unidade.pos_x, unidade.pos_y
    
    for r in range(-unidade.velocidade, unidade.velocidade + 1):
        for c in range(-unidade.velocidade, unidade.velocidade + 1):
            nx, ny = x + c, y + r
            if 0 <= nx < motor.tabuleiro.largura and 0 <= ny < motor.tabuleiro.altura:
                if motor.tabuleiro.get_personagem_em(nx, ny) is None and motor.tabuleiro.get_terrain_em(nx, ny) != TERRENO_PAREDE:
                    tela.blit(movimento_surf, (nx * TAMANHO_CELULA, ny * TAMANHO_CELULA + y_offset))

    for inimigo in motor.combatentes:
        if inimigo.time != unidade.time and inimigo.esta_vivo:
            dist = abs(x - inimigo.pos_x) + abs(y - inimigo.pos_y)
            if dist <= unidade.alcance:
                tela.blit(ataque_surf, (inimigo.pos_x * TAMANHO_CELULA, inimigo.pos_y * TAMANHO_CELULA + y_offset))

def desenhar_comandos(tela, fonte, y_offset, botoes, mouse_pos, personagem_ativo=None):
    skill_menu_open = any(k == 'voltar_skills' for k in botoes.keys())
    fonte_retro = pygame.font.SysFont("Courier New", 16, bold=True)

    for nome, botao in botoes.items():
        is_skill_btn = nome.startswith('habilidade_') or nome == 'voltar_skills'
        is_main_btn = nome in ['atacar', 'habilidade', 'item', 'proxima_acao']
        
        if skill_menu_open:
            if is_main_btn: continue
        else:
            if is_skill_btn: continue
            
        if is_main_btn or is_skill_btn:
            rect = botao.rect
            hover = rect.collidepoint(mouse_pos)
            
            cor_fundo = (60, 40, 20) if not hover else (80, 60, 40)
            cor_borda = (218, 165, 32) # Gold
            
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
            pass

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
        "  - Clique fora para cancelar."
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

def desenhar_itens_no_chao(tela, tabuleiro, y_offset, visibilidade_map):
    for y in range(tabuleiro.altura):
        for x in range(tabuleiro.largura):
            if visibilidade_map[y][x] > 0: 
                item = tabuleiro.get_item_em(x, y)
                if item:
                    rect = pygame.Rect(x * TAMANHO_CELULA + 5, y * TAMANHO_CELULA + 5 + y_offset, TAMANHO_CELULA - 10, TAMANHO_CELULA - 10)
                    pygame.draw.circle(tela, (255, 215, 0), rect.center, 5)
                    if visibilidade_map[y][x] == 1:
                         nevoeiro_visto = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
                         nevoeiro_visto.fill((0, 0, 0, 180))
                         tela.blit(nevoeiro_visto, (x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset))
