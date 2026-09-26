# Handoff Report: Levantamento de Entidades, Heróis, Castas Isectum e Modo Cerco

**Agente**: `survey_explorer_content`  
**Tipo**: Hard Handoff (Tarefa Concluída)  
**Destinatário**: Orchestrator / Tracks de Implementação Godot 4  

---

## 1. Observação

Foram inspecionados diretamente os seguintes arquivos de código-fonte, dados e assets:

1. **Dados de Personagens e Classes**:
   - `dados/personagens.json`: Contém os atributos de 9 classes básicas (`Guerreiro`, `Mago`, `Ladino`, `Arqueiro`, `Barbaro`, `Clerigo`, `Paladino`, `Druida`, `Bruxo`), 8 monstros/chefes (`ReiGoblin`, `LordeLich`, `DragaoAnciao`, `Goblin`, `Esqueleto`, `Kobold`, `Sienna`, `SiennaPhoenix`) e 11 heróis protagonistas (`Novak` l.84, `Koema` l.89, `Rilem` l.94, `Yukito` l.99, `Aquele` l.118, `Stark` l.123, `Elden` l.128, `Doom` l.133, `Gruu` l.138, `Kuro` l.143, `Darwin` l.148).
   - `src/personagens/protagonistas.py`: Define classes dos 5 primeiros heróis (`Novak` l.3, `Koema` l.47, `Rilem` l.90, `Yukito` l.130, `Aquele` l.165).
   - `src/personagens/novos_personagens.py`: Define classes dos 6 heróis adicionais (`Stark` l.4, `Elden` l.37, `Doom` l.71, `Gruu` l.105, `Kuro` l.137, `Darwin` l.169) e o aliado elite `FilhoDoImperador` (Príncipe Lysander, l.203).
   - `src/personagens/personagem_base.py`: Implementa mecânicas D&D 5e: modificadores `(stat - 10)//2`, bônus de proficiência `1 + ceil(nivel / 4)`, AC dinâmico com perks (`muralha_escudos`, `mimetismo`), ações básicas (`Dash`, `Disengage`, `Dodge`, `Help`, `Grapple`, `Shove`) e Death Saving Throws (`realizar_teste_morte` l.769-804: Nat 20 revive com 1 HP, Nat 1 adiciona 2 falhas, $\ge 10$ sucesso, $< 10$ falha, 3 falhas = morte, dano inconsciente = 1 falha).

2. **As 24 Castas de Insetos Isectum**:
   - `src/cerco_isectum.py:286-383`: Dicionário `DADOS_INIMIGOS` lista exatamente as 24 castas:
     `vespa_cacadora`, `louva_deus`, `viuva_canibal`, `escaravelho_necrofago`, `besouro_unicornio`, `gafanhoto_praga`, `carrapato_vampiro`, `libelula_blindada`, `besouro_gorgulho`, `cigarra_ressonante`, `enxame_rainha`, `vagalume_sombras`, `larva_carniceira`, `tarantula_golias`, `formiga_correicao`, `aranha_clepto`, `centopeia_olhos`, `abelha_tecela`, `mariposa_esfinge`, `efemera_mimetica`, `vespa_joia`, `viuva_negra`, `besouro_rinoceronte`, `mosca_tse_tse`.
   - `src/castas_isectum.py`:
     - `INSETOS_BOSS` (l.97-105): 6 bosses capturáveis com efeito invertido (`libelula_blindada`, `enxame_rainha`, `viuva_canibal`, `vespa_cacadora`, `mosca_tse_tse`, `gafanhoto_praga`).
     - `aplicar_efeito_inseto` (l.561-970): Lógica completa de execução ativa para cada um dos 24 insetos.
     - `CARTAS_DEFESA` (l.18-51) e `CARTAS_RUNA` (l.56-92): Ações táticas de suporte e reação aos insetos.
   - `assets/images/characters/monsters/isectum/`: Contém os 24 arquivos `.png` com o nome exato de cada casta, além de `brutamonte.png` e `infiltrador.png`.

3. **Modo Cerco contra Isectum & Deckbuilding**:
   - `src/cerco_isectum.py`: Define `CARTAS_BASICAS` (12 cartas por herói), catálogo de upgrades `CARTAS_UPGRADE_AMARELO`, `CARTAS_UPGRADE_CINZA`, `CARTAS_UPGRADE_VERMELHO`, fluxo de invasores e regras de catapultas e torres de assalto.
   - `src/states/cerco/round_simultaneo.py`:
     - Resolução em camadas: `CAMADA_ORDEM = ["movimento", "trabalho", "escavacao", "upgrade"]`.
     - Sinergia de 2+ heróis: Movimento (+1 passo), Trabalho (+1 recurso), Escavação (-2 pedregulhos), Upgrade (+1 cristal).
     - Sincronia Suprema / Perfeita: Todos os 3+ heróis com mesmo tipo $\rightarrow$ +2 Cristais Roxos.
     - Pressão crescente (Rounds 1, 2, 3+) e Vantagem por Velocidade (primeiro a esgotar mão ganha +1 carta no próximo turno).
   - `src/states/cerco/draw_cards.py`: Renderização do leque (Fan Arc Layout: `fan_arc_y = int((offset_center ** 2) * 1.6)`, elevação no hover `deslocamento_y = -30`, badges M, T, E e gemas com moldura chanfrada).
   - `src/resolvedor_acoes.py`: Mapeamento das 9 zonas do grid 20x20 (`camara_central`, `carpintaria`, `curtume`, `fundicao`, `patio`, 4 muralhas, 4 torres, 4 campos externos), pathfinding com terrenos/elevações, regras de trabalho de recursos (`madeira`, `couro`, `metal`), escavação de pedregulhos e mercado de upgrades (5 slots com queima permanente de carta).
   - `src/juiz_combate.py`: Dado D6 customizado (impactos físicos e disparos), combate melee (2 impactos = 1 dano) e ranged a partir de torres (1 disparo = 1 dano).

