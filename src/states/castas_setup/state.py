"""
castas_setup_state.py — Tela de Configuração do Modo Castas dos Isectum
Focado no modo integrado (Cerco Tático com Duelos Grimwood), onde se escolhe os Heróis e 1 a 4 Filhos do Imperador oponentes.
"""
from __future__ import annotations
import pygame
import json

from ..state_base import GameState
from ...config import (
    ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA,
    RESOLUCOES, atualizar_resolucao
)
from .data import (
    ESTADO_JOGO_CASTAS,
    C_BG, C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_TEXTO, C_DIM,
    C_VERDE, C_PERIGO, C_INSETO,
    DIFICULDADES_CASTAS, HEROIS_DISPONIVEIS,
)


class CastasSetupState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self._setup_fonts()
        
        self.num_adversarios = 1        # 1 a 4 Filhos do Imperador oponentes
        self.controle_filhos = "humano"  # "humano" (hotseat) ou "ia" (bot)
        self.selecionados = {nome: False for nome, _, _ in HEROIS_DISPONIVEIS}
        self.selecionados["Stark"] = True
        self.dificuldade_idx = 1
        
        self.resolucao_idx = 0
        for i, (rw, rh) in enumerate(RESOLUCOES):
            if rw == LARGURA_TELA and rh == ALTURA_TELA:
                self.resolucao_idx = i
                break
                
        self._setup_layout()

    def _setup_fonts(self):
        self.fT  = pygame.font.Font(None, 52)
        self.fG  = pygame.font.Font(None, 36)
        self.fM  = pygame.font.Font(None, 28)
        self.fP  = pygame.font.Font(None, 22)
        self.fMi = pygame.font.Font(None, 18)

    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        
        # Área de escolha de Heróis
        qtd_herois = len(HEROIS_DISPONIVEIS)
        linhas_herois = max(1, (qtd_herois + 4) // 5)
        altura_herois = 55 + linhas_herois * 105
        self.area_herois = pygame.Rect(40, 90, W - 80, altura_herois)
        
        # Área de escolha de Filhos do Imperador (oponentes 1-4)
        y_oponentes = 90 + altura_herois + 10
        self.area_oponentes = pygame.Rect(40, y_oponentes, W - 80, 110)
        
        # Área de Dificuldade
        y_dif = y_oponentes + 120
        self.area_dificuldade = pygame.Rect(40, y_dif, W - 80, 120)
        
        # Resolução
        self.area_resolucao = pygame.Rect(40, y_dif + 132, W - 80, 80)
        
        self.btn_iniciar = pygame.Rect(W // 2 - 200, H - 58, 400, 44)
        self.btn_voltar  = pygame.Rect(20, 18, 100, 34)
        
        # Retângulos para heróis
        self.heroi_rects = []
        # Retângulos para dificuldades
        self.diff_rects  = []
        dx = self.area_dificuldade.x + 20
        dy = self.area_dificuldade.y + 45
        for i in range(len(DIFICULDADES_CASTAS)):
            self.diff_rects.append(pygame.Rect(dx + i * 220, dy, 200, 55))
            
        # Retângulos para resoluções
        self.res_rects = []
        rx = self.area_resolucao.x + 20
        ry = self.area_resolucao.y + 32
        for i in range(len(RESOLUCOES)):
            self.res_rects.append(pygame.Rect(rx + i * 105, ry, 95, 32))

        # Retângulos para quantidade de oponentes
        self.oponente_rects = []
        ox = self.area_oponentes.x + 20
        oy = self.area_oponentes.y + 40
        for i in range(4): # 1 a 4 Filhos do Imperador
            self.oponente_rects.append(pygame.Rect(ox + i * 110, oy, 95, 50))

        # Retângulos para tipo de controle
        self.btn_ctrl_humano = pygame.Rect(ox + 480, oy, 180, 50)
        self.btn_ctrl_ia     = pygame.Rect(ox + 670, oy, 180, 50)

    def get_config(self):
        herois_escolhidos = []
        for nome, cls, _ in HEROIS_DISPONIVEIS:
            if self.selecionados.get(nome, False):
                herois_escolhidos.append((nome, cls))
        diff = DIFICULDADES_CASTAS[self.dificuldade_idx]
        return {
            "herois": herois_escolhidos, 
            "dificuldade": diff,
            "num_diretores": self.num_adversarios,
            "controle_filhos": self.controle_filhos
        }

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
                    
                # Botão Iniciar
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

                # Cliques nos Heróis
                for i, rect in enumerate(self.heroi_rects):
                    if rect and rect.collidepoint(mouse):
                        nome = HEROIS_DISPONIVEIS[i][0]
                        self.selecionados[nome] = not self.selecionados[nome]
                        return
                        
                # Cliques nos Filhos do Imperador (oponentes)
                for i, rect in enumerate(self.oponente_rects):
                    if rect and rect.collidepoint(mouse):
                        self.num_adversarios = i + 1
                        return

                # Clique no tipo de controle (Humano vs IA)
                if self.btn_ctrl_humano.collidepoint(mouse):
                    self.controle_filhos = "humano"
                    return
                if self.btn_ctrl_ia.collidepoint(mouse):
                    self.controle_filhos = "ia"
                    return

                # Escolha de Dificuldade
                for i, rect in enumerate(self.diff_rects):
                    if rect and rect.collidepoint(mouse):
                        self.dificuldade_idx = i
                        return
                        
                # Escolha de Resolução
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
        
        # Grid decorativo de fundo
        for ix in range(0, W, 60):
            for iy in range(0, H, 60):
                pygame.draw.circle(tela, (25, 10, 45), (ix, iy), 2)
                
        self._draw_titulo(tela, W)
        self._draw_herois(tela, W)
        self._draw_adversarios_seletor(tela)
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
        tela.blit(emoji_surf, (W // 2 - 240, 18))
        t1 = self.fG.render("CASTAS DOS", True, C_ACENTO)
        t2 = self.fG.render("ISECTUM", True, C_OURO)
        cx = W // 2 - (t1.get_width() + t2.get_width() + 12) // 2
        tela.blit(t1, (cx, 22))
        tela.blit(t2, (cx + t1.get_width() + 12, 22))
        sub = self.fMi.render("Cerco Tático à Fortaleza com Resolução de Invasão via Duelo de Cartas (Grimwood)", True, C_DIM)
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
        tela.blit(tt, (r.x + 20, r.y + 12))

        mouse = pygame.mouse.get_pos()
        self.heroi_rects = []
        cols = 5
        cw = (r.width - 60) // cols
        ch = 95

        for i, (nome, _, classe) in enumerate(HEROIS_DISPONIVEIS):
            col = i % cols
            row = i // cols
            hx = r.x + 20 + col * (cw + 10)
            hy = r.y + 44 + row * (ch + 8)
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

    def _draw_adversarios_seletor(self, tela):
        """Desenha o painel de escolha de Filhos do Imperador oponentes e seu controle."""
        r = self.area_oponentes
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)
        
        tt = self.fM.render("QUANTIDADE DE FILHOS DO IMPERADOR", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 10))

        tt_ctrl = self.fM.render("CONTROLE DOS ADVERSÁRIOS", True, C_ACENTO)
        tela.blit(tt_ctrl, (r.x + 480, r.y + 10))

        mouse = pygame.mouse.get_pos()
        for i, rect in enumerate(self.oponente_rects):
            sel = self.num_adversarios == (i + 1)
            hover = rect.collidepoint(mouse)
            bg = (60, 15, 70) if sel else ((28, 12, 45) if hover else (18, 8, 28))
            bd = C_ACENTO if sel else C_BORDA
            
            pygame.draw.rect(tela, bg, rect, border_radius=8)
            pygame.draw.rect(tela, bd, rect, 2 if sel else 1, border_radius=8)
            
            num_t = self.fG.render(f"{i + 1} Filho" + ("s" if i > 0 else ""), True, C_OURO if sel else C_TEXTO)
            tela.blit(num_t, (rect.centerx - num_t.get_width() // 2, rect.centery - num_t.get_height() // 2))

        # Desenha botões de controle (Humano vs IA)
        # Humano (Hotseat)
        sel_h = self.controle_filhos == "humano"
        hov_h = self.btn_ctrl_humano.collidepoint(mouse)
        bg_h = (15, 60, 40) if sel_h else ((15, 30, 20) if hov_h else (12, 18, 15))
        bd_h = C_VERDE if sel_h else C_BORDA
        pygame.draw.rect(tela, bg_h, self.btn_ctrl_humano, border_radius=8)
        pygame.draw.rect(tela, bd_h, self.btn_ctrl_humano, 2 if sel_h else 1, border_radius=8)
        txt_h = self.fMi.render("👨‍💻 JOGADORES (HOTSEAT)", True, C_TEXTO)
        tela.blit(txt_h, (self.btn_ctrl_humano.centerx - txt_h.get_width() // 2, self.btn_ctrl_humano.centery - txt_h.get_height() // 2))

        # IA (Robô)
        sel_ia = self.controle_filhos == "ia"
        hov_ia = self.btn_ctrl_ia.collidepoint(mouse)
        bg_ia = (90, 15, 35) if sel_ia else ((45, 10, 20) if hov_ia else (18, 8, 12))
        bd_ia = C_PERIGO if sel_ia else C_BORDA
        pygame.draw.rect(tela, bg_ia, self.btn_ctrl_ia, border_radius=8)
        pygame.draw.rect(tela, bd_ia, self.btn_ctrl_ia, 2 if sel_ia else 1, border_radius=8)
        txt_ia = self.fMi.render("🤖 INTELIGÊNCIA ARTIFICIAL", True, C_TEXTO)
        tela.blit(txt_ia, (self.btn_ctrl_ia.centerx - txt_ia.get_width() // 2, self.btn_ctrl_ia.centery - txt_ia.get_height() // 2))

    def _draw_dificuldade(self, tela):
        r = self.area_dificuldade
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)
        tt = self.fM.render("DIFICULDADE DA PARTIDA", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 10))

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
            
            desc_text = diff["desc"].replace("Diretor", "Filhos").replace("Filho do Imperador", "Filhos")
            dd = self.fMi.render(desc_text, True, C_DIM)
            if dd.get_width() > rect.width - 8:
                partes = desc_text.split(". ")
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
        lbl = f"🏰  INICIAR CERCO TÁTICO  ({qtd} defensor{'es' if qtd != 1 else ''} vs {self.num_adversarios} Filho{'s' if self.num_adversarios > 1 else ''})" if pode else "SELECIONE AO MENOS 1 DEFENSOR"

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
        it = self.fM.render(lbl, True, cor_txt)
        tela.blit(it, (self.btn_iniciar.centerx - it.get_width() // 2,
                       self.btn_iniciar.centery - it.get_height() // 2))

    def _draw_instrucoes(self, tela, W, H):
        txt = "Escolha heróis, oponentes e dificuldade da fortaleza | ESC para voltar"
        inst = self.fMi.render(txt, True, C_DIM)
        tela.blit(inst, (W // 2 - inst.get_width() // 2, H - 22))
