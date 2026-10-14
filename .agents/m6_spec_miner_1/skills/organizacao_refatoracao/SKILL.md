---
name: organizacao_refatoracao
description: Diretrizes de arquitetura limpa, padrão de refatoração, organização de pastas e testes unitários para o projeto RPG-battle.
---

# Skill de Organização & Refatoração de Código (RPG-battle)

Esta Skill define os padrões de arquitetura, refatoração de código, higienização da estrutura de arquivos e suíte de testes unitários para o projeto **RPG-battle**.

---

## 🏛️ 1. Arquitetura de Pastas Recomendada
Estrutura modular: src/ (core, engine, entities, states, ui), tests/, assets/, dados/, tools/, main.py.

## 🧹 2. Regras de Limpeza da Raiz
- Arquivos temporários de debug em tools/ ou scratch/
- Sem arquivos *.bak em src/
- Saves locais em dados/saves/ ou raiz

## 🧼 3. Padrão de Sanitização de Fontes e Emojis em Pygame
- Sempre sanitizar_texto_fonte(texto) antes de renderizar em fontes bitmap sem emojis.

## 🧪 4. Diretriz Obrigatória de Testes Unitários (SOLID + AAA)
- Estrutura AAA (Arrange-Act-Assert)
- Caminho feliz, Casos de borda, Tratamento de erros
