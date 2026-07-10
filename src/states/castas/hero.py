"""
castas_state_hero.py — Mixin de gestão de heróis (cartas, ataque a boss) para CastasState
"""
from __future__ import annotations
import random

from ...castas_isectum import (
    aplicar_delta_castas, aplicar_efeito_runa, aplicar_efeito_defesa,
    criar_carta_capturada, verificar_condicoes, DADOS_INIMIGOS,
    get_hp_inseto,
)
from .data import C_VERDE, C_PERIGO, C_HEROI, C_RUNA, C_DEFESA, C_CAPTURA, C_OURO


class CastasStateHeroMixin:
    """Mixin responsável pela gestão de heróis: mão, cartas, ataque a boss."""

    def _comprar_mao_defensor(self):
        from ...castas_isectum import aplicar_delta_castas
        heroi_nome = self._heroi_ativo_nome()
        if not heroi_nome:
            return
        hs = dict(self.estado["herois_status"][heroi_nome])

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

        vit, der, msg = verificar_condicoes(self.estado)
        if vit or der:
            self.estado = aplicar_delta_castas(self.estado, {
                "vitoria": vit, "derrota": der, "msg_fim": msg
            })
            self.fase = "FIM"

    def _atacar_boss(self, inseto_id):
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
            carta_cap = criar_carta_capturada(inseto_id)
            hs = dict(self.estado["herois_status"].get(heroi_nome, {}))
            deck = list(hs.get("deck", []))
            deck.insert(0, carta_cap)
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

    # ── HELPERS ───────────────────────────────────────────────────────
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
