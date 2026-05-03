import random
from .config import (
    TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, 
    TERRENO_PAREDE, TERRENO_AGUA, TERRENO_ROCHA, TERRENO_BARRIL
)

class MapGenerator:
    @staticmethod
    def gerar_mapa_vazio(largura, altura):
        return [[TERRENO_NORMAL for _ in range(largura)] for _ in range(altura)]

    @staticmethod
    def gerar_aleatorio(largura, altura):
        mapa = [[TERRENO_NORMAL for _ in range(largura)] for _ in range(altura)]
        
        for y in range(altura):
            for x in range(largura):
                # Bordas sempre parede? Opcional. Vamos deixar aberto por enquanto
                # mas o tabuleiro adiciona limitadores depois se quiser.
                
                r = random.random()
                if r < 0.05:
                    mapa[y][x] = TERRENO_PAREDE
                elif r < 0.15:
                    mapa[y][x] = TERRENO_FLORESTA
                elif r < 0.20:
                    mapa[y][x] = TERRENO_DIFICIL
                elif r < 0.25:
                    mapa[y][x] = TERRENO_AGUA
                elif r < 0.28:
                    mapa[y][x] = TERRENO_ROCHA
                elif r < 0.30:
                    mapa[y][x] = TERRENO_BARRIL
                else:
                    mapa[y][x] = TERRENO_NORMAL
                    
        return mapa
