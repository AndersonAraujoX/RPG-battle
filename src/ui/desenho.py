import pygame
import math
from src.config import (
    LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_FUNDO, COR_LINHA, COR_HP_BAR_FUNDO, COR_HP_BAR_FRENTE,
    COR_DANO, COR_CURA, COR_XP, COR_LEVEL_UP, COR_STATUS, COR_CRITICO, TIME_A, TIME_B,
    TAMANHO_CELULA, CORES_TERRENO, CORES_TIME, PROPRIEDADES_STATUS_EFEITO, TERRENO_PAREDE, 
    LARGURA_TABULEIRO, LARGURA_LOG, COR_BOTAO_HOVER,    COR_MANA_BAR, COR_ENERGIA_BAR, COR_BOTAO, COR_BOTAO_HOVER
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

def desenhar_sprite(tela, personagem, rect, cor, game_images): # Added game_images
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
            # Desenha um "X" ou um corpo genérico para personagens mortos
            pygame.draw.line(tela, (100, 0, 0), (x, y), (x + TAMANHO_CELULA, y + TAMANHO_CELULA), 3)
            pygame.draw.line(tela, (100, 0, 0), (x + TAMANHO_CELULA, y), (x, y + TAMANHO_CELULA), 3)
            # Desenha um círculo cinza escuro para o corpo
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
            p_inicial = pygame.Vector2(rect.center)
            p_final = pygame.Vector2(animacao_atual['alvo'].pos_x * TAMANHO_CELULA + TAMANHO_CELULA//2, animacao_atual['alvo'].pos_y * TAMANHO_CELULA + TAMANHO_CELULA//2 + offset_y)
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
            
            # HP Bar Foreground (Green to Red gradient logic could be added here)
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

    # Create a semi-transparent surface for highlighting
    highlight_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    highlight_surf.fill((255, 255, 0, 80)) # Yellow for highlight

    for p in motor.combatentes:
        if p.esta_vivo and p.time == TIME_A: # Only allied units (Team A)
            # Use standalone calcular_distancia function
            if calcular_distancia(p, hovered_enemy) <= p.alcance:
                rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
                tela.blit(highlight_surf, rect.topleft)




def desenhar_barra_iniciativa(tela, ordem_de_combate, personagem_ativo, game_images):
    BARRA_ALTURA = 80 # Increased height
    SPRITE_SIZE = 50 # Increased size
    SPRITE_PADDING = 20 # Increased padding
    
    # Draw background bar
    pygame.draw.rect(tela, (20, 20, 30), (0, 0, LARGURA_TELA, BARRA_ALTURA))
    pygame.draw.line(tela, COR_LINHA, (0, BARRA_ALTURA), (LARGURA_TELA, BARRA_ALTURA), 2)

    x_offset = SPRITE_PADDING
    for personagem in ordem_de_combate:
        if not personagem.esta_vivo:
            continue
        
        # Highlight active character
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, (255, 255, 0, 150), (x_offset - 4, BARRA_ALTURA // 2 - SPRITE_SIZE // 2 - 4, SPRITE_SIZE + 8, SPRITE_SIZE + 8), border_radius=5)

        sprite_rect = pygame.Rect(x_offset, BARRA_ALTURA // 2 - SPRITE_SIZE // 2, SPRITE_SIZE, SPRITE_SIZE)
        cor = CORES_TIME.get(personagem.time, (200, 200, 200))
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images)
        
        x_offset += SPRITE_SIZE + SPRITE_PADDING

# ... (projeteis function skipped)

def desenhar_ordem_iniciativa(tela, fonte, ordem, personagem_ativo, game_images):
    # This function seems redundant with desenhar_barra_iniciativa but is used for the HUD panel?
    # Let's keep it but improve spacing if used
    area_iniciativa = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 250, LARGURA_LOG, 100)
    pygame.draw.rect(tela, (15, 15, 15), area_iniciativa)
    
    titulo_render = fonte.render("Ordem de Iniciativa:", True, COR_TEXTO)
    tela.blit(titulo_render, (area_iniciativa.x + 10, area_iniciativa.y + 5))
    
    x_offset = area_iniciativa.x + 15
    y_offset = area_iniciativa.y + 35
    
    for personagem in ordem:
        if not personagem.esta_vivo:
            continue
            
        cor = CORES_TIME.get(personagem.time)
        
        # Highlight the active character
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, COR_BOTAO_HOVER, (x_offset - 2, y_offset - 2, 34, 34), border_radius=4)

        # Draw a smaller version of the character sprite
        sprite_rect = pygame.Rect(x_offset, y_offset, 30, 30) # Increased size
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images)
        
        x_offset += 40 # Increased spacing
        if x_offset > area_iniciativa.right - 35:
            x_offset = area_iniciativa.x + 15
            y_offset += 40


