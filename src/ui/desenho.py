import pygame
import math
from src.config import (
    TAMANHO_CELULA, CORES_TERRENO, COR_FUNDO, COR_LINHA, CORES_TIME,
    COR_HP_BAR_FUNDO, COR_HP_BAR_FRENTE, COR_TEXTO, PROPRIEDADES_STATUS_EFEITO,
    TERRENO_PAREDE, LARGURA_TABULEIRO, LARGURA_LOG, ALTURA_TELA, COR_BOTAO_HOVER, LARGURA_TELA
)
from src.personagens import (
    Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe, Paladino,
    ReiGoblin, LordeLich, DragaoAnciao, Druida, Bruxo
)

def desenhar_cenario(tela, motor, game_images, y_offset):
    for y in range(motor.tabuleiro.altura):
        for x in range(motor.tabuleiro.largura):
            rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
            terreno = motor.tabuleiro.get_terrain_em(x, y)
            terreno_img_key = f"terreno_{terreno.lower()}"
            if terreno_img_key in game_images and game_images[terreno_img_key]:
                scaled_img = pygame.transform.scale(game_images[terreno_img_key], (TAMANHO_CELULA, TAMANHO_CELULA))
                tela.blit(scaled_img, (x * TAMANHO_CELULA, y * TAMANHO_CELULA + y_offset))
            else:
                pygame.draw.rect(tela, CORES_TERRENO.get(terreno, COR_FUNDO), rect)
            pygame.draw.rect(tela, COR_LINHA, rect, 1)

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

def desenhar_personagens(tela, motor, fonte, personagem_ativo, tick, animacao_atual, game_images, y_offset):
    personagens_desenhados = set()
    atacante_animacao = animacao_atual['atacante'] if animacao_atual and 'atacante' in animacao_atual else None
    for p in motor.combatentes:
        if p.esta_vivo and p != atacante_animacao:
            cor = CORES_TIME.get(p.time, (200, 200, 200))
            rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
            if hasattr(p, 'dano_timer') and p.dano_timer > 0:
                fator = p.dano_timer / 15.0
                cor = (int(cor[0]*(1-fator) + 255*fator), int(cor[1]*(1-fator) + 50*fator), int(cor[2]*(1-fator) + 50*fator))
                p.dano_timer -= 1
            if p == personagem_ativo and not animacao_atual:
                escala = 1.0 + 0.15 * abs(math.sin(tick * 0.1))
                largura, altura = int(TAMANHO_CELULA * escala), int(TAMANHO_CELULA * escala)
                sprite_rect = pygame.Rect(rect.centerx - largura // 2, rect.centery - altura // 2, largura, altura)
                desenhar_sprite(tela, p, sprite_rect, cor, game_images)
            else:
                desenhar_sprite(tela, p, rect, cor, game_images)
            personagens_desenhados.add(p)

            # Desenhar indicadores de status
            if p.status_efeitos:
                status_x_offset = 0
                for efeito in p.status_efeitos:
                    prop = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome)
                    if prop:
                        # Desenha um pequeno quadrado colorido
                        cor_status = prop.get("cor", (255, 255, 255))
                        status_rect = pygame.Rect(rect.right - 10 - status_x_offset, rect.top + 2, 8, 8)
                        pygame.draw.rect(tela, cor_status, status_rect)

                        # Desenha o ícone do status
                        icone = prop.get("icone")
                        if icone:
                            # Create a smaller font for the icon
                            fonte_icone = pygame.font.Font(None, 10) # Smaller font for icon
                            icone_render = fonte_icone.render(icone, True, COR_TEXTO)
                            icone_rect = icone_render.get_rect(center=status_rect.center)
                            tela.blit(icone_render, icone_rect)
                            
                        status_x_offset += 10 # Offset para o próximo status
        
    if atacante_animacao and atacante_animacao.esta_vivo:
        p = atacante_animacao
        rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
        progresso = animacao_atual['progresso']
        if animacao_atual['tipo'] == 'ataque' and p.alcance == 1:
            p_inicial = pygame.Vector2(rect.center)
            p_final = pygame.Vector2(animacao_atual['alvo'].pos_x * TAMANHO_CELULA + TAMANHO_CELULA//2, animacao_atual['alvo'].pos_y * TAMANHO_CELULA + TAMANHO_CELULA//2 + y_offset)
            pos_interp = p_inicial.lerp(p_final, progresso * 2) if progresso <= 0.5 else p_final.lerp(p_inicial, (progresso - 0.5) * 2)
            rect.center = pos_interp
        cor = CORES_TIME.get(p.time, (200, 200, 200))
        desenhar_sprite(tela, p, rect, cor, game_images)
        personagens_desenhados.add(p)
    for p in motor.combatentes:
        if p.esta_vivo:
            rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
            hp_percent = p.hp_atual / p.hp_max
            hp_bar_fundo = pygame.Rect(rect.left, rect.top - 8, TAMANHO_CELULA, 5)
            hp_bar_frente = pygame.Rect(rect.left, rect.top - 8, int(TAMANHO_CELULA * hp_percent), 5)
            pygame.draw.rect(tela, COR_HP_BAR_FUNDO, hp_bar_fundo)
            pygame.draw.rect(tela, COR_HP_BAR_FRENTE, hp_bar_frente)
            
            bar_y = rect.top - 2
            # Draw Mana bar
            if p.mana_max > 0:
                mana_percent = p.mana_atual / p.mana_max
                mana_bar_fundo = pygame.Rect(rect.left, bar_y, TAMANHO_CELULA, 3)
                mana_bar_frente = pygame.Rect(rect.left, bar_y, int(TAMANHO_CELULA * mana_percent), 3)
                pygame.draw.rect(tela, COR_HP_BAR_FUNDO, mana_bar_fundo)
                pygame.draw.rect(tela, COR_MANA_BAR, mana_bar_frente)
                bar_y += 4
            
            # Draw Energy bar
            if p.energia_max > 0:
                energia_percent = p.energia_atual / p.energia_max
                energia_bar_fundo = pygame.Rect(rect.left, bar_y, TAMANHO_CELULA, 3)
                energia_bar_frente = pygame.Rect(rect.left, bar_y, int(TAMANHO_CELULA * energia_percent), 3)
                pygame.draw.rect(tela, COR_HP_BAR_FUNDO, energia_bar_fundo)
                pygame.draw.rect(tela, COR_ENERGIA_BAR, energia_bar_frente)

            level_render = fonte.render(str(p.nivel), True, COR_TEXTO)
            pygame.draw.circle(tela, (0,0,0), (rect.left + 6, rect.top + 6), 8)
            tela.blit(level_render, (rect.left + 2, rect.top))

            # Draw cooldown indicator
            if p.cooldowns:
                cooldown_x_offset = 0
                for i, (nome, cd) in enumerate(p.cooldowns.items()):
                    if p.cooldown_max.get(nome, 0) > 0:
                        # Draw a small pie chart indicator
                        angle = (cd / p.cooldown_max[nome]) * 2 * math.pi
                        rect_cooldown = pygame.Rect(rect.left + cooldown_x_offset, rect.bottom - 8, 8, 8)
                        
                        # Background
                        pygame.draw.ellipse(tela, (50, 50, 50), rect_cooldown)
                        
                        if angle > 0:
                            # foreground
                            start_angle = math.pi / 2
                            end_angle = start_angle + angle
                            
                            # Create a surface for the arc
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
            # Use motor.calcular_distancia for consistency and to avoid re-importing utils
            if motor.tabuleiro.calcular_distancia(p, hovered_enemy) <= p.alcance:
                rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA + y_offset, TAMANHO_CELULA, TAMANHO_CELULA)
                tela.blit(highlight_surf, rect.topleft)


                        cooldown_x_offset += 10

