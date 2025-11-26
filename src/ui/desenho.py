import pygame
import math
from src.config import (
    TAMANHO_CELULA, CORES_TERRENO, COR_FUNDO, COR_LINHA, CORES_TIME,
    COR_HP_BAR_FUNDO, COR_HP_BAR_FRENTE, COR_TEXTO, PROPRIEDADES_STATUS_EFEITO,
    TERRENO_PAREDE, LARGURA_TABULEIRO, LARGURA_LOG, ALTURA_TELA
)
from ..personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe

def desenhar_cenario(tela, motor):
    for y in range(motor.tabuleiro.altura):
        for x in range(motor.tabuleiro.largura):
            rect = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
            terreno = motor.tabuleiro.get_terrain_em(x, y)
            pygame.draw.rect(tela, CORES_TERRENO.get(terreno, COR_FUNDO), rect)
            pygame.draw.rect(tela, COR_LINHA, rect, 1)

def desenhar_sprite(tela, personagem, rect, cor):
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
    elif isinstance(personagem, Guerreiro): pygame.draw.rect(tela, cor, rect, border_radius=3)
    elif isinstance(personagem, Mago): pygame.draw.circle(tela, cor, center, radius)
    elif isinstance(personagem, Ladino): pygame.draw.polygon(tela, cor, [(center[0], rect.top), (rect.left, rect.bottom), (rect.right, rect.bottom)])
    elif isinstance(personagem, Arqueiro): pygame.draw.polygon(tela, cor, [(center[0], rect.top), (rect.right, center[1]), (center[0], rect.bottom), (rect.left, center[1])])
    elif isinstance(personagem, Barbaro): pygame.draw.polygon(tela, cor, [(rect.left + radius * 0.5, rect.top), (rect.right - radius * 0.5, rect.top), (rect.right, center[1]), (rect.right - radius * 0.5, rect.bottom), (rect.left + radius * 0.5, rect.bottom), (rect.left, center[1])])
    elif isinstance(personagem, Clerigo):
        pygame.draw.rect(tela, cor, (rect.left + radius * 0.4, rect.top, radius, rect.height))
        pygame.draw.rect(tela, cor, (rect.left, rect.top + radius * 0.4, rect.width, radius))
    else: pygame.draw.rect(tela, cor, rect)

