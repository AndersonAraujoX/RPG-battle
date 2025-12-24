import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUIRefactor(unittest.TestCase):
    def test_imports_facade(self):
        """Testa se o facade desenho.py exporta as funções esperadas."""
        try:
            from src.ui import desenho
            
            # Funções de render_ui
            self.assertTrue(hasattr(desenho, 'desenhar_menu_principal'))
            self.assertTrue(hasattr(desenho, 'desenhar_setup_batalha'))
            self.assertTrue(hasattr(desenho, 'desenhar_tela_fim'))
            
            # Funções de render_combate
            self.assertTrue(hasattr(desenho, 'desenhar_cenario'))
            self.assertTrue(hasattr(desenho, 'desenhar_personagens'))
            self.assertTrue(hasattr(desenho, 'desenhar_log'))
            
            # Funções de render_mundo
            self.assertTrue(hasattr(desenho, 'desenhar_mapa_mundo'))
            self.assertTrue(hasattr(desenho, 'desenhar_editor'))
            
            print("Facade Imports: OK")
        except ImportError as e:
            self.fail(f"Falha ao importar desenho.py: {e}")

    def test_imports_modules(self):
        """Testa se os novos módulos existem e são importáveis."""
        try:
            import src.ui.render_ui
            import src.ui.render_combate
            import src.ui.render_mundo
            print("Module Imports: OK")
        except ImportError as e:
            self.fail(f"Falha ao importar novos módulos: {e}")

    def test_game_class_import(self):
        """Testa se a classe Game importa sem erros (valida integraçao)."""
        try:
            from src.game import Game
            print("Game Class Import: OK")
        except Exception as e:
            self.fail(f"Falha ao importar Game class: {e}")

if __name__ == '__main__':
    unittest.main()
