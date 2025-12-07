from .item import Item

class Material(Item):
    def __init__(self, nome, descricao):
        super().__init__(nome, descricao)

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} examina {self.nome}. É um material de crafting.")

class Osso(Material):
    def __init__(self):
        super().__init__("Osso", "Um osso velho e quebradiço.")

class CouroGoblin(Material):
    def __init__(self):
        super().__init__("Couro de Goblin", "Pele verde e resistente.")

class EssenciaMagica(Material):
    def __init__(self):
        super().__init__("Essência Mágica", "Brilha com uma luz fraca.")

class EscamaKobold(Material):
    def __init__(self):
        super().__init__("Escama de Kobold", "Pequena escama dura.")
