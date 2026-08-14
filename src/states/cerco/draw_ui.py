"""
draw_ui.py — Mixin de renderização da interface do usuário (cabeçalho, botões, modais, banners e menu dev) para CercoState.
"""
from __future__ import annotations
import math
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from ...utils import sanitizar_texto_fonte, remover_emojis
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
        # AutoPlay — fica no topo direito, ao lado do botão voltar (W - 156)
        self.btn_autoplay        = pygame.Rect(W - 310, 68, 146, 30)
        # Mini-botões de velocidade (ficam no header acima do autoplay)
        vbw = 45
        self.btn_vel_lento   = pygame.Rect(W - 310, 22, vbw, 24)
        self.btn_vel_normal  = pygame.Rect(W - 260, 22, vbw, 24)
        self.btn_vel_rapido  = pygame.Rect(W - 210, 22, vbw, 24)

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

        # ── Botão AutoPlay — desenhado SEMPRE (antes de qualquer return) ────────
        import math as _math
        autoplay_ativo = getattr(self, 'autoplay_ativo', False)
        ap_hover = getattr(self, 'btn_autoplay', None) and self.btn_autoplay.collidepoint(mouse)

        if autoplay_ativo:
            pulso = ((_math.sin(self.timer * 0.15) + 1.0) / 2.0)
            r_ap = int(20 + 40 * pulso)
            g_ap = int(160 + 60 * pulso)
            b_ap = int(30 + 20 * pulso)
            cor_ap  = (r_ap, g_ap, b_ap)
            borda_ap = (60, 255, 80)
            lbl_ap   = "▶ ATIVO  [F5]"
        else:
            cor_ap   = (30, 50, 28) if ap_hover else (16, 28, 14)
            borda_ap = (60, 130, 50)
            lbl_ap   = "AutoPlay  [F5]"

        if getattr(self, 'btn_autoplay', None):
            pygame.draw.rect(tela, cor_ap,  self.btn_autoplay, border_radius=7)
            pygame.draw.rect(tela, borda_ap, self.btn_autoplay,
                             2 if autoplay_ativo else 1, border_radius=7)
            lbl_ap_s = self.fMi.render(lbl_ap, True,
                                       (180, 255, 160) if autoplay_ativo else C_DIM)
            tela.blit(lbl_ap_s, (
                self.btn_autoplay.centerx - lbl_ap_s.get_width() // 2,
                self.btn_autoplay.centery - lbl_ap_s.get_height() // 2,
            ))

        # Mini-botões de velocidade (só quando AutoPlay ativo)
        if autoplay_ativo:
            vel_atual = getattr(self, 'autoplay_velocidade', 'normal')
            for btn_r, vid, label in [
                (getattr(self, 'btn_vel_lento',  None), 'lento',  "⏸Lento"),
                (getattr(self, 'btn_vel_normal', None), 'normal', "▶Normal"),
                (getattr(self, 'btn_vel_rapido', None), 'rapido', "⚡Rápido"),
            ]:
                if btn_r is None:
                    continue
                sel = (vel_atual == vid)
                pygame.draw.rect(tela, (30, 100, 30) if sel else (12, 30, 12), btn_r, border_radius=4)
                pygame.draw.rect(tela, (80, 220, 80) if sel else (40, 80, 40), btn_r, 1, border_radius=4)
                lv = self.fMi.render(label, True, (160, 255, 140) if sel else (100, 160, 100))
                tela.blit(lv, (btn_r.centerx - lv.get_width() // 2,
                               btn_r.centery  - lv.get_height() // 2))

        # Fase de ameaça — só mostra botão de resolver
        if self.fase == "FASE_AMEACA":
            if self.carta_cerco:
                _btn(self.btn_confirmar, "▶ Resolver Ameaça  [ESPAÇO]",
                     True, (40, 20, 80), (70, 40, 130))
            # Botão voltar também na fase de ameaça
            voltar_hover = self.btn_voltar.collidepoint(mouse)
            pygame.draw.rect(tela, (30, 15, 15) if voltar_hover else (16, 10, 10),
                             self.btn_voltar, border_radius=5)
            pygame.draw.rect(tela, C_BORDA, self.btn_voltar, 1, border_radius=5)
            lbl_v = self.fMi.render("← Menu  [ESC]", True, C_TEXTO)
            tela.blit(lbl_v, (self.btn_voltar.centerx - lbl_v.get_width() // 2,
                              self.btn_voltar.centery - lbl_v.get_height() // 2))
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
        from ...utils import sanitizar_texto_fonte
        _btn(self.btn_merc_melee,      sanitizar_texto_fonte("Guarda Melee (5💎)"),  cristais >= 5,
             (50, 20, 70), (90, 40, 130), (25, 12, 35))
        _btn(self.btn_merc_arqueiro,   sanitizar_texto_fonte("Arqueiro (7💎)"),       cristais >= 7,
             (50, 20, 70), (90, 40, 130), (25, 12, 35))
        _btn(self.btn_merc_minerador,  sanitizar_texto_fonte("Minerador (4💎)"),      cristais >= 4,
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
                fallback = self.fMi.render("?", True, C_TEXTO)
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

        # Exibe os atributos de Vida (HP), Ataque (ATK) e Defesa (DEF) do herói ativo
        if hasattr(self, 'heroi_atual') and self.heroi_atual:
            ha = self.heroi_atual
            hp_cur = getattr(ha, 'hp_atual', 50)
            hp_max = max(1, getattr(ha, 'hp_max', 50))
            atk = getattr(ha, 'bonus_ataque', 5)
            dado_d = getattr(ha, 'dado_dano', (1, 8))
            d_str = f"{dado_d[0]}d{dado_d[1]}" if isinstance(dado_d, (tuple, list)) else str(dado_d)
            ac_val = getattr(ha, 'ac', getattr(ha, 'ac_base', 14))

            h_stats_txt = sanitizar_texto_fonte(f"❤️ {hp_cur}/{hp_max}  ⚔️ +{atk}({d_str})  🛡️ {ac_val}")
            lbl_stats = self.fMi.render(h_stats_txt, True, (240, 230, 160))

            px_st = bx + bw + 14
            py_st = by + 6
            tela.blit(lbl_stats, (px_st, py_st))

    def _draw_feedback(self, tela, W, H):
        alpha = min(255, self.feedback_timer * 4)
        surf  = pygame.Surface((W, 32), pygame.SRCALPHA)
        surf.fill((*self.msg_cor, 30))
        tela.blit(surf, (0, H // 2 - 16))
        ft = self.fP.render(self.msg_feedback[:80], True, self.msg_cor)
        tela.blit(ft, (W // 2 - ft.get_width() // 2, H // 2 - 10))

    def _draw_ia_turno_banner(self, tela, W, H):
        if self.fase == "REPOVOAR_MERCADO":
            from ...utils import sanitizar_texto_fonte
            bw, bh = 560, 68
            bx = (W - bw) // 2
            by = 95
            b_rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(tela, (24, 20, 12), b_rect, border_radius=10)
            pygame.draw.rect(tela, C_OURO, b_rect, 2, border_radius=10)
            t_m = self.fG.render(sanitizar_texto_fonte("🛒 FASE DE MERCADO & REPOSIÇÃO DE RECURSOS"), True, C_OURO)
            sub_m = self.fMi.render(sanitizar_texto_fonte("Compre upgrades nas oficinas e aloque mineradores [ENTER para continuar]"), True, C_TEXTO)
            tela.blit(t_m, (W // 2 - t_m.get_width() // 2, by + 12))
            tela.blit(sub_m, (W // 2 - sub_m.get_width() // 2, by + 42))

        # ⚡ Painel de Planejamento Simultâneo Co-op
        if getattr(self, "modo_sincronia", False) and not getattr(self, "em_resolucao_simultanea", False):
            from ...utils import sanitizar_texto_fonte
            if hasattr(self, "timer_planejamento_simultaneo"):
                self.timer_planejamento_simultaneo -= 1
                if self.timer_planejamento_simultaneo <= 0:
                    if hasattr(self, "executar_fase_resolucao_simultanea"):
                        self.executar_fase_resolucao_simultanea()

            secs_left = max(0, int(getattr(self, "timer_planejamento_simultaneo", 1200) / 60.0))
            bw, bh = 600, 50
            bx = (W - bw) // 2
            by = 68
            b_rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(tela, (14, 20, 36), b_rect, border_radius=8)
            pygame.draw.rect(tela, (80, 180, 255), b_rect, 2, border_radius=8)

            ordens_qtd = len(getattr(self, "fila_ordens_simultaneas", []))
            lbl_tit = self.fMi.render(sanitizar_texto_fonte(f"⚡ PLANEJAMENTO SIMULTÂNEO CO-OP ({secs_left}s)  |  Ordens: {ordens_qtd}"), True, (100, 220, 255))
            lbl_dica = self.fP.render(sanitizar_texto_fonte("Agende suas cartas e movimentos  [Pressione ESPAÇO para Executar Tática]"), True, (220, 235, 255))
            tela.blit(lbl_tit, (W // 2 - lbl_tit.get_width() // 2, by + 6))
            tela.blit(lbl_dica, (W // 2 - lbl_dica.get_width() // 2, by + 26))

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
        """Tela de DERROTA ou VITÓRIA — cinematic, imersiva e impactante."""
        import time
        e   = self.estado
        vit = e.get("vitoria", False)
        t   = time.time()

        # ── Fundo escuro total ───────────────────────────────────────────────
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 230))
        tela.blit(ov, (0, 0))

        # ── Cores temáticas ─────────────────────────────────────────────────
        if vit:
            cor_titulo  = (255, 215, 40)          # ouro
            cor_brilho  = (255, 240, 100)
            cor_borda   = (200, 160, 20)
            cor_faixa   = (40, 80, 20, 200)
            cor_glow    = (255, 230, 60, 30)
            cor_barra   = (80, 200, 80)
            titulo_txt  = "VITÓRIA!"
            emoji_txt   = "🏆"
        else:
            cor_titulo  = (220, 40, 40)            # vermelho sangue
            cor_brilho  = (255, 80, 60)
            cor_borda   = (160, 20, 20)
            cor_faixa   = (80, 10, 10, 200)
            cor_glow    = (200, 20, 20, 30)
            cor_barra   = (200, 50, 50)
            titulo_txt  = "DERROTA"
            emoji_txt   = "💀"

        # ── Scanlines animadas (horizontal stripes) ─────────────────────────
        stripe_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        phase = int(t * 30) % 8
        for y in range(phase, H, 8):
            pygame.draw.line(stripe_surf, (0, 0, 0, 28), (0, y), (W, y))
        tela.blit(stripe_surf, (0, 0))

        # ── Faixa central colorida (glowing box) ────────────────────────────
        box_h = 340
        box_w = min(700, W - 80)
        box_x = W // 2 - box_w // 2
        box_y = H // 2 - box_h // 2

        # Sombra difusa (glow externo)
        glow_r = int(14 + 6 * math.sin(t * 2.5))
        for gi in range(glow_r, 0, -2):
            alpha = max(0, int(cor_glow[3] * (gi / glow_r)))
            glow_col = cor_glow[:3] + (alpha,)
            gs = pygame.Surface((box_w + gi * 4, box_h + gi * 4), pygame.SRCALPHA)
            pygame.draw.rect(gs, glow_col, (0, 0, gs.get_width(), gs.get_height()), border_radius=18)
            tela.blit(gs, (box_x - gi * 2, box_y - gi * 2))

        # Fundo da caixa
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill(cor_faixa)
        tela.blit(box_surf, (box_x, box_y))

        # Borda animada (pulsando)
        pulse = 2 + int(1.5 * abs(math.sin(t * 3.0)))
        pygame.draw.rect(tela, cor_borda, (box_x, box_y, box_w, box_h), pulse, border_radius=14)

        # Linha decorativa topo e base
        pygame.draw.line(tela, cor_titulo, (box_x + 24, box_y + 3),      (box_x + box_w - 24, box_y + 3), 2)
        pygame.draw.line(tela, cor_titulo, (box_x + 24, box_y + box_h - 3), (box_x + box_w - 24, box_y + box_h - 3), 2)

        # ── Título principal ─────────────────────────────────────────────────
        scale_t = 1.0 + 0.03 * math.sin(t * 2.0)
        fT_big  = pygame.font.Font(None, max(20, int(80 * (ALTURA_TELA / 720.0) * scale_t)))
        t1      = fT_big.render(titulo_txt, True, cor_brilho)
        # Sombra do título
        t1_sombra = fT_big.render(titulo_txt, True, (0, 0, 0))
        tela.blit(t1_sombra, (W // 2 - t1.get_width() // 2 + 3, box_y + 30 + 3))
        tela.blit(t1, (W // 2 - t1.get_width() // 2, box_y + 30))

        # ── Mensagem de detalhe ───────────────────────────────────────────────
        msg = (e.get("msg_vitoria") or "Os defensores resistiram! A fortaleza se manteve!") if vit \
            else (e.get("msg_derrota") or "A fortaleza caiu para os invasores Insectum!")
        # Quebra em linhas de ~55 chars
        palavras = msg.split()
        linhas_msg = []
        linha_atual = ""
        for p in palavras:
            if len(linha_atual) + len(p) + 1 <= 55:
                linha_atual += (" " if linha_atual else "") + p
            else:
                linhas_msg.append(linha_atual)
                linha_atual = p
        if linha_atual:
            linhas_msg.append(linha_atual)

        fM2 = pygame.font.Font(None, max(12, int(26 * (ALTURA_TELA / 720.0))))
        y_msg = box_y + 120
        for ln in linhas_msg[:3]:
            surf_ln = fM2.render(ln, True, (220, 210, 200))
            tela.blit(surf_ln, (W // 2 - surf_ln.get_width() // 2, y_msg))
            y_msg += 26

        # ── Separador ───────────────────────────────────────────────────────
        sep_y = box_y + 190
        pygame.draw.line(tela, cor_borda, (box_x + 40, sep_y), (box_x + box_w - 40, sep_y), 1)

        # ── Estatísticas da partida ──────────────────────────────────────────
        stats = [
            ("⚔ Rodada",          str(e.get("rodada", "?"))),
            ("💎 Cristais",        str(e.get("tesouro", 0))),
            ("🪙 Reserva",         str(e.get("reserva", 0))),
            ("🐛 Invasores",       str(sum(e.get("invasores", {}).values()))),
            ("📦 Upgrades",        str(len(e.get("cartas_upgrade_ativas", [])))),
        ]
        fP2 = pygame.font.Font(None, max(10, int(20 * (ALTURA_TELA / 720.0))))
        stat_w = (box_w - 80) // len(stats)
        stat_y = sep_y + 12
        for i, (label, valor) in enumerate(stats):
            sx = box_x + 40 + i * stat_w + stat_w // 2
            # Mini barra de fundo
            sb = pygame.Surface((stat_w - 6, 46), pygame.SRCALPHA)
            sb.fill((20, 20, 30, 160))
            tela.blit(sb, (sx - (stat_w - 6) // 2, stat_y))
            pygame.draw.rect(tela, cor_borda, (sx - (stat_w - 6) // 2, stat_y, stat_w - 6, 46), 1, border_radius=4)
            lbl_s = fP2.render(label, True, (160, 150, 140))
            val_s = fP2.render(valor, True, (240, 230, 200))
            tela.blit(lbl_s, (sx - lbl_s.get_width() // 2, stat_y + 5))
            tela.blit(val_s, (sx - val_s.get_width() // 2, stat_y + 24))

        # ── Botão "Voltar ao Menu" ───────────────────────────────────────────
        btn_w2, btn_h2 = 260, 44
        btn_x = W // 2 - btn_w2 // 2
        btn_y = box_y + box_h - 68
        mx, my = pygame.mouse.get_pos()
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w2, btn_h2)
        hover = btn_rect.collidepoint(mx, my)
        btn_cor = (80, 20, 20) if not vit else (20, 70, 20)
        btn_cor_h = (130, 30, 30) if not vit else (30, 110, 30)
        pygame.draw.rect(tela, btn_cor_h if hover else btn_cor, btn_rect, border_radius=8)
        pygame.draw.rect(tela, cor_brilho, btn_rect, 2, border_radius=8)
        fB = pygame.font.Font(None, max(12, int(24 * (ALTURA_TELA / 720.0))))
        lbl_btn = fB.render("🏠  Voltar ao Menu Principal", True, (240, 230, 200))
        tela.blit(lbl_btn, (btn_rect.centerx - lbl_btn.get_width() // 2, btn_rect.centery - lbl_btn.get_height() // 2))
        self._btn_fim_rect = btn_rect

        # Dica tecla
        fHint = pygame.font.Font(None, max(8, int(16 * (ALTURA_TELA / 720.0))))
        hint = fHint.render("Pressione  ENTER  ou  ESC  para voltar", True, (90, 80, 70))
        tela.blit(hint, (W // 2 - hint.get_width() // 2, btn_y + btn_h2 + 8))


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

    def _draw_modal_draft_recompensa(self, tela, W, H):
        """Renderiza o modal de escolha de 1 entre 3 cartas bônus (Draft) após cada ameaça."""
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 8, 16, 210))
        tela.blit(overlay, (0, 0))

        mw, mh = 620, 240
        mx, my = (W - mw) // 2, (H - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)

        pygame.draw.rect(tela, (20, 24, 40), modal_rect, border_radius=12)
        pygame.draw.rect(tela, C_OURO, modal_rect, 2, border_radius=12)

        tit = self.fG.render(sanitizar_texto_fonte("🎁 ESCOLHA 1 CARTA BÔNUS PARA SEU DECK!"), True, C_OURO)
        tela.blit(tit, (modal_rect.centerx - tit.get_width() // 2, modal_rect.y + 16))

        sub = self.fMi.render(sanitizar_texto_fonte("Inimigos puxaram uma ameaça — fortaleça seu baralho com uma recompensa!"), True, C_TEXTO)
        tela.blit(sub, (modal_rect.centerx - sub.get_width() // 2, modal_rect.y + 45))

        opcoes = getattr(self, "draft_opcoes", [])
        if not opcoes:
            return

        cw, ch = 175, 140
        gap = 20
        total_w = len(opcoes) * cw + (len(opcoes) - 1) * gap
        start_x = modal_rect.centerx - total_w // 2
        cy = modal_rect.y + 75

        mouse = pygame.mouse.get_pos()

        for idx, carta in enumerate(opcoes):
            cx = start_x + idx * (cw + gap)
            crect = pygame.Rect(cx, cy, cw, ch)
            hover = crect.collidepoint(mouse)

            bg_col = (45, 50, 80) if hover else (28, 32, 52)
            borda_col = (255, 215, 0) if hover else C_BORDA

            pygame.draw.rect(tela, bg_col, crect, border_radius=8)
            pygame.draw.rect(tela, borda_col, crect, 2 if hover else 1, border_radius=8)

            sym = carta.get("simbolo", "[Carta]")
            lbl_sym = self.fG.render(sanitizar_texto_fonte(sym), True, C_OURO)
            tela.blit(lbl_sym, (crect.x + 10, crect.y + 10))

            nome = self.fMi.render(sanitizar_texto_fonte(carta["nome"][:16]), True, C_TEXTO)
            tela.blit(nome, (crect.x + 40, crect.y + 12))

            desc = carta.get("descricao", "")
            if desc:
                lbl_desc = self.fMi.render(sanitizar_texto_fonte(desc[:24]), True, C_DIM)
                tela.blit(lbl_desc, (crect.x + 10, crect.y + 48))

            click_lbl = self.fMi.render("Clique para escolher", True, C_VERDE if hover else C_BORDA)
            tela.blit(click_lbl, (crect.centerx - click_lbl.get_width() // 2, crect.bottom - 24))

    def _draw_barrinha_qte_parry(self, tela, W, H):
        """Renderiza a barra de timing QTE Parry & Dodge no estilo Clair Obscur / Expedition 33."""
        if not getattr(self, "qte_parry_ativo", False) or not getattr(self, "qte_dados", None):
            return

        qte = self.qte_dados
        qte["timer"] -= 1

        import math
        progresso = math.sin((pygame.time.get_ticks() / 320.0) * math.pi)
        norm_pos = (progresso + 1.0) / 2.0
        qte["ponteiro"] = norm_pos

        if qte["timer"] <= 0:
            if hasattr(self, "_resolver_qte_parry"):
                self._resolver_qte_parry("MISS")
            return

        bw, bh = 440, 36
        bx = (W - bw) // 2
        by = 110
        bar_rect = pygame.Rect(bx, by, bw, bh)

        pygame.draw.rect(tela, (14, 16, 28), bar_rect, border_radius=10)
        pygame.draw.rect(tela, (255, 215, 0), bar_rect, 2, border_radius=10)

        # Zona Azul de Dodge (30% a 70%)
        d_x = bx + int(bw * 0.30)
        d_w = int(bw * 0.40)
        dodge_rect = pygame.Rect(d_x, by + 4, d_w, bh - 8)
        pygame.draw.rect(tela, (30, 140, 220), dodge_rect, border_radius=6)

        # Zona Dourada de Perfect Parry (42% a 58%)
        p_x = bx + int(bw * 0.42)
        p_w = int(bw * 0.16)
        parry_rect = pygame.Rect(p_x, by + 4, p_w, bh - 8)
        pygame.draw.rect(tela, (255, 215, 0), parry_rect, border_radius=6)
        pygame.draw.rect(tela, (255, 255, 255), parry_rect, 2, border_radius=6)

        # Ponteiro Néon
        px = bx + int(bw * norm_pos)
        pygame.draw.line(tela, (255, 255, 255), (px, by - 4), (px, by + bh + 4), 5)
        pygame.draw.line(tela, (0, 255, 240), (px, by - 2), (px, by + bh + 2), 3)

        from ...utils import sanitizar_texto_fonte
        ini_nome = getattr(qte.get("ini"), "nome", "Inimigo")
        alvo_nome = getattr(qte.get("alvo"), "nome", "Herói")
        txt = self.fG.render(sanitizar_texto_fonte(f"⚔️ PARRY! {ini_nome} atacando {alvo_nome}! [ESPAÇO / CLIQUE]"), True, (255, 255, 255))
        tela.blit(txt, (W // 2 - txt.get_width() // 2, by - 32))

        sub = self.fMi.render(sanitizar_texto_fonte("🌟 Dourado: PERFECT PARRY & RIPOSTE  |  🛡️ Azul: DODGE (-75% Dano)"), True, (210, 230, 255))
        tela.blit(sub, (W // 2 - sub.get_width() // 2, by + bh + 8))
