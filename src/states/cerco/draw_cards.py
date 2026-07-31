"""
draw_cards.py — Mixin de renderização de cartas da mão e overlays de ameça para CercoState.
"""
from __future__ import annotations
import math
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_TEXTO, C_DIM, C_CERCO, C_PAINEL,
)


class CercoDrawCardsMixin:
    """Sub-mixin com a renderização de cartas da mão e overlay de ameaça."""

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
        deck_ini_qtd = len(self.deck) if (hasattr(self, 'deck') and self.deck is not None) else len(self.estado.get("deck_inimigos", []))
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
            info_ini = DADOS_INIMIGOS.get(ultima_carta, {"nome": ultima_carta, "emoji": "", "antigo": ""})
            nome_lbl1 = self.fMi.render("REVELADO", True, C_DIM)
            nome_lbl2 = self.fMi.render(info_ini['nome'], True, C_PERIGO)
            if nome_lbl2.get_width() > 90:
                nome_lbl2 = self.fP.render(info_ini['nome'], True, C_PERIGO)
            if nome_lbl2.get_width() > 90:
                nome_lbl2 = self.fMi.render(f"{info_ini['nome'][:8]}...", True, C_PERIGO)
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
            
            eh_upgrade = carta.get("tipo") == "upgrade"
            tipo_gema = "movimento"
            if carta.get("trabalho"):  tipo_gema = "trabalho"
            if carta.get("escavacao"): tipo_gema = "escavacao"
            cor_gema = GEMAS_COR.get(tipo_gema, (200, 200, 200))
            if eh_upgrade:
                cor_gema = (255, 200, 50)

            sprite = None

            if eh_upgrade:
                c_top = (90, 65, 14) if hover else (70, 48, 10)
                c_bot = (40, 26, 4)
            elif tipo_gema == "movimento":
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
                grad = pygame.Surface((2, 2))
                grad.set_at((0, 0), c_top); grad.set_at((1, 0), c_top)
                grad.set_at((0, 1), c_bot); grad.set_at((1, 1), c_bot)
                grad_scaled = pygame.transform.smoothscale(grad, (cw, ch))
                tela.blit(grad_scaled, crect.topleft)

            borda_cor = C_ACENTO if sel else (C_OURO if hover else C_BORDA)
            pygame.draw.rect(tela, borda_cor, crect, 2 if sel or hover else 1, border_radius=7)
            
            cor_chanfro = (c_top[0]+25, c_top[1]+25, c_top[2]+25) if hover else (c_top[0]+12, c_top[1]+12, c_top[2]+12)
            pygame.draw.rect(tela, cor_chanfro, crect.inflate(-4, -4), 1, border_radius=6)
            
            pygame.draw.rect(tela, (4, 4, 6), crect.inflate(-6, -6), 1, border_radius=5)

            if not sprite:
                art_rect = pygame.Rect(crect.x + 6, crect.y + 24, cw - 12, 38)
                pygame.draw.rect(tela, (8, 6, 12), art_rect, border_radius=4)
                pygame.draw.rect(tela, (36, 36, 48), art_rect, 1, border_radius=4)
                
                if tipo_gema == "movimento":
                    pygame.draw.line(tela, (60, 160, 255), (art_rect.x + 8, art_rect.bottom - 8), (art_rect.right - 15, art_rect.y + 8), 2)
                    pygame.draw.line(tela, (120, 220, 255), (art_rect.x + 20, art_rect.bottom - 8), (art_rect.right - 6, art_rect.y + 8), 1)
                    pygame.draw.circle(tela, (30, 80, 160), (art_rect.centerx, art_rect.centery), 6)
                    pygame.draw.circle(tela, (100, 210, 255), (art_rect.centerx, art_rect.centery), 3)
                elif tipo_gema == "trabalho":
                    pygame.draw.circle(tela, (40, 110, 60), (art_rect.centerx, art_rect.centery), 12, 1)
                    pygame.draw.circle(tela, (90, 220, 110), (art_rect.centerx, art_rect.centery), 6, 1)
                    pygame.draw.line(tela, (70, 170, 90), (art_rect.x + 8, art_rect.centery), (art_rect.right - 8, art_rect.centery), 1)
                    pygame.draw.line(tela, (70, 170, 90), (art_rect.centerx, art_rect.y + 4), (art_rect.centerx, art_rect.bottom - 4), 1)
                elif tipo_gema == "escavacao":
                    p1 = [(art_rect.centerx, art_rect.y + 6), (art_rect.centerx + 7, art_rect.centery), (art_rect.centerx, art_rect.bottom - 6), (art_rect.centerx - 7, art_rect.centery)]
                    p2 = [(art_rect.centerx - 9, art_rect.y + 10), (art_rect.centerx - 4, art_rect.centery + 3), (art_rect.centerx - 9, art_rect.bottom - 10), (art_rect.centerx - 14, art_rect.centery + 3)]
                    p3 = [(art_rect.centerx + 9, art_rect.y + 10), (art_rect.centerx + 14, art_rect.centery + 3), (art_rect.centerx + 9, art_rect.bottom - 10), (art_rect.centerx + 4, art_rect.centery + 3)]
                    pygame.draw.polygon(tela, (180, 130, 30), p2)
                    pygame.draw.polygon(tela, (180, 130, 30), p3)
                    pygame.draw.polygon(tela, (255, 215, 80), p1)
                    pygame.draw.line(tela, (255, 250, 210), (art_rect.centerx, art_rect.y + 6), (art_rect.centerx - 7, art_rect.centery), 1)
                else:
                    pygame.draw.line(tela, (40, 40, 50), (art_rect.x + 10, art_rect.y + 10), (art_rect.right - 10, art_rect.bottom - 10), 1)
                    pygame.draw.line(tela, (40, 40, 50), (art_rect.right - 10, art_rect.y + 10), (art_rect.x + 10, art_rect.bottom - 10), 1)

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
            pygame.draw.line(tela, (255, 255, 255), (rx_center, ry_center - 7), (rx_center - 7, ry_center), 1)
            pygame.draw.line(tela, (255, 255, 255), (rx_center, ry_center), (rx_center - 7, ry_center), 1)

            banner_rect = pygame.Rect(crect.x + 8, crect.y + 66, cw - 16, 18)
            pygame.draw.rect(tela, (8, 8, 12, 220), banner_rect, border_radius=4)
            pygame.draw.rect(tela, (42, 42, 54), banner_rect, 1, border_radius=4)
            
            nome_cortado = carta["nome"][:14]
            nt = self.fMi.render(nome_cortado, True, C_OURO if sel else C_TEXTO)
            tela.blit(nt, (banner_rect.centerx - nt.get_width() // 2, banner_rect.y + 3))

            desc = carta.get("descricao", "")
            if desc:
                lbl_desc = self.fMi.render(desc[:22], True, C_DIM)
                tela.blit(lbl_desc, (crect.centerx - lbl_desc.get_width() // 2, crect.y + 88))

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

            if eh_upgrade:
                star_lbl = self.fMi.render("⭐ PERMANENTE", True, (255, 220, 60))
                star_bg = pygame.Rect(crect.centerx - star_lbl.get_width() // 2 - 4,
                                      crect.y + 42, star_lbl.get_width() + 8, 16)
                pygame.draw.rect(tela, (50, 36, 4), star_bg, border_radius=3)
                pygame.draw.rect(tela, (200, 160, 30), star_bg, 1, border_radius=3)
                tela.blit(star_lbl, (crect.centerx - star_lbl.get_width() // 2, crect.y + 43))
            elif sel:
                ql = self.fMi.render("DESCARTE", True, C_PERIGO)
                ql_bg = pygame.Rect(crect.centerx - ql.get_width() // 2 - 4, crect.y + 42, ql.get_width() + 8, 16)
                pygame.draw.rect(tela, (40, 10, 10), ql_bg, border_radius=3)
                pygame.draw.rect(tela, C_PERIGO, ql_bg, 1, border_radius=3)
                tela.blit(ql, (crect.centerx - ql.get_width() // 2, crect.y + 43))

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
        tipo_lbl = {"invasor": "HORDA DE INSETOS", "mover": "AVANÇO DE INSETOS",
                    "torre_assalto": "TORRE DE ASSALTO",
                    "catapulta": "CATAPULTA DE CERCO"
                    }.get(carta["tipo"], carta["tipo"].upper())
        tp = self.fM.render(tipo_lbl, True, cor_niv)
        tela.blit(tp, (cx + cw // 2 - tp.get_width() // 2, cy + 130))
        nr = self.fMi.render(f'"{self.narrativa[:64]}"', True, (150, 170, 210))
        tela.blit(nr, (cx + cw // 2 - nr.get_width() // 2, cy + 168))
        ins = self.fP.render("[ ESPAÇO ] → Resolver", True, C_DIM)
        tela.blit(ins, (cx + cw // 2 - ins.get_width() // 2, cy + 235))
