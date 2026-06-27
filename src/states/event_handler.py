import pygame
import json
from src.config import *
from src.utils import calcular_distancia
from src.perks import PERKS
from src.personagens.guerreiro import Guerreiro
from src.personagens.protagonistas import Novak, Yukito, Rilem, Koema

class EventHandler:
    def __init__(self, game):
        """
        Initializes the EventHandler with a reference to the main Game instance 
        to access its state (motor, tabuleiro, ui elements, etc).
        """
        self.game = game

    def handle_events(self, mouse_pos, personagem_ativo):
        g = self.game  # Shortcut for readability
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                g.rodando = False
            
            # Se o diálogo estiver ativo, apenas ele recebe input
            if g.dialogo.ativo:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                        g.dialogo.processar_input()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        g.dialogo.processar_input()
                continue # Impede outros eventos

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3): # Left or Right click
                    self._handle_mouse_click(event, mouse_pos, personagem_ativo)
                    
            elif g.estado_jogo == ESTADO_JOGO_CUTSCENE:
                 if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                      g.cutscene_manager.pular()


    def _handle_mouse_click(self, event, mouse_pos, personagem_ativo):
        g = self.game
        
        if g.estado_jogo == ESTADO_JOGO_MENU_PRINCIPAL:
            self._handle_menu_principal_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_DEV:
            self._handle_dev_menu_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_DEV_CHAPTERS:
            self._handle_dev_chapters_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_LEVEL_UP:
            self._handle_level_up_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_MAPA_MUNDO:
             self._handle_mapa_mundo_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_SETUP:
            self._handle_setup_click(event, mouse_pos)
        elif g.estado_jogo == ESTADO_JOGO_COMBATE:
            self._handle_combate_click(event, mouse_pos, personagem_ativo)
        elif g.estado_jogo == ESTADO_JOGO_EDITOR:
            self._handle_editor_click(event, mouse_pos)

    def _handle_menu_principal_click(self, event, mouse_pos):
        g = self.game
        if event.button == 1: # Menu is Left Click only
            for nome, botao in g.botoes_menu_principal.items():
                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    if nome == 'nova_batalha':
                        g.estado_jogo = ESTADO_JOGO_SETUP
                        g.active_tab_id = "times"
                        for t in g.menu_tabs.values(): t.selected = False
                        g.menu_tabs["times"].selected = True
                    elif nome == 'nova_campanha':
                        g.checkbox_campanha.checked = True
                        g.checkbox_chefe.checked = False
                        g.campaign_manager.reset()
                        g.iniciar_batalha_campanha_custom()
                    elif nome == 'continuar':
                        if g.campaign_manager.carregar_campanha():
                            g.checkbox_campanha.checked = True
                            g.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
                        else:
                            print("Nenhum save encontrado!")
                    elif nome == 'opcoes':
                        g.estado_jogo = ESTADO_JOGO_SETUP
                        g.active_tab_id = "configuracoes"
                        for t in g.menu_tabs.values(): t.selected = False
                        g.menu_tabs["configuracoes"].selected = True
                    elif nome == 'sair':
                        g.rodando = False
                    elif nome == 'dev':
                        g.estado_jogo = ESTADO_JOGO_DEV

    def _handle_dev_menu_click(self, event, mouse_pos):
         g = self.game
         if event.button == 1:
            for nome, botao in g.botoes_dev.items():
                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    if nome == 'voltar':
                        g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    elif nome == 'teste_combate':
                        try:
                            args_a = [0] * 12
                            args_a[0] = 1 # Guerreiro
                            args_b = [0] * 12
                            args_b[9] = 1 # Goblin
                            from src.motor_combate import MotorCombate
                            g.motor = MotorCombate(args_a + args_b, sound_player=g.play_sound, gerar_terreno=True)
                            g.estado_jogo = ESTADO_JOGO_COMBATE
                            g.log_combate.clear()
                            g.log_combate.append(("--- MODO DEV: TESTE COMBATE ---", COR_CRITICO))
                            g.tocar_musica('batalha')
                        except Exception as e:
                            print(f"Erro dev combate: {e}")
                    elif nome == 'teste_boss':
                        g.campaign_manager.reset()
                        g.iniciar_batalha_campanha_custom()
                    elif nome == 'teste_editor':
                        g.estado_jogo = ESTADO_JOGO_EDITOR
                    elif nome == 'teste_mapa':
                        g.estado_jogo = ESTADO_JOGO_MAPA_MUNDO
                    elif nome == 'teste_cutscene':
                        g.iniciar_sequencia_final()
                    elif nome == 'teste_fim':
                        g.motor.vencedor = "Time A (Dev)"
                        g.estado_jogo = ESTADO_JOGO_FIM
                    elif nome == 'selecao_capitulos':
                        g.estado_jogo = ESTADO_JOGO_DEV_CHAPTERS
                    elif nome == 'jogar_campanha':
                        g.checkbox_campanha.checked = True
                        g.campaign_manager.reset()
                        g.iniciar_proxima_batalha_campanha()
                    elif nome == 'teste_dialogo':
                        g.dialogo.iniciar_dialogo([
                            ("Dev", "Testando sistema de diálogo completo.", None),
                            ("Heroi", "Tudo parece operacional, comandante.", "guerreiro"),
                            ("Vilão", "Não por muito tempo...", "lich"),
                            ("Sistema", "Fim do teste.", None)
                        ])
                        g.estado_jogo = ESTADO_JOGO_NARRATIVA
                    elif nome == 'toggle_god_mode':
                        g.god_mode = not g.god_mode
                        status = "ON" if g.god_mode else "OFF"
                        bg = (50, 200, 50) if g.god_mode else (100, 50, 50)
                        g.botoes_dev['toggle_god_mode'].texto = f"God Mode: {status}"
                        g.botoes_dev['toggle_god_mode'].cor_fundo = bg
                        if g.motor:
                            for p in g.motor.personagens:
                                if p.time == TIME_A: p.invulneravel = g.god_mode
                    elif nome == 'add_resources':
                        g.campaign_manager.ganhar_xp(1000)
                        g.campaign_manager.gold += 1000
                        print("Dev: +1000 XP/Gold added.")
                    elif nome == 'unlock_all':
                        for pid in PERKS.keys():
                            if pid not in g.campaign_manager.perks_desbloqueados:
                                g.campaign_manager.perks_desbloqueados.append(pid)
                        print("Dev: All Perks unlocked.")
                    elif nome == 'teste_particulas':
                        pass # TODO: Hook into particle system properly
                    elif nome == 'teste_levelup':
                        dummy = Guerreiro("Teste", "A")
                        dummy.nivel = 5
                        dummy.xp = 0
                        g.personagem_level_up = dummy
                        g.estado_jogo = ESTADO_JOGO_LEVEL_UP
                        g.modo_level_up = 'stat'
                        g.verificar_opcoes_level_up()
                    elif nome == 'tree_warrior':
                        dummy = Novak("Novak Debug", "A")
                        dummy.nivel = 10
                        g.personagem_level_up = dummy
                        g.estado_jogo = ESTADO_JOGO_LEVEL_UP
                        g.modo_level_up = 'perk'
                        g.verificar_opcoes_level_up()
                    elif nome == 'tree_mage':
                        dummy = Yukito("Yukito Debug", "A")
                        dummy.nivel = 10
                        g.personagem_level_up = dummy
                        g.estado_jogo = ESTADO_JOGO_LEVEL_UP
                        g.modo_level_up = 'perk'
                        g.verificar_opcoes_level_up()
                    elif nome == 'tree_rogue':
                        dummy = Rilem("Rilem Debug", "A")
                        dummy.nivel = 10
                        g.personagem_level_up = dummy
                        g.estado_jogo = ESTADO_JOGO_LEVEL_UP
                        g.modo_level_up = 'perk'
                        g.verificar_opcoes_level_up()
                    elif nome == 'tree_cleric':
                        dummy = Koema("Koema Debug", "A")
                        dummy.nivel = 10
                        g.personagem_level_up = dummy
                        g.estado_jogo = ESTADO_JOGO_LEVEL_UP
                        g.modo_level_up = 'perk'
                        g.verificar_opcoes_level_up()

    def _handle_dev_chapters_click(self, event, mouse_pos):
        g = self.game
        if event.button == 1:
            for key, botao in g.botoes_capitulos.items():
                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    if key == 'voltar_dev':
                        g.estado_jogo = ESTADO_JOGO_DEV
                    elif key.startswith('cap_'):
                        idx = int(key.split('_')[1])
                        g.iniciar_capitulo_dev(idx)

    def _handle_level_up_click(self, event, mouse_pos):
        g = self.game
        if event.button == 1:
            clicked_btn_name = None
            for nome, botao in g.botoes_level_up.items():
                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    clicked_btn_name = nome
                    break
            
            if clicked_btn_name:
                personagem = g.personagem_level_up
                if g.modo_level_up == 'stat':
                    if clicked_btn_name == 'forca': personagem._forca += 1
                    elif clicked_btn_name == 'destreza': personagem._destreza += 1
                    elif clicked_btn_name == 'constituicao': personagem._constituicao += 1
                    elif clicked_btn_name == 'inteligencia': personagem._inteligencia += 1
                    elif clicked_btn_name == 'sabedoria': personagem._sabedoria += 1
                    elif clicked_btn_name == 'carisma': personagem._carisma += 1
                    
                    g.modo_level_up = 'perk'
                    g.verificar_opcoes_level_up()
                    if g.modo_level_up == 'stat': # Se não mudou para perk é pq não tem
                        g.estado_jogo = g.previous_state if g.previous_state else ESTADO_JOGO_COMBATE
                        g.personagem_level_up = None

                elif g.modo_level_up == 'perk':
                    if clicked_btn_name == 'concluir':
                         g.estado_jogo = g.previous_state if g.previous_state else ESTADO_JOGO_COMBATE
                         g.personagem_level_up = None
                    elif clicked_btn_name.startswith("perk_"):
                        perk_id = clicked_btn_name.replace("perk_", "")
                        classe = personagem.classe_nome
                        perk_data = next((p for p in PERKS.get(classe, []) if p['id'] == perk_id), None)
                        if perk_data and personagem.pode_desbloquear_perk(perk_data):
                            personagem.adquirir_perk(perk_id)
                            g.play_sound('level_up') 
                            g.estado_jogo = g.previous_state if g.previous_state else ESTADO_JOGO_COMBATE
                            g.personagem_level_up = None

        if event.button == 3: 
            g.estado_jogo = ESTADO_JOGO_DEV

    def _handle_mapa_mundo_click(self, event, mouse_pos):
        g = self.game
        if event.button == 1:
            if g.botoes_ui['voltar_menu'].rect.collidepoint(mouse_pos):
                 g.play_sound('button_click')
                 g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            
            if mouse_pos[1] > 50:
                g.campaign_manager.destino_movimento = mouse_pos
                
            for local in g.campaign_manager.locais:
                dist = ((local['pos'][0] - mouse_pos[0])**2 + (local['pos'][1] - mouse_pos[1])**2)**0.5
                if dist < local['raio']:
                    g.play_sound('button_click')
                    g.checkbox_campanha.checked = True
                    g.campaign_manager.nivel_atual = local['evento_id']
                    g.iniciar_proxima_batalha_campanha()

    def _handle_setup_click(self, event, mouse_pos):
        g = self.game
        if event.button == 1:
            for tab_id, tab in g.menu_tabs.items():
                if tab.rect.collidepoint(mouse_pos):
                    g.active_tab_id = tab_id
                    for t in g.menu_tabs.values(): t.selected = False
                    tab.selected = True
                    g.play_sound('button_click')
                    return

            for nome, botao in g.botoes_ui.items():
                is_botao_chefe_attr = nome.startswith('chefe_')
                is_botao_time_b = nome.startswith('B_')
                is_boss_nav = nome in ['next_boss', 'prev_boss']
                
                visible = True
                if g.active_tab_id == "times":
                    if is_botao_chefe_attr or is_boss_nav or is_botao_time_b or nome.startswith('A_'):
                        if g.checkbox_chefe.checked:
                            if is_botao_time_b: visible = False
                        else:
                            if is_boss_nav or is_botao_chefe_attr: visible = False
                    else:
                        visible = False 
                elif g.active_tab_id == "configuracoes":
                    if nome in ['sfx_vol_down', 'sfx_vol_up'] or nome.startswith('res_'):
                        visible = True
                    else:
                        visible = False 

                if nome in ['iniciar', 'editor_mapas', 'voltar_menu']:
                    visible = True

                if visible and botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    
                    if nome == 'iniciar':
                        if g.checkbox_campanha.checked:
                            g.iniciar_proxima_batalha_campanha()
                        else:
                            try:
                                args = []
                                for cls, _ in g.config_times['classes']:
                                    args.append(g.config_times[TIME_A].get(cls, 0))

                                if not g.checkbox_chefe.checked:
                                    for cls, _ in g.config_times['classes']:
                                        args.append(g.config_times[TIME_B].get(cls, 0))
                                
                                from src.motor_combate import MotorCombate
                                g.motor = MotorCombate(
                                    args,
                                    gerar_terreno=g.checkbox_terreno.checked,
                                    mapa_custom=g.editor_mapa if g.checkbox_mapa_custom.checked else None,
                                    sound_player=g.play_sound,
                                    modo_chefe=g.checkbox_chefe.checked,
                                    stats_chefe=g.config_chefe if g.checkbox_chefe.checked else None,
                                    boss_class=g.bosses[g.selected_boss_index]["classe"] if g.checkbox_chefe.checked else None
                                )
                                
                                g.estado_jogo = ESTADO_JOGO_COMBATE
                                g.game_over_processed = False
                                g.tocar_musica('batalha')
                                g.log_combate.clear()
                                g.log_combate.append(("A batalha começou!", COR_TEXTO))
                                
                                g.dialogo.iniciar_dialogo([
                                    ("Narrador", "A batalha está prestes a começar!", None),
                                    ("Guerreiro", "Preparem-se para lutar!", "guerreiro"),
                                    ("Inimigo", "Vocês não passarão!", "goblin")
                                ])

                                if g.checkbox_limitadores.checked:
                                    g.motor.tabuleiro.adicionar_limitadores()
                                    
                                g.atualizar_visibilidade() 

                            except ValueError as e:
                                print(f"Erro ao iniciar batalha: {e}")
                                g.log_combate.append((f"Erro: {e}", COR_DANO))
                    elif nome == 'voltar_menu':
                        g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    elif nome == 'editor_mapas':
                        g.estado_jogo = ESTADO_JOGO_EDITOR
                    elif nome.startswith('A_add_'):
                        idx = int(nome.split('_')[-1])
                        classe = g.config_times['classes'][idx][0]
                        g.config_times[TIME_A][classe] += 1
                    elif nome.startswith('A_sub_'):
                        idx = int(nome.split('_')[-1])
                        classe = g.config_times['classes'][idx][0]
                        if g.config_times[TIME_A][classe] > 0:
                            g.config_times[TIME_A][classe] -= 1
                    elif nome.startswith('B_add_'):
                        idx = int(nome.split('_')[-1])
                        classe = g.config_times['classes'][idx][0]
                        g.config_times[TIME_B][classe] += 1
                    elif nome.startswith('B_sub_'):
                        idx = int(nome.split('_')[-1])
                        classe = g.config_times['classes'][idx][0]
                        if g.config_times[TIME_B][classe] > 0:
                            g.config_times[TIME_B][classe] -= 1
                    elif nome == 'chefe_add_hp':
                        g.config_chefe['hp'] += 10
                    elif nome == 'chefe_sub_hp':
                        if g.config_chefe['hp'] > 10: g.config_chefe['hp'] -= 10
                    elif nome == 'chefe_add_ataque':
                        g.config_chefe['ataque'] += 1
                    elif nome == 'chefe_sub_ataque':
                        if g.config_chefe['ataque'] > 0: g.config_chefe['ataque'] -= 1
                    elif nome == 'chefe_add_ac':
                        g.config_chefe['ac'] += 1
                    elif nome == 'chefe_sub_ac':
                        if g.config_chefe['ac'] > 0: g.config_chefe['ac'] -= 1
                    elif nome == 'next_boss':
                        g.selected_boss_index = (g.selected_boss_index + 1) % len(g.bosses)
                    elif nome == 'prev_boss':
                        g.selected_boss_index = (g.selected_boss_index - 1) % len(g.bosses)
                    elif nome == 'sfx_vol_down':
                        g.volume_sfx = max(0.0, g.volume_sfx - 0.1)
                        pygame.mixer.music.set_volume(g.volume_sfx)
                    elif nome == 'sfx_vol_up':
                        g.volume_sfx = min(1.0, g.volume_sfx + 0.1)
                        pygame.mixer.music.set_volume(g.volume_sfx)
                    elif nome.startswith('res_'):
                        w, h = 1024, 768
                        if nome == 'res_800': w, h = 800, 600
                        elif nome == 'res_1024': w, h = 1024, 768
                        elif nome == 'res_1280': w, h = 1280, 720
                        
                        settings = {"width": w, "height": h}
                        try:
                            with open("settings.json", "w") as f:
                                json.dump(settings, f)
                            print(f"Resolução salva: {w}x{h}. Reinicie o jogo.")
                            if nome == 'res_fullscreen':
                                 g.rodando = False
                        except Exception as e:
                            print(f"Erro ao salvar settings: {e}")
                            
                        if nome == 'res_fullscreen':
                             g.rodando = False 

        if g.active_tab_id == "times" and event.type == pygame.MOUSEBUTTONDOWN:
            coluna_a_x = LARGURA_TELA // 4 - 150
            coluna_b_x = LARGURA_TELA * 3 // 4 - 150
            y_start = 200 
            espacamento_y = 45
            largura_linha = 350
            altura_linha = 40
            
            for i, (classe, nome_classe) in enumerate(g.config_times['classes']):
                y_pos = y_start + i * espacamento_y
                rect = pygame.Rect(coluna_a_x, y_pos, largura_linha, altura_linha)
                
                if rect.collidepoint(mouse_pos):
                    if event.button == 1: 
                        g.config_times['A'][classe] += 1
                        g.play_sound('button_click')
                    elif event.button == 3: 
                        if g.config_times['A'][classe] > 0:
                            g.config_times['A'][classe] -= 1
                            g.play_sound('button_click')
            
            if not g.checkbox_chefe.checked:
                for i, (classe, nome_classe) in enumerate(g.config_times['classes']):
                    y_pos = y_start + i * espacamento_y
                    rect = pygame.Rect(coluna_b_x, y_pos, largura_linha, altura_linha)
                    
                    if rect.collidepoint(mouse_pos):
                        if event.button == 1: 
                            g.config_times['B'][classe] += 1
                            g.play_sound('button_click')
                        elif event.button == 3: 
                            if g.config_times['B'][classe] > 0:
                                g.config_times['B'][classe] -= 1
                                g.play_sound('button_click')

        if g.active_tab_id == "configuracoes":
            if g.checkbox_terreno.rect.collidepoint(mouse_pos): g.checkbox_terreno.toggle()
            if g.checkbox_auto.rect.collidepoint(mouse_pos): g.checkbox_auto.toggle()
            if g.checkbox_chefe.rect.collidepoint(mouse_pos): g.checkbox_chefe.toggle()
            if g.checkbox_autoplay.rect.collidepoint(mouse_pos): g.checkbox_autoplay.toggle()
            if g.checkbox_mapa_custom.rect.collidepoint(mouse_pos): g.checkbox_mapa_custom.toggle()
            if g.checkbox_campanha.rect.collidepoint(mouse_pos): g.checkbox_campanha.toggle()
            if g.checkbox_limitadores.rect.collidepoint(mouse_pos): g.checkbox_limitadores.toggle()


    def _handle_combate_click(self, event, mouse_pos, personagem_ativo):
        g = self.game

        if g.motor and g.motor.vencedor:
            if event.button == 1:
                for nome, botao in g.botoes_fim.items():
                    if botao.rect.collidepoint(mouse_pos):
                        g.play_sound('button_click')
                        if nome == 'reiniciar':
                             if g.checkbox_campanha.checked:
                                 g.iniciar_proxima_batalha_campanha()
                             else:
                                 g.estado_jogo = ESTADO_JOGO_SETUP
                        elif nome == 'voltar_menu':
                             g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            return

        if event.button == 1:
            for nome, botao in list(g.botoes_combate.items()):
                is_skill_btn = nome.startswith('habilidade_') or nome == 'voltar_skills'
                is_action_btn = nome.startswith('acao_') or nome == 'voltar_acoes'
                is_main_btn = nome in ['atacar', 'habilidade', 'item', 'acoes', 'proxima_acao']
                
                if g.skill_menu_open:
                    if is_main_btn or is_action_btn: continue
                elif g.actions_menu_open:
                    if is_main_btn or is_skill_btn: continue
                else:
                    if is_skill_btn or is_action_btn: continue

                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    
                    if nome == 'proxima_acao':
                            g.log_combate.append((f"{personagem_ativo.nome} passou a vez.", COR_TEXTO))
                            g.habilidade_selecionada = None
                            g.acao_action_selecionada = None
                            g.skill_menu_open = False
                            g.actions_menu_open = False
                            g.motor.avancar_turno()

                    elif nome == 'acoes': 
                         if personagem_ativo and personagem_ativo.time == TIME_A:
                             g.actions_menu_open = True
                             g.play_sound('button_click')
                             g.atualizar_botoes_acoes(personagem_ativo)

                    elif nome == 'voltar_acoes':
                         g.actions_menu_open = False
                         g.acao_action_selecionada = None
                         
                    elif nome == 'habilidade': 
                         if personagem_ativo and personagem_ativo.time == TIME_A:
                             g.skill_menu_open = True
                             g.play_sound('button_click')
                             g.atualizar_botoes_habilidade(personagem_ativo)

                    elif nome == 'voltar_skills': 
                         g.skill_menu_open = False
                         g.habilidade_selecionada = None
                         g.play_sound('button_click')

                    elif nome.startswith('habilidade_'):
                        hab_key = nome.split('habilidade_')[1]
                        if g.habilidade_selecionada == hab_key:
                            g.habilidade_selecionada = None
                        else:
                            g.habilidade_selecionada = hab_key
                            g.log_combate.append((f"Habilidade selecionada: {personagem_ativo.habilidades[hab_key]['nome']}", COR_TEXTO))
                    
                    elif nome == 'acao_dash':
                        if personagem_ativo.usar_dash(g.log_combate):
                            g.motor.avancar_turno() 
                            g.actions_menu_open = False

                    elif nome == 'acao_disengage':
                        if personagem_ativo.usar_disengage(g.log_combate):
                            g.motor.avancar_turno()
                            g.actions_menu_open = False

                    elif nome == 'acao_dodge':
                        if personagem_ativo.usar_dodge(g.log_combate):
                            g.motor.avancar_turno()
                            g.actions_menu_open = False
                            
                    elif nome in ['acao_help', 'acao_grapple', 'acao_shove']:
                        action = nome.replace('acao_', '')
                        if g.acao_action_selecionada == action:
                            g.acao_action_selecionada = None
                        else:
                            g.acao_action_selecionada = action
                            g.log_combate.append((f"Ação selecionada: {action.title()}. Clique no alvo.", COR_TEXTO))

                    elif nome == 'salvar':
                        g.motor.salvar_jogo()
                        g.log_combate.append(("Jogo salvo!", COR_XP))
                    elif nome == 'carregar':
                        if g.motor.carregar_jogo():
                            g.log_combate.append(("Jogo carregado!", COR_XP))
                            g.atualizar_visibilidade()
                    elif nome == 'voltar_menu':
                        g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    elif nome == 'reiniciar':
                        g.estado_jogo = ESTADO_JOGO_SETUP
                    elif nome == 'cancelar':
                        g.estado_jogo = ESTADO_JOGO_SETUP
                        g.tocar_musica('menu')
                    elif nome == 'cheat_win':
                        g.iniciar_sequencia_final()

        grid_pos = g.screen_to_grid(mouse_pos[0], mouse_pos[1])
        if grid_pos is not None and g.motor:
            grid_x, grid_y = grid_pos
            clicked_unit = g.motor.tabuleiro.get_personagem_em(grid_x, grid_y)
            if clicked_unit:
                g.unidade_selecionada = clicked_unit

            if personagem_ativo and personagem_ativo.time == TIME_A and not g.animacao_atual and not g.fila_animacoes:
                
                if g.acao_action_selecionada:
                    if not clicked_unit: 
                        g.log_combate.append(("Selecione um alvo válido.", COR_DANO))
                    else:
                        dist = calcular_distancia(personagem_ativo, clicked_unit)
                        success = False
                        
                        if g.acao_action_selecionada == 'help':
                            if dist <= 1.5: 
                                success = personagem_ativo.usar_help(clicked_unit, g.log_combate)
                            else:
                                g.log_combate.append(("Alvo muito longe para Ajudar/Distrair!", COR_DANO))
                                
                        elif g.acao_action_selecionada == 'grapple':
                            if dist <= 1.5:
                                success = personagem_ativo.usar_grapple(clicked_unit, g.log_combate)
                            else:
                                g.log_combate.append(("Alvo fora de alcance (Melee)!", COR_DANO))
                        
                        elif g.acao_action_selecionada == 'shove':
                            if dist <= 1.5:
                                success = personagem_ativo.usar_shove(clicked_unit, g.log_combate)
                            else:
                                g.log_combate.append(("Alvo fora de alcance (Melee)!", COR_DANO))
                                
                        if success:
                            g.motor.avancar_turno()
                            g.acao_action_selecionada = None
                            g.actions_menu_open = False
                
                elif g.habilidade_selecionada:
                    valid_tiles, tipo = g.motor.get_alcance_habilidade(personagem_ativo, g.habilidade_selecionada)
                    if (grid_x, grid_y) in valid_tiles:
                        eventos, logs = g.motor.jogador_usar_habilidade(
                            personagem_ativo, 
                            g.habilidade_selecionada, 
                            alvo=clicked_unit, 
                            pos_alvo=(grid_x, grid_y)
                        )
                        if eventos or logs:
                            g.fila_animacoes.extend(eventos)
                            g.log_combate.extend(logs)
                            if eventos:
                                g.motor.avancar_turno()
                                g.habilidade_selecionada = None
                    else:
                        g.log_combate.append(("Alvo inválido para habilidade!", COR_DANO))
                        g.play_sound('invalid_action')
                        
                elif clicked_unit and clicked_unit.time == TIME_B:
                    dist = calcular_distancia(personagem_ativo, clicked_unit)
                    if dist <= personagem_ativo.alcance:
                        eventos, logs = g.motor.jogador_ataca_personagem(personagem_ativo, clicked_unit)
                        g.fila_animacoes.extend(eventos)
                        g.log_combate.extend(logs)
                        g.motor.avancar_turno()
                    else:
                        g.log_combate.append(("Alvo fora de alcance!", COR_DANO))
                        g.play_sound('invalid_action')
                        
                elif not clicked_unit:
                    if event.button == 1: # Left click move only
                        eventos, logs = g.motor.jogador_move_personagem(personagem_ativo, grid_x, grid_y)
                        if eventos: 
                            g.fila_animacoes.extend(eventos)
                            g.log_combate.extend(logs)
                            g.motor.avancar_turno()
                            g.atualizar_visibilidade()
                        else:
                            if not logs: g.play_sound('invalid_action')
                            g.log_combate.extend(logs)
                                
    def _handle_editor_click(self, event, mouse_pos):
        g = self.game
        
        if event.button == 1:
            if mouse_pos[0] > LARGURA_TABULEIRO:
                for nome, botao in g.botoes_gerador.items():
                    if botao.rect.collidepoint(mouse_pos):
                        g.play_sound('button_click')
                        if nome == 'w_dec' and g.map_gen_width > 10: g.map_gen_width -= 1
                        elif nome == 'w_inc' and g.map_gen_width < 30: g.map_gen_width += 1
                        elif nome == 'h_dec' and g.map_gen_height > 10: g.map_gen_height -= 1
                        elif nome == 'h_inc' and g.map_gen_height < 22: g.map_gen_height += 1
                        if nome == 'gerar':
                            from src.map_generator import MapGenerator
                            g.editor_mapa = MapGenerator.gerar_aleatorio(g.map_gen_width, g.map_gen_height)
                            largura_mapa_pixels = g.map_gen_width * TAMANHO_CELULA
                            x_ui = max(LARGURA_TABULEIRO, largura_mapa_pixels) + 20
                            g.botoes_gerador['w_dec'].rect.x = x_ui
                            g.botoes_gerador['w_inc'].rect.x = x_ui + 80
                            g.botoes_gerador['h_dec'].rect.x = x_ui
                            g.botoes_gerador['h_inc'].rect.x = x_ui + 80
                            g.botoes_gerador['gerar'].rect.x = x_ui
                            
                            for i, t_nome in enumerate([TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_FOGO, TERRENO_AGUA, TERRENO_ROCHA, TERRENO_BARRIL]):
                                if t_nome in g.botoes_editor:
                                    g.botoes_editor[t_nome].rect.x = x_ui
                            
            for nome, botao in g.botoes_editor.items():
                if botao.rect.collidepoint(mouse_pos):
                    g.play_sound('button_click')
                    if nome in [TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO, TERRENO_ROCHA, TERRENO_BARRIL]:
                        g.editor_terreno_selecionado = nome
                    elif nome == 'salvar':
                        from src.salvar_carregar import salvar_mapa_json
                        if salvar_mapa_json(g.editor_mapa):
                            print("Mapa Salvo com Sucesso!")
                            g.play_sound('level_up') 
                    elif nome == 'carregar':
                        from src.salvar_carregar import carregar_mapa_json
                        mapa_carregado = carregar_mapa_json()
                        if mapa_carregado:
                            g.editor_mapa = mapa_carregado
                            g.map_gen_height = len(g.editor_mapa)
                            g.map_gen_width = len(g.editor_mapa[0]) if g.map_gen_height > 0 else 20
                            print("Mapa Carregado com Sucesso!")
                            g.play_sound('level_up')
                    elif nome == 'voltar':
                        g.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL

            grid_pos = g.screen_to_grid(mouse_pos[0], mouse_pos[1])
            if grid_pos is not None:
                grid_x, grid_y = grid_pos
                g.editor_mapa[grid_y][grid_x] = g.editor_terreno_selecionado
