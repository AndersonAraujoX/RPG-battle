"""
ia_heroi.py — Inteligência Artificial do Filho do Imperador no modo Cerco.

O Príncipe Lysander age autonomamente no turno dele, tomando decisões
táticas baseadas no estado do cerco:
  1. Joga cartas da mão para ganhar pontos de ação
  2. Decide onde mover (prioriza zonas com inimigos ou recursos)
  3. Ataca inimigos adjacentes se possível
  4. Trabalha/escava se estiver em zona produtiva e sem ameaças
"""
from __future__ import annotations
import random
import math
import time as _time


def _distancia(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class IAFilhoImperador:
    """Motor de decisão tática para o Filho do Imperador (Príncipe Lysander).

    Chamado ao início do turno do Príncipe para executar ações de forma
    autônoma: joga cartas, move, ataca ou trabalha.
    """

    # Delay entre ações para que o jogador possa acompanhar (em frames)
    DELAY_ENTRE_ACOES = 40

    def __init__(self, cerco_state):
        self.state = cerco_state
        self._fila_acoes = []          # lista de callables a serem executados
        self._timer_acao = 0
        self._executando = False

    # ── ENTRADA PRINCIPAL ─────────────────────────────────────────────
    def iniciar_turno(self):
        """Chamado quando começa o turno do Príncipe. Planeja todas as ações."""
        s = self.state
        principe = s.heroi_atual
        if not principe:
            return

        s._push("IA", f"⚔️ Príncipe Lysander age autonomamente!")
        s._feedback("⚔️ Lysander está planejando sua ação...", (180, 140, 255))

        self._fila_acoes = []
        self._executando = True
        self._timer_acao = self.DELAY_ENTRE_ACOES

        # Planejar a sequência completa de ações
        self._planejar_acoes()

    def _planejar_acoes(self):
        """Monta a fila de ações baseado na avaliação do estado."""
        s = self.state
        e = s.estado
        principe = s.heroi_atual

        # Passo 1: jogar todas as cartas da mão
        mao = list(e.get("mao", []))
        for carta in mao:
            c = carta.copy()  # captura por valor
            self._fila_acoes.append(lambda carta=c: self._jogar_carta(carta))

        # Passo 2: decidir ação principal
        self._fila_acoes.append(self._decidir_acao_principal)

        # Passo 3: finalizar turno
        self._fila_acoes.append(self._finalizar_turno)

    def update(self):
        """Chamado a cada frame durante o turno do Príncipe. Processa a fila."""
        if not self._executando or not self._fila_acoes:
            return

        self._timer_acao -= 1
        if self._timer_acao > 0:
            return

        # Executar próxima ação
        acao = self._fila_acoes.pop(0)
        acao()
        self._timer_acao = self.DELAY_ENTRE_ACOES

        # Verificar se terminou
        if not self._fila_acoes:
            self._executando = False

    @property
    def esta_executando(self):
        return self._executando

    # ── JOGAR CARTA ───────────────────────────────────────────────────
    def _jogar_carta(self, carta):
        from ...cerco_isectum import processar_carta, aplicar_delta
        s = self.state
        e = s.estado

        mao_atual = list(e.get("mao", []))
        if carta not in mao_atual:
            return  # já foi removida

        try:
            delta, logs = processar_carta(e, carta)
            mao_nova = [c for c in mao_atual if c is not carta and c != carta]
            delta["mao"] = mao_nova
            s.estado = aplicar_delta(e, delta)
            for tipo, msg in logs:
                s._push(tipo, msg)
            s._push("IA", f"🃏 Lysander jogou: {carta.get('nome', '?')} [{carta.get('simbolo', '?')}]")
        except Exception as exc:
            s._push("IA", f"Carta ignorada: {exc}")

        s.map_backbuffer_sujo = True

    # ── DECISÃO PRINCIPAL ─────────────────────────────────────────────
    def _decidir_acao_principal(self):
        """Decide entre: atacar inimigo, mover para ameaça, trabalhar, escavar."""
        s = self.state
        e = s.estado
        principe = s.heroi_atual
        if not principe:
            return

        px, py = principe.pos_x, principe.pos_y
        inimigos_vivos = [
            p for p in s.motor.combatentes
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0
        ]

        # Tenta atacar inimigo adjacente (corpo-a-corpo)
        if self._tentar_atacar(px, py, inimigos_vivos):
            return

        # Tenta mover em direção ao inimigo mais próximo que ameaça zonas internas
        mov = e.get("pontos_movimento", 0)
        if mov > 0 and inimigos_vivos:
            self._mover_para_objetivo(px, py, inimigos_vivos)
            return

        # Se estiver em zona de trabalho, trabalha
        if e.get("pontos_trabalho", 0) > 0:
            s._processar_acoes_automaticas()
            return

        # Se estiver em zona de escavação, escava
        if e.get("pontos_escavacao", 0) > 0:
            s._processar_acoes_automaticas()
            return

        s._push("IA", "🤔 Lysander espera — sem ações úteis disponíveis.")

    def _tentar_atacar(self, px, py, inimigos_vivos) -> bool:
        """Tenta atacar o inimigo mais fraco ao alcance. Retorna True se atacou."""
        from ...juiz_combate import resolver_melee, resolver_distancia
        from ...cerco_isectum import aplicar_delta

        s = self.state
        principe = s.heroi_atual
        if not principe:
            return False

        alcance = getattr(principe, "alcance", 1)
        alvos_alcance = [
            p for p in inimigos_vivos
            if _distancia(px, py, p.pos_x, p.pos_y) <= alcance + 0.5
        ]

        if not alvos_alcance:
            return False

        # Prioriza o inimigo com menos HP (mata o mais fraco primeiro)
        alvo = min(alvos_alcance, key=lambda p: p.hp_atual)

        try:
            if alcance <= 1:
                resultado = resolver_melee(principe, alvo, s.estado, s.motor.tabuleiro)
            else:
                resultado = resolver_distancia(principe, alvo, s.estado, s.motor.tabuleiro)

            for tipo, msg in resultado.get("logs", []):
                s._push(tipo, msg)

            if alvo.hp_atual <= 0:
                s._push("IA", f"💀 Lysander abateu {alvo.nome}!")
                s.motor.combatentes.remove(alvo)
                if hasattr(s.motor, "time_b") and alvo in s.motor.time_b:
                    s.motor.time_b.remove(alvo)
                # Remove do tabuleiro
                tab = s.motor.tabuleiro
                if (0 <= alvo.pos_y < len(tab.grid) and
                        0 <= alvo.pos_x < len(tab.grid[0]) and
                        tab.grid[alvo.pos_y][alvo.pos_x] is alvo):
                    tab.grid[alvo.pos_y][alvo.pos_x] = None
                s.map_backbuffer_sujo = True
            else:
                s._push("IA", f"⚔️ Lysander atacou {alvo.nome} ({alvo.hp_atual}/{alvo.hp_max} HP restante)!")
        except Exception as exc:
            # Fallback: ataque simples
            dano = random.randint(8, 18)
            alvo.hp_atual = max(0, alvo.hp_atual - dano)
            s._push("IA", f"⚔️ Lysander causou {dano} de dano em {alvo.nome}!")
            if alvo.hp_atual <= 0:
                s._push("IA", f"💀 {alvo.nome} foi derrotado!")

        s.map_backbuffer_sujo = True
        return True

    def _mover_para_objetivo(self, px, py, inimigos_vivos):
        """Move o Príncipe em direção à maior ameaça ou zona estratégica."""
        from ...cerco_isectum import aplicar_delta
        from ...resolvedor_acoes import (
            obter_zona_por_coordenada, obter_celulas_alcancaveis,
            executar_mover, validar_mover,
        )

        s = self.state
        e = s.estado
        principe = s.heroi_atual
        if not principe:
            return

        mov = e.get("pontos_movimento", 0)
        if mov <= 0:
            return

        # Prioridade: inimigo em zona interna (muralha ou patio) mais próximo
        zonas_prioritarias = {"patio", "muralha_norte", "muralha_sul",
                              "muralha_oeste", "muralha_leste",
                              "torre_nw", "torre_ne", "torre_sw", "torre_se"}

        inimigos_internos = [
            p for p in inimigos_vivos
            if obter_zona_por_coordenada(p.pos_x, p.pos_y) in zonas_prioritarias
        ]

        alvos = inimigos_internos if inimigos_internos else inimigos_vivos
        if not alvos:
            return

        # Alvo mais próximo
        alvo = min(alvos, key=lambda p: _distancia(px, py, p.pos_x, p.pos_y))
        dest_x, dest_y = alvo.pos_x, alvo.pos_y

        # Obter células alcançáveis
        alcancaveis = obter_celulas_alcancaveis(s.motor, (px, py), mov)
        if not alcancaveis:
            return

        # Escolher a célula alcançável mais próxima do alvo (sem ocupar a célula do alvo)
        candidatas = [
            (cx, cy) for (cx, cy) in alcancaveis
            if s.motor.tabuleiro.get_personagem_em(cx, cy) is None
            and (cx, cy) != (dest_x, dest_y)
        ]
        if not candidatas:
            return

        melhor = min(candidatas, key=lambda c: _distancia(c[0], c[1], dest_x, dest_y))
        novo_x, novo_y = melhor

        # Executar movimento
        ok, msg_v = validar_mover(e, novo_x, novo_y)
        if not ok:
            # Tenta mover sem validação formal (fallback direto)
            tab = s.motor.tabuleiro
            if tab.grid[py][px] is principe:
                tab.grid[py][px] = None
            tab.grid[novo_y][novo_x] = principe
            principe.pos_x = novo_x
            principe.pos_y = novo_y

            nova_zona = obter_zona_por_coordenada(novo_x, novo_y) or "camara_central"
            s.estado = aplicar_delta(e, {
                "heroi_x": novo_x, "heroi_y": novo_y,
                "pos_heroi": nova_zona,
                "pontos_movimento": 0,
            })
        else:
            custo = _distancia(px, py, novo_x, novo_y) * 3
            delta, logs = executar_mover(e, novo_x, novo_y, int(custo))
            s.estado = aplicar_delta(e, delta)
            for tipo, msg in logs:
                s._push(tipo, msg)

            tab = s.motor.tabuleiro
            if tab.grid[py][px] is principe:
                tab.grid[py][px] = None
            tab.grid[novo_y][novo_x] = principe
            principe.pos_x = novo_x
            principe.pos_y = novo_y

        nova_zona = obter_zona_por_coordenada(novo_x, novo_y) or "camara_central"
        s._push("IA", f"🚶 Lysander moveu-se para ({novo_x}, {novo_y}) [{nova_zona}]")
        s.map_backbuffer_sujo = True

        # Tenta atacar após mover
        inimigos_vivos_atuais = [
            p for p in s.motor.combatentes
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0
        ]
        self._tentar_atacar(novo_x, novo_y, inimigos_vivos_atuais)

    # ── FIM DO TURNO ──────────────────────────────────────────────────
    def _finalizar_turno(self):
        """Limpa mão restante e passa para a próxima fase."""
        from ...cerco_isectum import aplicar_delta

        s = self.state
        e = s.estado

        # Descarta cartas restantes da mão
        mao = list(e.get("mao", []))
        descarte = list(e.get("descarte", [])) + mao
        s.estado = aplicar_delta(e, {"mao": [], "descarte": descarte})

        s._push("IA", "✅ Lysander encerrou seu turno.")
        s._feedback("✅ Lysander encerrou o turno.", (100, 255, 140))

        # Delega para o fluxo normal de fim de turno
        # Força mão vazia para que _fim_turno_heroi não bloqueie
        s.estado["mao"] = []
        s._fim_turno_heroi()
