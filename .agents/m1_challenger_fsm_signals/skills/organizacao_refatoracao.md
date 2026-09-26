---
name: organizacao_refatoracao
description: Diretrizes de arquitetura limpa, padrão de refatoração, organização de pastas e testes unitários para o projeto RPG-battle.
---

# Skill de Organização & Refatoração de Código (RPG-battle)

Esta Skill define os padrões de arquitetura, refatoração de código, higienização da estrutura de arquivos e suíte de testes unitários para o projeto **RPG-battle**.

---

## 🏛️ 1. Arquitetura de Pastas Recomendada
Siga a estrutura modular do projeto.

## 🧹 2. Regras de Limpeza da Raiz
Arquivos de debug/teste vão para tools/ ou scratch/.

## 🧼 3. Padrão de Sanitização de Fontes e Emojis em Pygame
Uso de sanitizar_texto_fonte() quando aplicável.

## 🧪 4. Diretriz Obrigatória de Testes Unitários (SOLID + AAA)
Arrange-Act-Assert, cobrindo caminho feliz, casos de borda e tratamento de erros.
