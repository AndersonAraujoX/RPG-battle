import pygame
import sys
from collections import deque

from ..config import *
from ..motor_combate import MotorCombate, calcular_distancia
from ..personagens import *
from .componentes import Botao
from .desenho import *
from .menu import setup_menu_ui, desenhar_menu

# --- Constantes de Estado de Combate ---
ESTADO_VEZ_IA = "VEZ_IA"
ESTADO_AGUARDANDO_JOGADOR = "AGUARDANDO_JOGADOR"
ESTADO_JOGADOR_SELECIONOU = "JOGADOR_SELECIONOU"

def carregar_sons():
    sounds = {}
    try:
        pygame.mixer.init()
        for name in ['button_click', 'attack', 'hit', 'miss', 'level_up', 'heal']:
            sounds[name] = pygame.mixer.Sound(f'assets/sounds/{name}.wav')
    except pygame.error as e:
        print(f"Erro ao carregar sons: {e}. Certifique-se de que os arquivos .wav existem em assets/sounds/.")
        return {}
    return sounds

def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Simulador de Batalha Tático")
    fonte_personagem = pygame.font.Font(None, 18)
    fonte_log = pygame.font.Font(None, 20)
    fonte_info = pygame.font.Font(None, 22)
    fonte_menu = pygame.font.Font(None, 28)
    fonte_titulo = pygame.font.Font(None, 48)
    clock = pygame.time.Clock()

    sounds = carregar_sons()
    def play_sound(nome):
        if nome in sounds: sounds[nome].play()

    # --- Variáveis de Estado ---
    estado_jogo = 'MENU'
    estado_combate = None
    motor = None
    unidade_selecionada = None # Unidade que o jogador está comandando
    personagem_info_painel = None # Unidade mostrada no painel de info
    painel_modo = 'LOG'
    fila_animacoes = deque()
    animacao_atual = None
    
    config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay = setup_menu_ui()
    
    botoes_combate = {'proxima_acao': Botao(LARGURA_TABULEIRO + 20, ALTURA_TELA - 70, LARGURA_LOG - 40, 50, "Próxima Ação", fonte_menu)}

    log_combate = deque(maxlen=35)
    tick = 0
    tempo_proxima_acao_auto = 0

    rodando = True
    while rodando:
        mouse_pos = pygame.mouse.get_pos()
        tick += 1
        agora = pygame.time.get_ticks()
        
        personagem_ativo = motor.get_personagem_ativo() if motor and not motor.vencedor else None

        # --- Loop de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): rodando = False
            if animacao_atual: continue

            if estado_jogo == 'MENU':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if checkbox_terreno.checar_clique(mouse_pos): play_sound('button_click'); continue
                    if checkbox_auto.checar_clique(mouse_pos): play_sound('button_click'); continue
                    if checkbox_chefe.checar_clique(mouse_pos): play_sound('button_click'); continue
                    if checkbox_autoplay.checar_clique(mouse_pos): play_sound('button_click'); continue # Novo
                    
                    for nome, botao in botoes_ui.items():
                        is_botao_chefe = nome.startswith('chefe_')
                        is_botao_time_b = nome.startswith('B_')
                        if checkbox_chefe.checked and is_botao_time_b: continue
                        if not checkbox_chefe.checked and is_botao_chefe: continue

                        if botao.checar_clique(mouse_pos):
                            play_sound('button_click')
                            if nome == 'iniciar':
                                estado_jogo = 'COMBATE'
                                args = [config_times['A'][c] for c,_ in config_times['classes']] + [config_times['B'][c] for c,_ in config_times['classes']]
                                try:
                                    motor = MotorCombate(args, gerar_terreno=checkbox_terreno.checked, sound_player=play_sound, modo_chefe=checkbox_chefe.checked, stats_chefe=config_chefe if checkbox_chefe.checked else None)
                                    for p in motor.combatentes: p.dano_timer = 0
                                    log_combate.clear(); log_combate.append("Batalha iniciada!")
                                except ValueError as e: print(f"Erro: {e}"); estado_jogo = 'MENU'
                                break
                            
                            partes_nome = nome.split('_')
                            if len(partes_nome) == 3:
                                time_ou_chefe, acao, item = partes_nome
                                if time_ou_chefe == 'chefe':
                                    if acao == 'add':
                                        if item == 'hp': config_chefe['hp'] += 25
                                        else: config_chefe[item] += 1
                                    elif acao == 'sub':
                                        if item == 'hp': config_chefe['hp'] = max(50, config_chefe['hp'] - 25)
                                        else: config_chefe[item] = max(1, config_chefe[item] - 1)
                                else:
                                    cls, _ = config_times['classes'][int(item)]
                                    if acao == 'add': config_times[time_ou_chefe][cls] += 1
                                    elif acao == 'sub': config_times[time_ou_chefe][cls] = max(0, config_times[time_ou_chefe][cls] - 1)

            elif estado_jogo == 'COMBATE' and motor:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Lógica de clique para o turno da IA (botão de próxima ação)
                    if estado_combate == ESTADO_VEZ_IA and not motor.vencedor and not fila_animacoes and botoes_combate['proxima_acao'].checar_clique(mouse_pos):
                        play_sound('button_click')
                        resultado = motor.proximo_passo()
                        log_combate.extend(resultado['logs'])
                        fila_animacoes.extend(resultado['eventos'])
                    
                    # Lógica de clique para o turno do Jogador
                    elif estado_combate in [ESTADO_AGUARDANDO_JOGADOR, ESTADO_JOGADOR_SELECIONOU]:
                        grid_x, grid_y = mouse_pos[0] // TAMANHO_CELULA, mouse_pos[1] // TAMANHO_CELULA
                        if 0 <= grid_x < 20 and 0 <= grid_y < 20:
                            p_clicado = motor.tabuleiro.get_personagem_em(grid_x, grid_y)
                            
                            # Selecionar uma unidade
                            if estado_combate == ESTADO_AGUARDANDO_JOGADOR:
                                if p_clicado and p_clicado.time == 'A' and p_clicado == personagem_ativo:
                                    unidade_selecionada = p_clicado
                                    estado_combate = ESTADO_JOGADOR_SELECIONOU
                                    personagem_info_painel = p_clicado
                                    painel_modo = 'INFO'
                                else: # Clicar fora ou em unidade inválida
                                    personagem_info_painel = p_clicado
                                    painel_modo = 'INFO' if p_clicado else 'LOG'

                            # Dar um comando a uma unidade selecionada
                            elif estado_combate == ESTADO_JOGADOR_SELECIONOU:
                                acao_realizada = False
                                # 1. Comando de Ataque
                                if p_clicado and p_clicado.time == 'B' and p_clicado.esta_vivo:
                                    dist = abs(unidade_selecionada.pos_x - grid_x) + abs(unidade_selecionada.pos_y - grid_y)
                                    if dist <= unidade_selecionada.alcance:
                                        logs_turno = [f"Jogador comanda {unidade_selecionada.nome} para atacar {p_clicado.nome}."]
                                        log_combate.extend(logs_turno)
                                        eventos = motor.jogador_ataca_personagem(unidade_selecionada, p_clicado)
                                        fila_animacoes.extend(eventos)
                                        acao_realizada = True
                                
                                # 2. Comando de Movimento
                                elif not p_clicado:
                                    dist = abs(unidade_selecionada.pos_x - grid_x) + abs(unidade_selecionada.pos_y - grid_y)
                                    if dist <= unidade_selecionada.velocidade and motor.tabuleiro.get_terrain_em(grid_x, grid_y) != TERRENO_PAREDE:
                                        logs_turno = [f"Jogador comanda {unidade_selecionada.nome} para mover para ({grid_x},{grid_y})."]
                                        log_combate.extend(logs_turno)
                                        eventos = motor.jogador_move_personagem(unidade_selecionada, grid_x, grid_y)
                                        fila_animacoes.extend(eventos)
                                        acao_realizada = True

                                # 3. Clicar em um espaço inválido ou em si mesmo para cancelar
                                else:
                                    unidade_selecionada = None
                                    estado_combate = ESTADO_AGUARDANDO_JOGADOR
                                
                                if acao_realizada:
                                    motor.avancar_turno()
                                    unidade_selecionada = None
                                    # O estado será atualizado no próximo ciclo da lógica de jogo
        
        # --- Lógica de Jogo ---
        if estado_jogo == 'COMBATE' and motor and not motor.vencedor:
            # Define o estado do turno se ainda não houver um (ou se o turno mudou)
            if not animacao_atual and not fila_animacoes:
                if personagem_ativo:
                    # Se Auto-Play está ativo, ou se é um personagem da IA, trata como vez da IA
                    if checkbox_autoplay.checked or personagem_ativo.time == 'B':
                        estado_combate = ESTADO_VEZ_IA
                        unidade_selecionada = None
                    else: # Vez do Time A (Jogador)
                        # Só reseta se a ação foi concluída (unidade_selecionada está None)
                        if not unidade_selecionada:
                            estado_combate = ESTADO_AGUARDANDO_JOGADOR
            
            # Avanço automático para a IA (e agora para o jogador se Auto-Play estiver ativo)
            if estado_combate == ESTADO_VEZ_IA and checkbox_auto.checked and not animacao_atual and not fila_animacoes:
                if agora > tempo_proxima_acao_auto:
                    resultado = motor.proximo_passo()
                    log_combate.extend(resultado['logs'])
                    fila_animacoes.extend(resultado['eventos'])
                    tempo_proxima_acao_auto = agora + 750

        # Processamento de animações
        if not animacao_atual and fila_animacoes:
            evento = fila_animacoes.popleft()
            animacao_atual = {'progresso': 0.0, **evento}
            if evento['tipo'] == 'ataque': animacao_atual['duracao'] = 25 if evento['atacante'].alcance > 1 else 20
            elif evento['tipo'] == 'ataque_area': animacao_atual['duracao'] = 40
            elif evento['tipo'] == 'dano' and evento['dano'] != 'ERROU!': evento['alvo'].dano_timer = 15; animacao_atual = None
            else: animacao_atual = None

        if animacao_atual:
            animacao_atual['progresso'] += 1.0 / animacao_atual['duracao']
            if animacao_atual['progresso'] >= 1.0: animacao_atual = None

        # --- Desenho ---
        if estado_jogo == 'MENU':
            desenhar_menu(tela, fonte_menu, config_times, config_chefe, botoes_ui, checkbox_terreno, checkbox_auto, checkbox_chefe, checkbox_autoplay)
        elif estado_jogo == 'COMBATE' and motor:
            tela.fill(COR_FUNDO)
            desenhar_cenario(tela, motor)
            
            # Destaca a unidade selecionada pelo jogador de forma diferente da unidade ativa da IA
            unidade_em_foco = unidade_selecionada if estado_combate == ESTADO_JOGADOR_SELECIONOU else personagem_ativo
            desenhar_personagens(tela, motor, fonte_personagem, unidade_em_foco, tick, animacao_atual)
            
            # Desenha o feedback de movimento/ataque para o jogador
            if estado_combate == ESTADO_JOGADOR_SELECIONOU:
                desenhar_feedback_jogador(tela, unidade_selecionada, motor)

            desenhar_projeteis_e_efeitos(tela, animacao_atual)
            
            log_max_altura = ALTURA_TELA - 150 # 150px para os comandos
            if painel_modo == 'LOG': desenhar_log(tela, fonte_log, list(log_combate), log_max_altura)
            elif painel_modo == 'INFO' and personagem_info_painel: desenhar_info_personagem(tela, fonte_info, personagem_info_painel, log_max_altura)

            desenhar_comandos(tela, fonte_log) # Desenha os comandos na parte inferior

            if not motor.vencedor:
                is_vez_ia = estado_combate == ESTADO_VEZ_IA
                botoes_combate['proxima_acao'].desabilitado = not is_vez_ia or checkbox_auto.checked or bool(animacao_atual or fila_animacoes)
                botoes_combate['proxima_acao'].update_hover(mouse_pos)
                botoes_combate['proxima_acao'].desenhar(tela, fonte_menu)
            else:
                desenhar_tela_fim(tela, fonte_titulo, motor.vencedor)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()