import json
import os
import sys

_BACKGROUNDS_CACHE = {}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def obter_background_cacheado(caminho_relativo, largura, altura, overlay_opacidade=None):
    """
    Retorna uma imagem de fundo convertida e escalada a partir de um cache global
    para evitar carregamento de arquivo e redimensionamento a cada frame.
    Permite opcionalmente aplicar um overlay escuro de opacidade (0-255).
    """
    chave = (caminho_relativo, largura, altura, overlay_opacidade)
    if chave in _BACKGROUNDS_CACHE:
        return _BACKGROUNDS_CACHE[chave]
    
    import pygame
    try:
        img_path = resource_path(caminho_relativo)
        img = pygame.image.load(img_path).convert()
        img_scaled = pygame.transform.scale(img, (largura, altura))
        
        # Aplica o overlay escuro apenas uma vez
        if overlay_opacidade is not None:
            overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, overlay_opacidade))
            img_scaled.blit(overlay, (0, 0))
            
        _BACKGROUNDS_CACHE[chave] = img_scaled
        return img_scaled
    except Exception as e:
        print(f"Erro ao carregar e cachear background {caminho_relativo}: {e}")
        fallback = pygame.Surface((largura, altura))
        fallback.fill((20, 20, 30))
        _BACKGROUNDS_CACHE[chave] = fallback
        return fallback

def calcular_distancia(p1, p2):
    return max(abs(p1.pos_x - p2.pos_x), abs(p1.pos_y - p2.pos_y))

def carregar_dados_personagens():
    with open(resource_path('dados/personagens.json'), 'r') as f:
        return json.load(f)

import random

def rolar_dado(faces=20):
    return random.randint(1, faces)

def rolar_d20(vantagem=False, desvantagem=False, logger=None):
    """
    Rola um d20 considerando vantagem e desvantagem.
    Retorna o valor final do dado.
    """
    r1 = rolar_dado(20)
    r2 = rolar_dado(20)
    
    final_roll = r1
    msg = ""
    
    # Mechanics:
    # If both V and D cancels out -> Normal Roll
    if vantagem and desvantagem:
        final_roll = r1
        # msg = " (Vantagem cancela Desvantagem)" # Optional log
        
    elif vantagem:
        final_roll = max(r1, r2)
        msg = f" (Vantagem [{r1}, {r2}])"
        
    elif desvantagem:
        final_roll = min(r1, r2)
        msg = f" (Desvantagem [{r1}, {r2}])"
    else:
        # Standard Roll
        final_roll = r1
    
    return final_roll, msg

def bresenham_line(x0, y0, x1, y1):
    """Yields points from (x0, y0) to (x1, y1) not inclusive of start/end."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
            
    # Remove start
    if points and points[0] == (x0, y0): points.pop(0)
    return points

def calcular_cobertura(atacante, alvo, tabuleiro):
    """
    Calcula bônus de cobertura (AC) para o alvo.
    Retorna 0 (Sem cobertura), 2 (Meia), 5 (3/4) ou 1000 (Total).
    Lógica Simplificada: Traça linha do centro ao centro. Se passar por obstáculo -> Meia Cobertura.
    """
    from src.config import TERRENO_PAREDE
    
    # Bresenham from attacker center to target center?
    # Grid coordinates are integers.
    path = bresenham_line(atacante.pos_x, atacante.pos_y, alvo.pos_x, alvo.pos_y)
    
    has_obstacle = False
    
    for px, py in path:
        # Check if point is valid board coordinate (Bresenham logic should stay within bounds if endpoints are in bounds)
        if not (0 <= px < tabuleiro.largura and 0 <= py < tabuleiro.altura): continue # Safe check
        
        # Check Wall (Total Block usually, but let's count as obstacle for now)
        if tabuleiro.terrain_grid[py][px] == TERRENO_PAREDE:
             # Wall blocks LOS -> Total Cover usually. 
             # But if Bresenham hits a wall between two visible units (corner case)?
             # Let's say Wall = Total Cover (Block)
             return 1000 
             
        # Check Creature (Soft Cover)
        char = tabuleiro.get_personagem_em(px, py)
        if char is not None and char != atacante and char != alvo:
            # Creature in the way -> Half Cover (+2)
            has_obstacle = True
            
    if has_obstacle:
        return 2 # Half Cover
        
    return 0 # No Cover
