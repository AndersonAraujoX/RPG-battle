# Original User Request

## 2026-10-16T01:04:10Z

Implementar os marcos M3 a M8 da Campanha Roguelike Tática em Godot 4 descritos em `CAMPANHA_ROGUELIKE.md`, conectando os nós do mapa aos combates táticos em grade 20x20, telas de recompensa/forja, relíquias, chefes dos 3 Atos e a batalha final épica em 3 fases contra o Rei dos Isectum.

Working directory: /home/anderson/Documents/projeto/RPG-battle/godot_project
Integrity mode: demo

## Reference Material
- Documento oficial de design e arquitetura: `CAMPANHA_ROGUELIKE.md`
- Fases e castas existentes: `dados/fases/`, `godot_project/scripts/cerco/IsectumCastes.gd`
- Arquitetura da run implementada: `godot_project/scripts/run/` (`RunNode.gd`, `RunMap.gd`, `RunMapGenerator.gd`, `RunState.gd`, `RunNodeResolver.gd`, `RunSession.gd`, `RunMapScreen.gd`)
- Suíte de testes GUT existente (729 testes verdes): `godot_project/run_gut_tests.sh`

## Requirements

### R1. Recompensas Pós-Combate, Forja & Sistema de Relíquias (M3)
- Modal interativo pós-combate "Escolha 1 de 3 Cartas" com animação de seleção e adição ao deck da expedição.
- Sistema de Relíquias passivas acopladas a sinais do `EventBus` (ex: dano adicional, redução de dano, ouro extra, cura em fogueira).
- Tela/Modal da Forja Anã (nó `FORGE`) permitindo comprar cartas, relíquias e remover cartas do deck usando ouro da run.

### R2. Integração do Combate Tático aos Nós do Mapa (M4)
- Conectar a seleção de nós `COMBAT`, `ELITE`, `SIEGE` e `BOSS` ao carregamento da arena tática em `Main.tscn` / `FortressBoard.tscn` com a composição de inimigos apropriada para o andar/Ato.
- Persistência contínua de PV entre combates: dano sofrido pelos heróis no tabuleiro reflete diretamente no `RunState` e na tela do mapa.
- Morte permanente na run (*Permadeath*): heróis mortos permanecem caídos e não entram no próximo combate.

### R3. Conteúdo e Mecânicas do Ato II (Túneis Vivos) (M5)
- Ambientes subterrâneos com visibilidade baseada em iluminação de tochas.
- Mecânica de casulos de quitina e ovos que eclodem se não forem destruídos.
- Mini-chefe `cigarra_ressonante` e combate com o chefe do Ato II `rainha_do_enxame` invocando ninhadas.

### R4. Os 3 Corações da Colmeia e a Batalha Final contra o Rei Isectum (M6)
- Nós especiais dos 3 Corações (`fase_09`, `fase_10`, `fase_11`): destruí-los aplica penalidades permanentes ao Rei Isectum.
- Boss Final `rei_isectum` ocupando 3x3 tiles na arena `fase_12`, com máquina de estados de 3 fases completas:
  * Fase 1: Trono de Âmbar (ataques ordenados à Guarda Real e queda do trono via cartas de Escavação).
  * Fase 2: Muralha Viva (arena dinâmica com bordas em miasma, rugido feromônico e esmagamento).
  * Fase 3: Coroa Quebrada (frenesi, duas ações por turno, fraqueza 2x a fogo e habilidade letal Devorar Essência).

### R5. Meta-Progressão Permanente & Ascensão (M7 & M8)
- Persistência em disco de Âmbar Real acumulado (`user://meta_save.json`).
- Tela de desbloqueio de novos heróis e cartas rúnicas no menu principal usando Âmbar Real.
- Sistema de Ascensão (1 a 10) ativado após a primeira vitória sobre o Rei Isectum.
- Telas de vitória épica e derrota detalhada com estatísticas da expedição.

## Acceptance Criteria

### Integridade e Execução
- [ ] O projeto executa sem erros ou warnings críticos no Godot 4.
- [ ] O fluxo completo de jogo Menu ➔ Nova Campanha ➔ Mapa ➔ Batalha ➔ Recompensa ➔ Fogueira/Forja ➔ Chefes de Ato ➔ Vitória/Derrota funciona sem travamentos.
- [ ] Todos os scripts standalone cumprem a diretriz de prevenção de execução infinita com Watchdog Timer.

### Regras Roguelike & Boss Fight
- [ ] O PV dos heróis persiste corretamente através dos nós do mapa e a morte permanente impede o uso do herói caído no mesmo ciclo de expedição.
- [ ] O Chefe Rei Isectum transiciona corretamente entre as 3 fases conforme sua vida é reduzida, respondendo à destruição prévia dos 3 Corações.
- [ ] O Âmbar Real é concedido no encerramento da expedição e desbloqueia novos heróis no quartel permanente.

### Verificação Automatizada (GUT)
- [ ] 100% dos testes GUT passam via linha de comando (`bash godot_project/run_gut_tests.sh`) com código de saída 0.
- [ ] Novas suítes de testes unitários cobrem o sistema de relíquias, seleção de recompensas, fases do Rei Isectum e persistência de meta-progressão.
