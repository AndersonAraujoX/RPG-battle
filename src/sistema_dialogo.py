import pygame

class Dialogo:
    def __init__(self):
        self.fila_falas = []
        self.fala_atual = None
        self.texto_exibido = ""
        self.indice_letra = 0
        self.tempo_ultimo_char = 0
        self.velocidade_texto = 30  # ms por caractere
        self.ativo = False
        self.esperando_input = False
        self.callback_fim = None

    def iniciar_dialogo(self, falas, callback=None):
        """
        Inicia uma sequência de diálogos.
        falas: Lista de dicionários/tuplas com (nome_personagem, texto, imagem_retrato_key)
        callback: Função a ser chamada quando o diálogo terminar.
        """
        self.fila_falas = list(falas)
        self.ativo = True
        self.callback_fim = callback
        self.proxima_fala()

    def proxima_fala(self):
        if not self.fila_falas:
            self.encerrar_dialogo()
            return

        self.fala_atual = self.fila_falas.pop(0)
        self.texto_exibido = ""
        self.indice_letra = 0
        self.tempo_ultimo_char = pygame.time.get_ticks()
        self.esperando_input = False

    def atualizar(self):
        if not self.ativo or not self.fala_atual:
            return

        if self.esperando_input:
            return

        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_char > self.velocidade_texto:
            texto_completo = self.fala_atual[1]
            if self.indice_letra < len(texto_completo):
                self.texto_exibido += texto_completo[self.indice_letra]
                self.indice_letra += 1
                self.tempo_ultimo_char = agora
            else:
                self.esperando_input = True

    def processar_input(self):
        """
        Chamado quando o jogador aperta o botão de ação.
        """
        if not self.ativo:
            return

        if self.esperando_input:
            self.proxima_fala()
        else:
            # Se ainda está digitando, completa o texto imediatamente
            self.texto_exibido = self.fala_atual[1]
            self.indice_letra = len(self.texto_exibido)
            self.esperando_input = True

    def encerrar_dialogo(self):
        self.ativo = False
        self.fala_atual = None
        if self.callback_fim:
            self.callback_fim()
