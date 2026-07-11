"""
castas_state_data.py — Constantes do modo Castas dos Isectum
"""
ESTADO_JOGO_CASTAS       = "castas"
ESTADO_JOGO_CASTAS_SETUP = "castas_setup"

# ── PALETA ──
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

# ── MODOS DE AÇÃO (herdados do Cerco + novos para Diretor) ──
MODO_NENHUM    = "nenhum"
MODO_MOVER     = "mover"
MODO_TRABALHAR = "trabalhar"
MODO_ESCAVAR   = "escavar"
MODO_SUBORNAR  = "subornar"
MODO_UPGRADE   = "upgrade"
MODO_CONVOCAR  = "convocar"
MODO_ATACAR    = "atacar"
MODO_ATIRAR    = "atirar"
# Diretor
MODO_DIR_ESCOLHER_CASTA = "dir_escolher_casta"
MODO_DIR_ESCOLHER_ZONA  = "dir_escolher_zona"

NAR = {
    "cerco":     ["Os insetos avançam!", "Uma horda se aproxima!", "A fortaleza treme!"],
    "invasor":   ["Novas castas emergem das sombras!", "Os insetos se multiplicam!"],
    "mover":     ["Os invasores reorganizam suas fileiras...", "Movimentação nas muralhas!"],
    "catapulta": ["Projéteis ácidos disparam!", "Fogo insetoide rasga o céu!"],
    "torre":     ["A torre resiste... por enquanto.", "Defesas testadas!"],
}

# ── DIFICULDADES DO FILHO DO IMPERADOR ──
DIFICULDADES_CASTAS = [
    {
        "id":          "facil",
        "nome":        "Aprendiz",
        "pedregulhos": 6,
        "tesouro":     25,
        "reserva":     12,
        "acoes_dir":   2,   # ações por turno
        "desc":        "Filho do Imperador recebe 2 ações. Bom para aprender.",
    },
    {
        "id":          "normal",
        "nome":        "Guardião",
        "pedregulhos": 8,
        "tesouro":     20,
        "reserva":     10,
        "acoes_dir":   3,
        "desc":        "Filho do Imperador recebe 3 ações. Experiência equilibrada.",
    },
    {
        "id":          "dificil",
        "nome":        "Rainha Suprema",
        "pedregulhos": 10,
        "tesouro":     15,
        "reserva":     8,
        "acoes_dir":   4,
        "desc":        "Filho do Imperador recebe 4 ações. Para jogadores experientes.",
    },
]
