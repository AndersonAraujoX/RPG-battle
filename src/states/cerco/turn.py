"""
cerco_state_turn.py — Mixin de fluxo de turno (fases, derrota, processamento automático)
para CercoState
"""
from __future__ import annotations

from ...resolvedor_acoes import obter_zona_por_coordenada, NOME_RECURSO
from ...juiz_combate import resetar_dano_turno_brutamonte
from .data import (
    MODO_NENHUM,
    C_VERDE, C_PERIGO, C_OURO, C_HEROI,
)


class CercoStateTurnMixin:
    """Mixin responsável pelo fluxo de turno: fim de turno, fases,
    verificação de derrota, processamento automático de ações."""

    # ── FIM DE TURNO DO HERÓI ────────────────────────────────────────
    def _fim_turno_heroi(self):
        if self.estado["mao"]:
            self._feedback("Use todas as cartas da mao para encerrar o turno!", C_PERIGO)
            try:
                self.game.play_sound('invalid_action')
            except:
                pass
            return

        from ...cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {
            "pontos_movimento": 0,
            "pontos_trabalho":  0,
            "pontos_escavacao": 0,
        })
        reset_brute = resetar_dano_turno_brutamonte(self.estado)
        if reset_brute:
            self.estado = aplicar_delta(self.estado, reset_brute)

        self._salvar_status_heroi(self.heroi_atual.nome)

        jogaram = list(self.estado.get("herois_jogaram", []))
        if self.heroi_atual.nome not in jogaram:
            jogaram.append(self.heroi_atual.nome)
        self.estado = aplicar_delta(self.estado, {"herois_jogaram": jogaram})

        proximo_heroi = None
        for h in self.herois:
            if h.nome not in jogaram:
                proximo_heroi = h
                break

        if proximo_heroi:
            idx_novo = self.herois.index(proximo_heroi)
            self.heroi_atual_idx = idx_novo
            self._carregar_status_heroi(proximo_heroi.nome)
            self._comprar_mao()

            tab = self.motor.tabuleiro
            for gy in range(tab.altura):
                for gx in range(tab.largura):
                    if tab.grid[gy][gx] is proximo_heroi:
                        self.estado = aplicar_delta(self.estado, {
                            "heroi_x": gx,
                            "heroi_y": gy,
                            "pos_heroi": obter_zona_por_coordenada(gx, gy) or "camara_central",
                        })
                        break

            nome_exibido = "?????" if proximo_heroi.nome == "Aquele" else proximo_heroi.nome
            self._feedback(f"Turno de {nome_exibido}! Use suas cartas.", C_HEROI)
            self._push("SISTEMA", f"Início do turno do herói: {nome_exibido}")
        else:
            self.estado = aplicar_delta(self.estado, {"herois_jogaram": []})

            pos_heroi = self.estado.get("pos_heroi", "camara_central")
            tem_slot_vazio = any(s.get("adquirido") or s.get("carta_id") is None for s in self.estado["slots_upgrade"])

            if pos_heroi == "camara_central" and tem_slot_vazio:
                self.fase = "REPOVOAR_MERCADO"
                self._feedback("Reposicao: Escolha uma carta para cada slot vazio!", C_OURO)
                self._push("SISTEMA", "Base Central: Escolha cartas para repovoar os slots vazios do mercado.")
                self.alcancaveis = {}
                self.modo_acao = MODO_NENHUM
                # Reset de estado de seleção de reposição
                self._slot_ativo_reposicao = None
                self._tab_tier_reposicao = "todos"
            else:
                self._concluir_fim_turno_completo()

    def _concluir_fim_turno_completo(self):
        from ...cerco_isectum import aplicar_delta
        import random as _rnd

        upgrades_ativas = list(self.estado.get("cartas_upgrade_ativas", []))

        # Reset e reembaralhamento para todos os heróis salvos em herois_status
        for nome_h, st in self.estado.get("herois_status", {}).items():
            todas = list(st.get("descarte", [])) + list(st.get("mao", [])) + list(st.get("deck_heroi", [])) + list(st.get("excluidas_ciclo", []))
            for up in upgrades_ativas:
                if not any(c.get("id") == up.get("id") for c in todas):
                    todas.append(dict(up))
            _rnd.shuffle(todas)
            tam_m = 3
            st["mao"] = todas[:tam_m]
            st["deck_heroi"] = todas[tam_m:]
            st["descarte"] = []
            st["excluidas_ciclo"] = []
            st["pontos_movimento"] = 0
            st["pontos_trabalho"] = 0
            st["pontos_escavacao"] = 0

        # Reset e reembaralhamento para o estado do herói ativo
        todas_ativo = list(self.estado.get("descarte", [])) + list(self.estado.get("mao", [])) + list(self.estado.get("deck_heroi", [])) + list(self.estado.get("excluidas_ciclo", []))
        for up in upgrades_ativas:
            if not any(c.get("id") == up.get("id") for c in todas_ativo):
                todas_ativo.append(dict(up))
        _rnd.shuffle(todas_ativo)
        tam_m_ativo = 3

        # Recicla / repovoa slots do mercado que estiverem vazios [ VAZIO ]
        from ...cerco_isectum import CARTAS_UPGRADE
        slots = [dict(s) for s in self.estado.get("slots_upgrade", [])]
        mudou_slots = False
        cartas_no_mercado_ids = {s.get("carta_id") for s in slots if s.get("carta_id") and not s.get("adquirido")}
        for i, s in enumerate(slots):
            if s.get("adquirido") or not s.get("carta_id"):
                candidatas = [c for c in CARTAS_UPGRADE if c["id"] not in cartas_no_mercado_ids]
                cand = _rnd.choice(candidatas if candidatas else CARTAS_UPGRADE)
                slots[i] = {
                    "id": i,
                    "nome": cand["nome"],
                    "simbolo": cand.get("simbolo", "⭐"),
                    "carta_id": cand["id"],
                    "custo": dict(cand["custo"]),
                    "descricao": cand.get("descricao", ""),
                    "adquirido": False,
                    "bloqueado": False,
                    "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}
                }
                cartas_no_mercado_ids.add(cand["id"])
                mudou_slots = True

        delta_atual = {
            "mao": todas_ativo[:tam_m_ativo],
            "deck_heroi": todas_ativo[tam_m_ativo:],
            "descarte": [],
            "excluidas_ciclo": [],
            "pontos_movimento": 0,
            "pontos_trabalho": 0,
            "pontos_escavacao": 0,
        }
        if mudou_slots:
            delta_atual["slots_upgrade"] = slots

        self.estado = aplicar_delta(self.estado, delta_atual)
        self.alcancaveis = {}
        self.modo_acao   = MODO_NENHUM

        # Verifica se há o Filho do Imperador como IA inimiga ativa
        ia_cmd = getattr(self, 'ia_comandante', None)
        if ia_cmd is not None:
            # Antes da Fase de Ameaça, o Filho do Imperador age como inimigo
            self.fase = "TURNO_FILHO_IMPERADOR"
            self.map_backbuffer_sujo = True
            self._push("SISTEMA", "👑 Vez do Filho do Imperador! A IA invasora age...")
            self._feedback("👑 FILHO DO IMPERADOR — Preparando invasão!", (220, 60, 30))
        else:
            self._iniciar_fase_ameaca()


    # ── PROCESSAMENTO AUTOMÁTICO ─────────────────────────────────────
    def _processar_acoes_automaticas(self, mostrar_erro_se_falhar=False):
        from ...resolvedor_acoes import validar_trabalhar, executar_trabalhar, validar_escavar, executar_escavar
        from ...cerco_isectum import aplicar_delta

        e = self.estado

        if e.get("pontos_trabalho", 0) > 0:
            ok, recurso, msg = validar_trabalhar(e, e["pontos_trabalho"])
            if ok:
                pts_gastos = e["pontos_trabalho"]
                delta, logs = executar_trabalhar(e, recurso, pts_gastos)
                self.estado = aplicar_delta(e, delta)
                e = self.estado
                for t, m in logs:
                    self._push(t, m)
                self._feedback(f"Trabalhou! +{pts_gastos}x {NOME_RECURSO[recurso]} produzido.", C_VERDE)
                self.modo_acao = MODO_NENHUM
            elif mostrar_erro_se_falhar:
                self._feedback(msg, C_PERIGO)

        if e.get("pontos_escavacao", 0) > 0:
            ok, qtd, msg = validar_escavar(e, e["pontos_escavacao"])
            if ok:
                delta, logs = executar_escavar(e, qtd)
                self.estado = aplicar_delta(e, delta)
                e = self.estado
                for t, m in logs:
                    self._push(t, m)
                self._feedback(f"Escavou! -{qtd} pedregulhos.", C_VERDE)
                self.modo_acao = MODO_NENHUM
                if self.estado.get("desafio_final_ativo") and self.estado.get("infiltradores", 0) == 0:
                    self.estado = aplicar_delta(self.estado, {
                        "vitoria": True,
                        "msg_vitoria": "Desafio Final concluído! As Formigas Infiltradoras de Elite foram derrotadas e os anões escaparam!"
                    })
                    self._push("VITORIA", "Desafio Final concluído! Vitória!")
                    self.fase = "FIM"
            elif mostrar_erro_se_falhar:
                self._feedback(msg, C_PERIGO)

        self._verificar_derrota_imediata()

    # ── VERIFICAÇÃO DE FIM DE JOGO ────────────────────────────────────
    def _verificar_derrota_imediata(self):
        """O sistema de derrota foi desativado a pedido do usuário.

        Eventos de Cerco (catapulta, perda de cristais, brutamontes) continuam
        aplicando seus efeitos normalmente, mas NUNCA interrompem o jogo com
        uma tela de DERROTA. O combate continua até a vitória!
        """
        return False

    # ── SPAWN DO MÃO REI ─────────────────────────────────────────────
    def _spawn_mao_rei(self):
        """Spawna o boss final A Mão Rei após o deck de ameaças ser esgotado."""
        from ...cerco_isectum import aplicar_delta
        from ...personagens.mao_rei import MaoRei
        from ...resolvedor_acoes import ZONAS_GRID

        self.estado = aplicar_delta(self.estado, {"mao_rei_spawnou": True})

        tab = self.motor.tabuleiro
        # Tenta posicionar em campo_norte primeiro, depois em outras regiões
        zonas_tentativa = ["campo_norte", "campo_sul", "campo_leste", "campo_oeste",
                           "muralha_norte", "muralha_sul"]
        cx, cy = 0, 0
        for zona_spawn in zonas_tentativa:
            if zona_spawn not in ZONAS_GRID:
                continue
            x1, y1, x2, y2 = ZONAS_GRID[zona_spawn]
            x1c = max(0, min(19, x1))
            x2c = max(0, min(19, x2))
            y1c = max(0, min(19, y1))
            y2c = max(0, min(19, y2))
            candidatas = [
                (gx, gy)
                for gy in range(y1c, y2c + 1)
                for gx in range(x1c, x2c + 1)
                if tab.get_terrain_em(gx, gy) != "parede" and tab.grid[gy][gx] is None
            ]
            if candidatas:
                import random as _rnd
                cx, cy = _rnd.choice(candidatas)
                break

        boss = MaoRei("👁️ A Mão Rei", "B", nivel=18)
        boss._zona_campo = None
        boss._is_boss = True

        sucesso = tab.adicionar_personagem(boss, cx, cy)
        if sucesso:
            self.motor.combatentes.append(boss)
            if not hasattr(self.motor, 'time_b'):
                self.motor.time_b = []
            self.motor.time_b.append(boss)
            self.map_backbuffer_sujo = True

        self._push("CERCO",
            "⚠️ As cartas de ameaça esgotaram... mas a guerra não acabou!")
        self._push("BOSS",
            "👁️ A MÃO REI surge do horizonte! O emissário pessoal do Imperador Insectum "
            "avança sobre a fortaleza! Derrotem-no para vencer!")
        self._feedback("👁️ A MÃO REI apareceu! Derrotem o boss para vencer!", (220, 0, 220))

    # ── VERIFICAÇÃO DE VITÓRIA POR DERROTA DO BOSS ────────────────────
    def _verificar_vitoria_boss(self):
        """Verifica se o Mão Rei foi derrotado — encerra com vitória."""
        from ...cerco_isectum import aplicar_delta
        if not self.estado.get("mao_rei_spawnou"):
            return
        if self.estado.get("vitoria") or self.estado.get("derrota"):
            return

        mao_rei_vivo = any(
            getattr(p, "_is_boss", False) and p.hp_atual > 0
            for p in self.motor.combatentes
        )
        mao_rei_existe = any(
            getattr(p, "_is_boss", False)
            for p in self.motor.combatentes
        )

        if mao_rei_existe and not mao_rei_vivo:
            self.estado = aplicar_delta(self.estado, {
                "vitoria": True,
                "msg_vitoria": "A Mão Rei foi derrotada! O Imperador Insectum recua — a fortaleza resistiu! VITÓRIA TOTAL!"
            })
            self._push("VITORIA",
                "👁️ A Mão Rei foi derrotada! A fortaleza resistiu ao Imperador Insectum! VITÓRIA!")
            self._feedback("🏆 VITÓRIA TOTAL! A Mão Rei foi derrotada!", (255, 215, 0))
            self.fase = "FIM"

    # ── FASE AMEAÇA ───────────────────────────────────────────────────
    def _iniciar_fase_ameaca(self):
        if self._verificar_derrota_imediata():
            return
        self._verificar_vitoria_boss()
        if self.estado.get("vitoria"):
            self.fase = "FIM"
            return
        # Se o deck de ameaças acabou, invoca o Boss Final: A Mão Rei!
        if not self.deck:
            if not self.estado.get("mao_rei_spawnou"):
                self._spawn_mao_rei()
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()
            return
        self.fase = "FASE_AMEACA"
        self.carta_cerco = self.deck.pop()
        self._push("CARTA", f"[N{self.carta_cerco['nivel']}] {self.carta_cerco['simbolo']} "
                            f"{self.carta_cerco['titulo']}")
        self._narrativa(self.carta_cerco["tipo"])

    def _resolver_carta_cerco(self):
        from ...cerco_isectum import avancar_ciclo_armas, processar_carta, aplicar_delta
        e = self.estado
        d, ls = avancar_ciclo_armas(e)
        if d:
            self.estado = aplicar_delta(e, d)
            e = self.estado
        for t, m in ls: self._push(t, m)

        delta, logs = processar_carta(self.estado, self.carta_cerco)
        self.estado = aplicar_delta(self.estado, delta)
        for t, m in logs: self._push(t, m)

        self.carta_cerco = None
        self.estado = aplicar_delta(self.estado, {"rodada": self.estado["rodada"] + 1})

        # Processa turnos automáticos dos Mercenários contratados
        self._processar_turnos_mercenarios()

        if self._verificar_derrota_imediata():
            return

        self._verificar_vitoria_boss()

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.fase = "FIM"
        else:
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()

    def _processar_turnos_mercenarios(self):
        """Processa as ações automáticas de todos os mercenários contratados no time A."""
        from ...cerco_isectum import aplicar_delta
        tab = self.motor.tabuleiro

        mercenarios = [
            p for p in list(self.motor.combatentes)
            if getattr(p, "time", "A") == "A" and getattr(p, "_is_mercenario", False) and p.hp_atual > 0
        ]

        if not mercenarios:
            return

        cristais_minerados = 0
        teve_movimento = False

        for m in mercenarios:
            tipo = getattr(m, "tipo_mercenario", "melee")

            # --- MINERADOR ---
            if tipo == "minerador":
                pedras = self.estado.get("pedregulhos", 0)
                if pedras > 0:
                    cristais_minerados += 2
                    self.estado = aplicar_delta(self.estado, {"pedregulhos": pedras - 1})
                    self._push("HEROI", f"⛏️ {m.nome} minerou as rochas e extraiu +2 Cristais Roxos!")
                else:
                    self._push("HEROI", f"⛏️ {m.nome} não encontrou mais pedregulhos para minerar.")

            # --- ARQUEIRO (Ataque à Distância da Torre / Perímetro) ---
            elif tipo == "arqueiro":
                inimigos = [
                    p for p in list(self.motor.combatentes)
                    if getattr(p, "time", "A") == "B" and p.hp_atual > 0
                ]
                if inimigos:
                    inimigos.sort(key=lambda ini: abs(ini.pos_x - m.pos_x) + abs(ini.pos_y - m.pos_y))
                    alvo = inimigos[0]
                    dist = abs(alvo.pos_x - m.pos_x) + abs(alvo.pos_y - m.pos_y)

                    # Arqueiros nas torres possuem alcance elevado de 18 células
                    if dist <= 18:
                        import random as _rnd
                        d20 = _rnd.randint(1, 20)
                        total_ataque = d20 + getattr(m, 'bonus_ataque', 5)
                        if total_ataque >= alvo.ac:
                            num_d, faces_d = getattr(m, 'dado_dano', (1, 10))
                            b_dano = getattr(m, 'bonus_dano', 4)
                            dano = sum(_rnd.randint(1, faces_d) for _ in range(num_d)) + b_dano
                            alvo.hp_atual -= dano
                            self._push("HEROI", f"🏹 Arqueiro Mercenário disparou em {alvo.nome}! Dano: {dano} (HP: {max(0, alvo.hp_atual)}/{alvo.hp_max})")
                            if alvo.hp_atual <= 0:
                                if 0 <= alvo.pos_y < len(tab.grid) and 0 <= alvo.pos_x < len(tab.grid[0]):
                                    if tab.grid[alvo.pos_y][alvo.pos_x] is alvo:
                                        tab.grid[alvo.pos_y][alvo.pos_x] = None
                                if alvo in self.motor.combatentes:
                                    self.motor.combatentes.remove(alvo)
                                if hasattr(self.motor, 'time_b') and alvo in self.motor.time_b:
                                    self.motor.time_b.remove(alvo)
                                self._push("HEROI", f"💀 Arqueiro ABATEU {alvo.nome}!")
                        else:
                            self._push("HEROI", f"🏹 Arqueiro disparou em {alvo.nome}, mas ERROU! (D20: {d20}+5 vs AC {alvo.ac})")
                else:
                    # Sem inimigos físicos, dispara flechas nas zonas com insetos invasores
                    invasores = dict(self.estado.get("invasores", {}))
                    zonas_com_invasores = [z for z, count in invasores.items() if count > 0]
                    if zonas_com_invasores:
                        zona_alvo = max(zonas_com_invasores, key=lambda z: invasores[z])
                        invasores[zona_alvo] -= 1
                        self.estado = aplicar_delta(self.estado, {"invasores": invasores})
                        from ...cerco_isectum import NOMES_ZONA
                        nome_z = NOMES_ZONA.get(zona_alvo, zona_alvo)
                        self._push("HEROI", f"🏹 Arqueiro da Torre disparou flechas em [{nome_z}] e eliminou 1x Inseto!")
                        teve_movimento = True

            # --- GUARDA MELEE (Combate Defensivo Próximo) ---
            elif tipo == "melee":
                inimigos = [
                    p for p in list(self.motor.combatentes)
                    if getattr(p, "time", "A") == "B" and p.hp_atual > 0
                ]
                if inimigos:
                    inimigos.sort(key=lambda ini: abs(ini.pos_x - m.pos_x) + abs(ini.pos_y - m.pos_y))
                    alvo = inimigos[0]
                    dist = abs(alvo.pos_x - m.pos_x) + abs(alvo.pos_y - m.pos_y)

                    if dist <= 1:
                        import random as _rnd
                        d20 = _rnd.randint(1, 20)
                        total_ataque = d20 + getattr(m, 'bonus_ataque', 4)
                        if total_ataque >= alvo.ac:
                            num_d, faces_d = getattr(m, 'dado_dano', (2, 6))
                            b_dano = getattr(m, 'bonus_dano', 3)
                            dano = sum(_rnd.randint(1, faces_d) for _ in range(num_d)) + b_dano
                            alvo.hp_atual -= dano
                            self._push("HEROI", f"⚔️ Guarda Mercenário atacou {alvo.nome}! Dano: {dano} (HP: {max(0, alvo.hp_atual)}/{alvo.hp_max})")
                            if alvo.hp_atual <= 0:
                                if 0 <= alvo.pos_y < len(tab.grid) and 0 <= alvo.pos_x < len(tab.grid[0]):
                                    if tab.grid[alvo.pos_y][alvo.pos_x] is alvo:
                                        tab.grid[alvo.pos_y][alvo.pos_x] = None
                                if alvo in self.motor.combatentes:
                                    self.motor.combatentes.remove(alvo)
                                if hasattr(self.motor, 'time_b') and alvo in self.motor.time_b:
                                    self.motor.time_b.remove(alvo)
                                self._push("HEROI", f"💀 Guarda ABATEU {alvo.nome}!")
                        else:
                            self._push("HEROI", f"⚔️ Guarda atacou {alvo.nome}, mas ERROU! (D20: {d20}+4 vs AC {alvo.ac})")
                    elif dist <= 3:
                        dx = 1 if alvo.pos_x > m.pos_x else (-1 if alvo.pos_x < m.pos_x else 0)
                        dy = 1 if alvo.pos_y > m.pos_y else (-1 if alvo.pos_y < m.pos_y else 0)
                        nx, ny = m.pos_x + dx, m.pos_y + dy
                        if 0 <= nx < tab.largura and 0 <= ny < tab.altura:
                            if tab.get_terrain_em(nx, ny) != "parede" and tab.grid[ny][nx] is None:
                                tab.grid[m.pos_y][m.pos_x] = None
                                tab.grid[ny][nx] = m
                                m.pos_x, m.pos_y = nx, ny
                                teve_movimento = True
                else:
                    from ...resolvedor_acoes import obter_zona_por_coordenada
                    zona_m = obter_zona_por_coordenada(m.pos_x, m.pos_y) or "patio"
                    invasores = dict(self.estado.get("invasores", {}))
                    zonas_com_invasores = [z for z, count in invasores.items() if count > 0]
                    if zonas_com_invasores:
                        zona_alvo = zona_m if invasores.get(zona_m, 0) > 0 else max(zonas_com_invasores, key=lambda z: invasores[z])
                        invasores[zona_alvo] -= 1
                        self.estado = aplicar_delta(self.estado, {"invasores": invasores})
                        from ...cerco_isectum import NOMES_ZONA
                        nome_z = NOMES_ZONA.get(zona_alvo, zona_alvo)
                        self._push("HEROI", f"⚔️ Guarda defendeu [{nome_z}] e combateu 1x Inseto!")
                        teve_movimento = True

        if cristais_minerados > 0:
            novos_tesouro = self.estado.get("tesouro", 0) + cristais_minerados
            self.estado = aplicar_delta(self.estado, {"tesouro": novos_tesouro})
            self._feedback(f"⛏️ +{cristais_minerados} Cristais Roxos (Mineração)!", (180, 80, 255))

        if teve_movimento or cristais_minerados > 0:
            self.map_backbuffer_sujo = True

