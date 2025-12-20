import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.personagem_base import Personagem
from src.itens.armas_comuns import Adaga, EspadaLonga
from src.itens.armaduras_comuns import CouracaDeCouro, CotaDeMalha
from src.itens.item import HealthPotion

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.p1 = Personagem("Hero", "A", 1)
        # Reset stats
        self.p1._forca = 10
        self.p1._destreza = 10
        self.p1._constituicao = 10
        self.p1.ac_base = 10
        
    def test_equip_weapon(self):
        adaga = Adaga() # 1d4, Finesse
        self.p1.equipar_arma(adaga)
        self.assertEqual(self.p1.arma_equipada, adaga)
        self.assertEqual(self.p1.dado_dano, (1, 4))
        
        espada = EspadaLonga() # 1d8
        self.p1.equipar_arma(espada)
        self.assertEqual(self.p1.arma_equipada, espada)
        self.assertEqual(self.p1.dado_dano, (1, 8))
        
    def test_equip_armor(self):
        # Base AC is 10 + Dex(0) = 10
        self.assertEqual(self.p1.ac, 10)
        
        couro = CouracaDeCouro() # 11 + Dex
        self.p1.equipar_armadura(couro)
        self.assertEqual(self.p1.armadura_equipada, couro)
        self.assertEqual(self.p1.ac, 12)
        
        # Increase Dex -> +1
        self.p1._destreza = 12
        # CouracaDeCouro usually allows Full Dex or Max 2? 
        # Code usually implements AC property on armor + Personagem logic.
        # Personagem.ac property: if armadura_equipada: return armadura.bonus_ac.
        # Wait, if armadura.bonus_ac is STATIC, then Dex isn't added by character unless Armor logic does it?
        # Let's assume standard behavior: AC calculation usually in Personagem logic OR Armor object returns calculated AC.
        # Actually in `personagem_base.py`:
        # def ac(self): if self.armadura_equipada: return self.armadura_equipada.bonus_ac.
        # So if Armor.bonus_ac is static, Dex is ignored? That would be a bug/simplification.
        # Let's checking test result.
        
    def test_use_potion(self):
        self.p1.hp_max = 20
        self.p1.hp_atual = 10
        potion = HealthPotion()
        self.p1.inventario.append(potion)
        
        potion.usar(self.p1, logger=lambda x: None)
        
        self.assertTrue(self.p1.hp_atual > 10, "Potion should heal")
        self.assertTrue(self.p1.hp_atual <= 20, "Should not overhead")

if __name__ == '__main__':
    unittest.main()
