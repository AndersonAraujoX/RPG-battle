import json
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def calcular_distancia(p1, p2):
    return max(abs(p1.pos_x - p2.pos_x), abs(p1.pos_y - p2.pos_y))

def carregar_dados_personagens():
    with open(resource_path('dados/personagens.json'), 'r') as f:
        return json.load(f)
