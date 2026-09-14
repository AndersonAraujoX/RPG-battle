"""
tests/test_cover.py — Testes Unitários de Cobertura Tática, Estruturas Destruíveis e Ninhos Dinâmicos (Padrão AAA)
"""
import unittest
from src.tabuleiro import Tabuleiro
from src.personagens.guerreiro import Guerreiro
from src.config import TERRENO_FLORESTA, TERRENO_ROCHA, TERRENO_DIFICIL


class TestCoverAndDestructibleTerrain(unittest.TestCase):

    def test_obter_bonificacao_cobertura_floresta_concede_3_ac(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)
        tab.terrain_grid[4][5] = TERRENO_FLORESTA  # Floresta adjacente em (5, 4)
        heroi = Guerreiro("Stark", "A")
        tab.adicionar_personagem(heroi, 4, 4)

        # Act
        bonus_ac = tab.obter_bonificacao_cobertura(4, 4)

        # Assert
        self.assertEqual(bonus_ac, 3)

    def test_obter_bonificacao_cobertura_rocha_concede_5_ac(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)
        tab.terrain_grid[4][5] = TERRENO_ROCHA  # Rocha pesada em (5, 4)
        heroi = Guerreiro("Stark", "A")
        tab.adicionar_personagem(heroi, 4, 4)

        # Act
        bonus_ac = tab.obter_bonificacao_cobertura(4, 4)

        # Assert
        self.assertEqual(bonus_ac, 5)

    def test_aplicar_dano_estrutura_destroi_terreno_vira_escombros(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)
        tab.terrain_grid[2][2] = TERRENO_FLORESTA
        tab.estrutura_hp_grid[2][2] = 15

        # Act (Dano suficiente para destruir a estrutura)
        destruida = tab.aplicar_dano_estrutura(2, 2, 20)

        # Assert
        self.assertTrue(destruida)
        self.assertEqual(tab.terrain_grid[2][2], TERRENO_DIFICIL)
        self.assertEqual(tab.estrutura_hp_grid[2][2], 0)


if __name__ == "__main__":
    unittest.main()
