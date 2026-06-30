import pygame
pygame.init()
try:
    img = pygame.image.load("assets/images/environment/card/pixelCardAssest.png")
    w, h = img.get_size()
    with open("test_result.txt", "w") as f:
        f.write(f"DIMS: {w}x{h}\n")
except Exception as e:
    with open("test_result.txt", "w") as f:
        f.write(f"ERR: {e}\n")
