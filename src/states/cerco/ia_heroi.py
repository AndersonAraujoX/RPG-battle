"""
ia_heroi.py — IA do Filho do Imperador no modo Cerco.

O Príncipe Lysander age como INIMIGO COMANDANTE no modo Cerco,
controlando as invasões como se fosse um jogador humano da casta do Imperador.

A cada turno (após os heróis), ele:
  1. Escolhe castas de insetos da sua mão
  2. Decide qual zona atacar (baseado em análise tática)
  3. Envia as tropas para invadir a fortaleza
  4. Usa habilidades especiais das castas

É como se um jogador inimigo estivesse jogando contra você no modo Cerco.
"""
from __future__ import annotations
import random
import math


class IAComandanteImperial:
    """
    IA do Filho do Imperador — age como um jogador adversário no modo Cerco.

    Simula um diretor humano das castas do Imperador, escolhendo
    estratégias de invasão com base no estado atual da fortaleza.
    """

    # Frames de delay entre ações (para o jogador acompanhar)
    DELAY_ACAO = 90   # ~1.5 segundos por ação

    def __init__(self, cerco_state):
        self.state = cerco_state
        self._ativo = False
        self._timer = 0
        self._fila = []          # lista de callables a executar
        self.acoes_por_turno = 3  # número de invasões por turno
        self._acoes_restantes = 0

        # Deck do Filho do Imperador (cartas de castas/insetos)
        from src.cerco_isectum import DADOS_INIMIGOS
        self._deck = list(DADOS_INIMIGOS.keys()) * 2
        random.shuffle(self._deck)
        self._mao = []
        self._comprar_mao(3)     # começa com 3 cartas na mão

        # Anuncio inicial
        self.banner_timer = 0

    # ── MÃO DE CARTAS ────────────────────────────────────────────────
    def _comprar_mao(self, qtd=1):
        """Compra cartas do deck para a mão."""
        for _ in range(qtd):
            if not self._deck:
                from src.cerco_isectum import DADOS_INIMIGOS
                self._deck = list(DADOS_INIMIGOS.keys()) * 2
                random.shuffle(self._deck)
            if self._deck:
                self._mao.append(self._deck.pop())

    # ── ENTRADA DO TURNO ─────────────────────────────────────────────
    def iniciar_turno(self):
        """Chamado quando começa o turno do Filho do Imperador."""
        s = self.state
        self._ativo = True
        self._timer = self.DELAY_ACAO
        self._acoes_restantes = self.acoes_por_turno

        # Compra cartas até ter 3 na mão
        while len(self._mao) < 3:
            self._comprar_mao(1)

        s._push("INIMIGO", "👑 FILHO DO IMPERADOR age! As castas imperiais invadem!")
        s._feedback("⚠ Turno do Filho do Imperador! Prepare-se...", (255, 80, 40))
        self.banner_timer = 180   # ~3 segundos de banner

        # Planeja as ações do turno
        self._fila = []
        for _ in range(self.acoes_por_turno):
            self._fila.append(self._executar_acao)
        self._fila.append(self._finalizar_turno)

    @property
    def esta_ativo(self):
        return self._ativo

    # ── LOOP DE UPDATE ────────────────────────────────────────────────
    def update(self):
        """Chamado a cada frame. Processa a fila de ações com delay."""
        if not self._ativo or not self._fila:
            return

        self._timer -= 1
        if self._timer > 0:
            return

        acao = self._fila.pop(0)
        acao()
        self._timer = self.DELAY_ACAO

        if not self._fila:
            self._ativo = False

    # ── DECISÃO TÁTICA ────────────────────────────────────────────────
    def _executar_acao(self):
        """Executa uma ação: escolhe casta e zona para invasão."""
        s = self.state
        e = s.estado

        if not self._mao:
            self._comprar_mao(2)
        if not self._mao:
            s._push("INIMIGO", "👑 Filho do Imperador sem cartas — aguardando reforços.")
            return

        # Escolhe a casta (carta da mão)
        inseto_id = self._escolher_casta(e)
        if inseto_id not in self._mao:
            inseto_id = self._mao[0]

        # Escolhe a zona de invasão taticamente
        zona = self._escolher_zona_taticamente(e)

        # Executa o spawn da casta
        self._invadir_zona(inseto_id, zona)

        # Remove a carta da mão e coloca no descarte
        if inseto_id in self._mao:
            self._mao.remove(inseto_id)
        self._comprar_mao(1)   # repõe 1 carta

    def _escolher_casta(self, e) -> str:
        """Escolhe qual casta jogar baseado na situação tática."""
        if not self._mao:
            return ""

        # Verifica zonas que precisam de reforço
        invasores = e.get("invasores", {})
        muralhas = ["muralha_norte", "muralha_sul", "muralha_leste", "muralha_oeste"]
        muralha_mais_fraca = min(muralhas, key=lambda z: invasores.get(z, 0))

        # Se uma muralha tem poucos invasores, prioriza castas de ataque
        if invasores.get(muralha_mais_fraca, 0) < 2:
            # Prefere insetos com efeitos de combate
            preferidas = ["tarantula_golias", "viuva_negra", "besouro_rinoceronte",
                          "carrapato_vampiro", "louva_deus"]
            for p in preferidas:
                if p in self._mao:
                    return p

        # Caso contrário, escolhe aleatoriamente com peso
        pesos = {c: 3 if c in ["vespa_cacadora", "formiga_correicao", "enxame_rainha"]
                 else 1 for c in self._mao}
        populacao = list(pesos.keys())
        pesos_lista = [pesos[c] for c in populacao]
        return random.choices(populacao, weights=pesos_lista)[0]

    def _escolher_zona_taticamente(self, e) -> str:
        """Escolhe a zona de invasão baseado na análise tática da fortaleza."""
        invasores = e.get("invasores", {})
        pedregulhos = e.get("pedregulhos", 0)

        # Zonas disponíveis
        campos = ["campo_norte", "campo_sul", "campo_oeste", "campo_leste"]
        muralhas = ["muralha_norte", "muralha_sul", "muralha_leste", "muralha_oeste"]

        # Tática 1: se há muitos pedregulhos, atacar pelo pátio (escavar defesa)
        if pedregulhos >= 6 and random.random() < 0.3:
            return "patio"

        # Tática 2: reforçar a muralha com menos invasores
        muralha_alvo = min(muralhas, key=lambda z: invasores.get(z, 0))
        if invasores.get(muralha_alvo, 0) < 3 and random.random() < 0.5:
            # Ataca pelo campo correspondente
            mapa_campo = {
                "muralha_norte": "campo_norte",
                "muralha_sul":   "campo_sul",
                "muralha_leste": "campo_leste",
                "muralha_oeste": "campo_oeste",
            }
            return mapa_campo.get(muralha_alvo, random.choice(campos))

        # Tática 3: diversificar campos para sobrecarregar a defesa
        campos_vazios = [c for c in campos if invasores.get(c, 0) == 0]
        if campos_vazios:
            return random.choice(campos_vazios)

        # Fallback: campo aleatório
        return random.choice(campos)

    def _invadir_zona(self, inseto_id: str, zona: str):
        """Executa a invasão: adiciona o inseto na zona escolhida."""
        from src.cerco_isectum import DADOS_INIMIGOS, aplicar_delta

        s = self.state
        e = s.estado

        info = DADOS_INIMIGOS.get(inseto_id, {})
        nome = info.get("nome", inseto_id)
        emoji = info.get("emoji", "🐛")

        # Incrementa contador de invasores na zona
        invasores = dict(e.get("invasores", {}))
        invasores[zona] = invasores.get(zona, 0) + 1
        s.estado = aplicar_delta(e, {"invasores": invasores})

        # Aplica efeito especial da casta
        s._aplicar_efeito_inimigo(inseto_id)

        # Sincroniza o tabuleiro com o novo estado
        s._sincronizar_inimigos_tabuleiro()
        s.map_backbuffer_sujo = True

        s._push(
            "INIMIGO",
            f"👑 Filho do Imperador envia {emoji} {nome} → {zona.replace('_', ' ').upper()}!"
        )

    # ── FIM DO TURNO ─────────────────────────────────────────────────
    def _finalizar_turno(self):
        """Finaliza o turno do Filho do Imperador e passa para a Fase de Ameaça."""
        s = self.state
        s._push("INIMIGO", "👑 Filho do Imperador encerrou o turno. Fase de Ameaça!")
        s._feedback("⚔ As castas imperiais invadiram! Fase de Ameaça iniciando...", (255, 120, 60))
        self._ativo = False
        self.banner_timer = 0
        # Inicia a fase de ameaça
        s._iniciar_fase_ameaca()
