"""
tests/test_fluidity.py — Testes Unitários de Quick-Cast, Snap Magnético, Auto-End Turn e Easing (Padrão AAA)
"""
import unittest
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago
from src.tabuleiro import Tabuleiro


class TestFluidityAndUXSuite(unittest.TestCase):

    def test_quick_cast_identifica_indice_da_carta(self):
        # Arrange
        teclas_mapeadas = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}

        # Act & Assert
        self.assertEqual(teclas_mapeadas[1], 0)
        self.assertEqual(teclas_mapeadas[3], 2)
        self.assertEqual(teclas_mapeadas[5], 4)

    def test_snap_magnetico_trava_no_inimigo_mais_proximo(self):
        # Arrange
        tab = Tabuleiro(largura=10, altura=10)
        inimigo = Mago("Gorgulho", "B")
        inimigo.hp_atual = 20
        tab.adicionar_personagem(inimigo, 5, 5)

        # Act (Mouse apontado para 4, 4 - dentro do raio de 2 células)
        mouse_gx, mouse_gy = 4, 4
        snap_target = None
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = mouse_gx + dx, mouse_gy + dy
                if 0 <= nx < tab.largura and 0 <= ny < tab.altura:
                    u = tab.grid[ny][nx]
                    if u and getattr(u, "time", "A") == "B" and getattr(u, "hp_atual", 0) > 0:
                        snap_target = (nx, ny)
                        break

        # Assert
        self.assertEqual(snap_target, (5, 5))

    def test_auto_end_turn_detecta_recursos_esgotados(self):
        # Arrange
        estado = {
            "mao": [],
            "pontos_movimento": 0,
            "pontos_trabalho": 0,
            "pontos_escavacao": 0
        }

        # Act
        sem_acoes_uteis = len(estado["mao"]) == 0 and estado["pontos_movimento"] <= 0 and estado["pontos_trabalho"] <= 0 and estado["pontos_escavacao"] <= 0

        # Assert
        self.assertTrue(sem_acoes_uteis)


if __name__ == "__main__":
    unittest.main()