def desenhar_personagens(tela, motor, fonte, personagem_ativo, tick, animacao_atual):
    personagens_desenhados = set()
    atacante_animacao = animacao_atual['atacante'] if animacao_atual and 'atacante' in animacao_atual else None
    for p in motor.combatentes:
        if p.esta_vivo and p != atacante_animacao:
            cor = CORES_TIME.get(p.time, (200, 200, 200))
            rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
            if hasattr(p, 'dano_timer') and p.dano_timer > 0:
                fator = p.dano_timer / 15.0
                cor = (int(cor[0]*(1-fator) + 255*fator), int(cor[1]*(1-fator) + 50*fator), int(cor[2]*(1-fator) + 50*fator))
                p.dano_timer -= 1
            if p == personagem_ativo and not animacao_atual:
                escala = 1.0 + 0.15 * abs(math.sin(tick * 0.1))
                largura, altura = int(TAMANHO_CELULA * escala), int(TAMANHO_CELULA * escala)
                sprite_rect = pygame.Rect(rect.centerx - largura // 2, rect.centery - altura // 2, largura, altura)
                desenhar_sprite(tela, p, sprite_rect, cor)
            else:
                desenhar_sprite(tela, p, rect, cor)
            personagens_desenhados.add(p)

            # Desenhar indicadores de status
            if p.status_efeitos:
                status_x_offset = 0
                for efeito in p.status_efeitos:
                    prop = PROPRIEDADES_STATUS_EFEITO.get(efeito.nome)
                    if prop:
                        # Desenha um pequeno quadrado colorido
                        cor_status = prop.get("cor", (255, 255, 255))
                        pygame.draw.rect(tela, cor_status, (rect.right - 10 - status_x_offset, rect.top + 2, 8, 8))
                        status_x_offset += 10 # Offset para o próximo status
        
    if atacante_animacao and atacante_animacao.esta_vivo:
        p = atacante_animacao
        rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
        progresso = animacao_atual['progresso']
        if animacao_atual['tipo'] == 'ataque' and p.alcance == 1:
            p_inicial = pygame.Vector2(rect.center)
            p_final = pygame.Vector2(animacao_atual['alvo'].pos_x * TAMANHO_CELULA + TAMANHO_CELULA//2, animacao_atual['alvo'].pos_y * TAMANHO_CELULA + TAMANHO_CELULA//2)
            pos_interp = p_inicial.lerp(p_final, progresso * 2) if progresso <= 0.5 else p_final.lerp(p_inicial, (progresso - 0.5) * 2)
            rect.center = pos_interp
        cor = CORES_TIME.get(p.time, (200, 200, 200))
        desenhar_sprite(tela, p, rect, cor)
        personagens_desenhados.add(p)
    for p in motor.combatentes:
        if p.esta_vivo:
            rect = pygame.Rect(p.pos_x * TAMANHO_CELULA, p.pos_y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
            hp_percent = p.hp_atual / p.hp_max
            hp_bar_fundo = pygame.Rect(rect.left, rect.top - 8, TAMANHO_CELULA, 5)
            hp_bar_frente = pygame.Rect(rect.left, rect.top - 8, int(TAMANHO_CELULA * hp_percent), 5)
            pygame.draw.rect(tela, COR_HP_BAR_FUNDO, hp_bar_fundo)
            pygame.draw.rect(tela, COR_HP_BAR_FRENTE, hp_bar_frente)
            level_render = fonte.render(str(p.nivel), True, COR_TEXTO)
            pygame.draw.circle(tela, (0,0,0), (rect.left + 6, rect.top + 6), 8)
            tela.blit(level_render, (rect.left + 2, rect.top))

def desenhar_projeteis_e_efeitos(tela, animacao_atual):
    if not animacao_atual: return
    progresso = animacao_atual['progresso']
    if animacao_atual['tipo'] == 'ataque' and animacao_atual['atacante'].alcance > 1:
        atacante, alvo = animacao_atual['atacante'], animacao_atual['alvo']
        start_pos = pygame.Vector2(atacante.pos_x * TAMANHO_CELULA + 15, atacante.pos_y * TAMANHO_CELULA + 15)
        end_pos = pygame.Vector2(alvo.pos_x * TAMANHO_CELULA + 15, alvo.pos_y * TAMANHO_CELULA + 15)
        if progresso <= 0.5:
            pos_interp = start_pos.lerp(end_pos, progresso * 2)
            pygame.draw.circle(tela, (255, 255, 0), pos_interp, 5)
    elif animacao_atual['tipo'] == 'ataque_area':
        raio_max = animacao_atual['raio'] * TAMANHO_CELULA
        raio_atual = raio_max * progresso
        centro = (animacao_atual['x'] * TAMANHO_CELULA + 15, animacao_atual['y'] * TAMANHO_CELULA + 15)
        superficie = pygame.Surface((raio_atual * 2, raio_atual * 2), pygame.SRCALPHA)
        cor = (255, 100, 0, int(200 * (1 - progresso)))
        pygame.draw.circle(superficie, cor, (raio_atual, raio_atual), raio_atual)
        tela.blit(superficie, (centro[0] - raio_atual, centro[1] - raio_atual))

def desenhar_log(tela, fonte, logs, max_altura=ALTURA_TELA):
    area_log = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, max_altura)
    pygame.draw.rect(tela, (10, 10, 10), area_log)
    titulo = fonte.render("LOG DE COMBATE", True, COR_TEXTO)
    tela.blit(titulo, (LARGURA_TABULEIRO + 20, 20))
    y_offset = 50
    for log_msg in logs:
        if y_offset + 20 > max_altura: # Evita desenhar fora da área
            break
        log_render = fonte.render(''.join(c for c in log_msg if c.isprintable()), True, COR_TEXTO)
        tela.blit(log_render, (LARGURA_TABULEIRO + 20, y_offset))
        y_offset += 20

def desenhar_info_personagem(tela, fonte, personagem, max_altura=ALTURA_TELA):
    area_info = pygame.Rect(LARGURA_TABULEIRO, 0, LARGURA_LOG, max_altura)
    pygame.draw.rect(tela, (15, 15, 15), area_info)
    y = 20
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

def desenhar_feedback_jogador(tela, unidade, motor):
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
                    tela.blit(movimento_surf, (nx * TAMANHO_CELULA, ny * TAMANHO_CELULA))

    # Mostra alcance de ataque
    for inimigo in motor.combatentes:
        if inimigo.time != unidade.time and inimigo.esta_vivo:
            dist = abs(x - inimigo.pos_x) + abs(y - inimigo.pos_y)
            if dist <= unidade.alcance:
                tela.blit(ataque_surf, (inimigo.pos_x * TAMANHO_CELULA, inimigo.pos_y * TAMANHO_CELULA))

def desenhar_tela_fim(tela, fonte, vencedor):
    overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))
    texto = f"O {vencedor} VENCEU!"
    texto_render = fonte.render(texto, True, COR_TEXTO)
    tela.blit(texto_render, texto_render.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2)))

def desenhar_comandos(tela, fonte):
    area_comandos = pygame.Rect(LARGURA_TABULEIRO, ALTURA_TELA - 150, LARGURA_LOG, 150)
    pygame.draw.rect(tela, (25, 25, 25), area_comandos) # Fundo para os comandos
    
    y_offset = ALTURA_TELA - 140
    comandos = [
        "Comandos:",
        "  - Clique em sua unidade para selecionar.",
        "  - Clique em azul para mover.",
        "  - Clique em vermelho para atacar.",
        "  - Clique fora para cancelar."
    ]
    for cmd in comandos:
        cmd_render = fonte.render(cmd, True, COR_TEXTO)
        tela.blit(cmd_render, (LARGURA_TABULEIRO + 10, y_offset))
        y_offset += 20
