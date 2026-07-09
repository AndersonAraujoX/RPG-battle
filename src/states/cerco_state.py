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
    OFICINAS, ZONA_ESCAVACAO, NOME_RECURSO,
    obter_zona_por_coordenada, ZONAS_GRID
)
from ..juiz_combate import (
    resolver_melee, resolver_distancia,
    rolar_d6_customizado, calcular_dano_melee,
    resetar_dano_turno_brutamonte, validar_pode_atacar_distancia,
    ZONAS_TORRES, ZONAS_INTERNAS
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

# Mapeamento zona → tipo de terreno (para sprites)
ZONA_TERRENO_MAP = {
    "camara_central": "normal",
    "curtume":        "dificil",
    "carpintaria":    "floresta",
    "fundicao":       "rocha",
    "patio":          "fogo",
    "muralha_norte":  "parede",
    "muralha_sul":    "parede",
    "muralha_oeste":  "parede",
    "muralha_leste":  "parede",
    "torre_nw":       "rocha",
    "torre_ne":       "rocha",
    "torre_sw":       "rocha",
    "torre_se":       "rocha",
    "_corredor":      "normal",
    "_campo":         "floresta",
    "_exterior":      "floresta",
}

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
MODO_ATACAR    = "atacar"       # corpo-a-corpo: clique na zona com invasores
MODO_ATIRAR    = "atirar"       # balestra: clique no alvo (de uma torre)


class CercoState(GameState):
    """Estado Pygame completo — Resolvedor de Ações como núcleo."""


    TAM_MAO = 5        # máximo de cartas na mão por turno
    DECK_FIXO = 12     # tamanho fixo do deck do herói

    def __init__(self, game, config=None):
        super().__init__(game)
        if config is None:
            config = self._default_config()
        self.config = config
        diff = config.get("dificuldade", {})
        herois = config.get("herois", [])
        self.estado  = criar_estado(
            pedregulhos=diff.get("pedregulhos", 8),
            is_solo=True
        )
        self.estado["tesouro"] = diff.get("tesouro", 20)
        self.estado["reserva"] = diff.get("reserva", 10)

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
        self.idx_carta_queimar  = -1
        self.idx_slot_upgrade   = -1
        self.idx_carta_sendo_jogada = -1
        # Zonas alcançáveis (highlight)
        self.alcancaveis        = {}
        self.zoom               = 1.0
        self.map_backbuffer     = None
        self.map_backbuffer_sujo = True
        # Animação de caminhada
        self.walk_anim          = None  # {char, from_pos, to_pos, progress,速度}
        self.monster_walk_anims = {}
        
        # Cria um motor de combate simulado para renderizar o cenário e calcular as distâncias na grade
        from ..motor_combate import MotorCombate
        self.motor = MotorCombate(args_times=[0]*24, gerar_terreno=False)
        # Configurar zonas no terreno
        from ..resolvedor_acoes import ZONAS_GRID
        # Preencher o terrain_grid do tabuleiro com as zonas correspondentes
        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            for cy in range(y1, y2 + 1):
                for cx in range(x1, x2 + 1):
                    if not (0 <= cx < self.motor.tabuleiro.largura and 0 <= cy < self.motor.tabuleiro.altura):
                        continue
                    if "muralha" in zona_id:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "rocha"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 1
                    elif "torre" in zona_id:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "barril"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 2
                    elif zona_id == "patio":
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "fogo"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "curtume":
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "dificil"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "carpintaria":
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "floresta"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "fundicao":
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "rocha"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0
                    elif zona_id == "camara_central":
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "normal"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 1
                    else:
                        self.motor.tabuleiro.terrain_grid[cy][cx] = "normal"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0

        # Cria os heróis selecionados e os posiciona no tabuleiro
        POSICOES_INICIAIS = [(9, 9), (7, 7), (11, 7), (7, 11), (9, 5), (5, 9), (13, 9)]
        self.herois = []
        self.heroi_atual_idx = 0
        self.motor.time_a = []
        self.motor.combatentes = []

        if not herois:
            from ..personagens.novos_personagens import Stark
            herois = [("Stark", Stark)]
        for i, (nome, cls) in enumerate(herois):
            pos = POSICOES_INICIAIS[i] if i < len(POSICOES_INICIAIS) else (9, 9)
            heroi = cls(nome, "A", nivel=5)
            self.herois.append(heroi)
            self.motor.time_a.append(heroi)
            self.motor.combatentes.append(heroi)
            self.motor.tabuleiro.adicionar_personagem(heroi, pos[0], pos[1])
        # Inicializa o status individual para cada herói no estado do jogo
        self.estado["herois_status"] = {}
        self.estado["herois_jogaram"] = []
        import copy
        import random
        from src.cerco_isectum import CARTAS_BASICAS
        
        # O primeiro herói herda o deck/descarte/mão inicial do estado geral
        p_heroi = self.herois[0]
        self.estado["herois_status"][p_heroi.nome] = {
            "mao":              list(self.estado.get("mao", [])),
            "deck_heroi":       list(self.estado.get("deck_heroi", [])),
            "descarte":         list(self.estado.get("descarte", [])),
            "excluidas_ciclo":  list(self.estado.get("excluidas_ciclo", [])),
            "pontos_movimento": self.estado.get("pontos_movimento", 0),
            "pontos_trabalho":  self.estado.get("pontos_trabalho", 0),
            "pontos_escavacao": self.estado.get("pontos_escavacao", 0),
            "voo_ativo":        self.estado.get("voo_ativo", False)
        }
        
        # Os heróis subsequentes recebem um baralho básico completo próprio embaralhado
        for h in self.herois[1:]:
            deck_sub = copy.deepcopy(CARTAS_BASICAS)
            random.shuffle(deck_sub)
            self.estado["herois_status"][h.nome] = {
                "mao":              [],
                "deck_heroi":       deck_sub,
                "descarte":         [],
                "excluidas_ciclo":  [],
                "pontos_movimento": 0,
                "pontos_trabalho":  0,
                "pontos_escavacao": 0,
                "voo_ativo":        False
            }
        self._setup_fonts()
        self._setup_layout()
        self.terrain_iso_cache = {}

        # Carrega o spritesheet das cartas do baralho
        from ..utils import resource_path
        caminho_card = resource_path("assets/images/environment/card/pixelCardAssest.png")
        try:
            self.spritesheet_cartas = pygame.image.load(caminho_card).convert_alpha()
            # Fatiar as cartas da primeira linha
            w_sheet, h_sheet = self.spritesheet_cartas.get_size()
            cw_temp = w_sheet // 6
            ch_temp = h_sheet // 2
            self.card_sprites = {
                "azul":      self.spritesheet_cartas.subsurface((0,         0, cw_temp, ch_temp)),
                "vermelha":  self.spritesheet_cartas.subsurface((cw_temp,   0, cw_temp, ch_temp)),
                "cinza":     self.spritesheet_cartas.subsurface((cw_temp*2, 0, cw_temp, ch_temp)),
                "verde":     self.spritesheet_cartas.subsurface((cw_temp*3, 0, cw_temp, ch_temp)),
                "amarela":   self.spritesheet_cartas.subsurface((cw_temp*4, 0, cw_temp, ch_temp)),
                "pedra":     self.spritesheet_cartas.subsurface((cw_temp*5, 0, cw_temp, ch_temp)),
            }
        except Exception as e:
            print(f"Erro ao carregar spritesheet de cartas: {e}")
            self.spritesheet_cartas = None
            self.card_sprites = {}
        
        self.carta_rects = []
        self.animacoes_cartas_compra = []
        self._init_terrain_textures()
        self._comprar_mao()
        nomes_herois = ", ".join(("?????" if h.nome == "Aquele" else h.nome) for h in self.herois)
        self._push("SISTEMA", f"Cerco contra Isectum! Heróis: {nomes_herois}")
        self._push("SISTEMA", f"Dificuldade: {diff.get('nome', 'Normal')}")

    @property
    def heroi_atual(self):
        if not self.herois:
            return None
        if self.heroi_atual_idx >= len(self.herois):
            self.heroi_atual_idx = 0
        return self.herois[self.heroi_atual_idx]

    def _salvar_status_heroi(self, nome_heroi):
        if "herois_status" not in self.estado:
            self.estado["herois_status"] = {}
        self.estado["herois_status"][nome_heroi] = {
            "mao":              list(self.estado.get("mao", [])),
            "deck_heroi":       list(self.estado.get("deck_heroi", [])),
            "descarte":         list(self.estado.get("descarte", [])),
            "excluidas_ciclo":  list(self.estado.get("excluidas_ciclo", [])),
            "pontos_movimento": self.estado.get("pontos_movimento", 0),
            "pontos_trabalho":  self.estado.get("pontos_trabalho", 0),
            "pontos_escavacao": self.estado.get("pontos_escavacao", 0),
            "voo_ativo":        self.estado.get("voo_ativo", False)
        }

    def _carregar_status_heroi(self, nome_heroi):
        if "herois_status" not in self.estado or nome_heroi not in self.estado["herois_status"]:
            return
        status = self.estado["herois_status"][nome_heroi]
        self.estado = aplicar_delta(self.estado, {
            "mao":              list(status.get("mao", [])),
            "deck_heroi":       list(status.get("deck_heroi", [])),
            "descarte":         list(status.get("descarte", []),),
            "excluidas_ciclo":  list(status.get("excluidas_ciclo", [])),
            "pontos_movimento": status.get("pontos_movimento", 0),
            "pontos_trabalho":  status.get("pontos_trabalho", 0),
            "pontos_escavacao": status.get("pontos_escavacao", 0),
            "voo_ativo":        status.get("voo_ativo", False)
        })

    def _alternar_heroi(self):
        """Alterna para o próximo herói na lista, salvando e carregando o status correspondente."""
        if len(self.herois) <= 1:
            return
        
        # Salva o status do herói atual antes de alternar
        heroi_antigo = self.heroi_atual
        if heroi_antigo:
            self._salvar_status_heroi(heroi_antigo.nome)
            
        self.heroi_atual_idx = (self.heroi_atual_idx + 1) % len(self.herois)
        novo = self.heroi_atual
        if novo:
            # Carrega o status do novo herói
            self._carregar_status_heroi(novo.nome)
            
            # Encontra a posição do herói no grid
            tab = self.motor.tabuleiro
            from ..resolvedor_acoes import obter_zona_por_coordenada
            for gy in range(tab.altura):
                for gx in range(tab.largura):
                    if tab.grid[gy][gx] is novo:
                        self.estado = aplicar_delta(self.estado, {
                            "heroi_x": gx,
                            "heroi_y": gy,
                            "pos_heroi": obter_zona_por_coordenada(gx, gy) or "camara_central",
                        })
                        break
            nome_exibido = "?????" if novo.nome == "Aquele" else novo.nome
            self._feedback(f"Herói atual: {nome_exibido}", C_HEROI)
            # Recalcula alcançáveis
            from ..resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor,
                (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )

    def _default_config(self):
        from ..personagens.novos_personagens import Stark
        return {
            "herois": [("Stark", Stark)],
            "dificuldade": {"nome": "Normal", "pedregulhos": 8, "tesouro": 20, "reserva": 10},
        }

    # ── FONTS ────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        s = max(0.5, ALTURA_TELA / 720.0)
        self.fT  = pygame.font.Font(None, max(16, int(48 * s)))
        self.fG  = pygame.font.Font(None, max(14, int(36 * s)))
        self.fM  = pygame.font.Font(None, max(12, int(28 * s)))
        self.fP  = pygame.font.Font(None, max(10, int(22 * s)))
        self.fMi = pygame.font.Font(None, max(8,  int(18 * s)))

    # ── LAYOUT (recalculado uma vez) ─────────────────────────────────────
    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        # Área do mapa (redimensionada para dar espaço na vertical)
        self.mapa_rect   = pygame.Rect(8, 65, W - 330, H - 217)
        # Painel lateral (log + recursos + mercado)
        self.painel_rect = pygame.Rect(W - 318, 65, 310, H - 75)
        # Faixa de cartas na mão (expandida para preencher o espaço inferior)
        self.mao_rect    = pygame.Rect(8, H - 146, W - 330, 138)
        # Botões de ação — posicionados na base inferior (H - 48)
        bw, bh = 110, 36
        bx = W - 318
        by = H - 48
        self.btn_fim_turno  = pygame.Rect(bx,         by, bw + 26, bh)
        self.btn_mover      = pygame.Rect(8,          by, bw - 4,  bh)
        self.btn_trabalhar  = pygame.Rect(8+bw,       by, bw - 4,  bh)
        self.btn_escavar    = pygame.Rect(8+bw*2,     by, bw - 4,  bh)
        self.btn_subornar   = pygame.Rect(8+bw*3,     by, bw - 4,  bh)
        self.btn_convocar   = pygame.Rect(8+bw*4,     by, bw - 4,  bh)
        self.btn_atacar     = pygame.Rect(8+bw*5,     by, bw - 4,  bh)
        self.btn_atirar     = pygame.Rect(8+bw*6,     by, bw - 4,  bh)
        self.btn_voltar     = pygame.Rect(W - 156, 68,  140,  30)
        self.btn_confirmar  = pygame.Rect(W//2-100, H-48, 200,  bh)
        # Rects das cartas na mão serão preenchidos apenas no _draw_mao
        pass

    def _draw_alpha_polygon(self, tela, color, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x + 1
        h = max_y - min_y + 1
        
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        translated_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        pygame.draw.polygon(surf, color, translated_points)
        tela.blit(surf, (min_x, min_y))

    def _draw_celula_tactica(self, tela, cx, cy, w, h, cor_base, cor_borda, estilo='movimento'):
        pulso = (math.sin(self.timer * 0.1) + 1.0) / 2.0  # 0.0 a 1.0
        
        alpha_base = cor_base[3] if len(cor_base) > 3 else 70
        alpha = int(alpha_base - 20 + 40 * pulso)
        alpha = max(20, min(230, alpha))
        
        fill_color = (cor_base[0], cor_base[1], cor_base[2], alpha)
        
        pts_outer = [
            (cx, cy - h // 2),
            (cx + w // 2, cy),
            (cx, cy + h // 2),
            (cx - w // 2, cy)
        ]
        self._draw_alpha_polygon(tela, fill_color, pts_outer)
        
        r_b, g_b, b_b = cor_borda[:3]
        cor_borda_pulsante = (
            max(0, min(255, int(r_b * (0.8 + 0.3 * pulso)))),
            max(0, min(255, int(g_b * (0.8 + 0.3 * pulso)))),
            max(0, min(255, int(b_b * (0.8 + 0.3 * pulso))))
        )
        pygame.draw.polygon(tela, cor_borda_pulsante, pts_outer, 2)
        
        w_inner = int(w * 0.7)
        h_inner = int(h * 0.7)
        pts_inner = [
            (cx, cy - h_inner // 2),
            (cx + w_inner // 2, cy),
            (cx, cy + h_inner // 2),
            (cx - w_inner // 2, cy)
        ]
        cor_inner = (cor_borda[0], cor_borda[1], cor_borda[2], int(40 + 20 * pulso))
        self._draw_alpha_polygon(tela, cor_inner, pts_inner)
        pygame.draw.polygon(tela, cor_borda, pts_inner, 1)

        # Cantoneiras
        bracket_w = max(2, w // 7)
        bracket_h = max(1, h // 7)
        
        pygame.draw.line(tela, (255, 255, 255), (cx, cy - h // 2), (cx - bracket_w, cy - h // 2 + bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx, cy - h // 2), (cx + bracket_w, cy - h // 2 + bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx, cy + h // 2), (cx - bracket_w, cy + h // 2 - bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx, cy + h // 2), (cx + bracket_w, cy + h // 2 - bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx - w // 2, cy), (cx - w // 2 + bracket_w, cy - bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx - w // 2, cy), (cx - w // 2 + bracket_w, cy + bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx + w // 2, cy), (cx + w // 2 - bracket_w, cy - bracket_h), 2)
        pygame.draw.line(tela, (255, 255, 255), (cx + w // 2, cy), (cx + w // 2 - bracket_w, cy + bracket_h), 2)

    # ── SPRITES DE TERRENO ────────────────────────────────────────────
    def _init_terrain_textures(self):
        self.terrain_iso_cache.clear()

    def _tex(self, zona_key, tw, th):
        tipo = ZONA_TERRENO_MAP.get(zona_key, "normal")
        key = (tipo, tw, th)
        if key in self.terrain_iso_cache:
            return self.terrain_iso_cache[key]
        img = self.game.imagens.get(f"terreno_{tipo.lower()}")
        if img is None:
            return None
        
        # Recorte inteligente do centro (crop) ajustado para preservar mais detalhes originais da imagem (82%)
        orig_w, orig_h = img.get_size()
        crop_w = int(orig_w * 0.82)
        crop_h = int(orig_h * 0.82)
        crop_x = (orig_w - crop_w) // 2
        crop_y = (orig_h - crop_h) // 2
        
        try:
            cropped_img = img.subsurface(pygame.Rect(crop_x, crop_y, crop_w, crop_h))
        except Exception:
            cropped_img = img

        # Redimensionamento bilinear de alta fidelidade para suavizar pixels e remover borrões
        try:
            scaled = pygame.transform.smoothscale(cropped_img, (tw, th))
        except Exception:
            scaled = pygame.transform.scale(cropped_img, (tw, th))
            
        surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        surf.blit(scaled, (0, 0))
        
        mask = pygame.Surface((tw, th), pygame.SRCALPHA)
        diamond = [(tw // 2, 0), (tw, th // 2), (tw // 2, th), (0, th // 2)]
        pygame.draw.polygon(mask, (255, 255, 255, 255), diamond)
        surf.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)
        self.terrain_iso_cache[key] = surf
        return surf

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
        """Compra até TAM_MAO cartas do deck do herói para a mão com animação."""
        mao = list(self.estado["mao"])
        deck = list(self.estado["deck_heroi"])
        discard = list(self.estado["descarte"])
        
        cartas_anteriores = len(mao)
        cartas_adicionadas = []

        while len(mao) < self.TAM_MAO:
            if not deck:
                if not discard and not self.estado.get("excluidas_ciclo", []):
                    break
                
                # Reembaralha as 12 cartas (deck + discard + hand + excluidas)
                todas = list(discard) + list(mao) + list(deck) + list(self.estado.get("excluidas_ciclo", []))
                random.shuffle(todas)
                
                # Descarta 2 aleatoriamente de face para baixo (excluídas do ciclo)
                # Para preservar a mão ativa do jogador, as 2 descartadas são tiradas de cartas fora de "mao"
                candidatas_descarte = [c for c in todas if c not in mao]
                excluidas = []
                if len(candidatas_descarte) >= 2:
                    excluidas.append(candidatas_descarte.pop(random.randrange(len(candidatas_descarte))))
                    excluidas.append(candidatas_descarte.pop(random.randrange(len(candidatas_descarte))))
                
                # As restantes formam o novo Deck de Saque (deck_heroi) menos o que já está na mão
                deck = [c for c in todas if c not in mao and c not in excluidas]
                discard = []
                
                self.estado = aplicar_delta(self.estado, {
                    "excluidas_ciclo": excluidas
                })
                self._push("SISTEMA", "Ciclo do Baralho: 12 cartas reembaralhadas. 2 descartadas face para baixo.")
            
            carta = deck.pop()
            mao.append(carta)
            cartas_adicionadas.append(carta)

        self.estado = aplicar_delta(self.estado, {
            "mao": mao, "deck_heroi": deck, "descarte": discard
        })

        # Dispara animações de compra para as cartas adicionadas
        if not hasattr(self, 'animacoes_cartas_compra'):
            self.animacoes_cartas_compra = []

        mr = self.mao_rect
        deck_x = mr.right - 76
        deck_y = mr.y + 6

        for idx_adicionado, carta in enumerate(cartas_adicionadas):
            idx_mao = cartas_anteriores + idx_adicionado
            cx, cy, cw_f, ch_f = self._calcular_pos_carta_na_mao(idx_mao, len(mao))
            
            self.animacoes_cartas_compra.append({
                'idx_mao': idx_mao,
                'carta': carta,
                'start_pos': (deck_x, deck_y),
                'end_pos': (cx, cy),
                'cw': cw_f,
                'ch': ch_f,
                'progresso': 0.0,
                'delay': idx_adicionado * 8, # delay de 8 frames (~130ms) entre as cartas
                'finalizada': False
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

        # Seleciona modo de ação automático baseado na carta jogada
        if carta.get("trabalho", 0) > 0:
            self._selecionar_modo(MODO_TRABALHAR)
        elif carta.get("movimento", 0) > 0:
            self._selecionar_modo(MODO_MOVER)
        elif carta.get("escavacao", 0) > 0:
            self._selecionar_modo(MODO_ESCAVAR)

    # ═══════════════════════════════════════════════════════════════════
    # HANDLE EVENTS
    # ═══════════════════════════════════════════════════════════════════
    def handle_events(self, events):
        self._setup_layout()
        mouse = pygame.mouse.get_pos()
        e = self.estado

        for event in events:
            if self.fase == "ESCOLHER_ACAO_CARTA":
                # ESC cancela escolha
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.fase = "ACAO_LIVRE"
                    self.idx_carta_sendo_jogada = -1
                    return
                # Clique do mouse
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    print(f"[DEBUG CLIQUE MODAL] mouse={mouse} ticks={pygame.time.get_ticks()} dt={pygame.time.get_ticks() - getattr(self, 'fase_aberta_tick', 0)}")
                    print(f"[DEBUG CLIQUE RECTS] andar={getattr(self, 'btn_andar_rect', None)} coletar={getattr(self, 'btn_coletar_rect', None)} ambos={getattr(self, 'btn_ambos_rect', None)} atacar={getattr(self, 'btn_atacar_rect', None)}")
                    if getattr(self, 'btn_andar_rect', None) and self.btn_andar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "andar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_coletar_rect', None) and self.btn_coletar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "coletar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_ambos_rect', None) and self.btn_ambos_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "ambos")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_atacar_rect', None) and self.btn_atacar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "atacar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                continue

            # Fim universal
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                self.game.cerco_state = None
                return

            if e.get("derrota") or e.get("vitoria"):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    self.game.cerco_state = None
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._on_click(mouse)
                elif event.button == 4:
                    new_z = min(3.0, self.zoom + 0.25)
                    if new_z != self.zoom:
                        self.zoom = new_z
                        self.terrain_iso_cache.clear()
                elif event.button == 5:
                    new_z = max(0.35, self.zoom - 0.25)
                    if new_z != self.zoom:
                        self.zoom = new_z
                        self.terrain_iso_cache.clear()
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _screen_to_grid(self, mx: int, my: int) -> tuple | None:
        """Converte coordenada da tela para célula (gx, gy) no mapa isométrico do cerco."""
        r = self.mapa_rect
        if not r.collidepoint(mx, my):
            return None
        CX = r.centerx
        CY = r.centery - 5
        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        theta = self.game.angulo_rotacao
        from ..resolvedor_acoes import obter_zona_por_coordenada as _oz
        GRID_MIN, GRID_MAX = 0, 19

        def _classificar(gx, gy):
            if GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                z = _oz(gx, gy)
                if z:
                    return z
                if 4 <= gx <= 15 and 4 <= gy <= 15:
                    return "_corredor"
            return None

        cells = []
        for gy in range(GRID_MIN, GRID_MAX + 1):
            for gx in range(GRID_MIN, GRID_MAX + 1):
                zona_key = _classificar(gx, gy)
                if zona_key is None:
                    continue
                el = {
                    "camara_central": 3, "curtume": 2, "carpintaria": 2,
                    "fundicao": 2, "patio": 2,
                    "muralha_norte": 4, "muralha_sul": 4,
                    "muralha_oeste": 4, "muralha_leste": 4,
                    "torre_nw": 6, "torre_ne": 6, "torre_sw": 6, "torre_se": 6,
                    "_corredor": 1,
                }.get(zona_key, 1)
                dx = gx - 9.5
                dy = gy - 9.5
                rx = dx * math.cos(theta) - dy * math.sin(theta)
                ry = dx * math.sin(theta) + dy * math.cos(theta)
                cx = (rx - ry) * (TW // 2) + CX
                cy = (rx + ry) * (TH // 2) - el * ES + CY
                proj_y = (rx + ry) * (TH // 2)
                cells.append((proj_y, gx, gy, cx, cy, el))

        cells.sort(key=lambda x: x[0], reverse=True)
        for _, gx, gy, cx, cy, el in cells:
            thick = el * ES
            ctr_y = cy + thick // 2
            half_h = (TH + thick) // 2
            dx_ = abs(mx - cx) / (TW / 2 + 1e-10)
            dy_ = abs(my - ctr_y) / (half_h + 1e-10)
            if dx_ + dy_ <= 1.0:
                return (gx, gy)
        return None

    def _on_key(self, key):
        if key == pygame.K_RETURN:
            if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
                self._fim_turno_heroi()
            elif self.fase == "REPOVOAR_MERCADO":
                self._concluir_fim_turno_completo()
        if key == pygame.K_SPACE:
            if self.fase == "FASE_AMEACA" and self.carta_cerco:
                self._resolver_carta_cerco()
        # Atalhos de teclado para ações diretas foram removidos
        if key == pygame.K_TAB:
            self._alternar_heroi()
        if key in (pygame.K_PLUS, pygame.K_EQUALS):
            new_z = min(3.0, self.zoom + 0.25)
            if new_z != self.zoom:
                self.zoom = new_z
                self.terrain_iso_cache.clear()
        if key == pygame.K_MINUS:
            new_z = max(0.35, self.zoom - 0.25)
            if new_z != self.zoom:
                self.zoom = new_z
                self.terrain_iso_cache.clear()

    # ── ANIMAÇÃO DE CAMINHADA ──────────────────────────────────────────
    def _start_walk(self, char, from_pos, to_pos, on_done=None):
        self.walk_anim = {
            "char": char,
            "from_pos": from_pos,
            "to_pos": to_pos,
            "progress": 0.0,
            "speed": 0.06,
            "on_done": on_done,
        }

    def _start_monster_walk(self, char, from_pos, to_pos):
        self.monster_walk_anims[char] = {
            "char": char,
            "from_pos": from_pos,
            "to_pos": to_pos,
            "progress": 0.0,
            "speed": 0.04,
        }

    def _update_walk(self):
        heroi_movendo = False
        if self.walk_anim:
            a = self.walk_anim
            a["progress"] += a["speed"]
            if a["progress"] >= 1.0:
                a["progress"] = 1.0
                on_done = a.get("on_done")
                self.walk_anim = None
                if on_done:
                    on_done()
                heroi_movendo = True
            else:
                heroi_movendo = True

        remover_anims = []
        for char, a in list(self.monster_walk_anims.items()):
            a["progress"] += a["speed"]
            if a["progress"] >= 1.0:
                remover_anims.append(char)
        for char in remover_anims:
            if char in self.monster_walk_anims:
                del self.monster_walk_anims[char]

        return heroi_movendo

    def _obter_posicao_virtual(self, char, gx, gy):
        zona = getattr(char, "_zona_campo", None)
        if zona == "campo_norte":
            return gx, -2
        elif zona == "campo_sul":
            return gx, 21
        elif zona == "campo_oeste":
            return -2, gy
        elif zona == "campo_leste":
            return 21, gy
        return gx, gy

    def _get_char_screen_pos(self, char, gx, gy, el, default_cx, default_cy):
        a = None
        if self.walk_anim and self.walk_anim["char"] is char:
            a = self.walk_anim
        elif char in self.monster_walk_anims:
            a = self.monster_walk_anims[char]

        if a is None:
            return default_cx, default_cy

        from_gx, from_gy = a["from_pos"]
        to_gx, to_gy = a["to_pos"]
        theta = self.game.angulo_rotacao
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)
        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        CX = self.mapa_rect.centerx
        CY = self.mapa_rect.centery - 5
        p = a["progress"]
        p_smooth = p * p * (3 - 2 * p)
        igx = from_gx + (to_gx - from_gx) * p_smooth
        igy = from_gy + (to_gy - from_gy) * p_smooth
        dx = igx - 9.5
        dy = igy - 9.5
        rx = dx * theta_cos - dy * theta_sin
        ry = dx * theta_sin + dy * theta_cos
        cy_coord = (rx + ry) * (TH // 2) - el * ES
        cx = int((rx - ry) * (TW // 2) + CX)
        cy = int(cy_coord + CY)
        if p < 1.0:
            # Efeito suave de pulo/quique ao caminhar
            cy -= int(abs(math.sin(p * math.pi)) * 6 * self.zoom)
        return cx, cy

    def _on_click(self, mouse):
        if pygame.time.get_ticks() - getattr(self, 'bloqueio_clique_tick', 0) < 150:
            return
        print(f"[DEBUG ON_CLICK] mouse={mouse} fase={self.fase} mao_len={len(self.estado['mao'])} mao={self.estado['mao']} deck_len={len(self.estado['deck_heroi'])} descarte_len={len(self.estado['descarte'])} cartas_rects={getattr(self, 'carta_rects', [])}")
        e = self.estado

        # ── Voltar ──────────────────────────────────────────────────────
        if self.btn_voltar.collidepoint(mouse):
            self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            return

        # ── Fase de Ameaça ──────────────────────────────────────────────
        if self.fase == "FASE_AMEACA":
            if self.carta_cerco and self.btn_confirmar.collidepoint(mouse):
                self._resolver_carta_cerco()
            return

        # ── Jogar Carta / Ação Livre / Reposição de Mercado ──────────────
        if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE", "REPOVOAR_MERCADO"):
            # Botão Fim de Turno
            if self.btn_fim_turno.collidepoint(mouse):
                if self.fase == "REPOVOAR_MERCADO":
                    self._concluir_fim_turno_completo()
                else:
                    self._fim_turno_heroi()
                return

            # Os botões de ação direta foram removidos do rodapé
            pass

            # Clique em carta na mão
            for i, rect in enumerate(self.carta_rects):
                if rect.collidepoint(mouse):
                    if i < len(e["mao"]):
                        carta = e["mao"][i]
                        if carta.get("tipo") in ("orc", "invasor"):
                            self._jogar_carta_invasao(i)
                            return
                        if self.modo_acao == MODO_UPGRADE and self.idx_slot_upgrade >= 0:
                            self.idx_carta_queimar = i
                            self._tentar_upgrade()
                        else:
                            self.idx_carta_sendo_jogada = i
                            self.fase = "ESCOLHER_ACAO_CARTA"
                            self.fase_aberta_tick = pygame.time.get_ticks()
                    return

            if self.fase == "REPOVOAR_MERCADO":
                # Botão Concluir Reposição
                if getattr(self, 'btn_concluir_reposicao_rect', None) and self.btn_concluir_reposicao_rect.collidepoint(mouse):
                    self._concluir_fim_turno_completo()
                    self._feedback("Fase de Ameaça Iniciada!", C_PERIGO)
                    return

                # Cliques nos slots para repovoar ou remover
                for slot in e["slots_upgrade"]:
                    sid = slot["id"]
                    rect = self._slot_rect(sid)
                    if rect and rect.collidepoint(mouse):
                        is_vazio = slot.get("adquirido") or slot.get("carta_id") is None
                        if is_vazio:
                            # Clicou em qual deck?
                            btn_w = (rect.width - 16) // 3
                            btn_amarelo = pygame.Rect(rect.x + 4, rect.y + 4, btn_w, 30)
                            btn_cinza = pygame.Rect(rect.x + 8 + btn_w, rect.y + 4, btn_w, 30)
                            btn_vermelho = pygame.Rect(rect.x + 12 + 2 * btn_w, rect.y + 4, btn_w, 30)

                            import random
                            from src.cerco_isectum import CARTAS_UPGRADE_AMARELO, CARTAS_UPGRADE_CINZA, CARTAS_UPGRADE_VERMELHO
                            nova_carta = None
                            deck_nome = ""

                            if btn_amarelo.collidepoint(mouse):
                                nova_carta = random.choice(CARTAS_UPGRADE_AMARELO)
                                deck_nome = "Amarelo"
                            elif btn_cinza.collidepoint(mouse):
                                nova_carta = random.choice(CARTAS_UPGRADE_CINZA)
                                deck_nome = "Cinza"
                            elif btn_vermelho.collidepoint(mouse):
                                nova_carta = random.choice(CARTAS_UPGRADE_VERMELHO)
                                deck_nome = "Vermelho"

                            if nova_carta:
                                slots = [dict(s) for s in self.estado["slots_upgrade"]]
                                s = slots[sid]
                                s["nome"] = nova_carta["nome"]
                                s["simbolo"] = nova_carta["simbolo"]
                                s["carta_id"] = nova_carta["id"]
                                s["custo"] = dict(nova_carta["custo"])
                                s["descricao"] = nova_carta["descricao"]
                                s["adquirido"] = False
                                s["bloqueado"] = False
                                s["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}

                                self.estado = aplicar_delta(self.estado, {"slots_upgrade": slots})
                                self._push("CARTA", f"Comprada nova carta do Deck {deck_nome} no slot {sid+1}.")
                                self._feedback(f"Carta [{nova_carta['nome']}] adicionada!", C_VERDE)
                                return
                        else:
                            # Clicou no botão descartar (X)?
                            btn_descartar = pygame.Rect(rect.right - 44, rect.y + 4, 40, 30)
                            if btn_descartar.collidepoint(mouse):
                                # Devolver recursos alocados para as oficinas
                                alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
                                for res, qtd in alocados.items():
                                    if qtd > 0:
                                        self._push("SISTEMA", f"Devolvido {qtd}x {res.upper()} para a oficina correspondente.")

                                slots = [dict(s) for s in self.estado["slots_upgrade"]]
                                s = slots[sid]
                                s["carta_id"] = None
                                s["nome"] = "Slot Vazio"
                                s["simbolo"] = ""
                                s["custo"] = {}
                                s["descricao"] = ""
                                s["adquirido"] = True
                                s["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}

                                self.estado = aplicar_delta(self.estado, {"slots_upgrade": slots})
                                self._push("CARTA", f"Carta do slot {sid+1} removida do mercado.")
                                self._feedback("Carta removida do mercado!", C_PERIGO)
                                return
                return

            # Clique em slot de upgrade (painel lateral)
            for slot in e["slots_upgrade"]:
                sid = slot["id"]
                rect = self._slot_rect(sid)
                if rect and rect.collidepoint(mouse):
                    if self.modo_acao == MODO_TRABALHAR:
                        # Alocar recurso do local de produção atual
                        from ..resolvedor_acoes import validar_alocar_recurso, executar_alocar_recurso
                        ok, recurso, msg = validar_alocar_recurso(e, sid, e["pontos_trabalho"])
                        if ok:
                            delta, logs = executar_alocar_recurso(e, sid, recurso)
                            self.estado = aplicar_delta(e, delta)
                            for t, m in logs: self._push(t, m)
                            self._feedback(f"Alocou 1x {recurso.upper()} sobre [{slot['nome']}]!", C_VERDE)
                            # Se não tem mais pontos de trabalho, sai do modo
                            if self.estado["pontos_trabalho"] <= 0:
                                self.modo_acao = MODO_NENHUM
                        else:
                            self._feedback(msg, C_PERIGO)
                    else:
                        # Tentativa de aquisição/troca
                        if slot.get("adquirido"):
                            self._feedback("Esta melhoria já foi adquirida!", C_PERIGO)
                            return
                        if slot.get("bloqueado"):
                            self._feedback("Esta melhoria foi destruída pela catapulta!", C_PERIGO)
                            return
                        
                        # Verifica se todos os recursos necessários estão alocados
                        from ..resolvedor_acoes import CUSTO_ADICIONAL_SLOT
                        custo_base = slot.get("custo", {})
                        custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
                        
                        # Custo total é custo da carta + custo do slot
                        custo_total = {}
                        for r in ["madeira", "couro", "metal"]:
                            qtd = custo_base.get(r, 0) + custo_adicional.get(r, 0)
                            if qtd > 0:
                                custo_total[r] = qtd
                                
                        alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
                        faltam = {}
                        for r, qtd in custo_total.items():
                            if alocados.get(r, 0) < qtd:
                                faltam[r] = qtd - alocados.get(r, 0)
                                
                        if not faltam:
                            # Pronto para adquirir
                            self.modo_acao = MODO_UPGRADE
                            self.idx_slot_upgrade = sid
                            self._feedback(f"Slot [{slot['nome']}] pronto! Escolha uma carta da mão para queimar.", C_OURO)
                        else:
                            # Faltam recursos
                            recs_txt = ", ".join(f"{q}x {r.upper()}" for r, q in faltam.items())
                            self._feedback(f"Falta alocar: {recs_txt}. Vá a uma oficina e use Trabalhar!", C_PERIGO)
                    return

            # Clique em célula do tabuleiro tático
            cell = self._screen_to_grid(mouse[0], mouse[1])
            if cell:
                self._on_cell_click(cell[0], cell[1])
                return

        # ── Movimento livre (fora de qualquer modo) ─────────────────────
        if self.modo_acao == MODO_NENHUM and not self.walk_anim:
            cell = self._screen_to_grid(mouse[0], mouse[1])
            if cell:
                self._on_cell_click(cell[0], cell[1])

    def _selecionar_modo(self, modo):
        self.modo_acao = modo
        self.idx_slot_upgrade  = -1
        self.idx_carta_queimar = -1
        msgs = {
            MODO_MOVER:     "Modo MOVER: clique em uma zona do mapa [M]",
            MODO_TRABALHAR: "Modo TRABALHAR: clique em uma Carta no Mercado para alocar 1x [Recurso] nela!",
            MODO_ESCAVAR:   "Modo ESCAVAR: confirme no Pátio [G]",
            MODO_SUBORNAR:  "Modo SUBORNAR: escolha recurso no painel",
            MODO_UPGRADE:   "Modo UPGRADE: Escolha carta da mão para queimar e resgatar a melhoria completa",
            MODO_CONVOCAR:  "Modo CONVOCAR: clique em qualquer célula vazia para colocar um aliado!",
            MODO_ATACAR:    "[A] ATACAR: clique na zona com invasores para combate melee (2D6 customizados)!",
            MODO_ATIRAR:    "[F] ATIRAR: de uma Torre, clique no alvo externo (Balestra 2D6)!",
        }
        self._feedback(msgs.get(modo, ""), C_ACENTO)

    def _on_cell_click(self, cx: int, cy: int):
        e = self.estado
        if self.walk_anim:
            return

        # Clique em um Goblin Pacífico (Infiltrador) ativa o modo de negociação!
        char = self.motor.tabuleiro.grid[cy][cx]
        if self.modo_acao == MODO_NENHUM and char and getattr(char, "_is_infiltrador", False):
            self.modo_acao = MODO_SUBORNAR
            self.alvo_negociacao = char
            self._feedback("Negociar: escolha Recurso no rodapé ou use Escavação para limpar rochas!", C_OURO)
            return

        # ── Movimento livre (MODO_NENHUM) ───────────────────────────────
        if self.modo_acao == MODO_NENHUM:
            from_pos = (e.get("heroi_x", 9), e.get("heroi_y", 9))
            if from_pos == (cx, cy):
                return
            from ..resolvedor_acoes import custo_minimo_grade
            custo = custo_minimo_grade(self.motor, from_pos, (cx, cy))
            if custo is None:
                self._feedback("Destino inaccessivel!", C_PERIGO)
                return
            def _finalize_free():
                self.motor.tabuleiro.mover_personagem(self.heroi_atual, cx, cy)
                from ..resolvedor_acoes import obter_zona_por_coordenada
                delta = {
                    "heroi_x": cx,
                    "heroi_y": cy,
                    "pos_heroi": obter_zona_por_coordenada(cx, cy) or "camara_central",
                }
                self.estado = aplicar_delta(e, delta)
                self._push("HEROI", f"Moveu para ({cx}, {cy})")
                self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)
            self._start_walk(self.heroi_atual, from_pos, (cx, cy), on_done=_finalize_free)

        elif self.modo_acao == MODO_MOVER:
            ok, custo, msg = validar_mover(e, cx, cy, e["pontos_movimento"], self.motor)
            if ok:
                from_pos = (e.get("heroi_x", 9), e.get("heroi_y", 9))
                def _finalize():
                    self.motor.tabuleiro.mover_personagem(self.heroi_atual, cx, cy)
                    delta, logs = executar_mover(e, cx, cy, custo)
                    self.estado = aplicar_delta(e, delta)
                    e2 = self.estado
                    for t, m in logs: self._push(t, m)
                    from ..resolvedor_acoes import obter_celulas_alcancaveis
                    self.alcancaveis = obter_celulas_alcancaveis(
                        self.motor, (e2.get("heroi_x", 9), e2.get("heroi_y", 9)),
                        e2["pontos_movimento"]
                    )
                    self._feedback(f"Moveu para ({cx}, {cy})", C_VERDE)
                    self.modo_acao = MODO_NENHUM
                    self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)
                self._start_walk(self.heroi_atual, from_pos, (cx, cy), on_done=_finalize)
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_TRABALHAR:
            self._feedback("Clique em uma das cartas do Mercado de Melhorias para alocar o recurso!", C_OURO)

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
            # Seleciona uma classe aliada aleatória
            from ..personagens.novos_personagens import Elden, Kuro, Darwin
            from ..personagens import Arqueiro, Clerigo
            aliado_classe = random.choice([Elden, Kuro, Darwin, Arqueiro, Clerigo])
            
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

        elif self.modo_acao == MODO_ATACAR:
            # ── COMBATE CORPO-A-CORPO com D6 Customizado ─────────────────
            zona_alvo = obter_zona_por_coordenada(cx, cy)
            if not zona_alvo:
                self._feedback("Clique em uma zona válida do mapa!", C_PERIGO)
                return
            zona_heroi = self.estado.get("pos_heroi")
            if zona_heroi != zona_alvo:
                self._feedback("Herói precisa estar na mesma zona do inimigo para combate corpo-a-corpo!", C_PERIGO)
                return
            invasores_na_zona = self.estado["invasores"].get(zona_alvo, 0)
            infiltradores = self.estado.get("infiltradores", 0)
            if invasores_na_zona == 0 and self.estado.get("brutamontes", 0) == 0 and (zona_alvo != "patio" or infiltradores == 0):
                self._feedback(f"Sem inimigos em [{zona_alvo}] para atacar!", C_PERIGO)
                return
            aliados_na_zona = 0
            for p in list(self.motor.combatentes):
                if getattr(p, "time", "B") == "A" and p.hp_atual > 0:
                    if obter_zona_por_coordenada(p.pos_x, p.pos_y) == zona_alvo:
                        aliados_na_zona += 1
            resultado = resolver_melee(self.estado, zona_alvo, num_dados=2, num_aliados_zona=max(1, aliados_na_zona))
            self.estado = aplicar_delta(self.estado, resultado["delta"])
            if self.estado.get("desafio_final_ativo") and self.estado.get("infiltradores", 0) == 0:
                self.estado = aplicar_delta(self.estado, {
                    "vitoria": True,
                    "msg_vitoria": "Desafio Final concluído! Os Goblins de Elite foram derrotados e os anões escaparam!"
                })
                self._push("VITORIA", "Desafio Final concluído! Vitória!")
                self.fase = "FIM"
            for t, m in resultado["logs"]:
                self._push(t, m)
            if resultado["rolagem"]:
                faces = resultado["rolagem"]["faces"]
                imp   = resultado["rolagem"]["impactos"]
                dano  = imp // 2
                self._feedback(f"Melee D6={faces} -> {imp} imp -> {dano} dano!", C_VERDE)
            self.modo_acao = MODO_NENHUM

        elif self.modo_acao == MODO_ATIRAR:
            # ── COMBATE À DISTÂNCIA / BALESTRA ───────────────────────────
            # Posição do herói determina se ele está em uma Torre
            hx = self.estado.get("heroi_x", 9)
            hy = self.estado.get("heroi_y", 9)
            zona_defensor = obter_zona_por_coordenada(hx, hy)
            zona_alvo_tiro = obter_zona_por_coordenada(cx, cy)
            if not zona_defensor or not zona_alvo_tiro:
                self._feedback("Posição inválida para Balestra!", C_PERIGO)
                return
            ok, msg_val = validar_pode_atacar_distancia(zona_defensor, zona_alvo_tiro)
            if not ok:
                self._feedback(msg_val, C_PERIGO)
                return
            resultado = resolver_distancia(self.estado, zona_defensor, zona_alvo_tiro, num_dados=2)
            self.estado = aplicar_delta(self.estado, resultado["delta"])
            for t, m in resultado["logs"]:
                self._push(t, m)
            if resultado["rolagem"]:
                faces = resultado["rolagem"]["faces"]
                dis   = resultado["rolagem"]["disparos"]
                self._feedback(f"Balestra D6={faces} -> {dis} disparos -> {dis} dano!", C_HEROI)
            self.modo_acao = MODO_NENHUM

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
        # Adiciona a carta de upgrade diretamente na mão do jogador para uso imediato
        slot = e["slots_upgrade"][self.idx_slot_upgrade]
        from ..cerco_isectum import CARTAS_UPGRADE
        carta_up = next((c for c in CARTAS_UPGRADE if c["id"] == slot.get("carta_id")), None)
        if carta_up:
            delta["mao"] = list(nova_mao) + [carta_up]
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
            # Remove a figura física do Goblin negociado no tabuleiro
            goblin_alvo = getattr(self, "alvo_negociacao", None)
            if goblin_alvo and goblin_alvo in self.motor.combatentes:
                tab = self.motor.tabuleiro
                if 0 <= goblin_alvo.pos_y < len(tab.grid) and 0 <= goblin_alvo.pos_x < len(tab.grid[0]):
                    tab.grid[goblin_alvo.pos_y][goblin_alvo.pos_x] = None
                self.motor.combatentes.remove(goblin_alvo)
                if hasattr(self.motor, 'time_b') and goblin_alvo in self.motor.time_b:
                    self.motor.time_b.remove(goblin_alvo)

            delta, logs = executar_subornar(e, recurso)
            self.estado = aplicar_delta(e, delta)
            for t, m in logs: self._push(t, m)
            self._feedback(f"Goblin negociou com sucesso!", C_VERDE)
        else:
            self._feedback(msg, C_PERIGO)
        self.modo_acao = MODO_NENHUM
        self.alvo_negociacao = None

    def _limpar_rocha_goblin(self):
        e = self.estado
        if e.get("pontos_escavacao", 0) < 4:
            self._feedback("Requer 4 Pontos de Escavação (PE)!", C_PERIGO)
            return

        # Remove o Goblin negociado da grade
        goblin_alvo = getattr(self, "alvo_negociacao", None)
        if goblin_alvo and goblin_alvo in self.motor.combatentes:
            tab = self.motor.tabuleiro
            if 0 <= goblin_alvo.pos_y < len(tab.grid) and 0 <= goblin_alvo.pos_x < len(tab.grid[0]):
                tab.grid[goblin_alvo.pos_y][goblin_alvo.pos_x] = None
            self.motor.combatentes.remove(goblin_alvo)
            if hasattr(self.motor, 'time_b') and goblin_alvo in self.motor.time_b:
                self.motor.time_b.remove(goblin_alvo)

        delta = {
            "infiltradores": max(0, e.get("infiltradores", 0) - 1),
            "pontos_escavacao": max(0, e.get("pontos_escavacao", 0) - 4),
        }
        self.estado = aplicar_delta(e, delta)
        self._push("HEROI", "⛏️ Ajudou Goblin a limpar rocha bônus (gastou 4 PE)!")
        self._feedback("Goblin negociou e saiu!", C_VERDE)
        self.modo_acao = MODO_NENHUM
        self.alvo_negociacao = None

    # ── FIM DE TURNO DO HERÓI ────────────────────────────────────────────
    def _fim_turno_heroi(self):
        # Validação: É obrigatório usar todas as cartas (incluindo as de invasão) antes de encerrar o turno
        if self.estado["mao"]:
            self._feedback("Use todas as cartas da mao para encerrar o turno!", C_PERIGO)
            try:
                self.game.play_sound('invalid_action')
            except:
                pass
            return
        
        # Reseta pontos
        self.estado = aplicar_delta(self.estado, {
            "pontos_movimento": 0,
            "pontos_trabalho":  0,
            "pontos_escavacao": 0,
        })
        # Reset acumulador de dano do Brutamonte (sobras de impacto não acumulam entre turnos)
        reset_brute = resetar_dano_turno_brutamonte(self.estado)
        if reset_brute:
            self.estado = aplicar_delta(self.estado, reset_brute)
            
        # Salva o status do herói atual
        self._salvar_status_heroi(self.heroi_atual.nome)
        
        # Registra que este herói já jogou
        jogaram = list(self.estado.get("herois_jogaram", []))
        if self.heroi_atual.nome not in jogaram:
            jogaram.append(self.heroi_atual.nome)
        self.estado = aplicar_delta(self.estado, {"herois_jogaram": jogaram})
        
        # Encontra o próximo herói que ainda não jogou
        proximo_heroi = None
        for h in self.herois:
            if h.nome not in jogaram:
                proximo_heroi = h
                break
                
        if proximo_heroi:
            # Alterna para o próximo herói aliado que ainda não jogou
            idx_novo = self.herois.index(proximo_heroi)
            self.heroi_atual_idx = idx_novo
            self._carregar_status_heroi(proximo_heroi.nome)
            
            # Novo herói compra sua nova mão
            self._comprar_mao()
            
            # Encontra a posição do novo herói no grid
            tab = self.motor.tabuleiro
            from ..resolvedor_acoes import obter_zona_por_coordenada
            for gy in range(tab.altura):
                for gx in range(tab.largura):
                    if tab.grid[gy][gx] is proximo_heroi:
                        self.estado = aplicar_delta(self.estado, {
                            "heroi_x": gx,
                            "heroi_y": gy,
                            "pos_heroi": obter_zona_por_coordenada(gx, gy) or "camara_central",
                        })
                        break
            
            nome_exibido = "?????" if proximo_heroi.nome == "Aquele" else proximo_heroi.nome
            self._feedback(f"Turno de {nome_exibido}! Use suas cartas.", C_HEROI)
            self._push("SISTEMA", f"Início do turno do herói: {nome_exibido}")
        else:
            # Todos os heróis jogaram na rodada! Reseta a lista e prossegue para a fase de ameaça
            self.estado = aplicar_delta(self.estado, {"herois_jogaram": []})
            
            # Reposição de Mercado: Se terminar na Área Central/Base ("camara_central") e houver slots vazios, entra em modo interativo
            pos_heroi = self.estado.get("pos_heroi", "camara_central")
            tem_slot_vazio = any(s.get("adquirido") or s.get("carta_id") is None for s in self.estado["slots_upgrade"])
            
            if pos_heroi == "camara_central" and tem_slot_vazio:
                self.fase = "REPOVOAR_MERCADO"
                self._feedback("Reposição: Escolha de qual deck comprar no painel lateral!", C_OURO)
                self._push("SISTEMA", "Base Central: Escolha de qual deck repovoar cada slot vazio no mercado.")
                self.alcancaveis = {}
                self.modo_acao = MODO_NENHUM
            else:
                self._concluir_fim_turno_completo()

    def _concluir_fim_turno_completo(self):
        # Descarta mão restante
        desc = list(self.estado["descarte"]) + list(self.estado["mao"])
        self.estado = aplicar_delta(self.estado, {"mao": [], "descarte": desc})
        self.alcancaveis = {}
        self.modo_acao   = MODO_NENHUM
        self._iniciar_fase_ameaca()

    def _processar_acoes_automaticas(self, mostrar_erro_se_falhar=False):
        e = self.estado
        from ..resolvedor_acoes import validar_trabalhar, executar_trabalhar, validar_escavar, executar_escavar, NOME_RECURSO
        
        # 1. Tenta trabalhar se tiver pontos de trabalho
        if e.get("pontos_trabalho", 0) > 0:
            ok, recurso, msg = validar_trabalhar(e, e["pontos_trabalho"])
            if ok:
                pts_gastos = e["pontos_trabalho"]
                delta, logs = executar_trabalhar(e, recurso, pts_gastos)
                self.estado = aplicar_delta(e, delta)
                e = self.estado
                for t, m in logs:
                    self._push(t, m)
                self._feedback(f"Trabalhou! +{pts_gastos}x {NOME_RECURSO[recurso]} produzido.", C_VERDE)
                self.modo_acao = MODO_NENHUM
            elif mostrar_erro_se_falhar:
                self._feedback(msg, C_PERIGO)
                
        # 2. Tenta escavar se tiver pontos de escavação
        if e.get("pontos_escavacao", 0) > 0:
            ok, qtd, msg = validar_escavar(e, e["pontos_escavacao"])
            if ok:
                delta, logs = executar_escavar(e, qtd)
                self.estado = aplicar_delta(e, delta)
                e = self.estado
                for t, m in logs:
                    self._push(t, m)
                self._feedback(f"Escavou! -{qtd} pedregulhos.", C_VERDE)
                self.modo_acao = MODO_NENHUM
                if self.estado.get("desafio_final_ativo") and self.estado.get("infiltradores", 0) == 0:
                    self.estado = aplicar_delta(self.estado, {
                        "vitoria": True,
                        "msg_vitoria": "Desafio Final concluído! Os Goblins de Elite foram derrotados e os anões escaparam!"
                    })
                    self._push("VITORIA", "Desafio Final concluído! Vitória!")
                    self.fase = "FIM"
            elif mostrar_erro_se_falhar:
                self._feedback(msg, C_PERIGO)
                
        # Verifica derrota imediata ao final do processamento
        self._verificar_derrota_imediata()

    def _verificar_derrota_imediata(self):
        e = self.estado
        derrota = False
        msg = ""

        if e.get("tesouro", 10) <= 0:
            derrota = True
            msg = "Todo o ouro da Câmara foi roubado! DERROTA!"
        elif e.get("reserva", 10) <= 0:
            derrota = True
            msg = "Orcs da reserva esgotados! DERROTA!"
        elif e.get("brutamontes", 0) >= 3:
            derrota = True
            msg = "3 Brutamontes/Trolls invadiram o túnel! DERROTA!"
        elif not self.deck:
            derrota = True
            msg = "O deck de Cerco de Ameaças acabou! DERROTA!"
        elif len(e.get("deck_catapulta", [1, 2, 3, 4])) <= 0:
            derrota = True
            msg = "O deck de munição de Catapulta esgotou! DERROTA!"

        if derrota:
            self.estado = aplicar_delta(self.estado, {
                "derrota": True,
                "msg_derrota": msg
            })
            self._push("DERROTA", msg)
            self.fase = "FIM"
            return True
        return False

    def _iniciar_fase_ameaca(self):
        if self._verificar_derrota_imediata():
            return
        self.fase = "FASE_AMEACA"
        self.carta_cerco = self.deck.pop()
        self._push("CARTA", f"[N{self.carta_cerco['nivel']}] {self.carta_cerco['simbolo']} "
                            f"{self.carta_cerco['titulo']}")
        self._narrativa(self.carta_cerco["tipo"])

    def _resolver_carta_cerco(self):
        e = self.estado
        # Fase A - Ativação de Máquinas: Sempre avança o ciclo das armas de cerco
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

        if self._verificar_derrota_imediata():
            return

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.fase = "FIM"
        else:
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()

    def _sincronizar_inimigos_tabuleiro(self):
        from src.resolvedor_acoes import ZONAS_GRID, obter_zona_por_coordenada
        from src.personagens.minions import Goblin, Esqueleto, Kobold, Troll
        import random

        e = self.estado
        tab = self.motor.tabuleiro

        # 1. Mapear os inimigos do time B atualmente no tabuleiro por zona
        inimigos_por_zona = {}
        for zona in ZONAS_GRID.keys():
            inimigos_por_zona[zona] = []

        for p in list(self.motor.combatentes):
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0:
                # Prioriza a flag _zona_campo se o monstro estiver em zona externa
                zona = getattr(p, "_zona_campo", None)
                if not zona:
                    zona = obter_zona_por_coordenada(p.pos_x, p.pos_y)
                if zona in inimigos_por_zona:
                    inimigos_por_zona[zona].append(p)

        # 2. Identificar excessos (de onde sairão monstros) e faltas (onde entrarão)
        excessos = [] # lista de combatentes que estão sobrando
        faltas = []   # lista de tuplas (zona, qtd_em_falta)

        for zona, (x1, y1, x2, y2) in ZONAS_GRID.items():
            esperados = e["invasores"].get(zona, 0)
            if zona == "patio":
                esperados += e.get("brutamontes", 0) + e.get("infiltradores", 0)

            atuais = inimigos_por_zona[zona]
            if len(atuais) > esperados:
                sobrando = len(atuais) - esperados
                for _ in range(sobrando):
                    if atuais:
                        excessos.append((zona, atuais.pop()))
            elif len(atuais) < esperados:
                faltas.append((zona, esperados - len(atuais)))

        # 3. Transferir combatentes em excesso para as zonas com falta (Movimento)
        faltas_atualizadas = []
        for zona_dest, qtd in faltas:
            x1, y1, x2, y2 = ZONAS_GRID[zona_dest]
            x1_c = max(0, min(19, x1))
            x2_c = max(0, min(19, x2))
            y1_c = max(0, min(19, y1))
            y2_c = max(0, min(19, y2))

            # Encontra células livres na zona de destino
            celulas_candidatas = []
            for cy in range(y1_c, y2_c + 1):
                for cx in range(x1_c, x2_c + 1):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas_candidatas.append((cx, cy))
            random.shuffle(celulas_candidatas)

            transferidos = 0
            for _ in range(qtd):
                if not celulas_candidatas:
                    break
                
                # Se tivermos combatentes em excesso em qualquer zona, transferimos um!
                if excessos:
                    zona_origem, monstro = excessos.pop(0)
                    cx, cy = celulas_candidatas.pop()
                    
                    # Salva posição antiga virtual
                    old_vx, old_vy = self._obter_posicao_virtual(monstro, monstro.pos_x, monstro.pos_y)
                    
                    # Atualiza a zona de destino no monstro
                    monstro._zona_campo = zona_dest if "campo" in zona_dest else None
                    
                    # Nova posição virtual
                    new_vx, new_vy = self._obter_posicao_virtual(monstro, cx, cy)
                    
                    # Atualiza posição real no tabuleiro
                    old_x, old_y = monstro.pos_x, monstro.pos_y
                    if 0 <= old_y < len(tab.grid) and 0 <= old_x < len(tab.grid[0]):
                        tab.grid[old_y][old_x] = None
                    tab.grid[cy][cx] = monstro
                    monstro.pos_x = cx
                    monstro.pos_y = cy
                    
                    # Dispara animação de caminhada usando posições virtuais
                    self._start_monster_walk(monstro, (old_vx, old_vy), (new_vx, new_vy))
                    transferidos += 1
                else:
                    break
            
            restante = qtd - transferidos
            if restante > 0:
                faltas_atualizadas.append((zona_dest, restante))

        # 4. Criar novos monstros para as faltas restantes (ex: spawn)
        for zona_dest, qtd in faltas_atualizadas:
            x1, y1, x2, y2 = ZONAS_GRID[zona_dest]
            x1_c = max(0, min(19, x1))
            x2_c = max(0, min(19, x2))
            y1_c = max(0, min(19, y1))
            y2_c = max(0, min(19, y2))

            celulas_candidatas = []
            for cy in range(y1_c, y2_c + 1):
                for cx in range(x1_c, x2_c + 1):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas_candidatas.append((cx, cy))

            if not celulas_candidatas:
                for cy in range(20):
                    for cx in range(20):
                        if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                            celulas_candidatas.append((cx, cy))
            random.shuffle(celulas_candidatas)

            for _ in range(qtd):
                if not celulas_candidatas:
                    break
                cx, cy = celulas_candidatas.pop()
                
                # Saca o tipo do inimigo do deck de inimigos (reembaralhando se estiver vazio)
                deck_ini = list(self.estado.get("deck_inimigos", []))
                desc_ini = list(self.estado.get("descarte_inimigos", []))
                if not deck_ini:
                    if desc_ini:
                        deck_ini = list(desc_ini)
                        random.shuffle(deck_ini)
                        desc_ini = []
                    else:
                        deck_ini = ["goblin", "esqueleto", "kobold"]
                        random.shuffle(deck_ini)
                carta_ini = deck_ini.pop()
                desc_ini.append(carta_ini)
                self.estado = aplicar_delta(self.estado, {
                    "deck_inimigos": deck_ini,
                    "descarte_inimigos": desc_ini
                })
                
                mapa_classes = {
                    "goblin": Goblin,
                    "esqueleto": Esqueleto,
                    "kobold": Kobold
                }
                classe_inimigo = mapa_classes.get(carta_ini, Goblin)
                nome_inimigo = f"Inseto {classe_inimigo.__name__}"
                is_infiltrador = False
                
                if zona_dest == "patio":
                    trolls_atuais = sum(1 for p in self.motor.combatentes if getattr(p, "classe_nome", None) == "Troll" and p.hp_atual > 0)
                    goblins_atuais = sum(1 for p in self.motor.combatentes if getattr(p, "classe_nome", None) == "Goblin" and p.hp_atual > 0 and getattr(p, "_is_infiltrador", False))
                    
                    if trolls_atuais < e.get("brutamontes", 0):
                        classe_inimigo = Troll
                        nome_inimigo = "Troll"
                    elif goblins_atuais < e.get("infiltradores", 0):
                        classe_inimigo = Goblin
                        nome_inimigo = "Goblin Infiltrador"
                        is_infiltrador = True
                
                inimigo = classe_inimigo(nome_inimigo, "B", nivel=3)
                if is_infiltrador:
                    inimigo._is_infiltrador = True
                
                sucesso = tab.adicionar_personagem(inimigo, cx, cy)
                if sucesso:
                    self.motor.combatentes.append(inimigo)
                    if not hasattr(self.motor, 'time_b'):
                        self.motor.time_b = []
                    self.motor.time_b.append(inimigo)
                    
                    # Rastreia que a zona de spawn é externa
                    inimigo._zona_campo = zona_dest if "campo" in zona_dest else None
                    
                    # Define a posição virtual final
                    new_vx, new_vy = self._obter_posicao_virtual(inimigo, cx, cy)
                    
                    # Efeito de invasão: surge fora da borda virtual
                    origem_x, origem_y = new_vx, new_vy
                    if "campo" in zona_dest:
                        if "norte" in zona_dest:
                            origem_y = -4
                        elif "sul" in zona_dest:
                            origem_y = 23
                        elif "oeste" in zona_dest:
                            origem_x = -4
                        elif "leste" in zona_dest:
                            origem_x = 23
                    else:
                        # Se spawnar direto nas muralhas, vem de fora
                        if "norte" in zona_dest:
                            origem_y = -2
                        elif "sul" in zona_dest:
                            origem_y = 21
                        elif "oeste" in zona_dest:
                            origem_x = -2
                        elif "leste" in zona_dest:
                            origem_x = 21
                    
                    if (origem_x, origem_y) != (new_vx, new_vy):
                        self._start_monster_walk(inimigo, (origem_x, origem_y), (new_vx, new_vy))

        # 5. Remover monstros que restaram em excesso (ex: mortos ou roubaram tesouro)
        for zona_origem, monstro in excessos:
            if 0 <= monstro.pos_y < len(tab.grid) and 0 <= monstro.pos_x < len(tab.grid[0]):
                tab.grid[monstro.pos_y][monstro.pos_x] = None
            if monstro in self.motor.combatentes:
                self.motor.combatentes.remove(monstro)
            if hasattr(self.motor, 'time_b') and monstro in self.motor.time_b:
                self.motor.time_b.remove(monstro)

    # ═══════════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════════
    def update(self):
        # Depuração: imprime a lista de monstros time B e suas flags
        time_b_debug = [p for p in self.motor.combatentes if getattr(p, "time", "A") == "B"]
        if time_b_debug and random.random() < 0.05: # Imprime ocasionalmente (~1 em cada 20 frames) para não inundar o console
            print("--- STATUS DOS INIMIGOS ---")
            for p in time_b_debug:
                print(f"  {p.nome}: pos=({p.pos_x}, {p.pos_y}) | _zona_campo={getattr(p, '_zona_campo', None)}")
        
        # Sincroniza inimigos se o estado de invasores mudou
        e = self.estado
        c_invasores = dict(e["invasores"])
        c_invasores["_brutamontes"] = e.get("brutamontes", 0)
        if not hasattr(self, "_ultimo_estado_invasores") or self._ultimo_estado_invasores != c_invasores:
            self._ultimo_estado_invasores = c_invasores
            self._sincronizar_inimigos_tabuleiro()

        self.timer = (self.timer + 1) % 120
        self._update_walk()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        # Sincroniza rotação com o motor do tabuleiro
        self.motor.angulo_rotacao = self.game.angulo_rotacao

        # Invalida o backbuffer se a rotação ou o zoom mudarem para poupar CPU
        ang = self.game.angulo_rotacao
        zm = self.zoom
        if not hasattr(self, '_ultimo_angulo') or self._ultimo_angulo != ang:
            self._ultimo_angulo = ang
            self.map_backbuffer_sujo = True
        if not hasattr(self, '_ultimo_zoom') or self._ultimo_zoom != zm:
            self._ultimo_zoom = zm
            self.map_backbuffer_sujo = True

        # Atualiza a animação de comprar cartas
        if hasattr(self, 'animacoes_cartas_compra') and self.animacoes_cartas_compra:
            for anim in self.animacoes_cartas_compra:
                if anim.get('finalizada', False):
                    continue
                if anim.get('delay', 0) > 0:
                    anim['delay'] -= 1
                    continue
                anim['progresso'] += 0.05  # progresso a 5% por frame (~20 frames = ~330ms de voo)
                if anim['progresso'] >= 1.0:
                    anim['progresso'] = 1.0
                    anim['finalizada'] = True

    # ═══════════════════════════════════════════════════════════════════
    # DRAW
    # ═══════════════════════════════════════════════════════════════════
    def draw(self, tela):
        self._setup_layout()
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

        if self.fase == "ESCOLHER_ACAO_CARTA":
            self._draw_modal_escolha_carta(tela, W, H)

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

        # ── Barra de Iniciativa Visual (Cabeçalho Central) ──────────────────
        bx = W // 2 - 150
        by = 8
        bw = 300
        bh = 32
        
        # Desenha trilha de fundo
        pygame.draw.rect(tela, (14, 16, 30), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(tela, C_BORDA, (bx, by, bw, bh), 1, border_radius=6)
        
        # Desenhamos os avatares dos heróis na trilha
        av_size = 22
        for idx, h in enumerate(self.herois):
            hx = bx + 8 + idx * (av_size + 14)
            hy = by + (bh - av_size) // 2
            
            # Moldura do herói
            h_rect = pygame.Rect(hx, hy, av_size, av_size)
            eh_ativo = (h is self.heroi_atual)
            
            # Se for o herói ativo e for a fase do jogador, destaca
            destaque = eh_ativo and (self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"))
            cor_b = C_VERDE if destaque else (C_ACENTO if eh_ativo else C_BORDA)
            
            pygame.draw.rect(tela, (8, 8, 16), h_rect, border_radius=3)
            
            if h.nome == "Aquele":
                fallback = self.fMi.render("🌑", True, C_TEXTO)
                tela.blit(fallback, (h_rect.centerx - fallback.get_width() // 2, h_rect.centery - fallback.get_height() // 2))
            else:
                img_key = f"personagem_{h.nome.lower()}"
                img = self.game.imagens.get(img_key)
                if img:
                    img_scaled = pygame.transform.scale(img, (av_size - 2, av_size - 2))
                    tela.blit(img_scaled, (h_rect.x + 1, h_rect.y + 1))
                else:
                    # Fallback inicial do herói
                    fallback = self.fMi.render(h.nome[0], True, C_TEXTO)
                    tela.blit(fallback, (h_rect.centerx - fallback.get_width() // 2, h_rect.centery - fallback.get_height() // 2))
                
            pygame.draw.rect(tela, cor_b, h_rect, 2 if destaque else 1, border_radius=3)
            
            # Efeito pulsar no ativo
            if destaque:
                pulse = abs(self.timer % 60 - 30) / 30.0
                rp = int(2 + 2 * pulse)
                pygame.draw.rect(tela, C_VERDE, h_rect.inflate(rp, rp), 1, border_radius=3)

        # Ícone de Ameaça/Invasores no fim da trilha
        ax = bx + bw - 30
        ay = by + (bh - av_size) // 2
        a_rect = pygame.Rect(ax, ay, av_size, av_size)
        
        eh_ameaca = (self.fase == "FASE_AMEACA")
        cor_a = C_PERIGO if eh_ameaca else C_DIM
        pygame.draw.rect(tela, (20, 10, 10) if eh_ameaca else (10, 12, 16), a_rect, border_radius=3)
        pygame.draw.rect(tela, cor_a, a_rect, 2 if eh_ameaca else 1, border_radius=3)
        
        # Desenha uma caveira simplificada com círculos
        pygame.draw.circle(tela, cor_a, (a_rect.centerx, a_rect.centery - 2), 4)
        pygame.draw.rect(tela, cor_a, (a_rect.centerx - 3, a_rect.centery + 1, 6, 4))
        pygame.draw.circle(tela, (0, 0, 0), (a_rect.centerx - 2, a_rect.centery - 2), 1)
        pygame.draw.circle(tela, (0, 0, 0), (a_rect.centerx + 2, a_rect.centery - 2), 1)
        
        if eh_ameaca:
            pulse = abs(self.timer % 60 - 30) / 30.0
            rp = int(2 + 2 * pulse)
            pygame.draw.rect(tela, C_PERIGO, a_rect.inflate(rp, rp), 1, border_radius=3)
            
        # Seta indicando o fluxo (Heróis -> Invasores)
        seta_x = bx + bw - 52
        seta_y = by + bh // 2
        pygame.draw.line(tela, C_DIM, (seta_x - 5, seta_y), (seta_x + 5, seta_y), 1)
        pygame.draw.line(tela, C_DIM, (seta_x + 5, seta_y), (seta_x + 1, seta_y - 3), 1)
        pygame.draw.line(tela, C_DIM, (seta_x + 5, seta_y), (seta_x + 1, seta_y + 3), 1)

        fase_label = {
            "JOGAR_CARTA": "Jogue Cartas",
            "ACAO_LIVRE":  "Execute Ações",
            "FASE_AMEACA": "Fase de Ameaça",
            "FIM":         "Fim",
        }
        
        rod_txt = f"RODADA {self.estado['rodada']}  |  {fase_label.get(self.fase, '').upper()}"
        fc = C_VERDE if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE") else C_PERIGO
        lbl_rod = self.fMi.render(rod_txt, True, fc if self.fase == "FASE_AMEACA" else C_DIM)
        tela.blit(lbl_rod, (W // 2 - lbl_rod.get_width() // 2, by + bh + 4))

        # Stats rápidas
        e = self.estado
        info = [
            (f"Ouro:{e['tesouro']}", C_OURO),
            (f"Res:{e['reserva']}", C_INVASOR),
            (f"Esc:{e['pedregulhos']}", (120, 160, 255)),
            (f"PM:{e['pontos_movimento']}", C_HEROI),
            (f"PT:{e['pontos_trabalho']}", C_VERDE),
            (f"PE:{e['pontos_escavacao']}", C_CERCO),
        ]
        x = W - 14
        for txt, cor in reversed(info):
            s = self.fMi.render(txt, True, cor)
            x -= s.get_width() + 14
            tela.blit(s, (x, 20))

        # Herói atual
        nome_exibido = "?????" if (self.heroi_atual and self.heroi_atual.nome == "Aquele") else (self.heroi_atual.nome if self.heroi_atual else "?")
        if len(self.herois) > 1:
            heroi_info = f"Heroi: {nome_exibido} [{self.heroi_atual_idx + 1}/{len(self.herois)}]  [TAB]"
        else:
            heroi_info = f"Heroi: {nome_exibido}"
        ph = self.fMi.render(heroi_info, True, C_HEROI)
        tela.blit(ph, (14, 46))

        # Botão voltar
        m = pygame.mouse.get_pos()
        hover = self.btn_voltar.collidepoint(m)
        bc = (48, 48, 72) if hover else (24, 24, 42)
        pygame.draw.rect(tela, bc, self.btn_voltar, border_radius=6)
        pygame.draw.rect(tela, C_BORDA if hover else (30, 30, 50), self.btn_voltar, 1, border_radius=6)
        vt = self.fMi.render("< MENU [ESC]", True, C_TEXTO if hover else C_DIM)
        tela.blit(vt, (self.btn_voltar.centerx - vt.get_width() // 2, self.btn_voltar.centery - vt.get_height() // 2))

    # ── MAPA ────────────────────────────────────────────────────────────
    def _draw_mapa(self, tela):
        r = self.mapa_rect
        
        # ── Constantes isométricas (escaladas pelo zoom) ─────────────
        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        CX = r.centerx
        CY = r.centery - 5
        theta = self.game.angulo_rotacao
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)

        RENDER_MIN = -5
        RENDER_MAX = 24
        GRID_MIN, GRID_MAX = 0, 19

        ELEV_ZONA = {
            "camara_central": 3, "curtume": 2, "carpintaria": 2, "fundicao": 2,
            "patio": 2, "muralha_norte": 4, "muralha_sul": 4, "muralha_oeste": 4, "muralha_leste": 4,
            "torre_nw": 6, "torre_ne": 6, "torre_sw": 6, "torre_se": 6, "_corredor": 1, "_campo": 0, "_exterior": 0
        }

        PALETA = {
            "camara_central": ((105, 82, 18),  (72, 55, 10),  (52, 38, 6)),
            "curtume":        ((120, 72, 28),  (82, 48, 16),  (60, 34, 10)),
            "carpintaria":    ((32, 90, 28),   (20, 60, 16),  (14, 44, 10)),
            "fundicao":       ((70, 70, 88),   (46, 46, 62),  (32, 32, 46)),
            "patio":          ((28, 60, 120),  (18, 40, 82),  (12, 28, 60)),
            "muralha_norte":  ((90, 92, 108),  (62, 64, 78),  (44, 46, 58)),
            "muralha_sul":    ((90, 92, 108),  (62, 64, 78),  (44, 46, 58)),
            "muralha_oeste":  ((90, 92, 108),  (62, 64, 78),  (44, 46, 58)),
            "muralha_leste":  ((90, 92, 108),  (62, 64, 78),  (44, 46, 58)),
            "torre_nw":       ((70, 72, 92),   (45, 46, 64),  (30, 32, 48)),
            "torre_ne":       ((70, 72, 92),   (45, 46, 64),  (30, 32, 48)),
            "torre_sw":       ((70, 72, 92),   (45, 46, 64),  (30, 32, 48)),
            "torre_se":       ((70, 72, 92),   (45, 46, 64),  (30, 32, 48)),
            "_corredor":      ((36, 34, 28),   (24, 22, 18),  (18, 16, 13)),
            "_campo":         ((30, 52, 22),   (20, 34, 14),  (14, 24, 10)),
            "_exterior":      ((18, 28, 12),   (12, 18, 8),   (8,  12, 5)),
        }

        from src.resolvedor_acoes import obter_zona_por_coordenada as _oz

        def _classificar(gx, gy):
            if GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                z = _oz(gx, gy)
                if z: return z, ELEV_ZONA.get(z, 1)
                if 4 <= gx <= 15 and 4 <= gy <= 15: return "_corredor", 1
                return None, 0
            dist_from_wall = max(max(0, GRID_MIN - gx, gx - GRID_MAX), max(0, GRID_MIN - gy, gy - GRID_MAX))
            if dist_from_wall <= 4: return "_campo", 0
            return "_exterior", 0

        # Rancheia as células por profundidade isométrica
        cells = []
        for gy in range(RENDER_MIN, RENDER_MAX + 1):
            for gx in range(RENDER_MIN, RENDER_MAX + 1):
                zona_key, el = _classificar(gx, gy)
                if zona_key is None: continue
                dx = gx - 9.5
                dy = gy - 9.5
                rx = dx * theta_cos - dy * theta_sin
                ry = dx * theta_sin + dy * theta_cos
                ground_depth = rx + ry
                cy_coord = (rx + ry) * (TH // 2) - el * ES
                cells.append((ground_depth, cy_coord, gx, gy, zona_key, el, rx, ry))
        cells.sort(key=lambda x: x[0])

        # Se o backbuffer não existe ou está sujo, nós o redesenhamos
        if getattr(self, 'map_backbuffer', None) is None or getattr(self, 'map_backbuffer_sujo', True):
            self.map_backbuffer = pygame.Surface((r.width, r.height))
            self.map_backbuffer.fill((10, 12, 22))

            # Céu Estrelado Noturno
            bg_sky = pygame.Surface((2, 2))
            bg_sky.set_at((0, 0), (6, 10, 26))
            bg_sky.set_at((1, 0), (6, 10, 26))
            bg_sky.set_at((0, 1), (18, 10, 24))
            bg_sky.set_at((1, 1), (18, 10, 24))
            bg_sky_scaled = pygame.transform.smoothscale(bg_sky, (r.width, r.height))
            self.map_backbuffer.blit(bg_sky_scaled, (0, 0))

            # Estrelas
            import random
            random.seed(1337)
            for _ in range(40):
                sx = random.randint(10, r.width - 10)
                sy = random.randint(10, r.height - 10)
                if sy < r.height * 0.4:
                    pygame.draw.circle(self.map_backbuffer, (180, 180, 210), (sx, sy), 1)

            # Névoa
            fog = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            pygame.draw.ellipse(fog, (40, 50, 80, 40), (0, r.height - 120, r.width, 140))
            pygame.draw.ellipse(fog, (20, 30, 60, 30), (-50, r.height - 80, r.width + 100, 100))
            self.map_backbuffer.blit(fog, (0, 0))

            # Moldura externa local
            local_r = pygame.Rect(0, 0, r.width, r.height)
            pygame.draw.rect(self.map_backbuffer, C_BORDA, local_r, 1, border_radius=12)
            d = 12
            for cx, cy in [(local_r.left, local_r.top), (local_r.right, local_r.top), (local_r.left, local_r.bottom), (local_r.right, local_r.bottom)]:
                x_dir = 1 if cx == local_r.left else -1
                y_dir = 1 if cy == local_r.top else -1
                pygame.draw.line(self.map_backbuffer, C_OURO, (cx, cy), (cx + d * x_dir, cy), 2)
                pygame.draw.line(self.map_backbuffer, C_OURO, (cx, cy), (cx, cy + d * y_dir), 2)

            # Desenha relevo e terrenos locais
            CX_local = r.width // 2
            CY_local = r.height // 2 - 5

            def _losango_local(cx_, cy_):
                return [
                    (cx_,           cy_ - TH // 2),
                    (cx_ + TW // 2, cy_),
                    (cx_,           cy_ + TH // 2),
                    (cx_ - TW // 2, cy_),
                ]

            for ground_depth, cy_coord, gx, gy, zona_key, el, rx, ry in cells:
                paleta = PALETA.get(zona_key, PALETA["_exterior"])
                _, cor_left, cor_right = paleta

                cx_ = int((rx - ry) * (TW // 2) + CX_local)
                cy_ = int(cy_coord + CY_local)

                if not local_r.inflate(TW + 4, TH + 4).collidepoint(cx_, cy_):
                    continue

                top_pts = _losango_local(cx_, cy_)
                thick = el * ES

                if thick > 0:
                    left_pts = [
                        (cx_ - TW // 2, cy_),
                        (cx_,           cy_ + TH // 2),
                        (cx_,           cy_ + TH // 2 + thick),
                        (cx_ - TW // 2, cy_ + thick),
                    ]
                    right_pts = [
                        (cx_,           cy_ + TH // 2),
                        (cx_ + TW // 2, cy_),
                        (cx_ + TW // 2, cy_ + thick),
                        (cx_,           cy_ + TH // 2 + thick),
                    ]
                    pygame.draw.polygon(self.map_backbuffer, cor_left,  left_pts)
                    pygame.draw.polygon(self.map_backbuffer, cor_right, right_pts)

                    # Tijolos procedurais nas paredes
                    h_step = max(5, int(8 * self.zoom))
                    c_mortar_l = (max(0, cor_left[0] - 35),  max(0, cor_left[1] - 35),  max(0, cor_left[2] - 35))
                    c_mortar_r = (max(0, cor_right[0] - 35), max(0, cor_right[1] - 35), max(0, cor_right[2] - 35))

                    for h in range(h_step, thick, h_step):
                        pygame.draw.line(self.map_backbuffer, c_mortar_l, (cx_ - TW // 2, cy_ + h), (cx_, cy_ + TH // 2 + h), 1)
                        pygame.draw.line(self.map_backbuffer, c_mortar_r, (cx_, cy_ + TH // 2 + h), (cx_ + TW // 2, cy_ + h), 1)

                    row_idx = 0
                    for h in range(0, thick, h_step):
                        j_h = min(h_step, thick - h)
                        if j_h <= 2: continue
                        fractions = [0.5] if row_idx % 2 == 0 else [0.25, 0.75]

                        for f in fractions:
                            jx = cx_ - TW // 2 + int(f * (TW // 2))
                            jy = cy_ + int(f * (TH // 2)) + h
                            pygame.draw.line(self.map_backbuffer, c_mortar_l, (jx, jy), (jx, jy + j_h), 1)

                        for f in fractions:
                            jx = cx_ + int(f * (TW // 2))
                            jy = cy_ + TH // 2 - int(f * (TH // 2)) + h
                            pygame.draw.line(self.map_backbuffer, c_mortar_r, (jx, jy), (jx, jy + j_h), 1)

                        row_idx += 1

                    pygame.draw.polygon(self.map_backbuffer, (15, 15, 20), left_pts, 1)
                    pygame.draw.polygon(self.map_backbuffer, (15, 15, 20), right_pts, 1)

                eh_muralha_torre = zona_key and ("muralha" in zona_key or "torre" in zona_key)
                usar_sprite = self.game.sprites_visiveis or eh_muralha_torre
                tex = self._tex(zona_key, TW, TH) if usar_sprite else None
                if tex:
                    self.map_backbuffer.blit(tex, (cx_ - TW // 2, cy_ - TH // 2))
                else:
                    cor_top = paleta[0]
                    pygame.draw.polygon(self.map_backbuffer, cor_top, top_pts)

                ZONA_CONTORNOS = {
                    "camara_central": (235, 195, 30),  # Dourado (Ouro)
                    "curtume":        (220, 120, 40),  # Âmbar/Laranja (Couro)
                    "carpintaria":    (60, 200, 60),   # Verde (Madeira)
                    "fundicao":       (120, 180, 240), # Azul/Cinza (Metal)
                    "patio":          (60, 160, 240)   # Ciano (Pedra)
                }
                cor_borda = (10, 12, 20)
                espessura = 1
                if zona_key in ZONA_CONTORNOS:
                    cor_borda = ZONA_CONTORNOS[zona_key]
                    espessura = 2
                pygame.draw.polygon(self.map_backbuffer, cor_borda, top_pts, espessura)

            self.map_backbuffer_sujo = False

        # Blita o buffer de terreno pronto na tela do jogo
        tela.blit(self.map_backbuffer, (r.x, r.y))

        # Renderização dinâmica e móvel por cima (Destaques, Personagens e Rótulos)
        labels_pendentes = {}
        ZONA_LABELS = {
            "camara_central": ("CAMARA CENTRAL (OURO)", C_OURO),
            "curtume":        ("CURTUME (COURO)",   (215, 165, 85)),
            "carpintaria":    ("CARPINTARIA (MADEIRA)", (85, 205, 85)),
            "fundicao":       ("FUNDICAO (METAL)",   (185, 185, 205)),
            "patio":          ("PATIO (PEDREGULHOS)",   (105, 165, 255)),
            "muralha_norte":  ("MURALHA NORTE",  C_DIM),
            "muralha_sul":    ("MURALHA SUL",    C_DIM),
            "muralha_oeste":  ("MURALHA OESTE",  C_DIM),
            "muralha_leste":  ("MURALHA LESTE",  C_DIM),
            "torre_nw":       ("TORRE NW",    (180, 180, 220)),
            "torre_ne":       ("TORRE NE",    (180, 180, 220)),
            "torre_sw":       ("TORRE SW",    (180, 180, 220)),
            "torre_se":       ("TORRE SE",    (180, 180, 220))
        }

        def _iso(gx, gy, el):
            dx = gx - 9.5
            dy = gy - 9.5
            rx = dx * theta_cos - dy * theta_sin
            ry = dx * theta_sin + dy * theta_cos
            sx = (rx - ry) * (TW // 2) + CX
            sy = (rx + ry) * (TH // 2) - el * ES + CY
            return int(sx), int(sy)

        def _losango(cx_, cy_):
            return [
                (cx_,           cy_ - TH // 2),
                (cx_ + TW // 2, cy_),
                (cx_,           cy_ + TH // 2),
                (cx_ - TW // 2, cy_),
            ]

        def _campo_direcao(gx, gy):
            if gy < GRID_MIN:   return "campo_norte"
            if gy > GRID_MAX:   return "campo_sul"
            if gx < GRID_MIN:   return "campo_oeste"
            if gx > GRID_MAX:   return "campo_leste"
            return None

        tab = self.motor.tabuleiro
        e = self.estado

        for ground_depth, cy_coord, gx, gy, zona_key, el, rx, ry in cells:
            cx_ = int((rx - ry) * (TW // 2) + CX)
            cy_ = int(cy_coord + CY)

            if not r.inflate(TW + 4, TH + 4).collidepoint(cx_, cy_):
                continue

            top_pts = _losango(cx_, cy_)

            # Destaques dinâmicos de hover e movimento
            mx_draw, my_draw = pygame.mouse.get_pos()
            dx_ = abs(mx_draw - cx_) / (TW / 2 + 0.001)
            dy_ = abs(my_draw - cy_) / (TH / 2 + 0.001)
            is_hover = (dx_ + dy_ <= 1.0) and r.collidepoint(mx_draw, my_draw)
            is_move_hl = self.modo_acao == MODO_MOVER and (gx, gy) in self.alcancaveis
            campo_dir = _campo_direcao(gx, gy)

            if is_hover:
                self._draw_alpha_polygon(tela, (255, 255, 255, 30), top_pts)
                pygame.draw.polygon(tela, (255, 255, 255), top_pts, 1)

            if is_move_hl:
                self._draw_celula_tactica(tela, cx_, cy_, TW, TH, (0, 150, 0, 45), (100, 255, 100), estilo='movimento')

            if campo_dir and zona_key == "_campo":
                inv_campo = e.get(campo_dir, 0)
                if inv_campo > 0:
                    pulso = abs((self.timer % 90) - 45) / 45.0
                    self._draw_celula_tactica(tela, cx_, cy_, TW, TH, (255, 0, 0, int(35 + 25 * pulso)), (255, 50, 50), estilo='ataque')

            # Coleta pontos de label para desenhar depois do loop
            if zona_key not in labels_pendentes and zona_key in ZONA_LABELS:
                from src.resolvedor_acoes import ZONAS_GRID as _ZG
                if zona_key in _ZG:
                    x1, y1, x2, y2 = _ZG[zona_key]
                    mid_gx = (x1 + x2) // 2
                    mid_gy = (y1 + y2) // 2
                    _, mid_el = _classificar(mid_gx, mid_gy)
                    mcx, mcy = _iso(mid_gx, mid_gy, mid_el)
                    labels_pendentes[zona_key] = (mcx, mcy)

            # Personagens
            if GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                char = tab.grid[gy][gx]
                if char:
                    # Ajuste de coordenadas se estiver nos campos externos
                    vgx, vgy, vel = gx, gy, el
                    if getattr(char, "_zona_campo", None):
                        zc = char._zona_campo
                        vel = 0
                        if zc == "campo_norte":
                            vgy = -2
                        elif zc == "campo_sul":
                            vgy = 21
                        elif zc == "campo_oeste":
                            vgx = -2
                        elif zc == "campo_leste":
                            vgx = 21
                        # Recalcula default_cx e default_cy baseados na posição virtual
                        default_cx, default_cy = _iso(vgx, vgy, vel)
                    else:
                        default_cx, default_cy = cx_, cy_

                    from src.ui.render_combate import desenhar_sprite
                    sw, sh = max(10, int(24 * self.zoom)), max(10, int(24 * self.zoom))
                    cx_draw, cy_draw = self._get_char_screen_pos(char, vgx, vgy, vel, default_cx, default_cy)
                    rect_char = pygame.Rect(cx_draw - sw // 2, cy_draw - sh + 2, sw, sh)
                    eh_atual = char is self.heroi_atual
                    cor_char = (100, 215, 255) if eh_atual else (200, 180, 255)
                    desenhar_sprite(tela, char, rect_char, cor_char, self.game.imagens, self.game.sprites_visiveis)
                    
                    # Desenha círculos de vida individuais do Troll (Brutamonte)
                    if char.nome == "Troll" or getattr(char, "classe_nome", None) == "Troll":
                        trolls_no_tabuleiro = [p for p in self.motor.combatentes if getattr(p, "classe_nome", None) == "Troll" and p.hp_atual > 0]
                        circulos_marcados = 0
                        if trolls_no_tabuleiro and trolls_no_tabuleiro[0] is char:
                            circulos_marcados = e.get("brutamonte_hp", {}).get("circulos_marcados", 0)
                        
                        circle_y = cy_draw - int(24 * self.zoom)
                        circle_x_start = cx_draw - int(10 * self.zoom)
                        for c_idx in range(3):
                            c_x = circle_x_start + c_idx * int(10 * self.zoom)
                            c_color = (255, 50, 50) if c_idx < circulos_marcados else (50, 200, 50)
                            pygame.draw.circle(tela, c_color, (c_x, circle_y), int(3 * self.zoom))
                            pygame.draw.circle(tela, (20, 20, 20), (c_x, circle_y), int(3 * self.zoom), 1)

                    if eh_atual:
                        pulse = abs(self.timer % 120 - 60) / 60.0
                        pulse_r = max(2, int((4 + 3 * pulse) * self.zoom))
                        pygame.draw.circle(tela, (120, 220, 255), (cx_draw, cy_draw), pulse_r, max(1, int(2 * self.zoom)))
                    nome_exibido = "?????" if char.nome == "Aquele" else char.nome
                    nome_s = self.fMi.render(nome_exibido, True, C_TEXTO)
                    if self.zoom != 1.0:
                        nome_s = pygame.transform.scale(nome_s,
                            (max(1, int(nome_s.get_width() * self.zoom)),
                             max(1, int(nome_s.get_height() * self.zoom))))
                    tela.blit(nome_s, (cx_draw - nome_s.get_width() // 2, cy_draw - int(32 * self.zoom)))




        # ── Informações Dinâmicas sobre Zonas (Super Minimalista) ────────────────
        e = self.estado
        for zona_key, (lcx, lcy) in labels_pendentes.items():
            # Y inicial centralizado
            y_off = lcy - int(8 * self.zoom)

            # 2. Informações Dinâmicas (Invasores)
            inv = e["invasores"].get(zona_key, 0)
            if inv > 0:
                li = self.fP.render(f"INV: {inv}", True, C_INVASOR)
                if self.zoom != 1.0:
                    li = pygame.transform.scale(li,
                        (max(1, int(li.get_width() * self.zoom)),
                         max(1, int(li.get_height() * self.zoom))))
                
                li_rect = li.get_rect(center=(lcx, y_off))
                li_rect.inflate_ip(4, 2)
                pygame.draw.rect(tela, (30, 10, 10, 180), li_rect, border_radius=3)
                tela.blit(li, li_rect)
                y_off += int(15 * self.zoom)

            # 3. Informações Específicas por Zona
            if zona_key == "camara_central":
                lt = self.fP.render(f"OURO: {e['tesouro']}", True, C_OURO)
                if self.zoom != 1.0:
                    lt = pygame.transform.scale(lt,
                        (max(1, int(lt.get_width() * self.zoom)),
                         max(1, int(lt.get_height() * self.zoom))))
                
                lt_rect = lt.get_rect(center=(lcx, y_off))
                lt_rect.inflate_ip(4, 2)
                pygame.draw.rect(tela, (25, 20, 10, 180), lt_rect, border_radius=3)
                tela.blit(lt, lt_rect)

            elif zona_key == "patio":
                gap = max(8, int(13 * self.zoom))
                if e["brutamontes"] > 0:
                    hp_dat = e.get("brutamonte_hp", {})
                    circ_tot  = hp_dat.get("circulos_total", 3)
                    circ_marc = hp_dat.get("circulos_marcados", 0)
                    lb = self.fMi.render(f"Brute x{e['brutamontes']}", True, C_BRUTE)
                    if self.zoom != 1.0:
                        lb = pygame.transform.scale(lb,
                            (max(1, int(lb.get_width() * self.zoom)),
                             max(1, int(lb.get_height() * self.zoom))))
                    tela.blit(lb, (lcx - lb.get_width() // 2, y_off)); y_off += gap
                    
                    circ_txt = "o" * (circ_tot - circ_marc) + "x" * circ_marc
                    lhp = self.fMi.render(circ_txt, True, C_PERIGO)
                    if self.zoom != 1.0:
                        lhp = pygame.transform.scale(lhp,
                            (max(1, int(lhp.get_width() * self.zoom)),
                             max(1, int(lhp.get_height() * self.zoom))))
                    tela.blit(lhp, (lcx - lhp.get_width() // 2, y_off)); y_off += gap
                    
                if e.get("infiltradores", 0) > 0:
                    lif = self.fMi.render(f"Inf x{e['infiltradores']}", True, C_CERCO)
                    if self.zoom != 1.0:
                        lif = pygame.transform.scale(lif,
                            (max(1, int(lif.get_width() * self.zoom)),
                             max(1, int(lif.get_height() * self.zoom))))
                    tela.blit(lif, (lcx - lif.get_width() // 2, y_off)); y_off += gap
                    
                lp = self.fMi.render(f"PEDRA: {e['pedregulhos']}", True, (120, 160, 255))
                if self.zoom != 1.0:
                    lp = pygame.transform.scale(lp,
                        (max(1, int(lp.get_width() * self.zoom)),
                         max(1, int(lp.get_height() * self.zoom))))
                
                lp_rect = lp.get_rect(center=(lcx, y_off))
                lp_rect.inflate_ip(4, 2)
                pygame.draw.rect(tela, (15, 20, 30, 180), lp_rect, border_radius=3)
                tela.blit(lp, lp_rect)

        # ── Armas de cerco e narrativa ───────────────────────────────────────
        self._draw_armas_cerco(tela)
        nr = self.fMi.render(self.narrativa[:88], True, C_DIM)
        tela.blit(nr, (r.x + 8, r.bottom - 18))


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

        # ── Recursos depositados (Design de Slots de Inventário) ─────────
        dep = self.estado.get("recursos_depositados", {})
        yt = y + 8
        tt = self.fMi.render("RECURSOS DEPOSITADOS", True, C_ACENTO)
        tela.blit(tt, (x + pw // 2 - tt.get_width() // 2, yt)); yt += 18
        
        res_info = [
            ("MAD", "madeira", (120, 200, 100)),
            ("COU", "couro",   (200, 150,  80)),
            ("MET", "metal",   (180, 180, 220))
        ]
        
        slot_w = (pw - 24) // 3
        rx = x + 8
        for label, key, cor in res_info:
            s_rect = pygame.Rect(rx, yt, slot_w, 36)
            pygame.draw.rect(tela, (18, 20, 32), s_rect, border_radius=4)
            pygame.draw.rect(tela, C_BORDA, s_rect, 1, border_radius=4)
            
            lbl = self.fMi.render(label, True, C_DIM)
            tela.blit(lbl, (s_rect.centerx - lbl.get_width() // 2, s_rect.y + 4))
            
            val = self.fP.render(str(dep.get(key, 0)), True, cor)
            tela.blit(val, (s_rect.centerx - val.get_width() // 2, s_rect.y + 16))
            
            rx += slot_w + 4
        yt += 42
        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

        # ── Mercado de Upgrades ──────────────────────────────────────────
        ut = self.fMi.render("MERCADO DE MELHORIAS", True, C_ACENTO)
        tela.blit(ut, (x + pw // 2 - ut.get_width() // 2, yt)); yt += 18

        self._slot_y_start = yt
        for slot in self.estado["slots_upgrade"]:
            sr = pygame.Rect(x + 6, yt, pw - 12, 38)
            self._slot_rects_cache[slot["id"]] = sr

            is_slot_vazio = slot.get("adquirido") or slot.get("carta_id") is None

            if self.fase == "REPOVOAR_MERCADO":
                if is_slot_vazio:
                    # Slot vazio! Desenhar os 3 botões de compra: [Amarelo], [Cinza], [Vermelho]
                    pygame.draw.rect(tela, (20, 20, 26), sr, border_radius=5)
                    pygame.draw.rect(tela, C_BORDA, sr, 1, border_radius=5)

                    btn_w = (sr.width - 16) // 3
                    
                    # Botão Amarelo
                    b_amarelo = pygame.Rect(sr.x + 4, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (70, 60, 10), b_amarelo, border_radius=4)
                    lbl_a = self.fMi.render("Amarelo", True, (255, 230, 120))
                    tela.blit(lbl_a, (b_amarelo.centerx - lbl_a.get_width() // 2, b_amarelo.centery - lbl_a.get_height() // 2))

                    # Botão Cinza
                    b_cinza = pygame.Rect(sr.x + 8 + btn_w, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (50, 50, 56), b_cinza, border_radius=4)
                    lbl_c = self.fMi.render("Cinza", True, (220, 220, 230))
                    tela.blit(lbl_c, (b_cinza.centerx - lbl_c.get_width() // 2, b_cinza.centery - lbl_c.get_height() // 2))

                    # Botão Vermelho
                    b_vermelho = pygame.Rect(sr.x + 12 + 2 * btn_w, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (80, 20, 20), b_vermelho, border_radius=4)
                    lbl_v = self.fMi.render("Vermelho", True, (255, 180, 180))
                    tela.blit(lbl_v, (b_vermelho.centerx - lbl_v.get_width() // 2, b_vermelho.centery - lbl_v.get_height() // 2))
                else:
                    # Slot ativo! Desenhar os detalhes da carta e um botão de [X] (Descartar) no final
                    pygame.draw.rect(tela, (18, 20, 38), sr, border_radius=5)
                    pygame.draw.rect(tela, C_BORDA, sr, 1, border_radius=5)

                    # Nome
                    nt = self.fMi.render(slot['nome'][:20], True, C_TEXTO)
                    tela.blit(nt, (sr.x + 4, sr.y + 4))

                    # Custo
                    from ..resolvedor_acoes import CUSTO_ADICIONAL_SLOT
                    custo_base = slot.get("custo", {})
                    custo_adicional = CUSTO_ADICIONAL_SLOT.get(slot["id"], {})
                    custo_total = {}
                    for r_type in ["madeira", "couro", "metal"]:
                        qtd_req = custo_base.get(r_type, 0) + custo_adicional.get(r_type, 0)
                        if qtd_req > 0:
                            custo_total[r_type] = qtd_req

                    alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
                    partes_custo = []
                    for r_type, qtd_total in custo_total.items():
                        qtd_alocada = alocados.get(r_type, 0)
                        simb_r = "W" if r_type == "madeira" else "L" if r_type == "couro" else "I"
                        partes_custo.append(f"{simb_r}:{qtd_alocada}/{qtd_total}")
                    custo_txt = " ".join(partes_custo)

                    ct2 = self.fMi.render(custo_txt, True, C_DIM)
                    tela.blit(ct2, (sr.x + 4, sr.y + 20))

                    # Botão Descartar
                    b_descartar = pygame.Rect(sr.right - 44, sr.y + 4, 40, 30)
                    pygame.draw.rect(tela, (80, 20, 20), b_descartar, border_radius=4)
                    lbl_x = self.fMi.render("X", True, (255, 255, 255))
                    tela.blit(lbl_x, (b_descartar.centerx - lbl_x.get_width() // 2, b_descartar.centery - lbl_x.get_height() // 2))
            else:
                # Fluxo normal
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

                if is_slot_vazio:
                    nt = self.fMi.render("[VAZIO]", True, C_DIM)
                    tela.blit(nt, (sr.x + 4, sr.y + 12))
                else:
                    st_nome = (f"[BLOQUEADO] {slot['nome']}" if slot.get("bloqueado") else
                               f"[ADQUIRIDO] {slot['nome']}" if slot.get("adquirido") else
                               f"[*] {slot['nome']}")
                    nt = self.fMi.render(st_nome[:26], True,
                                         C_PERIGO if slot.get("bloqueado") else
                                         C_VERDE  if slot.get("adquirido") else C_TEXTO)
                    tela.blit(nt, (sr.x + 4, sr.y + 4))

                    from ..resolvedor_acoes import CUSTO_ADICIONAL_SLOT
                    sid = slot["id"]
                    custo_base = slot.get("custo", {})
                    custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
                    
                    custo_total = {}
                    for r_type in ["madeira", "couro", "metal"]:
                        qtd = custo_base.get(r_type, 0) + custo_adicional.get(r_type, 0)
                        if qtd > 0:
                            custo_total[r_type] = qtd
                    
                    alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
                    
                    partes_custo = []
                    for r_type, qtd_total in custo_total.items():
                        qtd_alocada = alocados.get(r_type, 0)
                        simb_r = "W" if r_type == "madeira" else "L" if r_type == "couro" else "I"
                        partes_custo.append(f"{simb_r}:{qtd_alocada}/{qtd_total}")
                        
                    custo_txt = " ".join(partes_custo)
                    esta_completo = all(alocados.get(r_type, 0) >= qtd for r_type, qtd in custo_total.items())
                    cor_custo = C_VERDE if esta_completo else C_DIM
                    
                    if slot.get("adquirido"):
                        custo_txt = "Completado e Adquirido"
                        cor_custo = C_VERDE
                    elif slot.get("bloqueado"):
                        custo_txt = "Slot Destruído"
                        cor_custo = C_PERIGO
                    elif esta_completo:
                        custo_txt = custo_txt + "  [PRONTO]"
                        cor_custo = C_OURO

                    ct2 = self.fMi.render(custo_txt, True, cor_custo)
                    tela.blit(ct2, (sr.x + 4, sr.y + 20))

            yt += 42

        # Adiciona o botão "Concluir Reposição" se estiver na fase de repovoar
        if self.fase == "REPOVOAR_MERCADO":
            self.btn_concluir_reposicao_rect = pygame.Rect(x + 6, yt, pw - 12, 34)
            pygame.draw.rect(tela, (25, 80, 25), self.btn_concluir_reposicao_rect, border_radius=5)
            lbl_done = self.fG.render("CONCLUIR REPOSICAO", True, (255, 255, 255))
            tela.blit(lbl_done, (self.btn_concluir_reposicao_rect.centerx - lbl_done.get_width() // 2, self.btn_concluir_reposicao_rect.centery - lbl_done.get_height() // 2))
            yt += 38
        else:
            self.btn_concluir_reposicao_rect = None

        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

        # ── Log Estilizado (Terminal de RPG) ────────────────────────────
        log_bg = pygame.Rect(x + 6, yt, pw - 12, ph - (yt - y) - 8)
        pygame.draw.rect(tela, (8, 9, 16), log_bg, border_radius=4)
        pygame.draw.rect(tela, (25, 27, 42), log_bg, 1, border_radius=4)
        
        max_lin = max(1, (log_bg.height - 8) // 14)
        entries = self.log[-(max_lin):]
        
        cor_map = {"DERROTA": C_PERIGO, "VITORIA": C_VERDE, "AMEACA": C_INVASOR,
                   "CERCO": C_CERCO, "CARTA": C_OURO, "HEROI": C_VERDE,
                   "SISTEMA": C_DIM}
        pre_map = {"DERROTA": "[X]", "VITORIA": "[V]", "AMEACA": "[!]", "CERCO": "[C]",
                   "CARTA": "[#]", "HEROI": "[*]", "SISTEMA": "[o]"}
        
        yt_log = log_bg.y + 6
        for tipo, msg in entries:
            cor = cor_map.get(tipo, C_TEXTO)
            pre = pre_map.get(tipo, "-")
            linha = f"{pre} {msg}"
            for part in [linha[i:i + 36] for i in range(0, len(linha), 36)]:
                lt = self.fMi.render(part, True, cor)
                tela.blit(lt, (log_bg.x + 6, yt_log))
                yt_log += 14
                if yt_log > log_bg.bottom - 12:
                    break

    _slot_rects_cache = {}  # dict[int, pygame.Rect]

    def _slot_rect(self, slot_id):
        return self._slot_rects_cache.get(slot_id)

    def _calcular_pos_carta_na_mao(self, idx, total_cartas):
        mr = self.mao_rect
        total_cartas = max(1, total_cartas)
        # Espaço reservado: 230px na esquerda (deck inimigos + descarte), 130px na direita (deck herói)
        espaco_reservado_esquerda = 230
        espaco_reservado_direita = 130
        largura_disponivel = mr.width - espaco_reservado_esquerda - espaco_reservado_direita
        
        cw = min(96, largura_disponivel // total_cartas)
        gap = max(2, (largura_disponivel - cw * total_cartas) // (total_cartas + 1))
        cx = mr.x + espaco_reservado_esquerda + gap + idx * (cw + gap)
        cy = mr.y + 4
        ch = mr.height - 8
        return cx, cy, cw, ch

    # ── MÃO DO HERÓI (bottom strip) ──────────────────────────────────────
    def _draw_mao(self, tela):
        mr = self.mao_rect
        pygame.draw.rect(tela, (10, 12, 24), mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)

        mao = self.estado["mao"]
        self.carta_rects = []
        
        # 1. Desenhar o Deck (Baralho) do Herói no canto direito do rodapé
        deck_cartas_qtd = len(self.estado["deck_heroi"])
        deck_rect = pygame.Rect(mr.right - 106, mr.y + 6, 96, mr.height - 12)
        
        # Efeito de pilha 3D para o deck do herói
        for offset in range(min(4, max(1, deck_cartas_qtd // 3))):
            d_rect = deck_rect.move(-offset * 2, -offset * 2)
            sprite_verso = None
            if hasattr(self, 'card_sprites') and self.card_sprites:
                sprite_verso = self.card_sprites.get("pedra")
            if sprite_verso:
                scaled_verso = pygame.transform.smoothscale(sprite_verso, (d_rect.width, d_rect.height))
                tela.blit(scaled_verso, d_rect.topleft)
            else:
                pygame.draw.rect(tela, (40, 30, 20), d_rect, border_radius=6)
                pygame.draw.rect(tela, C_BORDA, d_rect, 1, border_radius=6)

        # Texto do Deck por cima da pilha
        if deck_cartas_qtd > 0:
            top_deck_rect = deck_rect.move(-min(4, max(1, deck_cartas_qtd // 3)) * 2, -min(4, max(1, deck_cartas_qtd // 3)) * 2)
            lbl_deck1 = self.fMi.render("BARALHO", True, C_OURO)
            lbl_deck2 = self.fMi.render(str(deck_cartas_qtd), True, C_TEXTO)
            tela.blit(lbl_deck1, (top_deck_rect.centerx - lbl_deck1.get_width() // 2, top_deck_rect.y + 40))
            tela.blit(lbl_deck2, (top_deck_rect.centerx - lbl_deck2.get_width() // 2, top_deck_rect.y + 64))

        # 2. Desenhar o Deck de Inimigos no canto esquerdo do rodapé
        deck_ini_qtd = len(self.estado.get("deck_inimigos", []))
        deck_ini_rect = pygame.Rect(mr.x + 10, mr.y + 6, 96, mr.height - 12)
        
        # Efeito de pilha 3D para o deck de inimigos (vermelho/ameaçador)
        for offset in range(min(4, max(1, deck_ini_qtd // 3))):
            d_rect = deck_ini_rect.move(offset * 2, -offset * 2)
            pygame.draw.rect(tela, (40, 14, 14), d_rect, border_radius=6)
            pygame.draw.rect(tela, (140, 30, 30), d_rect, 1, border_radius=6)
            
        # Texto do Deck por cima da pilha
        if deck_ini_qtd > 0:
            top_deck_rect = deck_ini_rect.move(min(4, max(1, deck_ini_qtd // 3)) * 2, -min(4, max(1, deck_ini_qtd // 3)) * 2)
            lbl_deck1 = self.fMi.render("DECK INI", True, C_PERIGO)
            lbl_deck2 = self.fMi.render(str(deck_ini_qtd), True, C_TEXTO)
            tela.blit(lbl_deck1, (top_deck_rect.centerx - lbl_deck1.get_width() // 2, top_deck_rect.y + 40))
            tela.blit(lbl_deck2, (top_deck_rect.centerx - lbl_deck2.get_width() // 2, top_deck_rect.y + 64))

        # 3. Desenhar a última carta de inimigo revelada ao lado do deck de inimigos
        descarte_ini = self.estado.get("descarte_inimigos", [])
        if descarte_ini:
            ultima_carta = descarte_ini[-1]
            carta_ini_rect = pygame.Rect(mr.x + 116, mr.y + 6, 96, mr.height - 12)
            
            # Fundo da carta revelada
            pygame.draw.rect(tela, (24, 16, 16), carta_ini_rect, border_radius=6)
            pygame.draw.rect(tela, C_PERIGO, carta_ini_rect, 1, border_radius=6)
            
            # Texto da carta
            nome_lbl1 = self.fMi.render("REVELADO", True, C_DIM)
            nome_lbl2 = self.fMi.render(ultima_carta.upper(), True, C_PERIGO)
            tela.blit(nome_lbl1, (carta_ini_rect.centerx - nome_lbl1.get_width() // 2, carta_ini_rect.y + 20))
            tela.blit(nome_lbl2, (carta_ini_rect.centerx - nome_lbl2.get_width() // 2, carta_ini_rect.y + 45))
            
            # Icone de Runa/Caveira
            pygame.draw.circle(tela, C_PERIGO, (carta_ini_rect.centerx, carta_ini_rect.y + 80), 5)
            pygame.draw.rect(tela, C_PERIGO, (carta_ini_rect.centerx - 4, carta_ini_rect.y + 84, 8, 4))

        if not mao:
            nt = self.fP.render("Sem cartas na mão — jogue cartas ou passe o turno", True, C_DIM)
            # Centraliza o texto no espaço disponível para as cartas da mão
            disponivel_x = mr.x + 230 + (mr.width - 360) // 2
            tela.blit(nt, (disponivel_x - nt.get_width() // 2, mr.centery - 8))
            return

        mouse = pygame.mouse.get_pos()
        GEMAS_COR = {
            "movimento": (100, 200, 255),  # Azul
            "trabalho":  (120, 220, 100),  # Verde
            "escavacao": (255, 195, 40),   # Dourado
        }

        # Rastreia quais cartas na mão têm animações ativas (não concluídas)
        anims_ativas = {}
        if hasattr(self, 'animacoes_cartas_compra') and self.animacoes_cartas_compra:
            for anim in self.animacoes_cartas_compra:
                if not anim.get('finalizada', False):
                    anims_ativas[anim['idx_mao']] = anim

        # Desenhar as cartas
        for i, carta in enumerate(mao):
            cx, cy, cw, ch = self._calcular_pos_carta_na_mao(i, len(mao))
            
            # Se a carta está sendo animada, calculamos a posição interpolada
            if i in anims_ativas:
                anim = anims_ativas[i]
                if anim.get('delay', 0) > 0:
                    # Ainda está no deck (delay), não desenha voando ainda
                    self.carta_rects.append(pygame.Rect(cx, cy, cw, ch))
                    continue
                
                prog = anim['progresso']
                sx, sy = anim['start_pos']
                ex, ey = anim['end_pos']
                
                # Interpolação linear + arco de parábola
                curr_x = sx + (ex - sx) * prog
                curr_y = sy + (ey - sy) * prog
                # Arco de subida: sobe até 35 pixels no meio do voo
                curr_y -= math.sin(prog * math.pi) * 35
                
                crect = pygame.Rect(int(curr_x), int(curr_y), cw, ch)
                self.carta_rects.append(crect)
                hover = False
                sel = False
            else:
                # Carta normal na mão
                temp_rect = pygame.Rect(cx, cy, cw, ch)
                hover = temp_rect.collidepoint(mouse)
                sel   = (i == self.idx_carta_queimar)
                
                # Animação suave de hover (sobe 8 pixels)
                deslocamento_y = -8 if hover else 0
                crect = pygame.Rect(cx, cy + deslocamento_y, cw, ch)
                self.carta_rects.append(crect)

            # --- DESENHO DE UMA CARTA ---
            sprite = None
            if hasattr(self, 'card_sprites') and self.card_sprites:
                if carta.get("movimento"):
                    sprite = self.card_sprites.get("azul")
                elif carta.get("trabalho"):
                    sprite = self.card_sprites.get("verde")
                elif carta.get("escavacao"):
                    sprite = self.card_sprites.get("amarela")
                else:
                    sprite = self.card_sprites.get("cinza")

            if sprite:
                scaled_sprite = pygame.transform.smoothscale(sprite, (cw, ch))
                tela.blit(scaled_sprite, crect.topleft)
                if sel:
                    pygame.draw.rect(tela, C_ACENTO, crect, 2, border_radius=7)
                elif hover:
                    pygame.draw.rect(tela, C_OURO, crect, 2, border_radius=7)
            else:
                grad = pygame.Surface((2, 2))
                c_top = (14, 20, 36) if not hover else (26, 34, 58)
                c_bot = (32, 18, 48) if not hover else (50, 28, 75)
                grad.set_at((0, 0), c_top); grad.set_at((1, 0), c_top)
                grad.set_at((0, 1), c_bot); grad.set_at((1, 1), c_bot)
                grad_scaled = pygame.transform.smoothscale(grad, (cw, ch))
                tela.blit(grad_scaled, crect.topleft)
                borda_cor = C_ACENTO if sel else (C_OURO if hover else C_BORDA)
                pygame.draw.rect(tela, borda_cor, crect, 1, border_radius=7)

            # Melhoria de Design da Carta (Mais minimalista, sem gem_frame retangular gigante)
            tipo_gema = "movimento"
            if carta.get("trabalho"):  tipo_gema = "trabalho"
            if carta.get("escavacao"): tipo_gema = "escavacao"
            cor_gema = GEMAS_COR.get(tipo_gema, (200, 200, 200))
            
            # Círculo/Aura de runa pequena no topo centro
            rx_center = crect.centerx
            ry_center = crect.y + 20
            pygame.draw.circle(tela, (8, 9, 16), (rx_center, ry_center), 10)
            
            # Desenha runa losango interna (maior)
            gem_pts = [
                (rx_center, ry_center - 6),
                (rx_center + 6, ry_center),
                (rx_center, ry_center + 6),
                (rx_center - 6, ry_center)
            ]
            pygame.draw.polygon(tela, cor_gema, gem_pts)
            pygame.draw.polygon(tela, C_TEXTO, gem_pts, 1)

            # Nome da carta com tamanho 18
            nome_cortado = carta["nome"][:16]
            nt = self.fMi.render(nome_cortado, True, C_TEXTO)
            tela.blit(nt, (crect.centerx - nt.get_width() // 2, crect.y + 36))

            # Descrição da carta no centro da nova carta grande
            desc = carta.get("descricao", "")
            if desc:
                lbl_desc = self.fMi.render(desc, True, C_DIM)
                tela.blit(lbl_desc, (crect.centerx - lbl_desc.get_width() // 2, crect.y + 68))

            # Stats formatados em uma caixinha discreta no rodapé
            stats = []
            if carta.get("movimento"): stats.append(f"M{carta['movimento']}")
            if carta.get("trabalho"):  stats.append(f"T{carta['trabalho']}")
            if carta.get("escavacao"): stats.append(f"E{carta['escavacao']}")
            st_text = " ".join(stats)
            st2 = self.fMi.render(st_text, True, cor_gema)
            
            stat_bg = pygame.Rect(crect.centerx - st2.get_width() // 2 - 4, crect.y + ch - 22, st2.get_width() + 8, 16)
            pygame.draw.rect(tela, (12, 14, 24), stat_bg, border_radius=3)
            pygame.draw.rect(tela, (28, 30, 48), stat_bg, 1, border_radius=3)
            tela.blit(st2, (crect.centerx - st2.get_width() // 2, crect.y + ch - 21))

            if sel:
                ql = self.fMi.render("DESCARTE", True, C_PERIGO)
                ql_bg = pygame.Rect(crect.centerx - ql.get_width() // 2 - 2, crect.y + 54, ql.get_width() + 4, 14)
                pygame.draw.rect(tela, (30, 10, 10), ql_bg, border_radius=2)
                tela.blit(ql, (crect.centerx - ql.get_width() // 2, crect.y + 54))

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

        # Os botões de ação direta foram desativados e removidos do rodapé
        pass

        # Fim de turno
        _btn(self.btn_fim_turno, "Encerrar Turno  [Ent]",
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
            
            # Botão Limpar Rocha (4 PE)
            br_rocha = pygame.Rect(bx, H - 48, 140, 36)
            ativo_rocha = e.get("pontos_escavacao", 0) >= 4
            _btn(br_rocha, "🪨 Limpar Rocha(4PE)", ativo_rocha,
                 (30, 40, 50), (50, 70, 90), (20, 20, 20))
            if br_rocha.collidepoint(mouse) and ativo_rocha:
                if pygame.mouse.get_pressed()[0]:
                    self._limpar_rocha_goblin()

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

        # Fundo da carta de ameaça vermelha do spritesheet
        sprite_ameaca = None
        if hasattr(self, 'card_sprites') and self.card_sprites:
            sprite_ameaca = self.card_sprites.get("vermelha")
            
        if sprite_ameaca:
            scaled_sprite = pygame.transform.smoothscale(sprite_ameaca, (cw, ch))
            tela.blit(scaled_sprite, (cx, cy))
            pygame.draw.rect(tela, cor_niv, pygame.Rect(cx, cy, cw, ch), 3, border_radius=14)
        else:
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

    def _draw_modal_escolha_carta(self, tela, W, H):
        # 1. Overlay semi-transparente
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 9, 16, 210))
        tela.blit(overlay, (0, 0))

        carta = self.estado["mao"][self.idx_carta_sendo_jogada]
        pm = carta.get("movimento", 0)
        pt = carta.get("trabalho", 0)
        pe = carta.get("escavacao", 0)

        is_hibrida = (pm > 0) and (pt > 0 or pe > 0)

        # 2. Caixa central do modal
        mw = 580 if is_hibrida else 440
        mh = 240
        mx, my = W // 2 - mw // 2, H // 2 - mh // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(tela, (18, 20, 32), modal_rect, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, modal_rect, 2, border_radius=8)

        # 3. Título e nome da carta
        tit = self.fG.render("ESCOLHA A ACAO DA CARTA", True, C_ACENTO)
        tela.blit(tit, (modal_rect.centerx - tit.get_width() // 2, my + 20))
        
        sub = self.fMi.render(carta["nome"].upper(), True, C_OURO)
        tela.blit(sub, (modal_rect.centerx - sub.get_width() // 2, my + 44))

        # 4. Botões de Ação
        btn_w, btn_h = 120, 80
        mouse = pygame.mouse.get_pos()
        
        if is_hibrida:
            # 4 botões: Andar, Coletar, Ambos, Atacar
            self.btn_andar_rect = pygame.Rect(mx + 20, my + 90, btn_w, btn_h)
            self.btn_coletar_rect = pygame.Rect(mx + 160, my + 90, btn_w, btn_h)
            self.btn_ambos_rect = pygame.Rect(mx + 300, my + 90, btn_w, btn_h)
            self.btn_atacar_rect = pygame.Rect(mx + 440, my + 90, btn_w, btn_h)
            
            # Desenha Andar
            b_andar_cor = (30, 80, 30) if self.btn_andar_rect.collidepoint(mouse) else (20, 50, 20)
            pygame.draw.rect(tela, b_andar_cor, self.btn_andar_rect, border_radius=6)
            pygame.draw.rect(tela, (85, 205, 85), self.btn_andar_rect, 1, border_radius=6)
            lbl_a1 = self.fMi.render("ANDAR", True, (200, 255, 200))
            lbl_a2 = self.fP.render(f"+{pm} PM", True, C_TEXTO)
            tela.blit(lbl_a1, (self.btn_andar_rect.centerx - lbl_a1.get_width() // 2, self.btn_andar_rect.y + 20))
            tela.blit(lbl_a2, (self.btn_andar_rect.centerx - lbl_a2.get_width() // 2, self.btn_andar_rect.y + 44))

            # Desenha Coletar
            b_coletar_cor = (80, 50, 15) if self.btn_coletar_rect.collidepoint(mouse) else (50, 30, 10)
            pygame.draw.rect(tela, b_coletar_cor, self.btn_coletar_rect, border_radius=6)
            pygame.draw.rect(tela, (215, 165, 85), self.btn_coletar_rect, 1, border_radius=6)
            lbl_c1 = self.fMi.render("COLETAR", True, (255, 220, 180))
            textos_recurso = []
            if pt > 0: textos_recurso.append(f"+{pt}PT")
            if pe > 0: textos_recurso.append(f"+{pe}PE")
            lbl_c2_str = " ".join(textos_recurso) if textos_recurso else "+0 Rec"
            lbl_c2 = self.fP.render(lbl_c2_str, True, C_TEXTO)
            tela.blit(lbl_c1, (self.btn_coletar_rect.centerx - lbl_c1.get_width() // 2, self.btn_coletar_rect.y + 20))
            tela.blit(lbl_c2, (self.btn_coletar_rect.centerx - lbl_c2.get_width() // 2, self.btn_coletar_rect.y + 44))

            # Desenha Ambos
            b_ambos_cor = (30, 70, 80) if self.btn_ambos_rect.collidepoint(mouse) else (20, 45, 50)
            pygame.draw.rect(tela, b_ambos_cor, self.btn_ambos_rect, border_radius=6)
            pygame.draw.rect(tela, (100, 220, 240), self.btn_ambos_rect, 1, border_radius=6)
            lbl_ab1 = self.fMi.render("AMBOS", True, (200, 240, 255))
            lbl_ab2 = self.fP.render("ANDAR+COL", True, C_TEXTO)
            tela.blit(lbl_ab1, (self.btn_ambos_rect.centerx - lbl_ab1.get_width() // 2, self.btn_ambos_rect.y + 20))
            tela.blit(lbl_ab2, (self.btn_ambos_rect.centerx - lbl_ab2.get_width() // 2, self.btn_ambos_rect.y + 44))

            # Desenha Atacar
            b_atacar_cor = (80, 20, 20) if self.btn_atacar_rect.collidepoint(mouse) else (50, 10, 10)
            pygame.draw.rect(tela, b_atacar_cor, self.btn_atacar_rect, border_radius=6)
            pygame.draw.rect(tela, (255, 100, 100), self.btn_atacar_rect, 1, border_radius=6)
            lbl_at1 = self.fMi.render("ATACAR", True, (255, 200, 200))
            lbl_at2 = self.fP.render("COMBATE", True, C_DIM)
            tela.blit(lbl_at1, (self.btn_atacar_rect.centerx - lbl_at1.get_width() // 2, self.btn_atacar_rect.y + 20))
            tela.blit(lbl_at2, (self.btn_atacar_rect.centerx - lbl_at2.get_width() // 2, self.btn_atacar_rect.y + 44))

        else:
            # 3 botões clássicos
            self.btn_ambos_rect = None
            self.btn_andar_rect = pygame.Rect(mx + 20, my + 90, btn_w, btn_h)
            self.btn_coletar_rect = pygame.Rect(mx + 160, my + 90, btn_w, btn_h)
            self.btn_atacar_rect = pygame.Rect(mx + 300, my + 90, btn_w, btn_h)
            
            # Desenha Andar
            b_andar_cor = (30, 80, 30) if self.btn_andar_rect.collidepoint(mouse) else (20, 50, 20)
            pygame.draw.rect(tela, b_andar_cor, self.btn_andar_rect, border_radius=6)
            pygame.draw.rect(tela, (85, 205, 85), self.btn_andar_rect, 1, border_radius=6)
            lbl_a1 = self.fMi.render("ANDAR", True, (200, 255, 200))
            lbl_a2 = self.fP.render(f"+{pm} PM", True, C_TEXTO)
            tela.blit(lbl_a1, (self.btn_andar_rect.centerx - lbl_a1.get_width() // 2, self.btn_andar_rect.y + 20))
            tela.blit(lbl_a2, (self.btn_andar_rect.centerx - lbl_a2.get_width() // 2, self.btn_andar_rect.y + 44))

            # Desenha Coletar
            b_coletar_cor = (80, 50, 15) if self.btn_coletar_rect.collidepoint(mouse) else (50, 30, 10)
            pygame.draw.rect(tela, b_coletar_cor, self.btn_coletar_rect, border_radius=6)
            pygame.draw.rect(tela, (215, 165, 85), self.btn_coletar_rect, 1, border_radius=6)
            lbl_c1 = self.fMi.render("COLETAR", True, (255, 220, 180))
            textos_recurso = []
            if pt > 0: textos_recurso.append(f"+{pt}PT")
            if pe > 0: textos_recurso.append(f"+{pe}PE")
            lbl_c2_str = " ".join(textos_recurso) if textos_recurso else "+0 Rec"
            lbl_c2 = self.fP.render(lbl_c2_str, True, C_TEXTO)
            tela.blit(lbl_c1, (self.btn_coletar_rect.centerx - lbl_c1.get_width() // 2, self.btn_coletar_rect.y + 20))
            tela.blit(lbl_c2, (self.btn_coletar_rect.centerx - lbl_c2.get_width() // 2, self.btn_coletar_rect.y + 44))

            # Desenha Atacar
            b_atacar_cor = (80, 20, 20) if self.btn_atacar_rect.collidepoint(mouse) else (50, 10, 10)
            pygame.draw.rect(tela, b_atacar_cor, self.btn_atacar_rect, border_radius=6)
            pygame.draw.rect(tela, (255, 100, 100), self.btn_atacar_rect, 1, border_radius=6)
            lbl_at1 = self.fMi.render("ATACAR", True, (255, 200, 200))
            lbl_at2 = self.fP.render("COMBATE", True, C_DIM)
            tela.blit(lbl_at1, (self.btn_atacar_rect.centerx - lbl_at1.get_width() // 2, self.btn_atacar_rect.y + 20))
            tela.blit(lbl_at2, (self.btn_atacar_rect.centerx - lbl_at2.get_width() // 2, self.btn_atacar_rect.y + 44))

        lbl_esc = self.fMi.render("Pressione [ESC] para cancelar", True, C_DIM)
        tela.blit(lbl_esc, (modal_rect.centerx - lbl_esc.get_width() // 2, my + 194))

    def _aplicar_acao_carta(self, idx, acao):
        print(f"[DEBUG APLICAR CARTA] idx={idx} acao={acao}")
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            print(f"[DEBUG APLICAR CANCELADO] idx fora dos limites da mao de tamanho {len(mao)}")
            return
        carta = mao.pop(idx)
        discard = list(self.estado["descarte"]) + [carta]
        
        val_mov = carta.get("movimento", 0)
        val_trab = carta.get("trabalho", 0)
        val_esc = carta.get("escavacao", 0)
        
        delta = {
            "mao": mao,
            "descarte": discard,
        }
        
        efeito = carta.get("efeito_extra")
        if efeito == "draw_1":
            # Compra 1 carta
            deck = list(self.estado["deck_heroi"])
            if deck:
                c = deck.pop(0)
                delta["mao"] = delta["mao"] + [c]
                delta["deck_heroi"] = deck
                self._push("SISTEMA", "Efeito extra da carta: Comprou 1 carta adicional.")
        elif efeito == "invocar_inimigo":
            import random
            from src.cerco_isectum import NOMES_ZONA
            zona_spawn = random.choice(["campo_norte", "campo_sul", "campo_leste", "campo_oeste"])
            
            # Adiciona +1 invasor nessa zona externa e desconta da reserva se possível
            novos_invasores = dict(self.estado["invasores"])
            novos_invasores[zona_spawn] = novos_invasores.get(zona_spawn, 0) + 1
            delta["invasores"] = novos_invasores
            
            self._push("AMEACA", f"Efeito da carta: Invocou 1x Invasor em {NOMES_ZONA.get(zona_spawn, zona_spawn)}!")
            self._feedback("Inimigo Invocado!", C_PERIGO)
        
        if acao == "andar":
            delta["pontos_movimento"] = self.estado["pontos_movimento"] + val_mov
            self.estado = aplicar_delta(self.estado, delta)
            self._push("HEROI", f"Jogou [{carta['nome']}] para ANDAR: +{val_mov} PM")
            self._feedback(f"Andar: +{val_mov} PM", C_VERDE)
            
            # Atualiza células alcançáveis
            from ..resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )
            self._selecionar_modo(MODO_MOVER)
            
        elif acao == "coletar":
            delta["pontos_trabalho"] = self.estado["pontos_trabalho"] + val_trab
            delta["pontos_escavacao"] = self.estado["pontos_escavacao"] + val_esc
            self.estado = aplicar_delta(self.estado, delta)
            
            recursos_adicionados = []
            if val_trab > 0: recursos_adicionados.append(f"+{val_trab}PT")
            if val_esc > 0: recursos_adicionados.append(f"+{val_esc}PE")
            rec_str = " ".join(recursos_adicionados) if recursos_adicionados else "+0 Rec"
            
            self._push("HEROI", f"Jogou [{carta['nome']}] para COLETAR: {rec_str}")
            self._feedback(f"Coletar: {rec_str}", C_VERDE)
            
            if val_trab > 0:
                self.modo_acao = MODO_TRABALHAR
            elif val_esc > 0:
                self.modo_acao = MODO_ESCAVAR
                
            self._processar_acoes_automaticas(mostrar_erro_se_falhar=True)
            
        elif acao == "ambos":
            delta["pontos_movimento"] = self.estado["pontos_movimento"] + val_mov
            delta["pontos_trabalho"] = self.estado["pontos_trabalho"] + val_trab
            delta["pontos_escavacao"] = self.estado["pontos_escavacao"] + val_esc
            self.estado = aplicar_delta(self.estado, delta)
            
            recursos_adicionados = []
            if val_trab > 0: recursos_adicionados.append(f"+{val_trab}PT")
            if val_esc > 0: recursos_adicionados.append(f"+{val_esc}PE")
            rec_str = " ".join(recursos_adicionados) if recursos_adicionados else "+0 Rec"
            
            self._push("HEROI", f"Jogou [{carta['nome']}] para AMBOS: +{val_mov} PM e {rec_str}")
            self._feedback(f"Ambos: +{val_mov} PM e {rec_str}", C_VERDE)
            
            # Atualiza células alcançáveis
            from ..resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )
            self._selecionar_modo(MODO_MOVER)
            self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)
            
        elif acao == "atacar":
            self.estado = aplicar_delta(self.estado, delta)
            self._push("HEROI", f"Jogou [{carta['nome']}] para ATACAR!")
            self._feedback("Atacar ativado!", C_VERDE)
            
            pos_heroi = self.estado.get("pos_heroi", "camara_central")
            if pos_heroi and "torre" in pos_heroi:
                self._selecionar_modo(MODO_ATIRAR)
            else:
                self._selecionar_modo(MODO_ATACAR)
                
        self._avancar_inimigos_carta()
        self.idx_carta_sendo_jogada = -1

    def _jogar_carta_invasao(self, idx):
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            return
        carta = mao.pop(idx)
        discard = list(self.estado["descarte"]) + [carta]
        
        # Invoca inimigo
        import random
        from src.cerco_isectum import NOMES_ZONA
        zona_spawn = random.choice(["campo_norte", "campo_sul", "campo_leste", "campo_oeste"])
        
        novos_invasores = dict(self.estado["invasores"])
        novos_invasores[zona_spawn] = novos_invasores.get(zona_spawn, 0) + 1
        
        delta = {
            "mao": mao,
            "descarte": discard,
            "invasores": novos_invasores
        }
        
        self.estado = aplicar_delta(self.estado, delta)
        
        self._push("AMEACA", f"Invasão: Invasor Orc jogado da mão! Spawn em {NOMES_ZONA.get(zona_spawn, zona_spawn)}!")
        self._feedback("Orc Invocado da Mão!", C_PERIGO)
        try:
            self.game.play_sound('invalid_action')
        except:
            pass

    def _avancar_inimigos_carta(self):
        """Toda vez que uma carta é jogada, os inimigos avançam 1 passo em direção ao ouro (camara_central).
        
        Fluxo de zonas:
          campos externos  → muralhas  → oficinas  → camara_central
        Invasores na camara_central roubam 1 moeda do tesouro e voltam à reserva.
        """
        from ..cerco_isectum import NOMES_ZONA

        # Mapeamento de avanço: zona_atual -> proxima_zona
        FLUXO = {
            "campo_norte": "muralha_norte",
            "campo_sul":   "muralha_sul",
            "campo_oeste": "muralha_oeste",
            "campo_leste": "muralha_leste",
            "muralha_norte": "carpintaria",
            "muralha_sul":   "curtume",
            "muralha_oeste": "fundicao",
            "muralha_leste": "patio",
            "carpintaria":   "camara_central",
            "curtume":       "camara_central",
            "fundicao":      "camara_central",
            "patio":         "camara_central",
        }

        e = self.estado
        novos = dict(e["invasores"])
        tesouro = e["tesouro"]
        reserva = e["reserva"]
        logs_avanco = []
        derrota = False

        # Ordem de processamento: do mais profundo ao mais externo,
        # para evitar dupla contagem no mesmo passo.
        ordem = [
            "camara_central",
            "carpintaria", "curtume", "fundicao", "patio",
            "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
            "campo_norte", "campo_sul", "campo_oeste", "campo_leste",
        ]

        for zona in ordem:
            qtd = novos.get(zona, 0)
            if qtd <= 0:
                continue

            if zona == "camara_central":
                # Inimigos na câmara roubam tesouro e voltam à reserva
                roubado = min(qtd, tesouro)
                if roubado > 0:
                    tesouro -= roubado
                    reserva = min(10, reserva + roubado)
                    nome_zona = NOMES_ZONA.get(zona, zona)
                    logs_avanco.append(
                        ("AMEACA", f"{qtd}x invasor no {nome_zona} rouba {roubado}🪙 do tesouro!")
                    )
                novos[zona] = 0
                if tesouro <= 0:
                    derrota = True
            elif zona in FLUXO:
                proxima = FLUXO[zona]
                if "campo" in zona:
                    # Escalada: apenas metade dos invasores sobe (arredondado para cima)
                    subindo = (qtd + 1) // 2
                    ficando = qtd - subindo
                    novos[zona] = ficando
                    novos[proxima] = novos.get(proxima, 0) + subindo
                    nome_atual = NOMES_ZONA.get(zona, zona)
                    nome_prox = NOMES_ZONA.get(proxima, proxima)
                    logs_avanco.append(
                        ("AMEACA", f"{subindo}x invasor escala a muralha: {nome_atual} → {nome_prox} ({ficando}x ficaram para trás)")
                    )
                else:
                    # Avanço normal nas áreas internas
                    novos[zona] = 0
                    novos[proxima] = novos.get(proxima, 0) + qtd
                    nome_atual = NOMES_ZONA.get(zona, zona)
                    nome_prox = NOMES_ZONA.get(proxima, proxima)
                    logs_avanco.append(
                        ("AMEACA", f"{qtd}x invasor avança: {nome_atual} → {nome_prox}")
                    )

        # Aplica as mudanças de estado
        delta = {"invasores": novos, "tesouro": tesouro, "reserva": reserva}
        if derrota:
            delta["derrota"] = True
            delta["msg_derrota"] = "Tesouro saqueado pelos invasores — DERROTA!"

        self.estado = aplicar_delta(self.estado, delta)

        # Log dos avanços
        if logs_avanco:
            self._push("AMEACA", "🏃 Inimigos avançam ao jogar a carta!")
            for tag, msg in logs_avanco:
                self._push(tag, msg)

        if derrota:
            self._push("DERROTA", self.estado.get("msg_derrota", "DERROTA!"))
            self.fase = "FIM"
