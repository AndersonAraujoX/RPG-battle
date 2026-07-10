"""
castas_setup_state.py — Tela de Configuração do Modo Castas dos Isectum

Refatorado: constantes → castas_setup_state_data.py
"""
from __future__ import annotations
import pygame
import json

from ..state_base import GameState
from ...config import (
    ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA,
    RESOLUCOES, atualizar_resolucao,
)
from .data import (
    ESTADO_JOGO_CASTAS, ESTADO_JOGO_CASTAS_SETUP,
    C_BG, C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_TEXTO, C_DIM,
    C_VERDE, C_PERIGO, C_INSETO,
    DIFICULDADES_CASTAS, HEROIS_DISPONIVEIS,
)


class CastasSetupState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self._setup_fonts()
        self._setup_layout()
        self.selecionados = {nome: False for nome, _, _ in HEROIS_DISPONIVEIS}
        self.selecionados["Stark"] = True
        self.dificuldade_idx = 1
        self.resolucao_idx = 0
        for i, (rw, rh) in enumerate(RESOLUCOES):
            if rw == LARGURA_TELA and rh == ALTURA_TELA:
                self.resolucao_idx = i
                break

    def _setup_fonts(self):
        self.fT  = pygame.font.Font(None, 52)
        self.fG  = pygame.font.Font(None, 36)
        self.fM  = pygame.font.Font(None, 28)
        self.fP  = pygame.font.Font(None, 22)
        self.fMi = pygame.font.Font(None, 18)

    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        qtd_herois = len(HEROIS_DISPONIVEIS)
        linhas_herois = max(1, (qtd_herois + 4) // 5)
        altura_herois = 55 + linhas_herois * 105
        y_dif = 95 + altura_herois + 10
        self.area_herois      = pygame.Rect(40, 90, W - 80, altura_herois)
        self.area_dificuldade = pygame.Rect(40, y_dif, W - 80, 140)
        self.area_resolucao   = pygame.Rect(40, y_dif + 155, W - 80, 80)
        self.btn_iniciar      = pygame.Rect(W // 2 - 140, H - 58, 280, 44)
        self.btn_voltar       = pygame.Rect(20, 18, 100, 34)
        self.heroi_rects = []
        self.diff_rects  = []
        dx = self.area_dificuldade.x + 20
        dy = self.area_dificuldade.y + 55
        for i in range(len(DIFICULDADES_CASTAS)):
            self.diff_rects.append(pygame.Rect(dx + i * 220, dy, 200, 55))
        self.res_rects = []
        rx = self.area_resolucao.x + 20
        ry = self.area_resolucao.y + 32
        for i in range(len(RESOLUCOES)):
            self.res_rects.append(pygame.Rect(rx + i * 105, ry, 95, 32))

    def get_config(self):
        herois_escolhidos = []
        for nome, cls, _ in HEROIS_DISPONIVEIS:
            if self.selecionados.get(nome, False):
                herois_escolhidos.append((nome, cls))
        diff = DIFICULDADES_CASTAS[self.dificuldade_idx]
        return {"herois": herois_escolhidos, "dificuldade": diff}

    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.castas_setup_state = None
                self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_voltar.collidepoint(mouse):
                    self.game.castas_setup_state = None
                    self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    return
                if self.btn_iniciar.collidepoint(mouse):
                    qtd = sum(1 for v in self.selecionados.values() if v)
                    if qtd == 0:
                        return
                    config = self.get_config()
                    from ..castas import CastasState
                    self.game.castas_state = CastasState(self.game, config)
                    self.game.castas_setup_state = None
                    self.game.estado_jogo = ESTADO_JOGO_CASTAS
                    return
                for i, rect in enumerate(self.heroi_rects):
                    if rect and rect.collidepoint(mouse):
                        nome = HEROIS_DISPONIVEIS[i][0]
                        self.selecionados[nome] = not self.selecionados[nome]
                        return
                for i, rect in enumerate(self.diff_rects):
                    if rect and rect.collidepoint(mouse):
                        self.dificuldade_idx = i
                        return
                for i, rect in enumerate(self.res_rects):
                    if rect and rect.collidepoint(mouse):
                        self.resolucao_idx = i
                        w, h = RESOLUCOES[i]
                        atualizar_resolucao(w, h)
                        self.game.tela = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        with open("settings.json", "w") as f:
                            json.dump({"width": w, "height": h}, f)
                        self._setup_layout()
                        return

    def update(self):
        pass

    def draw(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)
        for ix in range(0, W, 60):
            for iy in range(0, H, 60):
                pygame.draw.circle(tela, (20, 10, 35), (ix, iy), 2)
        self._draw_titulo(tela, W)
        self._draw_herois(tela, W)
        self._draw_dificuldade(tela)
        self._draw_resolucao(tela)
        self._draw_botoes(tela, W, H)
        self._draw_instrucoes(tela, W, H)

    def _draw_titulo(self, tela, W):
        bar = pygame.Surface((W, 80), pygame.SRCALPHA)
        bar.fill((8, 4, 20, 230))
        tela.blit(bar, (0, 0))
        pygame.draw.line(tela, C_BORDA, (0, 80), (W, 80), 2)

        emoji_surf = self.fT.render("🐛", True, C_INSETO)
        tela.blit(emoji_surf, (W // 2 - 200, 18))
        t1 = self.fG.render("CASTAS DOS", True, C_ACENTO)
        t2 = self.fG.render("ISECTUM", True, C_OURO)
        cx = W // 2 - (t1.get_width() + t2.get_width() + 12) // 2
        tela.blit(t1, (cx, 22))
        tela.blit(t2, (cx + t1.get_width() + 12, 22))
        sub = self.fMi.render("Modo Assimétrico 2 Jogadores — Heróis vs. Diretor Isectum", True, C_DIM)
        tela.blit(sub, (W // 2 - sub.get_width() // 2, 52))

        mouse = pygame.mouse.get_pos()
        hover = self.btn_voltar.collidepoint(mouse)
        bc = (48, 24, 72) if hover else (22, 12, 38)
        pygame.draw.rect(tela, bc, self.btn_voltar, border_radius=6)
        pygame.draw.rect(tela, C_BORDA, self.btn_voltar, 1, border_radius=6)
        vt = self.fMi.render("< MENU", True, C_TEXTO if hover else C_DIM)
        tela.blit(vt, (self.btn_voltar.centerx - vt.get_width() // 2,
                       self.btn_voltar.centery - vt.get_height() // 2))

    def _draw_herois(self, tela, W):
        r = self.area_herois
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)
        tt = self.fM.render("ESCOLHA OS DEFENSORES", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 14))

        mouse = pygame.mouse.get_pos()
        self.heroi_rects = []
        cols = 4 if len(HEROIS_DISPONIVEIS) <= 4 else 5
        cw = (r.width - 60) // cols
        ch = 95

        for i, (nome, _, classe) in enumerate(HEROIS_DISPONIVEIS):
            col = i % cols
            row = i // cols
            hx = r.x + 20 + col * (cw + 10)
            hy = r.y + 52 + row * (ch + 8)
            rect = pygame.Rect(hx, hy, cw, ch)
            self.heroi_rects.append(rect)

            sel = self.selecionados.get(nome, False)
            hover = rect.collidepoint(mouse)
            cor_fundo = (28, 12, 50) if sel else ((18, 10, 30) if not hover else (24, 14, 42))
            cor_borda = C_ACENTO if sel else (C_BORDA if not hover else (100, 50, 150))

            pygame.draw.rect(tela, cor_fundo, rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, rect, 2 if sel else 1, border_radius=8)

            av_size = 60
            av_rect = pygame.Rect(hx + 10, hy + (ch - av_size) // 2, av_size, av_size)
            pygame.draw.rect(tela, (8, 4, 18), av_rect, border_radius=6)
            img_key = f"personagem_{nome.lower()}"
            img = self.game.imagens.get(img_key)
            if img and nome != "Aquele":
                img_s = pygame.transform.scale(img, (av_size - 4, av_size - 4))
                tela.blit(img_s, (av_rect.x + 2, av_rect.y + 2))
            else:
                pygame.draw.rect(tela, C_BORDA, av_rect, 1, border_radius=6)
                fb = self.fM.render(nome[:2].upper(), True, C_DIM)
                tela.blit(fb, (av_rect.centerx - fb.get_width() // 2,
                               av_rect.centery - fb.get_height() // 2))

            tx = hx + 10 + av_size + 10
            nome_ex = "?????" if nome == "Aquele" else nome
            nt = self.fM.render(nome_ex, True, C_OURO if sel else C_TEXTO)
            tela.blit(nt, (tx, hy + 22))
            ct = self.fP.render(classe if nome != "Aquele" else "?????", True, C_DIM)
            tela.blit(ct, (tx, hy + 50))
            if sel:
                pygame.draw.circle(tela, C_INSETO, (rect.right - 12, rect.y + 12), 5)

    def _draw_dificuldade(self, tela):
        r = self.area_dificuldade
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)
        tt = self.fM.render("DIFICULDADE DO DIRETOR ISECTUM", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 14))

        mouse = pygame.mouse.get_pos()
        cores_dif = [C_VERDE, C_OURO, C_PERIGO]
        for i, diff in enumerate(DIFICULDADES_CASTAS):
            rect = self.diff_rects[i]
            sel = i == self.dificuldade_idx
            hover = rect.collidepoint(mouse)
            cor = cores_dif[i]
            bg = (28, 16, 50) if sel else ((16, 10, 28) if not hover else (24, 14, 40))
            pygame.draw.rect(tela, bg, rect, border_radius=7)
            pygame.draw.rect(tela, cor if sel else C_BORDA, rect, 2 if sel else 1, border_radius=7)
            dt = self.fM.render(diff["nome"], True, cor if sel else C_TEXTO)
            tela.blit(dt, (rect.centerx - dt.get_width() // 2, rect.y + 8))
            dd = self.fMi.render(diff["desc"], True, C_DIM)
            if dd.get_width() > rect.width - 8:
                partes = diff["desc"].split(". ")
                y_text = rect.y + 30
                for parte in partes:
                    s = self.fMi.render(parte, True, C_DIM)
                    tela.blit(s, (rect.centerx - s.get_width() // 2, y_text))
                    y_text += 14
            else:
                tela.blit(dd, (rect.centerx - dd.get_width() // 2, rect.y + 32))

    def _draw_resolucao(self, tela):
        r = self.area_resolucao
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)
        tt = self.fM.render("RESOLUÇÃO", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 8))
        mouse = pygame.mouse.get_pos()
        for i, (rw, rh) in enumerate(RESOLUCOES):
            rect = self.res_rects[i]
            sel = i == self.resolucao_idx
            hover = rect.collidepoint(mouse)
            bg = (24, 40, 60) if sel else ((16, 20, 36) if not hover else (24, 30, 50))
            cor_b = (100, 200, 255) if sel else C_BORDA
            pygame.draw.rect(tela, bg, rect, border_radius=6)
            pygame.draw.rect(tela, cor_b, rect, 2 if sel else 1, border_radius=6)
            lbl = self.fMi.render(f"{rw}x{rh}", True, C_TEXTO if sel else C_DIM)
            tela.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                            rect.centery - lbl.get_height() // 2))

    def _draw_botoes(self, tela, W, H):
        mouse = pygame.mouse.get_pos()
        qtd = sum(1 for v in self.selecionados.values() if v)
        pode = qtd > 0
        if pode:
            hover = self.btn_iniciar.collidepoint(mouse)
            cor_bg  = (60, 15, 100) if hover else (40, 8, 70)
            cor_bd  = (200, 80, 255) if hover else C_ACENTO
            cor_txt = C_TEXTO
        else:
            cor_bg  = (18, 14, 28)
            cor_bd  = (55, 40, 75)
            cor_txt = C_DIM
        pygame.draw.rect(tela, cor_bg, self.btn_iniciar, border_radius=12)
        pygame.draw.rect(tela, cor_bd, self.btn_iniciar, 2, border_radius=12)
        lbl = f"🐛  INICIAR CASTAS  ({qtd} defensor{'es' if qtd != 1 else ''})" if pode else "SELECIONE AO MENOS 1 DEFENSOR"
        it = self.fM.render(lbl, True, cor_txt)
        tela.blit(it, (self.btn_iniciar.centerx - it.get_width() // 2,
                       self.btn_iniciar.centery - it.get_height() // 2))

    def _draw_instrucoes(self, tela, W, H):
        txt = "Clique nos heróis para selecionar/deselecionar | ESC para voltar"
        inst = self.fMi.render(txt, True, C_DIM)
        tela.blit(inst, (W // 2 - inst.get_width() // 2, H - 22))
