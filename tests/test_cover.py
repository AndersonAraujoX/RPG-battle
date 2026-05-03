import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import calcular_cobertura
from src.personagens.personagem_base import Personagem
from src.config import TERRENO_PAREDE, TERRENO_NORMAL

class MockTabuleiro:
    def __init__(self):
        self.largura = 10
        self.altura = 10
        self.terrain_grid = [[TERRENO_NORMAL for _ in range(10)] for _ in range(10)]
        self.personagens_grid = [[None for _ in range(10)] for _ in range(10)]
        
    def get_personagem_em(self, x, y):
        return self.personagens_grid[y][x]

class TestCoverSystem(unittest.TestCase):
    def setUp(self):
        self.tab = MockTabuleiro()
        self.p1 = Personagem("Shooter", "A", 1)
        self.p1.pos_x, self.p1.pos_y = 0, 0
        
        self.p2 = Personagem("Target", "B", 1)
        self.p2.pos_x, self.p2.pos_y = 0, 4 # 3 tiles between them: (0,1), (0,2), (0,3)

    def test_no_cover_open_field(self):
        cover = calcular_cobertura(self.p1, self.p2, self.tab)
        self.assertEqual(cover, 0)

    def test_creature_cover(self):
        # Place creature in strict line (0, 2)
        blocker = Personagem("Blocker", "B", 1)
        self.tab.personagens_grid[2][0] = blocker
        
        cover = calcular_cobertura(self.p1, self.p2, self.tab)
        self.assertEqual(cover, 2) # Half Cover

    def test_wall_cover(self):
        # Place wall in strict line (0, 2)
        self.tab.terrain_grid[2][0] = TERRENO_PAREDE
        
        cover = calcular_cobertura(self.p1, self.p2, self.tab)
        self.assertEqual(cover, 1000) # Total Cover

if __name__ == '__main__':
    unittest.main()
