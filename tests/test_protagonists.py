import unittest
from src.motor_combate import MotorCombate
from src.personagens.protagonistas import Novak, Koema, Rilem, Yukito
from src.personagens.personagem_base import Personagem
from src.tabuleiro import Tabuleiro

class TestProtagonists(unittest.TestCase):
    def setUp(self):
        self.tabuleiro = Tabuleiro(20, 20)
        self.novak = Novak("Novak", "A", 5)
        self.koema = Koema("Koema", "A", 5)
        self.rilem = Rilem("Rilem", "A", 5)
        self.yukito = Yukito("Yukito", "A", 5)
        self.inimigo = Personagem("Inimigo", "B", 5)
        
        self.novak.pos_x, self.novak.pos_y = 5, 5
        self.inimigo.pos_x, self.inimigo.pos_y = 6, 5 # Adjacent
        
        self.novak.pos_x, self.novak.pos_y = 5, 5
        self.inimigo.pos_x, self.inimigo.pos_y = 6, 5 # Adjacent
        
        # Instantiate with dummy args
        self.motor = MotorCombate([0]*20) 
        self.motor.time_a = [self.novak, self.koema, self.rilem, self.yukito]
        self.motor.time_b = [self.inimigo]
        self.motor.tabuleiro = self.tabuleiro
        
        # Add to board
        self.tabuleiro.adicionar_personagem(self.novak, 5, 5)
        self.tabuleiro.adicionar_personagem(self.inimigo, 6, 5)

    def test_novak_skills(self):
        # Provocar
        self.assertIn('provocar', self.novak.habilidades)
        acao = {'acao': 'usar_habilidade', 'habilidade': 'provocar', 'alvo': None} # Area self centered usually or UI defined
        # Motor logic for provocar doesn't use target, uses self position
        self.motor._executar_acao(self.novak, acao, [self.inimigo], [self.novak], [])
        
        # Check Provoked status
        has_provoked = any(e.nome == "Provocado" for e in self.inimigo.status_efeitos)
        self.assertTrue(has_provoked, "Inimigo should be Provoked")
        
        # ...
        
    def test_rilem_skills(self):
         acao = {'acao': 'usar_habilidade', 'habilidade': 'comando_tatico', 'alvo': 'todos_aliados'}
         self.rilem.energia_atual = 40
         self.motor._executar_acao(self.rilem, acao, [self.inimigo], [self.rilem, self.novak], [])
         
         # Check Buff
         has_buff = any(e.nome == "Comando Tatico" for e in self.rilem.status_efeitos)
         self.assertTrue(has_buff, "Rilem should have Comando Tatico")

    def test_yukito_skills(self):
        # Explosao Arcana
        acao = {'acao': 'usar_habilidade', 'habilidade': 'explosao_arcana', 'alvo': self.inimigo}
        hp_before = self.inimigo.hp_atual
        self.motor._executar_acao(self.yukito, acao, [self.inimigo], [self.yukito], [])
        # Damage 15, HP capped at 0
        expected_hp = max(0, hp_before - 15)
        self.assertEqual(self.inimigo.hp_atual, expected_hp, "Explosao Arcana should deal damage")

if __name__ == '__main__':
    unittest.main()
