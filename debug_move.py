
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.motor_combate import MotorCombate
from src.personagens.protagonistas import Novak

def test_movement():
    print("Initializing MotorCombate for Movement Test...")
    
    # Create a simple 20x20 board with a single character
    hero = Novak("Hero", "A")
    hero.pos_x = 5
    hero.pos_y = 5
    # hero.velocidade is derived from dexterity, so we rely on the class default or modify destreza if needed.

    
    motor = MotorCombate(args_times=None, custom_time_a=[hero])
    

    # Force visibility update just in case
    motor.atualizar_visibilidade()
    
    print(f"Hero Position: ({hero.pos_x}, {hero.pos_y})")
    print(f"Hero Speed: {hero.velocidade}")
    
    validos = motor.get_movimento_valido(hero)
    print(f"Valid Moves: {validos}")
    
    if not validos:
        print("FAILURE: No valid moves found for hero.")
        return

    # Try to move to the first valid spot
    target_x, target_y = validos[0]
    
    print(f"Attempting to move to ({target_x}, {target_y})...")
    
    eventos, logs = motor.jogador_move_personagem(hero, target_x, target_y)
    
    print(f"Result Events: {len(eventos)}")
    for e in eventos:
        print(f"  Event: {e}")
        
    print(f"Result Logs: {logs}")

    print(f"Hero Position After: ({hero.pos_x}, {hero.pos_y})")
    
    if not eventos:
        print("FAILURE: Movement returned no events.")
        # Check pathfinding directly
        print("Checking pathfinding...")
        path = motor._astar_pathfinding((hero.pos_x, hero.pos_y), (target_x, target_y), hero.velocidade)
        print(f"Pathfinding result: {path}")
    else:
        print("SUCCESS: Movement generated events.")

if __name__ == "__main__":
    test_movement()
