# src/personagens/status_efeito.py
from ..config import PROPRIEDADES_STATUS_EFEITO

class StatusEfeito:
    def __init__(self, nome, duracao_turnos=1):
        if nome not in PROPRIEDADES_STATUS_EFEITO:
            raise ValueError(f"Status Effect '{nome}' not defined in PROPRIEDADES_STATUS_EFEITO.")
        
        self.nome = nome
        self.propriedades = PROPRIEDADES_STATUS_EFEITO[nome]
        self.duracao_restante = duracao_turnos
    
    def aplicar_efeito_por_turno(self, personagem, tabuleiro, logger=print):
        if self.duracao_restante <= 0: return

        efeito_turno = self.propriedades.get("efeito_por_turno")
        if efeito_turno:
            if "dano_fixo" in efeito_turno:
                dano = efeito_turno["dano_fixo"]
                logger(f"  {personagem.nome} recebe {dano} de dano de {self.nome}!")
                personagem.receber_dano(dano, None, tabuleiro, logger) # None for attacker
            elif "dano_percentual_hp_max" in efeito_turno:
                dano = int(personagem.hp_max * efeito_turno["dano_percentual_hp_max"])
                logger(f"  {personagem.nome} sangra e recebe {dano} de dano de {self.nome}!")
                personagem.receber_dano(dano, None, tabuleiro, logger) # None for attacker
        
        # Outros efeitos por turno podem ser adicionados aqui

    def tick(self):
        self.duracao_restante -= 1
        return self.duracao_restante > 0

    def __str__(self):
        return f"{self.nome} ({self.duracao_restante} turnos)"
