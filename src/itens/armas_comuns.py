from .arma import Arma

class EspadaLonga(Arma):
    def __init__(self):
        super().__init__("Espada Longa", "Uma espada longa e versátil.", (1, 8))

class Adaga(Arma):
    def __init__(self):
        super().__init__("Adaga", "Uma adaga rápida e mortal.", (1, 4))

class ArcoCurto(Arma):
    def __init__(self):
        super().__init__("Arco Curto", "Um arco curto para ataques à distância.", (1, 6))

class MachadoGrande(Arma):
    def __init__(self):
        super().__init__("Machado Grande", "Um machado pesado de duas mãos.", (1, 12))
