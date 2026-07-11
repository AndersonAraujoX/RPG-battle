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

        # Múltiplos Filhos do Imperador
        self.num_diretores = config.get("num_diretores", 1)
        self.controle_filhos = config.get("controle_filhos", "humano")
        self.diretores = [f"Filho {i+1}" for i in range(self.num_diretores)]
        self.timer_diretor_bot = 0

        # Estado adicional do Filho do Imperador
        self.casta_selecionada = None
        self.modo_acao = MODO_NENHUM
        self._zona_rects_mapa  = {}
        self.diretor_carta_rects = []

        # Inicializa Decks e Mãos individuais para cada Filho do Imperador
        from src.cerco_isectum import DADOS_INIMIGOS
        maos_dir = {}
        decks_dir = {}
        descarte_dir = {}
        acoes_dir = {}

        # Determina o tamanho da mão baseado na dificuldade (padrão: 3)
        tam_mao_dir = 3
        if diff_raw.get("id") == "facil":
            tam_mao_dir = 2
        elif diff_raw.get("id") == "dificil":
            tam_mao_dir = 4

        acoes_inicial = diff_raw.get("acoes_dir", 3)

        for d_nome in self.diretores:
            pool = list(DADOS_INIMIGOS.keys()) * 2
            random.shuffle(pool)
            
            # Mão
            mao = []
            for _ in range(tam_mao_dir):
                if pool:
                    mao.append(pool.pop())
            
            maos_dir[d_nome] = mao
            decks_dir[d_nome] = pool
            descarte_dir[d_nome] = []
            acoes_dir[d_nome] = acoes_inicial

        # Adiciona campos de estado para o modo Castas
        from ...cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {
            "castas_invasoras": {},    # zona_id → inseto_id
            "zonas_bloqueadas": [],    # zonas sem trabalho nesta rodada
            "maos_diretores":   maos_dir,
            "decks_diretores":  decks_dir,
            "descarte_diretores": descarte_dir,
            "acoes_diretores":  acoes_dir,
            "diretor_ativo_idx": 0,
        })

        self._push("SISTEMA", f"🐛 Modo Castas — Jogando contra {self.num_diretores} Filho(s) do Imperador!")
        self._push("SISTEMA", "Defenda a fortaleza contra as invasões e vença no Duelo!")

    # ── PROPRIEDADE: heroi_atual ────────────────────────────────────────
    # (herdada de CercoState)

    # ── OVERRIDE: título do log inicial ───────────────────────────────
    # CercoState já chama _push em __init__, basta adicionar no nosso __init__

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self):
        """Delega para CercoState.update() e roda a IA para o turno dos Filhos do Imperador."""
        CercoState.update(self)

        # Se for o turno de algum bot Filho do Imperador e o controle for I.A.
        if self.fase == "TURNO_DIRETOR" and self.controle_filhos == "ia":
            idx = self.estado.get("diretor_ativo_idx", 0)
            if idx < len(self.diretores):
                ativo = self.diretores[idx]
                acoes = self.estado["acoes_diretores"].get(ativo, 0)

                if acoes > 0:
                    self.timer_diretor_bot += 1
                    if self.timer_diretor_bot >= 40: # Pequeno atraso visual de ~0.7s
                        self.timer_diretor_bot = 0
                        
                        # IA joga uma carta de sua mão
                        mao = self.estado["maos_diretores"].get(ativo, [])
                        if mao:
                            import random
                            inseto_id = random.choice(mao)
                            
                            # Define o campo de spawn com base no índice do Filho
                            campos = ["campo_norte", "campo_sul", "campo_oeste", "campo_leste"]
                            zona_spawn = campos[idx % len(campos)]
                            
                            # Executa ação de spawn
                            self._diretor_usar_acao_inseto_multi(ativo, inseto_id, zona_spawn)
                        else:
                            # Sem cartas, passa
                            self._concluir_turno_diretor()
                else:
                    self._concluir_turno_diretor()
