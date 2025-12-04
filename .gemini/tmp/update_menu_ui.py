
file_path = 'src/ui/menu.py'

new_setup_menu_ui_content = '''def setup_menu_ui():
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
    
    # --- Tabs ---
    menu_tabs = {}
    tab_width = 150
    tab_height = 40
    tab_x_start = LARGURA_TELA // 2 - (tab_width * 2) // 2 # Center the tabs
    tab_y = 90

    menu_tabs["times"] = Tab(tab_x_start, tab_y, tab_width, tab_height, "Times", fonte, "times")
    menu_tabs["configuracoes"] = Tab(tab_x_start + tab_width, tab_y, tab_width, tab_height, "Configurações", fonte, "configuracoes")

    tab_content_y_start = 150 # Where the content for the tabs will begin

    # Botões Time A e B
    x_a, x_b = LARGURA_TELA//4, LARGURA_TELA*3//4
    for i, (cls, _) in enumerate(config_times['classes']):
        y_pos = tab_content_y_start + i * 50
        botoes[f'A_add_{i}'] = Botao(x_a + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'A_sub_{i}'] = Botao(x_a - 120, y_pos, 28, 28, "-", fonte)
        botoes[f'B_add_{i}'] = Botao(x_b + 60, y_pos, 28, 28, "+", fonte)
        botoes[f'B_sub_{i}'] = Botao(x_b - 120, y_pos, 28, 28, "+", fonte)

    # Botões Chefe (genéricos, não mais de stats)
    botoes['next_boss'] = Botao(x_b + 60, tab_content_y_start, 100, 30, "Próximo", fonte)
    botoes['prev_boss'] = Botao(x_b - 180, tab_content_y_start, 100, 30, "Anterior", fonte)


    # Checkboxes, position adjusted for the "configuracoes" tab
    checkbox_terreno = Checkbox(LARGURA_TELA//2 - 150, tab_content_y_start, 25, "Gerar Terreno Aleatório", fonte)
    checkbox_auto = Checkbox(LARGURA_TELA // 2 - 150, tab_content_y_start + 40, 25, "Rodada Automática", fonte)
    checkbox_chefe = Checkbox(LARGURA_TELA // 2 - 150, tab_content_y_start + 80, 25, "Modo Chefe", fonte)
    checkbox_autoplay = Checkbox(LARGURA_TELA // 2 - 150, tab_content_y_start + 120, 25, "Modo Auto-Play (Espectador)", fonte)
    
    # Volume controls - position adjusted
    y_volume = tab_content_y_start + 240 # Below campaign checkbox
    botoes['sfx_vol_down'] = Botao(LARGURA_TELA//2 - 150 + 200, y_volume, 28, 28, "-", fonte)
    botoes['sfx_vol_up'] = Botao(LARGURA_TELA//2 - 150 + 260, y_volume, 28, 28, "+", fonte)
    
    return config_times, config_chefe, botoes, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, bosses, menu_tabs
'''

with open(file_path, 'r') as f:
    content = f.read()

start_marker = 'def setup_menu_ui():'
end_marker_old = '    return config_times, config_chefe, botoes, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay, bosses' # This will be the end of the old function

start_index = content.find(start_marker)
end_index = content.find(end_marker_old, start_index) + len(end_marker_old)

if start_index != -1 and end_index != -1:
    before_function = content[:start_index]
    after_function = content[end_index:]
    
    new_content = before_function + new_setup_menu_ui_content + after_function

    with open(file_path, 'w') as f:
        f.write(new_content)
    print("setup_menu_ui function updated successfully.")
else:
    print("Error: Could not find setup_menu_ui function or its old return statement.")

