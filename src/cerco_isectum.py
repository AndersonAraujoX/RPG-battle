"""
cerco_isectum.py — Motor de Eventos de Cerco + Estado Completo

Gerencia o estado global do jogo Cerco contra Isectum:
  - Motor de eventos de cerco (ameaças)
  - Deck do herói (cartas de ação)
  - Mercado de upgrades (deckbuilding)
  - Infiltradores, Brutamontes, Tesouro
"""
import random
import copy

# ═══════════════════════════════════════════════════════════════════════════
# NOMES E ÍCONES
# ═══════════════════════════════════════════════════════════════════════════
NOMES_ZONA = {
    "muralha_norte":  "Muralha Norte",
    "muralha_sul":    "Muralha Sul",
    "muralha_oeste":  "Muralha Oeste",
    "muralha_leste":  "Muralha Leste",
    "carpintaria":    "Madeira",
    "curtume":        "Couro",
    "fundicao":       "Ferro",
    "patio":          "Nexos",
    "camara_central": "Ouro",
    "torre_nw":       "Torre NO",
    "torre_ne":       "Torre NE",
    "torre_sw":       "Torre SO",
    "torre_se":       "Torre SE",
}

FLUXO_ZONAS = {
    "muralha_norte": "carpintaria",
    "muralha_sul":   "curtume",
    "muralha_oeste": "fundicao",
    "muralha_leste": "patio",
    "carpintaria":   "camara_central",
    "curtume":       "camara_central",
    "fundicao":      "camara_central",
    "patio":         "camara_central",
}

# ═══════════════════════════════════════════════════════════════════════════
# DECK DO HERÓI — cartas de ação
# ═══════════════════════════════════════════════════════════════════════════
CARTAS_BASICAS = [
    {"id": "trabalho_1",  "nome": "Trabalho",     "simbolo": "🪵", "tipo": "basica",
     "movimento": 0, "trabalho": 1, "escavacao": 0,
     "descricao": "+1 Trabalho"},
    {"id": "trabalho_2",  "nome": "Trabalho",     "simbolo": "🪵", "tipo": "basica",
     "movimento": 0, "trabalho": 1, "escavacao": 0,
     "descricao": "+1 Trabalho"},
    {"id": "trabalho_3",  "nome": "Trabalho",     "simbolo": "🪵", "tipo": "basica",
     "movimento": 0, "trabalho": 1, "escavacao": 0,
     "descricao": "+1 Trabalho"},
    {"id": "marcha_1",    "nome": "Marcha",        "simbolo": "👣", "tipo": "basica",
     "movimento": 2, "trabalho": 0, "escavacao": 0,
     "descricao": "+2 Movimento"},
    {"id": "marcha_2",    "nome": "Marcha",        "simbolo": "👣", "tipo": "basica",
     "movimento": 2, "trabalho": 0, "escavacao": 0,
     "descricao": "+2 Movimento"},
    {"id": "marcha_3",    "nome": "Marcha",        "simbolo": "👣", "tipo": "basica",
     "movimento": 2, "trabalho": 0, "escavacao": 0,
     "descricao": "+2 Movimento"},
    {"id": "escavacao_1", "nome": "Escavação",     "simbolo": "⛏️", "tipo": "basica",
     "movimento": 0, "trabalho": 0, "escavacao": 2,
     "descricao": "+2 Escavação"},
    {"id": "escavacao_2", "nome": "Escavação",     "simbolo": "⛏️", "tipo": "basica",
     "movimento": 0, "trabalho": 0, "escavacao": 2,
     "descricao": "+2 Escavação"},
    {"id": "forca_1",     "nome": "Força Anã",     "simbolo": "💪", "tipo": "basica",
     "movimento": 1, "trabalho": 2, "escavacao": 0,
     "descricao": "+1 Mov  +2 Trab"},
    {"id": "forca_2",     "nome": "Força Anã",     "simbolo": "💪", "tipo": "basica",
     "movimento": 1, "trabalho": 2, "escavacao": 0,
     "descricao": "+1 Mov  +2 Trab"},
    {"id": "sprint_1",    "nome": "Sprint",        "simbolo": "⚡", "tipo": "basica",
     "movimento": 3, "trabalho": 0, "escavacao": 1,
     "descricao": "+3 Mov  +1 Esc"},
    {"id": "versatil_1",  "nome": "Versatilidade", "simbolo": "🎯", "tipo": "basica",
     "movimento": 1, "trabalho": 1, "escavacao": 1,
     "descricao": "+1 Mov +1 Trab +1 Esc"},
]

