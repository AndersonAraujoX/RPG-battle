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
    # Interior
    "camara_central": "Ouro",
    "curtume":        "Couro",
    "fundicao":       "Ferro",
    "patio":          "Nexos",
    "carpintaria":    "Madeira",
    # Muralhas do perímetro
    "muralha_norte":  "Muralha Norte",
    "muralha_sul":    "Muralha Sul",
    "muralha_oeste":  "Muralha Oeste",
    "muralha_leste":  "Muralha Leste",
    # Torres dos cantos
    "torre_nw":       "Torre NO",
    "torre_ne":       "Torre NE",
    "torre_sw":       "Torre SO",
    "torre_se":       "Torre SE",
    # Zonas externas (campo de batalha — spawn dos inimigos)
    "campo_norte":    "Campo Norte",
    "campo_sul":      "Campo Sul",
    "campo_oeste":    "Campo Oeste",
    "campo_leste":    "Campo Leste",
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
    {"id": "trabalho_1",  "nome": "Trabalho",     "simbolo": "T", "tipo": "basica",
     "movimento": 0, "trabalho": 3, "escavacao": 0,
     "descricao": "+3 Trabalho"},
    {"id": "trabalho_2",  "nome": "Trabalho",     "simbolo": "T", "tipo": "basica",
     "movimento": 0, "trabalho": 3, "escavacao": 0,
     "descricao": "+3 Trabalho"},
    {"id": "marcha_4",    "nome": "Marcha",        "simbolo": "M", "tipo": "basica",
     "movimento": 15, "trabalho": 0, "escavacao": 0,
     "descricao": "+15 Movimento"},
    {"id": "marcha_1",    "nome": "Marcha",        "simbolo": "M", "tipo": "basica",
     "movimento": 15, "trabalho": 0, "escavacao": 0,
     "descricao": "+15 Movimento"},
    {"id": "marcha_2",    "nome": "Marcha",        "simbolo": "M", "tipo": "basica",
     "movimento": 15, "trabalho": 0, "escavacao": 0,
     "descricao": "+15 Movimento"},
    {"id": "marcha_3",    "nome": "Marcha",        "simbolo": "M", "tipo": "basica",
     "movimento": 15, "trabalho": 0, "escavacao": 0,
     "descricao": "+15 Movimento"},
    {"id": "escavacao_1", "nome": "Escavacao",     "simbolo": "E", "tipo": "basica",
     "movimento": 0, "trabalho": 0, "escavacao": 4,
     "descricao": "+4 Escavacao"},
    {"id": "marcha_5",    "nome": "Marcha",        "simbolo": "M", "tipo": "basica",
     "movimento": 15, "trabalho": 0, "escavacao": 0,
     "descricao": "+15 Movimento"},
    {"id": "forca_1",     "nome": "Forca Ana",     "simbolo": "F", "tipo": "basica",
     "movimento": 15, "trabalho": 4, "escavacao": 0,
     "descricao": "+15 Mov  +4 Trab"},
    {"id": "forca_2",     "nome": "Forca Ana",     "simbolo": "F", "tipo": "basica",
     "movimento": 15, "trabalho": 4, "escavacao": 0,
     "descricao": "+15 Mov  +4 Trab"},
    {"id": "invocador_1", "nome": "Invocador Orc", "simbolo": "I", "tipo": "basica",
     "movimento": 15, "trabalho": 3, "escavacao": 0, "efeito_extra": "invocar_inimigo",
     "descricao": "+15 Mov +3 Trab (Invoca)"},
    {"id": "invocador_2", "nome": "Portal Inseto", "simbolo": "I", "tipo": "basica",
     "movimento": 0, "trabalho": 3, "escavacao": 3, "efeito_extra": "invocar_inimigo",
     "descricao": "+3 Trab +3 Esc (Invoca)"},
]

CARTAS_UPGRADE_AMARELO = [
    {"id": "mestre_1",    "nome": "Mestre Artesao", "simbolo": "X", "tipo": "upgrade",
     "movimento": 0, "trabalho": 5, "escavacao": 0, "efeito_extra": "draw_1",
     "descricao": "+5 Trab, compra 1 carta",
     "custo": {"madeira": 2}},
    {"id": "corrida_1",   "nome": "Corrida Livre",  "simbolo": "R", "tipo": "upgrade",
     "movimento": 30, "trabalho": 0, "escavacao": 0, "efeito_extra": None,
     "descricao": "+30 Movimento",
     "custo": {"couro": 2}},
    {"id": "perfurador",  "nome": "Perfurador",     "simbolo": "P", "tipo": "upgrade",
     "movimento": 0, "trabalho": 0, "escavacao": 5, "efeito_extra": None,
     "descricao": "+5 Escavacao",
     "custo": {"metal": 2}},
    {"id": "trabalhador_ef", "nome": "Trab. Eficiente", "simbolo": "T", "tipo": "upgrade",
     "movimento": 15, "trabalho": 4, "escavacao": 0, "efeito_extra": None,
     "descricao": "+4 Trab +15 Mov",
     "custo": {"madeira": 1, "couro": 1}},
]

