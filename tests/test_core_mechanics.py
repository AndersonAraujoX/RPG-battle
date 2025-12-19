import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import rolar_dado, rolar_d20

class TestCoreMechanics(unittest.TestCase):
    def test_dice_roll_basic(self):
        """Test basic d20 roll bounds."""
        for _ in range(100):
            res = rolar_dado(20)
            self.assertTrue(1 <= res <= 20)

    def test_advantage(self):
        """Test Advantage logic."""
        # Hard to test random statistically in unit test without mocking.
        # But we can check internal logic if we mocked random, or just check return format.
        roll, msg = rolar_d20(vantagem=True)
        self.assertTrue(1 <= roll <= 20)
        self.assertIn("Vantagem", msg)
        
    def test_disadvantage(self):
        """Test Disadvantage logic."""
        roll, msg = rolar_d20(desvantagem=True)
        self.assertTrue(1 <= roll <= 20)
        self.assertIn("Desvantagem", msg)

    def test_cancellation(self):
        """Test Cancellation logic."""
        roll, msg = rolar_d20(vantagem=True, desvantagem=True)
        self.assertTrue(1 <= roll <= 20)
        self.assertEqual(msg, "") # Should be empty string as per implementation

    def test_saving_throw(self):
        """Test Saving Throw arithmetic (mocked roll would be better, but we check ranges)."""
        from src.personagens.personagem_base import Personagem
        p = Personagem("TestMage", "A", 1)
        # Force stats -> DEX 10 (Mod 0)
        p._destreza = 10
        
        # DC 1 (Always success unless roll 1 + 0 < 1 impossible)
        success, msg = p.fazer_teste_resistencia('destreza', 1, logger=lambda x: None)
        self.assertTrue(success)
        
        # DC 30 (Always fail)
        success, msg = p.fazer_teste_resistencia('destreza', 30, logger=lambda x: None)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
