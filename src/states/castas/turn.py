"""
castas_turn.py — Mixin de fluxo de turno para CastasState

Fluxo assimétrico:
  JOGAR_CARTA → (todos os heróis jogaram) → TURNO_DIRETOR → FASE_AMEACA → repeat

O Diretor humano usa suas ações para:
  - Enviar castas de insetos para zonas específicas
  - Revelar cartas de ameaça
"""
from __future__ import annotations

from .data import (
    MODO_NENHUM, MODO_DIR_ESCOLHER_CASTA, MODO_DIR_ESCOLHER_ZONA,
    C_VERDE, C_PERIGO, C_OURO, C_HEROI, C_DIRETOR,
)


class CastasStateTurnMixin:

    # ── FIM DE TURNO DO HERÓI ────────────────────────────────────────────
    def _fim_turno_heroi(self):
        """Fim do turno do herói ativo. Herdado do Cerco mas com desvio para TURNO_DIRETOR."""
        if self.estado["mao"]:
            self._feedback("Use todas as cartas da mão para encerrar o turno!", C_PERIGO)
            try: self.game.play_sound('invalid_action')
            except: pass
            return

        from src.cerco_isectum import aplicar_delta
        from src.juiz_combate import resetar_dano_turno_brutamonte

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

        # Verifica se há próximo herói
        proximo = None
        for h in self.herois:
            if h.nome not in jogaram:
                proximo = h
                break

        if proximo:
            # Muda para próximo herói
            self.heroi_atual_idx = self.herois.index(proximo)
            self._carregar_status_heroi(proximo.nome)
            self._comprar_mao()
            nome_ex = "?????" if proximo.nome == "Aquele" else proximo.nome
            self._feedback(f"Turno de {nome_ex}! Use suas cartas.", C_HEROI)
            self._push("SISTEMA", f"Início do turno: {nome_ex}")
        else:
            # Todos os heróis jogaram → agora é o turno do Diretor
            self.estado = aplicar_delta(self.estado, {"herois_jogaram": []})
            self._iniciar_turno_diretor()

    # ── TURNO DO DIRETOR ─────────────────────────────────────────────────
    def _iniciar_turno_diretor(self):
        """Começa o turno do Diretor humano (jogador 2)."""
        from .data import DIFICULDADES_CASTAS
        from src.cerco_isectum import aplicar_delta

        dif_id  = self.config.get("dificuldade", {}).get("id", "normal")
        dif     = next((d for d in DIFICULDADES_CASTAS if d["id"] == dif_id), DIFICULDADES_CASTAS[1])
        acoes   = dif.get("acoes_dir", 3)

        self.estado = aplicar_delta(self.estado, {"acoes_diretor": acoes})
        self.fase   = "TURNO_DIRETOR"
        self.modo_acao = MODO_DIR_ESCOLHER_CASTA
        self.casta_selecionada = None
        self._feedback(f"🐛 Turno do Diretor! {acoes} ações disponíveis.", C_DIRETOR)
        self._push("SISTEMA", f"Turno do Diretor Isectum — {acoes} ação(ões).")

    def _diretor_usar_acao_inseto(self, inseto_id, zona_id):
        """Diretor humano envia um inseto para uma zona específica."""
        from src.cerco_isectum import DADOS_INIMIGOS, aplicar_delta, NOMES_ZONA

        if inseto_id not in DADOS_INIMIGOS:
            self._feedback("Casta inválida!", C_PERIGO)
            return

        zonas_validas = [
            "campo_norte", "campo_sul", "campo_oeste", "campo_leste",
            "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
            "torre_nw", "torre_ne", "torre_sw", "torre_se",
        ]
        if zona_id not in zonas_validas:
            self._feedback("Zona inválida para invasão!", C_PERIGO)
            return

        e = self.estado
        acoes = e.get("acoes_diretor", 0)
        if acoes <= 0:
            self._feedback("Sem ações restantes para o Diretor!", C_PERIGO)
            return

        # Adiciona invasor à zona
        invasores = dict(e["invasores"])
        invasores[zona_id] = invasores.get(zona_id, 0) + 1

        # Registra qual casta foi enviada para a zona (para instanciar o inseto certo)
        castas_inv = dict(e.get("castas_invasoras", {}))
        castas_inv[zona_id] = inseto_id

        self.estado = aplicar_delta(e, {
            "invasores":       invasores,
            "castas_invasoras": castas_inv,
            "acoes_diretor":   acoes - 1,
        })

        dados = DADOS_INIMIGOS[inseto_id]
        zona_nome = NOMES_ZONA.get(zona_id, zona_id)
        self._push("DIRETOR", f"🐛 {dados['emoji']} {dados['nome']} → {zona_nome}!")
        self._feedback(f"Casta enviada para {zona_nome}! {acoes - 1} ação(ões) restantes.", C_DIRETOR)

        # Força sincronização imediata
        self._sincronizar_inimigos_tabuleiro()

        self.casta_selecionada = None
        self.modo_acao = MODO_DIR_ESCOLHER_CASTA

        if self.estado.get("acoes_diretor", 0) <= 0:
            self._concluir_turno_diretor()

    def _concluir_turno_diretor(self):
        """Diretor encerrou suas ações → passa para fase de ameaça."""
        from src.cerco_isectum import aplicar_delta
        self.estado = aplicar_delta(self.estado, {"acoes_diretor": 0})
        self.modo_acao = MODO_NENHUM
        self._iniciar_fase_ameaca()

    # ── FASE DE AMEAÇA ───────────────────────────────────────────────────
    def _iniciar_fase_ameaca(self):
        """Fase automática de movimento dos invasores (igual ao Cerco)."""
        if self._verificar_derrota_imediata():
            return
        self.fase = "FASE_AMEACA"
        self.carta_cerco = self.deck.pop() if self.deck else None
        if self.carta_cerco:
            self._push("CARTA", f"[N{self.carta_cerco.get('nivel', 1)}] "
                                f"{self.carta_cerco.get('simbolo','?')} "
                                f"{self.carta_cerco.get('titulo','?')}")

    def _resolver_carta_cerco(self):
        """Processa a carta de ameaça e avança para próxima rodada."""
        from src.cerco_isectum import avancar_ciclo_armas, processar_carta, aplicar_delta

        e = self.estado
        d, ls = avancar_ciclo_armas(e)
        if d:
            self.estado = aplicar_delta(e, d)
            e = self.estado
        for t, m in ls:
            self._push(t, m)

        if self.carta_cerco:
            delta, logs = processar_carta(self.estado, self.carta_cerco)
            self.estado = aplicar_delta(self.estado, delta)
            for t, m in logs:
                self._push(t, m)

        self.carta_cerco = None
        nova_rodada = self.estado.get("rodada", 1) + 1
        self.estado = aplicar_delta(self.estado, {"rodada": nova_rodada})

        # Limpa zonas bloqueadas da rodada anterior
        self.estado = aplicar_delta(self.estado, {"zonas_bloqueadas": []})

        if self._verificar_derrota_imediata():
            return

        if self.estado.get("derrota") or self.estado.get("vitoria"):
            self.fase = "FIM"
        else:
            self.fase = "JOGAR_CARTA"
            self._comprar_mao()
            self._push("SISTEMA", f"=== Rodada {nova_rodada} ===")

    # ── VERIFICAÇÃO DE DERROTA ───────────────────────────────────────────
    def _verificar_derrota_imediata(self):
        from src.cerco_isectum import aplicar_delta
        e     = self.estado
        msg   = ""
        derro = False

        if e.get("tesouro", 10) <= 0:
            derro = True; msg = "Todo o ouro da Câmara foi roubado pelos Insectum! DERROTA!"
        elif e.get("reserva", 10) <= 0:
            derro = True; msg = "Reservas esgotadas! As castas invadiram! DERROTA!"
        elif e.get("brutamontes", 0) >= 3:
            derro = True; msg = "3 Insectum-Brutamontes invadiram o túnel! DERROTA!"
        elif not self.deck:
            derro = True; msg = "O deck de Ameaças acabou! DERROTA!"

        if derro:
            self.estado = aplicar_delta(e, {"derrota": True, "msg_derrota": msg})
            self._push("DERROTA", msg)
            self.fase = "FIM"
            return True
        return False
