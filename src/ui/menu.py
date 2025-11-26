import pygame
from ..config import *
from .componentes import Botao, Checkbox
from ..personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino

def desenhar_menu(tela, fonte, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay):
    tela.fill(COR_FUNDO)
    titulo_render = fonte.render("CONFIGURAR TIMES", True, COR_TEXTO)
    tela.blit(titulo_render, (LARGURA_TELA // 2 - titulo_render.get_width() // 2, 30))
    y_start, x_time_a, x_time_b = 120, LARGURA_TELA // 4, LARGURA_TELA * 3 // 4
    
    # --- Time A ---
    tela.blit(fonte.render("Time A", True, CORES_TIME["A"]), (x_time_a - 80, y_start - 40))
    for i, (classe, nome_classe) in enumerate(config_times['classes']):
        y_pos = y_start + i * 50
        tela.blit(fonte.render(f"{nome_classe}: {config_times['A'][classe]}", True, COR_TEXTO), (x_time_a - 80, y_pos + 5))

    # --- Time B ou Chefe ---
    tela.blit(fonte.render("Time B", True, CORES_TIME["B"]), (x_time_b - 80, y_start - 40))
    if checkbox_chefe.checked:
        # Interface de Edição do Chefe
        chefe_attrs = [("HP", "hp"), ("AC", "ac"), ("Dados Dano", "dado_dano")]
        for i, (nome_attr, key) in enumerate(chefe_attrs):
            y_pos = y_start + i * 80
            valor = f"{config_chefe[key]}"
            if key == 'dado_dano': valor = f"{config_chefe[key]}d8"
            tela.blit(fonte.render(f"{nome_attr}: {valor}", True, COR_TEXTO), (x_time_b - 80, y_pos + 5))
    else:
        # Interface Normal do Time B
        for i, (classe, nome_classe) in enumerate(config_times['classes']):
            y_pos = y_start + i * 50
            tela.blit(fonte.render(f"{nome_classe}: {config_times['B'][classe]}", True, COR_TEXTO), (x_time_b - 80, y_pos + 5))

    # Desenha todos os botões, mas só mostra os relevantes
    for nome, botao in botoes_ui.items():
        is_botao_chefe = nome.startswith('chefe_')
        is_botao_time_b = nome.startswith('B_')
        
        if checkbox_chefe.checked:
            if is_botao_time_b: continue
        else:
            if is_botao_chefe: continue

        botao.update_hover(pygame.mouse.get_pos())
        botao.desenhar(tela, fonte)
    
    checkbox_terreno.desenhar(tela)
    checkbox_auto.desenhar(tela)
    checkbox_chefe.desenhar(tela)
    checkbox_autoplay.desenhar(tela)

def setup_menu_ui():
    fonte = pygame.font.Font(None, 28)
    config_times = {
        'classes': [(Guerreiro, "Guerreiro"), (Mago, "Mago"), (Ladino, "Ladino"), (Arqueiro, "Arqueiro"), (Barbaro, "Bárbaro"), (Clerigo, "Clérigo"), (Paladino, "Paladino")],
        'A': {cls: 1 for cls in [Guerreiro, Mago, Ladino]},
        'B': {cls: 1 for cls in [Guerreiro, Mago, Ladino]}
    }
    for cls, _ in config_times['classes']:
        config_times['A'].setdefault(cls, 0)
        config_times['B'].setdefault(cls, 0)

    config_chefe = {'hp': 250, 'ac': 20, 'dado_dano': 2}

    botoes = {}
    y_start, x_a, x_b = 120, LARGURA_TELA//4, LARGURA_TELA*3//4
    
    # Botões Time A e B
    for i, (cls, _) in enumerate(config_times['classes']):
        y_pos = y_start + i * 50
        botoes[f'A_add_{i}'] = Botao(x_a + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'A_sub_{i}'] = Botao(x_a - 120, y_pos, 28, 28, "-", fonte)
        botoes[f'B_add_{i}'] = Botao(x_b + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'B_sub_{i}'] = Botao(x_b - 120, y_pos, 28, 28, "-", fonte)

    # Botões Chefe
    chefe_attrs = ["hp", "ac", "dado_dano"]
    for i, attr in enumerate(chefe_attrs):
        y_pos = y_start + i * 80
        botoes[f'chefe_add_{attr}'] = Botao(x_b + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'chefe_sub_{attr}'] = Botao(x_b - 120, y_pos, 28, 28, "-", fonte)

    botoes['iniciar'] = Botao(LARGURA_TELA//2 - 100, ALTURA_TELA - 100, 200, 50, "Iniciar Batalha", fonte)
    checkbox_terreno = Checkbox(LARGURA_TELA//2 - 100, ALTURA_TELA - 150, 25, "Gerar Terreno Aleatório", fonte)
    checkbox_auto = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 185, 25, "Rodada Automática", fonte)
    checkbox_chefe = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 220, 25, "Modo Chefe", fonte)
    checkbox_autoplay = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 255, 25, "Modo Auto-Play (Espectador)", fonte)
    
    return config_times, config_chefe, botoes, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay
