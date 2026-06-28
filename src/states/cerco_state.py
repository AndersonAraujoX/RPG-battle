"""
cerco_state.py — Cerco contra Isectum (Pygame state completo)

Loop principal do jogo de tabuleiro. O Resolvedor de Ações é o núcleo:
cada ação do herói passa pela validação antes de alterar o estado.

Fases do turno:
  JOGAR_CARTA   → jogador seleciona cartas da mão para acumular pontos
  ACAO_LIVRE    → seleciona modo (mover/trabalhar/escavar/subornar/upgrade)
  SELECIONAR    → clica no mapa para mover, ou confirma ação in-loco
  FASE_AMEACA   → carta de ameaça revelada e resolvida
  FIM           → derrota ou vitória
"""
from __future__ import annotations
import pygame
import random
import math
from .state_base import GameState
from ..cerco_isectum import (
    criar_estado, criar_deck, processar_carta,
    avancar_ciclo_armas, aplicar_delta, NOMES_ZONA,
    CARTAS_UPGRADE
)
from ..resolvedor_acoes import (
    validar_mover,    executar_mover,
    validar_trabalhar, executar_trabalhar,
    validar_escavar,   executar_escavar,
    validar_subornar,  executar_subornar,
    validar_comprar_upgrade, executar_comprar_upgrade,
    OFICINAS, ZONA_ESCAVACAO, NOME_RECURSO
)
from ..config import ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA

# ═══════════════════════════════════════════════════════════════════════════
# PALETA
# ═══════════════════════════════════════════════════════════════════════════
C_BG      = (5,  6, 12)
C_PAINEL  = (14, 16, 30)
C_BORDA   = (45, 48, 78)
C_ACENTO  = (180, 120, 255)
C_OURO    = (255, 195,  40)
C_VERDE   = ( 50, 220, 110)
C_PERIGO  = (255,  55,  55)
C_CERCO   = (255, 100,   0)
C_TEXTO   = (235, 240, 255)
C_DIM     = (110, 120, 155)
C_INVASOR = ( 50, 240,  50)
C_BRUTE   = (255, 130,   0)
C_HEROI   = (100, 200, 255)
C_CARD    = ( 22,  28,  52)
C_CARD_HL = ( 40,  55, 100)
C_MOVE_HL = ( 30,  80,  30)
C_ACT_HL  = ( 80,  30,  30)

# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT DAS ZONAS NO MAPA (rx, ry, rw, rh — proporções 0..1)
# ═══════════════════════════════════════════════════════════════════════════
LAYOUT_ZONAS = {
    "muralha_norte":  (0.35, 0.01, 0.30, 0.12),
    "muralha_sul":    (0.35, 0.87, 0.30, 0.12),
    "muralha_oeste":  (0.00, 0.28, 0.16, 0.44),
    "muralha_leste":  (0.84, 0.28, 0.16, 0.44),
    "carpintaria":    (0.35, 0.14, 0.30, 0.20),
    "curtume":        (0.35, 0.66, 0.30, 0.20),
    "fundicao":       (0.17, 0.28, 0.17, 0.44),
    "patio":          (0.66, 0.28, 0.17, 0.44),
    "camara_central": (0.35, 0.35, 0.30, 0.30),
    "torre_nw":       (0.01, 0.01, 0.12, 0.12),
    "torre_ne":       (0.87, 0.01, 0.12, 0.12),
    "torre_sw":       (0.01, 0.87, 0.12, 0.12),
    "torre_se":       (0.87, 0.87, 0.12, 0.12),
}

COR_ZONA = {
    "muralha_norte": (35, 35, 62), "muralha_sul":   (35, 35, 62),
    "muralha_oeste": (35, 35, 62), "muralha_leste": (35, 35, 62),
    "carpintaria":   (20, 42, 20), "curtume":       (42, 28, 12),
    "fundicao":      (42, 22, 22), "patio":         (25, 25, 52),
    "camara_central":(12, 12, 48),
    "torre_nw": (28, 28, 52), "torre_ne": (28, 28, 52),
    "torre_sw": (28, 28, 52), "torre_se": (28, 28, 52),
}

ICONE_ZONA = {
    "muralha_norte": "🧱", "muralha_sul":   "🧱",
    "muralha_oeste": "🧱", "muralha_leste": "🧱",
    "carpintaria":   "🪵", "curtume":       "🧳",
    "fundicao":      "⚙️",  "patio":         "⛏️",
    "camara_central":"🏰",
    "torre_nw": "🗼", "torre_ne": "🗼", "torre_sw": "🗼", "torre_se": "🗼",
}

# ═══════════════════════════════════════════════════════════════════════════
# NARRATIVAS
# ═══════════════════════════════════════════════════════════════════════════
NAR = {
    "invasor":      ["Os insetoides escalam as muralhas!", "A horda avança!"],
    "mover":        ["Tambores — eles avançam!", "A maré negra rasteja!"],
    "torre_assalto":["Uma Torre de Assalto emerge!", "Pela pedra sagrada!"],
    "catapulta":    ["CATAPULTA! A rocha impacta!", "Pedras de fogo voam!"],
    "cerco":        ["O cerco aperta — resistam!", "Defendam a fortaleza!"],
    "derrota":      ["A fortaleza caiu. Isectum vence..."],
}

# Modos de ação do herói
MODO_NENHUM    = "nenhum"
MODO_MOVER     = "mover"
MODO_TRABALHAR = "trabalhar"
MODO_ESCAVAR   = "escavar"
MODO_SUBORNAR  = "subornar"
MODO_UPGRADE   = "upgrade"
MODO_CONVOCAR  = "convocar"


class CercoState(GameState):
    """Estado Pygame completo — Resolvedor de Ações como núcleo."""


    TAM_MAO = 5        # máximo de cartas na mão por turno
    DECK_FIXO = 12     # tamanho fixo do deck do herói

    def __init__(self, game):
        super().__init__(game)
        self.estado  = criar_estado(pedregulhos=8, is_solo=True)
        self.deck    = criar_deck()
        self.log     = []
        self.narrativa    = "Pela barba de Durin! O cerco começa!"
        self.carta_cerco  = None          # carta de ameaça atual
        self.fase         = "JOGAR_CARTA" # fase do turno
        self.modo_acao    = MODO_NENHUM   # modo de ação selecionado
        self.timer        = 0
        self.msg_feedback = ""
        self.msg_cor      = C_VERDE
        self.feedback_timer = 0
        # Índice de carta da mão selecionada para queima de upgrade
        self.idx_carta_queimar  = -1
        self.idx_slot_upgrade   = -1
        # Zonas alcançáveis (highlight)
        self.alcancaveis        = {}
        
        # Cria um motor de combate simulado para renderizar o cenário e calcular as distâncias na grade
        from ..motor_combate import MotorCombate
        self.motor = MotorCombate(args_times=[0]*24, gerar_terreno=False)
        # Configurar zonas no terreno
        from ..resolvedor_acoes import ZONAS_GRID
        # Preencher o terrain_grid do tabuleiro com as zonas correspondentes
        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            for cy in range(y1, y2 + 1):
                for cx in range(x1, x2 + 1):
                    # Definimos elevações e tipos de terrenos baseados nas zonas do cerco
                    if "muralha" in zona_id:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "rocha"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 2
                    elif "torre" in zona_id:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "barril"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 3
                    elif zona_id == "patio": # Nexos
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "fogo" # Representando magia/nexos
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "curtume": # Couro
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "dificil" # Lama/Couro
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "carpintaria": # Madeira
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "floresta" # Madeira/Floresta
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "fundicao": # Ferro
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "rocha"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "camara_central": # Ouro
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "normal"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 1
                    else:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "normal"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0

        # Adiciona o personagem do jogador (Novak) ao motor de combate e ao tabuleiro
        from ..personagens.protagonistas import Novak
        self.jogador_novak = Novak("Novak", "A", nivel=5)
        self.motor.time_a = [self.jogador_novak]
        self.motor.combatentes = [self.jogador_novak]
        self.motor.tabuleiro.adicionar_personagem(self.jogador_novak, 9, 9)

        self._setup_fonts()
        self._setup_layout()
        self._comprar_mao()
        self._push("SISTEMA", "Cerco contra Isectum iniciado! Jogue cartas e aja.")

    # ── FONTS ────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.fT  = pygame.font.Font(None, 48)
        self.fG  = pygame.font.Font(None, 36)
        self.fM  = pygame.font.Font(None, 28)
        self.fP  = pygame.font.Font(None, 22)
        self.fMi = pygame.font.Font(None, 18)

    # ── LAYOUT (recalculado uma vez) ─────────────────────────────────────
    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        # Área do mapa
        self.mapa_rect   = pygame.Rect(8, 65, W - 330, H - 170)
        # Painel lateral (log + recursos + mercado)
        self.painel_rect = pygame.Rect(W - 318, 65, 310, H - 75)
        # Faixa de cartas na mão (bottom)
        self.mao_rect    = pygame.Rect(8, H - 100, W - 330, 92)
        # Botões de ação
        bw, bh = 136, 36
        bx = W - 318
        by = H - 48
        self.btn_fim_turno  = pygame.Rect(bx,         by, bw,     bh)
        self.btn_mover      = pygame.Rect(8,    H - 48, bw - 10,  bh)
        self.btn_trabalhar  = pygame.Rect(8+bw, H - 48, bw - 10,  bh)
        self.btn_escavar    = pygame.Rect(8+bw*2, H-48, bw - 10,  bh)
        self.btn_subornar   = pygame.Rect(8+bw*3, H-48, bw - 10,  bh)
        self.btn_convocar   = pygame.Rect(8+bw*4, H-48, bw - 10,  bh)
        self.btn_voltar     = pygame.Rect(W - 156, 68,  140,  30)
        self.btn_confirmar  = pygame.Rect(W//2-100, H-48, 200,  bh)
        # Rects das cartas na mão
        self.carta_rects = []  # list[pygame.Rect]

    # ── LOG ──────────────────────────────────────────────────────────────
    def _push(self, tipo, msg):
        self.log.append((tipo, msg))
        if len(self.log) > 80:
            self.log.pop(0)

    def _feedback(self, msg, cor=C_VERDE):
        self.msg_feedback = msg
        self.msg_cor = cor
        self.feedback_timer = 120

    def _narrativa(self, tipo):
        self.narrativa = random.choice(NAR.get(tipo, NAR["cerco"]))

    # ── DECK DO HERÓI ────────────────────────────────────────────────────
    def _comprar_mao(self):
        """Compra até TAM_MAO cartas do deck do herói para a mão."""
        mao    = list(self.estado["mao"])
        deck   = list(self.estado["deck_heroi"])
        discard = list(self.estado["descarte"])
        while len(mao) < self.TAM_MAO:
            if not deck:
                if not discard:
                    break
                deck = discard[:]
                random.shuffle(deck)
                discard = []
                self._push("SISTEMA", "Deck embaralhado do descarte.")
            mao.append(deck.pop())
        self.estado = aplicar_delta(self.estado, {
            "mao": mao, "deck_heroi": deck, "descarte": discard
        })

    def _jogar_carta(self, idx):
        """Aplica os pontos de ação de uma carta da mão."""
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            return
        carta = mao.pop(idx)
        discard = list(self.estado["descarte"]) + [carta]
        delta = {
            "mao":              mao,
            "descarte":         discard,
            "pontos_movimento": self.estado["pontos_movimento"] + carta.get("movimento", 0),
            "pontos_trabalho":  self.estado["pontos_trabalho"]  + carta.get("trabalho",  0),
            "pontos_escavacao": self.estado["pontos_escavacao"] + carta.get("escavacao", 0),
        }
        self.estado = aplicar_delta(self.estado, delta)
        self._push("HEROI", f"Jogou [{carta['nome']}]: +{carta.get('movimento',0)}PM "
                            f"+{carta.get('trabalho',0)}PT +{carta.get('escavacao',0)}PE")
        self._feedback(f"Carta: {carta['nome']}", C_VERDE)
        # Atualiza células alcançáveis no tabuleiro tático
        from ..resolvedor_acoes import obter_celulas_alcancaveis
        self.alcancaveis = obter_celulas_alcancaveis(
            self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
            self.estado["pontos_movimento"]
        )

    # ═══════════════════════════════════════════════════════════════════
    # HANDLE EVENTS
    # ═══════════════════════════════════════════════════════════════════
    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()
        e = self.estado

        for event in events:
            # Fim universal
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.mudar_estado(ESTADO_JOGO_MENU_PRINCIPAL)
                return

            # Tela de fim
            if e.get("derrota") or e.get("vitoria"):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.game.mudar_estado(ESTADO_JOGO_MENU_PRINCIPAL)
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_click(mouse)
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key):
        if key == pygame.K_RETURN:
            if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
                self._fim_turno_heroi()
        if key == pygame.K_SPACE:
            if self.fase == "FASE_AMEACA" and self.carta_cerco:
                self._resolver_carta_cerco()
        if key == pygame.K_m and self.fase == "ACAO_LIVRE":
            self._selecionar_modo(MODO_MOVER)
        if key == pygame.K_t and self.fase == "ACAO_LIVRE":
            self._selecionar_modo(MODO_TRABALHAR)
        if key == pygame.K_e and self.fase == "ACAO_LIVRE":
            self._selecionar_modo(MODO_ESCAVAR)

    def _on_click(self, mouse):
        e = self.estado

        # ── Voltar ──────────────────────────────────────────────────────
        if self.btn_voltar.collidepoint(mouse):
            self.game.mudar_estado(ESTADO_JOGO_MENU_PRINCIPAL)
            return

        # ── Fase de Ameaça ──────────────────────────────────────────────
        if self.fase == "FASE_AMEACA":
            if self.carta_cerco and self.btn_confirmar.collidepoint(mouse):
                self._resolver_carta_cerco()
            return

        # ── Jogar Carta / Ação Livre ─────────────────────────────────────
        if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
            # Botão Fim de Turno
            if self.btn_fim_turno.collidepoint(mouse):
                self._fim_turno_heroi()
                return

            # Botões de modo de ação
            if self.btn_mover.collidepoint(mouse):
                self._selecionar_modo(MODO_MOVER); return
            if self.btn_trabalhar.collidepoint(mouse):
                self._selecionar_modo(MODO_TRABALHAR); return
            if self.btn_escavar.collidepoint(mouse):
                self._selecionar_modo(MODO_ESCAVAR); return
            if self.btn_subornar.collidepoint(mouse):
                self._selecionar_modo(MODO_SUBORNAR); return
            if self.btn_convocar.collidepoint(mouse):
                self._selecionar_modo(MODO_CONVOCAR); return

            # Clique em carta na mão
            for i, rect in enumerate(self.carta_rects):
                if rect.collidepoint(mouse):
                    if i < len(e["mao"]):
                        if self.modo_acao == MODO_UPGRADE and self.idx_slot_upgrade >= 0:
                            self.idx_carta_queimar = i
                            self._tentar_upgrade()
                        else:
                            self._jogar_carta(i)
                            self.fase = "ACAO_LIVRE"
                    return

            # Clique em slot de upgrade (painel lateral)
            for slot in e["slots_upgrade"]:
                sid = slot["id"]
                rect = self._slot_rect(sid)
                if rect and rect.collidepoint(mouse):
                    if self.modo_acao == MODO_UPGRADE:
                        self.idx_slot_upgrade = sid
                        self._feedback(f"Slot [{slot['nome']}] selecionado. Agora escolha carta para queimar.", C_OURO)
                    else:
                        self._selecionar_modo(MODO_UPGRADE)
                        self.idx_slot_upgrade = sid
                    return

            # Clique em célula do tabuleiro tático
            if self.mapa_rect.collidepoint(mouse):
                cell = getattr(self, '_hovered_cell_tactical', None)
                if cell:
                    self._on_cell_click(cell[0], cell[1])
                    return

    def _selecionar_modo(self, modo):
        self.modo_acao = modo
        self.idx_slot_upgrade  = -1
        self.idx_carta_queimar = -1
        msgs = {
            MODO_MOVER:     "Modo MOVER: clique em uma zona do mapa [M]",
            MODO_TRABALHAR: "Modo TRABALHAR: confirme na oficina onde está [T]",
            MODO_ESCAVAR:   "Modo ESCAVAR: confirme no Pátio [E]",
            MODO_SUBORNAR:  "Modo SUBORNAR: escolha recurso no painel",
            MODO_UPGRADE:   "Modo UPGRADE: clique no slot e depois na carta para queimar",
            MODO_CONVOCAR:  "Modo CONVOCAR: clique em qualquer célula vazia para colocar um aliado!",
        }
        self._feedback(msgs.get(modo, ""), C_ACENTO)

    def _on_cell_click(self, cx: int, cy: int):
        e = self.estado
        if self.modo_acao == MODO_MOVER:
            ok, custo, msg = validar_mover(e, cx, cy, e["pontos_movimento"], self.motor)
            if ok:
                # Atualiza a posição no tabuleiro isométrico real
                self.motor.tabuleiro.mover_personagem(self.jogador_novak, cx, cy)
                
                delta, logs = executar_mover(e, cx, cy, custo)
                self.estado = aplicar_delta(e, delta)
                e = self.estado
                for t, m in logs: self._push(t, m)
                
                # Recalcula alcancáveis na grade tática
                from ..resolvedor_acoes import obter_celulas_alcancaveis
                self.alcancaveis = obter_celulas_alcancaveis(
                    self.motor, (e.get("heroi_x", 9), e.get("heroi_y", 9)),
                    e["pontos_movimento"]
                )
                self._feedback(f"Moveu para ({cx}, {cy})", C_VERDE)
                self.modo_acao = MODO_NENHUM
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_TRABALHAR:
            ok, recurso, msg = validar_trabalhar(e, e["pontos_trabalho"])
            if ok:
                delta, logs = executar_trabalhar(e, recurso, e["pontos_trabalho"])
                self.estado = aplicar_delta(e, delta)
                for t, m in logs: self._push(t, m)
                self._feedback(f"+{e['pontos_trabalho']}x {NOME_RECURSO[recurso]}", C_VERDE)
                self.modo_acao = MODO_NENHUM
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_ESCAVAR:
            ok, qtd, msg = validar_escavar(e, e["pontos_escavacao"])
            if ok:
                delta, logs = executar_escavar(e, qtd)
                self.estado = aplicar_delta(e, delta)
                for t, m in logs: self._push(t, m)
                self._feedback(f"Escavou {qtd}x pedregulho!", C_VERDE)
                self.modo_acao = MODO_NENHUM
                if self.estado.get("vitoria"):
                    self.fase = "FIM"
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_CONVOCAR:
            # Seleciona uma classe aliada aleatória (ou você pode escolher uma padrão)
            from ..personagens.protagonistas import Koema, Rilem, Yukito
            from ..personagens import Arqueiro, Clerigo
            aliado_classe = random.choice([Koema, Rilem, Yukito, Arqueiro, Clerigo])
            
            # Tenta posicionar no tabuleiro
            novo_aliado = aliado_classe(f"{aliado_classe.__name__}", "A", nivel=3)
            sucesso = self.motor.tabuleiro.adicionar_personagem(novo_aliado, cx, cy)
            if sucesso:
                self.motor.time_a.append(novo_aliado)
                self.motor.combatentes.append(novo_aliado)
                self._push("HEROI", f"Aliado [{novo_aliado.nome}] convocado na célula ({cx}, {cy})!")
                self._feedback(f"{novo_aliado.nome} Convocado!", C_VERDE)
                self.modo_acao = MODO_NENHUM
            else:
                self._feedback("Célula ocupada ou inválida (parede). Escolha outra!", C_PERIGO)

    def _tentar_upgrade(self):
        e = self.estado
        mao = e["mao"]
        ok, msg = validar_comprar_upgrade(e, self.idx_slot_upgrade, self.idx_carta_queimar, mao)
        if not ok:
            self._feedback(msg, C_PERIGO)
            return
        deck_total = len(mao) + len(e["deck_heroi"]) + len(e["descarte"])
        delta, logs, nova_mao = executar_comprar_upgrade(
            e, self.idx_slot_upgrade, self.idx_carta_queimar, mao, deck_total
        )
        delta["mao"] = nova_mao
        # Adiciona carta de upgrade ao descarte
        slot = e["slots_upgrade"][self.idx_slot_upgrade]
        from ..cerco_isectum import CARTAS_UPGRADE
        carta_up = next((c for c in CARTAS_UPGRADE if c["id"] == slot.get("carta_id")), None)
        if carta_up:
            delta["descarte"] = list(e["descarte"]) + [carta_up]
        self.estado = aplicar_delta(e, delta)
        for t, m in logs: self._push(t, m)
        self._feedback(f"Upgrade [{slot['nome']}] adquirido!", C_OURO)
        self.idx_slot_upgrade  = -1
        self.idx_carta_queimar = -1
        self.modo_acao = MODO_NENHUM

    # ── SUBORNAR (acionado pelo painel) ─────────────────────────────────
    def _subornar_recurso(self, recurso):
        e = self.estado
        ok, msg = validar_subornar(e, recurso)
        if ok:
            delta, logs = executar_subornar(e, recurso)
            self.estado = aplicar_delta(e, delta)
            for t, m in logs: self._push(t, m)
            self._feedback(f"Infiltrador subornado!", C_VERDE)
        else:
            self._feedback(msg, C_PERIGO)
        self.modo_acao = MODO_NENHUM

    # ── FIM DE TURNO DO HERÓI ────────────────────────────────────────────
    def _fim_turno_heroi(self):
        # Reseta pontos
        self.estado = aplicar_delta(self.estado, {
            "pontos_movimento": 0,
            "pontos_trabalho":  0,
            "pontos_escavacao": 0,
        })
        # Descarta mão restante
        desc = list(self.estado["descarte"]) + list(self.estado["mao"])
        self.estado = aplicar_delta(self.estado, {"mao": [], "descarte": desc})
        self.alcancaveis = {}
        self.modo_acao   = MODO_NENHUM
        self._iniciar_fase_ameaca()

    def _iniciar_fase_ameaca(self):
        if not self.deck:
            self.estado = aplicar_delta(self.estado, {"vitoria": True})
            self._push("VITORIA", "Deck de cerco esgotado! VITÓRIA!")
            self.fase = "FIM"
            return
        self.fase = "FASE_AMEACA"
        self.carta_cerco = self.deck.pop()
        self._push("CARTA", f"[N{self.carta_cerco['nivel']}] {self.carta_cerco['simbolo']} "
                            f"{self.carta_cerco['titulo']}")
        self._narrativa(self.carta_cerco["tipo"])

    def _resolver_carta_cerco(self):
        e = self.estado
        if e["is_solo"]:
            d, ls = avancar_ciclo_armas(e)
            if d:
                self.estado = aplicar_delta(e, d)
                e = self.estado
            for t, m in ls: self._push(t, m)

        delta, logs = processar_carta(self.estado, self.carta_cerco)
        self.estado = aplicar_delta(self.estado, delta)
        for t, m in logs: self._push(t, m)

        self.carta_cerco = None
        self.estado = aplicar_delta(self.estado, {"rodada": self.estado["rodada"] + 1})

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.fase = "FIM"
        else:
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()

    # ═══════════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════════
    def update(self):
        self.timer = (self.timer + 1) % 120
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ═══════════════════════════════════════════════════════════════════
    # DRAW
    # ═══════════════════════════════════════════════════════════════════
    def draw(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)

        # Glow ambiente
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (60, 20, 120, 18), (W // 5, H // 4), 320)
        pygame.draw.circle(glow, (10, 60, 30,  14), (W * 4 // 5, H * 3 // 4), 260)
        tela.blit(glow, (0, 0))

        self._draw_header(tela, W)
        self._draw_mapa(tela)
        self._draw_painel_lateral(tela)
        self._draw_mao(tela)
        self._draw_botoes_acao(tela, W, H)

        if self.fase == "FASE_AMEACA" and self.carta_cerco:
            self._draw_carta_overlay(tela, W, H)

        if self.feedback_timer > 0:
            self._draw_feedback(tela, W, H)

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self._draw_fim(tela, W, H)

    # ── HEADER ──────────────────────────────────────────────────────────
    def _draw_header(self, tela, W):
        bar = pygame.Surface((W, 62), pygame.SRCALPHA)
        bar.fill((10, 12, 24, 220))
        tela.blit(bar, (0, 0))
        pygame.draw.line(tela, C_BORDA, (0, 62), (W, 62), 1)

        t1 = self.fG.render("CERCO CONTRA", True, C_ACENTO)
        t2 = self.fG.render("ISECTUM", True, C_OURO)
        tela.blit(t1, (14, 10))
        tela.blit(t2, (14 + t1.get_width() + 8, 10))

        rod = self.fP.render(f"RODADA {self.estado['rodada']}", True, C_DIM)
        tela.blit(rod, (W // 2 - rod.get_width() // 2, 20))

        fase_label = {
            "JOGAR_CARTA": "🃏 JOGUE CARTAS",
            "ACAO_LIVRE":  "⚔️  EXECUTE AÇÕES",
            "FASE_AMEACA": "⚠️  AMEAÇA",
            "FIM":         "🏁 FIM",
        }
        fc = C_VERDE if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE") else C_PERIGO
        fs = self.fMi.render(fase_label.get(self.fase, ""), True, fc)
        tela.blit(fs, (W // 2 - fs.get_width() // 2, 44))

        # Stats rápidas
        e = self.estado
        info = [
            (f"🏰{e['tesouro']}", C_OURO),
            (f"👿R:{e['reserva']}", C_INVASOR),
            (f"⛏️{e['pedregulhos']}", (120, 160, 255)),
            (f"PM:{e['pontos_movimento']}", C_HEROI),
            (f"PT:{e['pontos_trabalho']}", C_VERDE),
            (f"PE:{e['pontos_escavacao']}", C_CERCO),
        ]
        x = W - 14
        for txt, cor in reversed(info):
            s = self.fMi.render(txt, True, cor)
            x -= s.get_width() + 14
            tela.blit(s, (x, 20))

        # Posição do herói
        ph = self.fMi.render(f"🦸 {NOMES_ZONA.get(e['pos_heroi'], '?')}", True, C_HEROI)
        tela.blit(ph, (14, 46))

        # Botão voltar
        m = pygame.mouse.get_pos()
        bc = (40, 40, 70) if self.btn_voltar.collidepoint(m) else (22, 22, 42)
        pygame.draw.rect(tela, bc, self.btn_voltar, border_radius=6)
        vt = self.fMi.render("← Menu  [ESC]", True, C_DIM)
        tela.blit(vt, (self.btn_voltar.x + 6, self.btn_voltar.y + 8))

    # ── MAPA ────────────────────────────────────────────────────────────
    def _draw_mapa(self, tela):
        r = self.mapa_rect
        pygame.draw.rect(tela, (8, 10, 20), r, border_radius=12)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=12)

        # Usar as funções de desenho isométrico do jogo original
        from src.ui.render_combate import get_iso_coords, TILE_HEIGHT, TILE_WIDTH, ELEVATION_SCALE
        from src.resolvedor_acoes import ZONAS_GRID, obter_zona_por_coordenada
        
        tab = self.motor.tabuleiro
        theta = getattr(self, 'angulo_rotacao', 0.0)
        y_offset = 120  # Ajuste vertical dentro da janela do mapa
        
        # 1) Desenhar as Células Isométricas
        cells = []
        for y in range(tab.altura):
            for x in range(tab.largura):
                rx = x - 9.5
                ry = y - 9.5
                rot_x = rx * math.cos(theta) - ry * math.sin(theta) + 9.5
                rot_y = rx * math.sin(theta) + ry * math.cos(theta) + 9.5
                proj_y = (rot_x + rot_y) * (TILE_HEIGHT / 2)
                cells.append((proj_y, x, y))
        cells.sort(key=lambda item: item[0])

        mouse = pygame.mouse.get_pos()
        hovered_cell = None

        # Cores para cada tipo de zona no visual isométrico
        cores_isometricas = {
            "camara_central": (20, 20, 80),
            "carpintaria":    (20, 70, 20),
            "curtume":        (80, 50, 20),
            "fundicao":       (80, 20, 20),
            "patio":          (40, 40, 90),
            "muralha_norte":  (60, 60, 80),
            "muralha_sul":    (60, 60, 80),
            "muralha_oeste":  (60, 60, 80),
            "muralha_leste":  (60, 60, 80),
        }

        for _, x, y in cells:
            el = tab.get_elevation_em(x, y)
            zona = obter_zona_por_coordenada(x, y)
            cor_base = cores_isometricas.get(zona, (30, 30, 35))
            
            # Ajustar coordenada isométrica relativa ao nosso painel de mapa
            cx, cy = get_iso_coords(x, y, el, 0, theta)
            # Centraliza o mapa isométrico na nossa área de mapa
            cx = cx - 300 + r.centerx
            cy = cy - 200 + r.centery - 20
            
            thickness = el * ELEVATION_SCALE
            top_points = [
                (cx, cy - TILE_HEIGHT // 2),
                (cx + TILE_WIDTH // 2, cy),
                (cx, cy + TILE_HEIGHT // 2),
                (cx - TILE_WIDTH // 2, cy)
            ]

            # Destaque de movimento
            if self.modo_acao == MODO_MOVER and (x, y) in self.alcancaveis:
                cor_base = (30, 90, 30)

            # Hover
            if (abs(mouse[0] - cx) * 2 / TILE_WIDTH) + (abs(mouse[1] - cy) * 2 / TILE_HEIGHT) <= 1.0 and r.collidepoint(mouse):
                hovered_cell = (x, y)
                cor_base = tuple(min(255, c + 35) for c in cor_base)

            # Borda / Paredes da elevação
            if thickness > 0:
                r_c, g_c, b_c = cor_base
                cor_left = (int(r_c * 0.7), int(g_c * 0.7), int(b_c * 0.7))
                cor_right = (int(r_c * 0.5), int(g_c * 0.5), int(b_c * 0.5))
                
                left_points = [
                    (cx - TILE_WIDTH // 2, cy),
                    (cx, cy + TILE_HEIGHT // 2),
                    (cx, cy + TILE_HEIGHT // 2 + thickness),
                    (cx - TILE_WIDTH // 2, cy + thickness)
                ]
                right_points = [
                    (cx, cy + TILE_HEIGHT // 2),
                    (cx + TILE_WIDTH // 2, cy),
                    (cx + TILE_WIDTH // 2, cy + thickness),
                    (cx, cy + TILE_HEIGHT // 2 + thickness)
                ]
                pygame.draw.polygon(tela, cor_left, left_points)
                pygame.draw.polygon(tela, cor_right, right_points)
                pygame.draw.polygon(tela, (20, 20, 20), left_points, 1)
                pygame.draw.polygon(tela, (20, 20, 20), right_points, 1)

            pygame.draw.polygon(tela, cor_base, top_points)
            pygame.draw.polygon(tela, C_BORDA, top_points, 1)

            # Desenha Invasores nas Zonas mapeadas
            # Como mostramos o count por zona inteira, vamos desenhar o contador de invasores
            # no centro geométrico de cada zona lógica
            
            # Desenha qualquer combatente do tabuleiro nesta célula
            char_na_celula = tab.grid[y][x]
            if char_na_celula:
                from src.ui.render_combate import desenhar_sprite
                rect_char = pygame.Rect(cx - 16, cy - 26, 32, 32)
                # Destaque se for Novak
                cor_char = (100, 200, 255) if char_na_celula.nome == "Novak" else (180, 180, 255)
                desenhar_sprite(tela, char_na_celula, rect_char, cor_char, self.game.imagens)
                
                # Feedback visual sob Novak
                if char_na_celula.nome == "Novak":
                    pulse = abs(self.timer - 60) / 60.0
                    r_pulse = int(5 + 3 * pulse)
                    pygame.draw.circle(tela, (255, 255, 255), (cx, cy), r_pulse, 1)

        # Guarda a célula sob o mouse para o clique processar
        self._hovered_cell_tactical = hovered_cell

        # 2) Desenhar Textos Informativos de Invasores sobre as Zonas
        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
            el = tab.get_elevation_em(mid_x, mid_y)
            cx, cy = get_iso_coords(mid_x, mid_y, el, 0, theta)
            cx = cx - 300 + r.centerx
            cy = cy - 200 + r.centery - 20
            
            inv = self.estado["invasores"].get(zona_id, 0)
            if inv > 0:
                lbl = self.fP.render(f"INVx{inv}", True, C_INVASOR if zona_id != "camara_central" else C_PERIGO)
                # Fundo do texto para legibilidade
                bg = pygame.Surface((lbl.get_width() + 4, lbl.get_height() + 2))
                bg.fill((10, 10, 20))
                tela.blit(bg, (cx - lbl.get_width() // 2 - 2, cy - 8 - 1))
                tela.blit(lbl, (cx - lbl.get_width() // 2, cy - 8))
            
            # Se for o Pátio, mostra Brutamontes e Infiltradores
            if zona_id == "patio":
                cy_off = cy + 12
                if self.estado["brutamontes"] > 0:
                    lbl2 = self.fMi.render(f"BRUTx{self.estado['brutamontes']}", True, C_BRUTE)
                    tela.blit(lbl2, (cx - lbl2.get_width() // 2, cy_off))
                    cy_off += 12
                if self.estado.get("infiltradores", 0) > 0:
                    lbl3 = self.fMi.render(f"INFx{self.estado['infiltradores']}", True, C_CERCO)
                    tela.blit(lbl3, (cx - lbl3.get_width() // 2, cy_off))
                    cy_off += 12
                peds = self.estado["pedregulhos"]
                lbl4 = self.fMi.render(f"TUNEL: {peds}", True, (120, 160, 255))
                tela.blit(lbl4, (cx - lbl4.get_width() // 2, cy_off))

            # Se for Câmara Central, mostra o Tesouro
            if zona_id == "camara_central":
                lbl_t = self.fMi.render(f"OURO: {self.estado['tesouro']}", True, C_OURO)
                bg_t = pygame.Surface((lbl_t.get_width() + 4, lbl_t.get_height() + 2))
                bg_t.fill((10, 10, 20))
                tela.blit(bg_t, (cx - lbl_t.get_width() // 2 - 2, cy + 8 - 1))
                tela.blit(lbl_t, (cx - lbl_t.get_width() // 2, cy + 8))

        # Armas de cerco
        self._draw_armas_cerco(tela)

        # Narrativa
        nr = self.fMi.render(self.narrativa[:88], True, C_DIM)
        tela.blit(nr, (self.mapa_rect.x + 8, self.mapa_rect.bottom - 18))

    def _draw_armas_cerco(self, tela):
        x, y = self.mapa_rect.x + 8, self.mapa_rect.bottom - 50
        t = self.estado["torre_assalto"]
        c_t = {r: cl for r, cl in (("reserva", C_DIM), ("inativa", C_DIM),
                                    ("preparando", C_OURO), ("ativa", C_PERIGO))
               }[t["estado"]]
        tt = self.fMi.render(f"TORRE: {t['estado'].upper()}", True, c_t)
        tela.blit(tt, (x, y))

        ct = self.estado["catapulta"]
        c_c = {r: cl for r, cl in (("reserva", C_DIM), ("inativa", C_DIM),
                                    ("preparando", C_OURO), ("ativa", C_PERIGO))
               }[ct["estado"]]
        ctt = self.fMi.render(f"CATAPULTA: {ct['estado'].upper()}", True, c_c)
        tela.blit(ctt, (x + 180, y))

    # ── PAINEL LATERAL ──────────────────────────────────────────────────
    def _draw_painel_lateral(self, tela):
        pr = self.painel_rect
        pygame.draw.rect(tela, C_PAINEL, pr, border_radius=10)
        pygame.draw.rect(tela, C_BORDA,  pr, 1, border_radius=10)
        x, y, pw, ph = pr.x, pr.y, pr.width, pr.height

        # ── Recursos depositados ─────────────────────────────────────────
        dep = self.estado.get("recursos_depositados", {})
        yt = y + 8
        tt = self.fMi.render("⚙️ RECURSOS DEPOSITADOS", True, C_ACENTO)
        tela.blit(tt, (x + pw // 2 - tt.get_width() // 2, yt)); yt += 18
        res_info = [("🪵", "madeira", (120, 200, 100)),
                    ("🧳", "couro",   (200, 150,  80)),
                    ("⚙️",  "metal",   (180, 180, 220))]
        rx = x + 8
        for emoji, key, cor in res_info:
            s = self.fP.render(f"{emoji}{dep.get(key, 0)}", True, cor)
            tela.blit(s, (rx, yt))
            rx += pw // 3
        yt += 20
        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

        # ── Mercado de Upgrades ──────────────────────────────────────────
        ut = self.fMi.render("🏪 MERCADO DE MELHORIAS", True, C_ACENTO)
        tela.blit(ut, (x + pw // 2 - ut.get_width() // 2, yt)); yt += 18

        self._slot_y_start = yt
        for slot in self.estado["slots_upgrade"]:
            srect = self._slot_rect(slot["id"])
            if srect is None:
                continue
            # Redesenha rect aqui para ficar preciso
            sr = pygame.Rect(x + 6, yt, pw - 12, 38)
            # Guarda mapeamento
            self._slot_rects_cache[slot["id"]] = sr

            if slot.get("bloqueado"):
                scor = (50, 15, 15)
                bcor = C_PERIGO
            elif slot.get("adquirido"):
                scor = (12, 40, 12)
                bcor = C_VERDE
            elif self.idx_slot_upgrade == slot["id"]:
                scor = (30, 20, 60)
                bcor = C_ACENTO
            else:
                scor = (18, 20, 38)
                bcor = C_BORDA
            pygame.draw.rect(tela, scor, sr, border_radius=5)
            pygame.draw.rect(tela, bcor, sr, 1, border_radius=5)

            # Nome e custo
            st_nome = (f"💥{slot['nome']}" if slot.get("bloqueado") else
                       f"✅{slot['nome']}" if slot.get("adquirido") else
                       f"{slot['simbolo']} {slot['nome']}")
            nt = self.fMi.render(st_nome[:26], True,
                                 C_PERIGO if slot.get("bloqueado") else
                                 C_VERDE  if slot.get("adquirido") else C_TEXTO)
            tela.blit(nt, (sr.x + 4, sr.y + 4))

            custo_txt = " ".join(
                f"{NOME_RECURSO.get(r, r)[:2]}:{q}"
                for r, q in slot.get("custo", {}).items()
            )
            ct2 = self.fMi.render(custo_txt, True, C_DIM)
            tela.blit(ct2, (sr.x + 4, sr.y + 20))

            yt += 42

        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

        # ── Log ─────────────────────────────────────────────────────────
        max_lin = max(1, (ph - (yt - y) - 8) // 15)
        entries = self.log[-(max_lin):]
        cor_map = {"DERROTA": C_PERIGO, "VITORIA": C_VERDE, "AMEACA": C_INVASOR,
                   "CERCO": C_CERCO, "CARTA": C_OURO, "HEROI": C_VERDE,
                   "SISTEMA": C_DIM}
        pre_map = {"DERROTA": "⛔", "VITORIA": "🏆", "AMEACA": "👿", "CERCO": "⚡",
                   "CARTA": "🃏", "HEROI": "⚔️", "SISTEMA": "🔧"}
        for tipo, msg in entries:
            cor   = cor_map.get(tipo, C_TEXTO)
            pre   = pre_map.get(tipo, "▪")
            linha = f"{pre} {msg}"
            for part in [linha[i:i + 36] for i in range(0, len(linha), 36)]:
                lt = self.fMi.render(part, True, cor)
                tela.blit(lt, (x + 5, yt))
                yt += 14
                if yt > y + ph - 12:
                    return

    _slot_rects_cache = {}  # dict[int, pygame.Rect]

    def _slot_rect(self, slot_id):
        return self._slot_rects_cache.get(slot_id)

    # ── MÃO DO HERÓI (bottom strip) ──────────────────────────────────────
    def _draw_mao(self, tela):
        mr = self.mao_rect
        pygame.draw.rect(tela, (10, 12, 24), mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)

        mao = self.estado["mao"]
        self.carta_rects = []

        if not mao:
            nt = self.fP.render("Sem cartas na mão — jogue cartas ou passe o turno", True, C_DIM)
            tela.blit(nt, (mr.centerx - nt.get_width() // 2, mr.centery - 8))
            return

        cw    = min(120, (mr.width - 10) // max(1, len(mao)))
        gap   = max(2, (mr.width - cw * len(mao)) // (len(mao) + 1))
        mouse = pygame.mouse.get_pos()

        for i, carta in enumerate(mao):
            cx = mr.x + gap + i * (cw + gap)
            cy = mr.y + 4
            ch = mr.height - 8
            crect = pygame.Rect(cx, cy, cw, ch)
            self.carta_rects.append(crect)

            hover = crect.collidepoint(mouse)
            sel   = (i == self.idx_carta_queimar)
            fundo = C_ACENTO if sel else (C_CARD_HL if hover else C_CARD)
            pygame.draw.rect(tela, fundo, crect, border_radius=7)
            pygame.draw.rect(tela, C_ACENTO if sel else C_BORDA, crect, 1, border_radius=7)

            # Símbolo
            st = self.fM.render(carta.get("simbolo", "?"), True, C_TEXTO)
            tela.blit(st, (crect.centerx - st.get_width() // 2, cy + 4))

            # Nome
            nt = self.fMi.render(carta["nome"][:14], True, C_TEXTO)
            tela.blit(nt, (crect.centerx - nt.get_width() // 2, cy + 28))

            # Stats
            stats = []
            if carta.get("movimento"): stats.append(f"{carta['movimento']}PM")
            if carta.get("trabalho"):  stats.append(f"{carta['trabalho']}PT")
            if carta.get("escavacao"): stats.append(f"{carta['escavacao']}PE")
            st2 = self.fMi.render(" ".join(stats), True, C_HEROI)
            tela.blit(st2, (crect.centerx - st2.get_width() // 2, cy + 44))

            if sel:
                ql = self.fMi.render("QUEIMAR", True, C_PERIGO)
                tela.blit(ql, (crect.centerx - ql.get_width() // 2, cy + 62))

    # ── BOTÕES DE AÇÃO ───────────────────────────────────────────────────
    def _draw_botoes_acao(self, tela, W, H):
        mouse = pygame.mouse.get_pos()
        e = self.estado

        def _btn(rect, label, ativo, cor_at, cor_hl, cor_off):
            cor = (cor_hl if rect.collidepoint(mouse) else cor_at) if ativo else cor_off
            pygame.draw.rect(tela, cor, rect, border_radius=7)
            pygame.draw.rect(tela, C_BORDA, rect, 1, border_radius=7)
            t = self.fMi.render(label, True, C_TEXTO if ativo else C_DIM)
            tela.blit(t, (rect.centerx - t.get_width() // 2,
                          rect.centery - t.get_height() // 2))

        if self.fase == "FASE_AMEACA":
            if self.carta_cerco:
                _btn(self.btn_confirmar, "▶ Resolver Ameaça  [ESPAÇO]",
                     True, (40, 20, 80), (70, 40, 130), C_PAINEL)
            return

        # Turno do herói
        tem_pm = e["pontos_movimento"] > 0
        tem_pt = e["pontos_trabalho"]  > 0
        tem_pe = e["pontos_escavacao"] > 0

        m_at = MODO_MOVER == self.modo_acao
        t_at = MODO_TRABALHAR == self.modo_acao
        e_at = MODO_ESCAVAR == self.modo_acao
        s_at = MODO_SUBORNAR == self.modo_acao

        _btn(self.btn_mover,     f"[M] Mover ({e['pontos_movimento']}PM)",
             tem_pm, (20, 50, 20) if not m_at else (30, 80, 30),
             (40, 80, 40), (20, 28, 20))
        _btn(self.btn_trabalhar, f"[T] Trabalhar ({e['pontos_trabalho']}PT)",
             tem_pt, (50, 30, 10) if not t_at else (80, 50, 20),
             (90, 60, 20), (28, 20, 10))
        _btn(self.btn_escavar,   f"[E] Escavar ({e['pontos_escavacao']}PE)",
             tem_pe, (10, 30, 60) if not e_at else (20, 50, 90),
             (30, 70, 110), (10, 18, 30))
        _btn(self.btn_subornar,  "Subornar Inf",
             e.get("infiltradores", 0) > 0,
             (50, 30, 50) if not s_at else (80, 50, 80),
             (90, 60, 90), (28, 18, 28))
        
        c_at = MODO_CONVOCAR == self.modo_acao
        _btn(self.btn_convocar,  "[C] Convocar",
             True, (30, 60, 60) if not c_at else (45, 90, 90),
             (60, 110, 110), (15, 30, 30))

        # Fim de turno
        _btn(self.btn_fim_turno, "Encerrar Turno  [↵]",
             True, (60, 20, 20), (90, 30, 30), C_PAINEL)

        # Subornar inline (se modo ativo)
        if self.modo_acao == MODO_SUBORNAR:
            dep = e.get("recursos_depositados", {})
            bx = self.btn_subornar.right + 8
            for res, nome in [("madeira", "🪵"), ("couro", "🧳"), ("metal", "⚙️")]:
                br = pygame.Rect(bx, H - 48, 50, 36)
                ativo = dep.get(res, 0) > 0
                _btn(br, f"{nome}{dep.get(res,0)}", ativo,
                     (30, 40, 30), (50, 70, 50), (20, 20, 20))
                # Registra clique
                if br.collidepoint(mouse) and ativo:
                    if pygame.mouse.get_pressed()[0]:
                        self._subornar_recurso(res)
                bx += 56

    # ── OVERLAY CARTA DE AMEAÇA ──────────────────────────────────────────
    def _draw_carta_overlay(self, tela, W, H):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        tela.blit(ov, (0, 0))

        cw, ch = 440, 270
        cx = W // 2 - cw // 2
        cy = H // 2 - ch // 2
        carta = self.carta_cerco
        nivel = carta.get("nivel", 1)
        cor_niv = [C_VERDE, (100, 200, 255), C_OURO, C_CERCO, C_PERIGO][min(nivel - 1, 4)]

        pygame.draw.rect(tela, (10, 12, 26), pygame.Rect(cx, cy, cw, ch), border_radius=14)
        pygame.draw.rect(tela, cor_niv,      pygame.Rect(cx, cy, cw, ch), 3, border_radius=14)

        pulse = abs(self.timer - 60) / 60.0
        gs = pygame.Surface((cw + 20, ch + 20), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*cor_niv, int(35 * pulse)), gs.get_rect(), border_radius=18)
        tela.blit(gs, (cx - 10, cy - 10))

        nv_t = self.fMi.render(f"NÍVEL {nivel}", True, cor_niv)
        tela.blit(nv_t, (cx + cw // 2 - nv_t.get_width() // 2, cy + 8))

        sim = self.fT.render(carta.get("simbolo", "?"), True, C_TEXTO)
        tela.blit(sim, (cx + cw // 2 - sim.get_width() // 2, cy + 30))

        tt = self.fG.render(carta.get("titulo", ""), True, C_TEXTO)
        tela.blit(tt, (cx + cw // 2 - tt.get_width() // 2, cy + 90))

        tipo_lbl = {"invasor": "👿 INVASOR COMUM", "mover": "🏃 AVANÇO",
                    "torre_assalto": "🗼 TORRE DE ASSALTO",
                    "catapulta": "💥 CATAPULTA DE CERCO"
                    }.get(carta["tipo"], carta["tipo"].upper())
        tp = self.fM.render(tipo_lbl, True, cor_niv)
        tela.blit(tp, (cx + cw // 2 - tp.get_width() // 2, cy + 130))

        nr = self.fMi.render(f'"{self.narrativa[:64]}"', True, (150, 170, 210))
        tela.blit(nr, (cx + cw // 2 - nr.get_width() // 2, cy + 168))

        ins = self.fP.render("[ ESPAÇO ] → Resolver", True, C_DIM)
        tela.blit(ins, (cx + cw // 2 - ins.get_width() // 2, cy + 235))

    # ── FEEDBACK ────────────────────────────────────────────────────────
    def _draw_feedback(self, tela, W, H):
        alpha = min(255, self.feedback_timer * 4)
        surf  = pygame.Surface((W, 32), pygame.SRCALPHA)
        surf.fill((*self.msg_cor, 30))
        tela.blit(surf, (0, H // 2 - 16))
        ft = self.fP.render(self.msg_feedback[:80], True, self.msg_cor)
        tela.blit(ft, (W // 2 - ft.get_width() // 2, H // 2 - 10))

    # ── TELA DE FIM ──────────────────────────────────────────────────────
    def _draw_fim(self, tela, W, H):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        tela.blit(ov, (0, 0))
        e = self.estado
        vit = e.get("vitoria")
        cor = C_VERDE if vit else C_PERIGO
        t1  = self.fT.render("🏆 VITÓRIA!" if vit else "💀 DERROTA!", True, cor)
        tela.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 90))
        msg = (e.get("msg_vitoria") or "Os defensores resistiram!") if vit \
            else (e.get("msg_derrota") or "A fortaleza caiu.")
        t2 = self.fM.render(msg[:64], True, C_TEXTO)
        tela.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 20))
        t3 = self.fP.render(
            f"Rodada {e['rodada']}  |  Tesouro: {e['tesouro']}🪙  |  "
            f"Cartas no cerco: {len(self.deck)}", True, C_DIM
        )
        tela.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 24))
        t4 = self.fP.render("Clique para voltar ao menu", True, C_DIM)
        tela.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 + 60))
