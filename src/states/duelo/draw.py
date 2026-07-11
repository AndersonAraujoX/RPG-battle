"""
duelo_draw.py — Camada de Renderização do Duelo de Castas (Humano vs. N Bots)
"""
from __future__ import annotations
import pygame

from .data import (
    C_MESA, C_PAINEL, C_BORDA, C_TEXTO, C_DIM, C_OURO, C_VERDE, C_PERIGO, C_ACENTO,
    C_CARD_BG, C_CARD_HOVER, C_CARD_SELECT,
)
from src.config import LARGURA_TELA, ALTURA_TELA
from src.cerco_isectum import DADOS_INIMIGOS


class DueloStateDrawMixin:
    """Mixin contendo toda a lógica visual da tela de Duelo adaptável para N jogadores."""

    def draw(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        mouse = pygame.mouse.get_pos()

        # ── 1. LIMPA TELA COM VELUDO ESCURO ──────────────────────────────
        tela.fill(C_MESA)

        # Luzes decorativas nas bordas
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (85, 15, 65, 22), (W // 2, H // 2), 400)
        tela.blit(glow, (0, 0))

        # ── 2. PAINEL LATERAL (STATUS, PLACAR & LOGS) ───────────────────
        px = W - 310
        py = 10
        pw = 300
        ph = H - 20
        pygame.draw.rect(tela, C_PAINEL, (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(tela, C_BORDA, (px, py, pw, ph), 1, border_radius=8)

        # Título Duelo
        t_title = self.fG.render("DUELO DE CASTAS", True, C_OURO)
        tela.blit(t_title, (px + 15, py + 15))
        sub_t = self.fMi.render("Grimwood Swarm Engine", True, C_DIM)
        tela.blit(sub_t, (px + 15, py + 38))
        pygame.draw.line(tela, C_BORDA, (px + 10, py + 55), (px + pw - 10, py + 55), 1)

        # Placar de Pontos de Todos os Jogadores
        ly = py + 65
        lbl_p = self.fM.render("🏆 Placar (Feromônios):", True, C_ACENTO)
        tela.blit(lbl_p, (px + 15, ly))
        ly += 22

        for nome in self.jogadores:
            pts = self.pontos.get(nome, 0)
            is_ativo = (self.get_jogador_ativo() == nome)
            prefix = "▶ " if is_ativo else "  "
            cor = C_VERDE if nome == "VOCÊ" else (C_OURO if is_ativo else C_TEXTO)
            
            # Mostra também o tamanho da mão
            mao_tam = len(self.maos.get(nome, []))
            lbl_jog = self.fM.render(f"{prefix}{nome}: {pts} pts ({mao_tam} c.)", True, cor)
            tela.blit(lbl_jog, (px + 15, ly))
            ly += 20

        # Indicador de Ações
        ly += 12
        pygame.draw.line(tela, C_BORDA, (px + 10, ly), (px + pw - 10, ly), 1)
        ly += 12
        
        ativo = self.get_jogador_ativo()
        cor_t = C_VERDE if ativo == "VOCÊ" else C_PERIGO
        lbl_t = self.fG.render(f"● Turno: {ativo}", True, cor_t)
        lbl_a = self.fM.render(f"Ações restantes: {self.acoes_restantes}", True, C_TEXTO)
        tela.blit(lbl_t, (px + 15, ly))
        tela.blit(lbl_a, (px + 15, ly + 25))
        ly += 55
        pygame.draw.line(tela, C_BORDA, (px + 10, ly), (px + pw - 10, ly), 1)

        # Logs de Combate
        ly += 15
        log_t = self.fM.render("Log do Duelo:", True, C_ACENTO)
        tela.blit(log_t, (px + 15, ly))

        log_box = pygame.Rect(px + 10, ly + 22, pw - 20, H - ly - 80)
        pygame.draw.rect(tela, (12, 6, 20), log_box, border_radius=4)
        pygame.draw.rect(tela, C_BORDA, log_box, 1, border_radius=4)

        log_y = log_box.y + 8
        for autor, msg in self.log[-8:]:
            cor = C_OURO if autor == "VOCÊ" else (C_VERDE if autor == "SISTEMA" else C_PERIGO)
            txt = self.fMi.render(f"[{autor[:8]}] {msg[:28]}", True, cor)
            tela.blit(txt, (log_box.x + 8, log_y))
            log_y += 18

        # Botão de Voltar
        self.btn_voltar = pygame.Rect(px + 10, H - 42, pw - 20, 32)
        hover_v = self.btn_voltar.collidepoint(mouse)
        cor_v = (60, 20, 30) if hover_v else (35, 10, 20)
        pygame.draw.rect(tela, cor_v, self.btn_voltar, border_radius=6)
        pygame.draw.rect(tela, C_PERIGO, self.btn_voltar, 1, border_radius=6)
        texto_btn = "RETORNAR À FORTALEZA" if getattr(self, "modo_retorno_cerco", False) else "VOLTAR AO SETUP"
        txt_v = self.fM.render(texto_btn, True, C_TEXTO)
        tela.blit(txt_v, (self.btn_voltar.centerx - txt_v.get_width() // 2, self.btn_voltar.centery - txt_v.get_height() // 2))

        # ── 3. MESA DE CARTAS (ÁREA DE DUELO ADAPTÁVEL) ─────────────────
        mx_w = px - 20
        self.oponente_horda_rects = {}

        # Filtra apenas os oponentes (Filhos do Imperador)
        bots = [p for p in self.jogadores if p != "VOCÊ"]
        num_bots = len(bots)

        # Desenhar Hordas dos Adversários dinamicamente no topo (Y=15 a Y=220)
        if num_bots == 1:
            # 1 Bot: Ocupa o topo inteiro
            bot_name = bots[0]
            area = pygame.Rect(15, 15, mx_w, 140)
            self._draw_horda_adversario(tela, area, bot_name)
        elif num_bots == 2:
            # 2 Bots: Divididos lado a lado no topo
            aw = (mx_w - 15) // 2
            for idx, bot_name in enumerate(bots):
                ax = 15 + idx * (aw + 15)
                area = pygame.Rect(ax, 15, aw, 140)
                self._draw_horda_adversario(tela, area, bot_name, compact=True)
        else:
            # 3 ou 4 Bots: Grade de 2x2 no topo (Y=15 a Y=210)
            aw = (mx_w - 15) // 2
            ah = 90
            for idx, bot_name in enumerate(bots):
                col = idx % 2
                row = idx // 2
                ax = 15 + col * (aw + 15)
                ay = 15 + row * (ah + 10)
                area = pygame.Rect(ax, ay, aw, ah)
                self._draw_horda_adversario(tela, area, bot_name, compact=True, micro=True)

        # ── 4. MERCADO CENTRAL (NINHO - LINHA DO MEIO) ───────────────────
        # Centralizamos o Ninho entre Y=230 e Y=365
        ninho_y = 230 if num_bots <= 2 else 240
        ninho_area = pygame.Rect(15, ninho_y, mx_w, 140)
        pygame.draw.rect(tela, (20, 12, 34, 100), ninho_area, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, ninho_area, 1, border_radius=8)
        
        # Deck de Compra
        card_w, card_h = 70, 92
        self.deck_rect = pygame.Rect(ninho_area.x + 15, ninho_area.y + 24, card_w, card_h)
        pygame.draw.rect(tela, (40, 20, 60), self.deck_rect, border_radius=6)
        pygame.draw.rect(tela, C_ACENTO, self.deck_rect, 1, border_radius=6)
        lbl_deck_c1 = self.fMi.render("DECK", True, C_ACENTO)
        lbl_deck_c2 = self.fMi.render(str(len(self.deck)), True, C_TEXTO)
        tela.blit(lbl_deck_c1, (self.deck_rect.centerx - lbl_deck_c1.get_width() // 2, self.deck_rect.y + 25))
        tela.blit(lbl_deck_c2, (self.deck_rect.centerx - lbl_deck_c2.get_width() // 2, self.deck_rect.y + 45))

        # Ninho Aberto (3 Cartas)
        self.ninho_rects = []
        for i, cid in enumerate(self.ninho):
            bx = ninho_area.x + 110 + i * (card_w + 14)
            by = ninho_area.y + 24
            c_rect = pygame.Rect(bx, by, card_w, card_h)
            self.ninho_rects.append(c_rect)
            
            hov = c_rect.collidepoint(mouse)
            self._draw_carta_mesa(tela, c_rect, cid, hover=hov)

        # Pilha de Descarte
        self.descarte_rect = pygame.Rect(ninho_area.right - card_w - 15, ninho_area.y + 24, card_w, card_h)
        pygame.draw.rect(tela, (15, 10, 25), self.descarte_rect, border_radius=6)
        pygame.draw.rect(tela, C_BORDA, self.descarte_rect, 1, border_radius=6)
        lbl_desc_c1 = self.fMi.render("DESCARTE", True, C_DIM)
        lbl_desc_c2 = self.fMi.render(str(len(self.descarte)), True, C_DIM)
        tela.blit(lbl_desc_c1, (self.descarte_rect.centerx - lbl_desc_c1.get_width() // 2, self.descarte_rect.y + 25))
        tela.blit(lbl_desc_c2, (self.descarte_rect.centerx - lbl_desc_c2.get_width() // 2, self.descarte_rect.y + 45))

        # ── 5. SUA HORDA (MESA DO JOGADOR) ───────────────────────────────
        jogador_y = ninho_area.bottom + 12
        jogador_area = pygame.Rect(15, jogador_y, mx_w, 130)
        pygame.draw.rect(tela, (15, 25, 20, 100), jogador_area, border_radius=8)
        pygame.draw.rect(tela, C_VERDE, jogador_area, 1, border_radius=8)
        
        lbl_hj = self.fMi.render("SUA HORDA DE INSETOS", True, C_VERDE)
        tela.blit(lbl_hj, (jogador_area.x + 10, jogador_area.y + 6))

        self.horda_jogador_rects = []
        for i, cid in enumerate(self.hordas.get("VOCÊ", [])):
            bx = jogador_area.x + 15 + i * (card_w + 10)
            by = jogador_area.y + 24
            c_rect = pygame.Rect(bx, by, card_w, card_h)
            self.horda_jogador_rects.append(c_rect)
            self._draw_carta_mesa(tela, c_rect, cid)

        # ── 6. SUA MÃO DE CARTAS (RODAPÉ) ─────────────────────────────────
        self._draw_mao_jogador_deck(tela, mx_w, H, mouse)

        # ── 7. FEEDBACK E TOOLTIPS ───────────────────────────────────────
        if self.feedback_timer > 0:
            fb_surf = self.fM.render(self.msg_feedback, True, self.msg_cor)
            fx = mx_w // 2 - fb_surf.get_width() // 2
            fy = H - 200
            pygame.draw.rect(tela, (8, 4, 18, 200), (fx - 15, fy - 8, fb_surf.get_width() + 30, 32), border_radius=6)
            pygame.draw.rect(tela, C_BORDA, (fx - 15, fy - 8, fb_surf.get_width() + 30, 32), 1, border_radius=6)
            tela.blit(fb_surf, (fx, fy))

        self._draw_tooltip_hover(tela, W, H)

    def _draw_horda_adversario(self, tela, area, bot_name, compact=False, micro=False):
        """Renderiza a horda e cabeçalho de um bot adversário específico."""
        pygame.draw.rect(tela, (25, 10, 20, 100), area, border_radius=8)
        
        # Cor de destaque se for o turno dele
        is_turno = (self.get_jogador_ativo() == bot_name)
        cor_borda = C_ACENTO if is_turno else C_PERIGO
        pygame.draw.rect(tela, cor_borda, area, 1, border_radius=8)
        
        # Nome do Bot e Pontos
        prefix = "▶ " if is_turno else ""
        txt = f"{prefix}{bot_name} ({self.pontos.get(bot_name, 0)} pts)"
        lbl = self.fMi.render(txt, True, C_PERIGO)
        tela.blit(lbl, (area.x + 8, area.y + 5))

        # Desenha as cartas convocadas por esse bot
        horda = self.hordas.get(bot_name, [])
        card_w = 48 if micro else 60
        card_h = 64 if micro else 80
        gap = 6
        
        for i, cid in enumerate(horda):
            cx = area.x + 8 + i * (card_w + gap)
            cy = area.y + 20 if micro else area.y + 25
            c_rect = pygame.Rect(cx, cy, card_w, card_h)
            
            # Desenha mini carta compacta
            dados = DADOS_INIMIGOS.get(cid, {})
            pygame.draw.rect(tela, C_CARD_BG, c_rect, border_radius=4)
            pygame.draw.rect(tela, C_BORDA, c_rect, 1, border_radius=4)
            
            em = self.fM.render(dados.get("emoji", "🐛"), True, C_TEXTO)
            tela.blit(em, (c_rect.centerx - em.get_width() // 2, c_rect.y + (6 if micro else 12)))
            
            if not micro:
                nome_p = dados.get("nome", cid).split()[0]
                nm = self.fMi.render(nome_p[:7], True, C_TEXTO)
                tela.blit(nm, (c_rect.centerx - nm.get_width() // 2, c_rect.y + 44))

    def _draw_carta_mesa(self, tela, rect, cid, hover=False):
        """Desenha uma mini carta na mesa."""
        dados = DADOS_INIMIGOS.get(cid, {})
        emoji = dados.get("emoji", "🐛")
        nome = dados.get("nome", cid).split()[0]

        bg = C_CARD_HOVER if hover else C_CARD_BG
        border = C_ACENTO if hover else C_BORDA

        pygame.draw.rect(tela, bg, rect, border_radius=6)
        pygame.draw.rect(tela, border, rect, 1, border_radius=6)

        e_txt = self.fM.render(emoji, True, C_TEXTO)
        tela.blit(e_txt, (rect.centerx - e_txt.get_width() // 2, rect.y + 12))

        n_txt = self.fMi.render(nome[:8], True, C_TEXTO)
        tela.blit(n_txt, (rect.centerx - n_txt.get_width() // 2, rect.y + 44))

        c_txt = self.fMi.render(dados.get("classe", "")[:8], True, C_DIM)
        tela.blit(c_txt, (rect.centerx - c_txt.get_width() // 2, rect.y + 64))

    def _draw_mao_jogador_deck(self, tela, max_w, H, mouse):
        """Renderiza as cartas na mão do jogador ativo no rodapé."""
        card_w, card_h = 94, 120
        gap = 12
        ativo = self.get_jogador_ativo()
        if ativo != "VOCÊ" and getattr(self, "controle_filhos", "humano") == "ia":
            mao = []
        else:
            mao = self.maos.get(ativo, [])
        total_w = len(mao) * card_w + (len(mao) - 1) * gap
        start_x = (max_w - total_w) // 2
        start_y = H - 145

        self.mao_jogador_rects = []
        self.carta_hover_idx = -1

        for i, cid in enumerate(mao):
            cx = start_x + i * (card_w + gap)
            cy = start_y

            card_rect = pygame.Rect(cx, cy, card_w, card_h)
            is_hover = card_rect.collidepoint(mouse)

            if is_hover:
                cy -= 12
                card_rect.y = cy
                self.carta_hover_idx = i

            self.mao_jogador_rects.append(card_rect)

            sel = (i == self.carta_selecionada_idx)
            bg = C_CARD_HOVER if is_hover else C_CARD_BG
            border = C_CARD_SELECT if sel else (C_ACENTO if is_hover else C_BORDA)

            pygame.draw.rect(tela, bg, card_rect, border_radius=6)
            pygame.draw.rect(tela, border, card_rect, 2 if sel or is_hover else 1, border_radius=6)

            dados = DADOS_INIMIGOS.get(cid, {})
            
            em_t = self.fG.render(dados.get("emoji", "🐛"), True, C_TEXTO)
            tela.blit(em_t, (cx + 6, cy + 6))

            nome_c = dados.get("nome", cid).split()[0]
            nome_t = self.fM.render(nome_c, True, C_OURO if sel else C_TEXTO)
            tela.blit(nome_t, (cx + 30, cy + 10))

            tipo_t = self.fMi.render(dados.get("classe", ""), True, C_DIM)
            tela.blit(tipo_t, (cx + 6, cy + 30))

            # Descrição rápida
            efeito = dados.get("efeito", "")
            palavras = efeito.split()
            linhas = []
            l_atual = ""
            for p in palavras:
                if len(l_atual + " " + p) < 13:
                    l_atual += (" " if l_atual else "") + p
                else:
                    linhas.append(l_atual)
                    l_atual = p
            if l_atual:
                linhas.append(l_atual)

            ly = cy + 50
            for linha in linhas[:3]:
                tela.blit(self.fMi.render(linha, True, C_TEXTO if sel else C_DIM), (cx + 6, ly))
                ly += 14

    def _draw_tooltip_hover(self, tela, W, H):
        """Mostra uma descrição expandida no hover da carta da mão."""
        ativo = self.get_jogador_ativo()
        mao = self.maos.get(ativo, [])
        if self.carta_hover_idx < 0 or self.carta_hover_idx >= len(mao):
            return

        cid = mao[self.carta_hover_idx]
        dados = DADOS_INIMIGOS.get(cid, {})
        
        tw, th = 380, 110
        tx = 20
        ty = H - 260
        
        pygame.draw.rect(tela, (25, 14, 38), (tx, ty, tw, th), border_radius=6)
        pygame.draw.rect(tela, C_BORDA, (tx, ty, tw, th), 1, border_radius=6)

        t_title = self.fM.render(f"{dados.get('emoji','')} {dados.get('nome','')}", True, C_OURO)
        tela.blit(t_title, (tx + 12, ty + 10))
        t_sub = self.fMi.render(f"Classe: {dados.get('classe','')} (Efeito Imediato)", True, C_ACENTO)
        tela.blit(t_sub, (tx + 12, ty + 28))

        efeito = dados.get("efeito", "")
        palavras = efeito.split()
        linhas = []
        l_atual = ""
        for p in palavras:
            if len(l_atual + " " + p) < 45:
                l_atual += (" " if l_atual else "") + p
            else:
                linhas.append(l_atual)
                l_atual = p
        if l_atual:
            linhas.append(l_atual)

        ly = ty + 50
        for l in linhas[:3]:
            tela.blit(self.fMi.render(l, True, C_TEXTO), (tx + 12, ly))
            ly += 16
