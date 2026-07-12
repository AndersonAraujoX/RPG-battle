"""
cerco_state_draw.py — Mixin de renderização para CercoState.

Extraído de cerco_state.py para reduzir o monolito (~1800 linhas de draw).
"""
from __future__ import annotations
import math
import random
import zlib
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_BG, C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_CERCO, C_TEXTO, C_DIM, C_INVASOR, C_BRUTE, C_HEROI,
    ZONA_TERRENO_MAP, NAR,
    MODO_NENHUM, MODO_MOVER, MODO_TRABALHAR, MODO_ESCAVAR,
    MODO_SUBORNAR, MODO_UPGRADE, MODO_CONVOCAR, MODO_ATACAR, MODO_ATIRAR,
)


class CercoStateDrawMixin:
    """Mixin com todos os métodos de renderização usados por CercoState."""

    # ── FONTS ────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        s = max(0.5, ALTURA_TELA / 720.0)
        self.fT  = pygame.font.Font(None, max(16, int(48 * s)))
        self.fG  = pygame.font.Font(None, max(14, int(36 * s)))
        self.fM  = pygame.font.Font(None, max(12, int(28 * s)))
        self.fP  = pygame.font.Font(None, max(10, int(22 * s)))
        self.fMi = pygame.font.Font(None, max(8,  int(18 * s)))

    # ── LAYOUT ─────────────────────────────────────────────────────
    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        self.mapa_rect   = pygame.Rect(8, 65, W - 330, H - 217)
        self.painel_rect = pygame.Rect(W - 318, 65, 310, H - 75)
        self.mao_rect    = pygame.Rect(8, H - 146, W - 330, 138)
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

    # ── RENDERING UTILITIES ──────────────────────────────────────────────
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

    def _draw_celula_tactica(self, tela, gx, gy, el, cor_base, cor_borda, estilo='movimento'):
        pulso = (math.sin(self.timer * 0.1) + 1.0) / 2.0
        alpha_base = cor_base[3] if len(cor_base) > 3 else 70
        alpha = int(alpha_base - 20 + 40 * pulso)
        alpha = max(20, min(230, alpha))
        fill_color = (cor_base[0], cor_base[1], cor_base[2], alpha)
        
        theta = self.game.angulo_rotacao
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)
        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        r = self.mapa_rect
        CX = r.centerx
        CY = r.centery - 5

        def _iso_func(gx_, gy_, el_):
            dx = gx_ - 9.5
            dy = gy_ - 9.5
            rx = dx * theta_cos - dy * theta_sin
            ry = dx * theta_sin + dy * theta_cos
            sx = (rx - ry) * (TW // 2) + CX
            sy = (rx + ry) * (TH // 2) - el_ * ES + CY
            return int(sx), int(sy)

        p0 = _iso_func(gx - 0.5, gy - 0.5, el)
        p1 = _iso_func(gx + 0.5, gy - 0.5, el)
        p2 = _iso_func(gx + 0.5, gy + 0.5, el)
        p3 = _iso_func(gx - 0.5, gy + 0.5, el)
        pts_outer = [p0, p1, p2, p3]
        
        self._draw_alpha_polygon(tela, fill_color, pts_outer)
        r_b, g_b, b_b = cor_borda[:3]
        cor_borda_pulsante = (
            max(0, min(255, int(r_b * (0.8 + 0.3 * pulso)))),
            max(0, min(255, int(g_b * (0.8 + 0.3 * pulso)))),
            max(0, min(255, int(b_b * (0.8 + 0.3 * pulso))))
        )
        pygame.draw.polygon(tela, cor_borda_pulsante, pts_outer, 2)
        
        cx = (p0[0] + p1[0] + p2[0] + p3[0]) / 4
        cy = (p0[1] + p1[1] + p2[1] + p3[1]) / 4
        
        pts_inner = [
            (int(cx + 0.7 * (p0[0] - cx)), int(cy + 0.7 * (p0[1] - cy))),
            (int(cx + 0.7 * (p1[0] - cx)), int(cy + 0.7 * (p1[1] - cy))),
            (int(cx + 0.7 * (p2[0] - cx)), int(cy + 0.7 * (p2[1] - cy))),
            (int(cx + 0.7 * (p3[0] - cx)), int(cy + 0.7 * (p3[1] - cy)))
        ]
        cor_inner = (cor_borda[0], cor_borda[1], cor_borda[2], int(40 + 20 * pulso))
        self._draw_alpha_polygon(tela, cor_inner, pts_inner)
        pygame.draw.polygon(tela, cor_borda, pts_inner, 1)
        
        f = 1/7
        pygame.draw.line(tela, (255, 255, 255), p0, (int(p0[0] + f * (p3[0] - p0[0])), int(p0[1] + f * (p3[1] - p0[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p0, (int(p0[0] + f * (p1[0] - p0[0])), int(p0[1] + f * (p1[1] - p0[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p2, (int(p2[0] + f * (p3[0] - p2[0])), int(p2[1] + f * (p3[1] - p2[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p2, (int(p2[0] + f * (p1[0] - p2[0])), int(p2[1] + f * (p1[1] - p2[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p3, (int(p3[0] + f * (p0[0] - p3[0])), int(p3[1] + f * (p0[1] - p3[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p3, (int(p3[0] + f * (p2[0] - p3[0])), int(p3[1] + f * (p2[1] - p3[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p1, (int(p1[0] + f * (p0[0] - p1[0])), int(p1[1] + f * (p0[1] - p1[1]))), 2)
        pygame.draw.line(tela, (255, 255, 255), p1, (int(p1[0] + f * (p2[0] - p1[0])), int(p1[1] + f * (p2[1] - p1[1]))), 2)

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
        orig_w, orig_h = img.get_size()
        crop_w = int(orig_w * 0.82)
        crop_h = int(orig_h * 0.82)
        crop_x = (orig_w - crop_w) // 2
        crop_y = (orig_h - crop_h) // 2
        try:
            cropped_img = img.subsurface(pygame.Rect(crop_x, crop_y, crop_w, crop_h))
        except Exception:
            cropped_img = img
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

    # ── SLOT RECTS ───────────────────────────────────────────────────
    _slot_rects_cache: dict = {}

    def _slot_rect(self, slot_id):
        return self._slot_rects_cache.get(slot_id)

    def _calcular_pos_carta_na_mao(self, idx, total_cartas):
        mr = self.mao_rect
        total_cartas = max(1, total_cartas)
        espaco_reservado_esquerda = 230
        espaco_reservado_direita = 130
        largura_disponivel = mr.width - espaco_reservado_esquerda - espaco_reservado_direita
        cw = min(96, largura_disponivel // total_cartas)
        gap = max(2, (largura_disponivel - cw * total_cartas) // (total_cartas + 1))
        cx = mr.x + espaco_reservado_esquerda + gap + idx * (cw + gap)
        cy = mr.y + 4
        ch = mr.height - 8
        return cx, cy, cw, ch

    # ── POSIÇÕES VIRTUAIS E ANIMAÇÃO ─────────────────────────────────
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
            cy -= int(abs(math.sin(p * math.pi)) * 6 * self.zoom)
        return cx, cy

    # ═══════════════════════════════════════════════════════════════════
    # DRAW
    # ═══════════════════════════════════════════════════════════════════
    def draw(self, tela):
        self._setup_layout()
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)
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
        if getattr(self, "dev_menu_aberto", False):
            self._desenhar_dev_menu(tela)

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
        bx = W // 2 - 150
        by = 8
        bw = 300
        bh = 32
        pygame.draw.rect(tela, (14, 16, 30), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(tela, C_BORDA, (bx, by, bw, bh), 1, border_radius=6)
        av_size = 22
        for idx, h in enumerate(self.herois):
            hx = bx + 8 + idx * (av_size + 14)
            hy = by + (bh - av_size) // 2
            h_rect = pygame.Rect(hx, hy, av_size, av_size)
            eh_ativo = (h is self.heroi_atual)
            destaque = eh_ativo and (self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"))
            cor_b = C_VERDE if destaque else (C_ACENTO if eh_ativo else C_BORDA)
            pygame.draw.rect(tela, (8, 8, 16), h_rect, border_radius=3)
            if h.nome == "Aquele":
                fallback = self.fMi.render("\U0001f311", True, C_TEXTO)
                tela.blit(fallback, (h_rect.centerx - fallback.get_width() // 2, h_rect.centery - fallback.get_height() // 2))
            else:
                img_key = f"personagem_{h.nome.lower()}"
                img = self.game.imagens.get(img_key)
                if img:
                    img_scaled = pygame.transform.scale(img, (av_size - 2, av_size - 2))
                    tela.blit(img_scaled, (h_rect.x + 1, h_rect.y + 1))
                else:
                    fallback = self.fMi.render(h.nome[0], True, C_TEXTO)
                    tela.blit(fallback, (h_rect.centerx - fallback.get_width() // 2, h_rect.centery - fallback.get_height() // 2))
            pygame.draw.rect(tela, cor_b, h_rect, 2 if destaque else 1, border_radius=3)
            if destaque:
                pulse = abs(self.timer % 60 - 30) / 30.0
                rp = int(2 + 2 * pulse)
                pygame.draw.rect(tela, C_VERDE, h_rect.inflate(rp, rp), 1, border_radius=3)
        ax = bx + bw - 30
        ay = by + (bh - av_size) // 2
        a_rect = pygame.Rect(ax, ay, av_size, av_size)
        eh_ameaca = (self.fase == "FASE_AMEACA")
        cor_a = C_PERIGO if eh_ameaca else C_DIM
        pygame.draw.rect(tela, (20, 10, 10) if eh_ameaca else (10, 12, 16), a_rect, border_radius=3)
        pygame.draw.rect(tela, cor_a, a_rect, 2 if eh_ameaca else 1, border_radius=3)
        pygame.draw.circle(tela, cor_a, (a_rect.centerx, a_rect.centery - 2), 4)
        pygame.draw.rect(tela, cor_a, (a_rect.centerx - 3, a_rect.centery + 1, 6, 4))
        pygame.draw.circle(tela, (0, 0, 0), (a_rect.centerx - 2, a_rect.centery - 2), 1)
        pygame.draw.circle(tela, (0, 0, 0), (a_rect.centerx + 2, a_rect.centery - 2), 1)
        if eh_ameaca:
            pulse = abs(self.timer % 60 - 30) / 30.0
            rp = int(2 + 2 * pulse)
            pygame.draw.rect(tela, C_PERIGO, a_rect.inflate(rp, rp), 1, border_radius=3)
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
        nome_exibido = "?????" if (self.heroi_atual and self.heroi_atual.nome == "Aquele") else (self.heroi_atual.nome if self.heroi_atual else "?")
        if len(self.herois) > 1:
            heroi_info = f"Heroi: {nome_exibido} [{self.heroi_atual_idx + 1}/{len(self.herois)}]  [TAB]"
        else:
            heroi_info = f"Heroi: {nome_exibido}"
        ph = self.fMi.render(heroi_info, True, C_HEROI)
        tela.blit(ph, (14, 46))
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

        if getattr(self, 'map_backbuffer', None) is None or getattr(self, 'map_backbuffer_sujo', True):
            self.map_backbuffer = pygame.Surface((r.width, r.height))
            self.map_backbuffer.fill((10, 12, 22))
            bg_sky = pygame.Surface((2, 2))
            bg_sky.set_at((0, 0), (6, 10, 26))
            bg_sky.set_at((1, 0), (6, 10, 26))
            bg_sky.set_at((0, 1), (18, 10, 24))
            bg_sky.set_at((1, 1), (18, 10, 24))
            bg_sky_scaled = pygame.transform.smoothscale(bg_sky, (r.width, r.height))
            self.map_backbuffer.blit(bg_sky_scaled, (0, 0))
            random.seed(1337)
            for _ in range(40):
                sx = random.randint(10, r.width - 10)
                sy = random.randint(10, r.height - 10)
                if sy < r.height * 0.4:
                    pygame.draw.circle(self.map_backbuffer, (180, 180, 210), (sx, sy), 1)
            fog = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            pygame.draw.ellipse(fog, (40, 50, 80, 40), (0, r.height - 120, r.width, 140))
            pygame.draw.ellipse(fog, (20, 30, 60, 30), (-50, r.height - 80, r.width + 100, 100))
            self.map_backbuffer.blit(fog, (0, 0))
            local_r = pygame.Rect(0, 0, r.width, r.height)
            pygame.draw.rect(self.map_backbuffer, C_BORDA, local_r, 1, border_radius=12)
            d = 12
            for cx, cy in [(local_r.left, local_r.top), (local_r.right, local_r.top), (local_r.left, local_r.bottom), (local_r.right, local_r.bottom)]:
                x_dir = 1 if cx == local_r.left else -1
                y_dir = 1 if cy == local_r.top else -1
                pygame.draw.line(self.map_backbuffer, C_OURO, (cx, cy), (cx + d * x_dir, cy), 2)
                pygame.draw.line(self.map_backbuffer, C_OURO, (cx, cy), (cx, cy + d * y_dir), 2)
            CX_local = r.width // 2
            CY_local = r.height // 2 - 5

            def _iso_local(gx_, gy_, el_):
                dx_ = gx_ - 9.5
                dy_ = gy_ - 9.5
                rx_ = dx_ * theta_cos - dy_ * theta_sin
                ry_ = dx_ * theta_sin + dy_ * theta_cos
                sx_ = (rx_ - ry_) * (TW // 2) + CX_local
                sy_ = (rx_ + ry_) * (TH // 2) - el_ * ES + CY_local
                return int(sx_), int(sy_)

            for ground_depth, cy_coord, gx, gy, zona_key, el, rx, ry in cells:
                paleta = PALETA.get(zona_key, PALETA["_exterior"])
                _, cor_left, cor_right = paleta
                cx_ = int((rx - ry) * (TW // 2) + CX_local)
                cy_ = int(cy_coord + CY_local)
                if not local_r.inflate(TW + 4, TH + 4).collidepoint(cx_, cy_):
                    continue
                
                p0 = _iso_local(gx - 0.5, gy - 0.5, el)
                p1 = _iso_local(gx + 0.5, gy - 0.5, el)
                p2 = _iso_local(gx + 0.5, gy + 0.5, el)
                p3 = _iso_local(gx - 0.5, gy + 0.5, el)
                top_pts = [p0, p1, p2, p3]
                
                thick = el * ES
                if thick > 0:
                    p0_bot = _iso_local(gx - 0.5, gy - 0.5, 0)
                    p1_bot = _iso_local(gx + 0.5, gy - 0.5, 0)
                    p2_bot = _iso_local(gx + 0.5, gy + 0.5, 0)
                    p3_bot = _iso_local(gx - 0.5, gy + 0.5, 0)
                    
                    p = [p0, p1, p2, p3]
                    p_bot = [p0_bot, p1_bot, p2_bot, p3_bot]
                    
                    idx_left = min(range(4), key=lambda i: p[i][0])
                    idx_right = max(range(4), key=lambda i: p[i][0])
                    idx_bottom = max(range(4), key=lambda i: p_bot[i][1])
                    
                    v_left = p[idx_left]
                    v_left_bot = p_bot[idx_left]
                    v_bottom = p[idx_bottom]
                    v_bottom_bot = p_bot[idx_bottom]
                    v_right = p[idx_right]
                    v_right_bot = p_bot[idx_right]
                    
                    left_pts = [v_left, v_bottom, v_bottom_bot, v_left_bot]
                    right_pts = [v_bottom, v_right, v_right_bot, v_bottom_bot]
                    
                    pygame.draw.polygon(self.map_backbuffer, cor_left,  left_pts)
                    pygame.draw.polygon(self.map_backbuffer, cor_right, right_pts)
                    h_step = max(5, int(8 * self.zoom))
                    c_mortar_l = (max(0, cor_left[0] - 35),  max(0, cor_left[1] - 35),  max(0, cor_left[2] - 35))
                    c_mortar_r = (max(0, cor_right[0] - 35), max(0, cor_right[1] - 35), max(0, cor_right[2] - 35))
                    for h in range(h_step, thick, h_step):
                        pygame.draw.line(self.map_backbuffer, c_mortar_l, (v_left[0], v_left[1] + h), (v_bottom[0], v_bottom[1] + h), 1)
                        pygame.draw.line(self.map_backbuffer, c_mortar_r, (v_bottom[0], v_bottom[1] + h), (v_right[0], v_right[1] + h), 1)
                    row_idx = 0
                    for h in range(0, thick, h_step):
                        j_h = min(h_step, thick - h)
                        if j_h <= 2: continue
                        fractions = [0.5] if row_idx % 2 == 0 else [0.25, 0.75]
                        for f in fractions:
                            jx = int(v_left[0] + f * (v_bottom[0] - v_left[0]))
                            jy = int(v_left[1] + f * (v_bottom[1] - v_left[1]))
                            pygame.draw.line(self.map_backbuffer, c_mortar_l, (jx, jy + h), (jx, jy + h + j_h), 1)
                        for f in fractions:
                            jx = int(v_bottom[0] + f * (v_right[0] - v_bottom[0]))
                            jy = int(v_bottom[1] + f * (v_right[1] - v_bottom[1]))
                            pygame.draw.line(self.map_backbuffer, c_mortar_r, (jx, jy + h), (jx, jy + h + j_h), 1)
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
                has_tree_outside = False
                if zona_key in ("_campo", "_exterior"):
                    val = zlib.adler32(f"tree_{gx}_{gy}".encode())
                    if val % 100 < 30:
                        has_tree_outside = True
                if has_tree_outside:
                    trunk_w = max(2, int(6 * self.zoom))
                    trunk_h = max(4, int(16 * self.zoom))
                    sombra = pygame.Surface((int(24 * self.zoom), int(12 * self.zoom)), pygame.SRCALPHA)
                    pygame.draw.ellipse(sombra, (0, 0, 0, 70), (0, 0, sombra.get_width(), sombra.get_height()))
                    self.map_backbuffer.blit(sombra, (cx_ - sombra.get_width() // 2, cy_ - sombra.get_height() // 2))
                    pygame.draw.rect(self.map_backbuffer, (85, 55, 30), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h))
                    pygame.draw.rect(self.map_backbuffer, (55, 35, 20), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h), 1)
                    r1 = max(4, int(13 * self.zoom))
                    r2 = max(3, int(10 * self.zoom))
                    r3 = max(2, int(7 * self.zoom))
                    pygame.draw.circle(self.map_backbuffer, (28, 98, 43), (cx_, cy_ - trunk_h), r1)
                    pygame.draw.circle(self.map_backbuffer, (18, 68, 28), (cx_, cy_ - trunk_h), r1, 1)
                    pygame.draw.circle(self.map_backbuffer, (38, 128, 53), (cx_, cy_ - trunk_h - int(7 * self.zoom)), r2)
                    pygame.draw.circle(self.map_backbuffer, (23, 88, 33), (cx_, cy_ - trunk_h - int(7 * self.zoom)), r2, 1)
                    pygame.draw.circle(self.map_backbuffer, (48, 158, 63), (cx_, cy_ - trunk_h - int(13 * self.zoom)), r3)
                    pygame.draw.circle(self.map_backbuffer, (33, 108, 43), (cx_, cy_ - trunk_h - int(13 * self.zoom)), r3, 1)
                ZONA_CONTORNOS = {
                    "camara_central": (235, 195, 30),
                    "curtume":        (220, 120, 40),
                    "carpintaria":    (60, 200, 60),
                    "fundicao":       (120, 180, 240),
                    "patio":          (60, 160, 240)
                }
                cor_borda = (10, 12, 20)
                espessura = 1
                if zona_key in ZONA_CONTORNOS:
                    cor_borda = ZONA_CONTORNOS[zona_key]
                    espessura = 2
                pygame.draw.polygon(self.map_backbuffer, cor_borda, top_pts, espessura)
                dep = self.estado.get("recursos_depositados", {})
                if zona_key == "patio" and gx == 13 and gy == 9:
                    qtd_pedra = self.estado.get("pedregulhos", 8)
                    if qtd_pedra > 0:
                        w = max(4, int(10 * self.zoom))
                        h = max(3, int(8 * self.zoom))
                        dx = int(5 * self.zoom)
                        dy = int(4.5 * self.zoom)
                        posicoes = []
                        curr = 0
                        for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                            if curr >= qtd_pedra: break
                            items_in_layer = min(max_items, qtd_pedra - curr)
                            for idx in range(items_in_layer):
                                ox = (idx - (items_in_layer - 1) / 2) * dx
                                oy = -layer_idx * dy
                                posicoes.append((ox, oy))
                                curr += 1
                        for ox, oy in posicoes:
                            bx = cx_ + ox
                            by = cy_ + oy
                            sombra = pygame.Surface((w * 1.5, h), pygame.SRCALPHA)
                            pygame.draw.ellipse(sombra, (0, 0, 0, 40), (0, 0, w * 1.5, h))
                            self.map_backbuffer.blit(sombra, (bx - w * 0.75, by - h//2))
                            pts = [
                                (bx - w//2, by),
                                (bx - w//3, by - h//2),
                                (bx + w//3, by - h//2),
                                (bx + w//2, by),
                                (bx + w//4, by + h//3),
                                (bx - w//4, by + h//3),
                            ]
                            pygame.draw.polygon(self.map_backbuffer, (100, 105, 110), pts)
                            pygame.draw.polygon(self.map_backbuffer, (130, 135, 140), [pts[1], pts[2], (bx, by)])
                            pygame.draw.polygon(self.map_backbuffer, (80, 85, 90), [pts[0], pts[1], (bx, by), pts[5]])
                            pygame.draw.polygon(self.map_backbuffer, (40, 40, 40), pts, 1)
                elif zona_key == "carpintaria" and gx == 9 and gy == 13:
                    qtd_dep = dep.get("madeira", 0)
                    remaining = max(0, 10 - qtd_dep)
                    if remaining > 0:
                        w = max(4, int(12 * self.zoom))
                        h = max(2, int(5 * self.zoom))
                        dx = int(5 * self.zoom)
                        dy = int(4 * self.zoom)
                        posicoes = []
                        curr = 0
                        for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                            if curr >= remaining: break
                            items_in_layer = min(max_items, remaining - curr)
                            for idx in range(items_in_layer):
                                ox = (idx - (items_in_layer - 1) / 2) * dx
                                oy = -layer_idx * dy
                                posicoes.append((ox, oy))
                                curr += 1
                        for ox, oy in posicoes:
                            lx = cx_ - w // 2 + ox
                            ly = cy_ - h // 2 + oy
                            pygame.draw.rect(self.map_backbuffer, (95, 55, 25), (lx, ly, w, h), border_radius=1)
                            pygame.draw.line(self.map_backbuffer, (65, 35, 15), (lx + 2, ly + h//3), (lx + w - 2, ly + h//3), 1)
                            r_cut = h // 2
                            cut_cx = lx + w - r_cut
                            cut_cy = ly + h // 2
                            pygame.draw.circle(self.map_backbuffer, (215, 175, 120), (cut_cx, cut_cy), r_cut)
                            pygame.draw.circle(self.map_backbuffer, (145, 95, 50), (cut_cx, cut_cy), r_cut, 1)
                            pygame.draw.rect(self.map_backbuffer, (50, 25, 10), (lx, ly, w, h), 1, border_radius=1)
                elif zona_key == "fundicao" and gx == 5 and gy == 9:
                    qtd_dep = dep.get("metal", 0)
                    remaining = max(0, 10 - qtd_dep)
                    if remaining > 0:
                        w = max(4, int(10 * self.zoom))
                        h = max(2, int(5 * self.zoom))
                        thickness = max(1, int(2.5 * self.zoom))
                        dx = int(4 * self.zoom)
                        dy = int(3.5 * self.zoom)
                        posicoes = []
                        curr = 0
                        for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                            if curr >= remaining: break
                            items_in_layer = min(max_items, remaining - curr)
                            for idx in range(items_in_layer):
                                ox = (idx - (items_in_layer - 1) / 2) * dx
                                oy = -layer_idx * dy
                                posicoes.append((ox, oy))
                                curr += 1
                        for ox, oy in posicoes:
                            bx = cx_ + ox
                            by = cy_ + oy
                            top_pts = [
                                (bx - w//2 + thickness//2, by - h//2),
                                (bx + w//2 - thickness//2, by - h//2),
                                (bx + w//2,                by + h//2 - thickness),
                                (bx - w//2,                by + h//2 - thickness),
                            ]
                            right_pts = [
                                (bx + w//2 - thickness//2, by - h//2),
                                (bx + w//2,                by - h//2 + thickness),
                                (bx + w//2,                by + h//2),
                                (bx + w//2,                by + h//2 - thickness),
                            ]
                            left_pts = [
                                (bx - w//2,                by + h//2 - thickness),
                                (bx + w//2,                by + h//2 - thickness),
                                (bx + w//2,                by + h//2),
                                (bx - w//2,                by + h//2),
                            ]
                            c_top = (175, 185, 195)
                            c_side_l = (120, 125, 135)
                            c_side_r = (140, 145, 155)
                            pygame.draw.polygon(self.map_backbuffer, c_side_r, right_pts)
                            pygame.draw.polygon(self.map_backbuffer, c_side_l, left_pts)
                            pygame.draw.polygon(self.map_backbuffer, c_top, top_pts)
                            pygame.draw.polygon(self.map_backbuffer, (50, 50, 60), top_pts, 1)
                            pygame.draw.polygon(self.map_backbuffer, (50, 50, 60), left_pts, 1)
                            pygame.draw.line(self.map_backbuffer, (245, 245, 255), (bx - w//2 + 1, by + h//2 - thickness), (bx + w//2 - 1, by + h//2 - thickness), 1)
                elif zona_key == "curtume" and gx == 9 and gy == 5:
                    qtd_dep = dep.get("couro", 0)
                    remaining = max(0, 10 - qtd_dep)
                    if remaining > 0:
                        r_w = max(2, int(3.5 * self.zoom))
                        dx = int(5 * self.zoom)
                        dy = int(4 * self.zoom)
                        posicoes = []
                        curr = 0
                        for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                            if curr >= remaining: break
                            items_in_layer = min(max_items, remaining - curr)
                            for idx in range(items_in_layer):
                                ox = (idx - (items_in_layer - 1) / 2) * dx
                                oy = -layer_idx * dy
                                posicoes.append((ox, oy))
                                curr += 1
                        for ox, oy in posicoes:
                            bx = cx_ + ox
                            by = cy_ + oy
                            sombra_l = pygame.Surface((r_w * 3, r_w * 2), pygame.SRCALPHA)
                            pygame.draw.ellipse(sombra_l, (0, 0, 0, 40), (0, 0, r_w * 3, r_w * 2))
                            self.map_backbuffer.blit(sombra_l, (bx - r_w * 1.5, by - r_w))
                            circles = [
                                (bx - r_w//2, by + r_w//3, r_w),
                                (bx + r_w//2, by + r_w//3, r_w),
                                (bx,          by - r_w//2, r_w),
                            ]
                            for px, py, pr in circles:
                                pygame.draw.circle(self.map_backbuffer, (170, 170, 180), (px, py), pr + 1)
                            for px, py, pr in circles:
                                pygame.draw.circle(self.map_backbuffer, (245, 245, 250), (px, py), pr)
                            for px, py, pr in circles:
                                pygame.draw.circle(self.map_backbuffer, (220, 220, 230), (px + 1, py + 1), pr - 1)
                                pygame.draw.circle(self.map_backbuffer, (245, 245, 250), (px, py), pr - 1)
                elif zona_key == "camara_central":
                    if gx == 8 and gy == 8:
                        qtd = dep.get("madeira", 0)
                        if qtd > 0:
                            w = max(4, int(12 * self.zoom))
                            h = max(2, int(5 * self.zoom))
                            dx = int(5 * self.zoom)
                            dy = int(4 * self.zoom)
                            posicoes = []
                            curr = 0
                            for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                                if curr >= qtd: break
                                items_in_layer = min(max_items, qtd - curr)
                                for idx in range(items_in_layer):
                                    ox = (idx - (items_in_layer - 1) / 2) * dx
                                    oy = -layer_idx * dy
                                    posicoes.append((ox, oy))
                                    curr += 1
                            for ox, oy in posicoes:
                                lx = cx_ - w // 2 + ox
                                ly = cy_ - h // 2 + oy
                                pygame.draw.rect(self.map_backbuffer, (95, 55, 25), (lx, ly, w, h), border_radius=1)
                                pygame.draw.line(self.map_backbuffer, (65, 35, 15), (lx + 2, ly + h//3), (lx + w - 2, ly + h//3), 1)
                                r_cut = h // 2
                                cut_cx = lx + w - r_cut
                                cut_cy = ly + h // 2
                                pygame.draw.circle(self.map_backbuffer, (215, 175, 120), (cut_cx, cut_cy), r_cut)
                                pygame.draw.circle(self.map_backbuffer, (145, 95, 50), (cut_cx, cut_cy), r_cut, 1)
                                pygame.draw.rect(self.map_backbuffer, (50, 25, 10), (lx, ly, w, h), 1, border_radius=1)
                    elif gx == 8 and gy == 11:
                        qtd = dep.get("metal", 0)
                        if qtd > 0:
                            w = max(4, int(10 * self.zoom))
                            h = max(2, int(5 * self.zoom))
                            thickness = max(1, int(2.5 * self.zoom))
                            dx = int(4 * self.zoom)
                            dy = int(3.5 * self.zoom)
                            posicoes = []
                            curr = 0
                            for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                                if curr >= qtd: break
                                items_in_layer = min(max_items, qtd - curr)
                                for idx in range(items_in_layer):
                                    ox = (idx - (items_in_layer - 1) / 2) * dx
                                    oy = -layer_idx * dy
                                    posicoes.append((ox, oy))
                                    curr += 1
                            for ox, oy in posicoes:
                                bx = cx_ + ox
                                by = cy_ + oy
                                top_pts = [
                                    (bx - w//2 + thickness//2, by - h//2),
                                    (bx + w//2 - thickness//2, by - h//2),
                                    (bx + w//2,                by + h//2 - thickness),
                                    (bx - w//2,                by + h//2 - thickness),
                                ]
                                right_pts = [
                                    (bx + w//2 - thickness//2, by - h//2),
                                    (bx + w//2,                by - h//2 + thickness),
                                    (bx + w//2,                by + h//2),
                                    (bx + w//2,                by + h//2 - thickness),
                                ]
                                left_pts = [
                                    (bx - w//2,                by + h//2 - thickness),
                                    (bx + w//2,                by + h//2 - thickness),
                                    (bx + w//2,                by + h//2),
                                    (bx - w//2,                by + h//2),
                                ]
                                c_top = (175, 185, 195)
                                c_side_l = (120, 125, 135)
                                c_side_r = (140, 145, 155)
                                pygame.draw.polygon(self.map_backbuffer, c_side_r, right_pts)
                                pygame.draw.polygon(self.map_backbuffer, c_side_l, left_pts)
                                pygame.draw.polygon(self.map_backbuffer, c_top, top_pts)
                                pygame.draw.polygon(self.map_backbuffer, (50, 50, 60), top_pts, 1)
                                pygame.draw.polygon(self.map_backbuffer, (50, 50, 60), left_pts, 1)
                                pygame.draw.line(self.map_backbuffer, (245, 245, 255), (bx - w//2 + 1, by + h//2 - thickness), (bx + w//2 - 1, by + h//2 - thickness), 1)
                    elif gx == 11 and gy == 8:
                        qtd = dep.get("couro", 0)
                        if qtd > 0:
                            r_w = max(2, int(3.5 * self.zoom))
                            dx = int(5 * self.zoom)
                            dy = int(4 * self.zoom)
                            posicoes = []
                            curr = 0
                            for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                                if curr >= qtd: break
                                items_in_layer = min(max_items, qtd - curr)
                                for idx in range(items_in_layer):
                                    ox = (idx - (items_in_layer - 1) / 2) * dx
                                    oy = -layer_idx * dy
                                    posicoes.append((ox, oy))
                                    curr += 1
                            for ox, oy in posicoes:
                                bx = cx_ + ox
                                by = cy_ + oy
                                sombra_l = pygame.Surface((r_w * 3, r_w * 2), pygame.SRCALPHA)
                                pygame.draw.ellipse(sombra_l, (0, 0, 0, 40), (0, 0, r_w * 3, r_w * 2))
                                self.map_backbuffer.blit(sombra_l, (bx - r_w * 1.5, by - r_w))
                                circles = [
                                    (bx - r_w//2, by + r_w//3, r_w),
                                    (bx + r_w//2, by + r_w//3, r_w),
                                    (bx,          by - r_w//2, r_w),
                                ]
                                for px, py, pr in circles:
                                    pygame.draw.circle(self.map_backbuffer, (170, 170, 180), (px, py), pr + 1)
                                for px, py, pr in circles:
                                    pygame.draw.circle(self.map_backbuffer, (245, 245, 250), (px, py), pr)
                                for px, py, pr in circles:
                                    pygame.draw.circle(self.map_backbuffer, (220, 220, 230), (px + 1, py + 1), pr - 1)
                                    pygame.draw.circle(self.map_backbuffer, (245, 245, 250), (px, py), pr - 1)
                    elif gx == 9 and gy == 9:
                        qtd_ouro = self.estado.get("tesouro", 20)
                        visual_n = (qtd_ouro + 1) // 2
                        if visual_n > 0:
                            w = max(4, int(8 * self.zoom))
                            h = max(2, int(4 * self.zoom))
                            dx = int(4 * self.zoom)
                            dy = int(3 * self.zoom)
                            posicoes = []
                            curr = 0
                            for layer_idx, max_items in enumerate([4, 3, 2, 1]):
                                if curr >= visual_n: break
                                items_in_layer = min(max_items, visual_n - curr)
                                for idx in range(items_in_layer):
                                    ox = (idx - (items_in_layer - 1) / 2) * dx
                                    oy = -layer_idx * dy
                                    posicoes.append((ox, oy))
                                    curr += 1
                            for ox, oy in posicoes:
                                bx = cx_ + ox
                                by = cy_ + oy
                                pygame.draw.ellipse(self.map_backbuffer, (200, 150, 0), (bx - w//2, by - h//2, w, h))
                                pygame.draw.rect(self.map_backbuffer, (220, 170, 10), (bx - w//2, by - h//2 + 1, w, h//2))
                                pygame.draw.ellipse(self.map_backbuffer, (255, 220, 50), (bx - w//2, by - h//2, w, h//2))
                                pygame.draw.ellipse(self.map_backbuffer, (255, 245, 150), (bx - w//4, by - h//2 + 1, w//2, h//4))
                                pygame.draw.ellipse(self.map_backbuffer, (130, 90, 0), (bx - w//2, by - h//2, w, h), 1)
            self.map_backbuffer_sujo = False
        tela.blit(self.map_backbuffer, (r.x, r.y))
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


        def _campo_direcao(gx, gy):
            if gy < GRID_MIN:   return "campo_norte"
            if gy > GRID_MAX:   return "campo_sul"
            if gx < GRID_MIN:   return "campo_oeste"
            if gx > GRID_MAX:   return "campo_leste"
            return None

        tab = self.motor.tabuleiro
        e = self.estado

        mx_draw, my_draw = pygame.mouse.get_pos()
        hovered_g = self._screen_to_grid(mx_draw, my_draw)

        for ground_depth, cy_coord, gx, gy, zona_key, el, rx, ry in cells:
            cx_ = int((rx - ry) * (TW // 2) + CX)
            cy_ = int(cy_coord + CY)
            if not r.inflate(TW + 4, TH + 4).collidepoint(cx_, cy_):
                continue
            p0 = _iso(gx - 0.5, gy - 0.5, el)
            p1 = _iso(gx + 0.5, gy - 0.5, el)
            p2 = _iso(gx + 0.5, gy + 0.5, el)
            p3 = _iso(gx - 0.5, gy + 0.5, el)
            top_pts = [p0, p1, p2, p3]
            is_hover = (gx, gy) == hovered_g
            is_move_hl = self.modo_acao == MODO_MOVER and (gx, gy) in self.alcancaveis
            campo_dir = _campo_direcao(gx, gy)
            if is_hover:
                self._draw_alpha_polygon(tela, (255, 255, 255, 30), top_pts)
                pygame.draw.polygon(tela, (255, 255, 255), top_pts, 1)
            if is_move_hl:
                self._draw_celula_tactica(tela, gx, gy, el, (0, 150, 0, 45), (100, 255, 100), estilo='movimento')
            if campo_dir and zona_key == "_campo":
                inv_campo = e.get(campo_dir, 0)
                if inv_campo > 0:
                    pulso = abs((self.timer % 90) - 45) / 45.0
                    self._draw_celula_tactica(tela, gx, gy, el, (255, 0, 0, int(35 + 25 * pulso)), (255, 50, 50), estilo='ataque')
            if zona_key not in labels_pendentes and zona_key in ZONA_LABELS:
                from src.resolvedor_acoes import ZONAS_GRID as _ZG
                if zona_key in _ZG:
                    x1, y1, x2, y2 = _ZG[zona_key]
                    mid_gx = (x1 + x2) // 2
                    mid_gy = (y1 + y2) // 2
                    _, mid_el = _classificar(mid_gx, mid_gy)
                    mcx, mcy = _iso(mid_gx, mid_gy, mid_el)
                    labels_pendentes[zona_key] = (mcx, mcy)
            if GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                char = tab.grid[gy][gx]
                if char:
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

        e = self.estado
        for zona_key, (lcx, lcy) in labels_pendentes.items():
            y_off = lcy - int(8 * self.zoom)
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
            if zona_key == "camara_central":
                pass
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
        ut = self.fMi.render("MERCADO DE MELHORIAS", True, C_ACENTO)
        tela.blit(ut, (x + pw // 2 - ut.get_width() // 2, yt)); yt += 18
        self._slot_y_start = yt
        for slot in self.estado["slots_upgrade"]:
            sr = pygame.Rect(x + 6, yt, pw - 12, 38)
            self._slot_rects_cache[slot["id"]] = sr
            is_slot_vazio = slot.get("adquirido") or slot.get("carta_id") is None
            if self.fase == "REPOVOAR_MERCADO":
                if is_slot_vazio:
                    pygame.draw.rect(tela, (20, 20, 26), sr, border_radius=5)
                    pygame.draw.rect(tela, C_BORDA, sr, 1, border_radius=5)
                    btn_w = (sr.width - 16) // 3
                    b_amarelo = pygame.Rect(sr.x + 4, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (70, 60, 10), b_amarelo, border_radius=4)
                    lbl_a = self.fMi.render("Fraco", True, (255, 230, 120))
                    tela.blit(lbl_a, (b_amarelo.centerx - lbl_a.get_width() // 2, b_amarelo.centery - lbl_a.get_height() // 2))
                    b_cinza = pygame.Rect(sr.x + 8 + btn_w, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (50, 50, 56), b_cinza, border_radius=4)
                    lbl_c = self.fMi.render("Médio", True, (220, 220, 230))
                    tela.blit(lbl_c, (b_cinza.centerx - lbl_c.get_width() // 2, b_cinza.centery - lbl_c.get_height() // 2))
                    b_vermelho = pygame.Rect(sr.x + 12 + 2 * btn_w, sr.y + 4, btn_w, 30)
                    pygame.draw.rect(tela, (80, 20, 20), b_vermelho, border_radius=4)
                    lbl_v = self.fMi.render("Forte", True, (255, 180, 180))
                    tela.blit(lbl_v, (b_vermelho.centerx - lbl_v.get_width() // 2, b_vermelho.centery - lbl_v.get_height() // 2))
                else:
                    pygame.draw.rect(tela, (18, 20, 38), sr, border_radius=5)
                    pygame.draw.rect(tela, C_BORDA, sr, 1, border_radius=5)
                    nt = self.fMi.render(slot['nome'][:20], True, C_TEXTO)
                    tela.blit(nt, (sr.x + 4, sr.y + 4))
                    from ...resolvedor_acoes import CUSTO_ADICIONAL_SLOT
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
                    b_descartar = pygame.Rect(sr.right - 44, sr.y + 4, 40, 30)
                    pygame.draw.rect(tela, (80, 20, 20), b_descartar, border_radius=4)
                    lbl_x = self.fMi.render("X", True, (255, 255, 255))
                    tela.blit(lbl_x, (b_descartar.centerx - lbl_x.get_width() // 2, b_descartar.centery - lbl_x.get_height() // 2))
            else:
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
                    from ...resolvedor_acoes import CUSTO_ADICIONAL_SLOT
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
        if self.fase == "REPOVOAR_MERCADO":
            self.btn_concluir_reposicao_rect = pygame.Rect(x + 6, yt, pw - 12, 34)
            pygame.draw.rect(tela, (25, 80, 25), self.btn_concluir_reposicao_rect, border_radius=5)
            lbl_done = self.fG.render("CONCLUIR REPOSICAO", True, (255, 255, 255))
            tela.blit(lbl_done, (self.btn_concluir_reposicao_rect.centerx - lbl_done.get_width() // 2, self.btn_concluir_reposicao_rect.centery - lbl_done.get_height() // 2))
            yt += 38
        else:
            self.btn_concluir_reposicao_rect = None
        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6
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

    # ── MÃO DO HERÓI ──────────────────────────────────────────────────────
    def _draw_mao(self, tela):
        mr = self.mao_rect
        pygame.draw.rect(tela, (10, 12, 24), mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)
        mao = self.estado["mao"]
        self.carta_rects = []
        deck_cartas_qtd = len(self.estado["deck_heroi"])
        deck_rect = pygame.Rect(mr.right - 106, mr.y + 6, 96, mr.height - 12)
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
        if deck_cartas_qtd > 0:
            top_deck_rect = deck_rect.move(-min(4, max(1, deck_cartas_qtd // 3)) * 2, -min(4, max(1, deck_cartas_qtd // 3)) * 2)
            lbl_deck1 = self.fMi.render("BARALHO", True, C_OURO)
            lbl_deck2 = self.fMi.render(str(deck_cartas_qtd), True, C_TEXTO)
            tela.blit(lbl_deck1, (top_deck_rect.centerx - lbl_deck1.get_width() // 2, top_deck_rect.y + 40))
            tela.blit(lbl_deck2, (top_deck_rect.centerx - lbl_deck2.get_width() // 2, top_deck_rect.y + 64))
        deck_ini_qtd = len(self.estado.get("deck_inimigos", []))
        deck_ini_rect = pygame.Rect(mr.x + 10, mr.y + 6, 96, mr.height - 12)
        for offset in range(min(4, max(1, deck_ini_qtd // 3))):
            d_rect = deck_ini_rect.move(offset * 2, -offset * 2)
            pygame.draw.rect(tela, (40, 14, 14), d_rect, border_radius=6)
            pygame.draw.rect(tela, (140, 30, 30), d_rect, 1, border_radius=6)
        if deck_ini_qtd > 0:
            top_deck_rect = deck_ini_rect.move(min(4, max(1, deck_ini_qtd // 3)) * 2, -min(4, max(1, deck_ini_qtd // 3)) * 2)
            lbl_deck1 = self.fMi.render("DECK INI", True, C_PERIGO)
            lbl_deck2 = self.fMi.render(str(deck_ini_qtd), True, C_TEXTO)
            tela.blit(lbl_deck1, (top_deck_rect.centerx - lbl_deck1.get_width() // 2, top_deck_rect.y + 40))
            tela.blit(lbl_deck2, (top_deck_rect.centerx - lbl_deck2.get_width() // 2, top_deck_rect.y + 64))
        descarte_ini = self.estado.get("descarte_inimigos", [])
        if descarte_ini:
            ultima_carta = descarte_ini[-1]
            carta_ini_rect = pygame.Rect(mr.x + 116, mr.y + 6, 96, mr.height - 12)
            pygame.draw.rect(tela, (24, 16, 16), carta_ini_rect, border_radius=6)
            pygame.draw.rect(tela, C_PERIGO, carta_ini_rect, 1, border_radius=6)
            from ...cerco_isectum import DADOS_INIMIGOS
            info_ini = DADOS_INIMIGOS.get(ultima_carta, {"nome": ultima_carta, "emoji": "\U0001f47e", "antigo": ""})
            nome_lbl1 = self.fMi.render("REVELADO", True, C_DIM)
            nome_lbl2 = self.fMi.render(f"{info_ini['emoji']} {info_ini['nome']}", True, C_PERIGO)
            if nome_lbl2.get_width() > 90:
                nome_lbl2 = self.fP.render(f"{info_ini['emoji']} {info_ini['nome']}", True, C_PERIGO)
            if nome_lbl2.get_width() > 90:
                nome_lbl2 = self.fMi.render(f"{info_ini['emoji']} {info_ini['nome'][:8]}...", True, C_PERIGO)
            tela.blit(nome_lbl1, (carta_ini_rect.centerx - nome_lbl1.get_width() // 2, carta_ini_rect.y + 12))
            tela.blit(nome_lbl2, (carta_ini_rect.centerx - nome_lbl2.get_width() // 2, carta_ini_rect.y + 32))
            if info_ini.get("antigo"):
                antigo_lbl = self.fMi.render(f"({info_ini['antigo']})", True, C_DIM)
                tela.blit(antigo_lbl, (carta_ini_rect.centerx - antigo_lbl.get_width() // 2, carta_ini_rect.y + 52))
            pygame.draw.circle(tela, C_PERIGO, (carta_ini_rect.centerx, carta_ini_rect.y + 80), 5)
            pygame.draw.rect(tela, C_PERIGO, (carta_ini_rect.centerx - 4, carta_ini_rect.y + 84, 8, 4))
        if not mao:
            nt = self.fP.render("Sem cartas na mão — jogue cartas ou passe o turno", True, C_DIM)
            disponivel_x = mr.x + 230 + (mr.width - 360) // 2
            tela.blit(nt, (disponivel_x - nt.get_width() // 2, mr.centery - 8))
            return
        mouse = pygame.mouse.get_pos()
        GEMAS_COR = {
            "movimento": (100, 200, 255),
            "trabalho":  (120, 220, 100),
            "escavacao": (255, 195, 40),
        }
        anims_ativas = {}
        if hasattr(self, 'animacoes_cartas_compra') and self.animacoes_cartas_compra:
            for anim in self.animacoes_cartas_compra:
                if not anim.get('finalizada', False):
                    anims_ativas[anim['idx_mao']] = anim
        for i, carta in enumerate(mao):
            cx, cy, cw, ch = self._calcular_pos_carta_na_mao(i, len(mao))
            if i in anims_ativas:
                anim = anims_ativas[i]
                if anim.get('delay', 0) > 0:
                    self.carta_rects.append(pygame.Rect(cx, cy, cw, ch))
                    continue
                prog = anim['progresso']
                sx, sy = anim['start_pos']
                ex, ey = anim['end_pos']
                curr_x = sx + (ex - sx) * prog
                curr_y = sy + (ey - sy) * prog
                curr_y -= math.sin(prog * math.pi) * 35
                crect = pygame.Rect(int(curr_x), int(curr_y), cw, ch)
                self.carta_rects.append(crect)
                hover = False
                sel = False
            else:
                temp_rect = pygame.Rect(cx, cy, cw, ch)
                hover = temp_rect.collidepoint(mouse)
                sel   = (i == self.idx_carta_queimar)
                deslocamento_y = -8 if hover else 0
                crect = pygame.Rect(cx, cy + deslocamento_y, cw, ch)
                self.carta_rects.append(crect)
            # 1. Determina o tipo de gema e a cor do acento/tema
            tipo_gema = "movimento"
            if carta.get("trabalho"):  tipo_gema = "trabalho"
            if carta.get("escavacao"): tipo_gema = "escavacao"
            cor_gema = GEMAS_COR.get(tipo_gema, (200, 200, 200))

            # 2. Renderiza Fundo (Força a renderização procedural premium)
            sprite = None

            # Determina cores do gradiente de acordo com o tipo
            if tipo_gema == "movimento":
                c_top = (26, 46, 82) if hover else (14, 26, 50)
                c_bot = (12, 18, 32)
            elif tipo_gema == "trabalho":
                c_top = (24, 64, 34) if hover else (12, 42, 22)
                c_bot = (10, 20, 12)
            elif tipo_gema == "escavacao":
                c_top = (75, 55, 14) if hover else (50, 36, 8)
                c_bot = (26, 16, 6)
            else:
                c_top = (40, 40, 50) if hover else (25, 25, 30)
                c_bot = (15, 15, 18)

            if sprite:
                scaled_sprite = pygame.transform.smoothscale(sprite, (cw, ch))
                tela.blit(scaled_sprite, crect.topleft)
            else:
                # Gradiente processado via smoothscale
                grad = pygame.Surface((2, 2))
                grad.set_at((0, 0), c_top); grad.set_at((1, 0), c_top)
                grad.set_at((0, 1), c_bot); grad.set_at((1, 1), c_bot)
                grad_scaled = pygame.transform.smoothscale(grad, (cw, ch))
                tela.blit(grad_scaled, crect.topleft)

            # 3. Moldura Externa e Chanfros Internos
            borda_cor = C_ACENTO if sel else (C_OURO if hover else C_BORDA)
            pygame.draw.rect(tela, borda_cor, crect, 2 if sel or hover else 1, border_radius=7)
            
            # Linha de chanfro interna brilhante
            cor_chanfro = (c_top[0]+25, c_top[1]+25, c_top[2]+25) if hover else (c_top[0]+12, c_top[1]+12, c_top[2]+12)
            pygame.draw.rect(tela, cor_chanfro, crect.inflate(-4, -4), 1, border_radius=6)
            
            # Linha de chanfro interna escura para profundidade
            pygame.draw.rect(tela, (4, 4, 6), crect.inflate(-6, -6), 1, border_radius=5)

            # 4. Caixa de Arte Procedural (Desenha apenas se NÃO houver imagem de asset de fundo)
            if not sprite:
                art_rect = pygame.Rect(crect.x + 6, crect.y + 24, cw - 12, 38)
                pygame.draw.rect(tela, (8, 6, 12), art_rect, border_radius=4)
                pygame.draw.rect(tela, (36, 36, 48), art_rect, 1, border_radius=4)
                
                # Desenhos vetoriais abstratos baseados no tipo
                if tipo_gema == "movimento":
                    # Linhas de vento/velocidade ciano
                    pygame.draw.line(tela, (60, 160, 255), (art_rect.x + 8, art_rect.bottom - 8), (art_rect.right - 15, art_rect.y + 8), 2)
                    pygame.draw.line(tela, (120, 220, 255), (art_rect.x + 20, art_rect.bottom - 8), (art_rect.right - 6, art_rect.y + 8), 1)
                    pygame.draw.circle(tela, (30, 80, 160), (art_rect.centerx, art_rect.centery), 6)
                    pygame.draw.circle(tela, (100, 210, 255), (art_rect.centerx, art_rect.centery), 3)
                elif tipo_gema == "trabalho":
                    # Engrenagem/projeto verde
                    pygame.draw.circle(tela, (40, 110, 60), (art_rect.centerx, art_rect.centery), 12, 1)
                    pygame.draw.circle(tela, (90, 220, 110), (art_rect.centerx, art_rect.centery), 6, 1)
                    pygame.draw.line(tela, (70, 170, 90), (art_rect.x + 8, art_rect.centery), (art_rect.right - 8, art_rect.centery), 1)
                    pygame.draw.line(tela, (70, 170, 90), (art_rect.centerx, art_rect.y + 4), (art_rect.centerx, art_rect.bottom - 4), 1)
                elif tipo_gema == "escavacao":
                    # Cristais geométricos dourados
                    p1 = [(art_rect.centerx, art_rect.y + 6), (art_rect.centerx + 7, art_rect.centery), (art_rect.centerx, art_rect.bottom - 6), (art_rect.centerx - 7, art_rect.centery)]
                    p2 = [(art_rect.centerx - 9, art_rect.y + 10), (art_rect.centerx - 4, art_rect.centery + 3), (art_rect.centerx - 9, art_rect.bottom - 10), (art_rect.centerx - 14, art_rect.centery + 3)]
                    p3 = [(art_rect.centerx + 9, art_rect.y + 10), (art_rect.centerx + 14, art_rect.centery + 3), (art_rect.centerx + 9, art_rect.bottom - 10), (art_rect.centerx + 4, art_rect.centery + 3)]
                    pygame.draw.polygon(tela, (180, 130, 30), p2)
                    pygame.draw.polygon(tela, (180, 130, 30), p3)
                    pygame.draw.polygon(tela, (255, 215, 80), p1)
                    pygame.draw.line(tela, (255, 250, 210), (art_rect.centerx, art_rect.y + 6), (art_rect.centerx - 7, art_rect.centery), 1)
                else:
                    # Padrão de grade genérico
                    pygame.draw.line(tela, (40, 40, 50), (art_rect.x + 10, art_rect.y + 10), (art_rect.right - 10, art_rect.bottom - 10), 1)
                    pygame.draw.line(tela, (40, 40, 50), (art_rect.right - 10, art_rect.y + 10), (art_rect.x + 10, art_rect.bottom - 10), 1)

            # 5. Gema de Custo de Energia (Refinada 3D)
            rx_center = crect.centerx
            ry_center = crect.y + 13
            pygame.draw.circle(tela, (2, 2, 4), (rx_center, ry_center), 11)
            
            gem_pts = [
                (rx_center, ry_center - 8),
                (rx_center + 8, ry_center),
                (rx_center, ry_center + 8),
                (rx_center - 8, ry_center)
            ]
            pygame.draw.polygon(tela, cor_gema, gem_pts)
            pygame.draw.polygon(tela, (255, 255, 255), gem_pts, 1)
            # Linhas de brilho da faceta da gema
            pygame.draw.line(tela, (255, 255, 255), (rx_center, ry_center - 7), (rx_center - 7, ry_center), 1)
            pygame.draw.line(tela, (255, 255, 255), (rx_center, ry_center), (rx_center - 7, ry_center), 1)

            # 6. Banner de Título & Nome da Carta
            banner_rect = pygame.Rect(crect.x + 8, crect.y + 66, cw - 16, 18)
            pygame.draw.rect(tela, (8, 8, 12, 220), banner_rect, border_radius=4)
            pygame.draw.rect(tela, (42, 42, 54), banner_rect, 1, border_radius=4)
            
            nome_cortado = carta["nome"][:14]
            nt = self.fMi.render(nome_cortado, True, C_OURO if sel else C_TEXTO)
            tela.blit(nt, (banner_rect.centerx - nt.get_width() // 2, banner_rect.y + 3))

            # 7. Descrição
            desc = carta.get("descricao", "")
            if desc:
                lbl_desc = self.fMi.render(desc[:22], True, C_DIM)
                tela.blit(lbl_desc, (crect.centerx - lbl_desc.get_width() // 2, crect.y + 88))

            # 8. Status/Atributos Segmentados (Layout Premium de TCG)
            stats = []
            if carta.get("movimento"): stats.append(("M", str(carta["movimento"]), (80, 180, 255)))
            if carta.get("trabalho"):  stats.append(("T", str(carta["trabalho"]), (100, 220, 120)))
            if carta.get("escavacao"): stats.append(("E", str(carta["escavacao"]), (255, 215, 80)))
            
            if stats:
                y_status = crect.y + ch - 22
                box_w = 26
                box_h = 16
                gap = 4
                total_w = len(stats) * box_w + (len(stats) - 1) * gap
                start_bx = crect.centerx - total_w // 2
                
                for idx_stat, (letra, valor, cor_attr) in enumerate(stats):
                    bx = start_bx + idx_stat * (box_w + gap)
                    by = y_status
                    rect_stat = pygame.Rect(bx, by, box_w, box_h)
                    
                    pygame.draw.rect(tela, (10, 12, 18), rect_stat, border_radius=3)
                    pygame.draw.rect(tela, cor_attr, rect_stat, 1, border_radius=3)
                    
                    lbl_s = self.fMi.render(f"{letra}{valor}", True, cor_attr)
                    tela.blit(lbl_s, (rect_stat.centerx - lbl_s.get_width() // 2, rect_stat.centery - lbl_s.get_height() // 2))

            # 9. Overlay de Descarte/Queima
            if sel:
                ql = self.fMi.render("DESCARTE", True, C_PERIGO)
                ql_bg = pygame.Rect(crect.centerx - ql.get_width() // 2 - 4, crect.y + 42, ql.get_width() + 8, 16)
                pygame.draw.rect(tela, (40, 10, 10), ql_bg, border_radius=3)
                pygame.draw.rect(tela, C_PERIGO, ql_bg, 1, border_radius=3)
                tela.blit(ql, (crect.centerx - ql.get_width() // 2, crect.y + 43))

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

        _btn(self.btn_fim_turno, "Encerrar Turno  [Ent]",
             True, (60, 20, 20), (90, 30, 30), C_PAINEL)

        if self.modo_acao == MODO_SUBORNAR:
            dep = e.get("recursos_depositados", {})
            bx = self.btn_subornar.right + 8
            for res, nome in [("madeira", "\U0001fab5"), ("couro", "\U0001f9f3"), ("metal", "\u2699\ufe0f")]:
                br = pygame.Rect(bx, H - 48, 50, 36)
                ativo = dep.get(res, 0) > 0
                _btn(br, f"{nome}{dep.get(res,0)}", ativo,
                     (30, 40, 30), (50, 70, 50), (20, 20, 20))
                if br.collidepoint(mouse) and ativo:
                    if pygame.mouse.get_pressed()[0]:
                        self._subornar_recurso(res)
                bx += 56
            br_rocha = pygame.Rect(bx, H - 48, 140, 36)
            ativo_rocha = e.get("pontos_escavacao", 0) >= 4
            _btn(br_rocha, "\U0001faa8 Limpar Rocha(4PE)", ativo_rocha,
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
        tipo_lbl = {"invasor": "\U0001f47f INVASOR COMUM", "mover": "\U0001f3c3 AVANÇO",
                    "torre_assalto": "\U0001f5fc TORRE DE ASSALTO",
                    "catapulta": "\U0001f4a5 CATAPULTA DE CERCO"
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
        t1  = self.fT.render("\U0001f3c6 VITÓRIA!" if vit else "\U0001f480 DERROTA!", True, cor)
        tela.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 90))
        msg = (e.get("msg_vitoria") or "Os defensores resistiram!") if vit \
            else (e.get("msg_derrota") or "A fortaleza caiu.")
        t2 = self.fM.render(msg[:64], True, C_TEXTO)
        tela.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 20))
        t3 = self.fP.render(
            f"Rodada {e['rodada']}  |  Tesouro: {e['tesouro']}\U0001fa99  |  "
            f"Cartas no cerco: {len(self.deck)}", True, C_DIM
        )
        tela.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 24))
        t4 = self.fP.render("Clique para voltar ao menu", True, C_DIM)
        tela.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 + 60))

    # ── MODAL ESCOLHA AÇÃO ───────────────────────────────────────────────
    def _draw_modal_escolha_carta(self, tela, W, H):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 9, 16, 210))
        tela.blit(overlay, (0, 0))
        carta = self.estado["mao"][self.idx_carta_sendo_jogada]
        pm = carta.get("movimento", 0)
        pt = carta.get("trabalho", 0)
        pe = carta.get("escavacao", 0)
        is_hibrida = (pm > 0) and (pt > 0 or pe > 0)
        mw = 580 if is_hibrida else 440
        mh = 240
        mx, my = W // 2 - mw // 2, H // 2 - mh // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(tela, (18, 20, 32), modal_rect, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, modal_rect, 2, border_radius=8)
        tit = self.fG.render("ESCOLHA A ACAO DA CARTA", True, C_ACENTO)
        tela.blit(tit, (modal_rect.centerx - tit.get_width() // 2, my + 20))
        sub = self.fMi.render(carta["nome"].upper(), True, C_OURO)
        tela.blit(sub, (modal_rect.centerx - sub.get_width() // 2, my + 44))
        btn_w, btn_h = 120, 80
        mouse = pygame.mouse.get_pos()
        if is_hibrida:
            self.btn_andar_rect = pygame.Rect(mx + 20, my + 90, btn_w, btn_h)
            self.btn_coletar_rect = pygame.Rect(mx + 160, my + 90, btn_w, btn_h)
            self.btn_ambos_rect = pygame.Rect(mx + 300, my + 90, btn_w, btn_h)
            self.btn_atacar_rect = pygame.Rect(mx + 440, my + 90, btn_w, btn_h)
            b_andar_cor = (30, 80, 30) if self.btn_andar_rect.collidepoint(mouse) else (20, 50, 20)
            pygame.draw.rect(tela, b_andar_cor, self.btn_andar_rect, border_radius=6)
            pygame.draw.rect(tela, (85, 205, 85), self.btn_andar_rect, 1, border_radius=6)
            lbl_a1 = self.fMi.render("ANDAR", True, (200, 255, 200))
            lbl_a2 = self.fP.render(f"+{pm} PM", True, C_TEXTO)
            tela.blit(lbl_a1, (self.btn_andar_rect.centerx - lbl_a1.get_width() // 2, self.btn_andar_rect.y + 20))
            tela.blit(lbl_a2, (self.btn_andar_rect.centerx - lbl_a2.get_width() // 2, self.btn_andar_rect.y + 44))
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
            b_ambos_cor = (30, 70, 80) if self.btn_ambos_rect.collidepoint(mouse) else (20, 45, 50)
            pygame.draw.rect(tela, b_ambos_cor, self.btn_ambos_rect, border_radius=6)
            pygame.draw.rect(tela, (100, 220, 240), self.btn_ambos_rect, 1, border_radius=6)
            lbl_ab1 = self.fMi.render("AMBOS", True, (200, 240, 255))
            lbl_ab2 = self.fP.render("ANDAR+COL", True, C_TEXTO)
            tela.blit(lbl_ab1, (self.btn_ambos_rect.centerx - lbl_ab1.get_width() // 2, self.btn_ambos_rect.y + 20))
            tela.blit(lbl_ab2, (self.btn_ambos_rect.centerx - lbl_ab2.get_width() // 2, self.btn_ambos_rect.y + 44))
            b_atacar_cor = (80, 20, 20) if self.btn_atacar_rect.collidepoint(mouse) else (50, 10, 10)
            pygame.draw.rect(tela, b_atacar_cor, self.btn_atacar_rect, border_radius=6)
            pygame.draw.rect(tela, (255, 100, 100), self.btn_atacar_rect, 1, border_radius=6)
            lbl_at1 = self.fMi.render("ATACAR", True, (255, 200, 200))
            lbl_at2 = self.fP.render("COMBATE", True, C_DIM)
            tela.blit(lbl_at1, (self.btn_atacar_rect.centerx - lbl_at1.get_width() // 2, self.btn_atacar_rect.y + 20))
            tela.blit(lbl_at2, (self.btn_atacar_rect.centerx - lbl_at2.get_width() // 2, self.btn_atacar_rect.y + 44))
        else:
            self.btn_ambos_rect = None
            self.btn_andar_rect = pygame.Rect(mx + 20, my + 90, btn_w, btn_h)
            self.btn_coletar_rect = pygame.Rect(mx + 160, my + 90, btn_w, btn_h)
            self.btn_atacar_rect = pygame.Rect(mx + 300, my + 90, btn_w, btn_h)
            b_andar_cor = (30, 80, 30) if self.btn_andar_rect.collidepoint(mouse) else (20, 50, 20)
            pygame.draw.rect(tela, b_andar_cor, self.btn_andar_rect, border_radius=6)
            pygame.draw.rect(tela, (85, 205, 85), self.btn_andar_rect, 1, border_radius=6)
            lbl_a1 = self.fMi.render("ANDAR", True, (200, 255, 200))
            lbl_a2 = self.fP.render(f"+{pm} PM", True, C_TEXTO)
            tela.blit(lbl_a1, (self.btn_andar_rect.centerx - lbl_a1.get_width() // 2, self.btn_andar_rect.y + 20))
            tela.blit(lbl_a2, (self.btn_andar_rect.centerx - lbl_a2.get_width() // 2, self.btn_andar_rect.y + 44))
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
            b_atacar_cor = (80, 20, 20) if self.btn_atacar_rect.collidepoint(mouse) else (50, 10, 10)
            pygame.draw.rect(tela, b_atacar_cor, self.btn_atacar_rect, border_radius=6)
            pygame.draw.rect(tela, (255, 100, 100), self.btn_atacar_rect, 1, border_radius=6)
            lbl_at1 = self.fMi.render("ATACAR", True, (255, 200, 200))
            lbl_at2 = self.fP.render("COMBATE", True, C_DIM)
            tela.blit(lbl_at1, (self.btn_atacar_rect.centerx - lbl_at1.get_width() // 2, self.btn_atacar_rect.y + 20))
            tela.blit(lbl_at2, (self.btn_atacar_rect.centerx - lbl_at2.get_width() // 2, self.btn_atacar_rect.y + 44))
        lbl_esc = self.fMi.render("Pressione [ESC] para cancelar", True, C_DIM)
        tela.blit(lbl_esc, (modal_rect.centerx - lbl_esc.get_width() // 2, my + 194))

    # ── MENU DEV ─────────────────────────────────────────────────────────
    def _desenhar_dev_menu(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 6, 12, 220))
        tela.blit(overlay, (0, 0))
        pw, ph = 840, 360
        px = (W - pw) // 2
        py = (H - ph) // 2
        pygame.draw.rect(tela, (14, 16, 30), (px, py, pw, ph), border_radius=12)
        pygame.draw.rect(tela, C_ACENTO, (px, py, pw, ph), 2, border_radius=12)
        titulo = self.fG.render("MENU DEV: SELECIONE O INIMIGO PARA INVOCAR", True, C_OURO)
        tela.blit(titulo, (px + pw // 2 - titulo.get_width() // 2, py + 20))
        sub = self.fMi.render("Pressione F12 ou ESC para fechar", True, C_DIM)
        tela.blit(sub, (px + pw // 2 - sub.get_width() // 2, py + 48))
        x0 = px + 25
        y0 = py + 70
        cw, ch = 190, 35
        gap_x, gap_y = 10, 10
        mouse = pygame.mouse.get_pos()
        from ...cerco_isectum import DADOS_INIMIGOS
        keys = list(DADOS_INIMIGOS.keys())
        for idx, key in enumerate(keys):
            info = DADOS_INIMIGOS[key]
            col = idx % 4
            row = idx // 4
            bx = x0 + col * (cw + gap_x)
            by = y0 + row * (ch + gap_y)
            r = pygame.Rect(bx, by, cw, ch)
            hover = r.collidepoint(mouse)
            bg_cor = (30, 32, 54) if hover else (22, 24, 40)
            borda_cor = C_ACENTO if hover else C_BORDA
            pygame.draw.rect(tela, bg_cor, r, border_radius=6)
            pygame.draw.rect(tela, borda_cor, r, 1, border_radius=6)
            txt = f"{info['emoji']} {info['nome']}"
            txt_surf = self.fP.render(txt, True, C_TEXTO)
            if txt_surf.get_width() > cw - 12:
                txt_surf = self.fMi.render(txt, True, C_TEXTO)
            tela.blit(txt_surf, (r.x + 8, r.centery - txt_surf.get_height() // 2))
