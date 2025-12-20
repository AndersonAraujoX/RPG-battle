import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.personagem_base import Personagem

class TestSavingThrows(unittest.TestCase):
    def setUp(self):
        self.p1 = Personagem("Hero", "A", 1)
        # Base stats are 10 (+0 mod)
        self.p1._destreza = 14 # +2 Mod
        self.p1._constituicao = 10 # +0 Mod
        # self.p1.bonus_proficiencia is calculated based on level (1 -> +2)
        
        # Add proficiency
        self.p1.imunidades = [] # Re-using this list logic? No, proficiency is usually a list of attributes.
        # Current implementation of fazer_teste_resistencia uses mod_<attr> + proficiency (if class has it?)
        # Let's check the implementation of fazer_teste_resistencia first or assume generic behavior.
        # Actually I need to check how proficiency is handled in saves.
        # src/personagens/personagem_base.py: fazer_teste_resistencia
    
    def test_calculate_modifier(self):
        # DEX 14 -> +2
        self.assertEqual(self.p1.mod_des, 2)
        
    def test_saving_throw_mechanic(self):
        # We can't easily test random dice rolls without mocking or statistical tests.
        # Let's mock the roll or check the math range.
        
        # Mock rolar_d20 to return a fixed value
        # But rolar_d20 is imported in utils.
        # We can patch it or just check if the method runs without crashing.
        
        # Let's verify the modifier is applied.
        # Logic: roll + mod >= CD -> Success
        
        # Pass extremely low CD -> Should succeed
        success, msg = self.p1.fazer_teste_resistencia('destreza', 2) # Roll (1-20) + 2 >= 2. Min result 3. Always success.
        self.assertTrue(success, "Should succeed against low DC")
        
        # Pass extremely high CD -> Should fail
        success, msg = self.p1.fazer_teste_resistencia('destreza', 30) # Max 22. Always fail.
        self.assertFalse(success, "Should fail against high DC")

    def test_invalid_attribute(self):
        # Should default to +0 or error?
        # defaults to +0. If DC is 10 and roll is 14, it succeeds.
        # We can't guarantee failure unless DC is 21+.
        success, msg = self.p1.fazer_teste_resistencia('batata', 30)
        self.assertFalse(success, "Should fail against high DC even with +0 mod")
        
        # Verify it logs/uses 0 mod
        # (Implicitly verified by the fact that it runs without error)

if __name__ == '__main__':
    unittest.main()
