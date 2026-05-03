from .item import Item

class Armadura(Item):
    def __init__(self, nome, descricao, bonus_ac):
        super().__init__(nome, descricao)
        self.bonus_ac = bonus_ac

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} equipa {self.nome}.")
        personagem.equipar_armadura(self)