CARTAS_UPGRADE = [
    {"id": "mestre_1",    "nome": "Mestre Artesão", "simbolo": "🔨", "tipo": "upgrade",
     "movimento": 0, "trabalho": 3, "escavacao": 0, "efeito_extra": "draw_1",
     "descricao": "+3 Trab, compra 1 carta",
     "custo": {"madeira": 2}},
    {"id": "corrida_1",   "nome": "Corrida Livre",  "simbolo": "🏃", "tipo": "upgrade",
     "movimento": 4, "trabalho": 0, "escavacao": 0, "efeito_extra": None,
     "descricao": "+4 Movimento",
     "custo": {"couro": 2}},
    {"id": "perfurador",  "nome": "Perfurador",     "simbolo": "💣", "tipo": "upgrade",
     "movimento": 0, "trabalho": 0, "escavacao": 3, "efeito_extra": None,
     "descricao": "+3 Escavação",
     "custo": {"metal": 2}},
    {"id": "forjador",    "nome": "Grande Forjador", "simbolo": "⚒️", "tipo": "upgrade",
     "movimento": 1, "trabalho": 4, "escavacao": 0, "efeito_extra": None,
     "descricao": "+1 Mov  +4 Trab",
     "custo": {"madeira": 2, "metal": 1}},
    {"id": "explorador",  "nome": "Explorador",      "simbolo": "🗺️", "tipo": "upgrade",
     "movimento": 3, "trabalho": 1, "escavacao": 2, "efeito_extra": None,
     "descricao": "+3 Mov +1 Trab +2 Esc",
     "custo": {"couro": 1, "madeira": 1}},
]


def criar_mercado():
    """Retorna os slots de upgrade do mercado."""
    slots_base = [
        {"id": 0, "nome": "Mestre Artesão",  "simbolo": "🔨", "custo": {"madeira": 2},
         "carta_id": "mestre_1",   "bloqueado": False, "adquirido": False,
         "descricao": "+3 Trab, compra 1 carta"},
        {"id": 1, "nome": "Corrida Livre",   "simbolo": "🏃", "custo": {"couro": 2},
         "carta_id": "corrida_1",  "bloqueado": False, "adquirido": False,
         "descricao": "+4 Movimento"},
        {"id": 2, "nome": "Perfurador",      "simbolo": "💣", "custo": {"metal": 2},
         "carta_id": "perfurador", "bloqueado": False, "adquirido": False,
         "descricao": "+3 Escavação"},
        {"id": 3, "nome": "Grande Forjador", "simbolo": "⚒️", "custo": {"madeira": 2, "metal": 1},
         "carta_id": "forjador",   "bloqueado": False, "adquirido": False,
         "descricao": "+1 Mov  +4 Trab"},
        {"id": 4, "nome": "Explorador",      "simbolo": "🗺️", "custo": {"couro": 1, "madeira": 1},
         "carta_id": "explorador", "bloqueado": False, "adquirido": False,
         "descricao": "+3 Mov +1 Trab +2 Esc"},
    ]
    return slots_base


