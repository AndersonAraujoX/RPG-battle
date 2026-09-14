#!/usr/bin/env bash
# tools/build_web.sh — Compilar RPG-battle para WebAssembly usando Pygbag
set -e

echo "=== [RPG-battle] Iniciando Build Web (WebAssembly via Pygbag) ==="

if ! command -v pygbag &> /dev/null; then
    echo "Pygbag não encontrado. Instalando..."
    pip install pygbag
fi

echo "Compilando jogo a partir da raiz..."
pygbag --build .

echo ""
echo "=== Build Concluído com Sucesso! ==="
echo "Arquivos gerados na pasta 'build/web/'"
echo "Para testar localmente com servidor web embutido do Pygbag:"
echo "  pygbag ."
