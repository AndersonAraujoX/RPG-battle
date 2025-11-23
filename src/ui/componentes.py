import pygame
from ..config import COR_BOTAO, COR_BOTAO_HOVER, COR_BOTAO_DESABILITADO, COR_TEXTO

class Botao:
    def __init__(self, x, y, largura, altura, texto, fonte):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.texto = texto
        self.fonte = fonte
        self.cor_base = COR_BOTAO
        self.cor_hover = COR_BOTAO_HOVER
        self.cor_desabilitado = COR_BOTAO_DESABILITADO
        self.cor_atual = self.cor_base
        self.desabilitado = False

    def desenhar(self, tela, fonte):
        cor = self.cor_desabilitado if self.desabilitado else self.cor_atual
        pygame.draw.rect(tela, cor, self.rect, border_radius=5)
        texto_render = fonte.render(self.texto, True, COR_TEXTO)
        texto_rect = texto_render.get_rect(center=self.rect.center)
        tela.blit(texto_render, texto_rect)

    def checar_clique(self, pos):
        if not self.desabilitado and self.rect.collidepoint(pos):
            return True
        return False

    def update_hover(self, pos):
        if not self.desabilitado:
            self.cor_atual = self.cor_hover if self.rect.collidepoint(pos) else self.cor_base

class Checkbox:
    def __init__(self, x, y, tamanho, texto, fonte):
        self.rect = pygame.Rect(x, y, tamanho, tamanho)
        self.texto = texto
        self.fonte = fonte
        self.checked = False
        self.texto_render = self.fonte.render(self.texto, True, COR_TEXTO)
        self.texto_rect = self.texto_render.get_rect(left=self.rect.right + 10, centery=self.rect.centery)

    def desenhar(self, tela):
        pygame.draw.rect(tela, COR_TEXTO, self.rect, 2, border_radius=3)
        if self.checked:
            pygame.draw.line(tela, COR_TEXTO, (self.rect.left + 3, self.rect.centery), (self.rect.centerx - 2, self.rect.bottom - 3), 3)
            pygame.draw.line(tela, COR_TEXTO, (self.rect.centerx - 2, self.rect.bottom - 3), (self.rect.right - 3, self.rect.top + 3), 3)
        tela.blit(self.texto_render, self.texto_rect)

    def checar_clique(self, pos):
        if self.rect.collidepoint(pos) or self.texto_rect.collidepoint(pos):
            self.checked = not self.checked
            return True
        return False
