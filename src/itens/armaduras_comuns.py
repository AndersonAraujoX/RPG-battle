from .armadura import Armadura

class CouracaDeCouro(Armadura):
    def __init__(self):
        super().__init__("Couraça de Couro", "Uma armadura de couro leve.", 12)

class CotaDeMalha(Armadura):
    def __init__(self):
        super().__init__("Cota de Malha", "Uma armadura de malha flexível.", 14)

class PlacasDeAco(Armadura):
    def __init__(self):
        super().__init__("Placas de Aço", "Uma armadura de placas completa.", 18)
