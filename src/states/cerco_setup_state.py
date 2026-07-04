"""
cerco_setup_state.py — Tela de configuração do modo Cerco contra Isectum

Permite ao jogador selecionar:
  - Quantidade e quais personagens/heróis participarão
  - Dificuldade (Fácil / Normal / Difícil)
"""
from __future__ import annotations
import pygame
from .state_base import GameState
from ..config import ESTADO_JOGO_MENU_PRINCIPAL, ESTADO_JOGO_CERCO, LARGURA_TELA, ALTURA_TELA, RESOLUCOES, atualizar_resolucao
from ..personagens import Stark, Elden, Doom, Gruu, Kuro, Darwin, Aquele

C_BG        = (8, 10, 20)
C_PAINEL    = (14, 16, 30)
C_BORDA     = (45, 48, 78)
C_ACENTO    = (180, 120, 255)
C_OURO      = (255, 195, 40)
C_TEXTO     = (235, 240, 255)
C_DIM       = (110, 120, 155)
C_VERDE     = (50, 220, 110)
C_PERIGO    = (255, 55, 55)

DIFICULDADES = [
    {"id": "facil",   "nome": "Fácil",   "pedregulhos": 5,  "tesouro": 30, "reserva": 8},
    {"id": "normal",  "nome": "Normal",  "pedregulhos": 8,  "tesouro": 20, "reserva": 10},
    {"id": "dificil", "nome": "Difícil", "pedregulhos": 12, "tesouro": 15, "reserva": 14},
]

# Heróis disponíveis para seleção
HEROIS_DISPONIVEIS = [
    ("Aquele", Aquele, "Guerreiro"),
    ("Stark",  Stark,  "Paladino"),
    ("Elden",  Elden,  "Mago"),
    ("Doom",   Doom,   "Ladino"),
    ("Gruu",   Gruu,   "Barbaro"),
    ("Kuro",   Kuro,   "Ladino"),
    ("Darwin", Darwin, "Druida"),
]

ICONES_HEROI = {
    "Aquele": "🌑",
    "Stark":  "🛡️",
    "Elden":  "✨",
    "Doom":   "🌑",
    "Gruu":   "💀",
    "Kuro":   "🗡️",
    "Darwin": "🌿",
}