CARTAS_UPGRADE_CINZA = [
    {"id": "forjador",    "nome": "Grande Forjador", "simbolo": "G", "tipo": "upgrade",
     "movimento": 15, "trabalho": 6, "escavacao": 0, "efeito_extra": None,
     "descricao": "+15 Mov  +6 Trab",
     "custo": {"madeira": 2, "metal": 1}},
    {"id": "explorador",  "nome": "Explorador",      "simbolo": "O", "tipo": "upgrade",
     "movimento": 25, "trabalho": 3, "escavacao": 4, "efeito_extra": None,
     "descricao": "+25 Mov +3 Trab +4 Esc",
     "custo": {"couro": 1, "madeira": 1}},
    {"id": "guarda_mur",  "nome": "Guarda Muralha",  "simbolo": "W", "tipo": "upgrade",
     "movimento": 20, "trabalho": 4, "escavacao": 0, "efeito_extra": None,
     "descricao": "+20 Mov +4 Trab",
     "custo": {"metal": 2, "couro": 1}},
    {"id": "lider_eq",    "nome": "Lider de Equipe", "simbolo": "L", "tipo": "upgrade",
     "movimento": 0, "trabalho": 5, "escavacao": 3, "efeito_extra": None,
     "descricao": "+5 Trab +3 Esc",
     "custo": {"madeira": 2, "couro": 1}},
]

CARTAS_UPGRADE_VERMELHO = [
    {"id": "super_camp",  "nome": "Super Campeao",  "simbolo": "C", "tipo": "upgrade",
     "movimento": 35, "trabalho": 6, "escavacao": 0, "efeito_extra": None,
     "descricao": "+35 Mov +6 Trab",
     "custo": {"metal": 3, "madeira": 1}},
    {"id": "escavador_r", "nome": "Escavador Real",  "simbolo": "E", "tipo": "upgrade",
     "movimento": 15, "trabalho": 0, "escavacao": 8, "efeito_extra": None,
     "descricao": "+15 Mov +8 Esc",
     "custo": {"metal": 2, "madeira": 2, "couro": 1}},
    {"id": "mestre_const","nome": "Mestre Construtor", "simbolo": "B", "tipo": "upgrade",
     "movimento": 25, "trabalho": 8, "escavacao": 0, "efeito_extra": None,
     "descricao": "+8 Trab +25 Mov",
     "custo": {"madeira": 3, "couro": 2}},
]

CARTAS_UPGRADE = CARTAS_UPGRADE_AMARELO + CARTAS_UPGRADE_CINZA + CARTAS_UPGRADE_VERMELHO


def criar_mercado():
    """Retorna os slots de upgrade do mercado."""
    slots_base = [
        {"id": 0, "nome": "Mestre Artesao",  "simbolo": "X", "custo": {"madeira": 2},
         "carta_id": "mestre_1",   "bloqueado": False, "adquirido": False,
         "descricao": "+5 Trab, compra 1 carta", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}},
        {"id": 1, "nome": "Corrida Livre",   "simbolo": "R", "custo": {"couro": 2},
         "carta_id": "corrida_1",  "bloqueado": False, "adquirido": False,
         "descricao": "+30 Movimento", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}},
        {"id": 2, "nome": "Perfurador",      "simbolo": "P", "custo": {"metal": 2},
         "carta_id": "perfurador", "bloqueado": False, "adquirido": False,
         "descricao": "+5 Escavacao", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}},
        {"id": 3, "nome": "Grande Forjador", "simbolo": "G", "custo": {"madeira": 2, "metal": 1},
         "carta_id": "forjador",   "bloqueado": False, "adquirido": False,
         "descricao": "+15 Mov  +6 Trab", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}},
        {"id": 4, "nome": "Explorador",      "simbolo": "O", "custo": {"couro": 1, "madeira": 1},
         "carta_id": "explorador", "bloqueado": False, "adquirido": False,
         "descricao": "+25 Mov +3 Trab +4 Esc", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0}},
    ]
    return slots_base


