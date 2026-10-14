#!/usr/bin/env python3
"""
tools/verificar_timeout_scripts.py

Linter e verificador estático de prevenção de execuções infinitas (Skill prevencao_execucao_infinita).
Analisa scripts GDScript e Python para detectar:
1. Ausência de quit() ou sys.exit() em scripts de execução standalone.
2. Ausência de Watchdog Timer de segurança em scripts SceneTree do Godot.
3. Loops 'while' descontrolados ou infinitos sem contador de teto (max attempts).
"""

import os
import re
import sys
from typing import Dict, List, Any


def analisar_script_gd(caminho: str, conteudo: str) -> Dict[str, Any]:
    """
    Analisa um script GDScript verificando conformidade com as regras de prevenção
    de execução infinita.
    """
    linhas = conteudo.splitlines()
    eh_scenetree = bool(re.search(r'extends\s+SceneTree', conteudo))
    possui_quit = bool(re.search(r'\bquit\s*\(', conteudo))
    possui_watchdog = bool(re.search(r'watchdog|create_timer\s*\(\s*[0-9]+(\.[0-9]+)?\s*\).*(?:quit|timeout)', conteudo, re.IGNORECASE))
    
    problemas: List[str] = []

    if eh_scenetree:
        if not possui_quit:
            problemas.append("Script herda de SceneTree mas não contém chamada de quit() explícita.")
        if not possui_watchdog:
            problemas.append("Script SceneTree não implementa Watchdog Timer de fail-safe.")

    # Detecção de while perigoso
    for idx, linha in enumerate(linhas, 1):
        linha_limpa = linha.strip()
        if re.search(r'\bwhile\s+true\b', linha_limpa, re.IGNORECASE):
            problemas.append(f"Linha {idx}: Uso arriscado de 'while true' sem condição de término declarada.")

    aprovado = len(problemas) == 0
    return {
        "caminho": caminho,
        "eh_scenetree": eh_scenetree,
        "possui_quit": possui_quit,
        "possui_watchdog": possui_watchdog,
        "problemas": problemas,
        "aprovado": aprovado
    }


def analisar_script_py(caminho: str, conteudo: str) -> Dict[str, Any]:
    """
    Analisa um script Python verificando loops infinitos sem proteção de timeout.
    """
    linhas = conteudo.splitlines()
    problemas: List[str] = []

    for idx, linha in enumerate(linhas, 1):
        linha_limpa = linha.strip()
        # Ignora comentários
        if linha_limpa.startswith("#"):
            continue
        if re.search(r'\bwhile\s+True\s*:', linha_limpa):
            # Checa se nas próximas 10 linhas há menção a break, timeout ou exit
            trecho = "\n".join(linhas[idx:idx+15])
            if not re.search(r'\b(break|timeout|sys\.exit|raise)\b', trecho):
                problemas.append(f"Linha {idx}: 'while True' sem mecanismo evidente de break ou timeout no bloco imediato.")

    aprovado = len(problemas) == 0
    return {
        "caminho": caminho,
        "problemas": problemas,
        "aprovado": aprovado
    }


def verificar_diretorio(diretorio: str) -> List[Dict[str, Any]]:
    """
    Varre recursivamente um diretório analisando todos os arquivos .gd e .py.
    """
    resultados: List[Dict[str, Any]] = []
    if not os.path.exists(diretorio):
        return resultados

    for raiz, _, arquivos in os.walk(diretorio):
        for arq in arquivos:
            caminho_completo = os.path.join(raiz, arq)
            if arq.endswith(".gd"):
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        conteudo = f.read()
                    resultados.append(analisar_script_gd(caminho_completo, conteudo))
                except Exception as e:
                    resultados.append({
                        "caminho": caminho_completo,
                        "problemas": [f"Erro ao ler arquivo: {str(e)}"],
                        "aprovado": False
                    })
            elif arq.endswith(".py"):
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        conteudo = f.read()
                    resultados.append(analisar_script_py(caminho_completo, conteudo))
                except Exception as e:
                    resultados.append({
                        "caminho": caminho_completo,
                        "problemas": [f"Erro ao ler arquivo: {str(e)}"],
                        "aprovado": False
                    })

    return resultados


def main() -> int:
    diretorios = ["tools", "godot_project/tools"]
    total_problemas = 0
    total_analisados = 0

    print("🛡️ Verificador de Prevenção de Execução Infinita (Skill prevencao_execucao_infinita)")
    print("=" * 80)

    for d in diretorios:
        if not os.path.exists(d):
            continue
        resultados = verificar_diretorio(d)
        for r in resultados:
            total_analisados += 1
            if not r["aprovado"]:
                total_problemas += len(r["problemas"])
                print(f"❌ [FALHA] {r['caminho']}")
                for p in r["problemas"]:
                    print(f"   └── {p}")
            else:
                if r.get("eh_scenetree", False):
                    print(f"✅ [PROTEGIDO] {r['caminho']} (SceneTree com Watchdog e quit)")

    print("=" * 80)
    print(f"Total de scripts analisados: {total_analisados} | Problemas detectados: {total_problemas}")

    if total_problemas > 0:
        print("⚠️ Foram encontradas inconsistências que podem causar execução infinita.")
        return 1
    else:
        print("🎉 Todos os scripts standalone cumprem as diretrizes de prevenção de execução infinita!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
