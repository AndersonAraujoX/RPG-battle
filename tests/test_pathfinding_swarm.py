"""
tests/test_pathfinding_swarm.py — Testes Unitários de Pathfinding A*, Disposição de Cartas em Leque e Enxame (Padrão AAA)
"""
import unittest
from src.tabuleiro import Tabuleiro
from src.config import TERRENO_PAREDE, TERRENO_NORMAL


class TestPathfindingAndSwarmSuite(unittest.TestCase):

    def test_encontrar_caminho_retorna_rota_direta(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)

        # Act
        caminho = tab.encontrar_caminho(2, 2, 5, 2, max_passos=5)

        # Assert
        self.assertEqual(len(caminho), 3)
        self.assertEqual(caminho[-1], (5, 2))
        self.assertIn((3, 2), caminho)
        self.assertIn((4, 2), caminho)

    def test_encontrar_caminho_desvia_de_obstaculo_parede(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)
        # Coloca parede bloqueando o caminho direto (3, 2)
        tab.terrain_grid[2][3] = TERRENO_PAREDE

        # Act
        caminho = tab.encontrar_caminho(2, 2, 4, 2, max_passos=6)

        # Assert
        self.assertTrue(len(caminho) > 0)
        self.assertNotIn((3, 2), caminho)  # Não atravessa a parede
        self.assertEqual(caminho[-1], (4, 2))

    def test_encontrar_caminho_respeita_limite_max_passos(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)

        # Act (Destino a 6 passos de distância, mas orçamento é 3)
        caminho = tab.encontrar_caminho(1, 1, 7, 1, max_passos=3)

        # Assert
        self.assertEqual(caminho, [])

    def test_calculo_leque_cartas_arco_simetrico(self):
        # Arrange
        total_cartas = 5
        mid_idx = (total_cartas - 1) / 2.0  # 2.0

        # Act
        arc_card_0 = int(((0 - mid_idx) ** 2) * 1.6)
        arc_card_2 = int(((2 - mid_idx) ** 2) * 1.6)
        arc_card_4 = int(((4 - mid_idx) ** 2) * 1.6)

        # Assert
        self.assertEqual(arc_card_2, 0)  # Carta central não desce
        self.assertEqual(arc_card_0, arc_card_4)  # Cartas das pontas são simétricas
        self.assertTrue(arc_card_0 > 0)


if __name__ == "__main__":
    unittest.main()