def desenhar_barra_iniciativa(tela, ordem_de_combate, personagem_ativo, game_images):
    BARRA_ALTURA = 60
    SPRITE_SIZE = 40
    SPRITE_PADDING = 10
    
    # Draw background bar
    pygame.draw.rect(tela, (20, 20, 30), (0, 0, LARGURA_TELA, BARRA_ALTURA))
    pygame.draw.line(tela, COR_LINHA, (0, BARRA_ALTURA), (LARGURA_TELA, BARRA_ALTURA), 2)

    x_offset = SPRITE_PADDING
    for personagem in ordem_de_combate:
        if not personagem.esta_vivo:
            continue
        
        # Highlight active character
        if personagem == personagem_ativo:
            pygame.draw.rect(tela, (255, 255, 0, 150), (x_offset - 2, BARRA_ALTURA // 2 - SPRITE_SIZE // 2 - 2, SPRITE_SIZE + 4, SPRITE_SIZE + 4), border_radius=5)

        sprite_rect = pygame.Rect(x_offset, BARRA_ALTURA // 2 - SPRITE_SIZE // 2, SPRITE_SIZE, SPRITE_SIZE)
        cor = CORES_TIME.get(personagem.time, (200, 200, 200))
        desenhar_sprite(tela, personagem, sprite_rect, cor, game_images)
        
        x_offset += SPRITE_SIZE + SPRITE_PADDING


def desenhar_projeteis_e_efeitos(tela, animacao_atual, y_offset):
    if not animacao_atual: return
    progresso = animacao_atual['progresso']
    if animacao_atual['tipo'] == 'ataque' and animacao_atual['atacante'].alcance > 1:
        atacante, alvo = animacao_atual['atacante'], animacao_atual['alvo']
        start_pos = pygame.Vector2(atacante.pos_x * TAMANHO_CELULA + 15, atacante.pos_y * TAMANHO_CELULA + 15 + y_offset)
        end_pos = pygame.Vector2(alvo.pos_x * TAMANHO_CELULA + 15, alvo.pos_y * TAMANHO_CELULA + 15 + y_offset)
        if progresso <= 0.5:
            pos_interp = start_pos.lerp(end_pos, progresso * 2)
            pygame.draw.circle(tela, (255, 255, 0), pos_interp, 5)
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
    for log_msg in logs:
        if y_offset_texto + 20 > max_altura: # Evita desenhar fora da área
            break
        log_render = fonte.render(''.join(c for c in log_msg if c.isprintable()), True, COR_TEXTO)
        tela.blit(log_render, (LARGURA_TABULEIRO + 20, y_offset_texto))
        y_offset_texto += 20

def desenhar_info_personagem(tela, fonte, personagem, max_altura, y_offset):
    area_info = pygame.Rect(LARGURA_TABULEIRO, y_offset, LARGURA_LOG, max_altura - y_offset)
    pygame.draw.rect(tela, (15, 15, 15), area_info)
    y = y_offset + 20
    tela.blit(fonte.render(f"{personagem.nome} (Lvl {personagem.nivel})", True, CORES_TIME.get(personagem.time)), (LARGURA_TABULEIRO + 20, y)); y += 30
    tela.blit(fonte.render(f"Classe: {personagem.__class__.__name__}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 40
    tela.blit(fonte.render(f"HP: {personagem.hp_atual} / {personagem.hp_max}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 25
    tela.blit(fonte.render(f"XP: {personagem.xp} / {personagem.xp_para_upar}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 40
    tela.blit(fonte.render(f"AC: {personagem.ac}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 25
    tela.blit(fonte.render(f"Bônus Atk: +{personagem.bonus_ataque}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 25
    tela.blit(fonte.render(f"Bônus Dmg: +{personagem.bonus_dano}", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 40
    tela.blit(fonte.render("Habilidades:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 25
    if not personagem.cooldowns: tela.blit(fonte.render("  Nenhuma", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for nome, cd in personagem.cooldowns.items():
        if y + 20 > max_altura:
            break
        status, cor = ("Pronta!", (60,220,60)) if cd == 0 else (f"{cd} turnos", (220,180,60))
        tela.blit(fonte.render(f"  - {nome.replace('_', ' ').title()}:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y))
        tela.blit(fonte.render(status, True, cor), (LARGURA_TABULEIRO + 200, y)); y += 25
    y += 10 # Espaçamento
    tela.blit(fonte.render("Efeitos de Status:", True, COR_TEXTO), (LARGURA_TABULEIRO + 20, y)); y += 25
    if not personagem.status_efeitos: tela.blit(fonte.render("  Nenhum", True, (150,150,150)), (LARGURA_TABULEIRO + 20, y))
    for efeito in personagem.status_efeitos:
        if y + 20 > max_altura:
            break
        cor_status = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome, {}).get("cor", COR_TEXTO) # Pega a cor do config
        tela.blit(fonte.render(f"  - {efeito.nome} ({efeito.duracao_restante} turnos)", True, cor_status), (LARGURA_TABULEIRO + 20, y)); y += 25

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
            if abs(r) + abs(c) > unidade.velocidade: continue
            
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

def desenhar_tela_fim(tela, fonte, vencedor, y_offset):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))
    texto = f"O {vencedor} VENCEU!"
    texto_render = fonte.render(texto, True, COR_TEXTO)
    tela.blit(texto_render, texto_render.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + y_offset // 2)))

def desenhar_comandos(tela, fonte, y_offset):
    area_comandos = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 150 + y_offset, LARGURA_LOG, 150)
    pygame.draw.rect(tela, (25, 25, 25), area_comandos) # Fundo para os comandos
    
    y_offset_texto = ALTURA_TELA - 140 + y_offset
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

def desenhar_ordem_iniciativa(tela, fonte, ordem, personagem_ativo, game_images): # Added game_images
    area_iniciativa = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 250, LARGURA_LOG, 100)
    pygame.draw.rect(tela, (15, 15, 15), area_iniciativa)
    
    titulo_render = fonte.render("Ordem de Iniciativa:", True, COR_TEXTO)
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

def desenhar_feedback_invalido(tela, alpha, y_offset):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA - y_offset), pygame.SRCALPHA)
    overlay.fill((255, 0, 0, alpha))
    tela.blit(overlay, (0, y_offset))
