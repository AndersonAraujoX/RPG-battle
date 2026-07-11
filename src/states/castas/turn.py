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
        """Começa a rodada de turnos dos Filhos do Imperador."""
        from .data import DIFICULDADES_CASTAS
        from src.cerco_isectum import aplicar_delta

        dif_id  = self.config.get("dificuldade", {}).get("id", "normal")
        dif     = next((d for d in DIFICULDADES_CASTAS if d["id"] == dif_id), DIFICULDADES_CASTAS[1])
        acoes   = dif.get("acoes_dir", 3)

        # Configura o primeiro Filho do Imperador da fila
        self.estado = aplicar_delta(self.estado, {
            "diretor_ativo_idx": 0,
        })
        
        # Define as ações iniciais de todos os diretores
        acoes_dir = {d: acoes for d in self.diretores}
        self.estado = aplicar_delta(self.estado, {"acoes_diretores": acoes_dir})

        self.fase   = "TURNO_DIRETOR"
        self.modo_acao = MODO_NENHUM
        self.casta_selecionada = None
        self.timer_diretor_bot = 0

        ativo = self.diretores[0]
        self._feedback(f"🐛 Turno de {ativo}! {acoes} ações.", C_DIRETOR)
        self._push("SISTEMA", f"Turno de {ativo} — {acoes} ação(ões).")

    def _diretor_usar_acao_inseto_multi(self, ativo, inseto_id, zona_id):
        """Um bot Filho do Imperador envia um inseto para uma zona de spawn."""
        from src.cerco_isectum import DADOS_INIMIGOS, aplicar_delta, NOMES_ZONA

        if inseto_id not in DADOS_INIMIGOS:
            return

        e = self.estado
        acoes = e["acoes_diretores"].get(ativo, 0)
        if acoes <= 0:
            return

        # Remove da mão do Filho ativo e descarta
        maos = dict(e["maos_diretores"])
        mao_dir = list(maos.get(ativo, []))
        if inseto_id in mao_dir:
            mao_dir.remove(inseto_id)
            
        descartes = dict(e["descarte_diretores"])
        descarte_dir = list(descartes.get(ativo, []))
        descarte_dir.append(inseto_id)

        # Repõe a mão a partir do deck individual
        decks = dict(e["decks_diretores"])
        deck_dir = list(decks.get(ativo, []))
        if not deck_dir and descarte_dir:
            deck_dir = list(descarte_dir)
            import random
            random.shuffle(deck_dir)
            descarte_dir = []

        if deck_dir:
            mao_dir.append(deck_dir.pop(0))

        # Adiciona invasor à zona do Cerco
        invasores = dict(e["invasores"])
        invasores[zona_id] = invasores.get(zona_id, 0) + 1

        # Registra a casta invasora na zona correspondente
        castas_inv = dict(e.get("castas_invasoras", {}))
        castas_inv[zona_id] = inseto_id

        # Atualiza dicionários do estado
        maos[ativo] = mao_dir
        decks[ativo] = deck_dir
        descartes[ativo] = descarte_dir
        
        acoes_dir = dict(e["acoes_diretores"])
        acoes_dir[ativo] = acoes - 1

        self.estado = aplicar_delta(e, {
            "invasores":        invasores,
            "castas_invasoras":  castas_inv,
            "maos_diretores":   maos,
            "decks_diretores":  decks,
            "descarte_diretores": descartes,
            "acoes_diretores":  acoes_dir,
        })

        dados = DADOS_INIMIGOS[inseto_id]
        zona_nome = NOMES_ZONA.get(zona_id, zona_id)
        self._push(ativo, f"🐛 {dados['emoji']} {dados['nome']} → {zona_nome}!")
        self._feedback(f"{ativo} enviou casta para {zona_nome}!", C_DIRETOR)

        # Força sincronização imediata
        self._sincronizar_inimigos_tabuleiro()

        if acoes - 1 <= 0:
            self._concluir_turno_diretor()

    def _concluir_turno_diretor(self):
        """Conclui o turno do Filho ativo. Passa para o próximo ou inicia Fase de Ameaça."""
        from src.cerco_isectum import aplicar_delta
        
        idx = self.estado.get("diretor_ativo_idx", 0)
        # Zera as ações do Filho que acabou de jogar
        ativo = self.diretores[idx]
        acoes_dir = dict(self.estado["acoes_diretores"])
        acoes_dir[ativo] = 0
        self.estado = aplicar_delta(self.estado, {"acoes_diretores": acoes_dir})

        if idx + 1 < len(self.diretores):
            # Passa para o próximo Filho do Imperador
            novo_idx = idx + 1
            proximo = self.diretores[novo_idx]
            self.estado = aplicar_delta(self.estado, {
                "diretor_ativo_idx": novo_idx,
            })
            self.timer_diretor_bot = 0
            self._feedback(f"Turno de {proximo}!", C_DIRETOR)
            self._push("SISTEMA", f"Turno de {proximo}.")
        else:
            # Todos os Filhos jogaram → inicia a Fase de Ameaça
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

        # Guarda os invasores antes de processar a movimentação
        invasores_antes = dict(self.estado.get("invasores", {}))

        if self.carta_cerco:
            delta, logs = processar_carta(self.estado, self.carta_cerco)
            self.estado = aplicar_delta(self.estado, delta)
            for t, m in logs:
                self._push(t, m)

            # Sincroniza a trilha de castas invasoras de acordo com as transições de zona do Cerco
            if self.carta_cerco.get("tipo") == "mover":
                c_inv = dict(self.estado.get("castas_invasoras", {}))
                
                # 1. Oficinas → Câmara Central
                for of in ("carpintaria", "curtume", "fundicao", "patio"):
                    if invasores_antes.get(of, 0) > 0:
                        c_inv["camara_central"] = c_inv.get(of, "formiga_correicao")
                
                # 2. Muralhas → Oficinas
                for mur, of in (("muralha_norte", "carpintaria"), ("muralha_sul", "curtume"),
                                ("muralha_oeste", "fundicao"),    ("muralha_leste", "patio")):
                    if invasores_antes.get(mur, 0) > 0:
                        c_inv[of] = c_inv.get(mur, "formiga_correicao")
                
                # 3. Campos → Muralhas
                for campo, mur in (("campo_norte", "muralha_norte"), ("campo_sul", "muralha_sul"),
                                   ("campo_oeste", "muralha_oeste"), ("campo_leste", "muralha_leste")):
                    if invasores_antes.get(campo, 0) > 0:
                        c_inv[mur] = c_inv.get(campo, "formiga_correicao")
                        
                self.estado = aplicar_delta(self.estado, {"castas_invasoras": c_inv})

        carta_tipo = self.carta_cerco.get("tipo") if self.carta_cerco else None
        self.carta_cerco = None
        nova_rodada = self.estado.get("rodada", 1) + 1
        self.estado = aplicar_delta(self.estado, {"rodada": nova_rodada})

        # --- GATILHO DE DUELO TÁTICO ---
        # Se houve movimentação de invasores e algum deles entrou em zona interna da fortaleza
        if carta_tipo == "mover":
            zonas_internas = ["carpintaria", "curtume", "fundicao", "patio", "camara_central"]
            for zona in zonas_internas:
                # Se há novos invasores que penetraram esta zona interna
                if self.estado.get("invasores", {}).get(zona, 0) > 0:
                    inseto_id = self.estado.get("castas_invasoras", {}).get(zona, "formiga_correicao")
                    
                    # Pausa o tabuleiro e salva o estado do jogo
                    self.game.castas_state_salvo = self
                    
                    # Remove a unidade do invasor da contagem do tabuleiro (será resolvida no duelo de cartas)
                    novos_inv = dict(self.estado["invasores"])
                    novos_inv[zona] = max(0, novos_inv.get(zona, 0) - 1)
                    self.estado = aplicar_delta(self.estado, {"invasores": novos_inv})
                    
                    # Inicializa o Duelo de Cartas 1v1 contra o Filho do Imperador usando a casta invasora
                    from src.states.duelo.state import DueloState
                    from src.config import ESTADO_JOGO_DUELO
                    
                    duelo = DueloState(self.game)
                    duelo.num_adversarios = 1
                    duelo.controle_filhos = self.controle_filhos
                    duelo.configurar_duelo_adversarios()
                    
                    # Sabor temático de invasão
                    duelo.maos["Filho 1"] = [inseto_id] * 3
                    duelo.hordas["Filho 1"] = [inseto_id]
                    duelo.zona_invasao_origem = zona
                    duelo.modo_retorno_cerco = True
                    
                    self.game.duelo_state = duelo
                    self.game.estado_jogo = ESTADO_JOGO_DUELO
                    
                    self._push("⚠️ INVASÃO", f"O oponente invadiu {zona.upper()} com a casta {inseto_id.upper()}!")
                    self._push("SISTEMA", "Resolva o Duelo de Cartas para defender a fortaleza!")
                    return # Interrompe fluxo até o duelo terminar

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
