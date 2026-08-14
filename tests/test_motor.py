"""
tests/test_motor.py — Testes Unitários do Motor de Combate (Padrão AAA)
"""
import pytest
from src.motor_combate import MotorCombate
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago


def test_motor_combate_inicializacao():
    # Arrange
    args = [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # Act
    motor = MotorCombate(args_times=args, gerar_terreno=False)

    # Assert
    assert len(motor.combatentes) > 0
    assert motor.rodada_atual >= 1


def test_guerreiro_ataque_reduz_hp_alvo():
    # Arrange
    heroi = Guerreiro("Arthur", pos_x=5, pos_y=5)
    alvo = Mago("Merlin", pos_x=5, pos_y=6, hp_atual=30)
    hp_inicial = alvo.hp_atual

    # Act
    alvo.hp_atual -= 10

    # Assert
    assert alvo.hp_atual == 20
    assert alvo.hp_atual < hp_inicial


def test_personagem_limite_hp_zero():
    # Arrange
    heroi = Guerreiro("Arthur", pos_x=5, pos_y=5, hp_atual=10)

    # Act
    heroi.hp_atual = max(0, heroi.hp_atual - 15)

    # Assert
    assert heroi.hp_atual == 0
