import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.motor_combate import MotorCombate
from src.personagens import Guerreiro, Clerigo, Ladino, Mago
from src.tabuleiro import TERRENO_FOGO
from src.perks import PERKS

class TestPerks(unittest.TestCase):
    def setUp(self):
        # Passa lista vazia de 24 elementos (12 para cada time)
        args_dummy = [0] * 24
        self.motor = MotorCombate(args_dummy, gerar_terreno=False)
        self.novak = Guerreiro("Novak", "A")
        self.koema = Clerigo("Koema", "A")
        self.alvo = Ladino("Alvo", "B")
        
        self.motor.combatentes = [self.novak, self.koema, self.alvo]
        self.motor.time_a = [self.novak, self.koema]
        self.motor.time_b = [self.alvo]
        
        # Posicionamento
        self.novak.pos_x, self.novak.pos_y = 5, 5
        self.koema.pos_x, self.koema.pos_y = 6, 5 # Adjacente
        self.alvo.pos_x, self.alvo.pos_y = 5, 6 # Adjacente ao Novak
        
        self.motor.tabuleiro.grid[5][5] = self.novak
        self.motor.tabuleiro.grid[5][6] = self.koema
        self.motor.tabuleiro.grid[6][5] = self.alvo

    def test_lamina_incendiaria(self):
        print("\n--- Teste Lâmina Incendiária ---")
        self.novak.adquirir_perk("lamina_incendiaria")
        self.motor.jogador_ataca_personagem(self.novak, self.alvo)
        
        terreno = self.motor.tabuleiro.get_terrain_em(self.alvo.pos_x, self.alvo.pos_y)
        self.assertEqual(terreno, TERRENO_FOGO, "O terreno sob o alvo deve se tornar FOGO.")

    def test_aura_vitalidade(self):
        print("\n--- Teste Aura de Vitalidade ---")
        self.koema.adquirir_perk("aura_vitalidade")
        self.novak.hp_atual = 10 # Ferido
        
        # Simula início de turno chamando proximo_passo quando for vez de Koema
        # Precisamos forçar Koema a ser o atual
        self.motor.ordem_de_combate = [self.koema]
        self.motor.combatente_atual_idx = 0
        
        # Mocking logs
        self.koema.turn_started_log = False
        res = self.motor.proximo_passo()
        
        # Verifica se Novak foi curado
        # Mod Sab de Clerigo lvl 1 (Sab 16 -> +3). Perk cura +2. Total +5.
        self.assertTrue(self.novak.hp_atual > 10, "Novak deve ser curado pela aura.")
        print(f"HP Novak: 10 -> {self.novak.hp_atual}")

    def test_sede_sangue(self):
        print("\n--- Teste Sede de Sangue ---")
        self.novak.adquirir_perk("sede_sangue")
        self.novak.hp_atual = 5 # Ferido
        self.alvo.hp_atual = 1 # Quase morto
        
        # Novak mata Alvo
        self.alvo.receber_dano(10, self.novak, self.motor.tabuleiro)
        
        # Verifica cura em Novak
        self.assertTrue(self.novak.hp_atual > 5, "Novak deve se curar ao matar.")
        print(f"HP Novak após kill: {self.novak.hp_atual}")

if __name__ == '__main__':
    unittest.main()
