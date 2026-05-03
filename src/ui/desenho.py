"""
Módulo Facade para renderização (Compatibilidade retroativa)
Reexporta funções dos módulos especializados em src/ui/
"""

from src.ui.render_ui import (
    PainelUI,
    desenhar_interface_retro,
    desenhar_menu_principal,
    desenhar_setup_batalha,
    desenhar_tela_carregando,
    desenhar_tela_salvando,
    desenhar_tela_fim,
    desenhar_tela_level_up,
    desenhar_dialogo
)

from src.ui.render_combate import (
    desenhar_cenario,
    desenhar_sprite,
    desenhar_personagens,
    desenhar_pre_visualizacao_ataque,
    desenhar_alcance_movimento,
    desenhar_alcance_habilidade,
    desenhar_barra_iniciativa,
    desenhar_ordem_iniciativa,
    desenhar_projeteis_e_efeitos,
    desenhar_log,
    desenhar_info_personagem,
    desenhar_inventario,
    desenhar_feedback_jogador,
    desenhar_comandos,
    desenhar_floating_texts,
    desenhar_feedback_invalido,
    desenhar_itens_no_chao
)

from src.ui.render_mundo import (
    desenhar_editor,
    desenhar_mapa_mundo
)