def desenhar_projeteis_e_efeitos(tela, animacao_atual, y_offset, game_images):
    if not animacao_atual: return
    progresso = animacao_atual['progresso']
    
    if animacao_atual['tipo'] == 'ataque':
        atacante = animacao_atual['atacante']
        alvo = animacao_atual['alvo']
        start_pos = pygame.Vector2(atacante.pos_x * TAMANHO_CELULA + 15, atacante.pos_y * TAMANHO_CELULA + 15 + y_offset)
        end_pos = pygame.Vector2(alvo.pos_x * TAMANHO_CELULA + 15, alvo.pos_y * TAMANHO_CELULA + 15 + y_offset)

        if progresso <= 0.5:
            pos_interp = start_pos.lerp(end_pos, progresso * 2)
            
            if isinstance(atacante, Arqueiro):
                # Desenha uma flecha
                vetor_direcao = (end_pos - start_pos).normalize()
                angulo = vetor_direcao.angle_to(pygame.Vector2(1, 0))
                # Placeholder para imagem de flecha
                ponta = pos_interp
                base1 = pos_interp - vetor_direcao * 15 + vetor_direcao.rotate(90) * 4
                base2 = pos_interp - vetor_direcao * 15 - vetor_direcao.rotate(90) * 4
                pygame.draw.line(tela, (139, 69, 19), pos_interp, pos_interp - vetor_direcao * 15, 2)
                pygame.draw.polygon(tela, (200, 200, 200), [ponta, base1, base2])
            elif animacao_atual.get('habilidade') == 'raio_de_gelo':
                # Bola de gelo pulsante
                raio = 5 + 3 * math.sin(progresso * 20)
                pygame.draw.circle(tela, (173, 216, 230), pos_interp, raio)
            elif atacante.alcance > 1:
                 # Projétil genérico
                pygame.draw.circle(tela, (255, 255, 0), pos_interp, 5)
        
        # Efeito de corte para ataques corpo a corpo
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
    
    # Fundo do Painel de Info (Marrom translúcido)
    s = pygame.Surface((area_info.width, area_info.height), pygame.SRCALPHA)
    s.fill((40, 30, 20, 230))
    tela.blit(s, area_info.topleft)
    
    # Borda Dourada
    pygame.draw.rect(tela, (218, 165, 32), area_info, 3, border_radius=5)
    
    if not unidade:
        texto = fonte.render("Selecione uma unidade", True, (150, 150, 150))
        tela.blit(texto, (LARGURA_TABULEIRO + 20, 100))
        return

    y = 100
    # Nome (Dourado)
    nome_render = fonte.render(f"{unidade.nome} ({unidade.classe_nome})", True, (255, 215, 0))
    tela.blit(nome_render, (LARGURA_TABULEIRO + 20, y))
    y += 30
    
    # Stats
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
    # Status Effects
    if unidade.status_efeitos:
        tela.blit(fonte.render("Status:", True, (150, 150, 255)), (LARGURA_TABULEIRO + 20, y))
        y += 25
        for efeito in unidade.status_efeitos:
            cor_status = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome, {}).get("cor", COR_TEXTO)
            tela.blit(fonte.render(f"- {efeito.nome} ({efeito.duracao_restante} turnos)", True, cor_status), (LARGURA_TABULEIRO + 30, y))
            y += 25
    
    y += 15 # Espaçamento
    tela.blit(fonte.render("Habilidades:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 30
    if not unidade.cooldowns: tela.blit(fonte.render("  Nenhuma", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for nome, cd in unidade.cooldowns.items():
        if y + 25 > area_info.bottom: # Use area_info.bottom for boundary check
            break
        status, cor = ("Pronta!", (60,220,60)) if cd == 0 else (f"{cd} turnos", (220,180,60))
        tela.blit(fonte.render(f"  - {nome.replace('_', ' ').title()}:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y))
        tela.blit(fonte.render(status, True, cor), (LARGURA_TABULEIRO + 200, y)); y += 30
    y += 15 # Espaçamento
    tela.blit(fonte.render("Efeitos de Status:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 30
    if not personagem.status_efeitos: tela.blit(fonte.render("  Nenhum", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for efeito in personagem.status_efeitos:
        if y + 25 > max_altura:
            break
        cor_status = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome, {}).get("cor", COR_TEXTO) # Pega a cor do config
        tela.blit(fonte.render(f"  - {efeito.nome} ({efeito.duracao_restante} turnos)", True, cor_status), (LARGURA_TABULEIRO + 20, y)); y += 30

def desenhar_inventario(tela, fonte, personagem, max_altura, y_offset, mouse_pos):
    area_inventario = pygame.Rect(LARGURA_TABULEIRO, y_offset, LARGURA_LOG, max_altura - y_offset)
    pygame.draw.rect(tela, (15, 15, 25), area_inventario) # Fundo azul escuro
    
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
        
        # Highlight se o mouse estiver sobre o item
        cor_fundo_item = COR_BOTAO_HOVER if item_rect.collidepoint(mouse_pos) else COR_BOTAO
        pygame.draw.rect(tela, cor_fundo_item, item_rect, border_radius=5)
        
        nome_item_render = fonte.render(item.nome, True, COR_TEXTO)
        tela.blit(nome_item_render, (item_rect.x + 10, item_rect.y + 10))
        
        y += 40


def desenhar_feedback_jogador(tela, unidade, motor, y_offset):
    if not unidade: return

    # Prepara superfícies semi-transparentes para o feedback
    movimento_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    movimento_surf.fill((0, 100, 255, 80)) # Azul para movimento
    ataque_surf = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
    ataque_surf.fill((255, 50, 0, 100)) # Vermelho para ataque

    x, y = unidade.pos_x, unidade.pos_y
    
    # Mostra alcance de movimento
    for r in range(-unidade.velocidade, unidade.velocidade + 1):
        for c in range(-unidade.velocidade, unidade.velocidade + 1):
            # if abs(r) + abs(c) > unidade.velocidade: continue # Removed for Square Distance
            
            nx, ny = x + c, y + r
            if 0 <= nx < motor.tabuleiro.largura and 0 <= ny < motor.tabuleiro.altura:
                if motor.tabuleiro.get_personagem_em(nx, ny) is None and motor.tabuleiro.get_terrain_em(nx, ny) != TERRENO_PAREDE:
                    tela.blit(movimento_surf, (nx * TAMANHO_CELULA, ny * TAMANHO_CELULA + y_offset))

    # Mostra alcance de ataque
    for inimigo in motor.combatentes:
        if inimigo.time != unidade.time and inimigo.esta_vivo:
            dist = abs(x - inimigo.pos_x) + abs(y - inimigo.pos_y)
            if dist <= unidade.alcance:
                tela.blit(ataque_surf, (inimigo.pos_x * TAMANHO_CELULA, inimigo.pos_y * TAMANHO_CELULA + y_offset))

def desenhar_tela_fim(tela, fonte, vencedor, y_offset, botoes, mouse_pos):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))
    
    texto = f"O {vencedor} VENCEU!"
    texto_render = fonte.render(texto, True, COR_TEXTO)
    tela.blit(texto_render, texto_render.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 - 50)))

    botoes['reiniciar'].update_hover(mouse_pos)
    botoes['reiniciar'].desenhar(tela, fonte)
    botoes['voltar_menu'].update_hover(mouse_pos)
    botoes['voltar_menu'].desenhar(tela, fonte)

def desenhar_comandos(tela, fonte, y_offset, botoes, mouse_pos):
    area_comandos = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 240 + y_offset, LARGURA_LOG, 240)
    
    # Fundo do Painel de Comandos (Marrom translúcido)
    s = pygame.Surface((area_comandos.width, area_comandos.height), pygame.SRCALPHA)
    s.fill((40, 30, 20, 230))
    tela.blit(s, area_comandos.topleft)
    
    # Borda Dourada
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
        
    # Desenhar botões de combate (Passar Turno, Salvar, Carregar)
    for botao in botoes.values():
        botao.update_hover(mouse_pos)
        botao.desenhar(tela, fonte, mouse_pos)

def desenhar_ordem_iniciativa(tela, fonte, ordem, personagem_ativo, game_images): # Added game_images
    area_iniciativa = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 250, LARGURA_LOG, 100)
    
    # Fundo do Painel de Iniciativa
    s = pygame.Surface((area_iniciativa.width, area_iniciativa.height), pygame.SRCALPHA)
    s.fill((30, 20, 10, 230))
    tela.blit(s, area_iniciativa.topleft)
    
    # Borda Dourada
    pygame.draw.rect(tela, (218, 165, 32), area_iniciativa, 3, border_radius=5)
    
    titulo_render = fonte.render("Ordem de Iniciativa:", True, (255, 215, 0)) # Título Dourado
    tela.blit(titulo_render, (area_iniciativa.x + 10, area_iniciativa.y + 5))
    
    x_offset = area_iniciativa.x + 10
    y_offset = area_iniciativa.y + 30
    
    for personagem in ordem:
        if not personagem.esta_vivo:
            continue
            
        cor = CORES_TIME.get(personagem.time)
        
        # Highlight the active character
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, COR_BOTAO_HOVER, (x_offset - 2, y_offset - 2, 24, 24), border_radius=4)

        # Draw a smaller version of the character sprite
        sprite_rect = pygame.Rect(x_offset, y_offset, 20, 20)
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images) # Pass game_images
        
        x_offset += 25
        if x_offset > area_iniciativa.right - 25:
            x_offset = area_iniciativa.x + 10
            y_offset += 25

def desenhar_floating_texts(tela, floating_texts):
    for texto in floating_texts:
        texto.draw(tela)

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
    area_ui = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, ALTURA_TELA)
    pygame.draw.rect(tela, (30, 30, 40), area_ui)
    
    titulo_render = fonte_menu.render("Editor de Mapas", True, COR_TEXTO)
    tela.blit(titulo_render, titulo_render.get_rect(center=(LARGURA_TABULEIRO + LARGURA_LOG // 2, 50)))

    for nome, botao in botoes.items():
        botao.update_hover(mouse_pos)
        # Highlight no terreno selecionado
        if nome == terreno_selecionado:
            pygame.draw.rect(tela, COR_BOTAO_HOVER, botao.rect.inflate(4, 4), border_radius=7)
        botao.desenhar(tela, fonte_menu)

def desenhar_itens_no_chao(tela, tabuleiro, y_offset, visibilidade_map):
    for y in range(tabuleiro.altura):
        for x in range(tabuleiro.largura):
            if visibilidade_map[y][x] > 0: # Visto ou visível
                item = tabuleiro.get_item_em(x, y)
                if item:
                    rect = pygame.Rect(x * TAMANHO_CELULA + 5, y * TAMANHO_CELULA + 5 + y_offset, TAMANHO_CELULA - 10, TAMANHO_CELULA - 10)
                    # Simples representação de item como um círculo dourado
                    pygame.draw.circle(tela, (255, 215, 0), rect.center, 5)
                    if visibilidade_map[y][x] == 1: # Efeito de nevoeiro se apenas visto
                         nevoeiro_visto = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA), pygame.SRCALPHA)
                         nevoeiro_visto.fill((0, 0, 0, 180))
                         tela.blit(nevoeiro_visto, (x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset))

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
    overlay.fill((0, 0, 0, 220))
    tela.blit(overlay, (0, 0))

    titulo_render = fonte_titulo.render("LEVEL UP!", True, (255, 215, 0))
    tela.blit(titulo_render, titulo_render.get_rect(center=(LARGURA_TELA // 2, 100)))

    nome_render = fonte_menu.render(f"{personagem.nome} subiu para o nível {personagem.nivel}!", True, COR_TEXTO)
    tela.blit(nome_render, nome_render.get_rect(center=(LARGURA_TELA // 2, 180)))
    
    subtitulo_render = fonte_menu.render("Escolha um atributo para aumentar:", True, COR_TEXTO)
    tela.blit(subtitulo_render, subtitulo_render.get_rect(center=(LARGURA_TELA // 2, 250)))

    for nome, botao in botoes.items():
        botao.update_hover(mouse_pos)
        botao.desenhar(tela, fonte_menu)

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
        bg_img = pygame.image.load(resource_path("assets/images/menu_background.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (LARGURA_TELA, ALTURA_TELA))
        tela.blit(bg_img, (0, 0))
    except Exception as e:
        print(f"Erro ao carregar background: {e}")
        tela.fill((20, 20, 30))
    
    # Título "FINAL DE KINDREAD SOUL"
    # Estilo: Épico com Borda Grossa
    fonte_titulo = pygame.font.Font(None, 110)
    fonte_subtitulo = pygame.font.Font(None, 130)
    
    texto_titulo = "FINAL DE"
    texto_subtitulo = "KINDREAD SOUL"
    
    # Posições
    x_titulo = 80
    y_titulo = 80
    x_sub = 80
    y_sub = 160
    
    # Renderizar com Outline
    # "FINAL DE" - Dourado Pálido com borda preta
    draw_text_with_outline(tela, texto_titulo, fonte_titulo, (240, 230, 140), (x_titulo, y_titulo), outline_width=4)
    
    # "KINDREAD SOUL" - Laranja/Dourado Intenso com borda preta grossa
    draw_text_with_outline(tela, texto_subtitulo, fonte_subtitulo, (255, 140, 0), (x_sub, y_sub), outline_width=5)
    
    # Efeito de Brilho (Overlay simples)
    # Uma cópia branca levemente deslocada e transparente para dar volume?
    # Ou apenas um gradiente simulado (faixa mais clara no meio)
    # Vamos tentar desenhar o texto de novo com uma cor mais clara e clipar? 
    # Pygame puro é chato para isso. Vamos manter o outline que já melhora muito.

    for botao in botoes.values():
        botao.desenhar(tela, fonte, mouse_pos)

def desenhar_feedback_invalido(tela, alpha, y_offset):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA - y_offset), pygame.SRCALPHA)
    overlay.fill((255, 0, 0, alpha))
    tela.blit(overlay, (0, y_offset))

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

def desenhar_setup_batalha(tela, fonte, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, checkbox_mapa_custom, checkbox_campanha, checkbox_limitadores, bosses, selected_boss_index, game_images, volume_sfx, menu_tabs, active_tab_id, mouse_pos=None):
    # Fundo (Wallpaper)
    try:
        bg_img = pygame.image.load(resource_path("assets/images/menu_background.png")).convert()
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
        
        # Draw volume controls separately
        y_volume = config_y + 280 # Below limiters checkbox
        tela.blit(fonte.render(f"Volume SFX: {int(volume_sfx * 100)}%", True, COR_TEXTO), (config_x, y_volume))
        botoes_ui['sfx_vol_down'].rect.topleft = (config_x + 200, y_volume)
        botoes_ui['sfx_vol_down'].desenhar(tela, fonte, mouse_pos)
        botoes_ui['sfx_vol_up'].rect.topleft = (config_x + 260, y_volume)
        botoes_ui['sfx_vol_up'].desenhar(tela, fonte, mouse_pos)

    # Iniciar Batalha button (always visible)
    botoes_ui['iniciar'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 60)
    botoes_ui['iniciar'].desenhar(tela, fonte, mouse_pos)
    
    # Editor de Mapas button (always visible)
    botoes_ui['editor_mapas'].rect.center = (LARGURA_TELA // 2, ALTURA_TELA - 120)
    botoes_ui['editor_mapas'].desenhar(tela, fonte, mouse_pos)
    
    # Botão Voltar ao Menu Principal
    botoes_ui['voltar_menu'].rect.topleft = (20, 20)
    botoes_ui['voltar_menu'].desenhar(tela, fonte, mouse_pos)

def desenhar_mapa_mundo(tela, fonte, botoes, campaign_manager, nivel_atual, game_images, mouse_pos):
    # Fundo (Mapa Mundi)
    try:
        bg_img = pygame.image.load(resource_path("assets/images/mapa_mundo.png")).convert()
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
