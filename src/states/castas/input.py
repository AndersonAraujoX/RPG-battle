"""
castas_input.py — Mixin de input para CastasState

Heróis usam os mesmos controles do Cerco.
Diretor (jogador 2) tem controles próprios:
  - Fase TURNO_DIRETOR:
      · Painel lateral: lista de castas disponíveis para clicar
      · Após escolher casta → clique no mapa para escolher zona
      · Botão "Encerrar Turno do Diretor"
"""
from __future__ import annotations
import pygame

from .data import (
    MODO_NENHUM, MODO_DIR_ESCOLHER_CASTA, MODO_DIR_ESCOLHER_ZONA,
    C_VERDE, C_PERIGO, C_OURO, C_HEROI, C_DIRETOR, C_TEXTO,
)


class CastasStateInputMixin:

    # ── HANDLE EVENTS PRINCIPAL ───────────────────────────────────────────
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.game.rodando = False
                return

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(pygame.mouse.get_pos())

            if event.type == pygame.MOUSEWHEEL:
                self.zoom = max(0.5, min(2.0, self.zoom + event.y * 0.1))
                self.map_backbuffer_sujo = True

    # ── TECLADO ───────────────────────────────────────────────────────────
    def _handle_keydown(self, event):
        from src.config import ESTADO_JOGO_MENU_PRINCIPAL
        if event.key == pygame.K_ESCAPE:
            self.game.castas_state = None
            self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL

        # Atalhos de modo (heróis) — delega para _on_key herdado do cerco/input
        if self.fase == "JOGAR_CARTA":
            if event.key == pygame.K_SPACE:
                self._fim_turno_heroi()
            else:
                # Passa para o handler de teclado do Cerco (modos de ação)
                if hasattr(self, '_on_key'):
                    self._on_key(event.key)


    # ── CLIQUE ────────────────────────────────────────────────────────────
    def _handle_click(self, mouse):
        # Fase FIM
        if self.fase == "FIM":
            from src.config import ESTADO_JOGO_MENU_PRINCIPAL
            self.game.castas_state = None
            self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
            return

        # Fase TURNO_DIRETOR
        if self.fase == "TURNO_DIRETOR":
            self._handle_click_diretor(mouse)
            return

        # Fase FASE_AMEAÇA
        if self.fase == "FASE_AMEACA":
            if hasattr(self, 'btn_resolver_rect') and self.btn_resolver_rect.collidepoint(mouse):
                self._resolver_carta_cerco()
            return

        # Fase JOGAR_CARTA — delega para o Cerco via métodos herdados
        self._handle_click_heroi(mouse)

    # ── INPUT DO DIRETOR ─────────────────────────────────────────────────
    def _handle_click_diretor(self, mouse):
        """Trata cliques durante o turno do Diretor."""
        # Botão encerrar
        if hasattr(self, 'btn_diretor_encerrar') and self.btn_diretor_encerrar.collidepoint(mouse):
            self._concluir_turno_diretor()
            return

        # Clique na lista de castas (painel lateral)
        if hasattr(self, 'casta_panel_rects'):
            for inseto_id, rect in self.casta_panel_rects.items():
                if rect.collidepoint(mouse):
                    self.casta_selecionada = inseto_id
                    self.modo_acao = MODO_DIR_ESCOLHER_ZONA
                    from src.cerco_isectum import DADOS_INIMIGOS
                    dados = DADOS_INIMIGOS.get(inseto_id, {})
                    self._feedback(
                        f"Casta selecionada: {dados.get('emoji','')} {dados.get('nome', inseto_id)}. "
                        "Clique no mapa para escolher a zona de invasão.",
                        C_DIRETOR,
                    )
                    return

        # Clique no mapa isométrico para escolher zona
        if self.modo_acao == MODO_DIR_ESCOLHER_ZONA and self.casta_selecionada:
            zona_id = self._zona_pelo_clique(mouse)
            if zona_id:
                self._diretor_usar_acao_inseto(self.casta_selecionada, zona_id)
            else:
                self._feedback("Clique em uma zona de borda do mapa para invadir!", C_PERIGO)

    def _zona_pelo_clique(self, mouse):
        """Retorna o id da zona clicada no mapa isométrico."""
        if not hasattr(self, '_zona_rects_mapa') or not self._zona_rects_mapa:
            return None
        for zona_id, rect in self._zona_rects_mapa.items():
            if rect.collidepoint(mouse):
                return zona_id
        return None

    # ── INPUT DOS HERÓIS (reutiliza lógica do Cerco) ─────────────────────
    def _handle_click_heroi(self, mouse):
        """Cliques durante o turno dos heróis — delega para o método _on_click do Cerco."""
        # _on_click está definido em cerco/input.py e herdado pela MRO de CastasState
        self._on_click(mouse)
