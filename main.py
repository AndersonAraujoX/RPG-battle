import os
import shutil

# Diretório de artefatos e assets do jogo
ARTIFACTS_DIR = "/home/anderson/.gemini/antigravity-ide/brain/f161e1e2-4ae6-445e-a53d-082d3d4f7f60"
ENV_DIR = "assets/images/environment"

# Prefixos dos arquivos de imagem gerados para o nome do asset correspondente
PREFIXOS_IMAGENS = {
    "terreno_normal":    "terreno_normal.png",
    "terreno_floresta":  "terreno_floresta.png",
    "terreno_dificil":   "terreno_dificil.png",
    "terreno_parede":    "terreno_parede.png",
    "terreno_fogo":      "terreno_fogo.png",
    "terreno_rocha":     "terreno_rocha.png",
    "terreno_barril":    "terreno_barril.png",
    "terreno_campo":     "terreno_campo.png",
    "terreno_corredor":  "terreno_corredor.png",
    "terreno_exterior":  "terreno_exterior.png",
    "terreno_muralha_lo":"terreno_muralha_lo.png",
    "terreno_subsolo":   "terreno_subsolo.png",
}

if os.path.exists(ARTIFACTS_DIR):
    for filename in os.listdir(ARTIFACTS_DIR):
        for prefix, dest_name in PREFIXOS_IMAGENS.items():
            if filename.startswith(prefix) and filename.endswith(".png"):
                src_path = os.path.join(ARTIFACTS_DIR, filename)
                dest_path = os.path.join(ENV_DIR, dest_name)
                try:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    # Só sobrescreve se o artifact for mais novo que o destino
                    if os.path.exists(dest_path):
                        src_mtime = os.path.getmtime(src_path)
                        dst_mtime = os.path.getmtime(dest_path)
                        if src_mtime <= dst_mtime:
                            continue
                    shutil.copy2(src_path, dest_path)
                    print(f"[Assets Manager] Copiado {filename} -> {dest_path}")
                except Exception as ex:
                    print(f"[Assets Manager] Erro ao copiar {filename}: {ex}")

from src.game import Game

if __name__ == "__main__":
    game = Game()
    game.run()
