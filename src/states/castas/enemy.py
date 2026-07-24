"""
castas_enemy.py — Mixin de gestão de invasores Insectum para CastasState

Cada casta tem:
- Uma classe Pygame mapeada (Goblin, Esqueleto, Kobold, Troll, DragaoAnciao, ReiGoblin)
- Uma habilidade de entrada imediata que afeta o herói mais próximo ao spawnar
"""
from __future__ import annotations
import random


# ── MAPEAMENTO INSETO → CLASSE BASE ────────────────────────────────────────
INSETO_CLASSE = {
    "vespa_cacadora":     "Goblin",
    "louva_deus":         "Kobold",
    "viuva_canibal":      "Esqueleto",
    "escaravelho_necrofago": "Goblin",
    "besouro_unicornio":  "Kobold",
    "gafanhoto_praga":    "Esqueleto",
    "carrapato_vampiro":  "Goblin",
    "libelula_blindada":  "DragaoAnciao",
    "besouro_gorgulho":   "Kobold",
    "cigarra_ressonante": "Esqueleto",
    "enxame_rainha":      "ReiGoblin",
    "vagalume_sombras":   "Goblin",
    "larva_carniceira":   "Kobold",
    "tarantula_golias":   "Esqueleto",
    "formiga_correicao":  "Goblin",
    "aranha_clepto":      "Kobold",
    "centopeia_olhos":    "Esqueleto",
    "abelha_tecela":      "Goblin",
    "mariposa_esfinge":   "Kobold",
    "efemera_mimetica":   "Esqueleto",
    "vespa_joia":         "Goblin",
    "viuva_negra":        "Esqueleto",
    "besouro_rinoceronte":"Troll",
    "mosca_tse_tse":      "Esqueleto",
}


def _instanciar_inseto(inseto_id, zona_id=None):
    """Retorna uma instância da classe correta para o inseto com nome customizado."""
    from src.cerco_isectum import DADOS_INIMIGOS
    from src.personagens.minions import Goblin, Esqueleto, Kobold, Troll
    from src.personagens import DragaoAnciao, ReiGoblin

    dados = DADOS_INIMIGOS.get(inseto_id, {})
    nome  = dados.get("nome", inseto_id.replace("_", " ").title())
    classe_nome = INSETO_CLASSE.get(inseto_id, "Goblin")

    mapa = {
        "Goblin":      Goblin,
        "Esqueleto":   Esqueleto,
        "Kobold":      Kobold,
        "Troll":       Troll,
        "DragaoAnciao": DragaoAnciao,
        "ReiGoblin":   ReiGoblin,
    }
    cls = mapa.get(classe_nome, Goblin)
    mob = cls(nome, "B")
    mob._inseto_id    = inseto_id
    mob._zona_campo   = zona_id
    mob._habilidade_ativada = False   # flag: habilidade de entrada já foi aplicada
    return mob


