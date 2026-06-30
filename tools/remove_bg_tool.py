import os
import sys
import argparse
from PIL import Image
from image_processor import process_image

def main():
    parser = argparse.ArgumentParser(description="Remover fundo e halo de imagens para RPG Battle.")
    parser.add_argument("-i", "--input", required=True, help="Caminho do arquivo ou diretório de entrada.")
    parser.add_argument("-o", "--output", help="Caminho do arquivo ou diretório de saída.")
    parser.add_argument("-b", "--bg", choices=["auto", "white", "black"], default="auto", help="Tipo de fundo (padrão: auto).")
    parser.add_argument("-t", "--tolerance", type=int, default=30, help="Tolerância de cor (0-255, padrão: 30).")
    parser.add_argument("-e", "--erode", type=int, default=1, help="Quantidade de erosão do halo em pixels (padrão: 1).")
    parser.add_argument("-f", "--feather", type=float, default=1.0, help="Suavização das bordas em pixels (padrão: 1.0).")
    parser.add_argument("-d", "--defringe", type=int, default=3, help="Raio de defringe de cores (padrão: 3).")
    parser.add_argument("-m", "--mode", choices=["floodfill", "range"], default="floodfill", 
                        help="Modo de seleção: floodfill (preenchimento contíguo) ou range (faixa global) (padrão: floodfill).")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Erro: O caminho de entrada '{args.input}' não existe.")
        sys.exit(1)
        
    # Determine files to process
    files_to_process = []
    if os.path.isdir(args.input):
        for f in os.listdir(args.input):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                files_to_process.append((os.path.join(args.input, f), f))
        if not files_to_process:
            print(f"Nenhuma imagem encontrada no diretório '{args.input}'.")
            sys.exit(0)
    else:
        files_to_process.append((args.input, os.path.basename(args.input)))
        
    # Determine output directory/file
    out_dir = None
    if len(files_to_process) > 1 or os.path.isdir(args.input):
        # We need an output directory
        if args.output:
            out_dir = args.output
        else:
            out_dir = os.path.join(os.path.dirname(files_to_process[0][0]), "processed")
        os.makedirs(out_dir, exist_ok=True)
    else:
        # Single file
        if not args.output:
            # Save as filename_clean.png in same folder
            base, ext = os.path.splitext(files_to_process[0][0])
            args.output = f"{base}_clean.png"
            
    print(f"Iniciando processamento de {len(files_to_process)} imagem(ns)...")
    
    for in_path, filename in files_to_process:
        try:
            print(f"Processando: {filename}...")
            img = Image.open(in_path)
            processed_img, bg_color = process_image(
                img, 
                bg_type=args.bg, 
                tolerance=args.tolerance, 
                erode_pixels=args.erode, 
                feather_pixels=args.feather, 
                defringe_radius=args.defringe,
                mode=args.mode
            )
            
            if out_dir:
                # Save inside out_dir with same name
                out_path = os.path.join(out_dir, filename)
            else:
                out_path = args.output
                
            processed_img.save(out_path, "PNG")
            print(f"  Salvo em: {out_path} (Fundo detectado: {bg_color})")
        except Exception as e:
            print(f"  Erro ao processar '{filename}': {e}")
            
    print("Processamento concluído!")

if __name__ == "__main__":
    main()
