from .acessorio import Acessorio

class AnelDeForca(Acessorio):
    def __init__(self):
        super().__init__("Anel de Força", "Um anel que aumenta a força do usuário.", {'forca': 2})

class AmuletoDeVitalidade(Acessorio):
    def __init__(self):
        super().__init__("Amuleto de Vitalidade", "Um amuleto que aumenta a constituição do usuário.", {'constituicao': 2})

class BotasDaVelocidade(Acessorio):
    def __init__(self):
        super().__init__("Botas da Velocidade", "Botas que aumentam a velocidade do usuário.", {'velocidade': 1})
