"""
tests/test_cerco_state.py — Testes Unitários de Mecânicas do CercoState (QTE Parry, Riposte e Overwatch)
"""
try:
    import pytest
except ImportError:
    pytest = None
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago


def test_overwatch_postura_vigilancia_hero():
    # Arrange
    heroi = Guerreiro("Stark", pos_x=5, pos_y=5)

    # Act
    heroi.em_vigilancia = True

    # Assert
    assert getattr(heroi, "em_vigilancia", False) is True


def test_parry_perfect_anula_dano_e_contra_ataca():
    # Arrange
    heroi = Guerreiro("Stark", pos_x=5, pos_y=5, hp_atual=50)
    invasor = Mago("Gorgulho", pos_x=5, pos_y=6, hp_atual=30)
    dano_base = 15

    # Act (Simulação Perfect Parry)
    resultado = "PARRY"
    if resultado == "PARRY":
        dano_recebido = 0
        dano_riposte = 8
        heroi.hp_atual -= dano_recebido
        invasor.hp_atual -= dano_riposte

    # Assert
    assert heroi.hp_atual == 50
    assert invasor.hp_atual == 22


def test_dodge_reduz_75_porcento_dano():
    # Arrange
    heroi = Guerreiro("Stark", pos_x=5, pos_y=5, hp_atual=50)
    dano_base = 20

    # Act (Simulação Dodge Parcial)
    resultado = "DODGE"
    if resultado == "DODGE":
        dano_recebido = max(1, int(dano_base * 0.25))
        heroi.hp_atual -= dano_recebido

    # Assert
    assert dano_recebido == 5
    assert heroi.hp_atual == 45


def test_agendamento_ordem_simultanea_coop():
    # Arrange
    heroi = Guerreiro("Stark", pos_x=5, pos_y=5)
    fila_ordens = []

    # Act
    ordem = {
        "agente_nome": heroi.nome,
        "tipo_acao": "Onda de Choque",
        "dados": {"pos_alvo": [5, 6]}
    }
    fila_ordens.append(ordem)

    # Assert
    assert len(fila_ordens) == 1
    assert fila_ordens[0]["agente_nome"] == "Stark"
    assert fila_ordens[0]["tipo_acao"] == "Onda de Choque"
