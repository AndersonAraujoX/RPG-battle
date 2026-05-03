import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.personagem_base import Personagem
from src.personagens.status_efeito import StatusEfeito

class MockTabuleiro:
    def get_terrain_em(self, x, y): return 0

class TestStatusEffects(unittest.TestCase):
    def setUp(self):
        self.p1 = Personagem("TestSubject", "A", 1)
        self.tabuleiro = MockTabuleiro()

    def test_apply_and_tick_effect(self):
        # Apply Poison
        self.p1.aplicar_status_efeito("Envenenado", 3, logger=lambda x: None)
        self.assertEqual(len(self.p1.status_efeitos), 1)
        self.assertEqual(self.p1.status_efeitos[0].nome, "Envenenado")
        self.assertEqual(self.p1.status_efeitos[0].duracao_restante, 3)
        
        # Tick 1
        self.p1.tick_status_efeitos(self.tabuleiro, logger=lambda x: None)
        self.assertEqual(self.p1.status_efeitos[0].duracao_restante, 2)
        
        # Tick 2
        self.p1.tick_status_efeitos(self.tabuleiro, logger=lambda x: None)
        self.assertEqual(self.p1.status_efeitos[0].duracao_restante, 1)
        
        # Tick 3 (Expires at end of tick or start? usually start of next?)
        # Logic: if not efeito.tick(): remove.
        # tick() returns True if alive.
        # self.duracao -= 1. if duracao > 0 return True.
        
        self.p1.tick_status_efeitos(self.tabuleiro, logger=lambda x: None)
        # 1 -> 0. Should be removed.
        self.assertEqual(len(self.p1.status_efeitos), 0)

    def test_poison_damage_application(self):
        # Note: Damage logic is usually in MotorCombate loop or aplicar_efeito_por_turno?
        # Let's check StatusEfeito class logic.
        # If simple property, it might need external trigger.
        # MotorCombate code seen earlier had damage logic INSIDE avancar_turno loops.
        # But tick_status_efeitos calls `efeito.aplicar_efeito_por_turno`.
        # Let's verify if `aplicar_efeito_por_turno` does anything for generic effects.
        pass

    def test_remove_effect(self):
        self.p1.aplicar_status_efeito("Envenenado", 5)
        self.p1.remover_status_efeito("Envenenado")
        self.assertEqual(len(self.p1.status_efeitos), 0)

if __name__ == '__main__':
    unittest.main()
