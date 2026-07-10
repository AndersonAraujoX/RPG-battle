import os
import shutil
import pygame

def main():
    src_sheet = "/home/anderson/.gemini/antigravity-ide/brain/b2341e26-922c-497c-9fd1-36f1c570cc7f/isectum_spritesheet_1783642920213.png"
    dest_dir = "assets/images/characters/monsters"
    isectum_dir = os.path.join(dest_dir, "isectum")
    
    # Cria os diretórios necessários
    if not os.path.exists(isectum_dir):
        os.makedirs(isectum_dir)
        print(f"Diretório criado: {isectum_dir}")
        
    # Copia o spritesheet para o projeto
    sheet_dest_path = os.path.join(dest_dir, "isectum_spritesheet.png")
    try:
        shutil.copy(src_sheet, sheet_dest_path)
        print(f"Spritesheet copiado para: {sheet_dest_path}")
    except Exception as e:
        print(f"Erro ao copiar spritesheet: {e}")
        return
        
    # Carrega a imagem sem inicializar o pygame (modo headless puro)
    spritesheet = pygame.image.load(sheet_dest_path)
    w_in, h_in = spritesheet.get_size()
    
    cols = 6
    rows = 5
    cell_w = w_in // cols
    cell_h = h_in // rows
    
    mapping = {
        "vespa_cacadora":        (0, 0),
        "abelha_tecela":         (1, 0),
        "formiga_correicao":     (2, 0),
        "libelula_blindada":     (3, 0),
        "louva_deus":            (4, 0),
        "viuva_canibal":         (5, 0),
        
        "besouro_rinoceronte":   (0, 1),
        "vagalume_sombras":      (1, 1),
        "aranha_clepto":         (2, 1),
        "mariposa_esfinge":      (3, 1),
        "besouro_unicornio":     (4, 1),
        "infiltrador":           (5, 1),
        
        "centopeia_olhos":       (0, 2),
        "besouro_gorgulho":      (1, 2),
        "efemera_mimetica":      (2, 2),
        "cigarra_ressonante":    (3, 2),
        "larva_carniceira":      (4, 2),
        "viuva_negra":           (5, 2),
        
        "mosca_tse_tse":         (0, 3),
        "gafanhoto_praga":       (2, 3),
        "escaravelho_necrofago":  (3, 3),
        "vespa_joia":            (4, 3),
        "enxame_rainha":         (5, 3),
        
        "brutamonte":            (4, 4),
        "carrapato_vampiro":      (3, 4),
    }
    
    for name, (col, row) in mapping.items():
        # Fatia
        rect = pygame.Rect(col * cell_w, row * cell_h, cell_w, cell_h)
        sub = spritesheet.subsurface(rect)
        
        # Cria uma nova superfície com canal alpha
        cell_surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
        cell_surf.blit(sub, (0, 0))
        
        # Remove o fundo branco (quase branco)
        for y in range(cell_h):
            for x in range(cell_w):
                color = cell_surf.get_at((x, y))
                # Se for muito próximo do branco
                if color.r > 240 and color.g > 240 and color.b > 240:
                    cell_surf.set_at((x, y), (0, 0, 0, 0))
                    
        # Redimensiona para 32x32
        scaled = pygame.transform.scale(cell_surf, (32, 32))
        
        # Salva o arquivo individual
        out_file = os.path.join(isectum_dir, f"{name}.png")
        pygame.image.save(scaled, out_file)
        print(f"Salvo: {out_file}")
        
    print("Processamento concluído com sucesso!")

if __name__ == "__main__":
    main()
