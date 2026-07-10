"""
castas_state.py — Estado Pygame Principal: Modo Castas dos Isectum

Fases do turno:
  TURNO_DEFENSOR  → Defensor usa cartas da mão (movimento, trabalho, defesa, runa)
  TURNO_DIRETOR   → Diretor Isectum (IA) joga cartas de inseto
  FASE_AMEACA     → Carta do deck híbrido é revelada e resolvida
  FIM             → Vitória ou derrota
"""
from __future__ import annotations
import pygame
import random
import math
from .state_base import GameState
from ..castas_isectum import (
    criar_estado_castas, aplicar_delta_castas,
    processar_carta_hibrida, turno_diretor_ia,
    aplicar_efeito_runa, aplicar_efeito_defesa,
    aplicar_efeito_inseto, criar_carta_capturada,
    verificar_condicoes, DADOS_INIMIGOS, INSETOS_BOSS,
    get_hp_inseto, e_boss,
    CARTAS_DEFESA, CARTAS_RUNA,
)
from ..cerco_isectum import CARTAS_BASICAS, NOMES_ZONA
from ..config import ESTADO_JOGO_MENU_PRINCIPAL, LARGURA_TELA, ALTURA_TELA

ESTADO_JOGO_CASTAS       = "castas"
ESTADO_JOGO_CASTAS_SETUP = "castas_setup"

# ── PALETA ────────────────────────────────────────────────────────────────
C_BG      = (4,  3, 10)
C_PAINEL  = (10, 8, 24)
C_BORDA   = (60, 30, 100)
C_ACENTO  = (200, 80, 255)
C_OURO    = (255, 195, 40)
C_VERDE   = (50, 220, 110)
C_PERIGO  = (255, 55, 55)
C_INSETO  = (130, 240, 80)
C_TEXTO   = (235, 240, 255)
C_DIM     = (100, 90, 130)
C_HEROI   = (100, 200, 255)
C_DIRETOR = (255, 100, 60)
C_CARD    = (18, 12, 40)
C_CARD_HL = (38, 18, 70)
C_DEFESA  = (60, 160, 220)
C_RUNA    = (220, 130, 255)
C_CAPTURA = (255, 220, 40)


# Fonte all-in-one para render de texto único
def _render_txt(fonte, texto, cor, max_width=None):
    surf = fonte.render(texto, True, cor)
    if max_width and surf.get_width() > max_width:
        # Trunca com '…'
        while surf.get_width() > max_width and len(texto) > 1:
            texto = texto[:-1]
            surf = fonte.render(texto + "…", True, cor)
    return surf


