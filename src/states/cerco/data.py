"""
cerco_state_data.py — Constantes do estado de cerco.

Extraído de cerco_state.py para reduzir o monolito.
"""
from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
# PALETA
# ═══════════════════════════════════════════════════════════════════════════
C_BG      = (5,  6, 12)
C_PAINEL  = (14, 16, 30)
C_BORDA   = (45, 48, 78)
C_ACENTO  = (180, 120, 255)
C_OURO    = (255, 195,  40)
C_CRISTAL = (180,  80, 255)
C_VERDE   = ( 50, 220, 110)
C_PERIGO  = (255,  55,  55)
C_CERCO   = (255, 100,   0)
C_TEXTO   = (235, 240, 255)
C_DIM     = (110, 120, 155)
C_INVASOR = ( 50, 240,  50)
C_BRUTE   = (255, 130,   0)
C_HEROI   = (100, 200, 255)
C_CARD    = ( 22,  28,  52)
C_CARD_HL = ( 40,  55, 100)
C_MOVE_HL = ( 30,  80,  30)
C_ACT_HL  = ( 80,  30,  30)

# Mapeamento zona -> tipo de terreno (para sprites)
ZONA_TERRENO_MAP = {
    "camara_central": "normal",
    "curtume":        "dificil",
    "carpintaria":    "floresta",
    "fundicao":       "rocha",
    "patio":          "fogo",
    "muralha_norte":  "parede",
    "muralha_sul":    "parede",
    "muralha_oeste":  "parede",
    "muralha_leste":  "parede",
    "torre_nw":       "rocha",
    "torre_ne":       "rocha",
    "torre_sw":       "rocha",
    "torre_se":       "rocha",
    "_corredor":      "normal",
    "_campo":         "campo",
    "_exterior":      "exterior",
}

# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT DAS ZONAS NO MAPA (rx, ry, rw, rh — proporções 0..1)
# ═══════════════════════════════════════════════════════════════════════════
LAYOUT_ZONAS = {
    "muralha_norte":  (0.35, 0.01, 0.30, 0.12),
    "muralha_sul":    (0.35, 0.87, 0.30, 0.12),
    "muralha_oeste":  (0.00, 0.28, 0.16, 0.44),
    "muralha_leste":  (0.84, 0.28, 0.16, 0.44),
    "carpintaria":    (0.35, 0.14, 0.30, 0.20),
    "curtume":        (0.35, 0.66, 0.30, 0.20),
    "fundicao":       (0.17, 0.28, 0.17, 0.44),
    "patio":          (0.66, 0.28, 0.17, 0.44),
    "camara_central": (0.35, 0.35, 0.30, 0.30),
    "torre_nw":       (0.01, 0.01, 0.12, 0.12),
    "torre_ne":       (0.87, 0.01, 0.12, 0.12),
    "torre_sw":       (0.01, 0.87, 0.12, 0.12),
    "torre_se":       (0.87, 0.87, 0.12, 0.12),
}

COR_ZONA = {
    "muralha_norte": (35, 35, 62), "muralha_sul":   (35, 35, 62),
    "muralha_oeste": (35, 35, 62), "muralha_leste": (35, 35, 62),
    "carpintaria":   (20, 42, 20), "curtume":       (42, 28, 12),
    "fundicao":      (42, 22, 22), "patio":         (25, 25, 52),
    "camara_central":(12, 12, 48),
    "torre_nw": (28, 28, 52), "torre_ne": (28, 28, 52),
    "torre_sw": (28, 28, 52), "torre_se": (28, 28, 52),
}

ICONE_ZONA = {
    "muralha_norte": "\U0001f9f1", "muralha_sul":   "\U0001f9f1",
    "muralha_oeste": "\U0001f9f1", "muralha_leste": "\U0001f9f1",
    "carpintaria":   "\U0001faB5", "curtume":       "\U0001f9f3",
    "fundicao":      "\u2699\ufe0f", "patio":         "\u26cf\ufe0f",
    "camara_central":"\U0001f3f0",
    "torre_nw": "\U0001f5fc", "torre_ne": "\U0001f5fc",
    "torre_sw": "\U0001f5fc", "torre_se": "\U0001f5fc",
}

# ═══════════════════════════════════════════════════════════════════════════
# NARRATIVAS
# ═══════════════════════════════════════════════════════════════════════════
NAR = {
    "invasor":      ["Os insetoides escalam as muralhas!", "A horda avança!"],
    "mover":        ["Tambores — eles avançam!", "A maré negra rasteja!"],
    "torre_assalto":["Uma Torre de Assalto emerge!", "Pela pedra sagrada!"],
    "catapulta":    ["CATAPULTA! A rocha impacta!", "Pedras de fogo voam!"],
    "cerco":        ["O cerco aperta — resistam!", "Defendam a fortaleza!"],
    "derrota":      ["A fortaleza caiu. Isectum vence..."],
}

# Modos de ação do herói
MODO_NENHUM    = "nenhum"
MODO_MOVER     = "mover"
MODO_TRABALHAR = "trabalhar"
MODO_ESCAVAR   = "escavar"
MODO_SUBORNAR  = "subornar"
MODO_UPGRADE   = "upgrade"
MODO_CONVOCAR  = "convocar"
MODO_ATACAR    = "atacar"
MODO_ATIRAR    = "atirar"