# ═══════════════════════════════════════════════════════════════════════════
# ESTADO INICIAL DO JOGO
# ═══════════════════════════════════════════════════════════════════════════
def criar_estado(pedregulhos=8, is_solo=True):
    deck_heroi = copy.deepcopy(CARTAS_BASICAS)
    random.shuffle(deck_heroi)

    return {
        # ── Fortaleza ───────────────────────────────────────────────────
        "rodada":          1,
        "tesouro":         20,
        "reserva":         10,
        "derrota":         False,
        "vitoria":         False,
        "msg_derrota":     "",
        "msg_vitoria":     "",
        "pedregulhos":     pedregulhos,
        "pedregulhos_max": pedregulhos,
        "is_solo":         is_solo,
        # Tokens por zona
        "invasores":       {k: 0 for k in NOMES_ZONA},
        "brutamontes":     0,
        "infiltradores":   0,
        # Armas de cerco
        "torre_assalto":  {"estado": "reserva", "ciclo": 0},
        "catapulta":      {"estado": "reserva", "ciclo": 0},
        # ── Deckbuilding ────────────────────────────────────────────────
        "slots_upgrade":   criar_mercado(),
        "recursos_depositados": {"madeira": 0, "couro": 0, "metal": 0},
        # ── Herói ───────────────────────────────────────────────────────
        "pos_heroi":          "camara_central",
        "heroi_x":            9,
        "heroi_y":            9,
        "deck_heroi":         deck_heroi,
        "mao":                [],
        "descarte":           [],
        "pontos_movimento":   0,
        "pontos_trabalho":    0,
        "pontos_escavacao":   0,
        "voo_ativo":          False,
        "tamanho_deck_max":   12,
    }


# ═══════════════════════════════════════════════════════════════════════════
# DECK DE CERCO (ameaças — 50 cartas)
# ═══════════════════════════════════════════════════════════════════════════
def criar_deck():
    pool = []
    for _ in range(4):
        pool += [
            {"tipo": "invasor", "zona": "muralha_norte", "qtd": 1, "nivel": 1,
             "titulo": "Batalhão Norte",   "simbolo": "👿"},
            {"tipo": "invasor", "zona": "muralha_sul",   "qtd": 1, "nivel": 1,
             "titulo": "Batalhão Sul",     "simbolo": "👿"},
            {"tipo": "mover",   "zona": None,            "qtd": 1, "nivel": 1,
             "titulo": "Avanço",           "simbolo": "🏃"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",       "zona": "muralha_norte", "qtd": 2, "nivel": 2,
             "titulo": "Horda Norte",      "simbolo": "👿👿"},
            {"tipo": "invasor",       "zona": "muralha_oeste", "qtd": 2, "nivel": 2,
             "titulo": "Horda Oeste",      "simbolo": "👿👿"},
            {"tipo": "torre_assalto", "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Torre de Assalto", "simbolo": "🗼"},
            {"tipo": "mover",         "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Marcha",           "simbolo": "🏃🏃"},
            {"tipo": "invasor",       "zona": "muralha_leste", "qtd": 2, "nivel": 2,
             "titulo": "Horda Leste",      "simbolo": "👿👿"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",       "zona": "muralha_norte", "qtd": 3, "nivel": 3,
             "titulo": "Invasão Massiva",  "simbolo": "👿👿👿"},
            {"tipo": "catapulta",     "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Catapulta",        "simbolo": "💥"},
            {"tipo": "mover",         "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Marcha Forçada",   "simbolo": "⚡🏃"},
            {"tipo": "invasor",       "zona": "muralha_sul",   "qtd": 3, "nivel": 3,
             "titulo": "Cerco Sul",        "simbolo": "👿👿👿"},
            {"tipo": "torre_assalto", "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Nova Torre",       "simbolo": "🗼"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",   "zona": "muralha_leste", "qtd": 3, "nivel": 4,
             "titulo": "Assalto Leste",    "simbolo": "👿👿👿"},
            {"tipo": "catapulta", "zona": None,            "qtd": 1, "nivel": 4,
             "titulo": "Artilharia",       "simbolo": "💥💥"},
            {"tipo": "mover",     "zona": None,            "qtd": 1, "nivel": 4,
             "titulo": "Marcha Sombria",   "simbolo": "⚡⚡🏃"},
            {"tipo": "invasor",   "zona": "muralha_norte", "qtd": 3, "nivel": 4,
             "titulo": "Avalanche Norte",  "simbolo": "👿👿👿"},
            {"tipo": "invasor",   "zona": "muralha_oeste", "qtd": 3, "nivel": 4,
             "titulo": "Avalanche Oeste",  "simbolo": "👿👿👿"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",   "zona": "muralha_norte", "qtd": 4, "nivel": 5,
             "titulo": "Apocalipse Norte", "simbolo": "🔥👿"},
            {"tipo": "catapulta", "zona": None,            "qtd": 1, "nivel": 5,
             "titulo": "Artilharia Total", "simbolo": "🔥💥"},
            {"tipo": "mover",     "zona": None,            "qtd": 1, "nivel": 5,
             "titulo": "Corrida Final",    "simbolo": "🔥🏃"},
            {"tipo": "invasor",   "zona": "muralha_leste", "qtd": 4, "nivel": 5,
             "titulo": "Apocalipse Leste", "simbolo": "🔥👿"},
        ]
    random.shuffle(pool)
    return pool


