import pygame
import sys
from collections import deque

from .config import *
from .motor_combate import MotorCombate
from .personagens import *
from .ui.componentes import Botao
from .ui.desenho import *
from .ui.menu import setup_menu_ui, desenhar_menu

class Game:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Simulador de Batalha Tático")
        self.fonte_personagem = pygame.font.Font(None, 18)
        self.fonte_log = pygame.font.Font(None, 20)
        self.fonte_info = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 28)
        self.fonte_titulo = pygame.font.Font(None, 48)
        self.clock = pygame.time.Clock()

        self.sounds = self.carregar_sons()
        
        self.rodando = True
        self.estado_jogo = ESTADO_JOGO_MENU
        self.estado_combate = None
        self.motor = None
        self.unidade_selecionada = None
        self.personagem_info_painel = None
        self.painel_modo = PAINEL_MODO_LOG
        self.fila_animacoes = deque()
        self.animacao_atual = None
        self.tempo_proxima_acao_auto = 0
        self.log_combate = deque(maxlen=35)
        self.log_combate.append("Bem-vindo ao Simulador de Batalha!")

        self.botoes_combate = {}
        self.config_times = {}
        self.config_chefe = {}
        self.botoes_ui = {}
        self.checkbox_terreno = None
        self.checkbox_auto = None
        self.checkbox_chefe = None
        self.checkbox_autoplay = None

        self.setup_ui()

    def carregar_sons(self):
        # Temporarily disable sound loading as files are empty
        return {}
    
    def play_sound(self, nome):
        if nome in self.sounds:
            self.sounds[nome].play()

    def setup_ui(self):
        config_times_init, config_chefe_init, botoes_ui_init, checkbox_terreno_init, checkbox_auto_init, checkbox_chefe_init, checkbox_autoplay_init = setup_menu_ui()
    
        self.config_times.update(config_times_init)
        self.config_chefe.update(config_chefe_init)
        self.botoes_ui.update(botoes_ui_init)
        self.checkbox_terreno = checkbox_terreno_init
        self.checkbox_auto = checkbox_auto_init
        self.checkbox_chefe = checkbox_chefe_init
        self.checkbox_autoplay = checkbox_autoplay_init

        self.botoes_combate['proxima_acao'] = Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, LARGURA_LOG - 40, 50, "Próxima Ação", self.fonte_menu)

    def run(self):
        while self.rodando:
            mouse_pos = pygame.mouse.get_pos()
            tick = pygame.time.get_ticks()
            agora = pygame.time.get_ticks()
            
            personagem_ativo = self.motor.get_personagem_ativo() if self.motor and not self.motor.vencedor else None

            self.handle_events(mouse_pos, personagem_ativo)
            if not self.rodando: break

            self.update_game_logic(agora, personagem_ativo)
            
            self.draw_elements(tick, mouse_pos)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_events(self, mouse_pos, personagem_ativo):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): 
                self.rodando = False
                return
            if self.animacao_atual: return

            if self.estado_jogo == ESTADO_JOGO_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.checkbox_terreno.checar_clique(mouse_pos): self.play_sound('button_click'); return
                    if self.checkbox_auto.checar_clique(mouse_pos): self.play_sound('button_click'); return
                    if self.checkbox_chefe.checar_clique(mouse_pos): self.play_sound('button_click'); return
                    if self.checkbox_autoplay.checar_clique(mouse_pos): self.play_sound('button_click'); return
                    
                    for nome, botao in self.botoes_ui.items():
                        is_botao_chefe = nome.startswith('chefe_')
                        is_botao_time_b = nome.startswith('B_')
                        if self.checkbox_chefe.checked and is_botao_time_b: continue
                        if not self.checkbox_chefe.checked and is_botao_chefe: continue

                        if botao.checar_clique(mouse_pos):
                            self.play_sound('button_click')
                            if nome == 'iniciar':
                                self.estado_jogo = ESTADO_JOGO_COMBATE
                                args = [self.config_times[TIME_A][c] for c,_ in self.config_times['classes']] + \
                                    [self.config_times[TIME_B][c] for c,_ in self.config_times['classes']]
                                try:
                                    self.motor = MotorCombate(args, gerar_terreno=self.checkbox_terreno.checked, sound_player=self.play_sound, 
                                                        modo_chefe=self.checkbox_chefe.checked, stats_chefe=self.config_chefe if self.checkbox_chefe.checked else None)
                                    for p in self.motor.combatentes: p.dano_timer = 0
                                    self.log_combate.clear(); self.log_combate.append("Batalha iniciada!")
                                except ValueError as e: print(f"Erro: {e}"); self.estado_jogo = ESTADO_JOGO_MENU
                                return
                            
                            partes_nome = nome.split('_')
                            if len(partes_nome) == 3:
                                time_ou_chefe, acao, item = partes_nome
                                if time_ou_chefe == 'chefe':
                                    if acao == 'add':
                                        if item == 'hp': self.config_chefe['hp'] += 25
                                        else: self.config_chefe[item] += 1
                                    elif acao == 'sub':
                                        if item == 'hp': self.config_chefe['hp'] = max(50, self.config_chefe['hp'] - 25)
                                        else: self.config_chefe[item] = max(1, self.config_chefe[item] - 1)
                                else:
                                    cls, _ = self.config_times['classes'][int(item)]
                                    if acao == 'add': self.config_times[time_ou_chefe][cls] += 1
                                    elif acao == 'sub': self.config_times[time_ou_chefe][cls] = max(0, self.config_times[time_ou_chefe][cls] - 1)

            elif self.estado_jogo == ESTADO_JOGO_COMBATE and self.motor:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.estado_combate == ESTADO_COMBATE_VEZ_IA and not self.motor.vencedor and not self.fila_animacoes and self.botoes_combate['proxima_acao'].checar_clique(mouse_pos):
                        self.play_sound('button_click')
                        resultado = self.motor.proximo_passo()
                        self.log_combate.extend(resultado['logs'])
                        self.fila_animacoes.extend(resultado['eventos'])
                    
                    elif self.estado_combate in [ESTADO_COMBATE_AGUARDANDO_JOGADOR, ESTADO_COMBATE_JOGADOR_SELECIONOU]:
                        grid_x, grid_y = mouse_pos[0] // TAMANHO_CELULA, mouse_pos[1] // TAMANHO_CELULA
                        if 0 <= grid_x < 20 and 0 <= grid_y < 20:
                            p_clicado = self.motor.tabuleiro.get_personagem_em(grid_x, grid_y)
                            
                            if self.estado_combate == ESTADO_COMBATE_AGUARDANDO_JOGADOR:
                                if p_clicado and p_clicado.time == TIME_A and p_clicado == personagem_ativo:
                                    self.unidade_selecionada = p_clicado
                                    self.estado_combate = ESTADO_COMBATE_JOGADOR_SELECIONOU
                                    self.personagem_info_painel = p_clicado
                                    self.painel_modo = PAINEL_MODO_INFO
                                else:
                                    self.personagem_info_painel = p_clicado
                                    self.painel_modo = PAINEL_MODO_INFO if p_clicado else PAINEL_MODO_LOG

                            elif self.estado_combate == ESTADO_COMBATE_JOGADOR_SELECIONOU:
                                acao_realizada = False
                                if p_clicado and p_clicado.time == TIME_B and p_clicado.esta_vivo:
                                    dist = abs(self.unidade_selecionada.pos_x - grid_x) + abs(self.unidade_selecionada.pos_y - grid_y)
                                    if dist <= self.unidade_selecionada.alcance:
                                        logs_turno = [f"Jogador comanda {self.unidade_selecionada.nome} para atacar {p_clicado.nome}."]
                                        self.log_combate.extend(logs_turno)
                                        eventos = self.motor.jogador_ataca_personagem(self.unidade_selecionada, p_clicado)
                                        self.fila_animacoes.extend(eventos)
                                        acao_realizada = True
                                
                                elif not p_clicado:
                                    dist = abs(self.unidade_selecionada.pos_x - grid_x) + abs(self.unidade_selecionada.pos_y - grid_y)
                                    if dist <= self.unidade_selecionada.velocidade and self.motor.tabuleiro.get_terrain_em(grid_x, grid_y) != TERRENO_PAREDE:
                                        logs_turno = [f"Jogador comanda {self.unidade_selecionada.nome} para mover para ({grid_x},{grid_y})."]
                                        self.log_combate.extend(logs_turno)
                                        eventos = self.motor.jogador_move_personagem(self.unidade_selecionada, grid_x, grid_y)
                                        self.fila_animacoes.extend(eventos)
                                        acao_realizada = True

                                else:
                                    self.unidade_selecionada = None
                                    self.estado_combate = ESTADO_COMBATE_AGUARDANDO_JOGADOR
                                
                                if acao_realizada:
                                    self.motor.avancar_turno()
                                    self.unidade_selecionada = None

    def update_game_logic(self, agora, personagem_ativo):
        if self.estado_jogo == ESTADO_JOGO_COMBATE and self.motor and not self.motor.vencedor:
            if not self.animacao_atual and not self.fila_animacoes:
                if personagem_ativo:
                    if self.checkbox_autoplay.checked or personagem_ativo.time == TIME_B:
                        self.estado_combate = ESTADO_COMBATE_VEZ_IA
                        self.unidade_selecionada = None
                    else:
                        if not self.unidade_selecionada:
                            self.estado_combate = ESTADO_COMBATE_AGUARDANDO_JOGADOR
            
            if self.estado_combate == ESTADO_COMBATE_VEZ_IA and self.checkbox_auto.checked and not self.animacao_atual and not self.fila_animacoes:
                if agora > self.tempo_proxima_acao_auto:
                    resultado = self.motor.proximo_passo()
                    self.log_combate.extend(resultado['logs'])
                    self.fila_animacoes.extend(resultado['eventos'])
                    self.tempo_proxima_acao_auto = agora + 750

        if not self.animacao_atual and self.fila_animacoes:
            evento = self.fila_animacoes.popleft()
            self.animacao_atual = {'progresso': 0.0, **evento}
            if evento['tipo'] == 'ataque': self.animacao_atual['duracao'] = 25 if evento['atacante'].alcance > 1 else 20
            elif evento['tipo'] == 'ataque_area': self.animacao_atual['duracao'] = 40
            elif evento['tipo'] == 'dano' and evento['dano'] != 'ERROU!': evento['alvo'].dano_timer = 15; self.animacao_atual = None
            else: self.animacao_atual = None

        if self.animacao_atual:
            self.animacao_atual['progresso'] += 1.0 / self.animacao_atual['duracao']
            if self.animacao_atual['progresso'] >= 1.0: self.animacao_atual = None

    def draw_elements(self, tick, mouse_pos):
        personagem_ativo = self.motor.get_personagem_ativo() if self.motor and not self.motor.vencedor else None
        if self.estado_jogo == ESTADO_JOGO_MENU:
            desenhar_menu(self.tela, self.fonte_menu, self.config_times, self.config_chefe, self.botoes_ui, self.checkbox_terreno, self.checkbox_auto, self.checkbox_chefe, self.checkbox_autoplay)
        elif self.estado_jogo == ESTADO_JOGO_COMBATE and self.motor:
            self.tela.fill(COR_FUNDO)
            desenhar_cenario(self.tela, self.motor)
            
            unidade_em_foco = self.unidade_selecionada if self.estado_combate == ESTADO_COMBATE_JOGADOR_SELECIONOU else personagem_ativo
            desenhar_personagens(self.tela, self.motor, self.fonte_personagem, unidade_em_foco, tick, self.animacao_atual)
            
            if self.estado_combate == ESTADO_COMBATE_JOGADOR_SELECIONOU:
                desenhar_feedback_jogador(self.tela, self.unidade_selecionada, self.motor)

            desenhar_projeteis_e_efeitos(self.tela, self.animacao_atual)
            
            log_max_altura = ALTURA_TELA - 150
            if self.painel_modo == PAINEL_MODO_LOG: desenhar_log(self.tela, self.fonte_log, list(self.log_combate), log_max_altura)
            elif self.painel_modo == PAINEL_MODO_INFO and self.personagem_info_painel: desenhar_info_personagem(self.tela, self.fonte_info, self.personagem_info_painel, log_max_altura)

            desenhar_comandos(self.tela, self.fonte_log)

            if not self.motor.vencedor:
                is_vez_ia = self.estado_combate == ESTADO_COMBATE_VEZ_IA
                self.botoes_combate['proxima_acao'].desabilitado = not is_vez_ia or self.checkbox_auto.checked or bool(self.animacao_atual or self.fila_animacoes)
                self.botoes_combate['proxima_acao'].update_hover(mouse_pos)
                self.botoes_combate['proxima_acao'].desenhar(self.tela, self.fonte_menu)
            else:
                desenhar_tela_fim(self.tela, self.fonte_titulo, self.motor.vencedor)
