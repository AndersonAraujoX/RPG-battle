#!/usr/bin/env python3
"""
tools/run_coop_server.py — Inicializador do Servidor Co-op Online (RPG-battle)

Inicia o backend FastAPI + WebSockets usando Uvicorn para partidas multijogador em tempo real.
Acesse a interface em: http://localhost:8000/ ou http://localhost:8000/coop/
"""
import argparse
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from src.server.app import app


def main():
    parser = argparse.ArgumentParser(description="RPG-battle: Servidor Co-op Online (FastAPI + WebSockets)")
    parser.add_argument("--host", default="0.0.0.0", help="Endereço de rede para escuta (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Porta TCP do servidor (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Habilita auto-reload para desenvolvimento")
    args = parser.parse_args()

    print("=" * 70)
    print(" 🏰 RPG-BATTLE : SERVIDOR CO-OP ONLINE (TEMPO REAL)")
    print("=" * 70)
    print(f" ▶ Endereço Local:  http://localhost:{args.port}/coop/")
    print(f" ▶ Escutando em:    http://{args.host}:{args.port}/")
    print(f" ▶ API Docs:        http://localhost:{args.port}/docs")
    print("-" * 70)
    print(" Compartilhe o link da sala com seus companheiros de equipe!")
    print(" Pressione Ctrl+C para encerrar o servidor.")
    print("=" * 70)

    target = "src.server.app:app" if args.reload else app
    uvicorn.run(
        target,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
