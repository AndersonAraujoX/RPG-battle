"""
round_simultaneo.py — Mixin de Round de Sincronia para CercoState

Implementa a mecânica de ativação simultânea de cartas:
  - Todos os heróis selecionam 1 carta por round (sem espera sequencial).
  - Os efeitos são acumulados e resolvidos juntos (camadas: Movimento → Trabalho → Escavação → Upgrade).
  - Bônus de Sinergia quando 2+ heróis jogam cartas do mesmo tipo.
  - Inimigos avançam 1 passo após cada round.
  - O turno global encerra quando o primeiro herói esgota a mão.
  - Vantagem por Velocidade: quem esgota a mão primeiro ganha bônus no próximo turno.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# ─── Tipos de carta (camadas de resolução) ────────────────────────────────────
CAMADA_ORDEM = ["movimento", "trabalho", "escavacao", "upgrade"]

# ─── Bônus de Sinergia ────────────────────────────────────────────────────────
BONUS_SINERGIA = {
    "movimento":  {"mensagem": "⚡ SINCRONIA: Movimento — +1 passo bônus para todos!", "tipo": "passo_extra"},
    "trabalho":   {"mensagem": "⚡ SINCRONIA: Trabalho — +1 recurso bônus coletado!",   "tipo": "recurso_extra"},
    "escavacao":  {"mensagem": "⚡ SINCRONIA: Escavação — -2 pedregulhos extras!",       "tipo": "escavacao_extra"},
    "upgrade":    {"mensagem": "⚡ SINCRONIA SUPREMA: Todos jogaram Upgrade!",           "tipo": "cristal_extra"},
}

BONUS_SUPREMO = {
    "mensagem": "🌟 SINCRONIA PERFEITA: Todos jogaram o mesmo tipo! +2 Cristais Bônus!",
    "tipo": "cristal_extra_2",
}


class RoundSimultaneoMixin:
    """
    Mixin que implementa o 'Round de Sincronia' — a mecânica de ativação
    simultânea de cartas para todos os heróis por round.

    Fases introduzidas:
        ROUND_SIMULTANEO  — cada herói ainda está escolhendo sua carta
        ACAO_LIVRE        — (reutilizada) heróis usam os pontos gerados no mapa
    """

    # ─── Inicialização de estado ─────────────────────────────────────────────

    def _init_round_simultaneo(self):
        """Inicializa/reseta as variáveis de controle do Round de Sincronia."""
        # Carta que cada herói selecionou para este round (nome_heroi → carta ou None)
        self.rs_cartas_selecionadas: Dict[str, Optional[dict]] = {}
        # Herói que terminou de usar todas as cartas primeiro neste turno
        self.rs_vencedor_velocidade: Optional[str] = None
        # Número do round atual dentro do turno global
        self.rs_round_atual: int = 0
        # Flag: turno de sincronia ativo
        self.rs_ativo: bool = False
        # Bônus de carta extra para o vencedor de velocidade (guardado para próximo turno)
        self.rs_bonus_proxima_rodada: Dict[str, str] = {}  # nome_heroi → tipo_bonus

    # ─── Iniciar turno global (substitui a lógica sequencial por herói) ──────

    def iniciar_turno_sincronia(self):
        """
        Inicia um novo turno global de sincronia.
        Todos os heróis recebem suas mãos e o round começa.
        """
        from ...cerco_isectum import aplicar_delta

        self._init_round_simultaneo()
        self.rs_ativo = True
        self.rs_round_atual = 0
        self.estado = aplicar_delta(self.estado, {"herois_jogaram": []})

        # Aplica bônus de velocidade do turno anterior (carta extra)
        for nome_h, tipo_bonus in list(self.rs_bonus_proxima_rodada.items()):
            st = self.estado.get("herois_status", {}).get(nome_h)
            if st and st.get("deck_heroi"):
                carta_extra = st["deck_heroi"].pop(0)
                st["mao"].append(carta_extra)
                self._push("SISTEMA", f"🏃 {nome_h} ganhou 1 carta bônus por velocidade: [{carta_extra.get('nome', '?')}]")
        self.rs_bonus_proxima_rodada = {}

        self._iniciar_proximo_round()

    def _iniciar_proximo_round(self):
        """Avança para o próximo round dentro do turno global."""
        self.rs_round_atual += 1
        self.rs_cartas_selecionadas = {h.nome: None for h in self.herois if h.hp_atual > 0}
        self.fase = "ROUND_SIMULTANEO"
        nomes = ", ".join(
            "?????" if h.nome == "Aquele" else h.nome
            for h in self.herois if h.hp_atual > 0
        )
        self._push("SISTEMA", f"🔄 Round {self.rs_round_atual} — {nomes}: escolham 1 carta!")
        self._feedback(f"Round {self.rs_round_atual}: cada herói escolhe 1 carta simultaneamente!", (100, 200, 255))

    # ─── Seleção de carta por herói ──────────────────────────────────────────

    def selecionar_carta_round(self, nome_heroi: str, idx_carta: int) -> bool:
        """
        Registra a seleção de uma carta por um herói para o round atual.

        Returns:
            True se a seleção foi registrada com sucesso.
        """
        if self.fase != "ROUND_SIMULTANEO":
            return False

        # Obtém a mão do herói correto
        if nome_heroi == self.heroi_atual.nome:
            mao = self.estado.get("mao", [])
        else:
            st = self.estado.get("herois_status", {}).get(nome_heroi, {})
            mao = st.get("mao", [])

        if idx_carta < 0 or idx_carta >= len(mao):
            return False

        carta = mao[idx_carta]
        self.rs_cartas_selecionadas[nome_heroi] = {"carta": carta, "idx": idx_carta}

        nome_exibido = "?????" if nome_heroi == "Aquele" else nome_heroi
        self._push("CARTA", f"🃏 {nome_exibido} selecionou [{carta.get('nome', '?')}]")
        self._feedback(f"{nome_exibido} selecionou [{carta.get('nome', '?')}]! Aguardando outros...", (180, 220, 255))

        # Se todos os heróis vivos já escolheram, resolve o round
        herois_vivos = [h for h in self.herois if h.hp_atual > 0]
        todos_escolheram = all(
            self.rs_cartas_selecionadas.get(h.nome) is not None
            for h in herois_vivos
        )
        if todos_escolheram:
            self._resolver_round_simultaneo()
        return True

    # ─── Resolução do round ──────────────────────────────────────────────────

    def _resolver_round_simultaneo(self):
        """
        Resolve todas as cartas selecionadas no round atual.
        Ordem de resolução por camadas de tipo:
            Movimento → Trabalho → Escavação → Upgrade
        """
        from ...cerco_isectum import aplicar_delta

        cartas_por_heroi: Dict[str, dict] = {}
        for nome, sel in self.rs_cartas_selecionadas.items():
            if sel:
                cartas_por_heroi[nome] = sel["carta"]

        if not cartas_por_heroi:
            self._iniciar_proximo_round()
            return

        # — Detectar sinergia —
        sinergia = self._calcular_sinergia(cartas_por_heroi)

        # — Remover cartas das mãos —
        for nome, sel in self.rs_cartas_selecionadas.items():
            if not sel:
                continue
            idx = sel["idx"]
            if nome == self.heroi_atual.nome:
                mao = list(self.estado.get("mao", []))
                if idx < len(mao):
                    carta = mao.pop(idx)
                    descarte = list(self.estado.get("descarte", []))
                    descarte.append(carta)
                    self.estado = aplicar_delta(self.estado, {"mao": mao, "descarte": descarte})
            else:
                st = self.estado.get("herois_status", {}).get(nome, {})
                mao = list(st.get("mao", []))
                if idx < len(mao):
                    carta = mao.pop(idx)
                    descarte = list(st.get("descarte", []))
                    descarte.append(carta)
                    st["mao"] = mao
                    st["descarte"] = descarte

        # — Aplicar efeitos por camada —
        for camada in CAMADA_ORDEM:
            for nome, carta in cartas_por_heroi.items():
                tipo_carta = self._tipo_carta(carta)
                if tipo_carta != camada:
                    continue
                self._aplicar_efeito_carta_sincronia(nome, carta)

        # — Aplicar bônus de sinergia —
        if sinergia:
            self._aplicar_bonus_sinergia(sinergia, cartas_por_heroi)

        # — Pressão crescente: inimigos avançam —
        self._pressao_crescente_round()

        # — Verificar fim de turno —
        if not self._verificar_fim_turno_simultaneo():
            self._iniciar_proximo_round()

    def _tipo_carta(self, carta: dict) -> str:
        """Retorna o tipo de camada de resolução de uma carta."""
        if carta.get("tipo") == "upgrade":
            return "upgrade"
        if carta.get("escavacao"):
            return "escavacao"
        if carta.get("trabalho"):
            return "trabalho"
        return "movimento"

    def _aplicar_efeito_carta_sincronia(self, nome_heroi: str, carta: dict):
        """Aplica o efeito de uma carta no contexto do round simultâneo."""
        from ...cerco_isectum import aplicar_delta

        nome_ex = "?????" if nome_heroi == "Aquele" else nome_heroi
        tipo = self._tipo_carta(carta)

        if tipo == "movimento":
            pts = carta.get("movimento", 2)
            # Acumula pontos no estado do herói ativo ou no herois_status
            if nome_heroi == self.heroi_atual.nome:
                atual = self.estado.get("pontos_movimento", 0)
                self.estado = aplicar_delta(self.estado, {"pontos_movimento": atual + pts})
            else:
                st = self.estado.get("herois_status", {}).get(nome_heroi, {})
                st["pontos_movimento"] = st.get("pontos_movimento", 0) + pts
            self._push("CARTA", f"🔵 {nome_ex}: [{carta.get('nome', '?')}] → +{pts} Movimento")

        elif tipo == "trabalho":
            pts = carta.get("trabalho", 1)
            if nome_heroi == self.heroi_atual.nome:
                atual = self.estado.get("pontos_trabalho", 0)
                self.estado = aplicar_delta(self.estado, {"pontos_trabalho": atual + pts})
            else:
                st = self.estado.get("herois_status", {}).get(nome_heroi, {})
                st["pontos_trabalho"] = st.get("pontos_trabalho", 0) + pts
            self._push("CARTA", f"🟢 {nome_ex}: [{carta.get('nome', '?')}] → +{pts} Trabalho")

        elif tipo == "escavacao":
            pts = carta.get("escavacao", 1)
            if nome_heroi == self.heroi_atual.nome:
                atual = self.estado.get("pontos_escavacao", 0)
                self.estado = aplicar_delta(self.estado, {"pontos_escavacao": atual + pts})
            else:
                st = self.estado.get("herois_status", {}).get(nome_heroi, {})
                st["pontos_escavacao"] = st.get("pontos_escavacao", 0) + pts
            self._push("CARTA", f"🟡 {nome_ex}: [{carta.get('nome', '?')}] → +{pts} Escavação")

        elif tipo == "upgrade":
            upgrades_ativas = list(self.estado.get("cartas_upgrade_ativas", []))
            if not any(c.get("id") == carta.get("id") for c in upgrades_ativas):
                upgrades_ativas.append(dict(carta))
                from ...cerco_isectum import aplicar_delta
                self.estado = aplicar_delta(self.estado, {"cartas_upgrade_ativas": upgrades_ativas})
            self._push("CARTA", f"⭐ {nome_ex}: [{carta.get('nome', '?')}] → Upgrade PERMANENTE ativado!")

    # ─── Cálculo de Sinergia ─────────────────────────────────────────────────

    def _calcular_sinergia(self, cartas_por_heroi: Dict[str, dict]) -> Optional[dict]:
        """
        Detecta sinergia quando 2+ heróis jogam cartas do mesmo tipo.
        Retorna o dicionário de bônus aplicável, ou None.
        """
        if len(cartas_por_heroi) < 2:
            return None

        tipos = [self._tipo_carta(c) for c in cartas_por_heroi.values()]
        contagem = {}
        for t in tipos:
            contagem[t] = contagem.get(t, 0) + 1

        tipo_dominante = max(contagem, key=contagem.__getitem__)
        qtd_dominante = contagem[tipo_dominante]

        # Todos jogaram o mesmo tipo E são 3+ heróis → Bônus Supremo
        if qtd_dominante == len(cartas_por_heroi) and len(cartas_por_heroi) >= 3:
            return {**BONUS_SUPREMO, "tipo_carta": tipo_dominante}

        # 2+ heróis jogaram o mesmo tipo → Bônus normal do tipo
        if qtd_dominante >= 2:
            return {**BONUS_SINERGIA[tipo_dominante], "tipo_carta": tipo_dominante}

        return None


    def _aplicar_bonus_sinergia(self, sinergia: dict, cartas_por_heroi: Dict[str, dict]):
        """Aplica o bônus de sinergia ao estado do jogo."""
        from ...cerco_isectum import aplicar_delta

        self._push("SISTEMA", sinergia["mensagem"])
        self._feedback(sinergia["mensagem"], (255, 220, 60))

        tipo_bonus = sinergia["tipo"]

        if tipo_bonus == "passo_extra":
            atual = self.estado.get("pontos_movimento", 0)
            self.estado = aplicar_delta(self.estado, {"pontos_movimento": atual + 1})

        elif tipo_bonus == "recurso_extra":
            dep = dict(self.estado.get("recursos_depositados", {"madeira": 0, "couro": 0, "metal": 0}))
            import random as _rnd
            rec = _rnd.choice(["madeira", "couro", "metal"])
            dep[rec] = dep.get(rec, 0) + 1
            self.estado = aplicar_delta(self.estado, {"recursos_depositados": dep})
            self._push("HEROI", f"⚡ Sinergia: +1 {rec.upper()} bônus coletado!")

        elif tipo_bonus == "escavacao_extra":
            pedras = self.estado.get("pedregulhos", 0)
            if pedras > 0:
                self.estado = aplicar_delta(self.estado, {"pedregulhos": max(0, pedras - 2)})
                self._push("HEROI", "⚡ Sinergia: -2 Pedregulhos extras removidos!")

        elif tipo_bonus == "cristal_extra":
            novo_t = self.estado.get("tesouro", 0) + 1
            self.estado = aplicar_delta(self.estado, {"tesouro": novo_t})
            self._push("HEROI", f"⚡ Sinergia: +1 Cristal Roxo (Total: {novo_t}💎)!")

        elif tipo_bonus == "cristal_extra_2":
            novo_t = self.estado.get("tesouro", 0) + 2
            self.estado = aplicar_delta(self.estado, {"tesouro": novo_t})
            self._push("HEROI", f"🌟 Sincronia Perfeita: +2 Cristais Roxos (Total: {novo_t}💎)!")

    # ─── Pressão Crescente por Round ────────────────────────────────────────

    def _pressao_crescente_round(self):
        """
        A cada round, os inimigos ficam mais agressivos:
          Round 1: avançam 1 passo
          Round 2: avançam 1 passo + rolam ataque
          Round 3+: avançam 2 passos + atacam
        """
        round_num = self.rs_round_atual

        if round_num == 1:
            self._push("INIMIGO", f"🐛 Round {round_num}: Insetos avançam 1 passo...")
            self._processar_turnos_inimigos(apenas_passo=True)
        elif round_num == 2:
            self._push("INIMIGO", f"🐛 Round {round_num}: Insetos avançam e atacam!")
            self._processar_turnos_inimigos(apenas_passo=True)
            # Após o passo, processa ataques mas sem mover de novo
            self._processar_ataques_inimigos_round()
        else:
            self._push("INIMIGO", f"⚠️ Round {round_num}+: PRESSÃO MÁXIMA — Insetos avançam 2 passos e atacam!")
            self._processar_turnos_inimigos(apenas_passo=False)

        self._verificar_derrota_imediata()

    def _processar_ataques_inimigos_round(self):
        """Processa apenas os ataques dos inimigos, sem movimentação (para o Round 2)."""
        import random as _rnd
        tab = self.motor.tabuleiro
        inimigos = [
            p for p in list(self.motor.combatentes)
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0
        ]
        alvos = [
            p for p in list(self.motor.combatentes)
            if getattr(p, "time", "A") == "A" and p.hp_atual > 0
        ]
        if not inimigos or not alvos:
            return

        for ini in inimigos:
            alcance = getattr(ini, "alcance", 1)
            alvo = min(alvos, key=lambda a: abs(a.pos_x - ini.pos_x) + abs(a.pos_y - ini.pos_y))
            dist = abs(alvo.pos_x - ini.pos_x) + abs(alvo.pos_y - ini.pos_y)
            if dist <= alcance and alvo.hp_atual > 0:
                d20 = _rnd.randint(1, 20)
                bonus_atk = max(5, getattr(ini, "bonus_ataque", 5))
                if d20 + bonus_atk >= getattr(alvo, "ac", 14):
                    nd, nf = getattr(ini, "dado_dano", (1, 6))
                    dano = sum(_rnd.randint(1, nf) for _ in range(nd)) + getattr(ini, "bonus_dano", 3)
                    alvo.hp_atual -= dano
                    self._push("INIMIGO", f"⚔️ {ini.nome} ataca {alvo.nome}! -{dano} HP (Round {self.rs_round_atual})")
                    if hasattr(self, "_push_popup_combate"):
                        self._push_popup_combate(alvo.pos_x, alvo.pos_y, f"💥 -{dano}", (255, 80, 80))
                    if hasattr(self, "_salvar_status_heroi"):
                        self._salvar_status_heroi(alvo.nome)

    # ─── Verificação de Fim de Turno ────────────────────────────────────────

    def _verificar_fim_turno_simultaneo(self) -> bool:
        """
        Verifica se o turno global deve encerrar.
        O turno encerra quando o primeiro herói esgota sua mão.

        Returns:
            True se o turno foi encerrado.
        """
        herois_vivos = [h for h in self.herois if h.hp_atual > 0]
        if not herois_vivos:
            return True  # Derrota já será tratada

        # Verifica quem esgotou a mão
        herois_sem_mao = []
        for h in herois_vivos:
            if h.nome == self.heroi_atual.nome:
                mao = self.estado.get("mao", [])
            else:
                st = self.estado.get("herois_status", {}).get(h.nome, {})
                mao = st.get("mao", [])
            if not mao:
                herois_sem_mao.append(h.nome)

        if not herois_sem_mao:
            return False  # Nenhum herói esgotou, continua

        # O primeiro herói a esgotar ganha bônus de velocidade
        if not self.rs_vencedor_velocidade and herois_sem_mao:
            vencedor = herois_sem_mao[0]
            self.rs_vencedor_velocidade = vencedor
            nome_ex = "?????" if vencedor == "Aquele" else vencedor
            self._push("SISTEMA", f"🏃 {nome_ex} foi o mais rápido! Ganhará 1 carta extra no próximo turno.")
            self._feedback(f"🏃 {nome_ex} ganhou Vantagem por Velocidade!", (100, 255, 160))
            self.rs_bonus_proxima_rodada[vencedor] = "carta_extra"

        # Encerra o turno global
        self.rs_ativo = False
        self._concluir_fim_turno_completo()
        return True

    # ─── Painel de Informação do Round (para draw_ui) ───────────────────────

    def get_info_round_sincronia(self) -> dict:
        """
        Retorna informações do round atual para serem exibidas na UI.
        """
        herois_vivos = [h for h in self.herois if h.hp_atual > 0]
        selecionados = {
            nome: sel is not None
            for nome, sel in self.rs_cartas_selecionadas.items()
        }
        faltando = sum(1 for v in selecionados.values() if not v)

        cartas_por_tipo: Dict[str, int] = {}
        for sel in self.rs_cartas_selecionadas.values():
            if sel:
                t = self._tipo_carta(sel["carta"])
                cartas_por_tipo[t] = cartas_por_tipo.get(t, 0) + 1

        sinergia_detectada = None
        if len(cartas_por_tipo) > 0:
            tipo_dom = max(cartas_por_tipo, key=cartas_por_tipo.__getitem__)
            if cartas_por_tipo[tipo_dom] >= 2:
                sinergia_detectada = tipo_dom

        return {
            "round_atual": self.rs_round_atual,
            "total_herois": len(herois_vivos),
            "selecionados": selecionados,
            "faltando": faltando,
            "sinergia_detectada": sinergia_detectada,
            "cartas_selecionadas": {
                nome: sel["carta"] if sel else None
                for nome, sel in self.rs_cartas_selecionadas.items()
            },
            "vencedor_velocidade": self.rs_vencedor_velocidade,
        }
