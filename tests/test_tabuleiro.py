"""
tests/test_tabuleiro.py — Testes Unitários do Tabuleiro 2D e Grid (Padrão AAA)
"""
import pytest
from src.tabuleiro import Tabuleiro
from src.personagens.guerreiro import Guerreiro


def test_tabuleiro_posicionamento_unidade():
    # Arrange
    tab = Tabuleiro(largura=20, altura=20)
    heroi = Guerreiro("Thor", pos_x=4, pos_y=4)

    # Act
    sucesso = tab.adicionar_personagem(heroi, 4, 4)

    # Assert
    assert sucesso is True
    assert tab.grid[4][4] is heroi


def test_tabuleiro_limites_grid():
    # Arrange
    tab = Tabuleiro(largura=20, altura=20)

    # Act
    dentro_valido = 0 <= 10 < tab.largura and 0 <= 10 < tab.altura
    fora_valido = 0 <= 25 < tab.largura and 0 <= 25 < tab.altura

    # Assert
    assert dentro_valido is True
    assert fora_valido is False


def test_tabuleiro_movimentacao_unidade():
    # Arrange
    tab = Tabuleiro(largura=20, altura=20)
    heroi = Guerreiro("Thor", pos_x=2, pos_y=2)
    tab.adicionar_personagem(heroi, 2, 2)

    # Act
    sucesso = tab.mover_personagem(heroi, 3, 2)

    # Assert
    assert sucesso is True
    assert tab.grid[2][2] is None
    assert tab.grid[2][3] is heroi
    assert heroi.pos_x == 3
    assert heroi.pos_y == 2
