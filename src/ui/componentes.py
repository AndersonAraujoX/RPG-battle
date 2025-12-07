import pygame
from ..config import COR_BOTAO, COR_BOTAO_HOVER, COR_BOTAO_DESABILITADO, COR_TEXTO

class Botao:
    def __init__(self, x, y, largura, altura, texto, fonte, subtitulo="", icone=None, cor_fundo=COR_BOTAO):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.texto = texto
        self.subtitulo = subtitulo
        self.icone = icone # Pode ser uma string de caminho ou uma Surface
        self.fonte = fonte
        self.fonte_sub = pygame.font.Font(None, 20) # Fonte menor para subtítulo
        self.cor_base = cor_fundo
        self.cor_hover = COR_BOTAO_HOVER
        if cor_fundo == COR_BOTAO: # Se for a cor padrão antiga, usa a nova se disponível ou mantém
             # Lógica para compatibilidade: se for botão de menu principal, usa cores novas
             pass
        
        self.cor_desabilitado = COR_BOTAO_DESABILITADO
        self.cor_atual = self.cor_base
        self.desabilitado = False
        self.is_menu_button = bool(subtitulo) # Flag para renderização diferenciada

    def desenhar(self, tela, fonte, mouse_pos=None):
        if mouse_pos:
            self.update_hover(mouse_pos)
            
        cor = self.cor_desabilitado if self.desabilitado else self.cor_atual
        
        if self.is_menu_button:
            # Renderização estilo "Dark Fantasy" (Final de Kindread Soul)
            
            # Fundo com gradiente simulado (apenas um fill por enquanto)
            # Cor base escura, hover um pouco mais claro
            cor_fundo = (40, 40, 40) if not self.rect.collidepoint(pygame.mouse.get_pos()) else (60, 60, 60)
            pygame.draw.rect(tela, cor_fundo, self.rect, border_radius=2)
            
            # Borda Metálica/Dourada
            cor_borda = (100, 100, 100) # Aço escuro
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                cor_borda = (218, 165, 32) # Dourado no hover
            
            pygame.draw.rect(tela, cor_borda, self.rect, 2, border_radius=2)
            
            # Detalhe decorativo nos cantos (opcional, mas adiciona "flavor")
            tamanho_canto = 10
            pygame.draw.lines(tela, cor_borda, False, [(self.rect.x, self.rect.y + tamanho_canto), (self.rect.x, self.rect.y), (self.rect.x + tamanho_canto, self.rect.y)], 2)
            pygame.draw.lines(tela, cor_borda, False, [(self.rect.right - tamanho_canto, self.rect.y), (self.rect.right, self.rect.y), (self.rect.right, self.rect.y + tamanho_canto)], 2)
            pygame.draw.lines(tela, cor_borda, False, [(self.rect.x, self.rect.bottom - tamanho_canto), (self.rect.x, self.rect.bottom), (self.rect.x + tamanho_canto, self.rect.bottom)], 2)
            pygame.draw.lines(tela, cor_borda, False, [(self.rect.right - tamanho_canto, self.rect.bottom), (self.rect.right, self.rect.bottom), (self.rect.right, self.rect.bottom - tamanho_canto)], 2)

            # Ícone (Placeholder ou Imagem)
            if self.icone:
                # Placeholder: Losango ou círculo
                icone_rect = pygame.Rect(self.rect.x + 25, self.rect.centery - 20, 40, 40)
                # pygame.draw.rect(tela, (30, 30, 30), icone_rect, border_radius=5)
                # Desenhar um losango dourado
                center_icon = icone_rect.center
                points = [
                    (center_icon[0], center_icon[1] - 15),
                    (center_icon[0] + 15, center_icon[1]),
                    (center_icon[0], center_icon[1] + 15),
                    (center_icon[0] - 15, center_icon[1])
                ]
                pygame.draw.polygon(tela, cor_borda, points, 2)
            
            # Texto Principal
            cor_texto = (220, 220, 220) if not self.rect.collidepoint(pygame.mouse.get_pos()) else (255, 215, 0)
            texto_surface = self.fonte.render(self.texto, True, cor_texto)
            tela.blit(texto_surface, (self.rect.x + 90, self.rect.y + 15))
            
            # Subtítulo
            if self.subtitulo:
                sub_surface = self.fonte_sub.render(self.subtitulo, True, (150, 150, 150))
                tela.blit(sub_surface, (self.rect.x + 90, self.rect.y + 45))
                
        else:
            # Renderização Padrão (Antiga)
            pygame.draw.rect(tela, cor, self.rect, border_radius=5)
            # Adicionar borda sutil
            pygame.draw.rect(tela, (min(cor[0]+20, 255), min(cor[1]+20, 255), min(cor[2]+20, 255)), self.rect, 1, border_radius=5)
            
            texto_render = fonte.render(self.texto, True, COR_TEXTO)
            texto_rect = texto_render.get_rect(center=self.rect.center)
            tela.blit(texto_render, texto_rect)

    def checar_clique(self, pos):
        if not self.desabilitado and self.rect.collidepoint(pos):
            return True
        return False

    def update_hover(self, pos):
        if not self.desabilitado:
            if self.is_menu_button:
                 from ..config import COR_BOTAO_MENU, COR_BOTAO_MENU_HOVER
                 self.cor_atual = COR_BOTAO_MENU_HOVER if self.rect.collidepoint(pos) else COR_BOTAO_MENU
            else:
                self.cor_atual = self.cor_hover if self.rect.collidepoint(pos) else self.cor_base

