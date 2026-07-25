"""
cerco_setup_state_data.py — Constantes da tela de configuração do Cerco
"""
from ...personagens import Stark, Elden, Doom, Gruu, Kuro, Darwin, Aquele

C_BG        = (8, 10, 20)
C_PAINEL    = (14, 16, 30)
C_BORDA     = (45, 48, 78)
C_ACENTO    = (180, 120, 255)
C_OURO      = (255, 195, 40)
C_TEXTO     = (235, 240, 255)
C_DIM       = (110, 120, 155)
C_VERDE     = (50, 220, 110)
C_PERIGO    = (255, 55, 55)

DIFICULDADES = [
    {"id": "facil",   "nome": "Fácil (1/4 Deck)",         "fator_deck": 0.25, "pedregulhos": 5,  "tesouro": 30, "reserva": 8},
    {"id": "normal",  "nome": "Média (1/2 Deck)",         "fator_deck": 0.50, "pedregulhos": 8,  "tesouro": 20, "reserva": 10},
    {"id": "dificil", "nome": "Difícil (Deck Completo)", "fator_deck": 1.00, "pedregulhos": 12, "tesouro": 15, "reserva": 14},
]

HEROIS_DISPONIVEIS = [
    ("Aquele", Aquele, "Guerreiro"),
    ("Stark",  Stark,  "Paladino"),
    ("Elden",  Elden,  "Mago"),
    ("Doom",   Doom,   "Ladino"),
    ("Gruu",   Gruu,   "Barbaro"),
    ("Kuro",   Kuro,   "Ladino"),
    ("Darwin", Darwin, "Druida"),
]

ICONES_HEROI = {
    "Aquele": "🌑",
    "Stark":  "🛡️",
    "Elden":  "✨",
    "Doom":   "🌑",
    "Gruu":   "💀",
    "Kuro":   "🗡️",
    "Darwin": "🌿",
}
