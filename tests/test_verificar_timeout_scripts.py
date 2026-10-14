"""
tests/test_verificar_timeout_scripts.py

Suíte de testes unitários para tools/verificar_timeout_scripts.py.
Estrutura rigorosa Arrange-Act-Assert (AAA), cobrindo fluxo principal,
casos de borda e tratamento de erros conforme as diretrizes do projeto.
Compatível nativamente com python3 -m unittest e pytest.
"""

import os
import sys
import tempfile
import unittest

# Adiciona raiz do projeto ao path para importar a ferramenta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.verificar_timeout_scripts import (
    analisar_script_gd,
    analisar_script_py,
    verificar_diretorio
)


class TestVerificarTimeoutScripts(unittest.TestCase):
    # ── 1. Testes de Análise GDScript (Arrange-Act-Assert) ─────────────────────

    def test_analisar_script_gd_happy_path_com_watchdog_e_quit(self):
        # Arrange
        caminho = "tools/exemplo_seguro.gd"
        conteudo = """
        extends SceneTree

        func _init() -> void:
            var watchdog: SceneTreeTimer = create_timer(4.0)
            watchdog.timeout.connect(func(): quit(1))
            
            var timer: SceneTreeTimer = create_timer(1.0)
            timer.timeout.connect(_on_timeout)

        func _on_timeout() -> void:
            print("Concluído!")
            quit(0)
        """

        # Act
        resultado = analisar_script_gd(caminho, conteudo)

        # Assert
        self.assertTrue(resultado["eh_scenetree"])
        self.assertTrue(resultado["possui_quit"])
        self.assertTrue(resultado["possui_watchdog"])
        self.assertTrue(resultado["aprovado"])
        self.assertEqual(len(resultado["problemas"]), 0)

    def test_analisar_script_gd_falha_sem_quit(self):
        # Arrange: SceneTree sem chamada explícita de quit()
        caminho = "tools/exemplo_infinito.gd"
        conteudo = """
        extends SceneTree

        func _init() -> void:
            var timer = create_timer(2.0)
            timer.timeout.connect(func(): print("Sem quit!"))
        """

        # Act
        resultado = analisar_script_gd(caminho, conteudo)

        # Assert
        self.assertTrue(resultado["eh_scenetree"])
        self.assertFalse(resultado["possui_quit"])
        self.assertFalse(resultado["aprovado"])
        self.assertTrue(any("não contém chamada de quit()" in p for p in resultado["problemas"]))

    def test_analisar_script_gd_falha_sem_watchdog(self):
        # Arrange: SceneTree com quit() mas sem watchdog de emergência
        caminho = "tools/sem_watchdog.gd"
        conteudo = """
        extends SceneTree

        func _init() -> void:
            print("Iniciando")
            quit(0)
        """

        # Act
        resultado = analisar_script_gd(caminho, conteudo)

        # Assert
        self.assertTrue(resultado["eh_scenetree"])
        self.assertTrue(resultado["possui_quit"])
        self.assertFalse(resultado["possui_watchdog"])
        self.assertFalse(resultado["aprovado"])
        self.assertTrue(any("não implementa Watchdog Timer" in p for p in resultado["problemas"]))

    def test_analisar_script_gd_detecta_while_true_perigoso(self):
        # Arrange: Loop while true sem segurança
        caminho = "tools/loop_infinito.gd"
        conteudo = """
        extends Node

        func executar() -> void:
            while true:
                print("Preso")
        """

        # Act
        resultado = analisar_script_gd(caminho, conteudo)

        # Assert
        self.assertFalse(resultado["aprovado"])
        self.assertTrue(any("while true" in p for p in resultado["problemas"]))

    def test_analisar_script_gd_script_comum_sem_scenetree_aprovado(self):
        # Arrange: Script que é apenas um Node ou Resource comum
        caminho = "scripts/entities/Guerreiro.gd"
        conteudo = """
        class_name Guerreiro
        extends RefCounted

        var hp: int = 50
        """

        # Act
        resultado = analisar_script_gd(caminho, conteudo)

        # Assert
        self.assertFalse(resultado["eh_scenetree"])
        self.assertTrue(resultado["aprovado"])
        self.assertEqual(len(resultado["problemas"]), 0)

    # ── 2. Testes de Análise Python (Arrange-Act-Assert) ───────────────────────

    def test_analisar_script_py_happy_path(self):
        # Arrange: Script Python com loop while controlado por break
        caminho = "tools/conversor.py"
        conteudo = """
        import sys

        def processar():
            tentativas = 0
            while True:
                tentativas += 1
                if tentativas >= 10:
                    break
        """

        # Act
        resultado = analisar_script_py(caminho, conteudo)

        # Assert
        self.assertTrue(resultado["aprovado"])
        self.assertEqual(len(resultado["problemas"]), 0)

    def test_analisar_script_py_detecta_while_true_sem_saida(self):
        # Arrange: Script Python com while True infinito sem break/timeout evidente
        caminho = "tools/bloqueante.py"
        conteudo = """
        def escutar():
            while True:
                item = receber_dado()
                processar(item)
        """

        # Act
        resultado = analisar_script_py(caminho, conteudo)

        # Assert
        self.assertFalse(resultado["aprovado"])
        self.assertTrue(any("while True" in p for p in resultado["problemas"]))

    # ── 3. Testes de Diretório & Casos de Borda (Edge Cases) ──────────────────

    def test_verificar_diretorio_inexistente(self):
        # Arrange
        dir_inexistente = "caminho/fantasma/inexistente"

        # Act
        resultados = verificar_diretorio(dir_inexistente)

        # Assert
        self.assertEqual(resultados, [])

    def test_verificar_diretorio_com_arquivos_reais(self):
        # Arrange: Cria um diretório temporário com scripts de teste
        with tempfile.TemporaryDirectory() as tmpdir:
            arq_gd = os.path.join(tmpdir, "test_tool.gd")
            with open(arq_gd, "w", encoding="utf-8") as f:
                f.write("""
                extends SceneTree
                func _init() -> void:
                    var watchdog: SceneTreeTimer = create_timer(3.0)
                    watchdog.timeout.connect(func(): quit(1))
                    quit(0)
                """)

            arq_py = os.path.join(tmpdir, "test_tool.py")
            with open(arq_py, "w", encoding="utf-8") as f:
                f.write("""
                def main():
                    print("Seguro")
                """)

            # Act
            resultados = verificar_diretorio(tmpdir)

            # Assert
            self.assertEqual(len(resultados), 2)
            self.assertTrue(all(r["aprovado"] for r in resultados))


if __name__ == "__main__":
    unittest.main()
