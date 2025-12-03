from .item import Item

class Arma(Item):
    def __init__(self, nome, descricao, dado_dano):
        super().__init__(nome, descricao)
        self.dado_dano = dado_dano

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} equipa {self.nome}.")
        personagem.equipar_arma(self)
