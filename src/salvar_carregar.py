import pickle

def salvar_jogo(estado_jogo, nome_arquivo="savegame.pkl"):
    """Salva o estado do jogo em um arquivo."""
    try:
        with open(nome_arquivo, 'wb') as f:
            pickle.dump(estado_jogo, f)
        print(f"Jogo salvo em {nome_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar o jogo: {e}")

def carregar_jogo(nome_arquivo="savegame.pkl"):
    """Carrega o estado do jogo de um arquivo."""
    try:
        with open(nome_arquivo, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f"Arquivo de save '{nome_arquivo}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o jogo: {e}")
        return None
        return None

import json
import os

def salvar_mapa_json(mapa_grid, nome_arquivo="custom_map.json"):
    try:
        with open(nome_arquivo, 'w') as f:
            json.dump(mapa_grid, f)
        print(f"Mapa salvo em {nome_arquivo}")
        return True
    except Exception as e:
        print(f"Erro ao salvar mapa JSON: {e}")
        return False

def carregar_mapa_json(nome_arquivo="custom_map.json"):
    try:
        if not os.path.exists(nome_arquivo): return None
        with open(nome_arquivo, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar mapa JSON: {e}")
        return None
