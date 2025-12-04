import pygame
import time
import os

def test_file(filename):
    file_path = f'assets/sounds/{filename}'
    print(f"\nTesting music file: {file_path}")
    if not os.path.exists(file_path):
        print("ERROR: File not found!")
        return

    try:
        pygame.mixer.music.load(file_path)
        print("Music loaded successfully.")
        
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        print("Music playing... (Waiting 3 seconds)")
        
        start = time.time()
        while time.time() - start < 3:
            if not pygame.mixer.music.get_busy():
                print("Music stopped unexpectedly!")
                break
            time.sleep(0.1)
        
        pygame.mixer.music.stop()
        print("Test finished for this file.")
        
    except pygame.error as e:
        print(f"Pygame Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")

def main():
    pygame.init()
    pygame.mixer.init()
    
    files = ['menu.wav', 'battle1.wav']
    for f in files:
        test_file(f)
        time.sleep(1)

    pygame.quit()

if __name__ == "__main__":
    main()