class CercoSetupState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self._setup_fonts()
        self._setup_layout()

        self.selecionados = {nome: False for nome, _, _ in HEROIS_DISPONIVEIS}
        self.selecionados["Aquele"] = True
        self.dificuldade_idx = 1
        self.resolucao_idx = 2  # 1024x768 por padrão (índice 2 em RESOLUCOES)
        # Encontra a resolução atual no índice correspondente
        for i, (rw, rh) in enumerate(RESOLUCOES):
            if rw == LARGURA_TELA and rh == ALTURA_TELA:
                self.resolucao_idx = i
                break

    def _setup_fonts(self):
        self.fT  = pygame.font.Font(None, 48)
        self.fG  = pygame.font.Font(None, 36)
        self.fM  = pygame.font.Font(None, 28)
        self.fP  = pygame.font.Font(None, 22)
        self.fMi = pygame.font.Font(None, 18)

    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA

        qtd_herois = len(HEROIS_DISPONIVEIS)
        linhas_herois = max(1, (qtd_herois + 4) // 5)
        altura_herois = 50 + linhas_herois * 100
        y_dif = 90 + altura_herois + 15
        self.area_titulo   = pygame.Rect(0, 0, W, 70)
        self.area_herois   = pygame.Rect(40, 90, W - 80, altura_herois)
        self.area_dificuldade = pygame.Rect(40, y_dif, W - 80, 130)
        self.area_resolucao = pygame.Rect(40, y_dif + 145, W - 80, 100)
        self.btn_iniciar   = pygame.Rect(W // 2 - 120, H - 60, 240, 42)
        self.btn_voltar    = pygame.Rect(20, 20, 100, 36)

        self.heroi_rects = []

        self.diff_rects = []
        dx = self.area_dificuldade.x + 30
        dy = self.area_dificuldade.y + 50
        for i, _ in enumerate(DIFICULDADES):
            self.diff_rects.append(pygame.Rect(dx + i * 200, dy, 170, 44))

        self.res_rects = []
        rx = self.area_resolucao.x + 20
        ry = self.area_resolucao.y + 45
        for i, _ in enumerate(RESOLUCOES):
            self.res_rects.append(pygame.Rect(rx + i * 105, ry, 95, 36))

    def get_config(self):
        """Retorna as configurações selecionadas para iniciar o jogo."""
        herois_escolhidos = []
        for nome, cls, _ in HEROIS_DISPONIVEIS:
            if self.selecionados.get(nome, False):
                herois_escolhidos.append((nome, cls))
        diff = DIFICULDADES[self.dificuldade_idx]
        return {
            "herois": herois_escolhidos,
            "dificuldade": diff,
        }

    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.cerco_setup_state = None
                self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Voltar
                if self.btn_voltar.collidepoint(mouse):
                    self.game.cerco_setup_state = None
                    self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    return

                # Iniciar
                if self.btn_iniciar.collidepoint(mouse):
                    qtd = sum(1 for v in self.selecionados.values() if v)
                    if qtd == 0:
                        return
                    config = self.get_config()
                    from .cerco_state import CercoState
                    self.game.cerco_state = CercoState(self.game, config)
                    self.game.cerco_setup_state = None
                    self.game.estado_jogo = ESTADO_JOGO_CERCO
                    return

                # Clique em herói
                for i, rect in enumerate(self.heroi_rects):
                    if rect and rect.collidepoint(mouse):
                        nome = HEROIS_DISPONIVEIS[i][0]
                        self.selecionados[nome] = not self.selecionados[nome]
                        return

                # Clique em dificuldade
                for i, rect in enumerate(self.diff_rects):
                    if rect and rect.collidepoint(mouse):
                        self.dificuldade_idx = i
                        return

                # Clique em resolução
                for i, rect in enumerate(self.res_rects):
                    if rect and rect.collidepoint(mouse):
                        self.resolucao_idx = i
                        w, h = RESOLUCOES[i]
                        atualizar_resolucao(w, h)
                        self.game.tela = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        import json
                        with open("settings.json", "w") as f:
                            json.dump({"width": w, "height": h}, f)
                        self._setup_layout()
                        return

    def update(self):
        pass

    def draw(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)
        self._draw_titulo(tela, W)
        self._draw_herois(tela, W)
        self._draw_dificuldade(tela)
        self._draw_resolucao(tela)
        self._draw_botoes(tela)
        self._draw_instrucoes(tela, W)

    def _draw_titulo(self, tela, W):
        bar = pygame.Surface((W, 70), pygame.SRCALPHA)
        bar.fill((10, 12, 24, 220))
        tela.blit(bar, (0, 0))
        pygame.draw.line(tela, C_BORDA, (0, 70), (W, 70), 1)

        t1 = self.fG.render("CONFIGURAÇÃO DO", True, C_ACENTO)
        t2 = self.fG.render("CERCO", True, C_OURO)
        tela.blit(t1, (W // 2 - (t1.get_width() + t2.get_width() + 8) // 2, 16))
        tela.blit(t2, (W // 2 - (t1.get_width() + t2.get_width() + 8) // 2 + t1.get_width() + 8, 16))

        mouse = pygame.mouse.get_pos()
        hover = self.btn_voltar.collidepoint(mouse)
        bc = (48, 48, 72) if hover else (24, 24, 42)
        pygame.draw.rect(tela, bc, self.btn_voltar, border_radius=6)
        pygame.draw.rect(tela, C_BORDA if hover else (30, 30, 50), self.btn_voltar, 1, border_radius=6)
        
        vt = self.fMi.render("< MENU", True, C_TEXTO if hover else C_DIM)
        tela.blit(vt, (self.btn_voltar.centerx - vt.get_width() // 2, self.btn_voltar.centery - vt.get_height() // 2))

    def _draw_herois(self, tela, W):
        r = self.area_herois
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)

        tt = self.fM.render("SELECIONE SEUS HERÓIS", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 12))

        mouse = pygame.mouse.get_pos()
        self.heroi_rects = []
        cols = 4 if len(HEROIS_DISPONIVEIS) <= 4 else 5
        cw = (r.width - 60) // cols
        ch = 90
        y0 = r.y + 50

        for i, (nome, _, classe) in enumerate(HEROIS_DISPONIVEIS):
            col = i % cols
            row = i // cols
            hx = r.x + 20 + col * (cw + 10)
            hy = y0 + row * (ch + 10)

            rect = pygame.Rect(hx, hy, cw, ch)
            self.heroi_rects.append(rect)

            selecionado = self.selecionados.get(nome, False)
            hover = rect.collidepoint(mouse)

            if selecionado:
                cor_fundo = (32, 28, 58) if not hover else (42, 38, 75)
                cor_borda = C_ACENTO
            else:
                cor_fundo = (18, 16, 28) if not hover else (26, 24, 42)
                cor_borda = C_BORDA

            pygame.draw.rect(tela, cor_fundo, rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, rect, 2 if selecionado else 1, border_radius=8)

            # Avatar à esquerda
            avatar_size = 64
            avatar_rect = pygame.Rect(hx + 12, hy + (ch - avatar_size) // 2, avatar_size, avatar_size)
            pygame.draw.rect(tela, (10, 10, 20), avatar_rect, border_radius=6)
            
            if nome == "Aquele":
                pygame.draw.rect(tela, C_BORDA, avatar_rect, 1, border_radius=6)
                fallback = self.fT.render("🌑", True, C_DIM)
                tela.blit(fallback, (avatar_rect.centerx - fallback.get_width() // 2, avatar_rect.centery - fallback.get_height() // 2))
            else:
                img_key = f"personagem_{nome.lower()}"
                img = self.game.imagens.get(img_key)
                if img:
                    img_scaled = pygame.transform.scale(img, (avatar_size - 4, avatar_size - 4))
                    tela.blit(img_scaled, (avatar_rect.x + 2, avatar_rect.y + 2))
                else:
                    pygame.draw.rect(tela, C_BORDA, avatar_rect, 1, border_radius=6)
                    fallback = self.fP.render(nome[:2].upper(), True, C_DIM)
                    tela.blit(fallback, (avatar_rect.centerx - fallback.get_width() // 2, avatar_rect.centery - fallback.get_height() // 2))

            # Textos alinhados à direita do avatar
            text_x = hx + 12 + avatar_size + 12
            
            nome_exibido = "?????" if nome == "Aquele" else nome
            classe_exibida = "?????" if nome == "Aquele" else classe

            nt = self.fG.render(nome_exibido, True, C_OURO if selecionado else C_TEXTO)
            tela.blit(nt, (text_x, hy + 20))

            ct = self.fP.render(classe_exibida, True, C_DIM)
            tela.blit(ct, (text_x, hy + 48))

            # Indicador bolinha verde discreto
            if selecionado:
                pygame.draw.circle(tela, C_VERDE, (rect.right - 14, rect.y + 14), 5)

    def _draw_dificuldade(self, tela):
        r = self.area_dificuldade
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)

        tt = self.fM.render("DIFICULDADE DO COMBATE", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 12))

        mouse = pygame.mouse.get_pos()
        cores_diff = [C_VERDE, C_OURO, C_PERIGO]

        for i, diff in enumerate(DIFICULDADES):
            rect = self.diff_rects[i]
            selecionado = i == self.dificuldade_idx
            hover = rect.collidepoint(mouse)
            cor = cores_diff[i]

            if selecionado:
                bg = (32, 28, 58) if not hover else (42, 38, 75)
            else:
                bg = (18, 16, 28) if not hover else (26, 24, 42)

            pygame.draw.rect(tela, bg, rect, border_radius=6)
            pygame.draw.rect(tela, cor if selecionado else C_BORDA, rect, 2 if selecionado else 1, border_radius=6)

            dt = self.fM.render(diff["nome"], True, cor if selecionado else C_TEXTO)
            tela.blit(dt, (rect.centerx - dt.get_width() // 2, rect.y + 6))

            detalhes = f"Minas: {diff['pedregulhos']}  |  Ouro: {diff['tesouro']}  |  Reserva: {diff['reserva']}"
            dd = self.fMi.render(detalhes, True, C_DIM)
            tela.blit(dd, (rect.centerx - dd.get_width() // 2, rect.y + 26))

    def _draw_resolucao(self, tela):
        r = self.area_resolucao
        pygame.draw.rect(tela, C_PAINEL, r, border_radius=10)
        pygame.draw.rect(tela, C_BORDA, r, 1, border_radius=10)

        tt = self.fM.render("RESOLUÇÃO DA TELA", True, C_ACENTO)
        tela.blit(tt, (r.x + 20, r.y + 12))

        mouse = pygame.mouse.get_pos()
        for i, (rw, rh) in enumerate(RESOLUCOES):
            rect = self.res_rects[i]
            selecionado = i == self.resolucao_idx
            hover = rect.collidepoint(mouse)

            if selecionado:
                bg = (30, 50, 75) if not hover else (45, 70, 105)
            else:
                bg = (18, 22, 38) if not hover else (30, 35, 55)
            cor_b = (100, 200, 255) if selecionado else C_BORDA

            pygame.draw.rect(tela, bg, rect, border_radius=6)
            pygame.draw.rect(tela, cor_b, rect, 2 if selecionado else 1, border_radius=6)

            label = f"{rw}x{rh}"
            dt = self.fMi.render(label, True, C_TEXTO if selecionado else C_DIM)
            tela.blit(dt, (rect.centerx - dt.get_width() // 2, rect.y + 10))

    def _draw_botoes(self, tela):
        mouse = pygame.mouse.get_pos()
        qtd = sum(1 for v in self.selecionados.values() if v)
        pode_iniciar = qtd > 0

        if pode_iniciar:
            hover = self.btn_iniciar.collidepoint(mouse)
            cor_btn = (46, 124, 62) if hover else (34, 98, 48)
            cor_borda = (100, 235, 120) if hover else C_VERDE
            cor_texto = C_TEXTO
        else:
            cor_btn = (24, 24, 28)
            cor_borda = (60, 60, 70)
            cor_texto = C_DIM

        pygame.draw.rect(tela, cor_btn, self.btn_iniciar, border_radius=10)
        pygame.draw.rect(tela, cor_borda, self.btn_iniciar, 2, border_radius=10)

        txt = f"INICIAR CERCO ({qtd} herói{'s' if qtd != 1 else ''})" if pode_iniciar else "SELECIONE AO MENOS 1 HERÓI"
        it = self.fM.render(txt, True, cor_texto)
        tela.blit(it, (self.btn_iniciar.centerx - it.get_width() // 2,
                       self.btn_iniciar.centery - it.get_height() // 2))

    def _draw_instrucoes(self, tela, W):
        txt = "Clique nos heróis para selecionar/deselecionar | ESC para voltar ao Menu"
        inst = self.fMi.render(txt, True, C_DIM)
        tela.blit(inst, (W // 2 - inst.get_width() // 2, ALTURA_TELA - 30))
