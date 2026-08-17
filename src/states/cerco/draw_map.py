"""
draw_map.py — Mixin de renderização do mapa tático (2D isométrico, terreno, sprites e unidades) para CercoState.
"""
from __future__ import annotations
import math
import random
import zlib
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from ...utils import remover_emojis, sanitizar_texto_fonte
from .data import (
    C_OURO, C_CRISTAL, C_BORDA, C_VERDE, C_ACENTO,
    C_PERIGO, C_CERCO, C_TEXTO, C_DIM, C_BRUTE,
    ZONA_TERRENO_MAP,
    MODO_MOVER, MODO_CONVOCAR,
)


class CercoDrawMapMixin:
    """Sub-mixin com renderização de mapa, polígonos, texturas e sprites."""

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

    def _draw_mapa(self, tela):
        r = self.mapa_rect

        # 🎥 CÂMERA CINEMATOGRÁFICA ACTION ZOOM (Interpolação Suave)
        if getattr(self, "camera_zoom_timer", 0) > 0:
            self.camera_zoom_timer -= 1
            self.map_backbuffer_sujo = True
            if self.camera_zoom_timer <= 0:
                self.zoom_alvo = getattr(self, "zoom_base", 1.0)
                self.foco_grid_alvo = None
                self.map_backbuffer_sujo = True

        target_z = getattr(self, "zoom_alvo", 1.0)
        curr_z = getattr(self, "zoom", 1.0)
        if abs(curr_z - target_z) > 0.005:
            self.zoom += (target_z - curr_z) * 0.12
            self.map_backbuffer_sujo = True

        theta = self.game.angulo_rotacao
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)

        # 🎥 Deslocamento e Interpolação Suave de Câmera (Soft Target Following)
        foco_alvo = getattr(self, "foco_grid_alvo", None)
        if not foco_alvo:
            # Quando não há Action Zoom de combate ativo, a câmera segue suavemente o herói ativo
            h_ativo = getattr(self, "heroi_atual", None)
            if h_ativo and hasattr(h_ativo, "pos_x"):
                foco_alvo = (h_ativo.pos_x, h_ativo.pos_y)
            else:
                foco_alvo = (9.5, 9.5)

        if not hasattr(self, "foco_grid_atual") or self.foco_grid_atual is None:
            self.foco_grid_atual = [float(foco_alvo[0]), float(foco_alvo[1])]

        dx_c = (foco_alvo[0] - self.foco_grid_atual[0])
        dy_c = (foco_alvo[1] - self.foco_grid_atual[1])
        if abs(dx_c) > 0.005 or abs(dy_c) > 0.005:
            self.foco_grid_atual[0] += dx_c * 0.12
            self.foco_grid_atual[1] += dy_c * 0.12
            self.map_backbuffer_sujo = True  # Atualiza a visualização da câmera a cada frame

        fgx, fgy = self.foco_grid_atual[0], self.foco_grid_atual[1]
        dx_f = fgx - 9.5
        dy_f = fgy - 9.5
        rx_f = dx_f * theta_cos - dy_f * theta_sin
        ry_f = dx_f * theta_sin + dy_f * theta_cos
        offset_cx = -int((rx_f - ry_f) * (max(6, int(24 * self.zoom)) // 2) * 0.95)
        offset_cy = -int((rx_f + ry_f) * (max(3, int(12 * self.zoom)) // 2) * 0.95)

        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        CX = r.centerx + offset_cx
        CY = r.centery - 5 + offset_cy
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
        from ...resolvedor_acoes import obter_zona_por_coordenada as _oz

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
                tg = getattr(self.motor.tabuleiro, 'terrain_grid', None)
                terreno_tile = tg[gy][gx] if (tg and 0 <= gy < len(tg) and 0 <= gx < len(tg[0])) else None
                has_tree = False
                if zona_key in ("_campo", "_exterior"):
                    val = zlib.adler32(f"tree_{gx}_{gy}".encode())
                    if val % 100 < 30:
                        has_tree = True

                if has_tree:
                    num_arvores_mortas = min(30, self.estado.get("total_inimigos_gerados", 0) // 4)
                    tree_order = (zlib.adler32(f"tree_order_{gx}_{gy}".encode())) % 30
                    is_morta = tree_order < num_arvores_mortas

                    trunk_w = max(2, int(6 * self.zoom))
                    trunk_h = max(4, int(16 * self.zoom))

                    r1 = max(4, int(13 * self.zoom))
                    r2 = max(3, int(10 * self.zoom))
                    r3 = max(2, int(7 * self.zoom))

                    if is_morta:
                        sombra_base = pygame.Surface((int(14 * self.zoom), int(7 * self.zoom)), pygame.SRCALPHA)
                        pygame.draw.ellipse(sombra_base, (40, 0, 50, 55), (0, 0, sombra_base.get_width(), sombra_base.get_height()))
                        self.map_backbuffer.blit(sombra_base, (cx_ - sombra_base.get_width() // 2, cy_ - sombra_base.get_height() // 2))

                        pygame.draw.rect(self.map_backbuffer, (50, 42, 38), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h))
                        pygame.draw.rect(self.map_backbuffer, (30, 25, 20), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h), 1)

                        pygame.draw.circle(self.map_backbuffer, (75, 40, 85), (cx_, cy_ - trunk_h), r1)
                        pygame.draw.circle(self.map_backbuffer, (45, 20, 55), (cx_, cy_ - trunk_h), r1, 1)
                        pygame.draw.circle(self.map_backbuffer, (105, 50, 115), (cx_, cy_ - trunk_h - int(7 * self.zoom)), r2)
                        pygame.draw.circle(self.map_backbuffer, (65, 30, 75), (cx_, cy_ - trunk_h - int(7 * self.zoom)), r2, 1)
                        pygame.draw.circle(self.map_backbuffer, (130, 65, 140), (cx_, cy_ - trunk_h - int(13 * self.zoom)), r3)
                        pygame.draw.circle(self.map_backbuffer, (85, 40, 95), (cx_, cy_ - trunk_h - int(13 * self.zoom)), r3, 1)

                        sp_off = int(4 * self.zoom)
                        sp_r = max(1, int(2 * self.zoom))
                        pygame.draw.circle(self.map_backbuffer, (190, 210, 110), (cx_ - sp_off, cy_ - trunk_h - sp_off), sp_r)
                        pygame.draw.circle(self.map_backbuffer, (210, 180, 90), (cx_ + sp_off, cy_ - trunk_h - int(9 * self.zoom)), sp_r)
                        pygame.draw.circle(self.map_backbuffer, (160, 230, 140), (cx_, cy_ - trunk_h - int(14 * self.zoom)), sp_r)
                    else:
                        sombra = pygame.Surface((int(24 * self.zoom), int(12 * self.zoom)), pygame.SRCALPHA)
                        pygame.draw.ellipse(sombra, (0, 0, 0, 70), (0, 0, sombra.get_width(), sombra.get_height()))
                        self.map_backbuffer.blit(sombra, (cx_ - sombra.get_width() // 2, cy_ - sombra.get_height() // 2))

                        pygame.draw.rect(self.map_backbuffer, (85, 55, 30), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h))
                        pygame.draw.rect(self.map_backbuffer, (55, 35, 20), (cx_ - trunk_w // 2, cy_ - trunk_h, trunk_w, trunk_h), 1)

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
                                ch_w = max(5, int(8 * self.zoom))
                                ch_h = max(7, int(11 * self.zoom))
                                pts = [
                                    (bx, by - ch_h // 2),
                                    (bx + ch_w // 2, by - ch_h // 6),
                                    (bx + ch_w // 3, by + ch_h // 2),
                                    (bx - ch_w // 3, by + ch_h // 2),
                                    (bx - ch_w // 2, by - ch_h // 6),
                                ]
                                pygame.draw.polygon(self.map_backbuffer, (110, 20, 160), pts)
                                top_pts = [(bx, by - ch_h // 2), (bx + ch_w // 2, by - ch_h // 6), (bx, by), (bx - ch_w // 2, by - ch_h // 6)]
                                pygame.draw.polygon(self.map_backbuffer, (210, 140, 255), top_pts)
                                pygame.draw.polygon(self.map_backbuffer, (245, 210, 255), top_pts, 1)
                                pygame.draw.polygon(self.map_backbuffer, (70, 10, 110), pts, 1)
            self.map_backbuffer_sujo = False
        tela.blit(self.map_backbuffer, (r.x, r.y))
        labels_pendentes = {}
        ZONA_LABELS = {
            "camara_central": ("CAMARA CENTRAL (CRISTAL ROXO)", C_CRISTAL),
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
            if self.modo_acao == MODO_CONVOCAR and GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                if tab.grid[gy][gx] is None and tab.get_terrain_em(gx, gy) != "parede":
                    tipo_m = getattr(self, 'tipo_mercenario_selecionado', 'melee')
                    valido = True
                    if tipo_m == "minerador":
                        valido = (zona_key == "patio" or tab.get_terrain_em(gx, gy) in ("patio", "rocha", "barril", "fogo"))
                    elif tipo_m == "arqueiro":
                        valido = bool(zona_key and zona_key.startswith("torre"))

                    if valido:
                        if is_hover:
                            self._draw_celula_tactica(tela, gx, gy, el, (200, 100, 255, 110), (255, 220, 255), estilo='movimento')
                        else:
                            self._draw_celula_tactica(tela, gx, gy, el, (160, 80, 240, 45), (200, 140, 255), estilo='movimento')
            if campo_dir and zona_key == "_campo":
                inv_campo = e.get(campo_dir, 0)
                if inv_campo > 0:
                    pulso = abs((self.timer % 90) - 45) / 45.0
                    self._draw_celula_tactica(tela, gx, gy, el, (255, 0, 0, int(35 + 25 * pulso)), (255, 50, 50), estilo='ataque')
            if zona_key not in labels_pendentes and zona_key in ZONA_LABELS:
                from ...resolvedor_acoes import ZONAS_GRID as _ZG
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
                    from ...ui.render_combate import desenhar_sprite
                    sw, sh = max(10, int(24 * self.zoom)), max(10, int(24 * self.zoom))
                    cx_draw, cy_draw = self._get_char_screen_pos(char, vgx, vgy, vel, default_cx, default_cy)
                    rect_char = pygame.Rect(cx_draw - sw // 2, cy_draw - sh + 2, sw, sh)
                    eh_atual = char is self.heroi_atual
                    eh_mercenario = getattr(char, '_is_mercenario', False)
                    cor_char = (100, 215, 255) if eh_atual else ((220, 100, 255) if eh_mercenario else (200, 180, 255))
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
                    elif eh_mercenario:
                        pulse_m = abs(self.timer % 90 - 45) / 45.0
                        pr_m = max(2, int((3 + 2 * pulse_m) * self.zoom))
                        pygame.draw.circle(tela, (210, 120, 255), (cx_draw, cy_draw), pr_m, max(1, int(1.5 * self.zoom)))
                        simb_rec = getattr(char, "simbolo_recurso", None)
                        if simb_rec:
                            txt_rec = self.fMi.render(simb_rec, True, (255, 255, 255))
                            tela.blit(txt_rec, (cx_draw - int(6 * self.zoom), cy_draw - sh - int(18 * self.zoom)))

                    if getattr(char, "em_vigilancia", False) and getattr(char, "hp_atual", 0) > 0:
                        txt_vigi = self.fMi.render(sanitizar_texto_fonte("👁️ VIGILÂNCIA"), True, (255, 235, 80))
                        tela.blit(txt_vigi, (cx_draw - txt_vigi.get_width() // 2, cy_draw - sh - int(24 * self.zoom)))

                    # ── BADGE DE COBERTURA TÁTICA (+3 / +5 AC) ──────────
                    tab = getattr(self.motor, "tabuleiro", None)
                    if tab and hasattr(tab, "obter_bonificacao_cobertura"):
                        bonus_cob = tab.obter_bonificacao_cobertura(gx, gy)
                        if bonus_cob > 0 and getattr(char, "hp_atual", 0) > 0:
                            lbl_cob = self.fMi.render(sanitizar_texto_fonte(f"🛡️ COBERTURA (+{bonus_cob} AC)"), True, (120, 240, 160))
                            tela.blit(lbl_cob, (cx_draw - lbl_cob.get_width() // 2, cy_draw - sh - int(34 * self.zoom)))
                    # ── BARRA DE VIDA (HP) ACIMA DO PERSONAGEM ────────
                    hp_cur = getattr(char, "hp_atual", 10)
                    hp_max = max(1, getattr(char, "hp_max", 10))
                    pct_hp = max(0.0, min(1.0, hp_cur / hp_max))

                    bar_w = max(18, int(24 * self.zoom))
                    bar_h = max(3, int(4 * self.zoom))
                    bar_x = cx_draw - bar_w // 2
                    bar_y = cy_draw - sh - max(2, int(4 * self.zoom))

                    pygame.draw.rect(tela, (12, 12, 18), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=2)
                    cor_hp = (60, 220, 90) if pct_hp > 0.5 else ((240, 200, 40) if pct_hp >= 0.25 else (240, 50, 50))
                    fill_w = int(bar_w * pct_hp)
                    if fill_w > 0:
                        pygame.draw.rect(tela, cor_hp, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
                    pygame.draw.rect(tela, (40, 40, 60), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 1, border_radius=2)

                    # ── CARD COMPLETO DE STATS (VIDA, ATAQUE, DEFESA) AO PASSAR O MOUSE / SELECIONAR ──
                    mouse_pos = pygame.mouse.get_pos()
                    is_hover = rect_char.inflate(20, 20).collidepoint(mouse_pos)
                    if eh_atual or is_hover:
                        nome_raw = getattr(char, 'nome', '')
                        if getattr(char, '_is_mercenario', False):
                            tipo_m = getattr(char, 'tipo_mercenario', 'melee')
                            mapa_nomes = {'melee': 'Guarda', 'arqueiro': 'Arqueiro', 'minerador': 'Minerador'}
                            nome_exibido = mapa_nomes.get(tipo_m, 'Mercenário')
                        else:
                            nome_exibido = "?????" if nome_raw == "Aquele" else remover_emojis(nome_raw)

                        atk_val = getattr(char, 'bonus_ataque', getattr(char, '_bonus_ataque_override', 3))
                        dado_d = getattr(char, 'dado_dano', (1, 6))
                        d_str = f"{dado_d[0]}d{dado_d[1]}" if isinstance(dado_d, (tuple, list)) else str(dado_d)
                        def_val = getattr(char, 'ac', getattr(char, 'ac_base', 10))

                        stats_str = f"❤️{hp_cur}/{hp_max} ⚔️+{atk_val}({d_str}) 🛡️{def_val}"

                        nome_s = self.fMi.render(nome_exibido, True, (240, 230, 255))
                        stats_s = self.fMi.render(stats_str, True, (210, 230, 255))

                        if self.zoom != 1.0:
                            w_s1 = max(1, int(nome_s.get_width() * self.zoom))
                            h_s1 = max(1, int(nome_s.get_height() * self.zoom))
                            nome_s = pygame.transform.smoothscale(nome_s, (w_s1, h_s1))

                            w_s2 = max(1, int(stats_s.get_width() * self.zoom))
                            h_s2 = max(1, int(stats_s.get_height() * self.zoom))
                            stats_s = pygame.transform.smoothscale(stats_s, (w_s2, h_s2))

                        card_w = max(nome_s.get_width(), stats_s.get_width()) + 12
                        card_h = nome_s.get_height() + stats_s.get_height() + 6

                        card_x = cx_draw - card_w // 2
                        card_y = bar_y - card_h - 4

                        s_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                        s_bg.fill((12, 10, 22, 220))
                        pygame.draw.rect(s_bg, (180, 140, 255) if eh_mercenario else (100, 200, 255), (0, 0, card_w, card_h), 1, border_radius=5)
                        tela.blit(s_bg, (card_x, card_y))

                        tela.blit(nome_s, (card_x + (card_w - nome_s.get_width()) // 2, card_y + 2))
                        tela.blit(stats_s, (card_x + (card_w - stats_s.get_width()) // 2, card_y + 3 + nome_s.get_height()))

            # Desenha o Príncipe Lysander fora do tabuleiro como oponente comandante
            if gx == -3 and gy == -3:
                ia_cmd = getattr(self, 'ia_comandante', None)
                if ia_cmd is not None:
                    pulso = (math.sin(self.timer * 0.1) + 1.0) / 2.0
                    radius = max(12, int(28 * self.zoom))
                    sombra = pygame.Surface((radius * 2, radius), pygame.SRCALPHA)
                    pygame.draw.ellipse(sombra, (30, 5, 5, int(120 + 30 * pulso)), (0, 0, radius * 2, radius))
                    tela.blit(sombra, (cx_ - radius, cy_ - radius // 2))

                    cor_aura = (
                        int(200 + 55 * pulso),
                        int(50 + 20 * pulso),
                        50
                    )
                    pygame.draw.ellipse(tela, cor_aura,
                                        pygame.Rect(cx_ - radius, cy_ - radius // 2, radius * 2, radius),
                                        2)

                    from ...personagens.novos_personagens import FilhoDoImperador
                    if not hasattr(self, '_mock_principe'):
                        self._mock_principe = FilhoDoImperador("Príncipe Lysander", "B")

                    sw, sh = max(14, int(32 * self.zoom)), max(14, int(32 * self.zoom))
                    rect_prince = pygame.Rect(cx_ - sw // 2, cy_ - sh + 4, sw, sh)
                    cor_destaque = (255, 100, 100) if self.fase == "TURNO_FILHO_IMPERADOR" else (200, 80, 80)

                    from ...ui.render_combate import desenhar_sprite
                    desenhar_sprite(tela, self._mock_principe, rect_prince, cor_destaque, self.game.imagens, self.game.sprites_visiveis)

                    px_mastro = cx_ + int(20 * self.zoom)
                    py_mastro = cy_ - int(5 * self.zoom)
                    pygame.draw.line(tela, (140, 110, 50), (px_mastro, py_mastro + 4), (px_mastro, py_mastro - int(40 * self.zoom)), 3)
                    pts_bandeira = [
                        (px_mastro, py_mastro - int(40 * self.zoom)),
                        (px_mastro + int(18 * self.zoom), py_mastro - int(34 * self.zoom)),
                        (px_mastro + int(12 * self.zoom), py_mastro - int(27 * self.zoom)),
                        (px_mastro + int(18 * self.zoom), py_mastro - int(20 * self.zoom)),
                        (px_mastro, py_mastro - int(20 * self.zoom)),
                    ]
                    pygame.draw.polygon(tela, (180, 20, 20), pts_bandeira)
                    pygame.draw.polygon(tela, (255, 210, 40), pts_bandeira, 1)

                    lbl_prince = self.fMi.render("Pr. Lysander", True, (255, 120, 120))
                    tela.blit(lbl_prince, (cx_ - lbl_prince.get_width() // 2, cy_ - sh - int(14 * self.zoom)))

                    lbl_tag = self.fMi.render(sanitizar_texto_fonte("👑 COMANDANTE"), True, (255, 220, 40))
                    tela.blit(lbl_tag, (cx_ - lbl_tag.get_width() // 2, cy_ - sh - int(28 * self.zoom)))

        e = self.estado
        for zona_key, (lcx, lcy) in labels_pendentes.items():
            y_off = lcy - int(8 * self.zoom)
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
        # 🏃 RENDERIZAÇÃO DA TRILHA DE PATHFINDING A* (Caminho Visual Dinâmico)
        if hovered_g and hasattr(self, "heroi_atual") and self.heroi_atual:
            pts_mov = self.estado.get("pontos_movimento", 0)
            hx, hy = self.heroi_atual.pos_x, self.heroi_atual.pos_y
            if pts_mov > 0 and (hx, hy) != hovered_g and hasattr(tab, "encontrar_caminho"):
                caminho = tab.encontrar_caminho(hx, hy, hovered_g[0], hovered_g[1], max_passos=pts_mov)
                if caminho:
                    pontos_tela = []
                    _, h_el = _classificar(hx, hy)
                    pontos_tela.append(_iso(hx, hy, h_el))
                    for px, py in caminho:
                        _, p_el = _classificar(px, py)
                        pontos_tela.append(_iso(px, py, p_el))

                    if len(pontos_tela) >= 2:
                        pygame.draw.lines(tela, (60, 200, 255), False, pontos_tela, max(2, int(3 * self.zoom)))

                    pulse_val = abs(self.timer % 60 - 30) / 30.0
                    for idx_step, (sx, sy) in enumerate(pontos_tela[1:], 1):
                        r_dot = max(3, int((4 + 2 * pulse_val) * self.zoom))
                        pygame.draw.circle(tela, (20, 30, 50), (sx, sy), r_dot + 2)
                        pygame.draw.circle(tela, (100, 220, 255), (sx, sy), r_dot)
                        pygame.draw.circle(tela, (255, 255, 255), (sx, sy), max(1, r_dot - 2))

                    dest_sx, dest_sy = pontos_tela[-1]
                    lbl_passos = self.fMi.render(sanitizar_texto_fonte(f"🚶 {len(caminho)} PM"), True, (255, 235, 120))
                    bg_badge = pygame.Rect(dest_sx - lbl_passos.get_width() // 2 - 4, dest_sy - int(22 * self.zoom), lbl_passos.get_width() + 8, 16)
                    pygame.draw.rect(tela, (15, 20, 35), bg_badge, border_radius=4)
                    pygame.draw.rect(tela, (255, 215, 80), bg_badge, 1, border_radius=4)
                    tela.blit(lbl_passos, (dest_sx - lbl_passos.get_width() // 2, dest_sy - int(21 * self.zoom)))

        self._draw_popups_combate(tela)
        self._draw_armas_cerco(tela)
        nr = self.fMi.render(self.narrativa[:88], True, C_DIM)
        tela.blit(nr, (r.x + 8, r.bottom - 18))

    def _push_popup_combate(self, gx, gy, texto, cor=(255, 60, 60)):
        """Adiciona um texto flutuante de dano/combate no grid 2D."""
        if not hasattr(self, "popups_combate"):
            self.popups_combate = []
        self.popups_combate.append({
            'gx': gx,
            'gy': gy,
            'texto': texto,
            'cor': cor,
            'timer': 60,
            'max_timer': 60,
            'y_offset': 0
        })

    def _draw_popups_combate(self, tela):
        """Renderiza textos flutuantes de dano e combate subindo no grid isométrico."""
        if not hasattr(self, "popups_combate") or not self.popups_combate:
            return

        import math
        theta = math.radians(45)
        theta_cos = math.cos(theta)
        theta_sin = math.sin(theta)

        r = self.mapa_rect
        CX = r.centerx
        CY = r.centery - 5
        TW = int(64 * self.zoom)
        TH = int(32 * self.zoom)

        atrasados = []
        for pop in list(self.popups_combate):
            pop['timer'] -= 1
            pop['y_offset'] += 0.8 * self.zoom
            if pop['timer'] <= 0:
                continue
            atrasados.append(pop)

            gx, gy = pop['gx'], pop['gy']
            dx = gx - 9.5
            dy = gy - 9.5
            rx = dx * theta_cos - dy * theta_sin
            ry = dx * theta_sin + dy * theta_cos
            cx = int((rx - ry) * (TW // 2) + CX)
            cy = int((rx + ry) * (TH // 2) + CY)

            y_draw = cy - int(32 * self.zoom) - int(pop['y_offset'])

            txt_surf = self.fM.render(sanitizar_texto_fonte(pop['texto']), True, pop['cor'])
            if self.zoom != 1.0:
                w_s = max(1, int(txt_surf.get_width() * self.zoom))
                h_s = max(1, int(txt_surf.get_height() * self.zoom))
                txt_surf = pygame.transform.smoothscale(txt_surf, (w_s, h_s))
            else:
                w_s, h_s = txt_surf.get_width(), txt_surf.get_height()

            txt_sombra = self.fM.render(sanitizar_texto_fonte(pop['texto']), True, (10, 10, 15))
            if self.zoom != 1.0:
                txt_sombra = pygame.transform.smoothscale(txt_sombra, (w_s, h_s))

            x_draw = cx - txt_surf.get_width() // 2
            tela.blit(txt_sombra, (x_draw + 1, y_draw + 1))
            tela.blit(txt_surf, (x_draw, y_draw))

        self.popups_combate = atrasados

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

    def _focar_camera_combate(self, gx, gy, zoom=1.85, duracao=55):
        """Ativa a câmera cinematográfica deslizando e dando zoom na cena de ataque."""
        if getattr(self, "autoplay_ativo", False):
            return
        self.zoom_alvo = zoom
        self.foco_grid_alvo = (gx, gy)
        self.camera_zoom_timer = duracao
        self.map_backbuffer_sujo = True