class CastasState(GameState):
    """Estado completo do modo Castas dos Isectum."""

    TAM_MAO_DEFENSOR = 5
    TAM_MAO_DIRETOR  = 3  # ajustado pela dificuldade

    def __init__(self, game, config=None):
        super().__init__(game)
        if config is None:
            from ..personagens.novos_personagens import Stark
            config = {"herois": [("Stark", Stark)], "dificuldade": {"id": "normal"}}

        self.config = config
        diff   = config.get("dificuldade", {})
        herois = config.get("herois", [])

        herois_nomes = [nome for nome, _ in herois]
        dif_id = diff.get("id", "normal")

        self.estado = criar_estado_castas(herois_nomes=herois_nomes, dificuldade=dif_id)

        # Instanciar objetos de herói para renderização
        self.herois_obj = []
        for nome, cls in herois:
            h = cls(nome, "A", nivel=5)
            self.herois_obj.append(h)

        self.heroi_atual_idx = 0
        self.fase = "TURNO_DEFENSOR"

        self._setup_fonts()
        self._setup_layout()

        # Animação e feedback
        self.timer        = 0
        self.msg_feedback = ""
        self.msg_cor      = C_VERDE
        self.feedback_timer = 0

        # Seleção de carta na mão
        self.carta_selecionada_idx = -1
        self.carta_rects           = []

        # Carta de ameaça atual (revelada)
        self.carta_ameaca_atual = None
        self.ameaca_revelada    = False

        # Turno do Diretor: fila de resultados a processar
        self.fila_diretor    = []
        self.fila_idx        = 0
        self.aguardando_anim = False

        # Log visual
        self.log = []

        # Revela da mão do Diretor (top N cartas)
        self.deck_diretor_revelado = []

        # Comprar mão inicial do primeiro Defensor
        self._comprar_mao_defensor()

        self._push("SISTEMA", f"🐛 Castas dos Isectum! {len(herois_nomes)} defensor(es) vs. Diretor (IA).")
        self._push("SISTEMA", f"Dificuldade: {dif_id.capitalize()} | Deck Diretor: {len(self.estado['deck_diretor'])} cartas.")

    # ── FONTS ──────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        s = max(0.5, ALTURA_TELA / 720.0)
        self.fT  = pygame.font.Font(None, max(18, int(52 * s)))
        self.fG  = pygame.font.Font(None, max(14, int(36 * s)))
        self.fM  = pygame.font.Font(None, max(12, int(28 * s)))
        self.fP  = pygame.font.Font(None, max(10, int(22 * s)))
        self.fMi = pygame.font.Font(None, max(8,  int(18 * s)))

    # ── LAYOUT ─────────────────────────────────────────────────────────────
    def _setup_layout(self):
        W, H = LARGURA_TELA, ALTURA_TELA
        # Área central (tabuleiro de zonas)
        self.mapa_rect   = pygame.Rect(8, 60, W - 330, H - 220)
        # Painel lateral direito (log + info Diretor)
        self.painel_rect = pygame.Rect(W - 320, 60, 312, H - 70)
        # Faixa inferior — mão do Defensor
        self.mao_rect    = pygame.Rect(8, H - 152, W - 330, 144)
        # Botões de ação
        bw, bh = 120, 36
        by = H - 46
        self.btn_fim_turno  = pygame.Rect(W - 320, by, bw + 20, bh)
        self.btn_voltar     = pygame.Rect(W - 156, 62, 140, 28)

    # ── LOG ────────────────────────────────────────────────────────────────
    def _push(self, tipo, msg):
        self.log.append((tipo, msg))
        if len(self.log) > 80:
            self.log = self.log[-80:]

    def _feedback(self, msg, cor=None):
        self.msg_feedback  = msg
        self.msg_cor       = cor or C_VERDE
        self.feedback_timer = 180

    # ── COMPRAR MÃO ────────────────────────────────────────────────────────
    def _comprar_mao_defensor(self):
        heroi_nome = self._heroi_ativo_nome()
        if not heroi_nome:
            return
        hs = dict(self.estado["herois_status"][heroi_nome])

        # Verificar atordoamento
        if hs.get("turno_pulado"):
            hs["turno_pulado"] = False
            novos_hs = dict(self.estado["herois_status"])
            novos_hs[heroi_nome] = hs
            self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
            self._push("SISTEMA", f"🪰 {heroi_nome} estava atordoado — turno pulado!")
            self._feedback(f"{heroi_nome} foi atordoado! Turno pulado.", C_PERIGO)
            self._avancar_turno_heroi()
            return

        mao  = list(hs.get("mao", []))
        deck = list(hs.get("deck", hs.get("deck_heroi", [])))
        desc = list(hs.get("descarte", []))

        while len(mao) < self.TAM_MAO_DEFENSOR:
            if not deck:
                if not desc:
                    break
                # Ciclo: reembaralha descarte, exclui 2
                todas = list(desc)
                random.shuffle(todas)
                excluidas = []
                candidatas = [c for c in todas if c not in mao]
                for _ in range(min(2, len(candidatas))):
                    if candidatas:
                        excluidas.append(candidatas.pop(random.randrange(len(candidatas))))
                deck = [c for c in todas if c not in mao and c not in excluidas]
                desc = []
                hs["excluidas"] = hs.get("excluidas", []) + excluidas
                self._push("SISTEMA", f"Ciclo do baralho de {heroi_nome}: 2 cartas excluídas.")
            if deck:
                mao.append(deck.pop())

        hs["mao"]  = mao
        hs["deck"] = deck
        hs["descarte"] = desc
        novos_hs = dict(self.estado["herois_status"])
        novos_hs[heroi_nome] = hs
        self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
        self._push("SISTEMA", f"🃏 {heroi_nome} comprou mão ({len(mao)} cartas).")

    # ── HELPERS ────────────────────────────────────────────────────────────
    def _heroi_ativo_nome(self):
        nomes = self.estado.get("herois_nomes", [])
        if not nomes:
            return None
        idx = self.estado.get("turno_heroi_idx", 0) % len(nomes)
        return nomes[idx]

    def _mao_defensor(self):
        nome = self._heroi_ativo_nome()
        if not nome:
            return []
        return self.estado["herois_status"].get(nome, {}).get("mao", [])

    def _avancar_turno_heroi(self):
        """Passa para o próximo defensor ou inicia fase do Diretor."""
        nomes = self.estado.get("herois_nomes", [])
        jogaram = list(self.estado.get("herois_jogaram", []))
        nome_atual = self._heroi_ativo_nome()
        if nome_atual and nome_atual not in jogaram:
            jogaram.append(nome_atual)
        self.estado = aplicar_delta_castas(self.estado, {"herois_jogaram": jogaram})

        # Próximo herói que não jogou
        proximo = None
        for nome in nomes:
            if nome not in jogaram:
                proximo = nome
                break

        if proximo:
            idx_novo = nomes.index(proximo)
            self.estado = aplicar_delta_castas(self.estado, {"turno_heroi_idx": idx_novo})
            self._comprar_mao_defensor()
            self._feedback(f"Turno de {proximo}!", C_HEROI)
        else:
            # Todos jogaram → Fase do Diretor
            self.estado = aplicar_delta_castas(self.estado, {"herois_jogaram": []})
            self._iniciar_turno_diretor()

    def _iniciar_turno_diretor(self):
        self.fase = "TURNO_DIRETOR"
        self._push("DIRETOR", "══════ TURNO DO DIRETOR ISECTUM ══════")
        self._feedback("Diretor Isectum age!", C_DIRETOR)

        # Executa IA do Diretor
        self.fila_diretor = turno_diretor_ia(self.estado)
        self.fila_idx = 0
        self._processar_proxima_acao_diretor()

    def _processar_proxima_acao_diretor(self):
        if self.fila_idx >= len(self.fila_diretor):
            # Termina turno do Diretor → Fase de Ameaça
            self._iniciar_fase_ameaca()
            return
        delta, logs = self.fila_diretor[self.fila_idx]
        self.fila_idx += 1
        self.estado = aplicar_delta_castas(self.estado, delta)
        for tipo, msg in logs:
            self._push(tipo, msg)
        # Verifica condições após cada ação
        vit, der, msg = verificar_condicoes(self.estado)
        if vit or der:
            self.estado = aplicar_delta_castas(self.estado, {
                "vitoria": vit, "derrota": der, "msg_fim": msg
            })
            self.fase = "FIM"
            self._push("SISTEMA", f"🏁 {msg}")
            return
        # Próxima ação com pequeno delay visual
        self._processar_proxima_acao_diretor()

    def _iniciar_fase_ameaca(self):
        self.fase = "FASE_AMEACA"
        self._push("SISTEMA", "══════ FASE DE AMEAÇA ══════")
        deck_a = list(self.estado.get("deck_ameaca", []))
        desc_a = list(self.estado.get("descarte_ameaca", []))
        if not deck_a:
            if not desc_a:
                self._push("SISTEMA", "Deck de ameaças vazio! Próxima rodada sem ameaça.")
                self._concluir_rodada()
                return
            random.shuffle(desc_a)
            deck_a = desc_a
            desc_a = []
            self._push("SISTEMA", "Deck de ameaças reembaralhado!")
        carta = deck_a.pop()
        desc_a.append(carta)
        self.estado = aplicar_delta_castas(self.estado, {
            "deck_ameaca": deck_a,
            "descarte_ameaca": desc_a,
            "carta_ameaca_atual": carta,
        })
        self.carta_ameaca_atual = carta
        self.ameaca_revelada    = True

        heroi_ativo = self._heroi_ativo_nome()
        delta, logs = processar_carta_hibrida(self.estado, carta, heroi_ativo)
        self.estado = aplicar_delta_castas(self.estado, delta)
        for tipo, msg in logs:
            self._push(tipo, msg)
        self._feedback(f"⚠ {carta.get('titulo','Ameaça')} revelada!", C_PERIGO)

        vit, der, msg = verificar_condicoes(self.estado)
        if vit or der:
            self.estado = aplicar_delta_castas(self.estado, {
                "vitoria": vit, "derrota": der, "msg_fim": msg
            })
            self.fase = "FIM"
            self._push("SISTEMA", f"🏁 {msg}")
        else:
            self._concluir_rodada()

    def _concluir_rodada(self):
        """Incrementa rodada e retorna para TURNO_DEFENSOR."""
        rodada_atual = self.estado.get("rodada", 1)
        nova_rodada  = rodada_atual + 1
        # Decrementa bloqueios de zona
        zonas_b = dict(self.estado.get("zonas_bloqueadas", {}))
        for z in list(zonas_b.keys()):
            zonas_b[z] -= 1
            if zonas_b[z] <= 0:
                del zonas_b[z]

        self.estado = aplicar_delta_castas(self.estado, {
            "rodada": nova_rodada,
            "zonas_bloqueadas": zonas_b,
            "carta_ameaca_atual": None,
            "turno_heroi_idx": 0,
            "herois_jogaram": [],
        })
        self.carta_ameaca_atual = None
        self.ameaca_revelada = False
        self.fase = "TURNO_DEFENSOR"
        self._comprar_mao_defensor()
        self._push("SISTEMA", f"══════ RODADA {nova_rodada} ══════")
        self._feedback(f"Rodada {nova_rodada} — Hora dos Defensores!", C_VERDE)

    # ── JOGAR CARTA ────────────────────────────────────────────────────────
    def _jogar_carta(self, idx_carta):
        heroi_nome = self._heroi_ativo_nome()
        if not heroi_nome:
            return
        hs = dict(self.estado["herois_status"].get(heroi_nome, {}))
        mao = list(hs.get("mao", []))
        if idx_carta < 0 or idx_carta >= len(mao):
            return

        carta = mao[idx_carta]
        tipo  = carta.get("tipo", "basica")

        # Aplica efeito conforme tipo de carta
        if tipo == "runa":
            delta, logs = aplicar_efeito_runa(self.estado, carta, heroi_nome)
            self.estado = aplicar_delta_castas(self.estado, delta)
            for t, m in logs:
                self._push(t, m)
            self._feedback(f"⚡ {carta['nome']} ativada!", C_RUNA)

        elif tipo == "defesa":
            delta, logs = aplicar_efeito_defesa(self.estado, carta, heroi_nome)
            self.estado = aplicar_delta_castas(self.estado, delta)
            for t, m in logs:
                self._push(t, m)
            self._feedback(f"🛡 {carta['nome']} ativada!", C_DEFESA)

        elif tipo == "capturada":
            # Efeito invertido do inseto capturado
            efeito = carta.get("efeito", "bonus_generico")
            if efeito == "dar_turno_extra":
                hs_local = dict(self.estado["herois_status"].get(heroi_nome, {}))
                hs_local["acoes_extras"] = hs_local.get("acoes_extras", 0) + 1
                novos_hs = dict(self.estado["herois_status"])
                novos_hs[heroi_nome] = hs_local
                self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
                self._push("HEROI", f"★ {carta['nome']}: {heroi_nome} ganhou ação extra!")
            elif efeito == "completar_mao_defensor":
                self._comprar_mao_defensor()
                self._push("HEROI", f"★ {carta['nome']}: mão completada!")
            elif efeito == "bonus_generico":
                hs_local = dict(self.estado["herois_status"].get(heroi_nome, {}))
                hs_local["pontos_trabalho"] = hs_local.get("pontos_trabalho", 0) + 3
                novos_hs = dict(self.estado["herois_status"])
                novos_hs[heroi_nome] = hs_local
                self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
                self._push("HEROI", f"★ {carta['nome']}: +3 Trabalho!")
            else:
                self._push("HEROI", f"★ {carta['nome']}: {carta.get('descricao', 'Bônus!')}!")
            self._feedback(f"★ {carta['nome']} usada!", C_CAPTURA)

        else:
            # Carta básica/upgrade: acumula pontos
            pts_mov  = carta.get("movimento", 0)
            pts_trab = carta.get("trabalho", 0)
            pts_esc  = carta.get("escavacao", 0)
            hs_local = dict(self.estado["herois_status"].get(heroi_nome, {}))
            hs_local["pontos_movimento"]  = hs_local.get("pontos_movimento", 0)  + pts_mov
            hs_local["pontos_trabalho"]   = hs_local.get("pontos_trabalho", 0)   + pts_trab
            hs_local["pontos_escavacao"]  = hs_local.get("pontos_escavacao", 0)  + pts_esc
            novos_hs = dict(self.estado["herois_status"])
            novos_hs[heroi_nome] = hs_local
            self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
            partes = []
            if pts_mov:  partes.append(f"+{pts_mov} Mov")
            if pts_trab: partes.append(f"+{pts_trab} Trab")
            if pts_esc:  partes.append(f"+{pts_esc} Esc")
            self._push("HEROI", f"🃏 {heroi_nome} jogou {carta['nome']}: {', '.join(partes) or 'sem pontos'}")
            self._feedback(f"{carta['nome']}: {', '.join(partes)}", C_VERDE)

        # Remove carta da mão e move para descarte
        hs = dict(self.estado["herois_status"].get(heroi_nome, {}))
        mao = list(hs.get("mao", []))
        if idx_carta < len(mao):
            descartada = mao.pop(idx_carta)
            desc = list(hs.get("descarte", []))
            desc.append(descartada)
            hs["mao"]     = mao
            hs["descarte"] = desc
            novos_hs = dict(self.estado["herois_status"])
            novos_hs[heroi_nome] = hs
            self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})

        self.carta_selecionada_idx = -1

        # Verifica condições
        vit, der, msg = verificar_condicoes(self.estado)
        if vit or der:
            self.estado = aplicar_delta_castas(self.estado, {
                "vitoria": vit, "derrota": der, "msg_fim": msg
            })
            self.fase = "FIM"

    def _atacar_boss(self, inseto_id):
        """Ataca um inseto boss no campo. Se HP chegar a 0, captura."""
        bosses = dict(self.estado.get("bosses_no_campo", {}))
        if inseto_id not in bosses:
            self._feedback("Esse boss não está no campo!", C_PERIGO)
            return
        boss = dict(bosses[inseto_id])
        boss["hp"] -= 1
        heroi_nome = self._heroi_ativo_nome()
        nome_boss = DADOS_INIMIGOS.get(inseto_id, {}).get("nome", inseto_id)
        emoji     = DADOS_INIMIGOS.get(inseto_id, {}).get("emoji", "🐛")
        self._push("HEROI", f"⚔ {heroi_nome} atacou {emoji} {nome_boss}! HP: {boss['hp']}")

        if boss["hp"] <= 0:
            del bosses[inseto_id]
            elim = list(self.estado.get("bosses_eliminados", []))
            elim.append(inseto_id)
            self.estado = aplicar_delta_castas(self.estado, {
                "bosses_no_campo": bosses,
                "bosses_eliminados": elim,
            })
            self._push("HEROI", f"🏆 {emoji} {nome_boss} derrotado e CAPTURADO!")
            self._feedback(f"{nome_boss} capturado!", C_CAPTURA)

            # Cria carta capturada e adiciona ao deck do herói
            carta_cap = criar_carta_capturada(inseto_id)
            hs = dict(self.estado["herois_status"].get(heroi_nome, {}))
            deck = list(hs.get("deck", []))
            deck.insert(0, carta_cap)   # põe no topo do deck
            hs["deck"] = deck
            novos_hs = dict(self.estado["herois_status"])
            novos_hs[heroi_nome] = hs
            self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
            self._push("HEROI", f"★ Carta '{carta_cap['nome']}' adicionada ao deck de {heroi_nome}!")
        else:
            bosses[inseto_id] = boss
            self.estado = aplicar_delta_castas(self.estado, {"bosses_no_campo": bosses})
            self._feedback(f"{nome_boss}: {boss['hp']} HP restante!", C_OURO)

        vit, der, msg = verificar_condicoes(self.estado)
        if vit or der:
            self.estado = aplicar_delta_castas(self.estado, {
                "vitoria": vit, "derrota": der, "msg_fim": msg
            })
            self.fase = "FIM"

    # ── EVENTS ─────────────────────────────────────────────────────────────
    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.castas_state = None
                    self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
                    return
                if event.key == pygame.K_SPACE and self.fase == "TURNO_DEFENSOR":
                    self._encerrar_turno_defensor()
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_voltar.collidepoint(mouse):
                    self.game.castas_state = None
                    self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
                    return

                if self.fase == "FIM":
                    # Qualquer clique em FIM volta ao menu
                    self.game.castas_state = None
                    self.game.estado_jogo  = ESTADO_JOGO_MENU_PRINCIPAL
                    return

                if self.fase == "TURNO_DEFENSOR":
                    # Clique em carta da mão
                    for i, rect in enumerate(self.carta_rects):
                        if rect and rect.collidepoint(mouse):
                            if self.carta_selecionada_idx == i:
                                # Duplo clique → joga
                                self._jogar_carta(i)
                            else:
                                self.carta_selecionada_idx = i
                            return

                    # Clique no botão "Fim de Turno"
                    if self.btn_fim_turno.collidepoint(mouse):
                        self._encerrar_turno_defensor()
                        return

                    # Clique em boss no campo
                    for inseto_id, rect in self.boss_rects.items():
                        if rect.collidepoint(mouse):
                            self._atacar_boss(inseto_id)
                            return

    def _encerrar_turno_defensor(self):
        """Encerra turno do herói atual."""
        heroi_nome = self._heroi_ativo_nome()
        # Descarta a mão restante
        hs = dict(self.estado["herois_status"].get(heroi_nome, {}))
        mao  = list(hs.get("mao", []))
        desc = list(hs.get("descarte", []))
        desc.extend(mao)
        hs["mao"]      = []
        hs["descarte"] = desc
        hs["pontos_movimento"] = 0
        hs["pontos_trabalho"]  = 0
        hs["pontos_escavacao"] = 0
        hs["acoes_extras"]     = 0
        hs["imune_destruicao"] = False
        novos_hs = dict(self.estado["herois_status"])
        novos_hs[heroi_nome] = hs
        self.estado = aplicar_delta_castas(self.estado, {"herois_status": novos_hs})
        self.carta_selecionada_idx = -1
        self._push("HEROI", f"✅ {heroi_nome} encerrou o turno.")
        self._avancar_turno_heroi()

    # ── UPDATE ─────────────────────────────────────────────────────────────
    def update(self):
        self.timer += 1
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ── DRAW ───────────────────────────────────────────────────────────────
    def draw(self, tela):
        W, H = LARGURA_TELA, ALTURA_TELA
        tela.fill(C_BG)

        self._draw_hud_topo(tela, W)
        self._draw_zonas(tela)
        self._draw_bosses_campo(tela)
        self._draw_painel_lateral(tela, W, H)
        self._draw_mao(tela)
        self._draw_botoes(tela, W, H)
        self._draw_feedback(tela, W, H)
        self._draw_carta_ameaca(tela, W)
        self._draw_info_diretor(tela, W)

        if self.fase == "FIM":
            self._draw_tela_fim(tela, W, H)

    def _draw_hud_topo(self, tela, W):
        bar = pygame.Surface((W, 56), pygame.SRCALPHA)
        bar.fill((6, 4, 16, 220))
        tela.blit(bar, (0, 0))
        pygame.draw.line(tela, C_BORDA, (0, 56), (W, 56), 1)

        # Título
        t_titulo = self.fG.render("🐛 CASTAS DOS ISECTUM", True, C_ACENTO)
        tela.blit(t_titulo, (12, 14))

        # Fase atual
        fase_cor = {
            "TURNO_DEFENSOR": C_HEROI,
            "TURNO_DIRETOR":  C_DIRETOR,
            "FASE_AMEACA":    C_PERIGO,
            "FIM":            C_OURO,
        }.get(self.fase, C_DIM)
        fase_txt = {
            "TURNO_DEFENSOR": f"🃏 Turno dos Defensores — {self._heroi_ativo_nome() or '?'}",
            "TURNO_DIRETOR":  "🦟 Turno do Diretor Isectum",
            "FASE_AMEACA":    "⚠ Fase de Ameaça",
            "FIM":            "🏁 FIM DE JOGO",
        }.get(self.fase, self.fase)
        tf = self.fM.render(fase_txt, True, fase_cor)
        tela.blit(tf, (W // 2 - tf.get_width() // 2, 18))

        # Stats rápidos
        rod = self.estado.get("rodada", 1)
        rod_max = self.estado.get("rodadas_max", 15)
        hp_f = self.estado.get("hp_fortaleza", 0)
        hp_max = self.estado.get("hp_fortaleza_max", 20)
        roub = self.estado.get("cartas_roubadas_total", 0)

        stats = [
            (f"Rodada {rod}/{rod_max}", C_OURO),
            (f"HP Fortaleza: {hp_f}/{hp_max}", C_VERDE if hp_f > hp_max // 2 else C_PERIGO),
            (f"Cartas Roubadas: {roub}/10", C_PERIGO if roub >= 7 else C_DIM),
        ]
        x_stat = W - 430
        for txt_s, cor_s in stats:
            surf_s = self.fP.render(txt_s, True, cor_s)
            tela.blit(surf_s, (x_stat, 18))
            x_stat += surf_s.get_width() + 24

    def _draw_zonas(self, tela):
        """Desenha o mini-mapa das zonas com invasores."""
        mr = self.mapa_rect
        pygame.draw.rect(tela, C_PAINEL, mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)

        inv = self.estado.get("invasores", {})
        zonas_block = self.estado.get("zonas_bloqueadas", {})

        # Layout simplificado das zonas num grid fixo
        ZONAS_LAYOUT = {
            "muralha_norte":  (0.35, 0.02, 0.30, 0.14),
            "muralha_sul":    (0.35, 0.84, 0.30, 0.14),
            "muralha_oeste":  (0.01, 0.30, 0.14, 0.40),
            "muralha_leste":  (0.85, 0.30, 0.14, 0.40),
            "carpintaria":    (0.35, 0.18, 0.30, 0.18),
            "curtume":        (0.35, 0.64, 0.30, 0.18),
            "fundicao":       (0.17, 0.30, 0.16, 0.40),
            "patio":          (0.67, 0.30, 0.16, 0.40),
            "camara_central": (0.35, 0.38, 0.30, 0.24),
        }

        for zona_id, (rx, ry, rw, rh) in ZONAS_LAYOUT.items():
            x = mr.x + int(rx * mr.w)
            y = mr.y + int(ry * mr.h)
            w = int(rw * mr.w)
            h = int(rh * mr.h)
            rect_zona = pygame.Rect(x, y, w, h)

            n_inv = inv.get(zona_id, 0)
            bloqueada = zona_id in zonas_block

            # Cor base da zona
            if zona_id == "camara_central":
                cor_base = (12, 10, 40)
            elif "muralha" in zona_id:
                cor_base = (28, 14, 48) if n_inv == 0 else (60, 20, 20)
            else:
                cor_base = (14, 18, 36)

            pygame.draw.rect(tela, cor_base, rect_zona, border_radius=6)

            # Borda colorida por nível de ameaça
            if n_inv == 0:
                cor_bd = C_BORDA
            elif n_inv <= 2:
                cor_bd = C_OURO
            else:
                cor_bd = C_PERIGO
            if bloqueada:
                cor_bd = C_DEFESA
            pygame.draw.rect(tela, cor_bd, rect_zona, 2 if n_inv > 0 or bloqueada else 1, border_radius=6)

            # Nome da zona
            nome_z = NOMES_ZONA.get(zona_id, zona_id)
            nt = self.fMi.render(nome_z, True, C_DIM)
            tela.blit(nt, (x + 4, y + 4))

            # Contador de invasores
            if n_inv > 0:
                txt_inv = self.fM.render(f"👾 {n_inv}", True, C_PERIGO)
                tela.blit(txt_inv, (x + w // 2 - txt_inv.get_width() // 2,
                                    y + h // 2 - txt_inv.get_height() // 2))

            # Ícone de bloqueio
            if bloqueada:
                txt_bl = self.fMi.render(f"🕸 {zonas_block[zona_id]}t", True, C_DEFESA)
                tela.blit(txt_bl, (x + 4, y + h - txt_bl.get_height() - 4))

    def _draw_bosses_campo(self, tela):
        """Desenha os bosses no campo com HP e botão de ataque."""
        self.boss_rects = {}
        bosses = self.estado.get("bosses_no_campo", {})
        if not bosses:
            return

        mr = self.mapa_rect
        x_boss = mr.x + mr.w + 8  # Mostra à direita do mapa (dentro do painel)
        y_boss = mr.y + 10

        t = self.fM.render("⚠ BOSSES NO CAMPO", True, C_CAPTURA)
        tela.blit(t, (x_boss, y_boss))
        y_boss += 28

        for inseto_id, info in bosses.items():
            dados = DADOS_INIMIGOS.get(inseto_id, {})
            nome  = dados.get("nome", inseto_id)
            emoji = dados.get("emoji", "🐛")
            hp    = info.get("hp", 1)
            hp_max = get_hp_inseto(inseto_id)
            zona  = info.get("zona", "?")

            rect_b = pygame.Rect(x_boss, y_boss, 200, 70)
            pygame.draw.rect(tela, (25, 10, 45), rect_b, border_radius=8)
            pygame.draw.rect(tela, C_CAPTURA, rect_b, 2, border_radius=8)

            n1 = self.fP.render(f"{emoji} {nome}", True, C_OURO)
            tela.blit(n1, (x_boss + 8, y_boss + 6))
            n2 = self.fMi.render(f"Zona: {zona}", True, C_DIM)
            tela.blit(n2, (x_boss + 8, y_boss + 26))

            # Barra de HP
            bw = 140
            bh = 10
            bx = x_boss + 8
            by = y_boss + 44
            pygame.draw.rect(tela, (40, 10, 10), pygame.Rect(bx, by, bw, bh), border_radius=4)
            hp_pct = hp / max(hp_max, 1)
            pygame.draw.rect(tela, C_PERIGO, pygame.Rect(bx, by, int(bw * hp_pct), bh), border_radius=4)
            ht = self.fMi.render(f"HP {hp}/{hp_max}", True, C_TEXTO)
            tela.blit(ht, (bx + bw + 4, by - 2))

            # Botão de ataque (clicável no turno do defensor)
            if self.fase == "TURNO_DEFENSOR":
                btn = pygame.Rect(x_boss + 158, y_boss + 16, 36, 36)
                mouse = pygame.mouse.get_pos()
                hover_b = btn.collidepoint(mouse)
                pygame.draw.rect(tela, (50, 15, 15) if not hover_b else (90, 20, 20), btn, border_radius=6)
                pygame.draw.rect(tela, C_PERIGO, btn, 1, border_radius=6)
                at = self.fP.render("⚔", True, C_PERIGO)
                tela.blit(at, (btn.centerx - at.get_width() // 2, btn.centery - at.get_height() // 2))
                self.boss_rects[inseto_id] = btn

            y_boss += 82

    def _draw_painel_lateral(self, tela, W, H):
        pr = self.painel_rect
        pygame.draw.rect(tela, C_PAINEL, pr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, pr, 1, border_radius=8)

        y = pr.y + 8
        # Título do log
        t_log = self.fP.render("── LOG DE COMBATE ──", True, C_ACENTO)
        tela.blit(t_log, (pr.x + 8, y))
        y += 22

        # Itens do log (mais recentes no topo)
        log_exibir = self.log[-28:]
        for tipo, msg in reversed(log_exibir):
            cor_tipo = {
                "SISTEMA": C_DIM, "HEROI": C_HEROI, "DIRETOR": C_DIRETOR,
                "AMEAÇA": C_PERIGO, "DEFESA": C_DEFESA, "DERROTA": C_PERIGO,
                "INFO": C_DIM,
            }.get(tipo, C_TEXTO)
            prefixo = f"[{tipo}] "
            surf_p = self.fMi.render(prefixo, True, cor_tipo)
            tela.blit(surf_p, (pr.x + 6, y))
            surf_m = _render_txt(self.fMi, msg, C_TEXTO, pr.w - surf_p.get_width() - 12)
            tela.blit(surf_m, (pr.x + 6 + surf_p.get_width(), y))
            y += 16
            if y > pr.bottom - 20:
                break

        # Info Diretor no fundo do painel
        py_info = pr.bottom - 100
        pygame.draw.line(tela, C_BORDA, (pr.x + 6, py_info), (pr.right - 6, py_info), 1)
        t_dir = self.fP.render("── DIRETOR ISECTUM ──", True, C_DIRETOR)
        tela.blit(t_dir, (pr.x + 8, py_info + 4))
        deck_dir = len(self.estado.get("deck_diretor", []))
        mao_dir  = len(self.estado.get("mao_diretor", []))
        desc_dir = len(self.estado.get("descarte_diretor", []))
        acoes_r  = self.estado.get("acoes_diretor_restantes", 0)
        acoes_m  = self.estado.get("acoes_diretor_max", 3)
        info_lines = [
            (f"Deck: {deck_dir} | Mão: {mao_dir} | Desc: {desc_dir}", C_DIM),
            (f"Ações: {acoes_r}/{acoes_m} restantes", C_DIRETOR),
        ]
        for txt_i, cor_i in info_lines:
            si = self.fMi.render(txt_i, True, cor_i)
            py_info += 18
            tela.blit(si, (pr.x + 8, py_info))

        # Cartas reveladas do Diretor (Runa da Visão)
        reveladas = self.estado.get("deck_diretor_revelado", [])
        if reveladas:
            py_info += 18
            rv_t = self.fMi.render("Próx. cartas do Diretor:", True, C_RUNA)
            tela.blit(rv_t, (pr.x + 8, py_info))
            for c_rev in reveladas:
                py_info += 14
                rv_c = self.fMi.render(f"  {c_rev.get('emoji','?')} {c_rev.get('nome','?')}", True, C_DIM)
                tela.blit(rv_c, (pr.x + 8, py_info))
                if py_info > pr.bottom - 10:
                    break

    def _draw_mao(self, tela):
        """Desenha a mão do Defensor ativo na faixa inferior."""
        mr = self.mao_rect
        pygame.draw.rect(tela, (8, 6, 20), mr, border_radius=8)
        pygame.draw.rect(tela, C_BORDA, mr, 1, border_radius=8)

        heroi_nome = self._heroi_ativo_nome()
        mao = self._mao_defensor()
        self.carta_rects = []

        if not mao:
            vazio = self.fM.render("Mão vazia", True, C_DIM)
            tela.blit(vazio, (mr.centerx - vazio.get_width() // 2,
                              mr.centery - vazio.get_height() // 2))
            return

        # Título da mão
        nm_t = self.fP.render(f"{heroi_nome} — Mão ({len(mao)}/{self.TAM_MAO_DEFENSOR})", True, C_HEROI)
        tela.blit(nm_t, (mr.x + 10, mr.y + 6))

        n = len(mao)
        max_w = mr.w - 20
        cw = min(110, max_w // n - 4)
        ch = 110
        total_w = n * cw + (n - 1) * 4
        x0 = mr.x + (mr.w - total_w) // 2
        y0 = mr.y + mr.h - ch - 8
        mouse = pygame.mouse.get_pos()

        for i, carta in enumerate(mao):
            cx = x0 + i * (cw + 4)
            sel = i == self.carta_selecionada_idx
            hover = pygame.Rect(cx, y0 - 4, cw, ch + 8).collidepoint(mouse)
            cy = y0 - (10 if sel else (4 if hover else 0))

            tipo = carta.get("tipo", "basica")
            cor_card = {
                "basica":   C_CARD,
                "upgrade":  (18, 28, 18),
                "defesa":   (8, 24, 50),
                "runa":     (28, 12, 50),
                "capturada":(38, 32, 8),
            }.get(tipo, C_CARD)
            cor_borda = {
                "basica":   C_BORDA,
                "upgrade":  C_VERDE,
                "defesa":   C_DEFESA,
                "runa":     C_RUNA,
                "capturada":C_CAPTURA,
            }.get(tipo, C_BORDA)

            rect_c = pygame.Rect(cx, cy, cw, ch)
            self.carta_rects.append(rect_c)
            pygame.draw.rect(tela, cor_card, rect_c, border_radius=7)
            pygame.draw.rect(tela, cor_borda, rect_c, 2 if sel or hover else 1, border_radius=7)

            # Símbolo
            sym = self.fG.render(carta.get("simbolo", "?"), True, cor_borda)
            tela.blit(sym, (cx + cw // 2 - sym.get_width() // 2, cy + 8))

            # Nome (quebra se necessário)
            nome_carta = carta.get("nome", "?")
            nt = _render_txt(self.fMi, nome_carta, C_TEXTO, cw - 6)
            tela.blit(nt, (cx + 3, cy + 38))

            # Descrição curta
            desc = carta.get("descricao", "")
            dt = _render_txt(self.fMi, desc, C_DIM, cw - 6)
            tela.blit(dt, (cx + 3, cy + 54))

            # Stats rápidos
            pts = []
            if carta.get("movimento", 0):  pts.append(f"M{carta['movimento']}")
            if carta.get("trabalho", 0):   pts.append(f"T{carta['trabalho']}")
            if carta.get("escavacao", 0):  pts.append(f"E{carta['escavacao']}")
            if pts:
                pst = self.fMi.render(" ".join(pts), True, C_OURO)
                tela.blit(pst, (cx + 3, cy + 72))

            # Dica "clique 2x"
            if sel:
                hint = self.fMi.render("[jogar]", True, C_VERDE)
                tela.blit(hint, (cx + cw // 2 - hint.get_width() // 2, cy + ch - 16))

    def _draw_botoes(self, tela, W, H):
        mouse = pygame.mouse.get_pos()
        # Botão voltar
        hover_v = self.btn_voltar.collidepoint(mouse)
        pygame.draw.rect(tela, (22, 10, 38) if not hover_v else (38, 18, 60), self.btn_voltar, border_radius=6)
        pygame.draw.rect(tela, C_BORDA, self.btn_voltar, 1, border_radius=6)
        vt = self.fMi.render("< MENU", True, C_TEXTO if hover_v else C_DIM)
        tela.blit(vt, (self.btn_voltar.centerx - vt.get_width() // 2,
                       self.btn_voltar.centery - vt.get_height() // 2))

        # Botão Fim de Turno
        if self.fase == "TURNO_DEFENSOR":
            hover_ft = self.btn_fim_turno.collidepoint(mouse)
            pygame.draw.rect(tela, (18, 40, 18) if not hover_ft else (30, 70, 30), self.btn_fim_turno, border_radius=8)
            pygame.draw.rect(tela, C_VERDE, self.btn_fim_turno, 2, border_radius=8)
            ft = self.fM.render("Fim de Turno [SPACE]", True, C_VERDE if hover_ft else C_TEXTO)
            tela.blit(ft, (self.btn_fim_turno.centerx - ft.get_width() // 2,
                           self.btn_fim_turno.centery - ft.get_height() // 2))

    def _draw_feedback(self, tela, W, H):
        if self.feedback_timer > 0 and self.msg_feedback:
            alpha = min(255, self.feedback_timer * 3)
            surf_f = self.fG.render(self.msg_feedback, True, self.msg_cor)
            surf_f.set_alpha(alpha)
            tela.blit(surf_f, (W // 2 - surf_f.get_width() // 2, H - 185))

    def _draw_carta_ameaca(self, tela, W):
        if not self.carta_ameaca_atual or not self.ameaca_revelada:
            return
        carta = self.carta_ameaca_atual
        # Mini banner de ameaça no topo central
        bw, bh = 340, 52
        bx = W // 2 - bw // 2
        by = 60
        rect_a = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(tela, (30, 8, 8), rect_a, border_radius=8)
        pygame.draw.rect(tela, C_PERIGO, rect_a, 2, border_radius=8)
        tit = self.fM.render(f"⚠ {carta.get('titulo', '?')}", True, C_PERIGO)
        tela.blit(tit, (bx + 10, by + 8))
        desc = carta.get("descricao", carta.get("simbolo", ""))
        if desc:
            ds = _render_txt(self.fMi, desc, C_DIM, bw - 20)
            tela.blit(ds, (bx + 10, by + 30))
        sobren = carta.get("sobrenatural", False)
        if sobren:
            st = self.fMi.render("🌀 SOBRENATURAL", True, C_ACENTO)
            tela.blit(st, (rect_a.right - st.get_width() - 8, by + 8))

    def _draw_info_diretor(self, tela, W):
        """Mostra mão oculta do Diretor (face baixo) no topo direito."""
        mao_dir = self.estado.get("mao_diretor", [])
        if not mao_dir:
            return
        x0 = W - 320
        y0 = 62
        t_dir = self.fMi.render(f"🦟 Mão do Diretor ({len(mao_dir)})", True, C_DIRETOR)
        tela.blit(t_dir, (x0 + 8, y0))
        for i in range(len(mao_dir)):
            cx = x0 + 8 + i * 28
            cy = y0 + 18
            rect_dir = pygame.Rect(cx, cy, 24, 36)
            pygame.draw.rect(tela, (25, 8, 20), rect_dir, border_radius=4)
            pygame.draw.rect(tela, C_DIRETOR, rect_dir, 1, border_radius=4)
            # Face baixo: símbolo de inseto
            fb = self.fMi.render("🐛", True, C_DIM)
            tela.blit(fb, (cx + 4, cy + 8))

    def _draw_tela_fim(self, tela, W, H):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        msg_fim = self.estado.get("msg_fim", "FIM DE JOGO")
        vitoria = self.estado.get("vitoria", False)
        cor_fim = C_OURO if vitoria else C_PERIGO
        emoji_fim = "🏆" if vitoria else "💀"

        t1 = self.fT.render(f"{emoji_fim} FIM DE JOGO {emoji_fim}", True, cor_fim)
        tela.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 80))

        t2 = self.fG.render(msg_fim, True, C_TEXTO)
        tela.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 30))

        rodada = self.estado.get("rodada", 1)
        roub   = self.estado.get("cartas_roubadas_total", 0)
        bosses = len(self.estado.get("bosses_eliminados", []))
        stats_fim = [
            f"Rodadas: {rodada}",
            f"Cartas roubadas: {roub}",
            f"Bosses capturados: {bosses}",
        ]
        y_stat = H // 2 + 20
        for st in stats_fim:
            ss = self.fM.render(st, True, C_DIM)
            tela.blit(ss, (W // 2 - ss.get_width() // 2, y_stat))
            y_stat += 28

        t3 = self.fP.render("Clique para voltar ao menu", True, C_DIM)
        tela.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 130))
