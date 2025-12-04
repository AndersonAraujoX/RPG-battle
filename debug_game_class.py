from src.game import Game
import inspect

print("Inspecting Game class...")
if hasattr(Game, 'tocar_musica'):
    print("Method 'tocar_musica' FOUND in Game class.")
else:
    print("Method 'tocar_musica' NOT FOUND in Game class.")

print("\nMethods in Game:")
for name, method in inspect.getmembers(Game, predicate=inspect.isfunction):
    print(f"- {name}")
