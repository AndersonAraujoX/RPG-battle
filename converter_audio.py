import os
import sys
from pydub import AudioSegment

def converter_mp3_para_wav(diretorio):
    """
    Converte todos os arquivos .mp3 em um diretório para o formato .wav.
    """
    if not os.path.isdir(diretorio):
        print(f"Erro: O diretório '{diretorio}' não foi encontrado.")
        return

    print(f"Procurando por arquivos .mp3 em '{diretorio}'...")

    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".mp3"):
            caminho_mp3 = os.path.join(diretorio, nome_arquivo)
            nome_sem_ext = os.path.splitext(nome_arquivo)[0]
            caminho_wav = os.path.join(diretorio, f"{nome_sem_ext}.wav")
            
            print(f"Convertendo '{caminho_mp3}' para '{caminho_wav}'...")
            
            try:
                # Carrega o arquivo mp3
                audio = AudioSegment.from_mp3(caminho_mp3)
                # Exporta como wav
                audio.export(caminho_wav, format="wav")
                print("  Conversão concluída.")
            except Exception as e:
                print(f"  Falha ao converter '{nome_arquivo}'. Erro: {e}")
                print("  Certifique-se de que o ffmpeg está instalado e acessível no PATH do seu sistema.")
                print("  (No Ubuntu/Debian: sudo apt-get install ffmpeg)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 converter_audio.py <caminho_do_diretorio>")
        sys.exit(1)
        
    diretorio_alvo = sys.argv[1]
    converter_mp3_para_wav(diretorio_alvo)
