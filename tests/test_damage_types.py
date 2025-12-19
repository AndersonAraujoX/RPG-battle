import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personagens.personagem_base import Personagem
from src.config import DANO_FOGO, DANO_GELO, DANO_FISICO, DANO_CONTUNDENTE

# Mock Logger
def mock_logger(msg):
    # Handle tuple format (text, color)
    if isinstance(msg, tuple):
        print(f"[LOG] {msg[0]}")
    else:
        print(f"[LOG] {msg}")

def test_damage_mechanics():
    print("=== TESTING DAMAGE MECHANICS ===")
    
    # Create Dummy Characters
    atacante = Personagem("Test Attacker", "A",nivel=1)
    atacante.dado_dano = (1, 10) 
    
    alvo = Personagem("Test Dummy", "B", nivel=1)
    alvo.hp_atual = 100
    alvo.hp_max = 100
    
    print(f"\nCreated {alvo.nome} with {alvo.hp_atual} HP.")
    
    # 1. Normal Damage
    print("\n--- Test 1: Normal Damage (Physical) ---")
    dano = 10
    print(f"Applying {dano} {DANO_FISICO} damage...")
    taken, eff = alvo.receber_dano(dano, logger=mock_logger, tipo_dano=DANO_FISICO)
    print(f"Result: Took {taken} damage.{eff}")
    assert taken == 10
    
    # 2. Resistance (Fire)
    print("\n--- Test 2: Resistance (Fire) ---")
    alvo.resistencias.append(DANO_FOGO)
    dano = 20
    print(f"Dummy gains resistance to {DANO_FOGO}.")
    print(f"Applying {dano} {DANO_FOGO} damage...")
    taken, eff = alvo.receber_dano(dano, logger=mock_logger, tipo_dano=DANO_FOGO)
    print(f"Result: Took {taken} damage.{eff}")
    assert taken == 10 # Half of 20
    
    # 3. Vulnerability (Cold)
    print("\n--- Test 3: Vulnerability (Cold) ---")
    alvo.vulnerabilidades.append(DANO_GELO)
    dano = 15
    print(f"Dummy gains vulnerability to {DANO_GELO}.")
    print(f"Applying {dano} {DANO_GELO} damage...")
    taken, eff = alvo.receber_dano(dano, logger=mock_logger, tipo_dano=DANO_GELO)
    print(f"Result: Took {taken} damage.{eff}")
    assert taken == 30 # Double 15
    
    # 4. Immunity (Bludgeoning)
    print("\n--- Test 4: Immunity (Bludgeoning) ---")
    alvo.imunidades.append(DANO_CONTUNDENTE)
    dano = 50
    print(f"Dummy gains immunity to {DANO_CONTUNDENTE}.")
    print(f"Applying {dano} {DANO_CONTUNDENTE} damage...")
    taken, eff = alvo.receber_dano(dano, logger=mock_logger, tipo_dano=DANO_CONTUNDENTE)
    print(f"Result: Took {taken} damage.{eff}")
    assert taken == 0
    
    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    test_damage_mechanics()
