"""
castas_draw.py — Mixin de renderização para CastasState

Herda CercoStateDrawMixin e renderiza:
  - Painel lateral simplificado para o Diretor (estatísticas do deck dele).
  - A mão de cartas de insetos do Diretor na parte inferior.
  - O mapa tático destacando as zonas externas para onde ele pode enviar as hordas.
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

# Zonas externas válidas para o Diretor iniciar sua invasão
ZONAS_BORDA = ["campo_norte", "campo_sul", "campo_oeste", "campo_leste"]


class CastasStateDrawMixin(CercoStateDrawMixin):
    """Herda todo o draw do Cerco e adiciona camadas do modo Castas."""

    # ── DRAW PRINCIPAL ────────────────────────────────────────────────────
    def draw(self, tela):
        self._setup_layout()
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)

        # Brilho de fundo roxo/avermelhado sombrio (tema de insetos)
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (90, 15, 60, 20), (W // 5, H // 4), 320)
        pygame.draw.circle(glow, (25, 45, 10,  15), (W * 4 // 5, H * 3 // 4), 260)
        tela.blit(glow, (0, 0))

        self._draw_header(tela, W)
        self._draw_mapa(tela)

        if self.fase == "TURNO_DIRETOR":
            self._draw_painel_diretor(tela, W, H)
            self._draw_mao_diretor(tela)
        else:
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

    # ── HEADER SOBRESCRITO ────────────────────────────────────────────────
    def _draw_header(self, tela, W):
        bar = pygame.Surface((W, 62), pygame.SRCALPHA)
        bar.fill((10, 5, 20, 220))
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
            "TURNO_DIRETOR": "🐛 Turno do Filho do Imperador",
            "FASE_AMEACA":   "⚠ Fase de Ameaça",
            "FIM":           "FIM",
        }.get(self.fase, self.fase)
        cor_fase = C_DIRETOR if self.fase == "TURNO_DIRETOR" else C_HEROI
        rf = self.fM.render(f"Rodada {rodada}  |  {fase_txt}", True, cor_fase)
        tela.blit(rf, (W // 2 - rf.get_width() // 2, 12))

        # HUD recursos
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

    # ── PAINEL DO DIRETOR (Simplificado com estatísticas de Decks) ─────────
    def _draw_painel_diretor(self, tela, W, H):
        px = W - 318
        py = 65
        pw = 310
        ph = H - 75
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 8, 16, 220))
        tela.blit(panel, (px, py))
        pygame.draw.rect(tela, C_BORDA, (px, py, pw, ph), 1, border_radius=4)

        # Determina qual Filho do Imperador está ativo no momento
        idx = self.estado.get("diretor_ativo_idx", 0)
        ativo = self.diretores[idx] if idx < len(self.diretores) else self.diretores[0]
        acoes = self.estado["acoes_diretores"].get(ativo, 0)

        # Título do painel
        tt = self.fM.render(f"🐛 INVASÃO: {ativo.upper()}", True, C_DIRETOR)
        tela.blit(tt, (px + 15, py + 15))
        pygame.draw.line(tela, C_BORDA, (px + 8, py + 38), (px + pw - 8, py + 38), 1)

        # Instruções dinâmicas
        if self.casta_selecionada is None:
            inst_txt = "Oponente planejando ataque..." if self.num_diretores > 1 else "Selecione uma Carta da sua Mão!"
            inst_cor = C_DIM
        else:
            from src.cerco_isectum import DADOS_INIMIGOS
            c_nome = DADOS_INIMIGOS.get(self.casta_selecionada, {}).get("nome", "")
            inst_txt = f"Invadindo com: {c_nome}"
            inst_cor = C_OURO
        inst = self.fP.render(inst_txt, True, inst_cor)
        tela.blit(inst, (px + 15, py + 48))

        # Estatísticas do Deck de Castas do Filho Ativo
        deck_dir = self.estado.get("decks_diretores", {}).get(ativo, [])
        desc_dir = self.estado.get("descarte_diretores", {}).get(ativo, [])
        
        info_y = py + 100
        lbl_deck = self.fM.render(f"🎴 Deck do {ativo}: {len(deck_dir)} cartas", True, C_TEXTO)
        lbl_desc = self.fM.render(f"🗑 Pilha de Descarte: {len(desc_dir)} cartas", True, C_DIM)
        tela.blit(lbl_deck, (px + 15, info_y))
        tela.blit(lbl_desc, (px + 15, info_y + 30))

        # Detalhes da casta selecionada (se houver)
        if self.casta_selecionada:
            from src.cerco_isectum import DADOS_INIMIGOS
            dados = DADOS_INIMIGOS[self.casta_selecionada]
            
            dy = py + 200
            pygame.draw.rect(tela, (30, 10, 20), (px + 10, dy, pw - 20, 120), border_radius=6)
            pygame.draw.rect(tela, C_BORDA, (px + 10, dy, pw - 20, 120), 1, border_radius=6)
            
            nome_lbl = self.fM.render(f"{dados['emoji']} {dados['nome']}", True, C_OURO)
            classe_lbl = self.fP.render(f"Classe Base: {dados['classe']}", True, C_INSETO)
            tela.blit(nome_lbl, (px + 20, dy + 10))
            tela.blit(classe_lbl, (px + 20, dy + 32))
            
            # Descrição do efeito (com quebra de linha manual simples)
            efeito = dados.get("efeito", "")
            palavras = efeito.split()
            linhas = []
            linha_atual = ""
            for pal in palavras:
                if len(linha_atual + " " + pal) < 32:
                    linha_atual += (" " if linha_atual else "") + pal
                else:
                    linhas.append(linha_atual)
                    linha_atual = pal
            if linha_atual:
                linhas.append(linha_atual)
                
            ly = dy + 58
            for linha in linhas[:3]:
                tela.blit(self.fMi.render(linha, True, C_TEXTO), (px + 20, ly))
                ly += 16

        # Botão Encerrar Turno do Diretor (desabilitado se controlado pela IA de múltiplos Bots)
        btn_y = H - 52
        self.btn_diretor_encerrar = pygame.Rect(px + 8, btn_y, pw - 16, 38)
        mouse = pygame.mouse.get_pos()
        hover_enc = self.btn_diretor_encerrar.collidepoint(mouse)
        cor_enc_bg = (80, 20, 30) if hover_enc else (50, 10, 20)
        cor_enc_bd = (255, 80, 80) if hover_enc else C_PERIGO
        pygame.draw.rect(tela, cor_enc_bg, self.btn_diretor_encerrar, border_radius=8)
        pygame.draw.rect(tela, cor_enc_bd, self.btn_diretor_encerrar, 2, border_radius=8)
        
        texto_btn = "Oponente Agindo..." if self.num_diretores > 1 else "⏭  Encerrar Turno do Filho"
        enc_t = self.fM.render(texto_btn, True, C_TEXTO)
        tela.blit(enc_t, (
            self.btn_diretor_encerrar.centerx - enc_t.get_width() // 2,
            self.btn_diretor_encerrar.centery - enc_t.get_height() // 2,
        ))

        # Highlight das zonas válidas (apenas os Campos Externos) no mapa
        if self.modo_acao == MODO_DIR_ESCOLHER_ZONA:
            self._highlight_zonas_borda(tela)

    # ── MÃO DE CARTAS DO DIRETOR ──────────────────────────────────────────
    def _draw_mao_diretor(self, tela):
        """Renderiza a mão de cartas de insetos do Filho do Imperador ativo na parte inferior."""
        from src.cerco_isectum import DADOS_INIMIGOS

        mr = self.mao_rect

        # Desenha a área de mão estilizada com tema Isectum (sombrio)
        pygame.draw.rect(tela, (18, 8, 20), mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)

        # Pega a mão do diretor ativo
        idx = self.estado.get("diretor_ativo_idx", 0)
        ativo = self.diretores[idx] if idx < len(self.diretores) else self.diretores[0]
        mao_dir = self.estado.get("maos_diretores", {}).get(ativo, [])
        self.diretor_carta_rects = []

        if not mao_dir:
            vazia_lbl = self.fM.render(f"MÃO DE {ativo.upper()} VAZIA", True, C_DIM)
            tela.blit(vazia_lbl, (mr.centerx - vazia_lbl.get_width() // 2, mr.centery - vazia_lbl.get_height() // 2))
            return

        # Dimensões e posicionamento das cartas
        card_w = 140
        card_h = mr.height - 16
        gap = 12
        total_w = len(mao_dir) * card_w + (len(mao_dir) - 1) * gap
        start_x = mr.x + (mr.width - total_w) // 2

        mouse = pygame.mouse.get_pos()

        for idx, inseto_id in enumerate(mao_dir):
            cx = start_x + idx * (card_w + gap)
            cy = mr.y + 8
            card_rect = pygame.Rect(cx, cy, card_w, card_h)
            self.diretor_carta_rects.append((inseto_id, card_rect))

            dados = DADOS_INIMIGOS.get(inseto_id, {})
            sel = (inseto_id == self.casta_selecionada)
            hover = card_rect.collidepoint(mouse)

            # Cor de fundo e borda com tema de insetos (Roxo/Avermelhado)
            bg_color = (48, 12, 32) if sel else ((32, 10, 24) if hover else (22, 6, 16))
            border_color = C_INSETO if sel else ((255, 120, 180) if hover else C_BORDA)

            pygame.draw.rect(tela, bg_color, card_rect, border_radius=6)
            pygame.draw.rect(tela, border_color, card_rect, 2 if sel or hover else 1, border_radius=6)

            # Emoji
            emoji_lbl = self.fG.render(dados.get("emoji", "🐛"), True, C_TEXTO)
            tela.blit(emoji_lbl, (cx + 8, cy + 8))

            # Nome
            nome = dados.get("nome", inseto_id).split()
            nome_str = nome[0] if nome else "Inseto"
            nome_lbl = self.fP.render(nome_str, True, C_OURO if sel else C_TEXTO)
            tela.blit(nome_lbl, (cx + 34, cy + 12))

            # Classe
            classe_lbl = self.fMi.render(dados.get("classe", ""), True, C_ACENTO)
            tela.blit(classe_lbl, (cx + 8, cy + 34))

            # Habilidade resumida
            efeito = dados.get("efeito", "")
            linhas = []
            palavras = efeito.split()
            linha = ""
            for p in palavras:
                if len(linha + " " + p) < 17:
                    linha += (" " if linha else "") + p
                else:
                    linhas.append(linha)
                    linha = p
            if linha:
                linhas.append(linha)

            ly = cy + 54
            for l in linhas[:3]:
                tela.blit(self.fMi.render(l, True, C_DIM if not sel else C_TEXTO), (cx + 8, ly))
                ly += 14

    # ── HIGHLIGHT DE ZONAS (Apenas os campos de spawn exterior) ────────────
    def _highlight_zonas_borda(self, tela):
        """Destaca visualmente apenas os Campos Externos de spawn no mapa."""
        from src.resolvedor_acoes import ZONAS_GRID
        self._zona_rects_mapa = {}

        for zona_id, (x1, y1, x2, y2) in ZONAS_GRID.items():
            if zona_id not in ZONAS_BORDA:
                continue
            # Converte coordenadas do grid para tela (isométrico)
            pts = []
            for gx, gy in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:
                sx, sy = self._grid_to_screen(gx, gy)
                pts.append((sx, sy))
            if len(pts) >= 3:
                s = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
                # Destaque vermelho/laranja pulsante para área de spawn
                pygame.draw.polygon(s, (255, 100, 50, 45), pts)
                pygame.draw.polygon(s, (255, 100, 50, 180), pts, 2)
                tela.blit(s, (0, 0))

                # Cria o rect AABB para colisão de clique
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                self._zona_rects_mapa[zona_id] = pygame.Rect(
                    min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)
                )

    def _grid_to_screen(self, gx, gy):
        """Converte coordenadas da grade lógica para posição de pixel isométrica."""
        mr = self.mapa_rect
        CELL = 48
        ox = mr.x + mr.width // 2
        oy = mr.y + 40
        sx = ox + (gx - gy) * CELL * self.zoom // 2
        sy = oy + (gx + gy) * CELL * self.zoom // 4
        return int(sx), int(sy)
