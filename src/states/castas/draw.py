"""
castas_draw.py — Mixin de renderização para CastasState

Herda CercoStateDrawMixin e sobrescreve apenas:
  - draw() para adicionar o painel do Diretor e overlay de casta
  - _draw_header() para mostrar título e indicador de turno Diretor
  - _draw_painel_diretor() novo painel com lista de castas disponíveis
"""
from __future__ import annotations
import pygame

from ..cerco.draw import CercoStateDrawMixin
from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_BG, C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_INSETO, C_TEXTO, C_DIM, C_HEROI, C_DIRETOR,
    MODO_DIR_ESCOLHER_CASTA, MODO_DIR_ESCOLHER_ZONA,
)

# Zonas válidas para o Diretor invadir
ZONAS_BORDA = [
    "campo_norte", "campo_sul", "campo_oeste", "campo_leste",
    "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
    "torre_nw", "torre_ne", "torre_sw", "torre_se",
]


class CastasStateDrawMixin(CercoStateDrawMixin):
    """Herda todo o draw do Cerco e adiciona camadas do modo Castas."""

    # ── DRAW PRINCIPAL ────────────────────────────────────────────────────
    def draw(self, tela):
        self._setup_layout()
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)

        # Brilho de fundo roxo (diferencia visualmente do Cerco)
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (80, 20, 130, 18), (W // 5, H // 4), 320)
        pygame.draw.circle(glow, (20, 60, 10,  12), (W * 4 // 5, H * 3 // 4), 260)
        tela.blit(glow, (0, 0))

        self._draw_header(tela, W)
        self._draw_mapa(tela)

        if self.fase == "TURNO_DIRETOR":
            self._draw_painel_diretor(tela, W, H)
        else:
            self._draw_painel_lateral(tela)

        # Botões de ação (heróis) só aparecem quando não é turno do Diretor
        if self.fase != "TURNO_DIRETOR":
            self._draw_mao(tela)
            self._draw_botoes_acao(tela, W, H)

        if self.fase == "FASE_AMEACA" and self.carta_cerco:
            self._draw_carta_overlay(tela, W, H)

        if self.feedback_timer > 0:
            self._draw_feedback(tela, W, H)

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self._draw_fim(tela, W, H)

    # ── HEADER SOBRESCRITO ────────────────────────────────────────────────
    def _draw_header(self, tela, W):
        bar = pygame.Surface((W, 62), pygame.SRCALPHA)
        bar.fill((10, 5, 22, 220))
        tela.blit(bar, (0, 0))
        pygame.draw.line(tela, C_BORDA, (0, 62), (W, 62), 1)

        # Título
        t1 = self.fG.render("CASTAS DOS", True, C_ACENTO)
        t2 = self.fG.render("ISECTUM", True, C_OURO)
        tela.blit(t1, (14, 10))
        tela.blit(t2, (14 + t1.get_width() + 8, 10))

        # Rodada e fase
        rodada = self.estado.get("rodada", 1)
        fase_txt = {
            "JOGAR_CARTA":   "Turno dos Heróis",
            "TURNO_DIRETOR": "🐛 Turno do Diretor",
            "FASE_AMEACA":   "⚠ Fase de Ameaça",
            "FIM":           "FIM",
        }.get(self.fase, self.fase)
        cor_fase = C_DIRETOR if self.fase == "TURNO_DIRETOR" else C_HEROI
        rf = self.fM.render(f"Rodada {rodada}  |  {fase_txt}", True, cor_fase)
        tela.blit(rf, (W // 2 - rf.get_width() // 2, 12))

        # HUD recursos (canto direito)
        e = self.estado
        stats = [
            (f"🏆 {e.get('tesouro', 0)}", C_OURO),
            (f"🛡 {e.get('reserva', 0)}", C_HEROI),
        ]
        if self.fase == "TURNO_DIRETOR":
            acoes = e.get("acoes_diretor", 0)
            stats.append((f"🐛 {acoes} ações", C_DIRETOR))
        rx = W - 20
        for txt, cor in reversed(stats):
            s = self.fP.render(txt, True, cor)
            rx -= s.get_width() + 16
            tela.blit(s, (rx, 22))

        # Mini avatares dos heróis
        bx, by, bh = W // 2 + 140, 8, 30
        av_size = 22
        for idx, h in enumerate(self.herois):
            hx = bx + idx * (av_size + 8)
            h_rect = pygame.Rect(hx, by + (bh - av_size) // 2, av_size, av_size)
            is_ativo = (h is self.heroi_atual) and self.fase == "JOGAR_CARTA"
            cor_b = C_VERDE if is_ativo else C_BORDA
            pygame.draw.rect(tela, (8, 8, 16), h_rect, border_radius=3)
            img_key = f"personagem_{h.nome.lower()}"
            img = self.game.imagens.get(img_key)
            if img and h.nome != "Aquele":
                tela.blit(pygame.transform.scale(img, (av_size-2, av_size-2)), (h_rect.x+1, h_rect.y+1))
            else:
                fb = self.fMi.render(h.nome[0], True, C_TEXTO)
                tela.blit(fb, (h_rect.centerx - fb.get_width()//2, h_rect.centery - fb.get_height()//2))
            pygame.draw.rect(tela, cor_b, h_rect, 2 if is_ativo else 1, border_radius=3)

    # ── PAINEL DO DIRETOR ────────────────────────────────────────────────
    def _draw_painel_diretor(self, tela, W, H):
        """Painel lateral com lista de castas que o Diretor pode enviar."""
        from src.cerco_isectum import DADOS_INIMIGOS

        px = W - 318
        py = 65
        pw = 310
        ph = H - 75
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 8, 30, 220))
        tela.blit(panel, (px, py))
        pygame.draw.rect(tela, C_BORDA, (px, py, pw, ph), 1, border_radius=4)

        # Título do painel
        acoes = self.estado.get("acoes_diretor", 0)
        tt = self.fM.render(f"🐛 DIRETOR — {acoes} ação(ões)", True, C_DIRETOR)
        tela.blit(tt, (px + 10, py + 10))
        pygame.draw.line(tela, C_BORDA, (px + 8, py + 34), (px + pw - 8, py + 34), 1)

        inst = self.fMi.render(
            "Selecione uma casta e clique no mapa" if self.casta_selecionada is None
            else f"Casta: {DADOS_INIMIGOS.get(self.casta_selecionada, {}).get('nome', '')} | Clique na zona",
            True, C_DIM if self.casta_selecionada is None else C_OURO,
        )
        tela.blit(inst, (px + 8, py + 38))

        # Lista de castas
        mouse = pygame.mouse.get_pos()
        self.casta_panel_rects = {}
        cy = py + 60
        row_h = 44

        all_castas = list(DADOS_INIMIGOS.items())
        max_visivel = (ph - 80) // row_h

        for i, (inseto_id, dados) in enumerate(all_castas[:max_visivel]):
            row_rect = pygame.Rect(px + 6, cy, pw - 12, row_h - 4)
            self.casta_panel_rects[inseto_id] = row_rect

            sel    = (inseto_id == self.casta_selecionada)
            hover  = row_rect.collidepoint(mouse)
            cor_bg = (40, 12, 70) if sel else ((22, 10, 40) if hover else (14, 6, 24))
            cor_bd = C_ACENTO if sel else (C_INSETO if hover else C_BORDA)

            pygame.draw.rect(tela, cor_bg, row_rect, border_radius=6)
            pygame.draw.rect(tela, cor_bd, row_rect, 2 if sel else 1, border_radius=6)

            # Emoji + nome
            emoji = dados.get("emoji", "🐛")
            nome  = dados.get("nome", inseto_id)
            classe = dados.get("classe", "")
            nt = self.fP.render(f"{emoji}  {nome}", True, C_OURO if sel else C_TEXTO)
            tela.blit(nt, (row_rect.x + 8, row_rect.y + 6))
            ct = self.fMi.render(classe, True, C_ACENTO if sel else C_DIM)
            tela.blit(ct, (row_rect.x + 8, row_rect.y + 24))

            cy += row_h

        # Botão encerrar turno
        btn_y = H - 52
        self.btn_diretor_encerrar = pygame.Rect(px + 8, btn_y, pw - 16, 38)
        hover_enc = self.btn_diretor_encerrar.collidepoint(mouse)
        cor_enc_bg = (80, 20, 30) if hover_enc else (50, 10, 20)
        cor_enc_bd = (255, 80, 80) if hover_enc else C_PERIGO
        pygame.draw.rect(tela, cor_enc_bg, self.btn_diretor_encerrar, border_radius=8)
        pygame.draw.rect(tela, cor_enc_bd, self.btn_diretor_encerrar, 2, border_radius=8)
        enc_t = self.fM.render("⏭  Encerrar Turno do Diretor", True, C_TEXTO)
        tela.blit(enc_t, (
            self.btn_diretor_encerrar.centerx - enc_t.get_width() // 2,
            self.btn_diretor_encerrar.centery - enc_t.get_height() // 2,
        ))

        # Zona clicável highlight no mapa (para MODO_DIR_ESCOLHER_ZONA)
        if self.modo_acao == MODO_DIR_ESCOLHER_ZONA:
            self._highlight_zonas_borda(tela)

    def _highlight_zonas_borda(self, tela):
        """Destaca visualmente as zonas válidas para invasão no mapa."""
        from src.resolvedor_acoes import ZONAS_GRID
        self._zona_rects_mapa = {}

        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            if zona_id not in ZONAS_BORDA:
                continue
            # Converte coordenadas de grid para tela usando iso_to_screen
            pts = []
            for gx, gy in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:
                sx, sy = self._grid_to_screen(gx, gy)
                pts.append((sx, sy))
            if len(pts) >= 3:
                s = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
                pygame.draw.polygon(s, (200, 80, 255, 60), pts)
                pygame.draw.polygon(s, (200, 80, 255, 200), pts, 2)
                tela.blit(s, (0, 0))
                # Cria rect AABB para hit-testing
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                self._zona_rects_mapa[zona_id] = pygame.Rect(
                    min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)
                )

    def _grid_to_screen(self, gx, gy):
        """Converte posição de grid para posição na tela (iso)."""
        mr = self.mapa_rect
        CELL = 48
        ox = mr.x + mr.width // 2
        oy = mr.y + 40
        sx = ox + (gx - gy) * CELL * self.zoom // 2
        sy = oy + (gx + gy) * CELL * self.zoom // 4
        return int(sx), int(sy)
