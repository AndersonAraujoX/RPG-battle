"""
cerco_state.py — Cerco contra Isectum (Pygame state completo)

Refatorado em módulos:
  cerco_state_data.py   → constantes
  cerco_state_draw.py   → renderização (CercoStateDrawMixin)
  cerco_state_input.py  → eventos, teclado, clique (CercoStateInputMixin)
  cerco_state_hero.py   → gestão de heróis, cartas, upgrade (CercoStateHeroMixin)
  cerco_state_turn.py   → fluxo de turno, fases, derrota (CercoStateTurnMixin)
  cerco_state_enemy.py  → inimigos, efeitos, dev summon (CercoStateEnemyMixin)
"""
from __future__ import annotations
import pygame
import random
import copy

from ..state_base import GameState
from ...cerco_isectum import (
    criar_estado, criar_deck, processar_carta,
    avancar_ciclo_armas, aplicar_delta, NOMES_ZONA,
    CARTAS_UPGRADE, CARTAS_BASICAS,
)
from ...resolvedor_acoes import (
    validar_mover,    executar_mover,
    validar_trabalhar, executar_trabalhar,
    validar_escavar,   executar_escavar,
    validar_subornar,  executar_subornar,
    validar_comprar_upgrade, executar_comprar_upgrade,
    OFICINAS, ZONA_ESCAVACAO, NOME_RECURSO,
    obter_zona_por_coordenada, ZONAS_GRID,
    validar_alocar_recurso, executar_alocar_recurso,
    CUSTO_ADICIONAL_SLOT, custo_minimo_grade, obter_celulas_alcancaveis,
)
from ...juiz_combate import (
    resolver_melee, resolver_distancia,
    rolar_d6_customizado, calcular_dano_melee,
    resetar_dano_turno_brutamonte, validar_pode_atacar_distancia,
    ZONAS_TORRES, ZONAS_INTERNAS,
)
from ...config import ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA
from .data import (
    C_VERDE, C_PERIGO, C_ACENTO, C_HEROI, C_OURO, C_TEXTO, C_DIM,
    MODO_NENHUM, MODO_MOVER, MODO_TRABALHAR, MODO_ESCAVAR,
    MODO_SUBORNAR, MODO_UPGRADE, MODO_CONVOCAR, MODO_ATACAR, MODO_ATIRAR,
    NAR,
)
from .draw import CercoStateDrawMixin
from .input import CercoStateInputMixin
from .hero import CercoStateHeroMixin
from .turn import CercoStateTurnMixin
from .enemy import CercoStateEnemyMixin
from .ia_heroi import IAComandanteImperial
from .bot_heroi import BotHeroi
from .round_simultaneo import RoundSimultaneoMixin