DADOS_INIMIGOS = {
    "vespa_cacadora": {
        "nome": "Vespa-Caçadora", "emoji": "🐝", "antigo": "Amazon", "classe": "Goblin",
        "efeito": "Todos os jogadores devem lhe dar uma carta da mão que você pediu. Se eles não tiverem, você perdeu sua chance."
    },
    "louva_deus": {
        "nome": "Louva-a-Deus Mimético", "emoji": "🦗", "antigo": "Boogeyman", "classe": "Kobold",
        "efeito": "Troque de mãos com outro jogador."
    },
    "viuva_canibal": {
        "nome": "Viúva-Canibal", "emoji": "🕷️", "antigo": "The Bride", "classe": "Esqueleto",
        "efeito": "Pegue qualquer inseto macho já jogado e ative o efeito daquela carta imediatamente."
    },
    "escaravelho_necrofago": {
        "nome": "Escaravelho Necrófago", "emoji": "🪲", "antigo": "Centaur", "classe": "Goblin",
        "efeito": "Pegue a carta do topo da pilha de descarte e jogue-a imediatamente."
    },
    "besouro_unicornio": {
        "nome": "Besouro-Unicórnio Negro", "emoji": "🪳", "antigo": "Dark Unicorn", "classe": "Kobold",
        "efeito": "Uma onda de feromônios atordoa a todos. Faça todos os jogadores descartarem uma carta de sua mão, escolhida por você aleatoriamente."
    },
    "gafanhoto_praga": {
        "nome": "Gafanhoto-da-Praga", "emoji": "🦟", "antigo": "Demon", "classe": "Esqueleto",
        "efeito": "Envie qualquer combo ou conjunto de cartas do tabuleiro para a pilha de descarte."
    },
    "carrapato_vampiro": {
        "nome": "Carrapato-Vampiro", "emoji": "🩸", "antigo": "Dracula", "classe": "Goblin",
        "efeito": "Roube duas cartas diretamente da mão de um jogador."
    },
    "libelula_blindada": {
        "nome": "Libélula-Blindada", "emoji": "🛡️", "antigo": "Dragon", "classe": "DragaoAnciao",
        "efeito": "Protege o conjunto de cartas de que faz parte, tornando-o imune a poderes especiais. Depois de jogada, nenhuma carta nova pode ser adicionada a esse conjunto."
    },
    "besouro_gorgulho": {
        "nome": "Besouro-Gorgulho", "emoji": "🐜", "antigo": "Dwarf", "classe": "Kobold",
        "efeito": "Cave na pilha de descarte e no deck. Pegue a carta do topo da pilha de descarte e a do topo do baralho; escolha uma para guardar e descarte a outra."
    },
    "cigarra_ressonante": {
        "nome": "Cigarra-Ressonante", "emoji": "🪰", "antigo": "Elf", "classe": "Esqueleto",
        "efeito": "Reative o poder de qualquer criatura inseto sob o seu controle neste turno."
    },
    "enxame_rainha": {
        "nome": "Enxame da Rainha", "emoji": "🐝", "antigo": "The Eternals", "classe": "ReiGoblin",
        "efeito": "Complete sua mão até ter exatamente 7 cartas, puxando-as da pilha de compra ou roubando-as diretamente da mão de alguém."
    },
    "vagalume_sombras": {
        "nome": "Vagalumes das Sombras", "emoji": "🦋", "antigo": "Faeries", "classe": "Goblin",
        "efeito": "Pegue quaisquer duas cartas da pilha de descarte para a sua mão e jogue uma delas imediatamente."
    },
    "larva_carniceira": {
        "nome": "Larvas Carniceiras", "emoji": "🪱", "antigo": "Ghouls", "classe": "Kobold",
        "efeito": "Você pode optar por comprar cartas do baralho ou roubá-las da mão de um jogador."
    },
    "tarantula_golias": {
        "nome": "Tarântula-Golias", "emoji": "🕷️", "antigo": "Giant", "classe": "Esqueleto",
        "efeito": "Resgate qualquer carta da pilha de descarte e jogue-as imediatamente."
    },
    "formiga_correicao": {
        "nome": "Formigas-Correição", "emoji": "🐜", "antigo": "Goblins", "classe": "Goblin",
        "efeito": "Uma investida militar que limpa recursos. Roube 3 cartas divididas entre um ou mais jogadores."
    },
    "aranha_clepto": {
        "nome": "Aranha-Cleptoparasita", "emoji": "🕷️", "antigo": "Highwayman", "classe": "Kobold",
        "efeito": "Roube o território alheio. Troque seus combos com os de outro jogador."
    },
    "centopeia_olhos": {
        "nome": "Centopeia dos Cem Olhos", "emoji": "🐛", "antigo": "Hydra", "classe": "Esqueleto",
        "efeito": "Olhe fixamente e revele a mão inteira de um jogador à sua escolha."
    },
    "abelha_tecela": {
        "nome": "Abelha-Tecelã", "emoji": "🐝", "antigo": "The Laraki", "classe": "Goblin",
        "efeito": "Pegue um número de cartas da pilha igual ao número de jogadores. Escolha 1 para a sua mão e distribua 1 carta virada para cima para cada um dos outros jogadores."
    },
    "mariposa_esfinge": {
        "nome": "Mariposa-Esfinge", "emoji": "🦋", "antigo": "Mage", "classe": "Kobold",
        "efeito": "Compre duas cartas diretamente do baralho."
    },
    "efemera_mimetica": {
        "nome": "Efêmera Mimética", "emoji": "🦟", "antigo": "Nymph", "classe": "Esqueleto",
        "efeito": "Pegue qualquer carta de inseto sobrenatural que já tenha sido jogada na mesa e ative o efeito dela de novo."
    },
    "vespa_joia": {
        "nome": "Vespa-Joia Rainha", "emoji": "🐝", "antigo": "Shadow Queen", "classe": "Goblin",
        "efeito": "Olhe secretamente a mão de cada jogador da mesa e roube uma carta sem olhar da mão de um deles."
    },
    "viuva_negra": {
        "nome": "Viúva-Negra Tecelã", "emoji": "🕷️", "antigo": "Sorceress", "classe": "Esqueleto",
        "efeito": "Sacrifique um conjunto de corujas ou corvos para reivindicar e escolher qualquer combo do jogo como seu."
    },
    "besouro_rinoceronte": {
        "nome": "Besouro-Rinoceronte", "emoji": "🪲", "antigo": "Troll", "classe": "Troll",
        "efeito": "Força o jogador alvo a descartar uma carta de sua mão, escolhida aleatoriamente por você."
    },
    "mosca_tse_tse": {
        "nome": "Mosca-Tsé-Tsé", "emoji": "🪰", "antigo": "Werewolf", "classe": "Esqueleto",
        "efeito": "Pica um oponente injetando uma toxina sonífera. Escolha um jogador para perder completamente a sua vez."
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ESTADO INICIAL DO JOGO
# ═══════════════════════════════════════════════════════════════════════════
def criar_estado(pedregulhos=8, is_solo=True):
    deck_heroi = copy.deepcopy(CARTAS_BASICAS)
    random.shuffle(deck_heroi)

    deck_ini = list(DADOS_INIMIGOS.keys()) * 2
    random.shuffle(deck_ini)

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
        # Tokens por zona — inclui campos externos
        "invasores":       {k: 0 for k in NOMES_ZONA},
        # Inimigos nos campos externos (após avançar da reserva)
        "campo_norte":     0,
        "campo_sul":       0,
        "campo_oeste":     0,
        "campo_leste":     0,
        "brutamontes":     0,
        "infiltradores":   0,
        # Armas de cerco
        "catapulta":      {"estado": "reserva", "ciclo": 0},
        "deck_catapulta":  [1, 2, 3, 4],
        "torre_assalto":  {"estado": "reserva", "ciclo": 0},
        "deck_inimigos":   deck_ini,
        "descarte_inimigos": [],
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
        "excluidas_ciclo":    [],
        "cartas_upgrade_ativas": [],  # Upgrades acumulados (nunca descartados)
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
             "titulo": "Batalhao Norte",   "simbolo": "I"},
            {"tipo": "invasor", "zona": "muralha_sul",   "qtd": 1, "nivel": 1,
             "titulo": "Batalhao Sul",     "simbolo": "I"},
            {"tipo": "mover",   "zona": None,            "qtd": 1, "nivel": 1,
             "titulo": "Avanco",           "simbolo": "A"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",       "zona": "muralha_norte", "qtd": 2, "nivel": 2,
             "titulo": "Horda Norte",      "simbolo": "II"},
            {"tipo": "invasor",       "zona": "muralha_oeste", "qtd": 2, "nivel": 2,
             "titulo": "Horda Oeste",      "simbolo": "II"},
            {"tipo": "torre_assalto", "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Torre de Assalto", "simbolo": "T"},
            {"tipo": "mover",         "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Marcha",           "simbolo": "AA"},
            {"tipo": "invasor",       "zona": "muralha_leste", "qtd": 2, "nivel": 2,
             "titulo": "Horda Leste",      "simbolo": "II"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",       "zona": "muralha_norte", "qtd": 3, "nivel": 3,
             "titulo": "Invasao Massiva",  "simbolo": "III"},
            {"tipo": "catapulta",     "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Catapulta",        "simbolo": "C"},
            {"tipo": "mover",         "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Marcha Forcada",   "simbolo": "SA"},
            {"tipo": "invasor",       "zona": "muralha_sul",   "qtd": 3, "nivel": 3,
             "titulo": "Cerco Sul",        "simbolo": "III"},
            {"tipo": "torre_assalto", "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Nova Torre",       "simbolo": "T"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",   "zona": "muralha_leste", "qtd": 3, "nivel": 4,
             "titulo": "Assalto Leste",    "simbolo": "III"},
            {"tipo": "catapulta", "zona": None,            "qtd": 1, "nivel": 4,
             "titulo": "Artilharia",       "simbolo": "CC"},
            {"tipo": "mover",     "zona": None,            "qtd": 1, "nivel": 4,
             "titulo": "Marcha Sombria",   "simbolo": "SSA"},
            {"tipo": "invasor",   "zona": "muralha_norte", "qtd": 3, "nivel": 4,
             "titulo": "Avalanche Norte",  "simbolo": "III"},
            {"tipo": "invasor",   "zona": "muralha_oeste", "qtd": 3, "nivel": 4,
             "titulo": "Avalanche Oeste",  "simbolo": "III"},
        ]
    for _ in range(2):
        pool += [
            {"tipo": "invasor",   "zona": "muralha_norte", "qtd": 4, "nivel": 5,
             "titulo": "Apocalipse Norte", "simbolo": "SI"},
            {"tipo": "catapulta", "zona": None,            "qtd": 1, "nivel": 5,
             "titulo": "Artilharia Total", "simbolo": "SCC"},
            {"tipo": "mover",     "zona": None,            "qtd": 1, "nivel": 5,
             "titulo": "Corrida Final",    "simbolo": "SA"},
            {"tipo": "invasor",   "zona": "muralha_leste", "qtd": 4, "nivel": 5,
             "titulo": "Apocalipse Leste", "simbolo": "SI"},
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
        # Inimigos aparecem primeiro no campo externo correspondente
        mapa_spawn = {
            "muralha_norte": "campo_norte",
            "muralha_sul":   "campo_sul",
            "muralha_oeste": "campo_oeste",
            "muralha_leste": "campo_leste",
        }
        zona_spawn = mapa_spawn.get(zona, zona)
        if estado["reserva"] <= 0:
            delta["derrota"]     = True
            delta["msg_derrota"] = "Reserva esgotada — DERROTA"
            logs.append(("DERROTA", delta["msg_derrota"]))
        else:
            qreal = min(qtd, estado["reserva"])
            novos = dict(estado["invasores"])
            novos[zona_spawn] = novos.get(zona_spawn, 0) + qreal
            delta["invasores"] = novos
            delta["reserva"]   = estado["reserva"] - qreal
            logs.append(("AMEACA", f"+{qreal}x Invasor em {NOMES_ZONA.get(zona_spawn, zona_spawn)}"))

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
        # novos movimentos: campos externos → muralhas (Escalada: apenas metade sobe)
        for campo, mur in (("campo_norte", "muralha_norte"), ("campo_sul", "muralha_sul"),
                           ("campo_oeste", "muralha_oeste"), ("campo_leste", "muralha_leste")):
            n = novos.get(campo, 0)
            if n > 0:
                subindo = (n + 1) // 2
                ficando = n - subindo
                novos[mur] = novos.get(mur, 0) + subindo
                novos[campo] = ficando
                logs.append(("AMEACA", f"{subindo}x invasor escala: {NOMES_ZONA.get(campo, campo)} → {NOMES_ZONA[mur]} ({ficando}x ficaram para trás)"))
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
    # Consome munição do deck de Catapulta
    deck_catapulta = list(estado.get("deck_catapulta", [1, 2, 3, 4]))
    if deck_catapulta:
        deck_catapulta.pop()
    
    delta = {"tesouro": nt, "catapulta": {"estado": "reserva", "ciclo": 0},
             "slots_upgrade": novos_slots, "deck_catapulta": deck_catapulta}
    logs.append(("CERCO", f"Catapulta remove 1🪙 (Tesouro: {nt}) [Catapulta Restantes: {len(deck_catapulta)}]"))
    
    if len(deck_catapulta) <= 0:
        delta["derrota"] = True
        delta["msg_derrota"] = "O deck de munição de Catapulta esgotou! DERROTA!"
        logs.append(("DERROTA", delta["msg_derrota"]))
    elif nt == 0:
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
