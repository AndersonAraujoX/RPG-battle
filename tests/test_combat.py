import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.motor_combate import MotorCombate
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago
from src.personagens.ladino import Ladino
from src.personagens.clerigo import Clerigo
from src.personagens.minions import Goblin, Esqueleto
from src.config import TIME_A, TIME_B

def dummy_sound_player(sound_name):
    pass

def run_test_battle():
    print("Iniciando teste de batalha automatizado...")
    
    # Setup Teams (Counts for each class)
    # Classes order: Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold
    # Team A: 1 of each hero class
    time_a_counts = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0] 
    # Team B: A mix of enemies including bosses (Bosses are handled separately in MotorCombate usually, but here we pass them as normal args if we want them in the list, 
    # BUT MotorCombate logic for 'args' only maps to the standard classes list.
    # To test bosses, we might need to instantiate them manually or check how MotorCombate handles them.
    # MotorCombate _setup_times uses the 'classes' list which is:
    # [Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold]
    # So we can't easily add bosses via 'args' list without modifying MotorCombate or the test setup.
    # Let's stick to the standard classes first, then maybe add a separate test for bosses.
    
    # Team B: 1 of each minion type + extras to balance
    time_b_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3]
    
    args = time_a_counts + time_b_counts
    
    # Initialize Engine
    try:
        motor = MotorCombate(args, gerar_terreno=True, sound_player=dummy_sound_player)
        print("Motor de combate inicializado com sucesso.")
    except Exception as e:
        print(f"ERRO FATAL na inicialização: {e}")
        return

    turnos = 0
    max_turnos = 100
    
    while not motor.vencedor and turnos < max_turnos:
        turnos += 1
        try:
            # Simulate a step
            resultado = motor.proximo_passo()
            
            # Print logs for debugging
            for log in resultado['logs']:
                print(log[0])

            
        except Exception as e:
            print(f"ERRO durante o turno {turnos}: {e}")
            import traceback
            traceback.print_exc()
            break
            
    if motor.vencedor:
        print(f"Batalha terminou em {turnos} turnos. Vencedor: {motor.vencedor}")
    else:
        print(f"Batalha atingiu o limite de {max_turnos} turnos sem vencedor.")

if __name__ == "__main__":
    run_test_battle()
