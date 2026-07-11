"""
castas_input.py — Mixin de input para CastasState

Heróis usam os mesmos controles do Cerco.
Filho do Imperador (jogador 2) tem controles próprios:
  - Fase TURNO_DIRETOR:
      · Mão inferior: cartas de castas disponíveis para jogar
      · Após escolher carta → clique no mapa para escolher zona de spawn
      · Botão "Encerrar Turno do Filho do Imperador"
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
        # Se for Turno do Filho do Imperador, processamos localmente
        if self.fase == "TURNO_DIRETOR":
            for event in events:
                if event.type == pygame.QUIT:
                    self.game.rodando = False
                    return

                if event.type == pygame.KEYDOWN:
                    # Filho do Imperador volta ao menu com ESC
                    if event.key == pygame.K_ESCAPE:
                        from src.config import ESTADO_JOGO_MENU_PRINCIPAL
                        self.game.castas_state = None
                        self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
                        return
                    # Filho do Imperador encerra turno com Enter
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self._concluir_turno_diretor()
                        return

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.controle_filhos == "humano":
                        self._handle_click_diretor(pygame.mouse.get_pos())
                    return

                if event.type == pygame.MOUSEWHEEL:
                    self.zoom = max(0.5, min(2.0, self.zoom + event.y * 0.1))
                    self.map_backbuffer_sujo = True
        else:
            # Caso contrário (Turno dos Heróis, Escolha de Ação, Ameaça),
            # delegamos inteiramente ao resolvedor do Cerco para que modais e cartas funcionem.
            from src.states.cerco.input import CercoStateInputMixin
            
            # Interceptamos apenas o ESC para sair
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    from src.config import ESTADO_JOGO_MENU_PRINCIPAL
                    self.game.castas_state = None
                    self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
                    return

            CercoStateInputMixin.handle_events(self, events)

    # ── INPUT DO FILHO DO IMPERADOR ──────────────────────────────────────
    def _handle_click_diretor(self, mouse):
        """Trata cliques durante o turno do Filho do Imperador."""
        # Botão encerrar
        if hasattr(self, 'btn_diretor_encerrar') and self.btn_diretor_encerrar.collidepoint(mouse):
            self._concluir_turno_diretor()
            return

        # Clique nas cartas da mão do Filho do Imperador ativo (parte inferior da tela)
        if hasattr(self, 'diretor_carta_rects') and self.diretor_carta_rects:
            for inseto_id, rect in self.diretor_carta_rects:
                if rect.collidepoint(mouse):
                    self.casta_selecionada = inseto_id
                    self.modo_acao = MODO_DIR_ESCOLHER_ZONA
                    from src.cerco_isectum import DADOS_INIMIGOS
                    dados = DADOS_INIMIGOS.get(inseto_id, {})
                    self._feedback(
                        f"Casta selecionada: {dados.get('emoji','')} {dados.get('nome', inseto_id)}. "
                        "Clique em uma zona externa do mapa para spawnar!",
                        C_DIRETOR,
                    )
                    return

        # Clique no mapa isométrico para escolher zona
        if self.modo_acao == MODO_DIR_ESCOLHER_ZONA and self.casta_selecionada:
            zona_id = self._zona_pelo_clique(mouse)
            if zona_id:
                # Pega o Filho ativo correspondente do turno
                idx = self.estado.get("diretor_ativo_idx", 0)
                ativo = self.diretores[idx] if idx < len(self.diretores) else self.diretores[0]
                self._diretor_usar_acao_inseto_multi(ativo, self.casta_selecionada, zona_id)
            else:
                self._feedback("Clique em um dos Campos Externos destacados no mapa!", C_PERIGO)

    def _zona_pelo_clique(self, mouse):
        """Retorna o id da zona clicada no mapa isométrico."""
        if not hasattr(self, '_zona_rects_mapa') or not self._zona_rects_mapa:
            return None
        for zona_id, rect in self._zona_rects_mapa.items():
            if rect.collidepoint(mouse):
                return zona_id
        return None
