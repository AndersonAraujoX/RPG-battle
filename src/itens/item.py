class Item:
    def __init__(self, nome, descricao):
        self.nome = nome
        self.descricao = descricao

    def usar(self, personagem, logger=print):
        logger(f"{personagem.nome} usa {self.nome}.")

class HealthPotion(Item):
    def __init__(self):
        super().__init__("Poção de Cura", "Restaura 2d4 + 2 de HP.")
        self.cura_dado = (2, 4)
        self.cura_bonus = 2

    def usar(self, personagem, logger=print):
        import random
        cura = sum(random.randint(1, self.cura_dado[1]) for _ in range(self.cura_dado[0])) + self.cura_bonus
        super().usar(personagem, logger)
        personagem.receber_cura(cura, logger)