class CastasEnemyMixin:
    """Mixin responsável por sincronizar os invasores Insectum no tabuleiro
    e aplicar habilidades de entrada imediatas."""

    # ── SINCRONIZAR INIMIGOS ──────────────────────────────────────────────
    def _sincronizar_inimigos_tabuleiro(self):
        from src.resolvedor_acoes import ZONAS_GRID, obter_zona_por_coordenada
        from src.cerco_isectum import aplicar_delta

        e   = self.estado
        tab = self.motor.tabuleiro

        # mapa zona → inimigos vivos
        inimigos_por_zona = {zona: [] for zona in ZONAS_GRID}
        for p in list(self.motor.combatentes):
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0:
                zona = getattr(p, "_zona_campo", None) or obter_zona_por_coordenada(p.pos_x, p.pos_y)
                if zona in inimigos_por_zona:
                    inimigos_por_zona[zona].append(p)

        excessos = []
        faltas   = []
        for zona, (x1, y1, x2, y2) in ZONAS_GRID.items():
            esperados = e["invasores"].get(zona, 0)
            if zona == "patio":
                esperados += e.get("brutamontes", 0) + e.get("infiltradores", 0)

            atuais = inimigos_por_zona[zona]
            if len(atuais) > esperados:
                for _ in range(len(atuais) - esperados):
                    excessos.append((zona, atuais.pop()))
            elif len(atuais) < esperados:
                faltas.append((zona, esperados - len(atuais)))

        for zona_dest, qtd in faltas:
            x1, y1, x2, y2 = ZONAS_GRID[zona_dest]
            x1c, x2c = max(0, min(19, x1)), max(0, min(19, x2))
            y1c, y2c = max(0, min(19, y1)), max(0, min(19, y2))
            candidatas = []
            for cy in range(y1c, y2c + 1):
                for cx in range(x1c, x2c + 1):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        candidatas.append((cx, cy))
            random.shuffle(candidatas)

            # Determina qual inseto spawnar (pega do histórico de invasões desta zona)
            inseto_id = self._proximo_inseto_para_zona(zona_dest)

            for _ in range(qtd):
                if not candidatas:
                    break
                if excessos:
                    zona_orig, mob = excessos.pop(0)
                    cx, cy = candidatas.pop()
                    old_x, old_y = mob.pos_x, mob.pos_y
                    tab.grid[old_y][old_x] = None
                    mob._zona_campo = zona_dest
                    tab.adicionar_personagem(mob, cx, cy)
                    if mob not in self.motor.combatentes:
                        self.motor.combatentes.append(mob)
                else:
                    if not candidatas:
                        break
                    cx, cy = candidatas.pop()
                    mob = _instanciar_inseto(inseto_id, zona_dest)
                    tab.adicionar_personagem(mob, cx, cy)
                    self.motor.combatentes.append(mob)
                    if hasattr(self.motor, 'time_b'):
                        self.motor.time_b.append(mob)

                    tot = self.estado.get("total_inimigos_gerados", 0) + 1
                    self.estado = aplicar_delta(self.estado, {"total_inimigos_gerados": tot})
                    if tot % 4 == 0:
                        self._push("CERCO", f"🍄 Insetos consumiram a matéria orgânica! Uma árvore se tornou morta fúngica! (Total: {tot // 4} árvore(s))")

                    # Dispara habilidade de entrada imediata
                    self._aplicar_habilidade_entrada(mob, zona_dest)

        # Remove mortos do tabuleiro
        for p in list(self.motor.combatentes):
            if getattr(p, "time", "A") == "B" and p.hp_atual <= 0:
                if 0 <= p.pos_y < tab.altura and 0 <= p.pos_x < tab.largura:
                    if tab.grid[p.pos_y][p.pos_x] is p:
                        tab.grid[p.pos_y][p.pos_x] = None
                self.motor.combatentes.remove(p)
                if hasattr(self.motor, 'time_b') and p in self.motor.time_b:
                    self.motor.time_b.remove(p)

    def _proximo_inseto_para_zona(self, zona_id):
        """Retorna o id do inseto mais recentemente designado para esta zona."""
        insetos_zona = self.estado.get("castas_invasoras", {})
        return insetos_zona.get(zona_id, "formiga_correicao")

    # ── HABILIDADES DE ENTRADA ────────────────────────────────────────────
    def _aplicar_habilidade_entrada(self, mob, zona_id):
        """Dispara o efeito imediato da casta ao spawnar. Afeta o herói mais próximo."""
        inseto_id = getattr(mob, "_inseto_id", "formiga_correicao")
        heroi = self._heroi_mais_proximo(mob)
        if heroi is None:
            return

        from src.cerco_isectum import DADOS_INIMIGOS, aplicar_delta
        dados = DADOS_INIMIGOS.get(inseto_id, {})
        nome  = dados.get("nome", inseto_id)
        emoji = dados.get("emoji", "🐛")
        e     = self.estado
        hs    = dict(e.get("herois_status", {}))

        def get_hs(h): return dict(hs.get(h.nome, {}))
        def set_hs(h, v): hs[h.nome] = v

        # ── Por inseto ──────────────────────────────────────────────────
        if inseto_id == "vespa_cacadora":
            # Herói deve dar 1 carta da mão
            mao_h = get_hs(heroi).get("mao", [])
            if mao_h:
                carta = random.choice(mao_h)
                mao_h.remove(carta)
                hstatus = get_hs(heroi)
                hstatus["mao"] = mao_h
                set_hs(heroi, hstatus)
                self._push("INSETO", f"{emoji} {nome}: {heroi.nome} perdeu a carta «{carta['nome']}»!")

        elif inseto_id == "mosca_tse_tse":
            # Herói mais próximo pula 1 turno
            jogaram = list(e.get("herois_jogaram", []))
            if heroi.nome not in jogaram:
                jogaram.append(heroi.nome)
                self.estado = aplicar_delta(e, {"herois_jogaram": jogaram})
                e = self.estado
            self._push("INSETO", f"{emoji} {nome}: {heroi.nome} foi picado e perdeu o turno!")

        elif inseto_id == "carrapato_vampiro":
            # Herói descarta 2 cartas
            hstatus = get_hs(heroi)
            mao_h   = hstatus.get("mao", [])
            qtd = min(2, len(mao_h))
            descartadas = random.sample(mao_h, qtd) if qtd else []
            for c in descartadas:
                mao_h.remove(c)
                hstatus.setdefault("descarte", []).append(c)
            hstatus["mao"] = mao_h
            set_hs(heroi, hstatus)
            self._push("INSETO", f"{emoji} {nome}: {heroi.nome} descartou {qtd} carta(s)!")

        elif inseto_id == "enxame_rainha":
            # Todos os heróis descartam 1 carta
            for h in self.herois:
                hstatus = get_hs(h)
                mao_h   = hstatus.get("mao", [])
                if mao_h:
                    c = random.choice(mao_h)
                    mao_h.remove(c)
                    hstatus.setdefault("descarte", []).append(c)
                    hstatus["mao"] = mao_h
                    set_hs(h, hstatus)
            self._push("INSETO", f"{emoji} {nome}: todos os heróis descartaram 1 carta!")

        elif inseto_id == "besouro_unicornio":
            # Todos descartam 1 carta escolhida pelo Diretor (aqui: aleatória)
            for h in self.herois:
                hstatus = get_hs(h)
                mao_h   = hstatus.get("mao", [])
                if mao_h:
                    c = random.choice(mao_h)
                    mao_h.remove(c)
                    hstatus.setdefault("descarte", []).append(c)
                    hstatus["mao"] = mao_h
                    set_hs(h, hstatus)
            self._push("INSETO", f"{emoji} {nome}: todos descartam 1 carta (feromônios)!")

        elif inseto_id == "formiga_correicao":
            # Rouba 3 de tesouro
            novo_tesouro = max(0, e.get("tesouro", 0) - 3)
            self.estado  = aplicar_delta(e, {"tesouro": novo_tesouro})
            e = self.estado
            self._push("INSETO", f"{nome}: -3 cristais do tesouro!")

        elif inseto_id == "gafanhoto_praga":
            # Descarta 2 cartas do mercado (envia para descarte base do herói)
            slots = list(e.get("slots_upgrade", []))
            nao_adq = [s for s in slots if not s.get("adquirido") and not s.get("bloqueado")]
            if nao_adq:
                alvo = random.choice(nao_adq)
                alvo["bloqueado"] = True
                self.estado = aplicar_delta(e, {"slots_upgrade": slots})
                e = self.estado
                self._push("INSETO", f"{emoji} {nome}: slot «{alvo['nome']}» do mercado bloqueado!")
            else:
                self._push("INSETO", f"{emoji} {nome}: mercado já vazio — sem efeito.")

        elif inseto_id == "libelula_blindada":
            # Imune por 1 turno (marca no mob)
            mob._imune_turno = True
            self._push("INSETO", f"{emoji} {nome}: blindagem quitinosa — imune a ataques este turno!")

        elif inseto_id == "besouro_rinoceronte":
            # +2 HP ao entrar em zona interna
            mob.hp_atual = min(mob.hp_max, mob.hp_atual + 2)
            self._push("INSETO", f"{emoji} {nome}: regenerou 2 HP ao cruzar a muralha!")

        elif inseto_id == "tarantula_golias":
            # Bloqueia a zona por 1 rodada (invasores na zona bloqueiam cartas de trabalho)
            bloqueadas = list(e.get("zonas_bloqueadas", []))
            if zona_id not in bloqueadas:
                bloqueadas.append(zona_id)
            self.estado = aplicar_delta(e, {"zonas_bloqueadas": bloqueadas})
            e = self.estado
            from src.cerco_isectum import NOMES_ZONA
            self._push("INSETO", f"{emoji} {nome}: zona {NOMES_ZONA.get(zona_id, zona_id)} bloqueada!")

        else:
            # Genérico: narrativa no log
            from src.cerco_isectum import DADOS_INIMIGOS
            efeito = dados.get("efeito", "")
            self._push("INSETO", f"{emoji} {nome}: {efeito[:80]}")

        # Aplica mudanças de herois_status
        self.estado = aplicar_delta(self.estado, {"herois_status": hs})
        mob._habilidade_ativada = True

    def _heroi_mais_proximo(self, mob):
        """Retorna o herói vivo mais próximo do mob."""
        if not self.herois:
            return None
        vivos = [h for h in self.herois if h.hp_atual > 0]
        if not vivos:
            return None
        def dist(h):
            return abs(h.pos_x - mob.pos_x) + abs(h.pos_y - mob.pos_y)
        return min(vivos, key=dist)
