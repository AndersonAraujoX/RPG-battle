"""
tests/test_async_loop.py — Suíte de Testes Unitários para o Loop Assíncrono do Game (Padrão AAA)
Garante compatibilidade com Pygbag (WebAssembly) e execução desktop não-bloqueante.
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from src.game import Game
import main


class TestAsyncLoop(unittest.TestCase):

    def test_run_async_is_coroutine_function(self):
        # Arrange
        # A classe Game deve expor um método assíncrono para cooperar com o event loop do navegador

        # Act & Assert
        self.assertTrue(
            asyncio.iscoroutinefunction(Game.run_async),
            "Game.run_async deve ser uma corrotina assíncrona (async def)"
        )

    def test_main_function_is_coroutine(self):
        # Arrange
        # O ponto de entrada main() deve ser async def para o empacotador Pygbag/Emscripten

        # Act & Assert
        self.assertTrue(
            asyncio.iscoroutinefunction(main.main),
            "main.main() deve ser uma função de corrotina (async def)"
        )

    @patch("pygame.display.flip")
    @patch("pygame.quit")
    @patch("pygame.mouse.get_pos", return_value=(0, 0))
    @patch("pygame.time.get_ticks", return_value=100)
    def test_run_async_termina_imediatamente_se_rodando_for_falso(self, mock_ticks, mock_mouse, mock_quit, mock_flip):
        # Arrange
        with patch.object(Game, "__init__", return_value=None):
            game = Game()
            game.rodando = False
            game.motor = None
            game.clock = MagicMock()

            # Act
            asyncio.run(game.run_async())

            # Assert
            mock_quit.assert_called_once()
            mock_flip.assert_not_called()

    @patch("pygame.display.flip")
    @patch("pygame.quit")
    @patch("pygame.mouse.get_pos", return_value=(100, 100))
    @patch("pygame.time.get_ticks", return_value=150)
    def test_run_async_executa_um_frame_e_encerra_ao_desativar_rodando(self, mock_ticks, mock_mouse, mock_quit, mock_flip):
        # Arrange
        with patch.object(Game, "__init__", return_value=None):
            game = Game()
            game.rodando = True
            game.motor = None
            game.clock = MagicMock()
            game.handle_events = MagicMock()
            game.update_game_logic = MagicMock()
            game.draw_elements = MagicMock()

            # Simula evento de fechar janela durante o primeiro frame
            def simular_evento_fechar(mouse_pos, personagem_ativo):
                game.rodando = False

            game.handle_events.side_effect = simular_evento_fechar

            # Act
            asyncio.run(game.run_async())

            # Assert
            game.handle_events.assert_called_once()
            game.update_game_logic.assert_not_called()
            mock_quit.assert_called_once()

    @patch("pygame.display.flip")
    @patch("pygame.quit")
    @patch("pygame.mouse.get_pos", return_value=(50, 50))
    @patch("pygame.time.get_ticks", return_value=200)
    def test_run_async_completa_ciclo_de_renderizacao_se_continuar_rodando(self, mock_ticks, mock_mouse, mock_quit, mock_flip):
        # Arrange
        with patch.object(Game, "__init__", return_value=None):
            game = Game()
            game.rodando = True
            game.motor = None
            game.clock = MagicMock()
            game.handle_events = MagicMock()
            game.update_game_logic = MagicMock()
            game.draw_elements = MagicMock()

            # Permite 1 frame completo e encerra no início do 2º frame
            frame_count = 0
            def simular_um_frame_completo(agora, personagem_ativo):
                nonlocal frame_count
                frame_count += 1
                game.rodando = False

            game.update_game_logic.side_effect = simular_um_frame_completo

            # Act
            asyncio.run(game.run_async())

            # Assert
            self.assertEqual(frame_count, 1)
            game.draw_elements.assert_called_once()
            mock_flip.assert_called_once()
            mock_quit.assert_called_once()

    def test_web_template_config_validations(self):
        # Arrange
        template_path = "web_template.tmpl"

        # Act
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Assert
        self.assertIn('data-os="stdout,snd,gui"', content, "Terminal vtx deve ser substituído por stdout limpo")
        self.assertIn('ume_block : 0', content, "ume_block deve ser 0 para evitar travamento de mídia")
        self.assertIn('autorun : 1', content, "autorun deve ser 1")
        self.assertIn('window.MM.UME = true', content, "unlockMediaAndStart deve destravar window.MM.UME")
        self.assertIn('Cache-Control', content, "Headers de prevenção de cache devem estar presentes")

    def test_main_script_has_pep723_and_pygame_import(self):
        # Arrange
        main_path = "main.py"

        # Act
        with open(main_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Assert
        self.assertIn("/// script", code, "main.py deve conter cabeçalho PEP 723 para Pygbag")
        self.assertIn("pygame-ce", code, "main.py deve declarar dependência pygame-ce no PEP 723")
        self.assertIn("import pygame", code, "main.py deve conter import pygame no escopo raiz")

    def test_safe_rect_functionality_and_fallback(self):
        # Arrange
        from src.config import _safe_rect

        # Act - Criação com valores válidos
        rect = _safe_rect(10, 20, 100, 50)

        # Assert - Dimensões e posicionamento
        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 50)
        self.assertEqual(rect.right, 110)
        self.assertEqual(rect.bottom, 70)
        self.assertTrue(rect.collidepoint((50, 30)))
        self.assertFalse(rect.collidepoint((200, 300)))


if __name__ == "__main__":
    unittest.main()
