"""
castas_setup_state_data.py — Constantes da tela de configuração do modo Castas
"""
from ...personagens import Stark, Elden, Doom, Gruu, Kuro, Darwin, Aquele

ESTADO_JOGO_CASTAS       = "castas"
ESTADO_JOGO_CASTAS_SETUP = "castas_setup"

C_BG        = (5,  4, 12)
C_PAINEL    = (10, 12, 26)
C_BORDA     = (60, 30, 100)
C_ACENTO    = (200, 80, 255)
C_OURO      = (255, 195, 40)
C_TEXTO     = (235, 240, 255)
C_DIM       = (110, 100, 145)
C_VERDE     = (50, 220, 110)
C_PERIGO    = (255, 55, 55)
C_INSETO    = (130, 240, 80)

DIFICULDADES_CASTAS = [
    {
        "id":          "facil",
        "nome":        "Aprendiz",
        "pedregulhos": 6,
        "tesouro":     25,
        "reserva":     12,
        "acoes_dir":   2,
        "desc":        "Filho do Imperador recebe 2 ações por turno. Bom para aprender.",
    },
    {
        "id":          "normal",
        "nome":        "Guardião",
        "pedregulhos": 8,
        "tesouro":     20,
        "reserva":     10,
        "acoes_dir":   3,
        "desc":        "Filho do Imperador recebe 3 ações por turno. Experiência equilibrada.",
    },
    {
        "id":          "dificil",
        "nome":        "Rainha Suprema",
        "pedregulhos": 10,
        "tesouro":     15,
        "reserva":     8,
        "acoes_dir":   4,
        "desc":        "Filho do Imperador recebe 4 ações por turno. Para veteranos.",
    },
]

HEROIS_DISPONIVEIS = [
    ("Aquele", Aquele, "Guerreiro"),
    ("Stark",  Stark,  "Paladino"),
    ("Elden",  Elden,  "Mago"),
    ("Doom",   Doom,   "Ladino"),
    ("Gruu",   Gruu,   "Bárbaro"),
    ("Kuro",   Kuro,   "Ladino"),
    ("Darwin", Darwin, "Druida"),
]
