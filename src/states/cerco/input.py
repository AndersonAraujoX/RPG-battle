"""
cerco_state_input.py — Mixin de entrada (cliques, teclado, grid) para CercoState
"""
from __future__ import annotations
import pygame
import math
import random

from ...config import ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA
from ...resolvedor_acoes import obter_zona_por_coordenada
from .data import (
    MODO_NENHUM, MODO_MOVER, MODO_TRABALHAR, MODO_ESCAVAR,
    MODO_SUBORNAR, MODO_UPGRADE, MODO_CONVOCAR, MODO_ATACAR, MODO_ATIRAR,
    C_VERDE, C_PERIGO, C_ACENTO, C_OURO, C_HEROI,
)


class CercoStateInputMixin:
    """Mixin responsável pelo tratamento de eventos (mouse, teclado) e
    conversão coordenadas ecrã → grelha isométrica."""

    # ── HANDLE EVENTS ────────────────────────────────────────────────
    def handle_events(self, events):
        self._setup_layout()
        mouse = pygame.mouse.get_pos()
        e = self.estado

        if getattr(self, "dev_menu_aberto", False):
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_F12):
                        self.dev_menu_aberto = False
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    W, H = LARGURA_TELA, ALTURA_TELA
                    pw, ph = 840, 360
                    px = (W - pw) // 2
                    py = (H - ph) // 2
                    x0 = px + 25
                    y0 = py + 70
                    cw, ch = 190, 35
                    gap_x, gap_y = 10, 10
                    from ...cerco_isectum import DADOS_INIMIGOS
                    keys = list(DADOS_INIMIGOS.keys())
                    for idx, key in enumerate(keys):
                        col = idx % 4
                        row = idx // 4
                        bx = x0 + col * (cw + gap_x)
                        by = y0 + row * (ch + gap_y)
                        r = pygame.Rect(bx, by, cw, ch)
                        if r.collidepoint(mouse):
                            self._dev_summon_specific_enemy(key)
                            self.dev_menu_aberto = False
                            return
            return

        for event in events:
            if self.fase == "ESCOLHER_ACAO_CARTA":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.fase = "ACAO_LIVRE"
                    self.idx_carta_sendo_jogada = -1
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if getattr(self, 'btn_andar_rect', None) and self.btn_andar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "andar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_coletar_rect', None) and self.btn_coletar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "coletar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_ambos_rect', None) and self.btn_ambos_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "ambos")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                    elif getattr(self, 'btn_atacar_rect', None) and self.btn_atacar_rect.collidepoint(mouse):
                        self._aplicar_acao_carta(self.idx_carta_sendo_jogada, "atacar")
                        self.fase = "ACAO_LIVRE"
                        self.bloqueio_clique_tick = pygame.time.get_ticks()
                        return
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                self.game.cerco_state = None
                return

            if e.get("derrota") or e.get("vitoria"):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
                    self.game.cerco_state = None
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._on_click(mouse)
                elif event.button == 4:
                    new_z = min(3.0, self.zoom + 0.25)
                    if new_z != self.zoom:
                        self.zoom = new_z
                        self.terrain_iso_cache.clear()
                elif event.button == 5:
                    new_z = max(0.35, self.zoom - 0.25)
                    if new_z != self.zoom:
                        self.zoom = new_z
                        self.terrain_iso_cache.clear()
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    # ── CONVERSÃO ECRÃ → GRELHA ──────────────────────────────────────
    def _screen_to_grid(self, mx: int, my: int) -> tuple | None:
        r = self.mapa_rect
        if not r.collidepoint(mx, my):
            return None
        CX = r.centerx
        CY = r.centery - 5
        TW = max(6, int(24 * self.zoom))
        TH = max(3, int(12 * self.zoom))
        ES = max(2, int(8 * self.zoom))
        theta = self.game.angulo_rotacao
        GRID_MIN, GRID_MAX = 0, 19

        def _classificar(gx, gy):
            if GRID_MIN <= gx <= GRID_MAX and GRID_MIN <= gy <= GRID_MAX:
                z = obter_zona_por_coordenada(gx, gy)
                if z:
                    return z
                if 4 <= gx <= 15 and 4 <= gy <= 15:
                    return "_corredor"
            return None

        cells = []
        for gy in range(GRID_MIN, GRID_MAX + 1):
            for gx in range(GRID_MIN, GRID_MAX + 1):
                zona_key = _classificar(gx, gy)
                if zona_key is None:
                    continue
                el = {
                    "camara_central": 3, "curtume": 2, "carpintaria": 2,
                    "fundicao": 2, "patio": 2,
                    "muralha_norte": 4, "muralha_sul": 4,
                    "muralha_oeste": 4, "muralha_leste": 4,
                    "torre_nw": 6, "torre_ne": 6, "torre_sw": 6, "torre_se": 6,
                    "_corredor": 1,
                }.get(zona_key, 1)
                dx = gx - 9.5
                dy = gy - 9.5
                rx = dx * math.cos(theta) - dy * math.sin(theta)
                ry = dx * math.sin(theta) + dy * math.cos(theta)
                cx = (rx - ry) * (TW // 2) + CX
                cy = (rx + ry) * (TH // 2) - el * ES + CY
                proj_y = (rx + ry) * (TH // 2)
                cells.append((proj_y, gx, gy, cx, cy, el))

        cells.sort(key=lambda x: x[0], reverse=True)
        for _, gx, gy, cx, cy, el in cells:
            thick = el * ES
            ctr_y = cy + thick // 2
            half_h = (TH + thick) // 2
            dx_ = abs(mx - cx) / (TW / 2 + 1e-10)
            dy_ = abs(my - ctr_y) / (half_h + 1e-10)
            if dx_ + dy_ <= 1.0:
                return (gx, gy)
        return None

    # ── TECLADO ───────────────────────────────────────────────────────
    def _on_key(self, key):
        if key == pygame.K_RETURN:
            if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
                self._fim_turno_heroi()
            elif self.fase == "REPOVOAR_MERCADO":
                self._concluir_fim_turno_completo()
        if key == pygame.K_SPACE:
            if self.fase == "FASE_AMEACA" and self.carta_cerco:
                self._resolver_carta_cerco()
        if key == pygame.K_TAB:
            self._alternar_heroi()
        if key in (pygame.K_PLUS, pygame.K_EQUALS):
            new_z = min(3.0, self.zoom + 0.25)
            if new_z != self.zoom:
                self.zoom = new_z
                self.terrain_iso_cache.clear()
        if key == pygame.K_F12:
            self.dev_menu_aberto = not getattr(self, "dev_menu_aberto", False)
        if key == pygame.K_MINUS:
            new_z = max(0.35, self.zoom - 0.25)
            if new_z != self.zoom:
                self.zoom = new_z
                self.terrain_iso_cache.clear()

    # ── CLICK ─────────────────────────────────────────────────────────
    def _on_click(self, mouse):
        if pygame.time.get_ticks() - getattr(self, 'bloqueio_clique_tick', 0) < 150:
            return
        e = self.estado

        if self.btn_voltar.collidepoint(mouse):
            self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            return

        # Tela de fim de jogo — qualquer clique volta ao menu
        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.game.estado_jogo = ESTADO_JOGO_MENU_PRINCIPAL
            return

        if self.fase == "FASE_AMEACA":
            if self.carta_cerco and self.btn_confirmar.collidepoint(mouse):
                self._resolver_carta_cerco()
            return

        if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE", "REPOVOAR_MERCADO"):
            if self.btn_fim_turno.collidepoint(mouse):
                if self.fase == "REPOVOAR_MERCADO":
                    self._concluir_fim_turno_completo()
                else:
                    self._fim_turno_heroi()
                return

            if self.fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
                if getattr(self, "btn_merc_melee", None) and self.btn_merc_melee.collidepoint(mouse):
                    if e.get("tesouro", 0) < 5:
                        self._feedback("Cristais Roxos insuficientes! Requer 5 Cristais.", C_PERIGO)
                    else:
                        self.modo_acao = MODO_CONVOCAR
                        self.tipo_mercenario_selecionado = "melee"
                        self.custo_mercenario_selecionado = 5
                        self._feedback("🛡️ GUARDA (5💎): clique em qualquer célula para posicionar!", (180, 120, 255))
                    return

                if getattr(self, "btn_merc_arqueiro", None) and self.btn_merc_arqueiro.collidepoint(mouse):
                    if e.get("tesouro", 0) < 7:
                        self._feedback("Cristais Roxos insuficientes! Requer 7 Cristais.", C_PERIGO)
                    else:
                        self.modo_acao = MODO_CONVOCAR
                        self.tipo_mercenario_selecionado = "arqueiro"
                        self.custo_mercenario_selecionado = 7
                        self._feedback("🏹 ARQUEIRO (7💎): clique em uma TORRE (NW, NE, SW, SE) para posicionar!", (180, 120, 255))
                    return

                if getattr(self, "btn_merc_minerador", None) and self.btn_merc_minerador.collidepoint(mouse):
                    if e.get("tesouro", 0) < 4:
                        self._feedback("Cristais Roxos insuficientes! Requer 4 Cristais.", C_PERIGO)
                    else:
                        self.modo_acao = MODO_CONVOCAR
                        self.tipo_mercenario_selecionado = "minerador"
                        self.custo_mercenario_selecionado = 4
                        self._feedback("⛏️ MINERADOR (4💎): clique na Região das PEDRAS (Pátio) para posicionar!", (180, 120, 255))
                    return

            for i, rect in enumerate(self.carta_rects):
                if rect.collidepoint(mouse):
                    if i < len(e["mao"]):
                        carta = e["mao"][i]
                        if carta.get("tipo") in ("orc", "invasor"):
                            self._jogar_carta_invasao(i)
                            return
                        # Cartas de upgrade: jogadas normalmente (vão p/ cartas_upgrade_ativas)
                        self.idx_carta_sendo_jogada = i
                        self.fase = "ESCOLHER_ACAO_CARTA"
                        self.fase_aberta_tick = pygame.time.get_ticks()
                    return

            if self.fase == "REPOVOAR_MERCADO":
                if getattr(self, 'btn_concluir_reposicao_rect', None) and self.btn_concluir_reposicao_rect.collidepoint(mouse):
                    self._concluir_fim_turno_completo()
                    self._slot_ativo_reposicao = None
                    self._tab_tier_reposicao = "todos"
                    self._feedback("Fase de Ameaca Iniciada!", C_PERIGO)
                    return

                from ...cerco_isectum import aplicar_delta, CARTAS_UPGRADE

                # 1) Clique numa tab de tier
                for tab_id in ["todos", "amarelo", "cinza", "vermelho"]:
                    tr = self._slot_rects_cache.get(("tab_tier", tab_id))
                    if tr and tr.collidepoint(mouse):
                        self._tab_tier_reposicao = tab_id
                        return

                # 2) Clique num slot vazio → ativar esse slot
                for slot in e["slots_upgrade"]:
                    sid = slot["id"]
                    is_vazio = slot.get("adquirido") or slot.get("carta_id") is None
                    if is_vazio:
                        sr = self._slot_rects_cache.get(sid)
                        if sr and sr.collidepoint(mouse):
                            self._slot_ativo_reposicao = sid
                            self._feedback(f"Slot {sid+1} selecionado. Escolha uma carta.", C_ACENTO)
                            return

                # 3) Clique numa carta da lista → preenche o slot ativo
                slot_ativo_id = getattr(self, '_slot_ativo_reposicao', None)
                if slot_ativo_id is not None:
                    for carta in CARTAS_UPGRADE:
                        cr = self._slot_rects_cache.get(("reposicao_carta", carta["id"]))
                        if cr and cr.collidepoint(mouse):
                            slots = [dict(s) for s in self.estado["slots_upgrade"]]
                            s = slots[slot_ativo_id]
                            s["nome"] = carta["nome"]
                            s["simbolo"] = carta["simbolo"]
                            s["carta_id"] = carta["id"]
                            s["custo"] = dict(carta["custo"])
                            s["descricao"] = carta.get("descricao", "")
                            s["adquirido"] = False
                            s["bloqueado"] = False
                            s["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
                            self.estado = aplicar_delta(self.estado, {"slots_upgrade": slots})
                            self._push("CARTA", f"Slot {slot_ativo_id+1}: [{carta['nome']}] adicionada ao mercado.")
                            self._feedback(f"[{carta['nome']}] adicionada ao Slot {slot_ativo_id+1}!", C_VERDE)

                            # Avança para o próximo slot vazio
                            prox = None
                            for sv in self.estado["slots_upgrade"]:
                                if (sv.get("adquirido") or sv.get("carta_id") is None) and sv["id"] != slot_ativo_id:
                                    prox = sv["id"]
                                    break
                            self._slot_ativo_reposicao = prox
                            return

                return

            for slot in e["slots_upgrade"]:
                sid = slot["id"]
                rect = self._slot_rect(sid)
                if rect and rect.collidepoint(mouse):
                    if self.modo_acao == MODO_TRABALHAR:
                        from ...resolvedor_acoes import validar_alocar_recurso, executar_alocar_recurso
                        ok, recurso, msg = validar_alocar_recurso(e, sid, e["pontos_trabalho"])
                        if ok:
                            delta, logs = executar_alocar_recurso(e, sid, recurso)
                            self.estado = aplicar_delta(e, delta)
                            for t, m in logs: self._push(t, m)
                            self._feedback(f"Alocou 1x {recurso.upper()} sobre [{slot['nome']}]!", C_VERDE)
                            if self.estado["pontos_trabalho"] <= 0:
                                self.modo_acao = MODO_NENHUM
                        else:
                            self._feedback(msg, C_PERIGO)
                    else:
                        if slot.get("adquirido"):
                            self._feedback("Esta melhoria já foi adquirida!", C_PERIGO)
                            return
                        if slot.get("bloqueado"):
                            self._feedback("Esta melhoria foi destruída pela catapulta!", C_PERIGO)
                            return

                        dep = dict(e.get("recursos_depositados", {"madeira": 0, "couro": 0, "metal": 0}))
                        from ...resolvedor_acoes import CUSTO_ADICIONAL_SLOT
                        custo_base = slot.get("custo", {})
                        custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
                        alocados = dict(slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0}))

                        transferido_algum = False
                        for r_type in ["madeira", "couro", "metal"]:
                            total_req = custo_base.get(r_type, 0) + custo_adicional.get(r_type, 0)
                            alocado_atual = alocados.get(r_type, 0)
                            falta = total_req - alocado_atual
                            if falta > 0 and dep.get(r_type, 0) > 0:
                                transferir = min(falta, dep.get(r_type, 0))
                                dep[r_type] -= transferir
                                alocados[r_type] += transferir
                                transferido_algum = True
                                self._push("HEROI", f"Alocado {transferir}x {r_type.upper()} no upgrade [{slot['nome']}].")

                        if transferido_algum:
                            from ...cerco_isectum import aplicar_delta
                            slots = [dict(s) for s in e["slots_upgrade"]]
                            slots[sid]["recursos_alocados"] = alocados
                            self.estado = aplicar_delta(e, {
                                "recursos_depositados": dep,
                                "slots_upgrade": slots
                            })
                            e = self.estado
                            slot = e["slots_upgrade"][sid]
                            self.map_backbuffer_sujo = True
                            self._feedback("Recursos alocados do depósito!", C_VERDE)

                        custo_base = slot.get("custo", {})
                        custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
                        custo_total = {}
                        for r in ["madeira", "couro", "metal"]:
                            qtd = custo_base.get(r, 0) + custo_adicional.get(r, 0)
                            if qtd > 0:
                                custo_total[r] = qtd

                        alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
                        faltam = {}
                        for r, qtd in custo_total.items():
                            if alocados.get(r, 0) < qtd:
                                faltam[r] = qtd - alocados.get(r, 0)

                        if not faltam:
                            # Custo pago! Adiciona o upgrade direto ao deck — sem precisar queimar carta
                            self.idx_slot_upgrade = sid
                            self._adquirir_upgrade_direto(sid)
                        else:
                            recs_txt = ", ".join(f"{q}x {r.upper()}" for r, q in faltam.items())
                            self._feedback(f"Falta alocar: {recs_txt}. Colete mais recursos!", C_PERIGO)
                    return

            from ...cerco_isectum import aplicar_delta
            cell = self._screen_to_grid(mouse[0], mouse[1])
            if cell:
                self._on_cell_click(cell[0], cell[1])
                return

        if self.modo_acao == MODO_NENHUM and not self.walk_anim:
            cell = self._screen_to_grid(mouse[0], mouse[1])
            if cell:
                self._on_cell_click(cell[0], cell[1])

    def _selecionar_modo(self, modo):
        self.modo_acao = modo
        self.idx_slot_upgrade = -1
        self.idx_carta_queimar = -1
        msgs = {
            MODO_MOVER:     "Modo MOVER: clique em uma zona do mapa [M]",
            MODO_TRABALHAR: "Modo TRABALHAR: clique em uma Carta no Mercado para alocar 1x [Recurso] nela!",
            MODO_ESCAVAR:   "Modo ESCAVAR: confirme no Pátio [G]",
            MODO_SUBORNAR:  "Modo SUBORNAR: escolha recurso no painel",
            MODO_UPGRADE:   "Modo UPGRADE: Custo pago! O upgrade será adicionado ao seu deck.",
            MODO_CONVOCAR:  "Modo CONVOCAR: clique em qualquer célula vazia para colocar um aliado!",
            MODO_ATACAR:    "[A] ATACAR: clique na zona com invasores para combate melee (2D6 customizados)!",
            MODO_ATIRAR:    "[F] ATIRAR: de uma Torre, clique no alvo externo (Balestra 2D6)!",
        }
        self._feedback(msgs.get(modo, ""), C_ACENTO)

    # ── CLICK EM CÉLULA ──────────────────────────────────────────────
    def _on_cell_click(self, cx: int, cy: int):
        e = self.estado
        if self.walk_anim:
            return

        char = self.motor.tabuleiro.grid[cy][cx]
        if self.modo_acao == MODO_NENHUM and char and getattr(char, "_is_infiltrador", False):
            self.modo_acao = MODO_SUBORNAR
            self.alvo_negociacao = char
            self._feedback("Negociar: escolha Recurso no rodapé ou use Escavação para limpar rochas!", C_OURO)
            return

        if self.modo_acao == MODO_NENHUM:
            if char:
                if getattr(char, "_is_mercenario", False) or char in self.herois:
                    self._feedback(f"Célula já ocupada por [{char.nome}]!", C_ACENTO)
                    return

            from ...resolvedor_acoes import custo_minimo_grade, obter_zona_por_coordenada
            from ...cerco_isectum import aplicar_delta
            from_pos = (e.get("heroi_x", 9), e.get("heroi_y", 9))
            if from_pos == (cx, cy):
                return
            custo = custo_minimo_grade(self.motor, from_pos, (cx, cy))
            if custo is None:
                self._feedback("Destino inaccessivel!", C_PERIGO)
                return
            def _finalize_free():
                self.motor.tabuleiro.mover_personagem(self.heroi_atual, cx, cy)
                delta = {
                    "heroi_x": cx,
                    "heroi_y": cy,
                    "pos_heroi": obter_zona_por_coordenada(cx, cy) or "camara_central",
                }
                self.estado = aplicar_delta(e, delta)
                self._push("HEROI", f"Moveu para ({cx}, {cy})")
                self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)
            self._start_walk(self.heroi_atual, from_pos, (cx, cy), on_done=_finalize_free)

        elif self.modo_acao == MODO_MOVER:
            from ...resolvedor_acoes import validar_mover, executar_mover, obter_celulas_alcancaveis, obter_zona_por_coordenada
            from ...cerco_isectum import aplicar_delta
            ok, custo, msg = validar_mover(e, cx, cy, e["pontos_movimento"], self.motor)
            if ok:
                from_pos = (e.get("heroi_x", 9), e.get("heroi_y", 9))
                def _finalize():
                    self.motor.tabuleiro.mover_personagem(self.heroi_atual, cx, cy)
                    delta, logs = executar_mover(e, cx, cy, custo)
                    self.estado = aplicar_delta(e, delta)
                    e2 = self.estado
                    for t, m in logs: self._push(t, m)
                    self.alcancaveis = obter_celulas_alcancaveis(
                        self.motor, (e2.get("heroi_x", 9), e2.get("heroi_y", 9)),
                        e2["pontos_movimento"]
                    )
                    self._feedback(f"Moveu para ({cx}, {cy})", C_VERDE)
                    self.modo_acao = MODO_NENHUM
                    self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)
                self._start_walk(self.heroi_atual, from_pos, (cx, cy), on_done=_finalize)
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_TRABALHAR:
            self._feedback("Clique em uma das cartas do Mercado de Melhorias para alocar o recurso!", C_OURO)

        elif self.modo_acao == MODO_ESCAVAR:
            from ...resolvedor_acoes import validar_escavar, executar_escavar
            from ...cerco_isectum import aplicar_delta
            ok, qtd, msg = validar_escavar(e, e["pontos_escavacao"])
            if ok:
                delta, logs = executar_escavar(e, qtd)
                self.estado = aplicar_delta(e, delta)
                for t, m in logs: self._push(t, m)
                self._feedback(f"Escavou {qtd}x pedregulho!", C_VERDE)
                self.modo_acao = MODO_NENHUM
                if self.estado.get("vitoria"):
                    self.fase = "FIM"
            else:
                self._feedback(msg, C_PERIGO)

        elif self.modo_acao == MODO_CONVOCAR:
            tipo_m = getattr(self, 'tipo_mercenario_selecionado', 'melee')
            custo_m = getattr(self, 'custo_mercenario_selecionado', 5)

            if self.estado.get("tesouro", 0) < custo_m:
                self._feedback("Cristais Roxos insuficientes!", C_PERIGO)
                self.modo_acao = MODO_NENHUM
                return

            from ...resolvedor_acoes import obter_zona_por_coordenada
            zona_clicada = obter_zona_por_coordenada(cx, cy)
            terrain_type = self.motor.tabuleiro.get_terrain_em(cx, cy)

            if tipo_m == "minerador":
                if zona_clicada != "patio" and terrain_type not in ("patio", "rocha", "barril", "fogo"):
                    self._feedback("⛏️ Mineradores só podem ser posicionados na Região das Pedras (Pátio)!", C_PERIGO)
                    return
            elif tipo_m == "arqueiro":
                if not (zona_clicada and zona_clicada.startswith("torre")):
                    self._feedback("🏹 Arqueiros só podem ser posicionados nas Torres de Vigilância (NW, NE, SW, SE)!", C_PERIGO)
                    return

            from src.personagens.mercenarios import MercenarioMelee, MercenarioArqueiro, MercenarioMinerador
            mapa_merc = {
                "melee": MercenarioMelee,
                "arqueiro": MercenarioArqueiro,
                "minerador": MercenarioMinerador,
            }
            classe_m = mapa_merc.get(tipo_m, MercenarioMelee)
            novo_aliado = classe_m(nivel=3)
            sucesso = self.motor.tabuleiro.adicionar_personagem(novo_aliado, cx, cy)
            if sucesso:
                self.motor.time_a.append(novo_aliado)
                self.motor.combatentes.append(novo_aliado)
                novos_cristais = max(0, self.estado.get("tesouro", 0) - custo_m)
                from ...cerco_isectum import aplicar_delta
                self.estado = aplicar_delta(self.estado, {"tesouro": novos_cristais})
                self._push("HEROI", f"💎 Contratou [{novo_aliado.nome}] por {custo_m} Cristais Roxos em ({cx}, {cy})!")
                self._feedback(f"[{novo_aliado.nome}] Contratado!", C_VERDE)
                self.modo_acao = MODO_NENHUM
                self.map_backbuffer_sujo = True
            else:
                self._feedback("Célula ocupada ou inválida (parede). Escolha outra!", C_PERIGO)

        elif self.modo_acao == MODO_ATACAR:
            from ...resolvedor_acoes import obter_zona_por_coordenada
            from ...cerco_isectum import aplicar_delta
            from ...juiz_combate import resolver_melee
            zona_alvo = obter_zona_por_coordenada(cx, cy)
            if not zona_alvo:
                self._feedback("Clique em uma zona válida do mapa!", C_PERIGO)
                return
            zona_heroi = self.estado.get("pos_heroi")
            if zona_heroi != zona_alvo:
                self._feedback("Herói precisa estar na mesma zona do inimigo para combate corpo-a-corpo!", C_PERIGO)
                return
            invasores_na_zona = self.estado["invasores"].get(zona_alvo, 0)
            infiltradores = self.estado.get("infiltradores", 0)
            if invasores_na_zona == 0 and self.estado.get("brutamontes", 0) == 0 and (zona_alvo != "patio" or infiltradores == 0):
                self._feedback(f"Sem inimigos em [{zona_alvo}] para atacar!", C_PERIGO)
                return
            aliados_na_zona = 0
            for p in list(self.motor.combatentes):
                if getattr(p, "time", "B") == "A" and p.hp_atual > 0:
                    if obter_zona_por_coordenada(p.pos_x, p.pos_y) == zona_alvo:
                        aliados_na_zona += 1
            resultado = resolver_melee(self.estado, zona_alvo, num_dados=2, num_aliados_zona=max(1, aliados_na_zona))
            self.estado = aplicar_delta(self.estado, resultado["delta"])
            if self.estado.get("desafio_final_ativo") and self.estado.get("infiltradores", 0) == 0:
                self.estado = aplicar_delta(self.estado, {
                    "vitoria": True,
                    "msg_vitoria": "Desafio Final concluído! Os Goblins de Elite foram derrotados e os anões escaparam!"
                })
                self._push("VITORIA", "Desafio Final concluído! Vitória!")
                self.fase = "FIM"
            for t, m in resultado["logs"]:
                self._push(t, m)
            if resultado["rolagem"]:
                faces = resultado["rolagem"]["faces"]
                imp   = resultado["rolagem"]["impactos"]
                dano  = imp // 2
                self._feedback(f"Melee D6={faces} -> {imp} imp -> {dano} dano!", C_VERDE)
            self.modo_acao = MODO_NENHUM

        elif self.modo_acao == MODO_ATIRAR:
            from ...resolvedor_acoes import obter_zona_por_coordenada
            from ...cerco_isectum import aplicar_delta
            from ...juiz_combate import resolver_distancia, validar_pode_atacar_distancia
            hx = self.estado.get("heroi_x", 9)
            hy = self.estado.get("heroi_y", 9)
            zona_defensor = obter_zona_por_coordenada(hx, hy)
            zona_alvo_tiro = obter_zona_por_coordenada(cx, cy)
            if not zona_defensor or not zona_alvo_tiro:
                self._feedback("Posição inválida para Balestra!", C_PERIGO)
                return
            ok, msg_val = validar_pode_atacar_distancia(zona_defensor, zona_alvo_tiro)
            if not ok:
                self._feedback(msg_val, C_PERIGO)
                return
            resultado = resolver_distancia(self.estado, zona_defensor, zona_alvo_tiro, num_dados=2)
            self.estado = aplicar_delta(self.estado, resultado["delta"])
            for t, m in resultado["logs"]:
                self._push(t, m)
            if resultado["rolagem"]:
                faces = resultado["rolagem"]["faces"]
                dis   = resultado["rolagem"]["disparos"]
                self._feedback(f"Balestra D6={faces} -> {dis} disparos -> {dis} dano!", C_HEROI)
            self.modo_acao = MODO_NENHUM
