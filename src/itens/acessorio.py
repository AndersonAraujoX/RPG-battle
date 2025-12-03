from .item import Item

class Acessorio(Item):
    def __init__(self, nome, descricao, bonus):
        super().__init__(nome, descricao)
        self.bonus = bonus

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} equipa {self.nome}.")
        personagem.equipar_acessorio(self)
