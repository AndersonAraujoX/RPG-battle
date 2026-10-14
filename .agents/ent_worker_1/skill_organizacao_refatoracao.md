# Skill de Organização & Refatoração de Código (RPG-battle)

Esta Skill define os padrões de arquitetura, refatoração de código, higienização da estrutura de arquivos e suíte de testes unitários para o projeto RPG-battle.

## 1. Arquitetura Limpa & Princípios SOLID
- Código desacoplado, testável e tipado estaticamente em Godot 4.
- Injeção de dependências e sinais via EventBus para evitar acoplamento direto.

## 2. Padrão AAA em Testes Unitários
- Arrange: Preparar instâncias e dados
- Act: Executar métodos e comportamentos
- Assert: Validar resultados e sinais

## 3. Cobertura Mínima
- Caminho feliz
- Casos de borda (valores limites, coleções vazias, dano excessivo, cura em morto)
- Tratamento de exceções e tolerância a falhas (fallback de texturas, clamped HP)
- Zero memory leaks no ObjectDB
