import pygame
import os
from .config import LARGURA_TELA, ALTURA_TELA, COR_TEXTO
from .utils import resource_path

class CutsceneManager:
    def __init__(self, callback_fim):
        self.callback_fim = callback_fim
        self.slides = []
        self.slide_atual = 0
        self.tempo_slide_atual = 0
        self.ativo = False
        self.alpha = 0
        self.fade_state = "IN" # IN, DISPLAY, OUT
        self.fade_speed = 5
        self.fonte = pygame.font.Font(None, 48)
        self.musica_intro = None

        # Carregar imagens
        try:
            self.imagens = {
                "world": pygame.image.load(resource_path("assets/images/ui/intro_world.png")).convert(),
                "destruction": pygame.image.load(resource_path("assets/images/ui/intro_destruction.png")).convert(),
                "villains": pygame.image.load(resource_path("assets/images/ui/intro_villains.png")).convert(),
                "gathering": pygame.image.load(resource_path("assets/images/ui/intro_gathering.png")).convert(),
                "heroes": pygame.image.load(resource_path("assets/images/ui/intro_heroes.png")).convert()
            }
            # Resize images to fit screen if needed
            for k, img in self.imagens.items():
                self.imagens[k] = pygame.transform.scale(img, (LARGURA_TELA, ALTURA_TELA))
                
        except Exception as e:
            print(f"Erro ao carregar imagens da cutscene: {e}")
            self.imagens = {}

        # Duração total ~17s (1020 frames)
        # Dividindo texto épico em 5 slides
        # Slide 1: World
        # Slide 2: Destruction (The Fall)
        # Slide 3: Villains (The Awakening)
        # Slide 4: Gathering (The Call)
        # Slide 5: Heroes (The Journey)
        
        self.slides = [
            {
                "imagem": "world",
                "texto": "Em uma era antiga, onde lendas floresciam...",
                "duracao": 180 # 3s
            },
            {
                "imagem": "destruction",
                "texto": "...e se perdiam nas cinzas da guerra.",
                "duracao": 180 # 3s
            },
            {
                "imagem": "villains",
                "texto": "Um mal ancestral despertou, e as sombras da ruína se ergueram.",
                "duracao": 220 # ~3.6s
            },
            {
                "imagem": "gathering",
                "texto": "Mas a esperança persiste. Bravos heróis se reuniram.",
                "duracao": 200 # ~3.3s
            },
            {
                "imagem": "heroes",
                "texto": "Levantando-se para desafiar o destino e enfrentar o vazio eterno.",
                "duracao": 240 # ~4s
            }
        ]

    def iniciar(self):
        self.slide_atual = 0
        self.tempo_slide_atual = 0
        self.fade_state = "IN"
        self.alpha = 0
        self.ativo = True
        
        try:
            # Tocar intro.wav
            caminho_audio = resource_path("assets/sounds/intro.wav")
            if os.path.exists(caminho_audio):
                 pygame.mixer.music.load(caminho_audio)
                 pygame.mixer.music.play()
            else:
                 print("Audio intro.wav nao encontrado")
        except Exception as e:
            print(f"Erro ao tocar audio cutscene: {e}")

    def update(self):
        if not self.ativo:
            return

        if self.fade_state == "IN":
            self.alpha += self.fade_speed
            if self.alpha >= 255:
                self.alpha = 255
                self.fade_state = "DISPLAY"
        
        elif self.fade_state == "DISPLAY":
            self.tempo_slide_atual += 1
            if self.tempo_slide_atual >= self.slides[self.slide_atual]["duracao"]:
                self.fade_state = "OUT"
        
        elif self.fade_state == "OUT":
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.alpha = 0
                self.avancar_slide()

    def avancar_slide(self):
        self.slide_atual += 1
        self.tempo_slide_atual = 0
        self.fade_state = "IN"
        
        if self.slide_atual >= len(self.slides):
            self.finalizar()

    def finalizar(self):
        self.ativo = False
        if self.callback_fim:
            self.callback_fim()

    def pular(self):
        self.finalizar()

    def desenhar(self, tela):
        if not self.ativo or self.slide_atual >= len(self.slides):
            return

        slide = self.slides[self.slide_atual]
        img_key = slide["imagem"]
        
        if img_key in self.imagens:
            image = self.imagens[img_key]
            image.set_alpha(self.alpha)
            tela.blit(image, (0, 0))
        else:
            tela.fill((0, 0, 0))

        # Texto Principal com quebra de linha
        self.desenhar_texto_centralizado(tela, slide["texto"], ALTURA_TELA - 150)

    def desenhar_texto_centralizado(self, tela, texto, y_pos):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = []
        
        # Simples word wrap
        largura_maxima = LARGURA_TELA - 100
        
        for palavra in palavras:
            linha_teste = ' '.join(linha_atual + [palavra])
            if self.fonte.size(linha_teste)[0] < largura_maxima:
                linha_atual.append(palavra)
            else:
                linhas.append(' '.join(linha_atual))
                linha_atual = [palavra]
        linhas.append(' '.join(linha_atual))
        
        alt_linha = self.fonte.get_height()
        for i, linha in enumerate(linhas):
            # Sombra
            txt_sombra = self.fonte.render(linha, True, (0, 0, 0))
            txt_sombra.set_alpha(self.alpha)
            rect_sombra = txt_sombra.get_rect(center=(LARGURA_TELA // 2 + 2, y_pos + i * alt_linha + 2))
            tela.blit(txt_sombra, rect_sombra)
            
            # Texto
            txt = self.fonte.render(linha, True, (255, 255, 255))
            txt.set_alpha(self.alpha)
            rect = txt.get_rect(center=(LARGURA_TELA // 2, y_pos + i * alt_linha))
            tela.blit(txt, rect)
        
        # Indicador de Skip
        fonte_skip = pygame.font.Font(None, 24)
        txt_skip = fonte_skip.render("Pressione qualquer tecla para pular", True, (150, 150, 150))
        txt_skip.set_alpha(self.alpha) # Fade junto
        tela.blit(txt_skip, (LARGURA_TELA - 300, ALTURA_TELA - 30))
