"""
bot_heroi.py — Bot AutoPlay para o Modo Cerco contra Isectum.

O BotHeroi assume o controle de todos os heróis jogáveis automaticamente,
simulando as decisões de um jogador com uma IA heurística simples baseada
em prioridades. Ideal para testes e demonstrações automáticas.

Prioridades de ação:
  1. Jogar todas as cartas da mão (gera PM/PT/PE)
  2. Atacar inimigos em alcance melee
  3. Mover em direção ao inimigo mais próximo ou zona mais ameaçada
  4. Trabalhar (alocar recursos em upgrades)
  5. Escavar (remover pedregulhos do pátio)
  6. Encerrar o turno

Fases especiais:
  - FASE_AMEACA       → resolve automaticamente a carta de ameaça
  - REPOVOAR_MERCADO → escolhe carta aleatória para slots vazios
  - TURNO_FILHO_IMPERADOR → aguarda a IA inimiga terminar (não interfere)
"""
from __future__ import annotations
import random

# ── Velocidades predefinidas (em frames de delay entre ações) ──────────────
VELOCIDADES = {
    "lento":  90,    # ~1.5 s por ação a 60fps
    "normal": 45,    # ~0.75 s por ação
    "rapido": 12,    # ~0.2 s por ação
}


class BotHeroi:
    """Controlador automático de heróis para o Modo Cerco.

    Instanciado dentro do CercoState quando AutoPlay é ativado.
    Chame ``update()`` a cada frame dentro do ``CercoState.update()``.
    """

    def __init__(self, cerco_state, velocidade: str = "normal"):
        self.state = cerco_state
        self.velocidade = velocidade
        self._timer = 0          # countdown até a próxima ação
        self._fila: list = []    # fila de callables a executar
        self._esperando = False  # aguardando animação de caminhada etc.

    # ── Propriedade pública ────────────────────────────────────────────────
    @property
    def delay(self) -> int:
        return VELOCIDADES.get(self.velocidade, 45)

    # ── Entry-point principal ─────────────────────────────────────────────
    def update(self):
        """Chamado a cada frame pelo CercoState.update() quando AutoPlay ativo."""
        s = self.state

        # Não age se jogo já terminou
        if s.estado.get("vitoria") or s.estado.get("derrota"):
            return

        # Não age enquanto herói está em movimento ou arrastando carta
        if getattr(s, "walk_anim", None):
            return

        # Não interfere no turno inimigo (Filho do Imperador)
        if s.fase == "TURNO_FILHO_IMPERADOR":
            return

        # Tick de delay
        if self._timer > 0:
            self._timer -= 1
            return

        # Executa próxima ação da fila, ou planeja novo conjunto de ações
        if self._fila:
            acao = self._fila.pop(0)
            try:
                acao()
            except Exception as exc:
                s._push("BOT", f"[BOT] Erro interno: {exc}")
            self._timer = self.delay
        else:
            self._planejar_acoes()

    # ── Planejamento ──────────────────────────────────────────────────────
    def _planejar_acoes(self):
        """Decide quais ações enfileirar com base na fase e estado atual."""
        s = self.state
        fase = s.fase

        if fase == "FASE_AMEACA":
            self._fila.append(self._resolver_ameaca)

        elif fase == "REPOVOAR_MERCADO":
            self._fila.append(self._repovoar_mercado)

        elif fase == "ESCOLHER_ACAO_CARTA":
            self._fila.append(self._resolver_escolha_carta)

        elif fase in ("JOGAR_CARTA", "ACAO_LIVRE"):
            # 1. Jogar cartas restantes na mão (uma por tick — sempre joga a [0])
            mao = s.estado.get("mao", [])
            for _ in range(len(mao)):
                self._fila.append(self._jogar_proxima_carta)

            # 2. Recrutar mercenários (se tiver cristais suficientes)
            self._fila.append(self._tentar_recrutar_mercenarios)

            # 3. Atacar inimigos acessíveis ou invasores em zonas
            self._fila.append(self._tentar_atacar)

            # 4. Mover em direção ao objetivo mais relevante
            self._fila.append(self._tentar_mover)

            # 5. Trabalhar (alocar recursos)
            self._fila.append(self._tentar_trabalhar)

            # 6. Escavar pedregulhos
            self._fila.append(self._tentar_escavar)

            # 7. Encerrar turno
            self._fila.append(self._encerrar_turno)

        else:
            # Fase desconhecida – pequena pausa antes de tentar de novo
            self._timer = self.delay * 2

    # ── Ações individuais ─────────────────────────────────────────────────

    def _resolver_escolha_carta(self):
        """Resolve o modal de escolha de ação de carta (Andar/Coletar/Ambos/Atacar)."""
        s = self.state
        if s.fase == "ESCOLHER_ACAO_CARTA":
            idx = getattr(s, "idx_carta_sendo_jogada", -1)
            if idx >= 0:
                s._aplicar_acao_carta(idx, "ambos")
            s.fase = "ACAO_LIVRE"

    def _resolver_ameaca(self):
        """Resolve automaticamente a carta de ameaça (Fase de Ameaça)."""
        s = self.state
        if s.fase == "FASE_AMEACA" and s.carta_cerco:
            s._push("BOT", "[BOT] Resolvendo carta de ameaça automaticamente.")
            s._resolver_carta_cerco()

    def _repovoar_mercado(self):
        """Preenche slots vazios do mercado com cartas aleatórias."""
        s = self.state
        from ...cerco_isectum import aplicar_delta, CARTAS_UPGRADE
        e = s.estado

        slots = [dict(sl) for sl in e["slots_upgrade"]]
        cartas_disponiveis = list(CARTAS_UPGRADE)
        random.shuffle(cartas_disponiveis)

        alterou = False
        for slot in slots:
            if slot.get("adquirido") or slot.get("carta_id") is None:
                if cartas_disponiveis:
                    carta = cartas_disponiveis.pop(0)
                    slot["nome"]     = carta["nome"]
                    slot["simbolo"]  = carta["simbolo"]
                    slot["carta_id"] = carta["id"]
                    slot["custo"]    = dict(carta["custo"])
                    slot["descricao"] = carta.get("descricao", "")
                    slot["adquirido"] = False
                    slot["bloqueado"] = False
                    slot["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
                    s._push("BOT", f"[BOT] Repovoando slot {slot['id']+1} com [{carta['nome']}].")
                    alterou = True

        if alterou:
            s.estado = aplicar_delta(e, {"slots_upgrade": slots})

        # Finaliza a fase de reposição
        s._concluir_fim_turno_completo()
        s._push("BOT", "[BOT] Reposição concluída. Avançando turno.")

    def _jogar_proxima_carta(self):
        """Joga a próxima carta da mão (sempre índice 0, já que a lista encolhe)."""
        s = self.state
        mao = s.estado.get("mao", [])
        if not mao:
            return

        carta = mao[0]

        # Cartas de orc/invasor: descarta (invade zona aleatória)
        if carta.get("tipo") in ("orc", "invasor"):
            s._push("BOT", f"[BOT] Descartando carta invasora: [{carta.get('nome', '?')}].")
            s._jogar_carta_invasao(0)
            return

        # Cartas normais: joga pela lógica padrão do hero.py
        s._push("BOT", f"[BOT] Jogando carta [{carta.get('nome', '?')}].")
        s._jogar_carta(0)

    def _tentar_atacar(self):
        """Procura inimigos vivos no alcance do herói no grid e executa ataque físico."""
        s = self.state
        e = s.estado

        heroi_obj = getattr(s, "heroi_atual", None)
        if heroi_obj and hasattr(heroi_obj, "pos_x") and hasattr(heroi_obj, "pos_y"):
            hx, hy = heroi_obj.pos_x, heroi_obj.pos_y
            e["heroi_x"] = hx
            e["heroi_y"] = hy
        else:
            hx = e.get("heroi_x", 9)
            hy = e.get("heroi_y", 9)

        alcance_heroi = getattr(heroi_obj, "alcance", 1) if heroi_obj else 1

        # 1. Busca inimigos vivos no grid 2D (combate físico direto)
        inimigos_vivos = [
            p for p in s.motor.combatentes
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0
        ]
        if inimigos_vivos:
            inimigos_vivos.sort(key=lambda ini: abs(ini.pos_x - hx) + abs(ini.pos_y - hy))
            for ini in inimigos_vivos:
                dist = abs(ini.pos_x - hx) + abs(ini.pos_y - hy)
                if dist <= alcance_heroi:
                    from ...resolvedor_acoes import obter_zona_por_coordenada
                    zona_ini = obter_zona_por_coordenada(ini.pos_x, ini.pos_y) or "patio"
                    s._push("BOT", f"⚔️ [BOT] Atacando [{ini.nome}] (HP: {ini.hp_atual}/{ini.hp_max}) na célula ({ini.pos_x}, {ini.pos_y})!")
                    s._selecionar_modo("atacar")
                    s._on_cell_click(ini.pos_x, ini.pos_y)
                    return True

        # 2. Ataca invasores por zona apenas como fallback se não houver unidade 2D no alcance
        invasores = e.get("invasores", {})
        pos_heroi = e.get("pos_heroi", "camara_central")
        zonas_com_invasores = [z for z, n in invasores.items() if n > 0]

        zona_alvo = pos_heroi if pos_heroi in zonas_com_invasores else (zonas_com_invasores[0] if zonas_com_invasores else None)
        if zona_alvo:
            from ...resolvedor_acoes import ZONAS_GRID
            if zona_alvo in ZONAS_GRID:
                x1, y1, x2, y2 = ZONAS_GRID[zona_alvo]
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                s._push("BOT", f"[BOT] Atacando invasores na zona [{zona_alvo}].")
                s._selecionar_modo("atacar")
                s._on_cell_click(cx, cy)
                return True
        return False

    def _tentar_mover(self):
        """Move o herói em direção ao inimigo mais próximo, oficina necessária ou zona ameaçada."""
        s = self.state
        e = s.estado

        pm = e.get("pontos_movimento", 0)
        if pm <= 0:
            return

        # 1. Obtém a posição real e exata do herói no tabuleiro
        heroi_obj = getattr(s, "heroi_atual", None)
        if heroi_obj and hasattr(heroi_obj, "pos_x") and hasattr(heroi_obj, "pos_y"):
            hx, hy = heroi_obj.pos_x, heroi_obj.pos_y
            e["heroi_x"] = hx
            e["heroi_y"] = hy
        else:
            hx = e.get("heroi_x", 9)
            hy = e.get("heroi_y", 9)

        # 2. Recalcula células realmente alcançáveis com os PMs atuais
        from ...resolvedor_acoes import obter_celulas_alcancaveis, ZONAS_GRID, OFICINAS
        alcancaveis = obter_celulas_alcancaveis(s.motor, (hx, hy), pm)
        s.alcancaveis = alcancaveis

        if not alcancaveis:
            return

        # 3. Determina a coordenada do alvo desejado
        alvo_x, alvo_y = hx, hy

        # Alvo A: Inimigos vivos no tabuleiro (prioridade máxima se adjacente ou próximo)
        inimigos_vivos = [
            p for p in s.motor.combatentes
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0
        ]

        # Alvo B: Se tiver Pontos de Trabalho (PT > 0), prioriza mover para Oficina útil
        pt = e.get("pontos_trabalho", 0)
        oficina_alvo = None

        if pt > 0:
            # Descobre qual recurso é mais necessário nos upgrades
            recursos_necessarios = {"madeira": 0, "couro": 0, "metal": 0}
            for slot in e.get("slots_upgrade", []):
                if not slot.get("adquirido") and not slot.get("bloqueado"):
                    c_base = slot.get("custo", {})
                    aloc = slot.get("recursos_alocados", {})
                    for r in ["madeira", "couro", "metal"]:
                        falta = c_base.get(r, 0) - aloc.get(r, 0)
                        if falta > 0:
                            recursos_necessarios[r] += falta

            rec_prioridade = max(recursos_necessarios, key=lambda k: recursos_necessarios[k])
            if recursos_necessarios[rec_prioridade] > 0:
                for of_nome, of_rec in OFICINAS.items():
                    if of_rec == rec_prioridade and of_nome in ZONAS_GRID:
                        oficina_alvo = of_nome
                        break
            if not oficina_alvo:
                # Se nenhum upgrade específico precisa, escolhe qualquer oficina
                oficina_alvo = "carpintaria"

        # Alvo C: Se tiver Pontos de Escavação (PE > 0) e pedregulhos no Pátio, move para o Pátio!
        pe = e.get("pontos_escavacao", 0)
        pedregulhos = e.get("pedregulhos", 0)
        patio_alvo = "patio" if (pe > 0 and pedregulhos > 0) else None

        if inimigos_vivos:
            mais_proximo = min(
                inimigos_vivos,
                key=lambda ini: abs(ini.pos_x - hx) + abs(ini.pos_y - hy)
            )
            alvo_x, alvo_y = mais_proximo.pos_x, mais_proximo.pos_y
        elif oficina_alvo and oficina_alvo in ZONAS_GRID:
            x1, y1, x2, y2 = ZONAS_GRID[oficina_alvo]
            alvo_x = (x1 + x2) // 2
            alvo_y = (y1 + y2) // 2
        elif patio_alvo and patio_alvo in ZONAS_GRID:
            x1, y1, x2, y2 = ZONAS_GRID[patio_alvo]
            alvo_x = (x1 + x2) // 2
            alvo_y = (y1 + y2) // 2
        else:
            # Alvo D: Zona com mais invasores
            invasores = e.get("invasores", {})
            zonas_ameacadas = [(z, n) for z, n in invasores.items() if n > 0]
            if zonas_ameacadas:
                zona_alvo = max(zonas_ameacadas, key=lambda x: x[1])[0]
                if zona_alvo in ZONAS_GRID:
                    x1, y1, x2, y2 = ZONAS_GRID[zona_alvo]
                    alvo_x = (x1 + x2) // 2
                    alvo_y = (y1 + y2) // 2

        # Se o herói já está no alvo, não precisa mover
        if (hx, hy) == (alvo_x, alvo_y):
            return

        # 4. Escolhe a célula alcançável que aproxima o herói do alvo
        melhor_celula = min(
            alcancaveis.keys(),
            key=lambda c: abs(c[0] - alvo_x) + abs(c[1] - alvo_y)
        )
        nx, ny = melhor_celula

        # 5. Executa a movimentação
        s._push("BOT", f"[BOT] Movendo herói para ({nx}, {ny}).")
        s._selecionar_modo("mover")
        s._on_cell_click(nx, ny)

    def _tentar_trabalhar(self):
        """Aplica recursos depositados e trabalha em oficinas para adquirir upgrades de cartas."""
        s = self.state
        e = s.estado

        from ...resolvedor_acoes import CUSTO_ADICIONAL_SLOT, OFICINAS, obter_zona_por_coordenada, validar_alocar_recurso, executar_alocar_recurso, validar_trabalhar, executar_trabalhar
        from ...cerco_isectum import aplicar_delta

        # A) Transfere recursos já depositados (banco de recursos) para os slots de upgrade
        dep = dict(e.get("recursos_depositados", {}))
        slots = [dict(sl) for sl in e.get("slots_upgrade", [])]
        mudou = False

        for slot in slots:
            if slot.get("adquirido") or slot.get("bloqueado"):
                continue
            sid = slot["id"]
            custo_base = slot.get("custo", {})
            custo_adicional = CUSTO_ADICIONAL_SLOT.get(sid, {})
            alocados = dict(slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0}))

            transferiu = False
            for r_type in ["madeira", "couro", "metal"]:
                req = custo_base.get(r_type, 0) + custo_adicional.get(r_type, 0)
                tem_alocado = alocados.get(r_type, 0)
                falta = req - tem_alocado
                if falta > 0 and dep.get(r_type, 0) > 0:
                    tr = min(falta, dep.get(r_type, 0))
                    dep[r_type] -= tr
                    alocados[r_type] += tr
                    transferiu = True
                    mudou = True

            if transferiu:
                slot["recursos_alocados"] = alocados

            # Verifica se completou todos os recursos do upgrade
            custo_total = {
                r: custo_base.get(r, 0) + custo_adicional.get(r, 0)
                for r in ["madeira", "couro", "metal"]
            }
            if all(alocados.get(r, 0) >= q for r, q in custo_total.items() if q > 0):
                s.estado = aplicar_delta(e, {"recursos_depositados": dep, "slots_upgrade": slots})
                s._push("BOT", f"[BOT] Upgrade [{slot['nome']}] completado com recursos depositados!")
                s._adquirir_upgrade_direto(sid)
                e = s.estado
                slots = [dict(sl) for sl in e.get("slots_upgrade", [])]

        if mudou:
            s.estado = aplicar_delta(e, {"recursos_depositados": dep, "slots_upgrade": slots})
            e = s.estado

        # B) Se tiver Pontos de Trabalho (PT > 0) e o herói estiver em uma Oficina, trabalha!
        pt = e.get("pontos_trabalho", 0)
        if pt <= 0:
            return

        hx = e.get("heroi_x", 9)
        hy = e.get("heroi_y", 9)
        zona_atual = obter_zona_por_coordenada(hx, hy)

        if zona_atual in OFICINAS:
            recurso_produzido = OFICINAS[zona_atual]
            trabalhou_direto = False

            for slot in e.get("slots_upgrade", []):
                if slot.get("adquirido") or slot.get("bloqueado"):
                    continue
                sid = slot["id"]
                ok, recurso, msg = validar_alocar_recurso(e, sid, pt)
                if ok and recurso == recurso_produzido:
                    while e.get("pontos_trabalho", 0) > 0:
                        ok_step, rec_step, _ = validar_alocar_recurso(e, sid, e["pontos_trabalho"])
                        if not ok_step:
                            break
                        delta, logs = executar_alocar_recurso(e, sid, rec_step)
                        s.estado = aplicar_delta(e, delta)
                        e = s.estado
                        for t, m in logs:
                            s._push(t, m)
                        s._push("BOT", f"[BOT] Trabalhou em [{zona_atual}]: alocou {rec_step} em [{slot['nome']}].")

                        # Checa se completou o upgrade
                        c_base = slot.get("custo", {})
                        c_add = CUSTO_ADICIONAL_SLOT.get(sid, {})
                        aloc = e["slots_upgrade"][sid].get("recursos_alocados", {})
                        if all(aloc.get(r, 0) >= (c_base.get(r, 0) + c_add.get(r, 0)) for r in ["madeira", "couro", "metal"]):
                            s._push("BOT", f"[BOT] ⭐ Upgrade [{slot['nome']}] adquirido!")
                            s._adquirir_upgrade_direto(sid)
                            e = s.estado
                            break
                    trabalhou_direto = True
                    s.map_backbuffer_sujo = True
                    break

            # Se não alocou direto em slot, produz e deposita o recurso na reserva da fortaleza
            if not trabalhou_direto and e.get("pontos_trabalho", 0) > 0:
                ok, rec, msg = validar_trabalhar(e, e["pontos_trabalho"])
                if ok:
                    delta, logs = executar_trabalhar(e, rec, e["pontos_trabalho"])
                    s.estado = aplicar_delta(e, delta)
                    for t, m in logs:
                        s._push(t, m)
                    s._push("BOT", f"[BOT] Coletou recurso na [{zona_atual}]: +{e['pontos_trabalho']}x {rec}.")
                    s.map_backbuffer_sujo = True

    def _tentar_escavar(self):
        """Usa pontos de escavação para remover pedregulhos."""
        s = self.state
        e = s.estado

        pe = e.get("pontos_escavacao", 0)
        pedregulhos = e.get("pedregulhos", 0)
        if pe <= 0 or pedregulhos <= 0:
            return

        from ...resolvedor_acoes import validar_escavar, executar_escavar
        from ...cerco_isectum import aplicar_delta

        ok, qtd, msg = validar_escavar(e, pe)
        if ok:
            delta, logs = executar_escavar(e, qtd)
            s.estado = aplicar_delta(e, delta)
            for t, m in logs:
                s._push(t, m)
            s._push("BOT", f"[BOT] Escavou {qtd} pedregulho(s) do pátio.")
            s.map_backbuffer_sujo = True
        else:
            s._push("BOT", f"[BOT] Escavação não possível: {msg}")

    def _encerrar_turno(self):
        """Descarta cartas restantes e encerra o turno do herói."""
        s = self.state

        # Se ainda há cartas na mão, descarta todas antes de encerrar
        mao = s.estado.get("mao", [])
        if mao:
            from ...cerco_isectum import aplicar_delta
            desc = list(s.estado["descarte"]) + list(mao)
            s.estado = aplicar_delta(s.estado, {"mao": [], "descarte": desc})
            s._push("BOT", f"[BOT] Descartou {len(mao)} carta(s) restante(s) da mão.")

        s._push("BOT", "[BOT] Encerrando turno do herói.")
        s._fim_turno_heroi()

    # ── RECRUTAMENTO DE MERCENÁRIOS ───────────────────────────────────────
    def _tentar_recrutar_mercenarios(self):
        """Recruta e posiciona mercenários taticamente com base nos Cristais Roxos.

        Estratégia Tática por Classe:
          1. EMERGÊNCIA (Salas Internas Invadidas):
             - Se a Câmara Central ou Oficinas forem invadidas, recruta Guerreiro Melee (5💎)
               diretamente na sala invadida para barrar o avanço inimigo!
          2. MINERADORES (4💎):
             - Recrutado no Pátio/Escavação apenas se pedregulhos > 0 e se houver menos de 2
               mineradores ativos, focando na desobstrução das rotas de fuga.
          3. ARQUEIROS (7💎):
             - Posicionados prioritariamente nas Torres dos Cantos (NW, NE, SW, SE) para
               alcance panorâmico elevado. Se ocupadas, em muralhas voltadas aos inimigos.
          4. GUERREIROS MELEE / GUARDAS (5💎):
             - Posicionados nas muralhas mais ameaçadas ou em pontos de estrangulamento.
        """
        import random as _rnd
        s = self.state
        e = s.estado

        invasores = e.get("invasores", {})

        # Detecta invasão interna de emergência (câmara central ou oficinas)
        zonas_internas_brecha = [z for z in ("camara_central", "carpintaria", "curtume", "fundicao", "patio") if invasores.get(z, 0) > 0]
        is_emergencia = len(zonas_internas_brecha) > 0

        # Reserva de segurança dinâmica: 1 se em emergência, 3 em situação normal
        RESERVA_SEGURANCA = 1 if is_emergencia else 3
        cristais = e.get("tesouro", 0)

        if cristais < (4 + RESERVA_SEGURANCA):
            return

        from ...resolvedor_acoes import ZONAS_GRID
        from ...personagens.mercenarios import MercenarioMelee, MercenarioArqueiro, MercenarioMinerador
        from ...cerco_isectum import aplicar_delta

        tab = s.motor.tabuleiro

        def _celulas_livres_zona(zona_id):
            """Retorna lista de células livres em uma zona."""
            if zona_id not in ZONAS_GRID:
                return []
            x1, y1, x2, y2 = ZONAS_GRID[zona_id]
            livres = []
            for gy in range(y1, y2 + 1):
                for gx in range(x1, x2 + 1):
                    if (0 <= gx < tab.largura and 0 <= gy < tab.altura
                            and tab.grid[gy][gx] is None
                            and tab.get_terrain_em(gx, gy) != "parede"):
                        livres.append((gx, gy))
            return livres

        def _recrutar(classe, custo, cx, cy, tipo_nome):
            """Efetua o recrutamento do mercenário na posição (cx, cy)."""
            novo = classe(nivel=3)
            sucesso = tab.adicionar_personagem(novo, cx, cy)
            if sucesso:
                s.motor.time_a.append(novo)
                s.motor.combatentes.append(novo)
                s.estado = aplicar_delta(s.estado, {
                    "tesouro": max(0, s.estado.get("tesouro", 0) - custo)
                })
                s._push("BOT", f"[BOT] Recrutou {tipo_nome} em ({cx},{cy}) por {custo}💎.")
                s._feedback(f"🤖 Bot recrutou {tipo_nome}!", (140, 220, 140))
                s.map_backbuffer_sujo = True
                return True
            return False

        # ── 1. EMERGÊNCIA: Defesa Corpo a Corpo em Brechas Internas (Guerreiro Melee - 5💎)
        if is_emergencia and cristais >= (5 + RESERVA_SEGURANCA):
            for zona in zonas_internas_brecha:
                livres = _celulas_livres_zona(zona)
                if livres:
                    cx, cy = livres[0]
                    if _recrutar(MercenarioMelee, 5, cx, cy, "Guarda de Emergência 🛡️"):
                        return

        # ── 2. MINERADORES (4💎) → Pátio/Escavação
        pedregulhos = e.get("pedregulhos", 0)
        mineradores_ativos = sum(1 for p in s.motor.combatentes if getattr(p, "classe_nome", None) == "Minerador" and p.hp_atual > 0)

        if cristais >= (4 + RESERVA_SEGURANCA) and pedregulhos > 0 and mineradores_ativos < 2:
            livres_patio = _celulas_livres_zona("patio")
            if livres_patio:
                cx, cy = livres_patio[0]
                if _recrutar(MercenarioMinerador, 4, cx, cy, "Minerador ⛏️"):
                    return

        # ── 3. ARQUEIROS (7💎) → Torres dos Cantos Elevadas ou Muralhas Voltadas aos Inimigos
        if cristais >= (7 + RESERVA_SEGURANCA):
            # Prioridade 3A: Torres dos Cantos
            torres = ["torre_nw", "torre_ne", "torre_sw", "torre_se"]
            mapa_torre_campo = {
                "torre_nw": ["campo_norte", "campo_oeste"],
                "torre_ne": ["campo_norte", "campo_leste"],
                "torre_sw": ["campo_sul", "campo_oeste"],
                "torre_se": ["campo_sul", "campo_leste"],
            }
            torres.sort(key=lambda t: sum(invasores.get(c, 0) for c in mapa_torre_campo.get(t, [])), reverse=True)

            for torre in torres:
                livres = _celulas_livres_zona(torre)
                if livres:
                    cx, cy = livres[0]
                    if _recrutar(MercenarioArqueiro, 7, cx, cy, "Arqueiro de Torre 🏹"):
                        return

            # Prioridade 3B: Passadiço das Muralhas (se todas as torres estiverem ocupadas)
            muralhas = ["muralha_norte", "muralha_sul", "muralha_leste", "muralha_oeste"]
            muralhas.sort(key=lambda m: invasores.get(m, 0), reverse=True)
            for mur in muralhas:
                livres = _celulas_livres_zona(mur)
                if livres:
                    cx, cy = livres[0]
                    if _recrutar(MercenarioArqueiro, 7, cx, cy, "Arqueiro Muralha 🏹"):
                        return

        # ── 4. GUERREIROS MELEE / GUARDAS (5💎) → Muralhas Ameaçadas ou Pontos de Bloqueio
        if cristais >= (5 + RESERVA_SEGURANCA):
            muralhas = ["muralha_norte", "muralha_sul", "muralha_leste", "muralha_oeste"]
            muralhas.sort(key=lambda m: invasores.get(m, 0), reverse=True)
            for muralha in muralhas:
                livres = _celulas_livres_zona(muralha)
                if livres:
                    cx, cy = livres[0]
                    if _recrutar(MercenarioMelee, 5, cx, cy, "Guarda Muralha 🛡️"):
                        return
