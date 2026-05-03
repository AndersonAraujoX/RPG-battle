from .item import Item

class Arma(Item):
    def __init__(self, nome, descricao, dado_dano, tipo_dano="Fisico"):
        super().__init__(nome, descricao)
        self.dado_dano = dado_dano
        self.tipo_dano = tipo_dano

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} equipa {self.nome}.")
        personagem.equipar_arma(self)