# ═══════════════════════════════════════════════════════════════════════════
# MOTOR DE EVENTOS DE CERCO (Fase de Ameaça)
# ═══════════════════════════════════════════════════════════════════════════
def processar_carta(estado, carta):
    delta, logs = {}, []
    tipo = carta["tipo"]

    if tipo == "invasor":
        zona, qtd = carta["zona"], carta["qtd"]
        if estado["reserva"] <= 0:
            delta["derrota"]     = True
            delta["msg_derrota"] = "Reserva esgotada — DERROTA"
            logs.append(("DERROTA", delta["msg_derrota"]))
        else:
            qreal = min(qtd, estado["reserva"])
            novos = dict(estado["invasores"])
            novos[zona] = novos.get(zona, 0) + qreal
            delta["invasores"] = novos
            delta["reserva"]   = estado["reserva"] - qreal
            logs.append(("AMEACA", f"+{qreal}x Invasor em {NOMES_ZONA.get(zona, zona)}"))

    elif tipo == "mover":
        novos         = dict(estado["invasores"])
        teso_delta    = 0
        volta_reserva = 0
        # câmara central: rouba tesouro
        nc = novos.get("camara_central", 0)
        if nc > 0:
            teso_delta  -= nc
            volta_reserva += nc
            novos["camara_central"] = 0
            logs.append(("AMEACA", f"{nc}x Invasor rouba {nc}🪙 e volta à reserva"))
        # oficinas → câmara
        for of in ("carpintaria", "curtume", "fundicao", "patio"):
            n = novos.get(of, 0)
            if n > 0:
                novos["camara_central"] = novos.get("camara_central", 0) + n
                logs.append(("AMEACA", f"{n}x {NOMES_ZONA[of]} → Câmara Central"))
                novos[of] = 0
        # muralhas → oficina
        for mur, of in (("muralha_norte", "carpintaria"), ("muralha_sul", "curtume"),
                        ("muralha_oeste", "fundicao"),    ("muralha_leste", "patio")):
            n = novos.get(mur, 0)
            if n > 0:
                novos[of] = novos.get(of, 0) + n
                logs.append(("AMEACA", f"{n}x {NOMES_ZONA[mur]} → {NOMES_ZONA[of]}"))
                novos[mur] = 0
        nt = max(0, estado["tesouro"] + teso_delta)
        delta["invasores"] = novos
        delta["tesouro"]   = nt
        delta["reserva"]   = min(10, estado["reserva"] + volta_reserva)
        if nt == 0:
            delta["derrota"]     = True
            delta["msg_derrota"] = "Tesouro saqueado — DERROTA"
            logs.append(("DERROTA", delta["msg_derrota"]))

    elif tipo == "torre_assalto":
        t = estado["torre_assalto"]
        if t["estado"] == "reserva":
            st = "inativa" if estado["is_solo"] else "preparando"
            delta["torre_assalto"] = {"estado": st, "ciclo": 1}
            logs.append(("CERCO", f"Torre de Assalto → {st.upper()}"))
        else:
            r = _ativar_torre(estado)
            delta.update(r["delta"]); logs += r["logs"]

    elif tipo == "catapulta":
        c = estado["catapulta"]
        if c["estado"] == "reserva":
            st = "inativa" if estado["is_solo"] else "preparando"
            delta["catapulta"] = {"estado": st, "ciclo": 1}
            logs.append(("CERCO", f"Catapulta → {st.upper()}"))
        else:
            r = _ativar_catapulta(estado)
            delta.update(r["delta"]); logs += r["logs"]

    return delta, logs


