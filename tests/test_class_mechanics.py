import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.ladino import Ladino
from src.personagens.barbaro import Barbaro
from src.personagens.clerigo import Clerigo
from src.personagens.personagem_base import Personagem

class MockTabuleiro:
    def __init__(self):
        self.largura = 10
        self.altura = 10
        self.terrain_grid = [[0 for _ in range(10)] for _ in range(10)]
        self.personagens = [[None for _ in range(10)] for _ in range(10)]
    def get_terrain_em(self, x, y): return 0
    def get_personagem_em(self, x, y): return self.personagens[y][x]
    def mover_personagem(self, p, x, y): pass

class TestClassMechanics(unittest.TestCase):
    def setUp(self):
        self.tabuleiro = MockTabuleiro()
        
    def test_ladino_sneak_attack(self):
        ladino = Ladino("Rogue", "A", 1)
        target = Personagem("Target", "B", 1)
        target.hp_atual = 20
        
        initial_energy = ladino.energia_atual
        
        # Attack
        ladino.causar_dano(target, self.tabuleiro, logger=lambda x: None)
        
        # Verify Energy consumption (Sneak Attack cost is 5)
        self.assertTrue(ladino.energia_atual < initial_energy, "Energy should be consumed for Sneak Attack")
        
    def test_barbaro_reckless_attack(self):
        barbaro = Barbaro("Barb", "A", 1)
        target = Personagem("Target", "B", 1)
        target.hp_atual = 50
        
        # Ensure cooldown is ready
        barbaro.cooldowns['ataque_descuidado'] = 0
        
        barbaro.causar_dano(target, self.tabuleiro, logger=lambda x: None)
        
        # Verify Cooldown applied
        self.assertGreater(barbaro.cooldowns['ataque_descuidado'], 0, "Reckless Attack should trigger cooldown")
        
    def test_clerigo_heal_logic(self):
        clerigo = Clerigo("Cleric", "A", 1)
        clerigo.pos_x, clerigo.pos_y = 0, 0
        
        ally = Personagem("Ally", "A", 1)
        ally.hp_max = 20
        ally.hp_atual = 5 # Injured (< 70%)
        ally.pos_x, ally.pos_y = 0, 1 # Adjacent
        
        enemy = Personagem("Enemy", "B", 1)
        enemy.pos_x, enemy.pos_y = 0, 5
        
        # Decide Action
        acao = clerigo.decidir_acao([enemy], [clerigo, ally], self.tabuleiro, [])
        
        self.assertEqual(acao['acao'], 'usar_habilidade')
        self.assertEqual(acao['habilidade'], 'canalizar_divindade')
        self.assertEqual(acao['alvo'], ally)

if __name__ == '__main__':
    unittest.main()
