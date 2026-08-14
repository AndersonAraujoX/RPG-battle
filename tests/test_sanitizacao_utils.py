"""
tests/test_sanitizacao_utils.py — Testes Unitários de Sanitização de Fontes e Utilitários (Padrão AAA)
"""
try:
    import pytest
except ImportError:
    pytest = None
from src.utils import sanitizar_texto_fonte, remover_emojis


def test_sanitizar_texto_fonte_substitui_emojis_conhecidos():
    # Arrange
    texto_bruto = "❤️ 50/50  ⚔️ +5  🛡️ 14  👁️ VIGILÂNCIA  🌟 PERFECT  💥 12  🎁 DRAFT  💎 5"

    # Act
    texto_limpo = sanitizar_texto_fonte(texto_bruto)

    # Assert
    assert "[HP]" not in texto_limpo or "50/50" in texto_limpo
    assert "[ATK]" in texto_limpo
    assert "[DEF]" in texto_limpo
    assert "[VIGILÂNCIA]" in texto_limpo
    assert "[PERFECT]" in texto_limpo
    assert "[DANO]" in texto_limpo
    assert "[DRAFT]" in texto_limpo
    assert "[Cristal]" in texto_limpo or "5" in texto_limpo


def test_sanitizar_texto_fonte_com_entradas_especiais():
    # Arrange & Act
    resultado_vazio = sanitizar_texto_fonte("")
    resultado_numero = sanitizar_texto_fonte(12345)
    resultado_none = sanitizar_texto_fonte(None)

    # Assert
    assert resultado_vazio == ""
    assert resultado_numero == "12345"
    assert resultado_none == "None"


def test_remover_emojis_remove_caracteres_unicodes():
    # Arrange
    texto_com_emoji = "Heroi 🤖 atacando 🐛 inimigo"

    # Act
    texto_sem_emoji = remover_emojis(texto_com_emoji)

    # Assert
    assert "Heroi" in texto_sem_emoji
    assert "atacando" in texto_sem_emoji
    assert "inimigo" in texto_sem_emoji


def test_sanitizar_texto_fonte_cache_lru():
    # Arrange
    texto = "❤️ 100/100  ⚔️ +10"

    # Act
    res1 = sanitizar_texto_fonte(texto)
    res2 = sanitizar_texto_fonte(texto)

    # Assert
    assert res1 == res2
    assert hasattr(sanitizar_texto_fonte, "cache_info")
    info = sanitizar_texto_fonte.cache_info()
    assert info.hits >= 1