def _ativar_torre(estado):
    delta = {"brutamontes": estado["brutamontes"] + 1,
             "torre_assalto": {"estado": "reserva", "ciclo": 0}}
    logs  = [("CERCO", f"TORRE ATIVA! +1 Brutamonte no Pátio ({delta['brutamontes']}/3)")]
    if delta["brutamontes"] >= 3:
        delta["derrota"]     = True
        delta["msg_derrota"] = "3 Brutamontes — túnel invadido! DERROTA"
        logs.append(("DERROTA", delta["msg_derrota"]))
    return {"delta": delta, "logs": logs}


def _ativar_catapulta(estado):
    slot_idx    = random.randint(0, 4)
    novos_slots = [dict(s) for s in estado["slots_upgrade"]]
    logs = []
    if not novos_slots[slot_idx]["bloqueado"] and not novos_slots[slot_idx]["adquirido"]:
        novos_slots[slot_idx]["bloqueado"] = True
        logs.append(("CERCO", f"CATAPULTA! Slot [{novos_slots[slot_idx]['nome']}] destruído!"))
    nt = max(0, estado["tesouro"] - 1)
    delta = {"tesouro": nt, "catapulta": {"estado": "reserva", "ciclo": 0},
             "slots_upgrade": novos_slots}
    logs.append(("CERCO", f"Catapulta remove 1🪙 (Tesouro: {nt})"))
    if nt == 0:
        delta["derrota"]     = True
        delta["msg_derrota"] = "Tesouro zerado pela Catapulta — DERROTA"
        logs.append(("DERROTA", delta["msg_derrota"]))
    return {"delta": delta, "logs": logs}


def avancar_ciclo_armas(estado):
    delta, logs = {}, []
    t = estado["torre_assalto"]
    if t["estado"] == "inativa":
        delta["torre_assalto"] = {"estado": "preparando", "ciclo": 2}
        logs.append(("CERCO", "Torre: INATIVA → PREPARANDO (ativa no próximo turno!)"))
    elif t["estado"] == "preparando":
        r = _ativar_torre(estado)
        delta.update(r["delta"]); logs += r["logs"]
    c = estado["catapulta"]
    if c["estado"] == "inativa":
        delta["catapulta"] = {"estado": "preparando", "ciclo": 2}
        logs.append(("CERCO", "Catapulta: INATIVA → PREPARANDO (ativa no próximo turno!)"))
    elif c["estado"] == "preparando":
        r = _ativar_catapulta(estado)
        delta.update(r["delta"]); logs += r["logs"]
    return delta, logs


# ═══════════════════════════════════════════════════════════════════════════
# APLICAR DELTA (imutável)
# ═══════════════════════════════════════════════════════════════════════════
def aplicar_delta(estado, delta):
    novo = dict(estado)
    for k, v in delta.items():
        if k == "invasores" and isinstance(v, dict):
            novo["invasores"] = dict(estado["invasores"])
            novo["invasores"].update(v)
        else:
            novo[k] = v
    return novo
