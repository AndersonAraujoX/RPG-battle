"""
cerco_state_enemy.py — Mixin de gestão de inimigos (sincronização, efeitos especiais,
dev summon) para CercoState
"""
from __future__ import annotations
import random


class CercoStateEnemyMixin:
    """Mixin responsável pela sincronização de inimigos no tabuleiro,
    aplicação de efeitos especiais e summon via dev menu."""

    # ── SINCRONIZAR INIMIGOS ──────────────────────────────────────────
    def _sincronizar_inimigos_tabuleiro(self):
        # Guarda de reentrância: evita chamadas recursivas via _aplicar_efeito_inimigo
        if getattr(self, '_sincronizando', False):
            return
        self._sincronizando = True
        try:
            self._sincronizar_inimigos_tabuleiro_impl()
        finally:
            self._sincronizando = False

    def _sincronizar_inimigos_tabuleiro_impl(self):
        from ...resolvedor_acoes import ZONAS_GRID, obter_zona_por_coordenada
        from ...personagens.minions import Goblin, Esqueleto, Kobold, Troll
        from ...personagens import DragaoAnciao, ReiGoblin
        from ...cerco_isectum import aplicar_delta

        e = self.estado
        tab = self.motor.tabuleiro

        # Zonas internas da fortaleza — inimigos dentro delas estão em combate
        # ativo e NÃO devem ser tocados pela sincronização de spawn.
        ZONAS_INTERNAS = {
            "camara_central", "curtume", "carpintaria", "fundicao",
            "patio", "torre_nw", "torre_ne", "torre_sw", "torre_se",
            "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
        }
        # Zonas externas de spawn que a sincronização gerencia
        ZONAS_SPAWN = {z: bounds for z, bounds in ZONAS_GRID.items() if z not in ZONAS_INTERNAS}

        inimigos_por_zona = {zona: [] for zona in ZONAS_SPAWN}

        for p in list(self.motor.combatentes):
            if getattr(p, "time", "A") == "B" and p.hp_atual > 0:
                zona = getattr(p, "_zona_campo", None)
                if not zona:
                    zona = obter_zona_por_coordenada(p.pos_x, p.pos_y)
                # Ignora inimigos em zonas internas — eles estão em combate ativo
                if zona in ZONAS_INTERNAS:
                    continue
                if zona in inimigos_por_zona:
                    inimigos_por_zona[zona].append(p)

        excessos = []
        faltas = []

        for zona, (x1, y1, x2, y2) in ZONAS_SPAWN.items():
            esperados = e["invasores"].get(zona, 0)

            atuais = inimigos_por_zona[zona]
            if len(atuais) > esperados:
                sobrando = len(atuais) - esperados
                for _ in range(sobrando):
                    if atuais:
                        excessos.append((zona, atuais.pop()))
            elif len(atuais) < esperados:
                faltas.append((zona, esperados - len(atuais)))

        faltas_atualizadas = []
        for zona_dest, qtd in faltas:
            x1, y1, x2, y2 = ZONAS_GRID[zona_dest]
            x1_c = max(0, min(19, x1))
            x2_c = max(0, min(19, x2))
            y1_c = max(0, min(19, y1))
            y2_c = max(0, min(19, y2))

            celulas_candidatas = []
            for cy in range(y1_c, y2_c + 1):
                for cx in range(x1_c, x2_c + 1):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas_candidatas.append((cx, cy))
            random.shuffle(celulas_candidatas)

            transferidos = 0
            for _ in range(qtd):
                if not celulas_candidatas:
                    break

                if excessos:
                    zona_origem, monstro = excessos.pop(0)
                    cx, cy = celulas_candidatas.pop()

                    old_vx, old_vy = self._obter_posicao_virtual(monstro, monstro.pos_x, monstro.pos_y)
                    monstro._zona_campo = zona_dest if "campo" in zona_dest else None
                    new_vx, new_vy = self._obter_posicao_virtual(monstro, cx, cy)

                    old_x, old_y = monstro.pos_x, monstro.pos_y
                    if 0 <= old_y < len(tab.grid) and 0 <= old_x < len(tab.grid[0]):
                        tab.grid[old_y][old_x] = None
                    tab.grid[cy][cx] = monstro
                    monstro.pos_x = cx
                    monstro.pos_y = cy

                    self._start_monster_walk(monstro, (old_vx, old_vy), (new_vx, new_vy))
                    transferidos += 1
                else:
                    break

            restante = qtd - transferidos
            if restante > 0:
                faltas_atualizadas.append((zona_dest, restante))

        for zona_dest, qtd in faltas_atualizadas:
            x1, y1, x2, y2 = ZONAS_GRID[zona_dest]
            x1_c = max(0, min(19, x1))
            x2_c = max(0, min(19, x2))
            y1_c = max(0, min(19, y1))
            y2_c = max(0, min(19, y2))

            celulas_candidatas = []
            for cy in range(y1_c, y2_c + 1):
                for cx in range(x1_c, x2_c + 1):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas_candidatas.append((cx, cy))

            if not celulas_candidatas:
                for cy in range(20):
                    for cx in range(20):
                        if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                            celulas_candidatas.append((cx, cy))
            random.shuffle(celulas_candidatas)

            for _ in range(qtd):
                if not celulas_candidatas:
                    break
                cx, cy = celulas_candidatas.pop()

                from ...cerco_isectum import DADOS_INIMIGOS
                deck_ini = list(self.estado.get("deck_inimigos", []))
                desc_ini = list(self.estado.get("descarte_inimigos", []))
                if not deck_ini:
                    if desc_ini:
                        deck_ini = list(desc_ini)
                        random.shuffle(deck_ini)
                        desc_ini = []
                    else:
                        deck_ini = list(DADOS_INIMIGOS.keys())
                        random.shuffle(deck_ini)
                carta_ini = deck_ini.pop()
                desc_ini.append(carta_ini)
                self.estado = aplicar_delta(self.estado, {
                    "deck_inimigos": deck_ini,
                    "descarte_inimigos": desc_ini
                })

                info_ini = DADOS_INIMIGOS.get(carta_ini, {"classe": "Goblin", "nome": "Formiga-Correição", "emoji": "\U0001f41c"})

                mapa_classes = {
                    "Goblin": Goblin,
                    "Esqueleto": Esqueleto,
                    "Kobold": Kobold,
                    "Troll": Troll,
                    "DragaoAnciao": DragaoAnciao,
                    "ReiGoblin": ReiGoblin
                }

                classe_inimigo = mapa_classes.get(info_ini["classe"], Goblin)
                nome_inimigo = info_ini['nome']
                is_infiltrador = False

                if zona_dest == "patio":
                    trolls_atuais = sum(1 for p in self.motor.combatentes if getattr(p, "classe_nome", None) == "Troll" and p.hp_atual > 0)
                    goblins_atuais = sum(1 for p in self.motor.combatentes if getattr(p, "classe_nome", None) == "Goblin" and p.hp_atual > 0 and getattr(p, "_is_infiltrador", False))

                    if trolls_atuais < e.get("brutamontes", 0):
                        classe_inimigo = Troll
                        nome_inimigo = "Besouro-Rinoceronte"
                    elif goblins_atuais < e.get("infiltradores", 0):
                        classe_inimigo = Goblin
                        nome_inimigo = "Formiga Infiltradora"
                        is_infiltrador = True

                inimigo = classe_inimigo(nome_inimigo, "B", nivel=3)
                if is_infiltrador:
                    inimigo._is_infiltrador = True
                    inimigo.tipo_inseto = "infiltrador"
                elif classe_inimigo == Troll:
                    inimigo.tipo_inseto = "besouro_rinoceronte"
                else:
                    inimigo.tipo_inseto = carta_ini

                sucesso = tab.adicionar_personagem(inimigo, cx, cy)
                if sucesso:
                    self.motor.combatentes.append(inimigo)
                    if not hasattr(self.motor, 'time_b'):
                        self.motor.time_b = []
                    self.motor.time_b.append(inimigo)

                    tot = self.estado.get("total_inimigos_gerados", 0) + 1
                    self.estado = aplicar_delta(self.estado, {"total_inimigos_gerados": tot})
                    if tot % 4 == 0:
                        self._push("CERCO", f"🍄 Insetos consumiram a matéria orgânica! Uma árvore se tornou morta fúngica! (Total: {tot // 4} árvore(s))")

                    self._aplicar_efeito_inimigo(carta_ini)

                    inimigo._zona_campo = zona_dest if "campo" in zona_dest else None
                    new_vx, new_vy = self._obter_posicao_virtual(inimigo, cx, cy)

                    origem_x, origem_y = new_vx, new_vy
                    if "campo" in zona_dest:
                        if "norte" in zona_dest:
                            origem_y = -4
                        elif "sul" in zona_dest:
                            origem_y = 23
                        elif "oeste" in zona_dest:
                            origem_x = -4
                        elif "leste" in zona_dest:
                            origem_x = 23
                    else:
                        if "norte" in zona_dest:
                            origem_y = -2
                        elif "sul" in zona_dest:
                            origem_y = 21
                        elif "oeste" in zona_dest:
                            origem_x = -2
                        elif "leste" in zona_dest:
                            origem_x = 21

                    if (origem_x, origem_y) != (new_vx, new_vy):
                        self._start_monster_walk(inimigo, (origem_x, origem_y), (new_vx, new_vy))

        for zona_origem, monstro in excessos:
            # Monstros que avançaram ou migraram continuam vivos no combate 2D ativo
            monstro._zona_campo = None

    # ── EFEITO ESPECIAL ───────────────────────────────────────────────
    def _aplicar_efeito_inimigo(self, carta_key: str, _visitados=None):
        if _visitados is None:
            _visitados = set()
        if carta_key in _visitados or len(_visitados) >= 4:
            return
        _visitados = set(_visitados)
        _visitados.add(carta_key)

        from ...cerco_isectum import DADOS_INIMIGOS, aplicar_delta
        info = DADOS_INIMIGOS.get(carta_key)
        if not info:
            return

        nome = info.get("nome", "")
        emoji = info.get("emoji", "")
        efeito_desc = info.get("efeito", "")

        self._push("SISTEMA", f"{emoji} {nome} ativado! Efeito: {efeito_desc}")

        herois_nomes = [h.nome for h in self.herois]
        if not herois_nomes:
            return

        if carta_key == "vespa_cacadora":
            simbolo_pedido = random.choice(["T", "M", "E"])
            self._push("SISTEMA", f"Vespa-Caçadora exige cartas de símbolo '{simbolo_pedido}'!")
            for h_nome in herois_nomes:
                mao = self._obter_mao_heroi(h_nome)
                for i, c in enumerate(mao):
                    if c.get("simbolo") == simbolo_pedido:
                        c_removida = mao.pop(i)
                        self._definir_mao_heroi(h_nome, mao)
                        self._push("SISTEMA", f"Herói {h_nome} entregou {c_removida['nome']} ({c_removida['simbolo']})!")
                        break
                else:
                    self._push("SISTEMA", f"Herói {h_nome} não possuía o símbolo '{simbolo_pedido}'. Vespa-Caçadora perdeu a chance!")

        elif carta_key == "louva_deus":
            if len(herois_nomes) > 1:
                h1, h2 = random.sample(herois_nomes, 2)
                m1 = self._obter_mao_heroi(h1)
                m2 = self._obter_mao_heroi(h2)
                self._definir_mao_heroi(h1, m2)
                self._definir_mao_heroi(h2, m1)
                self._push("SISTEMA", f"Louva-a-Deus trocou as mãos de {h1} e {h2}!")
            else:
                h = herois_nomes[0]
                mao = self._obter_mao_heroi(h)
                if mao:
                    random.shuffle(mao)
                    self._definir_mao_heroi(h, mao)
                    self._push("SISTEMA", f"Louva-a-Deus embaralhou a mão de {h}!")

        elif carta_key == "viuva_canibal":
            desc_ini = self.estado.get("descarte_inimigos", [])
            machos = ["louva_deus", "gafanhoto_praga", "carrapato_vampiro", "besouro_gorgulho", "tarantula_golias", "mariposa_esfinge", "escaravelho_necrofago", "mosca_tse_tse"]
            validos = [c for c in desc_ini if c in machos and c not in _visitados]
            if validos:
                alvo = random.choice(validos)
                self._push("SISTEMA", f"Viúva-Canibal copia o efeito de {alvo.upper()}!")
                self._aplicar_efeito_inimigo(alvo, _visitados=_visitados)
            else:
                self._push("SISTEMA", "Nenhum inseto macho elegível no descarte para copiar.")

        elif carta_key == "escaravelho_necrofago":
            desc_ini = self.estado.get("descarte_inimigos", [])
            validos = [c for c in desc_ini if c not in _visitados]
            if validos:
                topo = validos[-1]
                self._push("SISTEMA", f"Escaravelho reativa o topo do descarte: {topo.upper()}")
                self._aplicar_efeito_inimigo(topo, _visitados=_visitados)
            else:
                self._push("SISTEMA", "Pilha de descarte de inimigos vazia.")

        elif carta_key == "besouro_unicornio":
            for h_nome in herois_nomes:
                mao = self._obter_mao_heroi(h_nome)
                if mao:
                    c = mao.pop(random.randrange(len(mao)))
                    self._definir_mao_heroi(h_nome, mao)
                    self._push("SISTEMA", f"Herói {h_nome} descartou a carta {c['nome']}!")

        elif carta_key == "gafanhoto_praga":
            self.estado = aplicar_delta(self.estado, {
                "pontos_movimento": 0,
                "pontos_trabalho": 0,
                "pontos_escavacao": 0
            })
            self._push("SISTEMA", "Gafanhoto-da-Praga limpou o tabuleiro! Pontos de ação zerados neste turno.")

        elif carta_key == "carrapato_vampiro":
            alvo = random.choice(herois_nomes)
            mao = self._obter_mao_heroi(alvo)
            removidas = []
            for _ in range(2):
                if mao:
                    removidas.append(mao.pop(random.randrange(len(mao))))
            self._definir_mao_heroi(alvo, mao)
            if removidas:
                nomes_rem = ", ".join(c["nome"] for c in removidas)
                self._push("SISTEMA", f"Carrapato-Vampiro roubou {len(removidas)} cartas ({nomes_rem}) de {alvo}!")

        elif carta_key == "libelula_blindada":
            self.fase = "ACAO_LIVRE"
            self._push("SISTEMA", "Libélula-Blindada bloqueou o turno! Fase de jogar cartas encerrada.")

        elif carta_key == "besouro_gorgulho":
            self._push("SISTEMA", "Besouro-Gorgulho cavou o deck de inimigos!")

        elif carta_key == "cigarra_ressonante":
            desc_ini = self.estado.get("descarte_inimigos", [])
            validos = [c for c in desc_ini if c not in _visitados]
            if validos:
                alvo = random.choice(validos)
                self._push("SISTEMA", f"Cigarra-Ressonante reativa {alvo.upper()}!")
                self._aplicar_efeito_inimigo(alvo, _visitados=_visitados)

        elif carta_key == "enxame_rainha":
            for h_nome in herois_nomes:
                mao = self._obter_mao_heroi(h_nome)
                if len(mao) > 3:
                    mao = mao[:3]
                    self._definir_mao_heroi(h_nome, mao)
                    self._push("SISTEMA", f"Enxame da Rainha drenou a mão de {h_nome} para 3 cartas.")

        elif carta_key == "vagalume_sombras":
            self._push("SISTEMA", "Vagalumes das Sombras brilham no escuro!")

        elif carta_key == "larva_carniceira":
            alvo = random.choice(herois_nomes)
            mao = self._obter_mao_heroi(alvo)
            if mao:
                c = mao.pop(random.randrange(len(mao)))
                self._definir_mao_heroi(alvo, mao)
                self._push("SISTEMA", f"Larvas Carniceiras comeram a carta {c['nome']} de {alvo}!")

        elif carta_key == "tarantula_golias":
            desc_ini = self.estado.get("descarte_inimigos", [])
            validos = [c for c in desc_ini if c not in _visitados]
            if validos:
                alvo = random.choice(validos)
                self._aplicar_efeito_inimigo(alvo, _visitados=_visitados)

        elif carta_key == "formiga_correicao":
            for _ in range(3):
                elegiveis = [h for h in herois_nomes if self._obter_mao_heroi(h)]
                if elegiveis:
                    alvo = random.choice(elegiveis)
                    mao = self._obter_mao_heroi(alvo)
                    c = mao.pop(random.randrange(len(mao)))
                    self._definir_mao_heroi(alvo, mao)
                    self._push("SISTEMA", f"Formigas-Correição roubaram {c['nome']} de {alvo}!")

        elif carta_key == "aranha_clepto":
            if len(self.herois) > 1:
                h1, h2 = random.sample(self.herois, 2)
                p1_x, p1_y = h1.pos_x, h1.pos_y
                p2_x, p2_y = h2.pos_x, h2.pos_y
                h1.pos_x, h1.pos_y = p2_x, p2_y
                h2.pos_x, h2.pos_y = p1_x, p1_y
                self.map_backbuffer_sujo = True
                self._push("SISTEMA", f"Aranha-Cleptoparasita trocou as posições de {h1.nome} e {h2.nome} no tabuleiro!")

        elif carta_key == "centopeia_olhos":
            alvo = random.choice(herois_nomes)
            self._push("SISTEMA", f"Centopeia dos Cem Olhos hipnotizou {alvo}!")

        elif carta_key == "abelha_tecela":
            self._push("SISTEMA", "Abelha-Tecelã convoca a colmeia!")

        elif carta_key == "mariposa_esfinge":
            self._push("SISTEMA", "Mariposa-Esfinge acelerou o cerco!")

        elif carta_key == "efemera_mimetica":
            self._push("SISTEMA", "Efêmera Mimética imita o ambiente!")

        elif carta_key == "vespa_joia":
            alvo = random.choice(herois_nomes)
            mao = self._obter_mao_heroi(alvo)
            if mao:
                c = mao.pop(random.randrange(len(mao)))
                self._definir_mao_heroi(alvo, mao)
                self._push("SISTEMA", f"Vespa-Joia roubou {c['nome']} de {alvo}!")

        elif carta_key == "viuva_negra":
            alvo_h = random.choice(self.herois)
            alvo_h.hp_atual = max(1, alvo_h.hp_atual - 10)
            self._push("SISTEMA", f"Viúva-Negra picou {alvo_h.nome} causando 10 de dano!")

        elif carta_key == "besouro_rinoceronte":
            if self.heroi_atual:
                mao = self._obter_mao_heroi(self.heroi_atual.nome)
                if mao:
                    c = mao.pop(random.randrange(len(mao)))
                    self._definir_mao_heroi(self.heroi_atual.nome, mao)
                    self._push("SISTEMA", f"Besouro-Rinoceronte forçou {self.heroi_atual.nome} a descartar {c['nome']}!")

        elif carta_key == "mosca_tse_tse":
            if self.heroi_atual:
                self.estado = aplicar_delta(self.estado, {
                    "pontos_movimento": 0,
                    "pontos_trabalho": 0,
                    "pontos_escavacao": 0
                })
                self.fase = "ACAO_LIVRE"
                self._push("SISTEMA", f"Mosca-Tsé-Tsé picou {self.heroi_atual.nome}! Perdeu a vez!")

    # ── DEV SUMMON ────────────────────────────────────────────────────
    def _dev_summon_specific_enemy(self, carta_key: str):
        from ...cerco_isectum import DADOS_INIMIGOS, aplicar_delta
        from ...personagens.minions import Goblin, Esqueleto, Kobold, Troll
        from ...personagens import DragaoAnciao, ReiGoblin
        from ...resolvedor_acoes import ZONAS_GRID

        info = DADOS_INIMIGOS.get(carta_key)
        if not info:
            return

        zonas_spawn = ["patio", "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste"]
        zona_dest = random.choice(zonas_spawn)

        tab = self.motor.tabuleiro
        x1, y1, x2, y2 = ZONAS_GRID[zona_dest]

        celulas = []
        for cy in range(y1, y2 + 1):
            for cx in range(x1, x2 + 1):
                if 0 <= cx < 20 and 0 <= cy < 20:
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas.append((cx, cy))

        if not celulas:
            for cy in range(20):
                for cx in range(20):
                    if tab.get_terrain_em(cx, cy) != "parede" and tab.grid[cy][cx] is None:
                        celulas.append((cx, cy))

        if not celulas:
            self._feedback("Não há espaço livre no tabuleiro para invocar!", C_PERIGO)
            return

        cx, cy = random.choice(celulas)

        mapa_classes = {
            "Goblin": Goblin,
            "Esqueleto": Esqueleto,
            "Kobold": Kobold,
            "Troll": Troll,
            "DragaoAnciao": DragaoAnciao,
            "ReiGoblin": ReiGoblin
        }

        classe_inimigo = mapa_classes.get(info["classe"], Goblin)
        nome_inimigo = f"{info['nome']} (Dev)"

        inimigo = classe_inimigo(nome_inimigo, "B", nivel=3)
        inimigo.tipo_inseto = carta_key
        sucesso = tab.adicionar_personagem(inimigo, cx, cy)
        if sucesso:
            self.motor.combatentes.append(inimigo)
            if not hasattr(self.motor, 'time_b'):
                self.motor.time_b = []
            self.motor.time_b.append(inimigo)

            if zona_dest in self.estado["invasores"]:
                self.estado["invasores"][zona_dest] += 1
            elif "muralha" in zona_dest or "patio" in zona_dest:
                self.estado["invasores"][zona_dest] = self.estado["invasores"].get(zona_dest, 0) + 1

            desc_ini = list(self.estado.get("descarte_inimigos", []))
            desc_ini.append(carta_key)
            self.estado = aplicar_delta(self.estado, {"descarte_inimigos": desc_ini})

            self._aplicar_efeito_inimigo(carta_key)
            self.map_backbuffer_sujo = True
            from .data import C_VERDE
            self._feedback(f"Dev: Invocou {info['nome']}!", C_VERDE)
