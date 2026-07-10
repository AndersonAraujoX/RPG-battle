"""
castas_state.py — Estado Pygame Principal: Modo Castas dos Isectum

Herda de CercoState mas substitui:
  - Inimigos: castas específicas dos Insectum (24 tipos com habilidades)
  - Turno do Diretor: jogador humano envia castas para zonas
  - Renderização: painel do Diretor com lista de castas

Fluxo assimétrico:
  JOGAR_CARTA (heróis) → TURNO_DIRETOR (player 2) → FASE_AMEACA → repeat
"""
from __future__ import annotations
import random
import copy
import pygame

from ..cerco.state import CercoState
from ..state_base import GameState
from ...cerco_isectum import (
    criar_estado, criar_deck, CARTAS_BASICAS, NOMES_ZONA,
)
from ...resolvedor_acoes import ZONAS_GRID
from ...config import ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA

from .data import (
    ESTADO_JOGO_CASTAS, ESTADO_JOGO_CASTAS_SETUP,
    C_VERDE, C_PERIGO, C_OURO, C_HEROI, C_DIRETOR,
    MODO_NENHUM, MODO_DIR_ESCOLHER_CASTA, MODO_DIR_ESCOLHER_ZONA,
    DIFICULDADES_CASTAS,
)
from .draw  import CastasStateDrawMixin
from .input import CastasStateInputMixin
from .enemy import CastasEnemyMixin
from .turn  import CastasStateTurnMixin


class CastasState(
    CastasStateDrawMixin,   # sobrescreve draw/header/painel_diretor
    CastasStateInputMixin,  # sobrescreve handle_events + input do diretor
    CastasEnemyMixin,       # sobrescreve _sincronizar_inimigos_tabuleiro
    CastasStateTurnMixin,   # sobrescreve _fim_turno_heroi, turno diretor, fase ameaça
    CercoState,             # base: tabuleiro, heróis, mapa, cartas, mercado, combate
):
    """Estado completo do modo Castas dos Isectum — 2 jogadores assimétrico."""

    def __init__(self, game, config=None):
        # Resolve config antes de chamar super().__init__
        if config is None:
            from ...personagens.novos_personagens import Stark
            config = {
                "herois":       [("Stark", Stark)],
                "dificuldade":  DIFICULDADES_CASTAS[1],   # normal
            }

        # Adapta dificuldade para o formato esperado pelo CercoState
        diff_raw = config.get("dificuldade", {})
        config_cerco = {
            "herois":      config.get("herois", []),
            "dificuldade": {
                "nome":        diff_raw.get("nome", "Guardião"),
                "pedregulhos": diff_raw.get("pedregulhos", 8),
                "tesouro":     diff_raw.get("tesouro", 20),
                "reserva":     diff_raw.get("reserva", 10),
            },
        }

        # Inicializa o CercoState (tabuleiro, heróis, deck, motor, cartas...)
        super().__init__(game, config_cerco)

        # Guarda config original com acoes_dir etc.
        self.config = config

        # Estado adicional do Diretor
        self.casta_selecionada = None
        self.modo_acao = MODO_NENHUM
        self._zona_rects_mapa  = {}
        self.casta_panel_rects = {}

        # Adiciona campos de estado para o modo Castas
        from ...cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {
            "castas_invasoras": {},    # zona_id → inseto_id
            "zonas_bloqueadas": [],    # zonas sem trabalho nesta rodada
            "acoes_diretor":    diff_raw.get("acoes_dir", 3),
        })

        self._push("SISTEMA", "🐛 Modo Castas dos Isectum — 2 jogadores assimétrico!")
        self._push("SISTEMA", "Heróis: usem cartas para defender a fortaleza.")
        self._push("SISTEMA", "Diretor: envie castas para invadir e atacar.")

    # ── PROPRIEDADE: heroi_atual ────────────────────────────────────────
    # (herdada de CercoState)

    # ── OVERRIDE: título do log inicial ───────────────────────────────
    # CercoState já chama _push em __init__, basta adicionar no nosso __init__

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self):
        """Delega para CercoState.update() (sincronização, animações, etc.)"""
        # Importa CercoState.update sem executar o de CastasState
        CercoState.update(self)
