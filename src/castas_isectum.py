"""
castas_isectum.py — Motor de Regras Puro: Modo Castas dos Isectum

Sistema de jogo de cartas assimétrico integrado ao Cerco:
  - Baralho híbrido (60% ameaças tradicionais / 40% sobrenaturais)
  - 24 insetos do Diretor com efeitos únicos
  - Cartas de Defesa e Runa para os Defensores
  - Sistema de captura: inseto derrotado entra no deck do Defensor
  - Modo Versus: Defensores vs. Diretor Isectum (IA ou 2º jogador)
"""
import random
import copy
from .cerco_isectum import DADOS_INIMIGOS, CARTAS_BASICAS, NOMES_ZONA

# ═══════════════════════════════════════════════════════════════════════════
# CARTAS DE DEFESA (compráveis no mercado)
# ═══════════════════════════════════════════════════════════════════════════
CARTAS_DEFESA = [
    {
        "id": "escudo_quitina", "nome": "Escudo de Quitina", "simbolo": "🛡",
        "tipo": "defesa", "subtipo": "reacao",
        "custo": {"metal": 2},
        "descricao": "Anula o próximo efeito de roubo/troca de inseto. O Diretor perde 1 ação.",
        "efeito": "anular_roubo",
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
    {
        "id": "teia_endurecida", "nome": "Teia Endurecida", "simbolo": "🕸",
        "tipo": "defesa", "subtipo": "continua",
        "custo": {"couro": 2},
        "descricao": "Bloqueia avanço de insetos por 1 turno em uma zona muralha.",
        "efeito": "bloquear_zona",
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
    {
        "id": "antidoto_alquimico", "nome": "Antídoto Alquímico", "simbolo": "⚗",
        "tipo": "defesa", "subtipo": "reacao",
        "custo": {"metal": 1, "couro": 2},
        "descricao": "Cancela efeito de Atordoamento (Mosca-Tsé-Tsé). Use imediatamente ao ser picado.",
        "efeito": "cancelar_atordoamento",
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
    {
        "id": "amuleto_resistencia", "nome": "Amuleto de Resistência", "simbolo": "💎",
        "tipo": "defesa", "subtipo": "passiva",
        "custo": {"metal": 2, "madeira": 1},
        "descricao": "Passiva: A primeira carta roubada desta rodada é devolvida à sua mão.",
        "efeito": "resistir_roubo_1",
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# CARTAS DE RUNA (ações extras e bônus táticos)
# ═══════════════════════════════════════════════════════════════════════════
CARTAS_RUNA = [
    {
        "id": "runa_haste", "nome": "Runa da Haste", "simbolo": "⚡",
        "tipo": "runa", "subtipo": "acao_extra",
        "custo": {"madeira": 1, "couro": 1},
        "descricao": "+2 ações extras ao Defensor ativo neste turno.",
        "efeito": "acoes_extras",
        "valor": 2,
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
    {
        "id": "runa_visao", "nome": "Runa da Visão", "simbolo": "👁",
        "tipo": "runa", "subtipo": "espionagem",
        "custo": {"couro": 1, "metal": 1},
        "descricao": "Revela as 3 cartas do topo do deck do Diretor Isectum.",
        "efeito": "revelar_deck_diretor",
        "valor": 3,
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
    {
        "id": "runa_fortaleza", "nome": "Runa da Fortaleza", "simbolo": "🏰",
        "tipo": "runa", "subtipo": "defesa_zona",
        "custo": {"madeira": 2, "metal": 1},
        "descricao": "+8 Trabalho e imunidade a destruição de recursos neste turno.",
        "efeito": "fortaleza_turno",
        "movimento": 0, "trabalho": 8, "escavacao": 0,
    },
    {
        "id": "runa_recuperacao", "nome": "Runa de Recuperação", "simbolo": "✨",
        "tipo": "runa", "subtipo": "recuperacao",
        "custo": {"couro": 2},
        "descricao": "Compra 2 cartas extras do deck neste turno.",
        "efeito": "comprar_extra",
        "valor": 2,
        "movimento": 0, "trabalho": 0, "escavacao": 0,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# DEFINIÇÕES DE HP E CAPTURA DOS INSETOS BOSS
# ═══════════════════════════════════════════════════════════════════════════
INSETOS_BOSS = {
    # boss com 2 HP, capturável
    "libelula_blindada":    {"hp": 2, "capturavel": True,  "efeito_invertido": "proteger_combo_defensor"},
    "enxame_rainha":        {"hp": 2, "capturavel": True,  "efeito_invertido": "completar_mao_defensor"},
    "viuva_canibal":        {"hp": 2, "capturavel": True,  "efeito_invertido": "copiar_efeito_aliado"},
    "vespa_cacadora":       {"hp": 1, "capturavel": True,  "efeito_invertido": "receber_cartas"},
    "mosca_tse_tse":        {"hp": 1, "capturavel": True,  "efeito_invertido": "dar_turno_extra"},
    "gafanhoto_praga":      {"hp": 1, "capturavel": True,  "efeito_invertido": "recuperar_combo"},
}

def get_hp_inseto(inseto_id):
    """Retorna os HP de um inseto (1 por padrão, 2 para bosses)."""
    return INSETOS_BOSS.get(inseto_id, {}).get("hp", 1)

def e_boss(inseto_id):
    return inseto_id in INSETOS_BOSS

# ═══════════════════════════════════════════════════════════════════════════
# CRIAÇÃO DO DECK HÍBRIDO DE AMEAÇAS (60% tradicional / 40% sobrenatural)
# ═══════════════════════════════════════════════════════════════════════════
def criar_deck_hibrido():
    """
    Retorna o deck de eventos do modo Castas.
    60% = ameaças táticas tradicionais (invasor, mover, catapulta, torre)
    40% = ameaças sobrenaturais dos insetos (roubo, destruicao, atordoamento, captura)
    """
    pool_tradicional = []
    for _ in range(3):
        pool_tradicional += [
            {"tipo": "invasor",      "zona": "muralha_norte", "qtd": 1, "nivel": 1,
             "titulo": "Batalhão Norte",    "simbolo": "I",   "sobrenatural": False},
            {"tipo": "invasor",      "zona": "muralha_sul",   "qtd": 1, "nivel": 1,
             "titulo": "Batalhão Sul",      "simbolo": "I",   "sobrenatural": False},
            {"tipo": "mover",        "zona": None,            "qtd": 1, "nivel": 1,
             "titulo": "Avanço",            "simbolo": "A",   "sobrenatural": False},
        ]
    for _ in range(2):
        pool_tradicional += [
            {"tipo": "invasor",      "zona": "muralha_norte", "qtd": 2, "nivel": 2,
             "titulo": "Horda Norte",       "simbolo": "II",  "sobrenatural": False},
            {"tipo": "invasor",      "zona": "muralha_oeste", "qtd": 2, "nivel": 2,
             "titulo": "Horda Oeste",       "simbolo": "II",  "sobrenatural": False},
            {"tipo": "torre_assalto","zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Torre de Assalto",  "simbolo": "T",   "sobrenatural": False},
            {"tipo": "mover",        "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Marcha",            "simbolo": "AA",  "sobrenatural": False},
        ]
    for _ in range(2):
        pool_tradicional += [
            {"tipo": "invasor",      "zona": "muralha_norte", "qtd": 3, "nivel": 3,
             "titulo": "Invasão Massiva",   "simbolo": "III", "sobrenatural": False},
            {"tipo": "catapulta",    "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Catapulta",         "simbolo": "C",   "sobrenatural": False},
            {"tipo": "mover",        "zona": None,            "qtd": 1, "nivel": 3,
             "titulo": "Marcha Forçada",    "simbolo": "SA",  "sobrenatural": False},
            {"tipo": "invasor",      "zona": "muralha_leste", "qtd": 2, "nivel": 3,
             "titulo": "Horda Leste",       "simbolo": "II",  "sobrenatural": False},
        ]

    pool_sobrenatural = []
    # Roubo — força descarte ao surgir no perímetro
    for _ in range(4):
        pool_sobrenatural.append(
            {"tipo": "roubo",        "zona": "muralha_norte", "qtd": 1, "nivel": 2,
             "titulo": "Carrapato Ladrão",  "simbolo": "🩸", "sobrenatural": True,
             "inseto_id": "carrapato_vampiro",
             "descricao": "Ao surgir: o Defensor ativo descarta 1 carta aleatória da mão."}
        )
    for _ in range(3):
        pool_sobrenatural.append(
            {"tipo": "roubo",        "zona": "muralha_sul",   "qtd": 1, "nivel": 2,
             "titulo": "Vespa Invasora",    "simbolo": "🐝", "sobrenatural": True,
             "inseto_id": "vespa_cacadora",
             "descricao": "Ao surgir: o Defensor deve entregar 1 carta específica ou o efeito é cancelado."}
        )
    # Destruição de recursos
    for _ in range(3):
        pool_sobrenatural.append(
            {"tipo": "destruicao",   "zona": "fundicao",      "qtd": 1, "nivel": 3,
             "titulo": "Gafanhoto Devorador","simbolo": "🦟", "sobrenatural": True,
             "inseto_id": "gafanhoto_praga",
             "descricao": "Limpa TODOS os recursos alocados em um slot de upgrade aleatório."}
        )
    for _ in range(2):
        pool_sobrenatural.append(
            {"tipo": "destruicao",   "zona": "carpintaria",   "qtd": 1, "nivel": 3,
             "titulo": "Enxame Corrosivo",  "simbolo": "🐜", "sobrenatural": True,
             "inseto_id": "formiga_correicao",
             "descricao": "Rouba 3 recursos distribuídos entre os slots de upgrade."}
        )
    # Atordoamento — pula turno do Defensor
    for _ in range(3):
        pool_sobrenatural.append(
            {"tipo": "atordoamento", "zona": None,            "qtd": 1, "nivel": 2,
             "titulo": "Mosca Sonífera",    "simbolo": "🪰", "sobrenatural": True,
             "inseto_id": "mosca_tse_tse",
             "descricao": "O próximo turno do Defensor ativo é completamente pulado."}
        )
    # Captura — token de inseto boss aparece, pode ser derrotado para captura
    for _ in range(2):
        pool_sobrenatural.append(
            {"tipo": "captura",      "zona": "muralha_leste", "qtd": 1, "nivel": 4,
             "titulo": "Aparição da Rainha","simbolo": "👑", "sobrenatural": True,
             "inseto_id": "enxame_rainha",
             "descricao": "Um inseto boss surge. Se derrotado, vai para o deck do Defensor."}
        )
    for _ in range(2):
        pool_sobrenatural.append(
            {"tipo": "captura",      "zona": "muralha_norte", "qtd": 1, "nivel": 4,
             "titulo": "Viúva Infiltrada",  "simbolo": "🕷", "sobrenatural": True,
             "inseto_id": "viuva_canibal",
             "descricao": "Um inseto boss surge. Se derrotado, vai para o deck do Defensor."}
        )

    # Mescla 60/40 e embaralha
    random.shuffle(pool_tradicional)
    random.shuffle(pool_sobrenatural)

    n_total = len(pool_tradicional) + len(pool_sobrenatural)
    # Aproxima 60% tradicional
    pool_final = pool_tradicional + pool_sobrenatural
    random.shuffle(pool_final)
    return pool_final


# ═══════════════════════════════════════════════════════════════════════════
# DECK DO DIRETOR (48 cartas — 2x cada inseto)
# ═══════════════════════════════════════════════════════════════════════════
def criar_deck_diretor():
    """Baralho do Diretor: 2 cópias de cada um dos 24 insetos."""
    cartas = []
    for inseto_id, dados in DADOS_INIMIGOS.items():
        for _ in range(2):
            cartas.append({
                "id": inseto_id,
                "nome": dados["nome"],
                "emoji": dados["emoji"],
                "tipo": "inseto",
                "efeito": dados["efeito"],
                "classe": dados.get("classe", "Goblin"),
                "hp": get_hp_inseto(inseto_id),
                "capturavel": INSETOS_BOSS.get(inseto_id, {}).get("capturavel", False),
            })
    random.shuffle(cartas)
    return cartas


# ═══════════════════════════════════════════════════════════════════════════
# CRIAÇÃO DE CARTA CAPTURADA (efeito invertido)
# ═══════════════════════════════════════════════════════════════════════════
def criar_carta_capturada(inseto_id):
    """
    Gera uma carta do tipo 'capturada' com efeito invertido/benéfico.
    Vai para o deck do Defensor que derrotou o boss.
    """
    dados = DADOS_INIMIGOS.get(inseto_id, {})
    boss_info = INSETOS_BOSS.get(inseto_id, {})
    efeito_invertido = boss_info.get("efeito_invertido", "bonus_generico")

    DESCRICOES_INVERTIDAS = {
        "proteger_combo_defensor":  "Protege seus combos de destruição por 1 rodada.",
        "completar_mao_defensor":   "Complete sua mão até 7 cartas do deck.",
        "copiar_efeito_aliado":     "Copie o efeito de uma carta de Defesa ou Runa usada neste turno.",
        "receber_cartas":           "Receba 1 carta de outro Defensor à sua escolha.",
        "dar_turno_extra":          "Ganhe 1 ação extra neste turno.",
        "recuperar_combo":          "Recupere um combo destruído do descarte.",
        "bonus_generico":           "+3 Trabalho e compre 1 carta extra.",
    }

    return {
        "id": f"capturado_{inseto_id}",
        "nome": f"{dados.get('nome', inseto_id)} [Capturado]",
        "emoji": dados.get("emoji", "🏆"),
        "tipo": "capturada",
        "subtipo": "dinamica",
        "efeito": efeito_invertido,
        "descricao": DESCRICOES_INVERTIDAS.get(efeito_invertido, "+3 Trabalho."),
        "movimento": 0, "trabalho": 3, "escavacao": 0,
        "simbolo": "★",
        "original_id": inseto_id,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ESTADO INICIAL DO MODO CASTAS
# ═══════════════════════════════════════════════════════════════════════════
def criar_estado_castas(herois_nomes=None, dificuldade="normal"):
    """
    Estado completo para o modo Castas dos Isectum.
    Separa o estado do Defensor e do Diretor.
    """
    if herois_nomes is None:
        herois_nomes = ["Stark"]

    # Configurações de dificuldade do Diretor
    config_dif = {
        "facil":   {"acoes_diretor": 2, "tam_mao_diretor": 2, "hp_fortaleza": 30},
        "normal":  {"acoes_diretor": 3, "tam_mao_diretor": 3, "hp_fortaleza": 20},
        "dificil": {"acoes_diretor": 4, "tam_mao_diretor": 4, "hp_fortaleza": 15},
    }.get(dificuldade, {"acoes_diretor": 3, "tam_mao_diretor": 3, "hp_fortaleza": 20})

    deck_def = copy.deepcopy(CARTAS_BASICAS)
    random.shuffle(deck_def)

    deck_dir = criar_deck_diretor()
    deck_ameaca = criar_deck_hibrido()

    return {
        # ── Meta ────────────────────────────────────────────────────────────
        "rodada": 1,
        "fase": "TURNO_DEFENSOR",      # TURNO_DEFENSOR | TURNO_DIRETOR | FASE_AMEACA | FIM
        "turno_heroi_idx": 0,          # índice do herói ativo entre os defensores
        "dificuldade": dificuldade,
        "derrota": False,
        "vitoria": False,
        "msg_fim": "",

        # ── Condições de Vitória / Derrota ────────────────────────────────
        "cartas_roubadas_total": 0,    # Isectum vence com 10+
        "camara_central_invasores": 0, # Isectum vence com 3+
        "bosses_eliminados": [],       # Defensores vencem ao eliminar todos os bosses capturáveis
        "rodadas_max": 15,             # Defensores vencem ao sobreviver 15 rodadas

        # ── Fortaleza ────────────────────────────────────────────────────
        "hp_fortaleza": config_dif["hp_fortaleza"],
        "hp_fortaleza_max": config_dif["hp_fortaleza"],
        "invasores": {k: 0 for k in NOMES_ZONA},
        "reserva": 12,
        "recursos": {"madeira": 0, "couro": 0, "metal": 0, "ouro": 0},
        "slots_upgrade": criar_mercado_castas(),
        "zonas_bloqueadas": {},        # zona_id -> rodadas restantes de bloqueio

        # ── Deck de Ameaça Híbrido ───────────────────────────────────────
        "deck_ameaca": deck_ameaca,
        "descarte_ameaca": [],
        "carta_ameaca_atual": None,
        "bosses_no_campo": {},         # inseto_id -> {"hp": N, "zona": "..."}

        # ── Defensores ───────────────────────────────────────────────────
        "herois_nomes": list(herois_nomes),
        "herois_status": {
            nome: {
                "mao": [],
                "deck": copy.deepcopy(CARTAS_BASICAS),
                "descarte": [],
                "excluidas": [],
                "pontos_movimento": 0,
                "pontos_trabalho": 0,
                "pontos_escavacao": 0,
                "acoes_extras": 0,        # concedidas por runas
                "turno_pulado": False,    # atordoamento da Mosca-Tsé-Tsé
                "protegido_roubo": False, # Escudo de Quitina ativo
                "resistir_roubo_1": False,# Amuleto de Resistência ativo
                "imune_destruicao": False,# Runa da Fortaleza ativa
            }
            for nome in herois_nomes
        },
        "herois_jogaram": [],

        # ── Diretor Isectum ──────────────────────────────────────────────
        "deck_diretor": deck_dir,
        "mao_diretor": [],             # cartas na mão do Diretor (ocultas)
        "descarte_diretor": [],
        "acoes_diretor_max": config_dif["acoes_diretor"],
        "acoes_diretor_restantes": config_dif["acoes_diretor"],
        "tam_mao_diretor": config_dif["tam_mao_diretor"],
        "acao_bloqueada": False,       # Escudo de Quitina bloqueou ação atual
        "deck_diretor_revelado": [],   # cartas visíveis pela Runa da Visão

        # ── Log ──────────────────────────────────────────────────────────
        "log": [],
    }


def criar_mercado_castas():
    """Mercado com slots para upgrades normais + defesas + runas."""
    slots = [
        # Upgrades de desempenho
        {"id": 0, "nome": "Mestre Artesão",   "simbolo": "X", "custo": {"madeira": 2},
         "carta_id": "mestre_1",    "bloqueado": False, "adquirido": False,
         "descricao": "+5 Trab, compra 1 carta", "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "upgrade"},
        {"id": 1, "nome": "Corrida Livre",    "simbolo": "R", "custo": {"couro": 2},
         "carta_id": "corrida_1",   "bloqueado": False, "adquirido": False,
         "descricao": "+30 Movimento",   "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "upgrade"},
        {"id": 2, "nome": "Perfurador",       "simbolo": "P", "custo": {"metal": 2},
         "carta_id": "perfurador",  "bloqueado": False, "adquirido": False,
         "descricao": "+5 Escavação",   "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "upgrade"},
        # Defesas
        {"id": 3, "nome": "Escudo de Quitina","simbolo": "🛡", "custo": {"metal": 2},
         "carta_id": "escudo_quitina", "bloqueado": False, "adquirido": False,
         "descricao": "Anula próximo roubo de inseto",
         "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "defesa"},
        {"id": 4, "nome": "Runa da Haste",    "simbolo": "⚡", "custo": {"madeira": 1, "couro": 1},
         "carta_id": "runa_haste",  "bloqueado": False, "adquirido": False,
         "descricao": "+2 Ações extras no turno",
         "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "runa"},
        {"id": 5, "nome": "Antídoto Alquím.", "simbolo": "⚗", "custo": {"metal": 1, "couro": 2},
         "carta_id": "antidoto_alquimico", "bloqueado": False, "adquirido": False,
         "descricao": "Cancela Atordoamento",
         "recursos_alocados": {"madeira": 0, "couro": 0, "metal": 0},
         "categoria": "defesa"},
    ]
    return slots


# ═══════════════════════════════════════════════════════════════════════════
# PROCESSADOR DE CARTAS DE AMEAÇA HÍBRIDAS
# ═══════════════════════════════════════════════════════════════════════════
def processar_carta_hibrida(estado, carta, heroi_ativo_nome=None):
    """
    Processa uma carta do deck de ameaças híbrido.
    Retorna (delta, logs) para ser aplicado com aplicar_delta_castas().
    """
    delta, logs = {}, []
    tipo = carta.get("tipo", "invasor")

    if tipo == "invasor":
        zona = carta.get("zona", "muralha_norte")
        qtd = carta.get("qtd", 1)
        novos_invasores = dict(estado["invasores"])
        qreal = min(qtd, estado["reserva"])
        novos_invasores[zona] = novos_invasores.get(zona, 0) + qreal
        delta["invasores"] = novos_invasores
        delta["reserva"] = max(0, estado["reserva"] - qreal)
        logs.append(("AMEAÇA", f"⚔️ {carta['titulo']}: {qreal} invasores em {zona}!"))

    elif tipo == "mover":
        # Move todos os invasores das muralhas para zonas internas
        novos_invasores = dict(estado["invasores"])
        FLUXO = {
            "muralha_norte": "carpintaria",
            "muralha_sul":   "curtume",
            "muralha_oeste": "fundicao",
            "muralha_leste": "patio",
            "carpintaria":   "camara_central",
            "curtume":       "camara_central",
            "fundicao":      "camara_central",
            "patio":         "camara_central",
        }
        for origem, destino in FLUXO.items():
            qtd_mover = novos_invasores.get(origem, 0)
            if qtd_mover > 0:
                novos_invasores[origem] = 0
                novos_invasores[destino] = novos_invasores.get(destino, 0) + qtd_mover
        delta["invasores"] = novos_invasores
        cam_central = novos_invasores.get("camara_central", 0)
        delta["camara_central_invasores"] = cam_central
        logs.append(("AMEAÇA", f"🏃 {carta['titulo']}: invasores avançam!"))
        if cam_central >= 3:
            delta["derrota"] = True
            delta["msg_fim"] = "Isectum invadiu a Câmara Central! DERROTA."
            logs.append(("DERROTA", delta["msg_fim"]))

    elif tipo == "catapulta":
        dano = 3
        novo_hp = max(0, estado["hp_fortaleza"] - dano)
        delta["hp_fortaleza"] = novo_hp
        logs.append(("AMEAÇA", f"💥 Catapulta! -{dano} HP da fortaleza. Restam {novo_hp}."))
        if novo_hp <= 0:
            delta["derrota"] = True
            delta["msg_fim"] = "A fortaleza foi destruída! DERROTA."

    elif tipo == "torre_assalto":
        dano = 2
        novo_hp = max(0, estado["hp_fortaleza"] - dano)
        delta["hp_fortaleza"] = novo_hp
        logs.append(("AMEAÇA", f"🗼 Torre de Assalto! -{dano} HP da fortaleza."))
        if novo_hp <= 0:
            delta["derrota"] = True
            delta["msg_fim"] = "A fortaleza foi destruída! DERROTA."

    elif tipo == "roubo":
        # Força descarte de carta aleatória do Defensor ativo
        if heroi_ativo_nome:
            hs = estado["herois_status"].get(heroi_ativo_nome, {})
            # Verifica proteções
            if hs.get("protegido_roubo"):
                logs.append(("DEFESA", f"🛡 Escudo de Quitina bloqueou o roubo de {carta['titulo']}!"))
                novos_hs = dict(estado["herois_status"])
                novos_hs[heroi_ativo_nome] = dict(hs)
                novos_hs[heroi_ativo_nome]["protegido_roubo"] = False
                delta["herois_status"] = novos_hs
                delta["acao_bloqueada"] = True
            elif hs.get("resistir_roubo_1"):
                logs.append(("DEFESA", f"💎 Amuleto devolveu a carta roubada de {carta['titulo']}!"))
                novos_hs = dict(estado["herois_status"])
                novos_hs[heroi_ativo_nome] = dict(hs)
                novos_hs[heroi_ativo_nome]["resistir_roubo_1"] = False
                delta["herois_status"] = novos_hs
            else:
                mao = list(hs.get("mao", []))
                roubada = None
                if mao:
                    roubada = mao.pop(random.randrange(len(mao)))
                    novos_hs = dict(estado["herois_status"])
                    novos_hs[heroi_ativo_nome] = dict(hs)
                    novos_hs[heroi_ativo_nome]["mao"] = mao
                    delta["herois_status"] = novos_hs
                    delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
                    nome_carta = roubada.get("nome", "?") if roubada else "?"
                    logs.append(("AMEAÇA", f"🩸 {carta['titulo']}: {heroi_ativo_nome} perdeu '{nome_carta}'!"))
                    if delta.get("cartas_roubadas_total", 0) >= 10:
                        delta["derrota"] = True
                        delta["msg_fim"] = "Isectum roubou 10+ cartas! DERROTA."
                else:
                    logs.append(("AMEAÇA", f"🩸 {carta['titulo']}: {heroi_ativo_nome} não tinha cartas!"))

    elif tipo == "destruicao":
        # Limpa recursos de um slot de upgrade aleatório
        if not estado.get("herois_status", {}).get(heroi_ativo_nome, {}).get("imune_destruicao"):
            slots = list(estado.get("slots_upgrade", []))
            alvos = [s for s in slots if any(v > 0 for v in s.get("recursos_alocados", {}).values())]
            if alvos:
                idx_alvo = random.randrange(len(alvos))
                for i, s in enumerate(slots):
                    if s is alvos[idx_alvo]:
                        slots[i] = dict(s)
                        slots[i]["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
                        logs.append(("AMEAÇA", f"🦟 {carta['titulo']}: recursos do slot '{s['nome']}' destruídos!"))
                        break
                delta["slots_upgrade"] = slots
            else:
                logs.append(("AMEAÇA", f"🦟 {carta['titulo']}: nenhum slot com recursos para destruir."))
        else:
            logs.append(("DEFESA", f"🏰 Runa da Fortaleza: imune à destruição de recursos!"))

    elif tipo == "atordoamento":
        # Pula o próximo turno do Defensor ativo
        if heroi_ativo_nome:
            hs = estado["herois_status"].get(heroi_ativo_nome, {})
            if hs.get("turno_pulado"):
                logs.append(("INFO", f"🪰 {heroi_ativo_nome} já estava atordoado!"))
            else:
                novos_hs = dict(estado["herois_status"])
                novos_hs[heroi_ativo_nome] = dict(hs)
                novos_hs[heroi_ativo_nome]["turno_pulado"] = True
                delta["herois_status"] = novos_hs
                logs.append(("AMEAÇA", f"🪰 {carta['titulo']}: {heroi_ativo_nome} perderá o próximo turno!"))

    elif tipo == "captura":
        # Surge um inseto boss no campo — deve ser derrotado para captura
        inseto_id = carta.get("inseto_id", "enxame_rainha")
        zona = carta.get("zona", "muralha_norte")
        bosses = dict(estado.get("bosses_no_campo", {}))
        if inseto_id not in bosses:
            bosses[inseto_id] = {"hp": get_hp_inseto(inseto_id), "zona": zona}
            delta["bosses_no_campo"] = bosses
            nome_boss = DADOS_INIMIGOS.get(inseto_id, {}).get("nome", inseto_id)
            emoji = DADOS_INIMIGOS.get(inseto_id, {}).get("emoji", "🐛")
            logs.append(("AMEAÇA", f"{emoji} {nome_boss} surgiu em {zona}! Derrote-o para capturar!"))
        else:
            logs.append(("INFO", f"Boss {inseto_id} já estava no campo."))

    return delta, logs


# ═══════════════════════════════════════════════════════════════════════════
# EFEITOS DOS INSETOS DO DIRETOR (ao jogar carta de inseto)
# ═══════════════════════════════════════════════════════════════════════════
def aplicar_efeito_inseto(estado, inseto_id, heroi_alvo_nome=None):
    """
    Executa o efeito de um inseto jogado pelo Diretor.
    Retorna (delta, logs, requer_escolha).
    requer_escolha=True indica que o jogador precisará tomar decisão visual.
    """
    delta, logs = {}, []
    requer_escolha = False

    dados = DADOS_INIMIGOS.get(inseto_id, {})
    nome = dados.get("nome", inseto_id)
    emoji = dados.get("emoji", "🐛")

    # Determina herói alvo (padrão: herói ativo)
    herois_nomes = estado.get("herois_nomes", [])
    if not heroi_alvo_nome and herois_nomes:
        idx = estado.get("turno_heroi_idx", 0) % len(herois_nomes)
        heroi_alvo_nome = herois_nomes[idx]

    def get_hs(nome_heroi):
        return estado["herois_status"].get(nome_heroi, {})

    def set_hs(nome_heroi, novo_hs):
        todos = dict(estado["herois_status"])
        todos[nome_heroi] = novo_hs
        delta["herois_status"] = todos

    # Checar se Escudo de Quitina bloqueia
    if heroi_alvo_nome:
        hs_alvo = get_hs(heroi_alvo_nome)
        if hs_alvo.get("protegido_roubo") and inseto_id in [
            "vespa_cacadora", "carrapato_vampiro", "formiga_correicao",
            "besouro_rinoceronte", "besouro_unicornio", "larva_carniceira",
            "aranha_clepto", "viuva_canibal", "louva_deus"
        ]:
            logs.append(("DEFESA", f"🛡 Escudo de Quitina de {heroi_alvo_nome} bloqueou {nome}! Diretor perde 1 ação."))
            novos_hs = dict(hs_alvo)
            novos_hs["protegido_roubo"] = False
            set_hs(heroi_alvo_nome, novos_hs)
            delta["acoes_diretor_restantes"] = max(0, estado.get("acoes_diretor_restantes", 0) - 1)
            return delta, logs, False

    # === EFEITOS POR INSETO ===

    if inseto_id == "vespa_cacadora":
        # Pede uma carta específica da mão do alvo
        hs = get_hs(heroi_alvo_nome)
        mao = list(hs.get("mao", []))
        if mao:
            # IA escolhe a primeira carta (no modo vs. real, requer_escolha=True)
            roubada = mao.pop(0)
            novos_hs = dict(hs)
            novos_hs["mao"] = mao
            set_hs(heroi_alvo_nome, novos_hs)
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
            logs.append(("DIRETOR", f"🐝 {nome}: pegou '{roubada.get('nome','?')}' de {heroi_alvo_nome}!"))
        else:
            logs.append(("INFO", f"🐝 {nome}: {heroi_alvo_nome} não tinha cartas!"))

    elif inseto_id == "louva_deus":
        # Troca mãos com outro herói aleatório
        if len(herois_nomes) >= 2:
            outro = random.choice([h for h in herois_nomes if h != heroi_alvo_nome])
            hs1 = dict(get_hs(heroi_alvo_nome))
            hs2 = dict(get_hs(outro))
            mao1, mao2 = list(hs1.get("mao", [])), list(hs2.get("mao", []))
            hs1["mao"] = mao2
            hs2["mao"] = mao1
            todos = dict(estado["herois_status"])
            todos[heroi_alvo_nome] = hs1
            todos[outro] = hs2
            delta["herois_status"] = todos
            logs.append(("DIRETOR", f"🦗 {nome}: {heroi_alvo_nome} trocou de mão com {outro}!"))
        else:
            logs.append(("INFO", f"🦗 {nome}: precisa de 2+ defensores para trocar mãos."))

    elif inseto_id == "viuva_canibal":
        # Copia efeito de inseto já jogado (ativa um inseto aleatório do descarte do Diretor)
        descarte = list(estado.get("descarte_diretor", []))
        insetos_desc = [c for c in descarte if c.get("tipo") == "inseto" and c["id"] != "viuva_canibal"]
        if insetos_desc:
            alvo = random.choice(insetos_desc)
            logs.append(("DIRETOR", f"🕷️ {nome}: copiando efeito de {alvo['nome']}..."))
            sub_delta, sub_logs, _ = aplicar_efeito_inseto(estado, alvo["id"], heroi_alvo_nome)
            for k, v in sub_delta.items():
                delta[k] = v
            logs.extend(sub_logs)
        else:
            logs.append(("INFO", f"🕷️ {nome}: nenhum inseto no descarte para copiar."))

    elif inseto_id == "escaravelho_necrofago":
        # Pega carta do topo do descarte do Defensor ativo e joga imediatamente
        hs = get_hs(heroi_alvo_nome)
        desc = list(hs.get("descarte", []))
        if desc:
            carta_topo = desc.pop()
            novos_hs = dict(hs)
            novos_hs["descarte"] = desc
            set_hs(heroi_alvo_nome, novos_hs)
            logs.append(("DIRETOR", f"🪲 {nome}: pegou '{carta_topo.get('nome','?')}' do descarte de {heroi_alvo_nome}!"))
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
        else:
            logs.append(("INFO", f"🪲 {nome}: descarte de {heroi_alvo_nome} vazio."))

    elif inseto_id == "besouro_unicornio":
        # Todos os defensores descartam 1 carta aleatória
        todos_hs = dict(estado["herois_status"])
        total_roubado = 0
        for nome_h in herois_nomes:
            hs = dict(todos_hs.get(nome_h, {}))
            mao = list(hs.get("mao", []))
            if mao:
                idx_r = random.randrange(len(mao))
                roubada = mao.pop(idx_r)
                hs["mao"] = mao
                todos_hs[nome_h] = hs
                total_roubado += 1
                logs.append(("DIRETOR", f"🪳 {nome}: {nome_h} descartou '{roubada.get('nome','?')}'!"))
        delta["herois_status"] = todos_hs
        if total_roubado:
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + total_roubado

    elif inseto_id == "gafanhoto_praga":
        # Limpa recursos de um slot aleatório
        slots = list(estado.get("slots_upgrade", []))
        alvos = [s for s in slots if any(v > 0 for v in s.get("recursos_alocados", {}).values())]
        if alvos:
            alvo_slot = random.choice(alvos)
            for i, s in enumerate(slots):
                if s is alvo_slot:
                    slots[i] = dict(s)
                    slots[i]["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
                    logs.append(("DIRETOR", f"🦟 {nome}: destruiu recursos do slot '{s['nome']}'!"))
                    break
            delta["slots_upgrade"] = slots
        else:
            logs.append(("INFO", f"🦟 {nome}: nenhum slot com recursos."))

    elif inseto_id == "carrapato_vampiro":
        # Rouba 2 cartas direto da mão
        hs = get_hs(heroi_alvo_nome)
        mao = list(hs.get("mao", []))
        roubadas = 0
        for _ in range(2):
            if mao:
                carta_r = mao.pop(random.randrange(len(mao)))
                roubadas += 1
                logs.append(("DIRETOR", f"🩸 {nome}: roubou '{carta_r.get('nome','?')}' de {heroi_alvo_nome}!"))
        novos_hs = dict(hs)
        novos_hs["mao"] = mao
        set_hs(heroi_alvo_nome, novos_hs)
        if roubadas:
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + roubadas

    elif inseto_id == "mosca_tse_tse":
        # Faz herói alvo pular o próximo turno
        hs = dict(get_hs(heroi_alvo_nome))
        hs["turno_pulado"] = True
        set_hs(heroi_alvo_nome, hs)
        logs.append(("DIRETOR", f"🪰 {nome}: {heroi_alvo_nome} perderá o próximo turno!"))

    elif inseto_id == "besouro_rinoceronte":
        # Herói alvo descarta 1 carta aleatória
        hs = dict(get_hs(heroi_alvo_nome))
        mao = list(hs.get("mao", []))
        if mao:
            carta_r = mao.pop(random.randrange(len(mao)))
            hs["mao"] = mao
            set_hs(heroi_alvo_nome, hs)
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
            logs.append(("DIRETOR", f"🪲 {nome}: {heroi_alvo_nome} descartou '{carta_r.get('nome','?')}'!"))

    elif inseto_id == "centopeia_olhos":
        # Revela a mão inteira do herói alvo (para o log)
        hs = get_hs(heroi_alvo_nome)
        mao = hs.get("mao", [])
        nomes_cartas = ", ".join(c.get("nome", "?") for c in mao) or "mão vazia"
        logs.append(("DIRETOR", f"🐛 {nome}: mão de {heroi_alvo_nome} revelada → {nomes_cartas}"))
        delta["mao_heroi_revelada"] = {heroi_alvo_nome: list(mao)}

    elif inseto_id == "mariposa_esfinge":
        # Diretor compra 2 cartas do seu deck
        deck_dir = list(estado.get("deck_diretor", []))
        mao_dir = list(estado.get("mao_diretor", []))
        for _ in range(2):
            if deck_dir:
                mao_dir.append(deck_dir.pop())
        delta["deck_diretor"] = deck_dir
        delta["mao_diretor"] = mao_dir
        logs.append(("DIRETOR", f"🦋 {nome}: Diretor comprou 2 cartas!"))

    elif inseto_id == "enxame_rainha":
        # Completa a mão do Diretor até tam_mao_diretor
        deck_dir = list(estado.get("deck_diretor", []))
        mao_dir = list(estado.get("mao_diretor", []))
        tam = estado.get("tam_mao_diretor", 3)
        while len(mao_dir) < tam and deck_dir:
            mao_dir.append(deck_dir.pop())
        delta["deck_diretor"] = deck_dir
        delta["mao_diretor"] = mao_dir
        logs.append(("DIRETOR", f"🐝 {nome}: Diretor completou a mão!"))

    elif inseto_id == "vagalume_sombras":
        # Pega 2 cartas do descarte do Defensor
        hs = dict(get_hs(heroi_alvo_nome))
        desc = list(hs.get("descarte", []))
        roubadas = 0
        for _ in range(min(2, len(desc))):
            carta_r = desc.pop(random.randrange(len(desc)))
            roubadas += 1
            logs.append(("DIRETOR", f"🦋 {nome}: recuperou '{carta_r.get('nome','?')}' do descarte de {heroi_alvo_nome}!"))
        hs["descarte"] = desc
        set_hs(heroi_alvo_nome, hs)
        if roubadas:
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + roubadas

    elif inseto_id == "larva_carniceira":
        # Compra do deck ou rouba da mão (IA: rouba se possível)
        hs = dict(get_hs(heroi_alvo_nome))
        mao = list(hs.get("mao", []))
        if mao:
            carta_r = mao.pop(random.randrange(len(mao)))
            hs["mao"] = mao
            set_hs(heroi_alvo_nome, hs)
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
            logs.append(("DIRETOR", f"🪱 {nome}: roubou '{carta_r.get('nome','?')}' de {heroi_alvo_nome}!"))
        else:
            deck_dir = list(estado.get("deck_diretor", []))
            mao_dir = list(estado.get("mao_diretor", []))
            if deck_dir:
                mao_dir.append(deck_dir.pop())
                delta["deck_diretor"] = deck_dir
                delta["mao_diretor"] = mao_dir
                logs.append(("DIRETOR", f"🪱 {nome}: comprou do deck (mão do herói vazia)."))

    elif inseto_id == "formiga_correicao":
        # Rouba 3 cartas divididas entre heróis
        todos_hs = dict(estado["herois_status"])
        total_roubado = 0
        for _ in range(3):
            herois_com_cartas = [h for h in herois_nomes if todos_hs.get(h, {}).get("mao")]
            if not herois_com_cartas:
                break
            alvo_h = random.choice(herois_com_cartas)
            hs = dict(todos_hs.get(alvo_h, {}))
            mao = list(hs.get("mao", []))
            if mao:
                carta_r = mao.pop(random.randrange(len(mao)))
                hs["mao"] = mao
                todos_hs[alvo_h] = hs
                total_roubado += 1
                logs.append(("DIRETOR", f"🐜 {nome}: roubou '{carta_r.get('nome','?')}' de {alvo_h}!"))
        delta["herois_status"] = todos_hs
        if total_roubado:
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + total_roubado

    elif inseto_id == "aranha_clepto":
        # Troca combos/mãos de dois heróis aleatórios
        if len(herois_nomes) >= 2:
            h1, h2 = random.sample(herois_nomes, 2)
            hs1 = dict(get_hs(h1))
            hs2 = dict(get_hs(h2))
            hs1["mao"], hs2["mao"] = list(hs2.get("mao", [])), list(hs1.get("mao", []))
            todos = dict(estado["herois_status"])
            todos[h1] = hs1
            todos[h2] = hs2
            delta["herois_status"] = todos
            logs.append(("DIRETOR", f"🕷️ {nome}: {h1} e {h2} trocaram de mão!"))
        else:
            # Só 1 herói: rouba 1 carta
            hs = dict(get_hs(heroi_alvo_nome))
            mao = list(hs.get("mao", []))
            if mao:
                carta_r = mao.pop(0)
                hs["mao"] = mao
                set_hs(heroi_alvo_nome, hs)
                logs.append(("DIRETOR", f"🕷️ {nome}: roubou '{carta_r.get('nome','?')}' de {heroi_alvo_nome}!"))

    elif inseto_id == "abelha_tecela":
        # Pega cartas do deck = nº de defensores, distribui 1 a cada, fica com 1
        deck_dir = list(estado.get("deck_diretor", []))
        mao_dir = list(estado.get("mao_diretor", []))
        cartas_compradas = []
        for _ in range(len(herois_nomes)):
            if deck_dir:
                cartas_compradas.append(deck_dir.pop())
        if cartas_compradas:
            mao_dir.append(cartas_compradas.pop(0))
            # As demais vão para os heróis (como bônus visível)
            todos_hs = dict(estado["herois_status"])
            for i, nome_h in enumerate(herois_nomes):
                if i < len(cartas_compradas):
                    hs = dict(todos_hs.get(nome_h, {}))
                    hs["mao"] = list(hs.get("mao", [])) + [cartas_compradas[i]]
                    todos_hs[nome_h] = hs
            delta["herois_status"] = todos_hs
            delta["deck_diretor"] = deck_dir
            delta["mao_diretor"] = mao_dir
            logs.append(("DIRETOR", f"🐝 {nome}: distribuiu cartas reveladas a todos!"))

    elif inseto_id == "efemera_mimetica":
        # Reativa efeito de inseto já usado pelo Diretor
        descarte_dir = list(estado.get("descarte_diretor", []))
        insetos_desc = [c for c in descarte_dir if c.get("tipo") == "inseto" and c["id"] != "efemera_mimetica"]
        if insetos_desc:
            alvo = random.choice(insetos_desc)
            logs.append(("DIRETOR", f"🦟 {nome}: reativando {alvo['nome']}..."))
            sub_delta, sub_logs, _ = aplicar_efeito_inseto(estado, alvo["id"], heroi_alvo_nome)
            for k, v in sub_delta.items():
                delta[k] = v
            logs.extend(sub_logs)
        else:
            logs.append(("INFO", f"🦟 {nome}: nada no descarte do Diretor para reativar."))

    elif inseto_id == "vespa_joia":
        # Olha a mão de cada defensor e rouba 1 sem olhar
        todas_maos = {h: get_hs(h).get("mao", []) for h in herois_nomes}
        log_reveal = " | ".join(f"{h}: {[c.get('nome','?') for c in m]}" for h, m in todas_maos.items())
        logs.append(("DIRETOR", f"🐝 {nome}: viu todas as mãos → {log_reveal}"))
        # Rouba 1 aleatória do alvo mais rico em cartas
        heroi_mais_cartas = max(herois_nomes, key=lambda h: len(get_hs(h).get("mao", [])), default=None)
        if heroi_mais_cartas:
            hs = dict(get_hs(heroi_mais_cartas))
            mao = list(hs.get("mao", []))
            if mao:
                carta_r = mao.pop(random.randrange(len(mao)))
                hs["mao"] = mao
                set_hs(heroi_mais_cartas, hs)
                delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
                logs.append(("DIRETOR", f"🐝 {nome}: roubou '{carta_r.get('nome','?')}' de {heroi_mais_cartas}!"))

    elif inseto_id == "viuva_negra":
        # Rouba todos os recursos da zona de maior concentração
        recursos_atuais = dict(estado.get("recursos", {}))
        total_perdido = 0
        for recurso, qtd in recursos_atuais.items():
            if qtd > 0:
                total_perdido += qtd
                recursos_atuais[recurso] = 0
                logs.append(("DIRETOR", f"🕷️ {nome}: confiscou {qtd}x {recurso}!"))
        if total_perdido:
            delta["recursos"] = recursos_atuais
        else:
            logs.append(("INFO", f"🕷️ {nome}: defensores sem recursos."))

    elif inseto_id == "cigarra_ressonante":
        # Reativa o efeito de qualquer inseto na mão do Diretor
        mao_dir = list(estado.get("mao_diretor", []))
        insetos_mao = [c for c in mao_dir if c.get("tipo") == "inseto" and c["id"] != "cigarra_ressonante"]
        if insetos_mao:
            alvo = random.choice(insetos_mao)
            logs.append(("DIRETOR", f"🪰 {nome}: reativou {alvo['nome']} da mão!"))
            sub_delta, sub_logs, _ = aplicar_efeito_inseto(estado, alvo["id"], heroi_alvo_nome)
            for k, v in sub_delta.items():
                delta[k] = v
            logs.extend(sub_logs)
        else:
            logs.append(("INFO", f"🪰 {nome}: sem insetos na mão do Diretor."))

    elif inseto_id == "besouro_gorgulho":
        # Pega topo do descarte e topo do deck do Defensor; Diretor escolhe 1 para roubar
        hs = dict(get_hs(heroi_alvo_nome))
        desc = list(hs.get("descarte", []))
        deck_h = list(hs.get("deck", []))
        cartas_escolha = []
        if desc:
            cartas_escolha.append(("descarte", desc[-1]))
        if deck_h:
            cartas_escolha.append(("deck", deck_h[-1]))
        if cartas_escolha:
            origem, carta_escolhida = cartas_escolha[0]  # IA pega a primeira
            if origem == "descarte":
                desc.pop()
            else:
                deck_h.pop()
            hs["descarte"] = desc
            hs["deck"] = deck_h
            set_hs(heroi_alvo_nome, hs)
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
            logs.append(("DIRETOR", f"🐜 {nome}: roubou '{carta_escolhida.get('nome','?')}' do {origem} de {heroi_alvo_nome}!"))

    elif inseto_id == "tarantula_golias":
        # Resgata carta do descarte do Defensor
        hs = dict(get_hs(heroi_alvo_nome))
        desc = list(hs.get("descarte", []))
        if desc:
            carta_r = desc.pop(random.randrange(len(desc)))
            hs["descarte"] = desc
            set_hs(heroi_alvo_nome, hs)
            delta["cartas_roubadas_total"] = estado.get("cartas_roubadas_total", 0) + 1
            logs.append(("DIRETOR", f"🕷️ {nome}: resgatou '{carta_r.get('nome','?')}' do descarte de {heroi_alvo_nome}!"))
        else:
            logs.append(("INFO", f"🕷️ {nome}: descarte vazio."))

    elif inseto_id == "libelula_blindada":
        # Protege a mão do Diretor: próximo roubo tentado por Defensor falha
        delta["mao_diretor_protegida"] = True
        logs.append(("DIRETOR", f"🛡️ {nome}: mão do Diretor protegida contra roubos!"))

    else:
        logs.append(("INFO", f"{emoji} {nome}: efeito não implementado."))

    # Verificar condição de derrota por cartas roubadas
    total_roubado = delta.get("cartas_roubadas_total", estado.get("cartas_roubadas_total", 0))
    if total_roubado >= 10 and not delta.get("derrota"):
        delta["derrota"] = True
        delta["msg_fim"] = "Isectum roubou 10+ cartas! DERROTA dos Defensores."
        logs.append(("DERROTA", delta["msg_fim"]))

    return delta, logs, requer_escolha


# ═══════════════════════════════════════════════════════════════════════════
# EFEITOS DE RUNAS DOS DEFENSORES
# ═══════════════════════════════════════════════════════════════════════════
def aplicar_efeito_runa(estado, carta_runa, heroi_nome):
    """Executa o efeito de uma carta de Runa jogada pelo Defensor."""
    delta, logs = {}, []
    efeito = carta_runa.get("efeito", "")
    hs = dict(estado["herois_status"].get(heroi_nome, {}))

    if efeito == "acoes_extras":
        valor = carta_runa.get("valor", 2)
        hs["acoes_extras"] = hs.get("acoes_extras", 0) + valor
        logs.append(("HEROI", f"⚡ Runa da Haste: {heroi_nome} ganhou +{valor} ações!"))

    elif efeito == "revelar_deck_diretor":
        valor = carta_runa.get("valor", 3)
        deck_dir = list(estado.get("deck_diretor", []))
        reveladas = deck_dir[-valor:] if len(deck_dir) >= valor else deck_dir[:]
        delta["deck_diretor_revelado"] = reveladas
        nomes = [c.get("nome", "?") for c in reveladas]
        logs.append(("HEROI", f"👁 Runa da Visão: próximas cartas do Diretor → {', '.join(nomes)}"))

    elif efeito == "fortaleza_turno":
        hs["imune_destruicao"] = True
        trabalho = carta_runa.get("trabalho", 8)
        hs["pontos_trabalho"] = hs.get("pontos_trabalho", 0) + trabalho
        logs.append(("HEROI", f"🏰 Runa da Fortaleza: +{trabalho} Trabalho e imune à destruição!"))

    elif efeito == "comprar_extra":
        valor = carta_runa.get("valor", 2)
        deck_h = list(hs.get("deck", []))
        mao = list(hs.get("mao", []))
        for _ in range(valor):
            if not deck_h:
                # Reembaralha descarte
                desc = list(hs.get("descarte", []))
                if not desc:
                    break
                random.shuffle(desc)
                deck_h = desc
                hs["descarte"] = []
            if deck_h:
                mao.append(deck_h.pop())
        hs["deck"] = deck_h
        hs["mao"] = mao
        logs.append(("HEROI", f"✨ Runa de Recuperação: {heroi_nome} comprou {valor} cartas!"))

    todos_hs = dict(estado["herois_status"])
    todos_hs[heroi_nome] = hs
    delta["herois_status"] = todos_hs
    return delta, logs


# ═══════════════════════════════════════════════════════════════════════════
# EFEITOS DE DEFESA DOS DEFENSORES
# ═══════════════════════════════════════════════════════════════════════════
def aplicar_efeito_defesa(estado, carta_defesa, heroi_nome):
    """Executa o efeito de uma carta de Defesa jogada pelo Defensor."""
    delta, logs = {}, []
    efeito = carta_defesa.get("efeito", "")
    hs = dict(estado["herois_status"].get(heroi_nome, {}))

    if efeito == "anular_roubo":
        hs["protegido_roubo"] = True
        logs.append(("HEROI", f"🛡 Escudo de Quitina ativado! {heroi_nome} está protegido contra o próximo roubo."))

    elif efeito == "bloquear_zona":
        # Bloqueia avanço numa zona muralha por 1 turno
        zonas_b = dict(estado.get("zonas_bloqueadas", {}))
        zona_mais_cheia = max(
            ["muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste"],
            key=lambda z: estado.get("invasores", {}).get(z, 0)
        )
        zonas_b[zona_mais_cheia] = 1
        delta["zonas_bloqueadas"] = zonas_b
        logs.append(("HEROI", f"🕸 Teia Endurecida: {zona_mais_cheia} bloqueada por 1 turno!"))

    elif efeito == "cancelar_atordoamento":
        if hs.get("turno_pulado"):
            hs["turno_pulado"] = False
            logs.append(("HEROI", f"⚗ Antídoto Alquímico: atordoamento de {heroi_nome} cancelado!"))
        else:
            logs.append(("INFO", f"⚗ Antídoto Alquímico: {heroi_nome} não estava atordoado."))

    elif efeito == "resistir_roubo_1":
        hs["resistir_roubo_1"] = True
        logs.append(("HEROI", f"💎 Amuleto de Resistência ativado! {heroi_nome} devolverá a próxima carta roubada."))

    todos_hs = dict(estado["herois_status"])
    todos_hs[heroi_nome] = hs
    delta["herois_status"] = todos_hs
    return delta, logs


# ═══════════════════════════════════════════════════════════════════════════
# TURNO DO DIRETOR (IA)
# ═══════════════════════════════════════════════════════════════════════════
def turno_diretor_ia(estado):
    """
    Executa automaticamente o turno do Diretor Isectum (modo solo/IA).
    Retorna lista de (delta, logs) a serem aplicados sequencialmente.
    """
    resultados = []
    acoes_max = estado.get("acoes_diretor_max", 3)
    deck_dir = list(estado.get("deck_diretor", []))
    mao_dir = list(estado.get("mao_diretor", []))
    descarte_dir = list(estado.get("descarte_diretor", []))
    herois_nomes = estado.get("herois_nomes", [])
    heroi_idx = estado.get("turno_heroi_idx", 0) % max(len(herois_nomes), 1)
    heroi_alvo = herois_nomes[heroi_idx] if herois_nomes else None

    # 1. Comprar até tam_mao_diretor cartas
    tam_mao = estado.get("tam_mao_diretor", 3)
    while len(mao_dir) < tam_mao and deck_dir:
        mao_dir.append(deck_dir.pop())

    d_compra = {"deck_diretor": deck_dir, "mao_diretor": list(mao_dir)}
    logs_compra = [("DIRETOR", f"🃏 Diretor Isectum comprou cartas (mão: {len(mao_dir)}).")]
    resultados.append((d_compra, logs_compra))

    # 2. Jogar cartas (até acoes_max)
    acoes_usadas = 0
    while mao_dir and acoes_usadas < acoes_max:
        # IA: tenta jogar o inseto com maior impacto (prioriza roubos)
        ordem_prioridade = [
            "carrapato_vampiro", "formiga_correicao", "besouro_unicornio",
            "mosca_tse_tse", "vespa_cacadora", "louva_deus",
            "gafanhoto_praga", "viuva_canibal", "enxame_rainha",
        ]
        carta_jogar = None
        for id_pref in ordem_prioridade:
            for c in mao_dir:
                if c.get("id") == id_pref:
                    carta_jogar = c
                    break
            if carta_jogar:
                break
        if not carta_jogar:
            carta_jogar = mao_dir[0]

        mao_dir.remove(carta_jogar)
        descarte_dir.append(carta_jogar)

        estado_temp = dict(estado)
        estado_temp["mao_diretor"] = list(mao_dir)
        estado_temp["descarte_diretor"] = list(descarte_dir)

        delta_ef, logs_ef, _ = aplicar_efeito_inseto(estado_temp, carta_jogar["id"], heroi_alvo)
        delta_ef["mao_diretor"] = list(mao_dir)
        delta_ef["descarte_diretor"] = list(descarte_dir)
        logs_ef.insert(0, ("DIRETOR", f"▶ Diretor joga: {carta_jogar['emoji']} {carta_jogar['nome']}"))
        resultados.append((delta_ef, logs_ef))

        # Atualiza estado_temp para próxima ação em cadeia
        for k, v in delta_ef.items():
            estado_temp[k] = v
        estado = dict(estado)
        for k, v in delta_ef.items():
            estado[k] = v

        acoes_usadas += 1

    return resultados


# ═══════════════════════════════════════════════════════════════════════════
# VERIFICAR CONDIÇÕES DE VITÓRIA
# ═══════════════════════════════════════════════════════════════════════════
def verificar_condicoes(estado):
    """Retorna (vitoria, derrota, msg) com base nas condições atuais."""
    if estado.get("derrota"):
        return False, True, estado.get("msg_fim", "Derrota!")
    if estado.get("vitoria"):
        return True, False, estado.get("msg_fim", "Vitória!")

    # Derrota: câmara central com 3+ invasores
    if estado.get("camara_central_invasores", 0) >= 3:
        return False, True, "Isectum invadiu a Câmara Central! DERROTA."

    # Derrota: 10+ cartas roubadas
    if estado.get("cartas_roubadas_total", 0) >= 10:
        return False, True, "Isectum roubou 10+ cartas! DERROTA dos Defensores."

    # Vitória: todos os bosses capturáveis eliminados
    bosses_capturavel = [b for b in INSETOS_BOSS if INSETOS_BOSS[b]["capturavel"]]
    bosses_elim = estado.get("bosses_eliminados", [])
    if all(b in bosses_elim for b in bosses_capturavel):
        return True, False, "Todos os bosses eliminados! VITÓRIA dos Defensores!"

    # Vitória: sobreviveu ao máximo de rodadas
    if estado.get("rodada", 1) > estado.get("rodadas_max", 15):
        return True, False, f"Sobreviveram {estado['rodadas_max']} rodadas! VITÓRIA!"

    return False, False, ""


# ═══════════════════════════════════════════════════════════════════════════
# APLICA DELTA AO ESTADO
# ═══════════════════════════════════════════════════════════════════════════
def aplicar_delta_castas(estado, delta):
    """Aplica um dicionário de alterações ao estado de forma imutável."""
    novo = dict(estado)
    for k, v in delta.items():
        novo[k] = v
    return novo
