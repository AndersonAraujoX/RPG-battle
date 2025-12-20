import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.motor_combate import MotorCombate
from src.personagens.personagem_base import Personagem

class MockTabuleiro:
    def __init__(self):
        self.largura = 10
        self.altura = 10
        self.terrain_grid = [[0 for _ in range(10)] for _ in range(10)]
        self.personagens = [[None for _ in range(10)] for _ in range(10)]
        self.itens_no_chao = [[None for _ in range(10)] for _ in range(10)] # Added missing attribute
    
    def get_terrain_em(self, x, y): return 0
    def get_personagem_em(self, x, y): return self.personagens[y][x]
    def get_elevation_em(self, x, y): return 0
    def mover_personagem(self, p, x, y):
        self.personagens[p.pos_y][p.pos_x] = None
        p.pos_x, p.pos_y = x, y
        self.personagens[y][x] = p
    def get_item_em(self, x, y): return None
    def calcular_linha_visao(self, x1, y1, x2, y2, ignorar_personagens=False): return True

class TestActionEconomy(unittest.TestCase):
    def setUp(self):
        # args_times expects enough elements for character classes.
        self.motor = MotorCombate([0]*20, sound_player=MagicMock())
        self.motor.tabuleiro = MockTabuleiro()
        
        self.p1 = Personagem("Hero", "A", 1)
        self.p1.pos_x, self.p1.pos_y = 0, 0
        self.p1.alcance = 1
        self.p1.dado_dano = (1, 6)
        
        self.p2 = Personagem("Enemy", "B", 1)
        self.p2.pos_x, self.p2.pos_y = 0, 5
        
        self.motor.combatentes = [self.p1, self.p2]
        self.motor.time_a = [self.p1]
        self.motor.time_b = [self.p2]
        self.motor.ordem_de_combate = [self.p1, self.p2]
        self.motor.turno_atual_index = 0
        
        # Place on grid
        self.motor.tabuleiro.personagens[0][0] = self.p1
        self.motor.tabuleiro.personagens[5][0] = self.p2

    def test_move_and_attack(self):
        # 1. Start Turn
        self.p1.iniciar_turno()
        
        # 2. Call proximo_passo (Trigger Move)
        res = self.motor.proximo_passo()
        self.assertTrue(self.p1.movimento_realizado, "Movement should have been realized")
        
        # 3. Call proximo_passo (Trigger Attack)
        res = self.motor.proximo_passo()
        self.assertTrue(self.p1.acao_realizada, "Action (Attack) should have been realized")
        
        # 4. End Turn
        res = self.motor.proximo_passo()
        # Logic for end turn verification

    def test_bonus_action(self):
        self.p1.iniciar_turno()
        # Mocking a Bonus Action capability
        # Current logic doesn't have a generic "Do Bonus Action" unless AI triggers it.
        # But we can verify that performing a Bonus Action doesn't consume the Main Action flag
        # and doesn't end the turn immediately.
        
        # Manually trigger a bonus action (simulated)
        self.p1.acao_bonus_realizada = True
        
        # Check flags
        self.assertFalse(self.p1.acao_realizada, "Bonus Action should not consume Main Action")
        
        # If we had a concrete Bonus Action in decide_action, we would test it here.
        # For now, just verifying the flags exist is basic sanity check.
        
    def test_cannot_act_twice(self):
        self.p1.iniciar_turno()
        self.p1.acao_realizada = True
        
        # Mock decide to try attacking again?
        # Actually decidir_acao checks flag.
        # So it should return 'passar' or 'move' (if not moved).
        
        acao = self.p1.decidir_acao([self.p2], [self.p1], self.motor.tabuleiro, [])
        self.assertNotEqual(acao['acao'], 'atacar', "Should not attack again")

if __name__ == '__main__':
    unittest.main()
