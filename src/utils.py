import json

def calcular_distancia(p1, p2):
    return max(abs(p1.pos_x - p2.pos_x), abs(p1.pos_y - p2.pos_y))

def carregar_dados_personagens():
    with open('dados/personagens.json', 'r') as f:
        return json.load(f)
