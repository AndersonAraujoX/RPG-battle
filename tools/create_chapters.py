import os
import json
import random

BASE_DIR = "dados/capitulos"
os.makedirs(BASE_DIR, exist_ok=True)

# Map templates (just using chapter 1's map as base and varying slightly would be ideal, 
# but for now we copy it or use a default)
DEFAULT_MAP = [
    ["FLORESTA" if random.random() < 0.3 else "NORMAL" for _ in range(20)]
    for _ in range(20)
]

def create_chapter(chapter_num):
    folder_name = f"capitulo_{chapter_num:02d}"
    folder_path = os.path.join(BASE_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Info
    info_data = {
        "id": f"cap_{chapter_num:02d}",
        "titulo": f"Capítulo {chapter_num}: O Desafio",
        "descricao": f"Os heróis avançam para a fase {chapter_num}.",
        "ordem": chapter_num
    }
    with open(os.path.join(folder_path, "info.json"), 'w', encoding='utf-8') as f:
        json.dump(info_data, f, indent=4, ensure_ascii=False)
        
    # Battle
    # Simple progression logic
    num_goblins = 1 + int(chapter_num * 0.5)
    num_orcs = int(chapter_num * 0.3)
    
    enemies = []
    # Goblins
    for i in range(num_goblins):
        enemies.append({
            "tipo": "Goblin", 
            "qtd": 1, 
            "pos": [[random.randint(10, 18), random.randint(5, 15)]]
        })
    # Orcs/Rei if later
    if chapter_num % 3 == 0:
         enemies.append({
            "tipo": "ReiGoblin", 
            "qtd": 1, 
            "pos": [[15, 10]]
        })
    
    battle_data = {
        "inimigos": enemies,
        "itens": []
    }
    with open(os.path.join(folder_path, "batalha.json"), 'w', encoding='utf-8') as f:
        json.dump(battle_data, f, indent=4, ensure_ascii=False)

    # Dialogue
    dialogue_data = {
        "inicio": [
            {"nome": "Narrador", "texto": f"Capítulo {chapter_num} inicia.", "retrato": None}
        ],
        "fim": [
             {"nome": "Narrador", "texto": f"Vitória no Capítulo {chapter_num}!", "retrato": None}
        ]
    }
    with open(os.path.join(folder_path, "dialogo.json"), 'w', encoding='utf-8') as f:
        json.dump(dialogue_data, f, indent=4, ensure_ascii=False)

    # Map
    # Generate a slightly random map for variety
    map_data = [
        ["FLORESTA" if random.random() < 0.1 * (chapter_num % 5) else "NORMAL" for _ in range(20)]
        for _ in range(20)
    ]
    with open(os.path.join(folder_path, "mapa.json"), 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=4)

    print(f"Created {folder_name}")

if __name__ == "__main__":
    # Create chapters 2 to 12
    for i in range(2, 13):
        create_chapter(i)
