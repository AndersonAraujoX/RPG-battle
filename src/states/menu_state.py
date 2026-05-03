import pygame
from .state_base import GameState
from ..ui.menu import desenhar_menu
from ..config import ESTADO_JOGO_COMBATE, ESTADO_JOGO_EDITOR, ESTADO_JOGO_CARREGANDO

class MenuState(GameState):
    def __init__(self, game):
        super().__init__(game)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.game.checkbox_terreno.checar_clique(mouse_pos): self.game.play_sound('button_click'); return
                if self.game.checkbox_auto.checar_clique(mouse_pos): self.game.play_sound('button_click'); return
                if self.game.checkbox_chefe.checar_clique(mouse_pos): self.game.play_sound('button_click'); return
                if self.game.checkbox_autoplay.checar_clique(mouse_pos): self.game.play_sound('button_click'); return
                if self.game.checkbox_mapa_custom.checar_clique(mouse_pos): self.game.play_sound('button_click'); return

                for nome, botao in self.game.botoes_ui.items():
                    is_botao_chefe = nome.startswith('chefe_')
                    is_botao_time_b = nome.startswith('B_')
                    if self.game.checkbox_chefe.checked and is_botao_time_b: continue
                    if not self.game.checkbox_chefe.checked and is_botao_chefe: continue

                    if botao.checar_clique(mouse_pos):
                        self.game.play_sound('button_click')
                        if nome == 'iniciar':
                            self.game.iniciar_combate()
                            return
                        
                        if nome == 'carregar_menu':
                            import glob
                            self.game.save_files = glob.glob('*.pkl')
                            self.game.mudar_estado(ESTADO_JOGO_CARREGANDO)
                            return
                        
                        if nome == 'editor_mapas':
                            self.game.mudar_estado(ESTADO_JOGO_EDITOR)
                            return

                        if nome == 'next_boss':
                            self.game.selected_boss_index = (self.game.selected_boss_index + 1) % len(self.game.bosses)
                            return
                        
                        if nome == 'prev_boss':
                            self.game.selected_boss_index = (self.game.selected_boss_index - 1) % len(self.game.bosses)
                            return
                        
                        partes_nome = nome.split('_')
                        if len(partes_nome) == 3:
                            time_ou_chefe, acao, item = partes_nome
                            if time_ou_chefe == 'chefe':
                                if acao == 'add':
                                    if item == 'hp': self.game.config_chefe['hp'] += 25
                                    else: self.game.config_chefe[item] += 1
                                elif acao == 'sub':
                                    if item == 'hp': self.game.config_chefe['hp'] = max(50, self.game.config_chefe['hp'] - 25)
                                    else: self.game.config_chefe[item] = max(1, self.game.config_chefe[item] - 1)
                            else:
                                cls, _ = self.game.config_times['classes'][int(item)]
                                if acao == 'add': self.game.config_times[time_ou_chefe][cls] += 1
                                elif acao == 'sub': self.game.config_times[time_ou_chefe][cls] = max(0, self.game.config_times[time_ou_chefe][cls] - 1)

    def update(self):
        pass

    def draw(self, tela):
        desenhar_menu(self.game.tela, self.game.fonte_menu, self.game.config_times, self.game.config_chefe, self.game.botoes_ui, 
                      self.game.checkbox_terreno, self.game.checkbox_auto, self.game.checkbox_chefe, self.game.checkbox_autoplay, 
                      self.game.checkbox_mapa_custom, self.game.bosses, self.game.selected_boss_index, self.game.imagens, self.game.volume_sfx)
