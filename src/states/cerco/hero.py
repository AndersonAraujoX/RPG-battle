"""
cerco_state_hero.py — Mixin de gestão de heróis (deck, cartas, suborno, upgrade) para CercoState
"""
from __future__ import annotations
import random

from ...resolvedor_acoes import obter_zona_por_coordenada
from .data import (
    MODO_NENHUM, MODO_MOVER, MODO_TRABALHAR, MODO_ESCAVAR,
    MODO_SUBORNAR, MODO_UPGRADE, MODO_CONVOCAR, MODO_ATACAR, MODO_ATIRAR,
    C_VERDE, C_PERIGO, C_HEROI, C_OURO,
)


class CercoStateHeroMixin:
    """Mixin responsável pela gestão de heróis: deck, cartas, status,
    alternância entre heróis, upgrade e suborno."""

    # ── STATUS ────────────────────────────────────────────────────────
    def _salvar_status_heroi(self, nome_heroi):
        if "herois_status" not in self.estado:
            self.estado["herois_status"] = {}
        self.estado["herois_status"][nome_heroi] = {
            "mao":              list(self.estado.get("mao", [])),
            "deck_heroi":       list(self.estado.get("deck_heroi", [])),
            "descarte":         list(self.estado.get("descarte", [])),
            "excluidas_ciclo":  list(self.estado.get("excluidas_ciclo", [])),
            "pontos_movimento": self.estado.get("pontos_movimento", 0),
            "pontos_trabalho":  self.estado.get("pontos_trabalho", 0),
            "pontos_escavacao": self.estado.get("pontos_escavacao", 0),
            "voo_ativo":        self.estado.get("voo_ativo", False)
        }

    def _carregar_status_heroi(self, nome_heroi):
        if "herois_status" not in self.estado or nome_heroi not in self.estado["herois_status"]:
            return
        status = self.estado["herois_status"][nome_heroi]
        from ...cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {
            "mao":              list(status.get("mao", [])),
            "deck_heroi":       list(status.get("deck_heroi", [])),
            "descarte":         list(status.get("descarte", []),),
            "excluidas_ciclo":  list(status.get("excluidas_ciclo", [])),
            "pontos_movimento": status.get("pontos_movimento", 0),
            "pontos_trabalho":  status.get("pontos_trabalho", 0),
            "pontos_escavacao": status.get("pontos_escavacao", 0),
            "voo_ativo":        status.get("voo_ativo", False)
        })

    def _alternar_heroi(self):
        if len(self.herois) <= 1:
            return
        heroi_antigo = self.heroi_atual
        if heroi_antigo:
            self._salvar_status_heroi(heroi_antigo.nome)
        self.heroi_atual_idx = (self.heroi_atual_idx + 1) % len(self.herois)
        novo = self.heroi_atual
        if novo:
            self._carregar_status_heroi(novo.nome)
            tab = self.motor.tabuleiro
            for gy in range(tab.altura):
                for gx in range(tab.largura):
                    if tab.grid[gy][gx] is novo:
                        from ...cerco_isectum import aplicar_delta
                        self.estado = aplicar_delta(self.estado, {
                            "heroi_x": gx,
                            "heroi_y": gy,
                            "pos_heroi": obter_zona_por_coordenada(gx, gy) or "camara_central",
                        })
                        break
            nome_exibido = "?????" if novo.nome == "Aquele" else novo.nome
            self._feedback(f"Herói atual: {nome_exibido}", C_HEROI)
            from ...resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor,
                (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )

    # ── DECK DO HERÓI ─────────────────────────────────────────────────
    def _comprar_mao(self):
        mao = list(self.estado["mao"])
        deck = list(self.estado["deck_heroi"])
        discard = list(self.estado["descarte"])
        # Cartas de upgrade acumuladas: sempre re-entram no ciclo
        upgrades_ativas = list(self.estado.get("cartas_upgrade_ativas", []))
        cartas_anteriores = len(mao)
        cartas_adicionadas = []

        while len(mao) < self.TAM_MAO:
            if not deck:
                if not discard and not self.estado.get("excluidas_ciclo", []) and not upgrades_ativas:
                    break
                todas = list(discard) + list(mao) + list(deck) + list(self.estado.get("excluidas_ciclo", []))
                # Adiciona cartas de upgrade ativas que ainda não estejam em 'todas' (sem duplicar)
                for up in upgrades_ativas:
                    if not any(c.get("id") == up.get("id") for c in todas):
                        todas.append(dict(up))
                random.shuffle(todas)
                candidatas_descarte = [c for c in todas if c not in mao]
                excluidas = []
                # Nunca exclui cartas de upgrade da rodada
                candidatas_excl = [c for c in candidatas_descarte if c.get("tipo") != "upgrade"]
                if len(candidatas_excl) >= 2:
                    excluidas.append(candidatas_excl.pop(random.randrange(len(candidatas_excl))))
                    excluidas.append(candidatas_excl.pop(random.randrange(len(candidatas_excl))))
                deck = [c for c in todas if c not in mao and c not in excluidas]
                discard = []
                from ...cerco_isectum import aplicar_delta
                self.estado = aplicar_delta(self.estado, {"excluidas_ciclo": excluidas})
                self._push("SISTEMA", f"Ciclo do Baralho: cartas reembaralhadas. 2 descartadas. "
                           f"({len(upgrades_ativas)} upgrade(s) no deck acumulado)")
            carta = deck.pop()
            mao.append(carta)
            cartas_adicionadas.append(carta)

        from ...cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {
            "mao": mao, "deck_heroi": deck, "descarte": discard
        })

        if not hasattr(self, 'animacoes_cartas_compra'):
            self.animacoes_cartas_compra = []

        mr = self.mao_rect
        deck_x = mr.right - 76
        deck_y = mr.y + 6

        for idx_adicionado, carta in enumerate(cartas_adicionadas):
            idx_mao = cartas_anteriores + idx_adicionado
            cx, cy, cw_f, ch_f = self._calcular_pos_carta_na_mao(idx_mao, len(mao))
            self.animacoes_cartas_compra.append({
                'idx_mao': idx_mao,
                'carta': carta,
                'start_pos': (deck_x, deck_y),
                'end_pos': (cx, cy),
                'cw': cw_f,
                'ch': ch_f,
                'progresso': 0.0,
                'delay': idx_adicionado * 8,
                'finalizada': False
            })

    def _jogar_carta(self, idx):
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            return
        carta = mao.pop(idx)

        from ...cerco_isectum import aplicar_delta
        is_upgrade = carta.get("tipo") == "upgrade"
        discard = list(self.estado["descarte"]) + [carta]

        if is_upgrade:
            # Cartas de upgrade acumulam em cartas_upgrade_ativas e vão para o descarte p/ ciclo
            ativas = [dict(c) for c in self.estado.get("cartas_upgrade_ativas", [])]
            if not any(c.get("id") == carta.get("id") for c in ativas):
                ativas.append(dict(carta))
            delta = {
                "mao":                  mao,
                "descarte":             discard,
                "cartas_upgrade_ativas": ativas,
                "pontos_movimento": self.estado["pontos_movimento"] + carta.get("movimento", 0),
                "pontos_trabalho":  self.estado["pontos_trabalho"]  + carta.get("trabalho",  0),
                "pontos_escavacao": self.estado["pontos_escavacao"] + carta.get("escavacao", 0),
            }
            self._push("HEROI", f"⭐ Upgrade ativado [{carta['nome']}]: acumulado! "
                                f"+{carta.get('movimento',0)}PM "
                                f"+{carta.get('trabalho',0)}PT +{carta.get('escavacao',0)}PE")
            self._feedback(f"⭐ Upgrade: {carta['nome']} (acumulado!)", (255, 200, 50))
        else:
            delta = {
                "mao":              mao,
                "descarte":         discard,
                "pontos_movimento": self.estado["pontos_movimento"] + carta.get("movimento", 0),
                "pontos_trabalho":  self.estado["pontos_trabalho"]  + carta.get("trabalho",  0),
                "pontos_escavacao": self.estado["pontos_escavacao"] + carta.get("escavacao", 0),
            }
            self._push("HEROI", f"Jogou [{carta['nome']}]: +{carta.get('movimento',0)}PM "
                                f"+{carta.get('trabalho',0)}PT +{carta.get('escavacao',0)}PE")
            self._feedback(f"Carta: {carta['nome']}", C_VERDE)

        self.estado = aplicar_delta(self.estado, delta)
        from ...resolvedor_acoes import obter_celulas_alcancaveis
        self.alcancaveis = obter_celulas_alcancaveis(
            self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
            self.estado["pontos_movimento"]
        )
        if carta.get("trabalho", 0) > 0:
            self._selecionar_modo(MODO_TRABALHAR)
        elif carta.get("movimento", 0) > 0:
            self._selecionar_modo(MODO_MOVER)
        elif carta.get("escavacao", 0) > 0:
            self._selecionar_modo(MODO_ESCAVAR)

    # ── AÇÕES DE CARTA ────────────────────────────────────────────────
    def _aplicar_acao_carta(self, idx, acao):
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            return
        carta = mao.pop(idx)

        is_upgrade = carta.get("tipo") == "upgrade"
        discard = list(self.estado["descarte"]) + [carta]

        if is_upgrade:
            ativas = [dict(c) for c in self.estado.get("cartas_upgrade_ativas", [])]
            if not any(c.get("id") == carta.get("id") for c in ativas):
                ativas.append(dict(carta))
            delta = {
                "mao": mao,
                "descarte": discard,
                "cartas_upgrade_ativas": ativas,
            }
        else:
            delta = {
                "mao": mao,
                "descarte": discard,
            }

        val_mov = carta.get("movimento", 0)
        val_trab = carta.get("trabalho", 0)
        val_esc = carta.get("escavacao", 0)

        efeito = carta.get("efeito_extra")
        if efeito == "draw_1":
            deck = list(self.estado["deck_heroi"])
            if deck:
                c = deck.pop(0)
                delta["mao"] = delta["mao"] + [c]
                delta["deck_heroi"] = deck
                self._push("SISTEMA", "Efeito extra da carta: Comprou 1 carta adicional.")
        elif efeito == "invocar_inimigo":
            from src.cerco_isectum import NOMES_ZONA
            zona_spawn = random.choice(["campo_norte", "campo_sul", "campo_leste", "campo_oeste"])
            novos_invasores = dict(self.estado["invasores"])
            novos_invasores[zona_spawn] = novos_invasores.get(zona_spawn, 0) + 1
            delta["invasores"] = novos_invasores
            self._push("AMEACA", f"Efeito da carta: Invocou 1x Invasor em {NOMES_ZONA.get(zona_spawn, zona_spawn)}!")
            self._feedback("Inimigo Invocado!", C_PERIGO)

        from ...cerco_isectum import aplicar_delta

        if acao == "andar":
            delta["pontos_movimento"] = self.estado["pontos_movimento"] + val_mov
            self.estado = aplicar_delta(self.estado, delta)
            self._push("HEROI", f"Jogou [{carta['nome']}] para ANDAR: +{val_mov} PM")
            self._feedback(f"Andar: +{val_mov} PM", C_VERDE)
            from ...resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )
            self._selecionar_modo(MODO_MOVER)

        elif acao == "coletar":
            delta["pontos_trabalho"] = self.estado["pontos_trabalho"] + val_trab
            delta["pontos_escavacao"] = self.estado["pontos_escavacao"] + val_esc
            self.estado = aplicar_delta(self.estado, delta)

            recursos_adicionados = []
            if val_trab > 0: recursos_adicionados.append(f"+{val_trab}PT")
            if val_esc > 0: recursos_adicionados.append(f"+{val_esc}PE")
            rec_str = " ".join(recursos_adicionados) if recursos_adicionados else "+0 Rec"

            self._push("HEROI", f"Jogou [{carta['nome']}] para COLETAR: {rec_str}")
            self._feedback(f"Coletar: {rec_str}", C_VERDE)

            if val_trab > 0:
                self.modo_acao = MODO_TRABALHAR
            elif val_esc > 0:
                self.modo_acao = MODO_ESCAVAR

            self._processar_acoes_automaticas(mostrar_erro_se_falhar=True)

        elif acao == "ambos":
            delta["pontos_movimento"] = self.estado["pontos_movimento"] + val_mov
            delta["pontos_trabalho"] = self.estado["pontos_trabalho"] + val_trab
            delta["pontos_escavacao"] = self.estado["pontos_escavacao"] + val_esc
            self.estado = aplicar_delta(self.estado, delta)

            recursos_adicionados = []
            if val_trab > 0: recursos_adicionados.append(f"+{val_trab}PT")
            if val_esc > 0: recursos_adicionados.append(f"+{val_esc}PE")
            rec_str = " ".join(recursos_adicionados) if recursos_adicionados else "+0 Rec"

            self._push("HEROI", f"Jogou [{carta['nome']}] para AMBOS: +{val_mov} PM e {rec_str}")
            self._feedback(f"Ambos: +{val_mov} PM e {rec_str}", C_VERDE)

            from ...resolvedor_acoes import obter_celulas_alcancaveis
            self.alcancaveis = obter_celulas_alcancaveis(
                self.motor, (self.estado.get("heroi_x", 9), self.estado.get("heroi_y", 9)),
                self.estado["pontos_movimento"]
            )
            self._selecionar_modo(MODO_MOVER)
            self._processar_acoes_automaticas(mostrar_erro_se_falhar=False)

        elif acao == "atacar":
            self.estado = aplicar_delta(self.estado, delta)
            self._push("HEROI", f"Jogou [{carta['nome']}] para ATACAR!")
            self._feedback("Atacar ativado!", C_VERDE)

            pos_heroi = self.estado.get("pos_heroi", "camara_central")
            if pos_heroi and "torre" in pos_heroi:
                self._selecionar_modo(MODO_ATIRAR)
            else:
                self._selecionar_modo(MODO_ATACAR)

        self._avancar_inimigos_carta()
        self.idx_carta_sendo_jogada = -1

    def _jogar_carta_invasao(self, idx):
        mao = list(self.estado["mao"])
        if idx < 0 or idx >= len(mao):
            return
        carta = mao.pop(idx)
        discard = list(self.estado["descarte"]) + [carta]

        from src.cerco_isectum import NOMES_ZONA, aplicar_delta
        zona_spawn = random.choice(["campo_norte", "campo_sul", "campo_leste", "campo_oeste"])
        novos_invasores = dict(self.estado["invasores"])
        novos_invasores[zona_spawn] = novos_invasores.get(zona_spawn, 0) + 1

        delta = {
            "mao": mao,
            "descarte": discard,
            "invasores": novos_invasores
        }

        self.estado = aplicar_delta(self.estado, delta)
        self._push("AMEACA", f"Invasão: Invasor Orc jogado da mão! Spawn em {NOMES_ZONA.get(zona_spawn, zona_spawn)}!")
        self._feedback("Orc Invocado da Mão!", C_PERIGO)
        try:
            self.game.play_sound('invalid_action')
        except:
            pass

    # ── AVANÇO DE INIMIGOS ────────────────────────────────────────────
    def _avancar_inimigos_carta(self):
        from ...cerco_isectum import NOMES_ZONA, aplicar_delta

        FLUXO = {
            "campo_norte": "muralha_norte",
            "campo_sul":   "muralha_sul",
            "campo_oeste": "muralha_oeste",
            "campo_leste": "muralha_leste",
            "muralha_norte": "carpintaria",
            "muralha_sul":   "curtume",
            "muralha_oeste": "fundicao",
            "muralha_leste": "patio",
            "carpintaria":   "camara_central",
            "curtume":       "camara_central",
            "fundicao":      "camara_central",
            "patio":         "camara_central",
        }

        e = self.estado
        novos = dict(e["invasores"])
        tesouro = e["tesouro"]
        reserva = e["reserva"]
        logs_avanco = []
        derrota = False

        ordem = [
            "camara_central",
            "carpintaria", "curtume", "fundicao", "patio",
            "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
            "campo_norte", "campo_sul", "campo_oeste", "campo_leste",
        ]

        for zona in ordem:
            qtd = novos.get(zona, 0)
            if qtd <= 0:
                continue

            if zona == "camara_central":
                roubado = min(qtd, tesouro)
                if roubado > 0:
                    tesouro -= roubado
                    reserva = min(10, reserva + roubado)
                    nome_zona = NOMES_ZONA.get(zona, zona)
                    logs_avanco.append(
                        ("AMEACA", f"{qtd}x invasor no {nome_zona} rouba {roubado} cristais do tesouro!")
                    )
                novos[zona] = 0
                if tesouro <= 0:
                    derrota = True
            elif zona in FLUXO:
                proxima = FLUXO[zona]
                if "campo" in zona:
                    subindo = (qtd + 1) // 2
                    ficando = qtd - subindo
                    novos[zona] = ficando
                    novos[proxima] = novos.get(proxima, 0) + subindo
                    nome_atual = NOMES_ZONA.get(zona, zona)
                    nome_prox = NOMES_ZONA.get(proxima, proxima)
                    logs_avanco.append(
                        ("AMEACA", f"{subindo}x invasor escala a muralha: {nome_atual} → {nome_prox} ({ficando}x ficaram para trás)")
                    )
                else:
                    novos[zona] = 0
                    novos[proxima] = novos.get(proxima, 0) + qtd
                    nome_atual = NOMES_ZONA.get(zona, zona)
                    nome_prox = NOMES_ZONA.get(proxima, proxima)
                    logs_avanco.append(
                        ("AMEACA", f"{qtd}x invasor avança: {nome_atual} → {nome_prox}")
                    )

        delta = {"invasores": novos, "tesouro": tesouro, "reserva": reserva}
        if derrota:
            delta["derrota"] = True
            delta["msg_derrota"] = "Cristais saqueados pelos invasores — DERROTA!"

        self.estado = aplicar_delta(self.estado, delta)

        if logs_avanco:
            self._push("AMEACA", "\U0001f3c3 Inimigos avançam ao jogar a carta!")
            for tag, msg in logs_avanco:
                self._push(tag, msg)

        if derrota:
            self._push("DERROTA", self.estado.get("msg_derrota", "DERROTA!"))
            self.fase = "FIM"

    # ── UPGRADE ───────────────────────────────────────────────────────
    def _adquirir_upgrade_direto(self, slot_id):
        """Adquire o upgrade e adiciona a carta direto na mão, resetando o slot do mercado com novo upgrade."""
        from ...cerco_isectum import CARTAS_UPGRADE, aplicar_delta
        e = self.estado

        slot = e["slots_upgrade"][slot_id]
        carta_up = next((c for c in CARTAS_UPGRADE if c["id"] == slot.get("carta_id")), None)
        if not carta_up:
            self._feedback("Carta de upgrade não encontrada!", C_PERIGO)
            return

        # 1. Adiciona em cartas_upgrade_ativas
        ativas = [dict(c) for c in e.get("cartas_upgrade_ativas", [])]
        if not any(c.get("id") == carta_up.get("id") for c in ativas):
            ativas.append(dict(carta_up))

        # 2. Adiciona a carta de upgrade diretamente na mão do jogador
        nova_mao = list(e["mao"]) + [dict(carta_up)]

        # 3. Reseta e repovoa o slot do mercado com a próxima carta de upgrade não comprada
        cartas_adquiridas_ids = {c.get("id") for c in ativas}
        cartas_no_mercado_ids = {
            s.get("carta_id") for i, s in enumerate(e["slots_upgrade"])
            if i != slot_id and s.get("carta_id") and not s.get("adquirido")
        }

        proxima_carta = None
        for candidate in CARTAS_UPGRADE:
            cid = candidate["id"]
            if cid not in cartas_adquiridas_ids and cid not in cartas_no_mercado_ids:
                proxima_carta = candidate
                break

        slots = [dict(s) for s in e["slots_upgrade"]]
        if proxima_carta:
            # Reseta o slot com a nova carta de upgrade
            slots[slot_id] = {
                "id": slot_id,
                "nome": proxima_carta["nome"],
                "simbolo": proxima_carta["simbolo"],
                "carta_id": proxima_carta["id"],
                "custo": dict(proxima_carta["custo"]),
                "descricao": proxima_carta.get("descricao", ""),
                "adquirido": False,
                "bloqueado": False,
                "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}
            }
            log_msg = f"⭐ Upgrade [{slot['nome']}] adquirido! Novo upgrade [{proxima_carta['nome']}] no mercado!"
        else:
            slots[slot_id]["adquirido"] = True
            slots[slot_id]["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
            log_msg = f"⭐ Upgrade [{slot['nome']}] adquirido! (Todas as melhorias compradas)"

        delta = {
            "slots_upgrade": slots,
            "mao": nova_mao,
            "cartas_upgrade_ativas": ativas,
        }
        self.estado = aplicar_delta(e, delta)
        self._push("HEROI", log_msg)
        self._feedback(f"⭐ Upgrade [{slot['nome']}] adquirido!", (255, 210, 50))
        self.idx_slot_upgrade = -1
        self.idx_carta_queimar = -1
        self.modo_acao = MODO_NENHUM

    def _tentar_upgrade(self):
        """Mantido por compatibilidade — redireciona para aquisição direta."""
        if self.idx_slot_upgrade >= 0:
            self._adquirir_upgrade_direto(self.idx_slot_upgrade)

    # ── SUBORNAR ──────────────────────────────────────────────────────
    def _subornar_recurso(self, recurso):
        from ...resolvedor_acoes import validar_subornar, executar_subornar
        from ...cerco_isectum import aplicar_delta
        e = self.estado
        ok, msg = validar_subornar(e, recurso)
        if ok:
            goblin_alvo = getattr(self, "alvo_negociacao", None)
            if goblin_alvo and goblin_alvo in self.motor.combatentes:
                tab = self.motor.tabuleiro
                if 0 <= goblin_alvo.pos_y < len(tab.grid) and 0 <= goblin_alvo.pos_x < len(tab.grid[0]):
                    tab.grid[goblin_alvo.pos_y][goblin_alvo.pos_x] = None
                self.motor.combatentes.remove(goblin_alvo)
                if hasattr(self.motor, 'time_b') and goblin_alvo in self.motor.time_b:
                    self.motor.time_b.remove(goblin_alvo)
            delta, logs = executar_subornar(e, recurso)
            self.estado = aplicar_delta(e, delta)
            for t, m in logs: self._push(t, m)
            self._feedback(f"Goblin negociou com sucesso!", C_VERDE)
        else:
            self._feedback(msg, C_PERIGO)
        self.modo_acao = MODO_NENHUM
        self.alvo_negociacao = None

    def _limpar_rocha_goblin(self):
        e = self.estado
        if e.get("pontos_escavacao", 0) < 4:
            self._feedback("Requer 4 Pontos de Escavação (PE)!", C_PERIGO)
            return

        goblin_alvo = getattr(self, "alvo_negociacao", None)
        if goblin_alvo and goblin_alvo in self.motor.combatentes:
            tab = self.motor.tabuleiro
            if 0 <= goblin_alvo.pos_y < len(tab.grid) and 0 <= goblin_alvo.pos_x < len(tab.grid[0]):
                tab.grid[goblin_alvo.pos_y][goblin_alvo.pos_x] = None
            self.motor.combatentes.remove(goblin_alvo)
            if hasattr(self.motor, 'time_b') and goblin_alvo in self.motor.time_b:
                self.motor.time_b.remove(goblin_alvo)

        from ...cerco_isectum import aplicar_delta
        delta = {
            "infiltradores": max(0, e.get("infiltradores", 0) - 1),
            "pontos_escavacao": max(0, e.get("pontos_escavacao", 0) - 4),
        }
        self.estado = aplicar_delta(e, delta)
        self._push("HEROI", "Ajudou Goblin a limpar rocha bônus (gastou 4 PE)!")
        self._feedback("Goblin negociou e saiu!", C_VERDE)
        self.modo_acao = MODO_NENHUM
        self.alvo_negociacao = None

    # ── HELPERS DE MAO ────────────────────────────────────────────────
    def _obter_mao_heroi(self, nome_heroi):
        if self.heroi_atual and self.heroi_atual.nome == nome_heroi:
            return list(self.estado.get("mao", []))
        status = self.estado.get("herois_status", {}).get(nome_heroi, {})
        return list(status.get("mao", []))

    def _definir_mao_heroi(self, nome_heroi, nova_mao):
        from ...cerco_isectum import aplicar_delta
        if self.heroi_atual and self.heroi_atual.nome == nome_heroi:
            self.estado = aplicar_delta(self.estado, {"mao": nova_mao})
            self._salvar_status_heroi(nome_heroi)
        else:
            if "herois_status" not in self.estado:
                self.estado["herois_status"] = {}
            if nome_heroi not in self.estado["herois_status"]:
                self.estado["herois_status"][nome_heroi] = {}
            self.estado["herois_status"][nome_heroi]["mao"] = nova_mao
