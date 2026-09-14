
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Testing Character Instantiation...")
    from src.personagens.protagonistas import Novak, Yukito, Rilem, Koema
    from src.personagens.sienna import Sienna
    
    print("Initializing Novak...")
    p1 = Novak("Novak", "A")
    print(f"Novak created. HP: {p1.hp_max}")
    
    print("Initializing Yukito...")
    p2 = Yukito("Yukito", "A")
    print(f"Yukito created. HP: {p2.hp_max}")

    print("Initializing Sienna...")
    boss = Sienna("Sienna", "B")
    print(f"Sienna created. HP: {boss.hp_max}")

    print("SUCCESS: All characters initialized correctly.")

except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