class CercoState(
    CercoStateDrawMixin,
    CercoStateInputMixin,
    CercoStateHeroMixin,
    CercoStateTurnMixin,
    CercoStateEnemyMixin,
    RoundSimultaneoMixin,
    GameState,
):
    """Estado Pygame completo — Resolvedor de Ações como núcleo."""

    TAM_MAO = 5
    DECK_FIXO = 12

    def __init__(self, game, config=None):
        super().__init__(game)
        if config is None:
            config = self._default_config()
        self.config = config
        diff = config.get("dificuldade", {})
        herois = config.get("herois", [])
        fator = diff.get("fator_deck", 1.0)
        if diff.get("id") == "facil":
            fator = 0.25
        elif diff.get("id") in ("normal", "media"):
            fator = 0.50
        elif diff.get("id") == "dificil":
            fator = 1.00

        self.estado = criar_estado(
            pedregulhos=diff.get("pedregulhos", 8),
            is_solo=True,
            fator_deck=fator,
        )
        self.estado["tesouro"] = diff.get("tesouro", 20)
        self.estado["reserva"] = diff.get("reserva", 10)

        self.deck   = criar_deck(fator_deck=fator)
        if not self.estado.get("deck_inimigos"):
            from ...cerco_isectum import DADOS_INIMIGOS
            deck_ini = list(DADOS_INIMIGOS.keys()) * 2
            import random as _rnd
            _rnd.shuffle(deck_ini)
            self.estado["deck_inimigos"] = deck_ini
        self.log    = []
        self.narrativa   = "Pela barba de Durin! O cerco começa!"
        self.carta_cerco = None
        self.fase        = "JOGAR_CARTA"
        self.modo_acao   = MODO_NENHUM
        self.timer       = 0
        self.msg_feedback = ""
        self.msg_cor      = C_VERDE
        self.feedback_timer = 0
        self.idx_carta_queimar  = -1
        self.idx_slot_upgrade   = -1
        self.idx_carta_sendo_jogada = -1
        self.alcancaveis        = {}
        self.zoom               = 1.0
        self.map_backbuffer     = None
        self.map_backbuffer_sujo = True
        self.walk_anim          = None
        self.monster_walk_anims = {}
        self.ia_heroi           = None   # Será instanciado após setup dos heróis
        self.ia_banner_timer    = 0      # Timer para o banner central de turno da IA
        self.dragging_card      = False  # Arrastar carta com o mouse
        self.drag_card_idx      = None   # Índice da carta sendo arrastada
        self.bloqueio_clique_tick = 0    # Evita double-clique
        self.dev_menu_aberto    = False  # Menu de debug (F12)
        self.tipo_mercenario_selecionado  = "melee"
        self.custo_mercenario_selecionado = 5
        self._slot_rects_cache  = {}     # Cache de rects dos slots do mercado

        # ── Modo Turno-a-Turno Singleplayer Clássico ─────────────────────────
        # Cada herói escolhe e ativa o efeito de suas cartas imediatamente em seu próprio turno
        self.modo_sincronia = False
        self._init_round_simultaneo()

        # ── AutoPlay Bot ─────────────────────────────────────────────────────
        self.autoplay_ativo       = False      # Toggle: bot controla os heróis
        self.autoplay_velocidade  = "normal"   # 'lento', 'normal', 'rapido'
        self.bot_heroi            = None       # Instância de BotHeroi (criada ao ativar)

        from ...motor_combate import MotorCombate
        self.motor = MotorCombate(args_times=[0]*24, gerar_terreno=False)

        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            if zona_id.startswith("campo_"):
                continue
            for cy in range(y1, y2 + 1):
                for cx in range(x1, x2 + 1):
                    if not (0 <= cx < self.motor.tabuleiro.largura and
                            0 <= cy < self.motor.tabuleiro.altura):
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
                        if random.random() < 0.45:
                            self.motor.tabuleiro.terrain_grid[cy][cx] = "floresta"
                        else:
                            self.motor.tabuleiro.terrain_grid[cy][cx] = "normal"
                        self.motor.tabuleiro.elevation_grid[cy][cx] = 0

        POSICOES_INICIAIS = [
            (9, 9), (7, 7), (11, 7), (7, 11),
            (9, 5), (5, 9), (13, 9),
        ]
        self.herois = []
        self.heroi_atual_idx = 0
        self.motor.time_a = []
        self.motor.combatentes = []

        if not herois:
            from ...personagens.novos_personagens import Stark
            herois = [("Stark", Stark)]
        for i, (nome, cls) in enumerate(herois):
            pos = POSICOES_INICIAIS[i] if i < len(POSICOES_INICIAIS) else (9, 9)
            heroi = cls(nome, "A", nivel=5)
            self.herois.append(heroi)
            self.motor.time_a.append(heroi)
            self.motor.combatentes.append(heroi)
            self.motor.tabuleiro.adicionar_personagem(heroi, pos[0], pos[1])
        self.estado["herois_status"] = {}
        self.estado["herois_jogaram"] = []

        p_heroi = self.herois[0]
        self.estado["heroi_x"] = p_heroi.pos_x
        self.estado["heroi_y"] = p_heroi.pos_y
        from ...resolvedor_acoes import obter_zona_por_coordenada
        self.estado["pos_heroi"] = obter_zona_por_coordenada(p_heroi.pos_x, p_heroi.pos_y) or "camara_central"

        self.estado["herois_status"][p_heroi.nome] = {
            "mao":              list(self.estado.get("mao", [])),
            "deck_heroi":       list(self.estado.get("deck_heroi", [])),
            "descarte":         list(self.estado.get("descarte", [])),
            "excluidas_ciclo":  list(self.estado.get("excluidas_ciclo", [])),
            "pontos_movimento": self.estado.get("pontos_movimento", 0),
            "pontos_trabalho":  self.estado.get("pontos_trabalho", 0),
            "pontos_escavacao": self.estado.get("pontos_escavacao", 0),
            "voo_ativo":        self.estado.get("voo_ativo", False),
            "hp_atual":         p_heroi.hp_max,
            "hp_max":           p_heroi.hp_max,
        }
        for h in self.herois[1:]:
            deck_sub = copy.deepcopy(CARTAS_BASICAS)
            random.shuffle(deck_sub)
            self.estado["herois_status"][h.nome] = {
                "mao":              deck_sub[:3],
                "deck_heroi":       deck_sub[3:],
                "descarte":         [],
                "excluidas_ciclo":  [],
                "pontos_movimento": 0,
                "pontos_trabalho":  0,
                "pontos_escavacao": 0,
                "voo_ativo":        False,
                "hp_atual":         h.hp_max,
                "hp_max":           h.hp_max,
            }
        self._setup_fonts()
        self._setup_layout()
        self.terrain_iso_cache = {}

        # Instanciar IA inimiga: Filho do Imperador como diretor inimigo
        self.ia_heroi = None        # alias legacy (não usado neste modo)
        self.ia_comandante = IAComandanteImperial(self)

        from ...utils import resource_path
        caminho_card = resource_path("assets/images/environment/card/pixelCardAssest.png")
        try:
            self.spritesheet_cartas = pygame.image.load(caminho_card).convert_alpha()
            w_sheet, h_sheet = self.spritesheet_cartas.get_size()
            cw_temp = w_sheet // 6
            ch_temp = h_sheet // 2
            self.card_sprites = {
                "azul":     self.spritesheet_cartas.subsurface((0,         0, cw_temp, ch_temp)),
                "vermelha": self.spritesheet_cartas.subsurface((cw_temp,   0, cw_temp, ch_temp)),
                "cinza":    self.spritesheet_cartas.subsurface((cw_temp*2, 0, cw_temp, ch_temp)),
                "verde":    self.spritesheet_cartas.subsurface((cw_temp*3, 0, cw_temp, ch_temp)),
                "amarela":  self.spritesheet_cartas.subsurface((cw_temp*4, 0, cw_temp, ch_temp)),
                "pedra":    self.spritesheet_cartas.subsurface((cw_temp*5, 0, cw_temp, ch_temp)),
            }
        except Exception as e:
            print(f"Erro ao carregar spritesheet de cartas: {e}")
            self.spritesheet_cartas = None
            self.card_sprites = {}

        self.carta_rects = []
        self.animacoes_cartas_compra = []
        self._init_terrain_textures()
        self._comprar_mao()
        nomes_herois = ", ".join(
            ("?????" if h.nome == "Aquele" else h.nome) for h in self.herois
        )
        self._push("SISTEMA", f"Cerco contra Isectum! Heróis: {nomes_herois}")
        self._push("SISTEMA", f"Dificuldade: {diff.get('nome', 'Normal')} (Deck de Ameaça: {len(self.deck)} cartas)")

    # ── PROPRIEDADES ──────────────────────────────────────────────────
    @property
    def heroi_atual(self):
        if not self.herois:
            return None
        if self.heroi_atual_idx >= len(self.herois):
            self.heroi_atual_idx = 0
        return self.herois[self.heroi_atual_idx]

    # ── CONFIG PADRÃO ─────────────────────────────────────────────────
    def _default_config(self):
        from ...personagens.novos_personagens import Stark
        return {
            "herois": [("Stark", Stark)],
            "dificuldade": {
                "nome": "Normal",
                "pedregulhos": 8,
                "tesouro": 20,
                "reserva": 10,
            },
        }

    # ── HELPERS ───────────────────────────────────────────────────────
    def _narrativa(self, tipo):
        self.narrativa = random.choice(NAR.get(tipo, NAR["cerco"]))

    def _push(self, tipo, msg):
        print(f"[{tipo}] {msg}", flush=True)
        self.log.append((tipo, msg))
        if len(self.log) > 80:
            self.log.pop(0)

    def _feedback(self, msg, cor=C_VERDE):
        self.msg_feedback = msg
        self.msg_cor = cor
        self.feedback_timer = 120

    # ── ANIMAÇÃO DE CAMINHADA ─────────────────────────────────────────
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

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self):
        e = self.estado
        c_invasores = dict(e["invasores"])
        c_invasores["_brutamontes"] = e.get("brutamontes", 0)
        c_invasores["_infiltradores"] = e.get("infiltradores", 0)
        if (
            not hasattr(self, "_ultimo_estado_invasores")
            or self._ultimo_estado_invasores != c_invasores
        ):
            self._ultimo_estado_invasores = c_invasores
            self._sincronizar_inimigos_tabuleiro()

        self.timer = (self.timer + 1) % 120
        self._update_walk()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        self.motor.angulo_rotacao = self.game.angulo_rotacao

        ang = self.game.angulo_rotacao
        zm = self.zoom
        if not hasattr(self, '_ultimo_angulo') or self._ultimo_angulo != ang:
            self._ultimo_angulo = ang
            self.map_backbuffer_sujo = True
        if not hasattr(self, '_ultimo_zoom') or self._ultimo_zoom != zm:
            self._ultimo_zoom = zm
            self.map_backbuffer_sujo = True

        curr_dep = self.estado.get("recursos_depositados", {})
        if not hasattr(self, '_ultimo_recursos') or self._ultimo_recursos != curr_dep:
            self._ultimo_recursos = dict(curr_dep)
            self.map_backbuffer_sujo = True

        curr_pedras = self.estado.get("pedregulhos", 8)
        if not hasattr(self, '_ultimo_pedregulhos') or self._ultimo_pedregulhos != curr_pedras:
            self._ultimo_pedregulhos = curr_pedras
            self.map_backbuffer_sujo = True

        curr_tot_ini = self.estado.get("total_inimigos_gerados", 0)
        if not hasattr(self, '_ultimo_total_inimigos') or self._ultimo_total_inimigos != curr_tot_ini:
            self._ultimo_total_inimigos = curr_tot_ini
            self.map_backbuffer_sujo = True

        if (
            hasattr(self, 'animacoes_cartas_compra')
            and self.animacoes_cartas_compra
        ):
            for anim in self.animacoes_cartas_compra:
                if anim.get('finalizada', False):
                    continue
                if anim.get('delay', 0) > 0:
                    anim['delay'] -= 1
                    continue
                anim['progresso'] += 0.05
                if anim['progresso'] >= 1.0:
                    anim['progresso'] = 1.0
                    anim['finalizada'] = True

        # ── IA do Filho do Imperador (inimigo comandante) ─────────────────
        # Quando a fase é TURNO_FILHO_IMPERADOR, a IA processa sua fila de ações
        ia_cmd = getattr(self, 'ia_comandante', None)
        if ia_cmd is not None and self.fase == "TURNO_FILHO_IMPERADOR":
            if not ia_cmd.esta_ativo:
                # Inicia o turno inimigo
                ia_cmd.iniciar_turno()
            else:
                ia_cmd.update()
        # Decrementa banner do inimigo
        if ia_cmd is not None and getattr(ia_cmd, 'banner_timer', 0) > 0:
            ia_cmd.banner_timer -= 1

        # ── Verificação de vitória pelo boss (Mão Rei) ────────────────────
        if self.estado.get("mao_rei_spawnou") and not self.estado.get("vitoria") and not self.estado.get("derrota"):
            self._verificar_vitoria_boss()

        # ── AutoPlay Bot ─────────────────────────────────────────────────
        if self.autoplay_ativo and self.bot_heroi is not None:
            self.bot_heroi.update()

    # ── AUTOPLAY TOGGLE ───────────────────────────────────────────────
    def _toggle_autoplay(self):
        """Ativa/desativa o modo AutoPlay. Cria ou destrói o BotHeroi."""
        self.autoplay_ativo = not self.autoplay_ativo
        if self.autoplay_ativo:
            self.bot_heroi = BotHeroi(self, velocidade=self.autoplay_velocidade)
            self._push("SISTEMA", "🤖 [BOT] AutoPlay ATIVADO! Bot assumiu o controle dos heróis.")
            self._feedback("🤖 AutoPlay ON — Bot jogando!", (60, 200, 80))
        else:
            self.bot_heroi = None
            self._push("SISTEMA", "🤖 [BOT] AutoPlay DESATIVADO.")
            self._feedback("AutoPlay OFF", (180, 100, 60))

    def _set_autoplay_velocidade(self, vel: str):
        """Altera a velocidade do bot (lento/normal/rapido)."""
        self.autoplay_velocidade = vel
        if self.bot_heroi is not None:
            self.bot_heroi.velocidade = vel
        self._feedback(f"🤖 Bot: velocidade '{vel}'", (80, 200, 120))
