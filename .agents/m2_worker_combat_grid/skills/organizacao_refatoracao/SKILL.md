---
name: organizacao_refatoracao
description: Diretrizes de arquitetura limpa, padrão de refatoração, organização de pastas e testes unitários para o projeto RPG-battle.
---

# Skill de Organização & Refatoração de Código (RPG-battle)

Esta Skill define os padrões de arquitetura, refatoração de código, higienização da estrutura de arquivos e suíte de testes unitários para o projeto **RPG-battle**.

---

## 🏛️ 1. Arquitetura de Pastas Recomendada
...
## 🧪 4. Diretriz Obrigatória de Testes Unitários (SOLID + AAA)
Para toda nova funcionalidade ou refatoração implementada:
1. Estrutura Arrange-Act-Assert (AAA)
2. Cobertura Mínima:
   - Fluxo principal (Caminho feliz).
   - Casos de borda (coleções vazias, limites de tabuleiro, unidades mortas).
   - Validação de exceções e tratamento de erros.
