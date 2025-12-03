import pygame
from ..config import *
from .componentes import Botao, Checkbox
from ..personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Chefe
from ..personagens.rei_goblin import ReiGoblin
from ..personagens.lorde_lich import LordeLich
from ..personagens.dragao_anciao import DragaoAnciao

def desenhar_menu(tela, fonte, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, bosses, selected_boss_index, game_images, volume_sfx):
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
        # --- Boss Selection UI ---
        selected_boss = bosses[selected_boss_index]
        boss_class = selected_boss["classe"]
        boss_name = selected_boss["nome"]

        # Display boss name
        tela.blit(fonte.render(boss_name, True, COR_TEXTO), (x_time_b - 80, y_start))

        # Display boss "print" (image)
        boss_img_key = f"personagem_{boss_class.__name__.lower()}"
        if boss_img_key in game_images and game_images[boss_img_key]:
            img = game_images[boss_img_key]
            # Scale image to a reasonable size for the menu
            scaled_img = pygame.transform.scale(img, (100, 100))
            tela.blit(scaled_img, (x_time_b - 50, y_start + 40))

        # Display boss stats and abilities
        # Create a temporary instance to get stats
        temp_boss = boss_class("temp", "B")
        y_offset = y_start + 160
        stats_to_show = [
            f"HP: {temp_boss.hp_max}",
            f"AC: {temp_boss.ac}",
            f"Ataque: +{temp_boss.bonus_ataque}",
            f"Dano: {temp_boss.dado_dano[0]}d{temp_boss.dado_dano[1]} +{temp_boss.bonus_dano}",
        ]
        for stat in stats_to_show:
            tela.blit(fonte.render(stat, True, COR_TEXTO), (x_time_b - 80, y_offset))
            y_offset += 30

        y_offset += 10
        tela.blit(fonte.render("Habilidades:", True, COR_TEXTO), (x_time_b - 80, y_offset))
        y_offset += 25
        for ability in temp_boss.cooldowns:
            tela.blit(fonte.render(f"- {ability.replace('_', ' ').title()}", True, COR_TEXTO), (x_time_b - 60, y_offset))
            y_offset += 25
        
        y_offset += 10
        tela.blit(fonte.render("Imunidades:", True, COR_TEXTO), (x_time_b - 80, y_offset))
        y_offset += 25
        for immunity in temp_boss.imunidades:
            tela.blit(fonte.render(f"- {immunity}", True, COR_TEXTO), (x_time_b - 60, y_offset))
            y_offset += 25

    else:
        # Interface Normal do Time B
        for i, (classe, nome_classe) in enumerate(config_times['classes']):
            y_pos = y_start + i * 50
            tela.blit(fonte.render(f"{nome_classe}: {config_times['B'][classe]}", True, COR_TEXTO), (x_time_b - 80, y_pos + 5))

    # Draw most buttons with filtering
    for nome, botao in botoes_ui.items():
        is_botao_chefe_attr = nome.startswith('chefe_')
        is_botao_time_b = nome.startswith('B_')
        is_boss_nav = nome in ['next_boss', 'prev_boss']
        is_vol_btn = nome.startswith('sfx_')

        if is_vol_btn: continue # Skip volume buttons here

        if checkbox_chefe.checked:
            if is_botao_time_b or is_botao_chefe_attr: continue
        else:
            if is_boss_nav or is_botao_chefe_attr: continue

        botao.update_hover(pygame.mouse.get_pos())
        botao.desenhar(tela, fonte)

    # Draw checkboxes
    checkbox_terreno.desenhar(tela)
    checkbox_auto.desenhar(tela)
    checkbox_chefe.desenhar(tela)
    checkbox_autoplay.desenhar(tela)
    
    # Draw volume controls separately
    y_volume = checkbox_autoplay.y + 40
    tela.blit(fonte.render(f"Volume SFX: {int(volume_sfx * 100)}%", True, COR_TEXTO), (checkbox_autoplay.x, y_volume))
    botoes_ui['sfx_vol_down'].update_hover(pygame.mouse.get_pos())
    botoes_ui['sfx_vol_down'].desenhar(tela, fonte)
    botoes_ui['sfx_vol_up'].update_hover(pygame.mouse.get_pos())
    botoes_ui['sfx_vol_up'].desenhar(tela, fonte)

def setup_menu_ui():
    fonte = pygame.font.Font(None, 28)
    config_times = {
        'classes': [(Guerreiro, "Guerreiro"), (Mago, "Mago"), (Ladino, "Ladino"), (Arqueiro, "Arqueiro"), (Barbaro, "Bárbaro"), (Clerigo, "Clérigo"), (Paladino, "Paladino"), (Druida, "Druida"), (Bruxo, "Bruxo")],
        'A': {cls: 1 for cls in [Guerreiro, Mago, Ladino]},
        'B': {cls: 1 for cls in [Guerreiro, Mago, Ladino]}
    }
    for cls, _ in config_times['classes']:
        config_times['A'].setdefault(cls, 0)
        config_times['B'].setdefault(cls, 0)

    config_chefe = {'hp': 250, 'ac': 20, 'dado_dano': 2}
    
    bosses = [
        {"classe": Chefe, "nome": "Chefe Padrão"},
        {"classe": ReiGoblin, "nome": "Rei Goblin"},
        {"classe": LordeLich, "nome": "Lorde Lich"},
        {"classe": DragaoAnciao, "nome": "Dragão Ancião"}
    ]

    botoes = {}
    y_start, x_a, x_b = 120, LARGURA_TELA//4, LARGURA_TELA*3//4

    # Botões Time A e B
    for i, (cls, _) in enumerate(config_times['classes']):
        y_pos = y_start + i * 50
        botoes[f'A_add_{i}'] = Botao(x_a + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'A_sub_{i}'] = Botao(x_a - 120, y_pos, 28, 28, "-", fonte)
        botoes[f'B_add_{i}'] = Botao(x_b + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'B_sub_{i}'] = Botao(x_b - 120, y_pos, 28, 28, "-", fonte)

    # Botões Chefe (genéricos, não mais de stats)
    botoes['next_boss'] = Botao(x_b + 60, y_start, 100, 30, "Próximo", fonte)
    botoes['prev_boss'] = Botao(x_b - 180, y_start, 100, 30, "Anterior", fonte)


    botoes['iniciar'] = Botao(LARGURA_TELA//2 - 100, ALTURA_TELA - 100, 200, 50, "Iniciar Batalha", fonte)
    checkbox_terreno = Checkbox(LARGURA_TELA//2 - 100, ALTURA_TELA - 150, 25, "Gerar Terreno Aleatório", fonte)
    checkbox_auto = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 185, 25, "Rodada Automática", fonte)
    checkbox_chefe = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 220, 25, "Modo Chefe", fonte)
        checkbox_autoplay = Checkbox(LARGURA_TELA // 2 - 100, ALTURA_TELA - 255, 25, "Modo Auto-Play (Espectador)", fonte)
    
        # Volume controls
        y_volume = checkbox_autoplay.y + 40
        botoes['sfx_vol_down'] = Botao(checkbox_autoplay.x + 200, y_volume, 28, 28, "-", fonte)
        botoes['sfx_vol_up'] = Botao(checkbox_autoplay.x + 260, y_volume, 28, 28, "+", fonte)
        
        return config_times, config_chefe, botoes, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, bosses