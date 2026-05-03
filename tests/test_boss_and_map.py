import unittest
from src.motor_combate import MotorCombate
from src.tabuleiro import TERRENO_NORMAL, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_FLORESTA, TERRENO_GELO
from src.personagens.rei_goblin import ReiGoblin
from src.personagens.lorde_lich import LordeLich
from src.personagens.dragao_anciao import DragaoAnciao

class TestBossAndMap(unittest.TestCase):
    def setUp(self):
        # Create a custom map (20x20)
        # Fill with normal terrain
        self.custom_map = [[TERRENO_NORMAL for _ in range(20)] for _ in range(20)]
        # Add a wall in the middle
        for i in range(5, 15):
            self.custom_map[10][i] = TERRENO_PAREDE
        # Add some difficult terrain
        self.custom_map[5][5] = TERRENO_DIFICIL
        
        # Hero team args (1 of each hero class)
        # Classes: Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold
        self.hero_args = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        # Team B args are ignored in boss mode usually, but let's pass empty
        self.enemy_args = [0] * 12
        self.args = self.hero_args + self.enemy_args

    def test_rei_goblin_battle(self):
        print("\nTesting Rei Goblin Battle...")
        stats_chefe = {'hp': 100, 'ataque': 5, 'defesa': 12} # Simplified stats
        motor = MotorCombate(
            self.args, 
            mapa_custom=self.custom_map, 
            modo_chefe=True, 
            stats_chefe=stats_chefe, 
            boss_class=ReiGoblin
        )
        
        # Verify map loaded
        self.assertEqual(motor.tabuleiro.terrain_grid[10][10], TERRENO_PAREDE)
        self.assertEqual(motor.tabuleiro.terrain_grid[5][5], TERRENO_DIFICIL)
        
        # Verify Boss exists
        boss = next((p for p in motor.time_b if isinstance(p, ReiGoblin)), None)
        self.assertIsNotNone(boss)
        self.assertEqual(boss.nome, "ReiGoblin")
        
        # Run a few turns
        for _ in range(50):
            motor.proximo_passo()
            if motor.vencedor:
                break
        print("Rei Goblin Battle Test Passed.")

    def test_lorde_lich_battle(self):
        print("\nTesting Lorde Lich Battle...")
        stats_chefe = {'hp': 150, 'ataque': 8, 'defesa': 15}
        motor = MotorCombate(
            self.args, 
            mapa_custom=self.custom_map, 
            modo_chefe=True, 
            stats_chefe=stats_chefe, 
            boss_class=LordeLich
        )
        
        boss = next((p for p in motor.time_b if isinstance(p, LordeLich)), None)
        self.assertIsNotNone(boss)
        
        for _ in range(50):
            motor.proximo_passo()
            if motor.vencedor:
                break
        print("Lorde Lich Battle Test Passed.")

    def test_dragao_anciao_battle(self):
        print("\nTesting Dragao Anciao Battle...")
        stats_chefe = {'hp': 300, 'ataque': 12, 'defesa': 18}
        motor = MotorCombate(
            self.args, 
            mapa_custom=self.custom_map, 
            modo_chefe=True, 
            stats_chefe=stats_chefe, 
            boss_class=DragaoAnciao
        )
        
        boss = next((p for p in motor.time_b if isinstance(p, DragaoAnciao)), None)
        self.assertIsNotNone(boss)
        
        for _ in range(50):
            motor.proximo_passo()
            if motor.vencedor:
                break
        print("Dragao Anciao Battle Test Passed.")

    def test_monster_mash(self):
        print("\nTesting Monster Mash (All Minions)...")
        # Team A: 1 of each hero (Indices 0-8)
        # Team B: 3 Goblins, 3 Skeletons, 3 Kobolds (Indices 9-11 in the second set of 12)
        
        # First 12 args for Team A
        args_a = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        # Next 12 args for Team B
        args_b = [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3]
        
        args = args_a + args_b
        
        motor = MotorCombate(
            args, 
            mapa_custom=self.custom_map
        )
        
        # Verify Minions exist
        goblins = [p for p in motor.time_b if p.nome.startswith("Goblin")]
        skeletons = [p for p in motor.time_b if p.nome.startswith("Esqueleto")]
        kobolds = [p for p in motor.time_b if p.nome.startswith("Kobold")]
        
        self.assertEqual(len(goblins), 3)
        self.assertEqual(len(skeletons), 3)
        self.assertEqual(len(kobolds), 3)
        
        for _ in range(50):
            motor.proximo_passo()
            if motor.vencedor:
                break
        print("Monster Mash Test Passed.")

if __name__ == '__main__':
    unittest.main()
