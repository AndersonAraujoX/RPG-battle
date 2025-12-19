import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.personagem_base import Personagem
from src.utils import rolar_d20

# Mock classes for Combat
class MockBoard:
    def get_terrain_em(self, x, y):
        return "NORMAL"

def mock_logger(msg):
    if isinstance(msg, tuple):
        print(f"[LOG] {msg[0]}")
    else:
        print(f"[LOG] {msg}")

def test_combat_advantage():
    print("=== TESTING COMBAT ADVANTAGE ===")
    
    attacker = Personagem("Hero", "A", 1)
    attacker.pos_x, attacker.pos_y = 0, 0
    attacker.alcance = 1
    
    target = Personagem("Enemy", "B", 1)
    target.pos_x, target.pos_y = 0, 1
    target.ac_base = 10 # Low AC to ensure hit
    
    ally = Personagem("Ally", "A", 1)
    ally.pos_x, ally.pos_y = 0, 2 # Flanking position (Opposite to (0,0) relative to (0,1)?)
    # Enemy is at (0,1). Attacker (0,0) -> dy = -1. Ally (0,2) -> dy = +1. Correct.
    ally.alcance = 1
    
    board = MockBoard()
    
    print("\n--- Test: Flanking (Should Trigger Advantage) ---")
    attacker.atacar(target, [], [ally], board, logger=mock_logger)
    
    print("\nCheck the log above for 'Vantagem' or 'Flanqueando'.")

if __name__ == "__main__":
    test_combat_advantage()
