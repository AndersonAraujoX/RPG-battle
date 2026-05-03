import unittest
import os
import pickle
from src.motor_combate import MotorCombate
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago
from src.personagens.minions import Goblin

class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.filename = "test_savegame.pkl"
        # Setup a simple battle state
        # args_times needs to be a list of integers for BOTH teams.
        # First 12 are for Team A, next 12 are for Team B (if logic supports it, let's check _setup_times)
        # _setup_times logic:
        # for i, classe in enumerate(classes):
        #     if len(args) > i + len(classes):
        #         personagens_para_criar_b.extend([classe] * args[i+len(classes)])
        
        # So we need 24 integers.
        args = [0] * 24
        args[0] = 1 # Team A: 1 Guerreiro (index 0)
        args[12 + 9] = 1 # Team B: 1 Goblin (index 9 + 12 offset)
        
        self.motor = MotorCombate(args)
        # self.motor.iniciar_combate(self.time_a, self.time_b) # This method doesn't exist in MotorCombate, it's done in __init__
        
        # Advance state slightly
        self.motor.proximo_passo() 
        self.motor.proximo_passo()

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_save_and_load(self):
        # Save
        self.motor.salvar_jogo(self.filename)
        self.assertTrue(os.path.exists(self.filename))

        # Create new engine and load
        # We need to pass valid args to init, even if we are going to overwrite state with load
        args = [0] * 24
        args[0] = 1
        args[12 + 9] = 1
        new_motor = MotorCombate(args)
        new_motor.carregar_jogo(self.filename)

        # Verify state
        self.assertEqual(len(new_motor.time_a), len(self.motor.time_a))
        self.assertEqual(len(new_motor.time_b), len(self.motor.time_b))
        self.assertEqual(new_motor.turno, self.motor.turno)
        
        # Verify deep state (attributes)
        p1_original = self.motor.time_a[0]
        p1_loaded = new_motor.time_a[0]
        self.assertEqual(p1_original.nome, p1_loaded.nome)
        self.assertEqual(p1_original.hp_atual, p1_loaded.hp_atual)
        self.assertEqual(p1_original.pos_x, p1_loaded.pos_x)
        self.assertEqual(p1_original.pos_y, p1_loaded.pos_y)

if __name__ == '__main__':
    unittest.main()
