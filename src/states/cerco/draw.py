"""
draw.py — Rendering Mixin principal do CercoState.
Composto pelos sub-mixins:
- CercoDrawMapMixin   (draw_map.py)   : Renderização de mapa isométrico, polígonos, texturas e unidades
- CercoDrawPanelMixin (draw_panel.py) : Renderização do painel lateral, mercado de upgrades e log
- CercoDrawCardsMixin (draw_cards.py) : Renderização da mão de cartas e overlays de ameça
- CercoDrawUIMixin    (draw_ui.py)    : Renderização de fontes, layout, cabeçalho, botões, modais e banners
"""
from __future__ import annotations
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_CERCO, C_TEXTO, C_DIM,
)
from .draw_map import CercoDrawMapMixin
from .draw_panel import CercoDrawPanelMixin
from .draw_cards import CercoDrawCardsMixin
from .draw_ui import CercoDrawUIMixin


class CercoStateDrawMixin(
    CercoDrawMapMixin,
    CercoDrawPanelMixin,
    CercoDrawCardsMixin,
    CercoDrawUIMixin
):
    """Mixin principal de renderização gráfica para o estado de cerco."""

    def draw(self, tela: pygame.Surface):
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill((10, 12, 22))

        # 1. Renderiza o mapa tático 2D/isométrico
        self._draw_mapa(tela)

        # 2. Renderiza a barra de cabeçalho
        self._draw_header(tela, W)

        # 3. Renderiza o painel lateral com mercado e log
        self._draw_painel_lateral(tela)

        # 4. Renderiza a mão de cartas do jogador
        self._draw_mao(tela)

        # 5. Renderiza botões de ação contextuais
        self._draw_botoes_acao(tela, W, H)

        # 6. Renderiza a carta sendo arrastada, se houver
        if self.dragging_card and self.drag_card_idx is not None:
            self._draw_carta_overlay_drag(tela)

        # 7. Modais, overlays de ameaça, banners e dev menu
        if self.fase == "ESCOLHER_DRAFT_RECOMPENSA" and getattr(self, "draft_opcoes", None):
            self._draw_modal_draft_recompensa(tela, W, H)

        if self.fase == "FASE_AMEACA" and self.carta_cerco:
            self._draw_carta_overlay(tela, W, H)

        if self.fase == "ESCOLHER_ACAO_CARTA" and 0 <= self.idx_carta_sendo_jogada < len(self.estado["mao"]):
            self._draw_modal_escolha_carta(tela, W, H)

        if self.feedback_timer > 0:
            self._draw_feedback(tela, W, H)

        # Banner de Turno do Príncipe Lysander
        self._draw_ia_turno_banner(tela, W, H)

        if self.fase in ("VITORIA", "DERROTA"):
            self._draw_fim(tela, W, H)

        if getattr(self, 'exibindo_dev_menu', False):
            self._desenhar_dev_menu(tela)

    def _draw_carta_overlay_drag(self, tela):
        """Renderiza a carta que está sendo arrastada no cursor do mouse."""
        if self.drag_card_idx is None or self.drag_card_idx >= len(self.estado["mao"]):
            return
        carta = self.estado["mao"][self.drag_card_idx]
        mx, my = pygame.mouse.get_pos()
        cw, ch = 96, self.mao_rect.height - 8
        cx = mx - cw // 2
        cy = my - ch // 2
        
        crect = pygame.Rect(cx, cy, cw, ch)
        
        # Fundo arrastando
        pygame.draw.rect(tela, (40, 40, 60), crect, border_radius=7)
        pygame.draw.rect(tela, C_ACENTO, crect, 2, border_radius=7)
        
        nome_s = self.fMi.render(carta["nome"][:14], True, C_OURO)
        tela.blit(nome_s, (crect.centerx - nome_s.get_width() // 2, crect.y + 10))
        
        desc = carta.get("descricao", "")
        if desc:
            lbl_desc = self.fMi.render(desc[:18], True, C_DIM)
            tela.blit(lbl_desc, (crect.centerx - lbl_desc.get_width() // 2, crect.y + 30))