class Tab(Botao): # Tab inherits from Botao
    def __init__(self, x, y, largura, altura, texto, fonte, id_tab):
        super().__init__(x, y, largura, altura, texto, fonte)
        self.id_tab = id_tab
        self.selected = False
        self.cor_selecionado = (100, 100, 200) # Cor para aba selecionada

    def desenhar(self, tela, fonte):
        cor = self.cor_selecionado if self.selected else self.cor_atual
        pygame.draw.rect(tela, cor, self.rect, border_radius=5)
        texto_render = fonte.render(self.texto, True, COR_TEXTO)
        texto_rect = texto_render.get_rect(center=self.rect.center)
        tela.blit(texto_render, texto_rect)

class Checkbox:
    def __init__(self, x, y, tamanho, texto, fonte, checked=False):
        self.rect = pygame.Rect(x, y, tamanho, tamanho)
        self.texto = texto
        self.fonte = fonte
        self.checked = checked
        self.texto_render = self.fonte.render(self.texto, True, COR_TEXTO)
        self.texto_rect = self.texto_render.get_rect(left=self.rect.right + 10, centery=self.rect.centery)

    def desenhar(self, tela):
        # Update text position to match rect
        self.texto_rect.left = self.rect.right + 10
        self.texto_rect.centery = self.rect.centery
        
        pygame.draw.rect(tela, COR_TEXTO, self.rect, 2, border_radius=3)
        if self.checked:
            pygame.draw.line(tela, COR_TEXTO, (self.rect.left + 3, self.rect.centery), (self.rect.centerx - 2, self.rect.bottom - 3), 3)
            pygame.draw.line(tela, COR_TEXTO, (self.rect.centerx - 2, self.rect.bottom - 3), (self.rect.right - 3, self.rect.top + 3), 3)
        tela.blit(self.texto_render, self.texto_rect)

    def checar_clique(self, pos):
        if self.rect.collidepoint(pos) or self.texto_rect.collidepoint(pos):
            self.toggle()
            return True
        return False

    def toggle(self):
        self.checked = not self.checked

class FloatingText:
    def __init__(self, x, y, texto, cor, fonte):
        self.x = x
        self.y = y
        self.texto = texto
        self.cor = cor
        self.fonte = fonte
        self.tempo_vida = 60  # 1 segundo a 60 FPS
        self.velocidade_y = -1

    def update(self):
        self.y += self.velocidade_y
        self.tempo_vida -= 1

    def draw(self, tela):
        if self.tempo_vida > 0:
            alpha = max(0, 255 * (self.tempo_vida / 60))
            texto_render = self.fonte.render(self.texto, True, self.cor)
            texto_render.set_alpha(alpha)
            tela.blit(texto_render, texto_render.get_rect(center=(self.x, self.y)))