---

## 2. Cadeia Lógica

1. **Atributos dos Heróis**: Como observado em `dados/personagens.json` e `src/personagens/protagonistas.py` / `novos_personagens.py`, todos os 11 heróis herdam de `Personagem`, que resolve estatísticas, modificadores D&D 5e e death saves de forma padronizada. Isso viabiliza criar um único script `CharacterData.gd` (`Custom Resource`) no Godot 4 com campos tipados e dicionário de habilidades, instanciável via `.tres` para cada um dos 11 heróis.
2. **Assets dos Heróis**: Em `src/config.py:333-360`, 7 heróis possuem spritesheets 4x4 de 256x256 em `assets/images/characters/animation/processed/` (`aquele`, `stark`, `elden`, `doom`, `gruu`, `kuro`, `darwin`), enquanto os outros 4 (`Novak`, `Koema`, `Rilem`, `Yukito`) utilizam sprites em `assets/images/characters/heroes/`. A cena `Character.tscn` no Godot deve suportar tanto sprites estáticos (`Sprite2D`) quanto folhas animadas (`AnimatedSprite2D` / `hframes=4, vframes=4`).
3. **Paridade das 24 Castas Isectum**: Como todas as 24 castas já possuem um dicionário estruturado em `DADOS_INIMIGOS` e funções de resolução ativa em `castas_isectum.py:aplicar_efeito_inseto`, a migração para GDScript pode portar a tabela de efeitos diretamente como um `Dictionary` ou enum `IsectumCasteId`, mantendo os mesmos nomes, emojis, custos, efeitos e sprites individuais de `assets/images/characters/monsters/isectum/`.
4. **Resolução de Sincronia Co-op**: O sistema de sincronia em `round_simultaneo.py` é desacoplado do loop de renderização Pygame — opera através de um dicionário de cartas selecionadas e acúmulo de deltas de estado. Isso se traduz com precisão para uma classe pura em GDScript (`CercoSyncRound.gd`), emitindo sinais (`EventBus.card_selected`, `EventBus.synergy_triggered`, `EventBus.round_resolved`).
5. **Ações Livres e Grid**: A lógica de `resolvedor_acoes.py` (movimentação com custos de elevação, trabalho em oficinas, escavação no pátio e compra no mercado) depende de coordenadas 20x20 e zonas lógicas. O uso do `AStar2D` nativo do Godot 4 mapeia diretamente os custos de terreno (`normal=1`, `dificil=2`, `parede=bloqueado`, delta de elevação).

---

## 3. Ressalvas (Caveats)

1. **Variabilidade de Resolução de Assets de Heróis**: 7 heróis possuem spritesheets 256x256 processados (`processed/*.png`), enquanto 4 possuem portraits/sprites de resoluções variadas em `heroes/*.png`. Recomenda-se normalizar a exibição na cena Godot `Character.tscn` através de um nó de pivot ou scaling proporcional.
2. **Multiplayer WebSocket vs Modo Solo**: No Python, o Diretor Isectum roda localmente via `turno_diretor_ia()` no modo solo ou via comandos manuais no modo versus. Na migração co-op para Godot 4, o servidor FastAPI existente (`src/server/protocol.py`) sincroniza as ações dos jogadores e o avanço dos rounds; a lógica do Diretor IA deve ser executável tanto no cliente offline quanto espelhada pelo servidor.
3. **Nenhum código-fonte do jogo foi modificado neste turno**: Em estrita conformidade com o papel de Teamwork Explorer, esta investigação foi estritamente de leitura, pesquisa e catalogação documental.

---

## 4. Conclusão

O ecossistema de entidades, heróis, insetos Isectum e mecânicas do modo Cerco está completamente inventariado e documentado em `.agents/survey_explorer_content/analysis.md`.
Todos os 11 heróis, o NPC elite Príncipe Lysander, as 24 castas Isectum, os 4 tipos de cartas de Cerco, os combos de sinergia e as regras de economia da fortaleza possuem especificações matemáticas e comportamentais claras para guiar as tracks de Arquitetura, Regras, Entidades, Deckbuilder e UI no Godot 4 sem ambiguidades.

---

## 5. Método de Verificação

Para verificar independentemente todas as afirmações deste relatório:

1. **Inspeção de Código e Arquivos**:
   ```bash
   # Verificar os 11 heróis no JSON de personagens:
   grep -E '"(Novak|Koema|Rilem|Yukito|Aquele|Stark|Elden|Doom|Gruu|Kuro|Darwin)"' dados/personagens.json
   
   # Verificar a contagem de 24 castas Isectum:
   python3 -c "from src.cerco_isectum import DADOS_INIMIGOS; print(len(DADOS_INIMIGOS), list(DADOS_INIMIGOS.keys()))"
   
   # Verificar os 24 assets PNG correspondentes:
   ls assets/images/characters/monsters/isectum/*.png | wc -l
   ```

2. **Execução da Suíte Canônica de Testes Python**:
   ```bash
   python3 -m unittest tests/test_cerco_rules.py
   ```
   *Condição de invalidação*: Se qualquer teste de regras de oficina, combate melee em zona, ataques de torre ou escavação falhar, a especificação das regras do Cerco deverá ser reavaliada.
