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
        desc = list(self.estado["descarte"]) + list(self.estado["mao"])
        self.estado = aplicar_delta(self.estado, {"mao": [], "descarte": desc})
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

    # ── VERIFICAÇÃO DE DERROTA ────────────────────────────────────────
    def _verificar_derrota_imediata(self):
        from ...cerco_isectum import aplicar_delta
        e = self.estado
        derrota = False
        msg = ""

        if e.get("tesouro", 10) <= 0:
            derrota = True
            msg = "Todo o ouro da Câmara foi roubado! DERROTA!"
        elif e.get("reserva", 10) <= 0:
            derrota = True
            msg = "Orcs da reserva esgotados! DERROTA!"
        elif e.get("brutamontes", 0) >= 3:
            derrota = True
            msg = "3 Brutamontes/Trolls invadiram o túnel! DERROTA!"
        elif not self.deck:
            derrota = True
            msg = "O deck de Cerco de Ameaças acabou! DERROTA!"
        elif len(e.get("deck_catapulta", [1, 2, 3, 4])) <= 0:
            derrota = True
            msg = "O deck de munição de Catapulta esgotou! DERROTA!"

        if derrota:
            self.estado = aplicar_delta(self.estado, {
                "derrota": True,
                "msg_derrota": msg
            })
            self._push("DERROTA", msg)
            self.fase = "FIM"
            return True
        return False

    # ── FASE AMEAÇA ───────────────────────────────────────────────────
    def _iniciar_fase_ameaca(self):
        if self._verificar_derrota_imediata():
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

        if self._verificar_derrota_imediata():
            return

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.fase = "FIM"
        else:
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()
