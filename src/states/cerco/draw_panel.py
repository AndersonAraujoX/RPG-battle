"""
draw_panel.py — Mixin de renderização do painel lateral (recursos, mercado de melhorias e histórico de eventos) para CercoState.
"""
from __future__ import annotations
import pygame

from ...config import LARGURA_TELA, ALTURA_TELA
from .data import (
    C_PAINEL, C_BORDA, C_ACENTO, C_OURO, C_VERDE, C_PERIGO,
    C_CERCO, C_TEXTO, C_DIM, C_INVASOR,
)


class CercoDrawPanelMixin:
    """Sub-mixin com a renderização do painel lateral, mercado e logs."""

    _slot_rects_cache: dict = {}

    def _slot_rect(self, slot_id):
        return self._slot_rects_cache.get(slot_id)

    def _draw_painel_lateral(self, tela):
        pr = self.painel_rect
        pygame.draw.rect(tela, C_PAINEL, pr, border_radius=10)
        pygame.draw.rect(tela, C_BORDA,  pr, 1, border_radius=10)
        
        old_clip = tela.get_clip()
        tela.set_clip(pr.inflate(-2, -2))
        x, y, pw, ph = pr.x, pr.y, pr.width, pr.height
        dep = self.estado.get("recursos_depositados", {})
        yt = y + 8

        # ── RECURSOS DEPOSITADOS ─────────────────────────────────────────
        tt = self.fMi.render("RECURSOS DEPOSITADOS", True, C_ACENTO)
        tela.blit(tt, (x + pw // 2 - tt.get_width() // 2, yt)); yt += 16

        res_info = [
            ("[W] MAD", "madeira", (100, 200,  90)),
            ("[L] COU", "couro",   (210, 150,  60)),
            ("[I] MET", "metal",   (160, 180, 240))
        ]
        slot_w = (pw - 24) // 3
        rx = x + 8
        for label, key, cor in res_info:
            s_rect = pygame.Rect(rx, yt, slot_w, 40)
            qtd = dep.get(key, 0)
            fundo = (30, 35, 50) if qtd > 0 else (14, 16, 26)
            pygame.draw.rect(tela, fundo, s_rect, border_radius=5)
            pygame.draw.rect(tela, cor if qtd > 0 else C_BORDA, s_rect, 1, border_radius=5)
            lbl = self.fMi.render(label, True, cor if qtd > 0 else C_DIM)
            tela.blit(lbl, (s_rect.centerx - lbl.get_width() // 2, s_rect.y + 5))
            val = self.fP.render(str(qtd), True, C_OURO if qtd > 0 else C_DIM)
            tela.blit(val, (s_rect.centerx - val.get_width() // 2, s_rect.y + 22))
            rx += slot_w + 4
        yt += 46

        # ── Tamanho do deck ──────────────────────────────────────────────
        deck_atual = len(self.estado.get("deck_heroi", [])) + len(self.estado.get("mao", [])) + len(self.estado.get("descarte", []))
        deck_max = self.estado.get("tamanho_deck_max", 12)
        deck_cor = C_PERIGO if deck_atual >= deck_max else C_VERDE
        deck_txt = self.fMi.render(f"Deck: {deck_atual}/{deck_max} cartas", True, deck_cor)
        tela.blit(deck_txt, (x + pw // 2 - deck_txt.get_width() // 2, yt))
        
        bar_w = pw - 24
        bar_rect = pygame.Rect(x + 12, yt + 14, bar_w, 6)
        pygame.draw.rect(tela, (30, 30, 50), bar_rect, border_radius=3)
        fill_w = int(bar_w * min(1.0, deck_atual / max(1, deck_max)))
        if fill_w > 0:
            pygame.draw.rect(tela, deck_cor, pygame.Rect(bar_rect.x, bar_rect.y, fill_w, 6), border_radius=3)
        yt += 26

        pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

        # ── MERCADO DE MELHORIAS ─────────────────────────────────────────
        ut = self.fM.render(">> MERCADO <<", True, C_ACENTO)
        tela.blit(ut, (x + pw // 2 - ut.get_width() // 2, yt)); yt += 20

        self._slot_y_start = yt

        TIER_COR = {
            "mestre_1": (200, 180, 60), "corrida_1": (200, 180, 60), "perfurador": (200, 180, 60),
            "trabalhador_ef": (200, 180, 60), "mestre_ef": (200, 180, 60), "engenheiro": (200, 180, 60),
            "forjador": (190, 190, 210), "explorador": (190, 190, 210), "guarda_mur": (190, 190, 210),
            "lider_eq": (190, 190, 210), "corredor": (190, 190, 210),
            "super_camp": (220, 100, 100), "escavador_r": (220, 100, 100), "mestre_const": (220, 100, 100),
            "arquiteto": (220, 100, 100),
        }
        SIMB_REC = {"madeira": "[W]", "couro": "[L]", "metal": "[I]"}
        COR_REC  = {"madeira": (100, 200, 90), "couro": (210, 150, 60), "metal": (160, 180, 240)}

        if self.fase == "REPOVOAR_MERCADO":
            from src.cerco_isectum import CARTAS_UPGRADE, CARTAS_UPGRADE_AMARELO, CARTAS_UPGRADE_CINZA, CARTAS_UPGRADE_VERMELHO

            slots_vazios = [s for s in self.estado["slots_upgrade"]
                            if s.get("adquirido") or s.get("carta_id") is None]

            if not hasattr(self, '_slot_ativo_reposicao') or self._slot_ativo_reposicao is None:
                self._slot_ativo_reposicao = slots_vazios[0]["id"] if slots_vazios else None

            if not hasattr(self, '_tab_tier_reposicao'):
                self._tab_tier_reposicao = "todos"

            for slot in self.estado["slots_upgrade"]:
                sid = slot["id"]
                is_vazio = slot.get("adquirido") or slot.get("carta_id") is None

                if not is_vazio:
                    sr = pygame.Rect(x + 6, yt, pw - 12, 24)
                    self._slot_rects_cache[sid] = sr
                    pygame.draw.rect(tela, (12, 35, 12), sr, border_radius=4)
                    pygame.draw.rect(tela, C_VERDE, sr, 1, border_radius=4)
                    nt = self.fMi.render(f"Slot {sid+1}: {slot['nome'][:18]}", True, C_VERDE)
                    tela.blit(nt, (sr.x + 4, sr.centery - nt.get_height() // 2))
                    yt += 28
                else:
                    sr = pygame.Rect(x + 6, yt, pw - 12, 24)
                    self._slot_rects_cache[sid] = sr
                    is_ativo = sid == self._slot_ativo_reposicao
                    bg = (40, 20, 60) if is_ativo else (20, 15, 30)
                    borda = C_ACENTO if is_ativo else C_BORDA
                    pygame.draw.rect(tela, bg, sr, border_radius=4)
                    pygame.draw.rect(tela, borda, sr, 2 if is_ativo else 1, border_radius=4)
                    lbl_v = self.fMi.render(f"Slot {sid+1}: [VAZIO]" + (" << Preenchendo" if is_ativo else " (clique para ativar)"), True, C_ACENTO if is_ativo else C_DIM)
                    tela.blit(lbl_v, (sr.x + 4, sr.centery - lbl_v.get_height() // 2))
                    yt += 28

            yt += 4
            pygame.draw.line(tela, C_BORDA, (x + 6, yt), (x + pw - 6, yt), 1); yt += 6

            if self._slot_ativo_reposicao is not None and slots_vazios:
                tabs = [("todos", "Todas"), ("amarelo", "Fraco"), ("cinza", "Medio"), ("vermelho", "Forte")]
                tab_w = (pw - 12) // len(tabs)
                tab_y = yt
                TIER_CORES = {"todos": (160,160,160), "amarelo":(200,180,60), "cinza":(160,160,200), "vermelho":(220,80,80)}
                for ti, (tab_id, tab_label) in enumerate(tabs):
                    tr = pygame.Rect(x + 6 + ti * tab_w, tab_y, tab_w - 2, 20)
                    is_sel = tab_id == self._tab_tier_reposicao
                    pygame.draw.rect(tela, TIER_CORES[tab_id] if is_sel else (20,20,35), tr, border_radius=3)
                    pygame.draw.rect(tela, TIER_CORES[tab_id], tr, 1, border_radius=3)
                    tl = self.fMi.render(tab_label, True, (0,0,0) if is_sel else TIER_CORES[tab_id])
                    tela.blit(tl, (tr.centerx - tl.get_width()//2, tr.centery - tl.get_height()//2))
                    self._slot_rects_cache[("tab_tier", tab_id)] = tr
                yt += 24

                tier_map = {
                    "todos": CARTAS_UPGRADE,
                    "amarelo": CARTAS_UPGRADE_AMARELO,
                    "cinza": CARTAS_UPGRADE_CINZA,
                    "vermelho": CARTAS_UPGRADE_VERMELHO,
                }
                cartas_filtradas = tier_map.get(self._tab_tier_reposicao, CARTAS_UPGRADE)

                lbl_escolha = self.fMi.render(f"Escolha carta para Slot {self._slot_ativo_reposicao + 1}:", True, C_OURO)
                tela.blit(lbl_escolha, (x + pw//2 - lbl_escolha.get_width()//2, yt)); yt += 16

                for carta in cartas_filtradas:
                    card_h = 56
                    sr = pygame.Rect(x + 6, yt, pw - 12, card_h)
                    self._slot_rects_cache[("reposicao_carta", carta["id"])] = sr

                    if carta in CARTAS_UPGRADE_AMARELO:
                        tier_cor = (180, 160, 50)
                    elif carta in CARTAS_UPGRADE_CINZA:
                        tier_cor = (160, 160, 200)
                    else:
                        tier_cor = (200, 80, 80)

                    mx, my = pygame.mouse.get_pos()
                    hover = sr.collidepoint(mx, my)
                    bg = (35, 28, 50) if hover else (14, 16, 30)
                    pygame.draw.rect(tela, bg, sr, border_radius=6)
                    pygame.draw.rect(tela, tier_cor, sr, 2 if hover else 1, border_radius=6)

                    nome_s = self.fP.render(carta["nome"][:22], True, (240, 240, 255))
                    tela.blit(nome_s, (sr.x + 6, sr.y + 5))

                    stats = []
                    if carta.get("movimento", 0): stats.append(f"+{carta['movimento']}MOV")
                    if carta.get("trabalho",  0): stats.append(f"+{carta['trabalho']}TRAB")
                    if carta.get("escavacao", 0): stats.append(f"+{carta['escavacao']}ESC")
                    if carta.get("efeito_extra") == "draw_1": stats.append("+1carta")
                    stats_s = self.fMi.render("  ".join(stats) if stats else "", True, (140, 240, 160))
                    tela.blit(stats_s, (sr.x + 6, sr.y + 22))

                    custo_partes = []
                    for res, qtd in carta.get("custo", {}).items():
                        simbr = "W" if res == "madeira" else "L" if res == "couro" else "I"
                        custo_partes.append(f"{simbr}:{qtd}")
                    custo_s = self.fMi.render("Custo: " + " ".join(custo_partes) if custo_partes else "", True, C_DIM)
                    tela.blit(custo_s, (sr.x + 6, sr.y + 36))

                    if hover:
                        arr = self.fP.render(">>", True, tier_cor)
                        tela.blit(arr, (sr.right - arr.get_width() - 8, sr.centery - arr.get_height()//2))

                    yt += card_h + 4
            else:
                ok_s = self.fP.render("Todos os slots preenchidos!", True, C_VERDE)
                tela.blit(ok_s, (x + pw//2 - ok_s.get_width()//2, yt)); yt += 24

            yt += 4

        else:
            for slot in self.estado["slots_upgrade"]:
                sid = slot["id"]
                card_h = 80
                sr = pygame.Rect(x + 6, yt, pw - 12, card_h)
                self._slot_rects_cache[sid] = sr

                carta_id = slot.get("carta_id")
                tier_cor = TIER_COR.get(carta_id, C_BORDA)
                is_slot_vazio = slot.get("adquirido") or carta_id is None

                if slot.get("bloqueado"):
                    bg_cor, borda_cor = (40, 10, 10), C_PERIGO
                elif slot.get("adquirido"):
                    bg_cor, borda_cor = (10, 35, 10), C_VERDE
                elif self.idx_slot_upgrade == sid:
                    bg_cor, borda_cor = (28, 18, 55), C_ACENTO
                else:
                    bg_cor, borda_cor = (14, 16, 30), tier_cor if not is_slot_vazio else C_BORDA

                pygame.draw.rect(tela, bg_cor, sr, border_radius=7)
                pygame.draw.rect(tela, borda_cor, sr, 2 if not is_slot_vazio else 1, border_radius=7)

                if is_slot_vazio:
                    lbl_vazio = self.fP.render("[ VAZIO ]", True, C_DIM)
                    tela.blit(lbl_vazio, (sr.centerx - lbl_vazio.get_width()//2, sr.centery - lbl_vazio.get_height()//2))
                else:
                    if slot.get("bloqueado"):
                        prefixo = "[X] "
                        nome_cor = C_PERIGO
                    elif slot.get("adquirido"):
                        prefixo = "[OK] "
                        nome_cor = C_VERDE
                    elif self.idx_slot_upgrade == sid:
                        prefixo = "[>>] "
                        nome_cor = C_ACENTO
                    else:
                        prefixo = ""
                        nome_cor = (240, 240, 255)

                    nome_s = self.fP.render((prefixo + slot['nome'])[:22], True, nome_cor)
                    tela.blit(nome_s, (sr.x + 6, sr.y + 6))

                    from src.cerco_isectum import CARTAS_UPGRADE
                    carta_data = next((c for c in CARTAS_UPGRADE if c["id"] == carta_id), None)
                    if carta_data:
                        stats = []
                        if carta_data.get("movimento",  0): stats.append(f"+{carta_data['movimento']}MOV")
                        if carta_data.get("trabalho",   0): stats.append(f"+{carta_data['trabalho']}TRAB")
                        if carta_data.get("escavacao",  0): stats.append(f"+{carta_data['escavacao']}ESC")
                        if carta_data.get("efeito_extra") == "draw_1": stats.append("+1carta")
                        stats_s = self.fMi.render("  ".join(stats) if stats else "Efeito especial", True, (140, 230, 150))
                        tela.blit(stats_s, (sr.x + 6, sr.y + 22))

                    from ...resolvedor_acoes import CUSTO_ADICIONAL_SLOT
                    custo_base = slot.get("custo", {})
                    custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
                    alocados = slot.get("recursos_alocados", {})

                    if slot.get("adquirido"):
                        status_s = self.fMi.render("[OK] Adquirido - no seu deck!", True, C_VERDE)
                        tela.blit(status_s, (sr.x + 6, sr.y + 38))
                    elif slot.get("bloqueado"):
                        status_s = self.fMi.render("[X] Destruido pela catapulta", True, C_PERIGO)
                        tela.blit(status_s, (sr.x + 6, sr.y + 38))
                    else:
                        custo_total = {}
                        for r_type in ["madeira", "couro", "metal"]:
                            req = custo_base.get(r_type, 0) + custo_adicional.get(r_type, 0)
                            if req > 0:
                                custo_total[r_type] = req

                        n_res = len(custo_total)
                        if n_res > 0:
                            bar_total_w = pw - 24
                            bar_unit_w = bar_total_w // n_res - 4
                            bx = sr.x + 6
                            by = sr.y + 40
                            for r_type, req in custo_total.items():
                                aloc = alocados.get(r_type, 0)
                                completo = aloc >= req
                                cor_res = COR_REC.get(r_type, C_DIM)
                                simbr = SIMB_REC.get(r_type, r_type[0].upper())
                                lbl_r = self.fMi.render(f"{simbr} {aloc}/{req}", True, C_VERDE if completo else cor_res)
                                tela.blit(lbl_r, (bx, by))
                                bar_bg = pygame.Rect(bx, by + 12, bar_unit_w, 5)
                                pygame.draw.rect(tela, (30, 30, 50), bar_bg, border_radius=2)
                                fill = int(bar_unit_w * min(1.0, aloc / max(1, req)))
                                if fill > 0:
                                    pygame.draw.rect(tela, C_VERDE if completo else cor_res,
                                                     pygame.Rect(bx, by + 12, fill, 5), border_radius=2)
                                bx += bar_unit_w + 6

                        esta_completo = all(alocados.get(r, 0) >= req for r, req in custo_total.items()) if custo_total else False
                        if esta_completo and not slot.get("adquirido"):
                            pulso = abs((self.timer % 60) - 30) / 30.0
                            cor_pronto = (int(220 + 35 * pulso), int(180 + 50 * pulso), 0)
                            pronto_s = self.fMi.render(">> PRONTO! Clique para comprar", True, cor_pronto)
                            tela.blit(pronto_s, (sr.x + 6, sr.y + 62))

                mx, my = pygame.mouse.get_pos()
                if sr.collidepoint(mx, my) and not slot.get("adquirido") and not slot.get("bloqueado"):
                    hover_ov = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
                    hover_ov.fill((255, 255, 255, 12))
                    tela.blit(hover_ov, sr.topleft)

                yt += card_h + 6

        if self.fase == "REPOVOAR_MERCADO":
            self.btn_concluir_reposicao_rect = pygame.Rect(x + 6, yt, pw - 12, 34)
            mx, my = pygame.mouse.get_pos()
            hover_btn = self.btn_concluir_reposicao_rect.collidepoint(mx, my)
            pygame.draw.rect(tela, (30, 100, 30) if hover_btn else (20, 70, 20),
                             self.btn_concluir_reposicao_rect, border_radius=5)
            pygame.draw.rect(tela, C_VERDE, self.btn_concluir_reposicao_rect, 1, border_radius=5)
            lbl_done = self.fP.render("[OK] CONCLUIR REPOSICAO", True, (255, 255, 255))
            tela.blit(lbl_done, (self.btn_concluir_reposicao_rect.centerx - lbl_done.get_width() // 2,
                                  self.btn_concluir_reposicao_rect.centery - lbl_done.get_height() // 2))
            yt += 38
        else:
            self.btn_concluir_reposicao_rect = None

        pygame.draw.line(tela, C_BORDA, (x + 6, min(yt, pr.bottom - 60)), (x + pw - 6, min(yt, pr.bottom - 60)), 1)
        yt = min(yt + 6, pr.bottom - 55)
        log_h = ph - (yt - y) - 8
        if log_h >= 20:
            log_bg = pygame.Rect(x + 6, yt, pw - 12, log_h)
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

        tela.set_clip(old_clip)
