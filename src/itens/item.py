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
        from src.config import COR_TEXTO, COR_CURA
        cura = sum(random.randint(1, self.cura_dado[1]) for _ in range(self.cura_dado[0])) + self.cura_bonus
        logger((f"{personagem.nome} usa {self.nome}.", COR_TEXTO))
        personagem.receber_cura(cura, logger)

class ManaPotion(Item):
    def __init__(self):
        super().__init__("Poção de Mana", "Restaura 5 de Mana.")
        self.mana_recuperada = 5

    def usar(self, personagem, logger=print):
        from src.config import COR_TEXTO, COR_MANA_BAR
        personagem.mana_atual = min(personagem.mana_max, personagem.mana_atual + self.mana_recuperada)
        logger((f"{personagem.nome} usa {self.nome} e recupera {self.mana_recuperada} de Mana.", COR_MANA_BAR))
        personagem.eventos_animacao.append({'tipo': 'floating_text', 'personagem': personagem, 'texto': f'+{self.mana_recuperada} MP', 'cor': COR_MANA_BAR})

class Antidote(Item):
    def __init__(self):
        super().__init__("Antídoto", "Cura veneno.")

    def usar(self, personagem, logger=print):
        from src.config import COR_TEXTO, STATUS_ENVENENADO
        logger((f"{personagem.nome} usa {self.nome}.", COR_TEXTO))
        personagem.remover_status_efeito(STATUS_ENVENENADO, logger)

class SmokeBomb(Item):
    def __init__(self):
        super().__init__("Bomba de Fumaça", "Permite fugir com sucesso garantido.")

    def usar(self, personagem, logger=print):
        from src.config import COR_TEXTO
        logger((f"{personagem.nome} joga uma {self.nome} no chão!", COR_TEXTO))
        # A lógica de fuga será tratada no motor de combate ou personagem, 
        # mas aqui podemos adicionar um status temporário de "Invisível" ou "Fuga Garantida"
        # Por simplicidade, vamos dizer que o personagem ganha um status de "Fuga Garantida" por 1 turno
        personagem.aplicar_status_efeito("Fuga Garantida", 1, logger)
