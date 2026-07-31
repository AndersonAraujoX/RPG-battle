"""
draw_ui.py — Mixin de renderização da interface do usuário (cabeçalho, botões, modais, banners e menu dev) para CercoState.
"""
from __future__ import annotations
import math
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_TEXTO, C_DIM, C_CERCO,
    MODO_SUBORNAR,
)


class CercoDrawUIMixin:
    """Sub-mixin com renderização de fontes, layout, cabeçalho, botões, modais e banners."""

    def _setup_fonts(self):
        s = max(0.5, ALTURA_TELA / 720.0)
        self.fT  = pygame.font.Font(None, max(16, int(48 * s)))
        self.fG  = pygame.font.Font(None, max(14, int(36 * s)))
        self.fM  = pygame.font.Font(None, max(12, int(28 * s)))
        self.fP  = pygame.font.Font(None, max(10, int(22 * s)))
        self.fMi = pygame.font.Font(None, max(8,  int(18 * s)))

    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        self.mapa_rect   = pygame.Rect(8, 65, W - 330, H - 255)
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
        self.btn_merc_melee      = pygame.Rect(8,    H - 184, 160, 32)
        self.btn_merc_arqueiro   = pygame.Rect(174,   H - 184, 160, 32)
        self.btn_merc_minerador  = pygame.Rect(340,   H - 184, 175, 32)

    def _draw_botoes_acao(self, tela, W, H):
        """Renderiza os botões de modo de ação na barra inferior."""
        e = self.estado
        mouse = pygame.mouse.get_pos()

        def _btn(rect, label, ativo, cor_at, cor_hl, cor_off=None):
            if cor_off is None:
                cor_off = C_PAINEL
            cor = (cor_hl if rect.collidepoint(mouse) else cor_at) if ativo else cor_off
            pygame.draw.rect(tela, cor, rect, border_radius=7)
            pygame.draw.rect(tela, C_BORDA, rect, 1, border_radius=7)
            t = self.fMi.render(label, True, C_TEXTO if ativo else C_DIM)
            tela.blit(t, (rect.centerx - t.get_width() // 2,
                          rect.centery - t.get_height() // 2))

        # Fase de ameaça — só mostra botão de resolver
        if self.fase == "FASE_AMEACA":
            if self.carta_cerco:
                _btn(self.btn_confirmar, "▶ Resolver Ameaça  [ESPAÇO]",
                     True, (40, 20, 80), (70, 40, 130))
            return

        # Botão de fim de turno
        _btn(self.btn_fim_turno, "Encerrar Turno  [Ent]",
             True, (60, 20, 20), (90, 30, 30))

        # Botões de modo de ação na barra inferior (definidos em _setup_layout)
        tem_mov = e.get("pontos_movimento", 0) > 0
        tem_trab = e.get("pontos_trabalho", 0) > 0
        tem_esc = e.get("pontos_escavacao", 0) > 0

        from .data import MODO_MOVER, MODO_TRABALHAR, MODO_ESCAVAR, MODO_SUBORNAR, MODO_CONVOCAR, MODO_ATACAR, MODO_ATIRAR

        modo = self.modo_acao

        _btn(self.btn_mover,     "Mover [M]",     tem_mov,
             (20, 50, 20) if modo == MODO_MOVER else (14, 28, 14),
             (30, 80, 30))
        _btn(self.btn_trabalhar, "Trabalhar [T]", tem_trab,
             (50, 40, 10) if modo == MODO_TRABALHAR else (28, 22, 8),
             (80, 65, 20))
        _btn(self.btn_escavar,   "Escavar [E]",   tem_esc,
             (40, 25, 10) if modo == MODO_ESCAVAR else (24, 14, 6),
             (65, 45, 18))
        _btn(self.btn_subornar,  "Subornar [S]",  True,
             (35, 15, 55) if modo == MODO_SUBORNAR else (20, 10, 30),
             (60, 30, 90))
        _btn(self.btn_atacar,    "Atacar [A]",    True,
             (55, 12, 12) if modo == MODO_ATACAR else (30, 8, 8),
             (85, 20, 20))
        _btn(self.btn_atirar,    "Atirar [F]",    True,
             (12, 30, 60) if modo == MODO_ATIRAR else (8, 16, 34),
             (20, 50, 90))

        # Suborno de recurso (mostra mini-botões enquanto no modo SUBORNAR)
        if modo == MODO_SUBORNAR:
            dep = e.get("recursos_depositados", {})
            bx = self.btn_subornar.right + 8
            for res, nome in [("madeira", "Mad"), ("couro", "Cou"), ("metal", "Met")]:
                br = pygame.Rect(bx, H - 48, 50, 36)
                ativo = dep.get(res, 0) > 0
                _btn(br, f"{nome}:{dep.get(res,0)}", ativo,
                     (30, 40, 30), (50, 70, 50))
                if br.collidepoint(mouse) and ativo:
                    if pygame.mouse.get_pressed()[0]:
                        self._subornar_recurso(res)
                bx += 56
            br_rocha = pygame.Rect(bx, H - 48, 140, 36)
            ativo_rocha = e.get("pontos_escavacao", 0) >= 4
            _btn(br_rocha, "Limpar Rocha(4PE)", ativo_rocha,
                 (30, 40, 50), (50, 70, 90))
            if br_rocha.collidepoint(mouse) and ativo_rocha:
                if pygame.mouse.get_pressed()[0]:
                    self._limpar_rocha_goblin()

        # Botões de recrutamento de mercenários (Cristais Roxos)
        cristais = e.get("tesouro", 0)
        _btn(self.btn_merc_melee,      f"Guarda Melee (5💎)",  cristais >= 5,
             (50, 20, 70), (90, 40, 130), (25, 12, 35))
        _btn(self.btn_merc_arqueiro,   f"Arqueiro (7💎)",       cristais >= 7,
             (50, 20, 70), (90, 40, 130), (25, 12, 35))
        _btn(self.btn_merc_minerador,  f"Minerador (4💎)",      cristais >= 4,
             (50, 20, 70), (90, 40, 130), (25, 12, 35))

        # Botão de voltar (topo-direito)
        voltar_hover = self.btn_voltar.collidepoint(mouse)
        pygame.draw.rect(tela, (30, 15, 15) if voltar_hover else (16, 10, 10),
                         self.btn_voltar, border_radius=5)
        pygame.draw.rect(tela, C_BORDA, self.btn_voltar, 1, border_radius=5)
        lbl_v = self.fMi.render("← Menu  [ESC]", True, C_TEXTO)
        tela.blit(lbl_v, (self.btn_voltar.centerx - lbl_v.get_width() // 2,
                          self.btn_voltar.centery - lbl_v.get_height() // 2))

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

    def _draw_feedback(self, tela, W, H):
        alpha = min(255, self.feedback_timer * 4)
        surf  = pygame.Surface((W, 32), pygame.SRCALPHA)
        surf.fill((*self.msg_cor, 30))
        tela.blit(surf, (0, H // 2 - 16))
        ft = self.fP.render(self.msg_feedback[:80], True, self.msg_cor)
        tela.blit(ft, (W // 2 - ft.get_width() // 2, H // 2 - 10))

    def _draw_ia_turno_banner(self, tela, W, H):
        timer = 0
        if getattr(self, 'ia_comandante', None) is not None:
            timer = getattr(self.ia_comandante, 'banner_timer', 0)
        if timer <= 0:
            return

        TOTAL = 180
        if timer > TOTAL:
            timer = TOTAL

        if timer > TOTAL - 20:
            alpha = int(255 * (TOTAL - timer) / 20)
        elif timer < 30:
            alpha = int(255 * timer / 30)
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(alpha * 0.55)))
        tela.blit(overlay, (0, 0))

        bw, bh = min(W - 80, 660), 180
        bx = W // 2 - bw // 2
        by = H // 2 - bh // 2

        pulso = (math.sin(self.timer * 0.2) + 1.0) / 2.0
        cor_roxo = (int(90 + 50 * pulso), int(20 + 20 * pulso), int(160 + 60 * pulso))
        cor_titulo = (int(200 + 40 * pulso), int(130 + 60 * pulso), 255)

        caixa = pygame.Surface((bw, bh), pygame.SRCALPHA)
        caixa.fill((10, 5, 30, int(alpha * 0.92)))
        tela.blit(caixa, (bx, by))
        
        pygame.draw.rect(tela, cor_roxo,
                         pygame.Rect(bx, by, bw, bh), 3, border_radius=12)
        pygame.draw.rect(tela, cor_titulo,
                         pygame.Rect(bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=10)

        pygame.draw.line(tela, cor_titulo,
                         (bx + 20, by + 24), (bx + bw - 20, by + 24), 1)

        cx_icon = bx + 50
        cy_icon = by + bh // 2
        coroa_pts = [
            (cx_icon - 20, cy_icon + 10),
            (cx_icon - 20, cy_icon - 12),
            (cx_icon - 10, cy_icon - 4),
            (cx_icon,      cy_icon - 18),
            (cx_icon + 10, cy_icon - 4),
            (cx_icon + 20, cy_icon - 12),
            (cx_icon + 20, cy_icon + 10),
        ]
        pygame.draw.polygon(tela, cor_titulo, coroa_pts)
        pygame.draw.polygon(tela, cor_roxo, coroa_pts, 2)

        t_titulo = self.fT.render("PRÍNCIPE LYSANDER", True, cor_titulo)
        t_titulo.set_alpha(alpha)
        tela.blit(t_titulo, (bx + bw // 2 - t_titulo.get_width() // 2, by + 22))

        t_sub = self.fM.render("Filho do Imperador — Invasão Imperial", True, (240, 150, 150))
        t_sub.set_alpha(alpha)
        tela.blit(t_sub, (bx + bw // 2 - t_sub.get_width() // 2, by + 75))

        t_desc = self.fP.render("O Príncipe envia ondas de castas de insetos para derrubar a fortaleza.", True, (190, 150, 150))
        t_desc.set_alpha(alpha)
        tela.blit(t_desc, (bx + bw // 2 - t_desc.get_width() // 2, by + 112))

        pygame.draw.line(tela, cor_titulo,
                         (bx + 20, by + bh - 24), (bx + bw - 20, by + bh - 24), 1)

        t_inst = self.fMi.render("Aguarde — O inimigo está planejando o ataque...", True, (150, 100, 100))
        t_inst.set_alpha(alpha)
        tela.blit(t_inst, (bx + bw // 2 - t_inst.get_width() // 2, by + bh - 16))

    def _draw_fim(self, tela, W, H):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        tela.blit(ov, (0, 0))
        e = self.estado
        vit = e.get("vitoria")
        cor = C_VERDE if vit else C_PERIGO
        t1  = self.fT.render("VITÓRIA!" if vit else "DERROTA!", True, cor)
        tela.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 90))
        msg = (e.get("msg_vitoria") or "Os defensores resistiram!") if vit \
            else (e.get("msg_derrota") or "A fortaleza caiu.")
        t2 = self.fM.render(msg[:64], True, C_TEXTO)
        tela.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 20))
        t3 = self.fP.render(
            f"Rodada {e['rodada']}  |  Cristais: {e['tesouro']}  |  "
            f"Cartas no cerco: {len(self.deck)}", True, C_DIM
        )
        tela.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 24))
        t4 = self.fP.render("Clique para voltar ao menu", True, C_DIM)
        tela.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 + 60))

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
            txt = info['nome']
            txt_surf = self.fP.render(txt, True, C_TEXTO)
            if txt_surf.get_width() > cw - 12:
                txt_surf = self.fMi.render(txt, True, C_TEXTO)
            tela.blit(txt_surf, (r.x + 8, r.centery - txt_surf.get_height() // 2))
