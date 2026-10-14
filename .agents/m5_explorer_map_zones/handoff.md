# Relatório de Investigação Visual & Arquitetura: Tabuleiro da Fortaleza & Painel de Recursos (Milestone 5)

## 1. Observation

A investigação baseou-se na análise comparativa da implementação de referência em Python (`src/states/cerco/draw_map.py`, `src/states/cerco/draw_panel.py`, `src/states/cerco/draw_ui.py`, `src/resolvedor_acoes.py`), do motor GDScript já migrado (`FortressBoard.gd`, `WorkshopEconomy.gd`, `CercoSyncRound.gd`, `CercoCombatJudge.gd`, `TacticalGrid.gd`, `EventBus.gd`, `GameManager.gd`), e dos assets gráficos em `assets/` e `godot_project/assets/`.

### 1.1 Mapeamento e Delineamento das 17 Zonas no Grid 20x20
- **Contrato de Dimensões e Cobertura**:
  - `FortressBoard.gd:18-20`: `GRID_WIDTH = 20`, `GRID_HEIGHT = 20`, `TOTAL_CELLS = 400`.
  - Partição exata e sem lacunas (`FortressBoard.gd:129-182`):
    1. **4 Torres de Vigia** (Cantos 4x4 = 16 células cada, total 64 células):
       - `ZONE_TORRE_NOROESTE`: `x in [0..3], y in [0..3]`
       - `ZONE_TORRE_NORDESTE`: `x in [16..19], y in [0..3]`
       - `ZONE_TORRE_SUDOESTE`: `x in [0..3], y in [16..19]`
       - `ZONE_TORRE_SUDESTE`: `x in [16..19], y in [16..19]`
    2. **4 Campos de Invasão / Spawns Externos** (Faixas de 2 células no perímetro exterior, excluindo torres; 12x2 = 24 células cada, total 96 células):
       - `ZONE_SPAWN_NORTE`: `x in [4..15], y in [0..1]`
       - `ZONE_SPAWN_SUL`: `x in [4..15], y in [18..19]`
       - `ZONE_SPAWN_OESTE`: `x in [0..1], y in [4..15]`
       - `ZONE_SPAWN_LESTE`: `x in [18..19], y in [4..15]`
    3. **4 Muralhas Perimetrais Defensivas** (Faixas de 2 células imediatamente internas aos spawns; 12x2 = 24 células cada, total 96 células):
       - `ZONE_MURALHA_NORTE`: `x in [4..15], y in [2..3]`
       - `ZONE_MURALHA_SUL`: `x in [4..15], y in [16..17]`
       - `ZONE_MURALHA_OESTE`: `x in [2..3], y in [4..15]`
       - `ZONE_MURALHA_LESTE`: `x in [16..17], y in [4..15]`
    4. **Câmara Central** (Núcleo 4x4 no centro, total 16 células):
       - `ZONE_CAMARA_CENTRAL`: `x in [8..11], y in [8..11]`
    5. **4 Quadrantes Internos (Oficinas & Pátio)** (Interior de 12x12 menos a câmara 4x4 = $144 - 16 = 128$ células divididas simetricamente em 32 células cada):
       - `ZONE_CARPINTARIA`: Quadrante Norte interno (32 células)
       - `ZONE_CURTUME`: Quadrante Sul interno (32 células)
       - `ZONE_FUNDICAO`: Quadrante Oeste interno (32 células)
       - `ZONE_PATIO_CENTRAL`: Quadrante Leste interno (32 células)
    - Total verificado: $64 + 96 + 96 + 16 + 128 = 400$ células. Testado e validado em `test_fortress_board.gd:69-96`.

- **Delineamento e Paleta Visual (Python `draw_map.py:240-257`, `448-454`, `759-773`)**:
  - `camara_central`: Paleta Ouro/Cristal `(105, 82, 18)`, contorno ouro `(235, 195, 30)`, rótulo `"CAMARA CENTRAL (CRISTAL ROXO)"`.
  - `carpintaria`: Paleta Verde Madeira `(32, 90, 28)`, contorno verde brilhante `(60, 200, 60)`, rótulo `"CARPINTARIA (MADEIRA)"`.
  - `curtume`: Paleta Marrom Couro `(120, 72, 28)`, contorno laranja `(220, 120, 40)`, rótulo `"CURTUME (COURO)"`.
  - `fundicao`: Paleta Aço Escuro `(70, 70, 88)`, contorno azul aço `(120, 180, 240)`, rótulo `"FUNDICAO (METAL)"`.
  - `patio`: Paleta Azul Real `(28, 60, 120)`, contorno azul ciano `(60, 160, 240)`, rótulo `"PATIO (PEDREGULHOS)"`.
  - `muralhas`: Paleta Cinza Rocha `(90, 92, 108)`, contorno reforçado.
  - `torres`: Paleta Pedra Fortificada `(70, 72, 92)`, topo destacado `(180, 180, 220)`.
  - `spawns/exterior`: Paleta Terreno Escuro `(30, 52, 22)` / `(18, 28, 12)`.
  - Pilhas físicas de recursos no mapa (`draw_map.py:461-755`):
    * Madeira empilhada em toras com corte de anéis de crescimento em `(9, 13)`.
    * Lingotes de metal em pirâmide isométrica com reflexo em `(5, 9)`.
    * Rolos de couro curtido em `(9, 5)`.
    * Pilha de pedregulhos em `(13, 9)`.
    * Aglomerado de cristais violeta multifacetados em `(9, 9)` na câmara central.

### 1.2 Níveis de Elevação (0, 1 e 2)
- Em `FortressBoard.gd:223-237`:
  - Elevação 0: Campos de invasão (`ALL_SPAWNS`), Oficinas (`ALL_WORKSHOPS`), Pátio Central e Câmara Central.
  - Elevação 1: 4 Muralhas Perimetrais (`ALL_WALLS`).
  - Elevação 2: 4 Torres de Vigia (`ALL_TOWERS`).
- Em `draw_map.py:58, 338-385`:
  - Deslocamento de projeção: `sy = (rx + ry) * (TH // 2) - el * ES + CY`. A elevação desloca verticalmente a célula para cima por `el * ES` pixels (8px a 16px por nível).
  - Extrusão 2.5D: quando `thick = el * ES > 0`, são traçados polígonos verticais nas laterais visíveis (`left_pts`, `right_pts`) sombreados com mortar lines horizontais e juntas alternadas de tijolos de alvenaria.
- Impacto mecânico no combate:
  - `CercoCombatJudge.gd:213-230`: Unidades em Torres (Elevação 2) podem disparar balestras contra Muralhas (Elevação 1), Spawns (Elevação 0) e Engenhos de Cerco externos com vantagem ou alcance expandido.
  - `TacticalGrid.gd:32-37`: Barreira de muralha fornece cobertura total ou cobertura parcial (+3 a +5 AC).

### 1.3 Integridade e Ruptura de Muralhas (Breaches)
- `FortressBoard.gd:10-12, 187-188, 328-387`:
  - Cada muralha possui `DEFAULT_WALL_MAX_HP = 100` e emite os sinais `wall_damaged(wall_id, amount, remaining_hp)`, `wall_repaired(wall_id, amount, new_hp)` e `wall_breached(wall_id)`.
  - Condição de Ruptura: `hp <= 0` ativa `is_wall_breached(wall_id) == true`.
- Estados visuais requeridos:
  * Intacta (76% a 100%): Textura de cantaria sólida, alvenaria limpa, barra verde de HP.
  * Danificada (26% a 75%): Rachaduras superficiais, esfarelamento de argamassa, barra amarela de HP.
  * Crítica (1% a 25%): Fraturas profundas, aviso piscante em vermelho escuro, fumaça sutil, barra vermelha de HP.
  * Rompida / Brecha (0 HP): Ruína desmoronada, altura visual colapsada para elevação de entulho/rocha (`TERRENO_DIFICIL`), partículas de poeira e brasas, banner de perigo "BRECHA NA MURALHA", e liberação do caminho de invasão direta para as oficinas (`get_next_invasion_zones`).

### 1.4 Destaques Táticos de Células e Zonas (Highlights)
- Movimentação (`MODO_MOVER`, `draw_map.py:808-814`):
  - Células alcançáveis calculadas por AStar2D (`TacticalGrid.find_path`) limitadas aos pontos de movimento disponíveis (`pontos_movimento`).
  - Renderização via diamante pulsante (`_draw_celula_tactica`) com preenchimento translúcido esmeralda `(0, 150, 0, 45)`, borda brilhante `(100, 255, 100)` e cantoneiras brancas.
  - Trilha visual dinâmica A* com linha conectando herói ao cursor com dots concêntricos pulsantes e badge `"🚶 X PM"` (`draw_map.py:1047-1076`).
- Trabalho / Reparo de Muralha (`MODO_TRABALHAR`):
  - Destaque em ouro/âmbar `(255, 200, 50, 70)` nas muralhas danificadas elegíveis para conserto via gastos de madeira e metal.
- Produção de Oficina:
  - Destaque na zona inteira com a cor temático-produtiva (Carpintaria = verde, Curtume = couro, Fundição = azul, Pátio = ciano).
- Combate à Distância / Balestra de Torre:
  - Quando a unidade ativa está na Torre (elevação 2), as zonas alvo elegíveis (`ALL_WALLS`, `ALL_SPAWNS`, Catapulta) pulsam em vermelho carmesim `(255, 0, 0, 60)`.
- Hover do Mouse:
  - Brilho translúcido branco suave `(255, 255, 255, 30)` e borda nítida de 1px na célula sob o cursor, exibindo tooltip com coordenadas e dados da célula.

### 1.5 Placar de Recursos & Status da Rodada
- Recursos Monitorados (`WorkshopEconomy.gd:26-63`):
  * Madeira (`wood` / `madeira`): Verde `#64C85A`, reparo de muralhas e upgrades.
  * Couro (`leather` / `couro`): Âmbar `#D2963C`, armaduras e upgrades.
  * Metal (`metal` / `ferro`): Azul Aço `#A0B4F0`, reparo de muralhas e armas de cerco.
  * Cristais (`crystal` / `cristais`): Violeta `#D28CFF`, recurso místico de vitória e sinergia suprema.
  * Pontos de Ação (`ap`): Ouro Imperial `#FFD700`, ativação de ações livres e compras imediatas.
- 4 Camadas de Sincronia Co-op (`CercoSyncRound.gd:25-35`):
  1. `LAYER_MARCHA` (Azul / Ícone de Asas / Botas 🏃)
  2. `LAYER_TRABALHO` (Âmbar / Ícone de Martelo 🔨)
  3. `LAYER_ESCAVACAO` (Ciano / Ícone de Picareta ⛏️)
  4. `LAYER_COMBATE` (Vermelho / Ícone de Espadas Cruzadas ⚔️)
- Reatividade a Sinais:
  * `WorkshopEconomy.resources_updated(wood, leather, metal, crystal, ap)`
  * `WorkshopEconomy.resource_added(type, amount, new_total)`
  * `WorkshopEconomy.resource_spent(type, amount, remaining)`
  * `WorkshopEconomy.wall_repaired_with_resources(wall_id, wood_spent, metal_spent, new_hp)`
  * `CercoSyncRound.layer_started(layer_name)` e `CercoSyncRound.layer_resolved(layer_name, summary)`
  * `CercoSyncRound.supreme_synchrony_triggered(badge, crystal_bonus)`

---

## 2. Logic Chain

1. **Da representação analítica de 400 células para a exibição de cena**:
   - `FortressBoard.gd` fornece o mapeamento rígido $x, y \to \text{zone\_id}$ e elevação $0, 1, 2$.
   - Para manter total separação entre motor de regras e visualização (SOLID), o componente visual `FortressBoardView.gd` deve consultar `FortressBoard` via interface de leitura desacoplada, sem poluir `FortressBoard` com código de renderização do Godot (`Node2D`, `CanvasItem`, `_draw`).

2. **Da elevação em números inteiros para percepção tridimensional (2.5D)**:
   - Em uma visão 2D de cima para baixo ou isométrica, uma célula na coordenada $(x, y)$ com elevação $E \in \{0, 1, 2\}$ é deslocada visualmente por $\Delta y = -E \times \text{ELEVATION\_OFFSET}$.
   - Para células de muralha ($E = 1$) e torre ($E = 2$), o espaço aberto abaixo da superfície elevada deve ser preenchido por um polígono vertical ("skirt"/mureta) desenhado em camadas z-index inferiores para criar o volume sólido dos baluartes e torres.

3. **Da integridade da muralha para a representação de ruína**:
   - Quando `FortressBoard.set_wall_hp` ou `damage_wall` reduz o HP para 0, é emitido `wall_breached`.
   - O componente visual deve conectar-se a esse sinal e atualizar o estado daquela muralha: alterar os polígonos/sprites de cantaria intacta para textura de escombros/entulho e rebaixar a silhueta visual para o nível do solo, indicando visualmente aos jogadores que os Isectum agora podem atravessar aquele setor.

4. **Da economia reativa para a atualização contínua do HUD**:
   - `WorkshopEconomy` emite `resources_updated` sempre que ocorre gasto, ganho ou reparo.
   - O componente `ResourceScoreboard.gd` liga-se a esse sinal no momento da inicialização (`bind_economy(economy)`). Dessa forma, qualquer alteração gerada por cartas, produção de oficinas ou eventos de invasão reflete instantaneamente nos contadores numéricos sem necessidade de polling de frames (`_process`).

5. **Da resolução de rodada simultânea para o rastreador de camadas**:
   - O `CercoSyncRound` resolve as ações registradas sequencialmente em 4 passos: Marcha $\to$ Trabalho $\to$ Escavação $\to$ Combate.
   - O HUD precisa exibir aos jogadores qual camada está ativa no momento. Ao escutar `layer_started` e `layer_resolved`, o `ResourceScoreboard` destaca o ícone da camada em execução e acende um indicador verde com checkmark ao concluir, dando clareza ao ritmo do turno cooperativo.

6. **Da testabilidade headless para a arquitetura de classes**:
   - Se os componentes visuais dependerem criticamente de janelas do sistema operacional, contextos OpenGL ou recursos de textura não disponíveis no modo CLI headless, o comando de teste `./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit` falhará.
   - Logo, cálculos de coordenadas (`grid_to_screen`, `screen_to_grid`), formatação de textos do scoreboard, detecção de cores de highlight e armazenamento de estados de exibição devem residir em métodos puramente matemáticos e manipuladores de dicionários/vetores que funcionem independentemente da renderização de tela.

---

## 3. Caveats

1. **Modo de Renderização do Godot 4**: O projeto utiliza o renderizador Compatibility (OpenGL 3.3 / WebGL 2.0). Soluções com shaders excessivamente pesados ou render passes complexos de 3D devem ser evitadas em favor de `CanvasItem._draw()`, `TileMapLayer` e instâncias modulares 2D de nós, garantindo paridade em WebAssembly e Desktop.
2. **Dependência de Texturas de Terreno**: Embora os arquivos `terreno_*.png` existam em `godot_project/assets/images/environment/`, a arquitetura deve prever fallback vetorial automático (desenho procedural de polígonos coloridos com contornos) para o caso de execução headless ou assets temporariamente descarregados.
3. **Escopo do Investigador**: Sendo este um papel de explorador exclusivamente em modo somente-leitura, nenhuma alteração de código foi realizada nos diretórios de fontes (`src/`, `godot_project/scripts/`, `godot_project/scenes/`). As propostas técnicas foram desenhadas de forma puramente modular e prontas para consumo pelos implementadores dos marcos M5.

---

## 4. Conclusion

A representação visual do Cerco da Fortaleza e seu painel de recursos exige três componentes principais desacoplados:

### 4.1 Componente: `FortressBoardView.gd` (`res://scripts/cerco/FortressBoardView.gd`)
- Herda de `Node2D`.
- Responsável por:
  * Gerenciamento de coordenadas e projeção: converte coordenadas de grade 20x20 $(x, y)$ em coordenadas globais de tela $(sx, sy)$ com suporte a escala/zoom e elevação.
  * Renderização em camadas ordenadas por Y/Z-index:
    1. `TerrainFloor`: Células térreas (0 a 19, 0 a 19) com cores e texturas zonais.
    2. `WallExtrusion`: Muretas verticais 2.5D para muralhas (elevação 1) e torres (elevação 2).
    3. `ZoneOverlay`: Contornos zonais, faixas de perigo nos campos de spawn e halos de seleção.
    4. `StockpileVisuals`: Pilhas de toras de madeira, lingotes de ferro, rolos de couro e cristais renderizados conforme o estado dos recursos.
    5. `BreachVisuals`: Máscaras visuais de ruptura de muralhas.
  * API pública limpa e testável:
    - `grid_to_screen(grid_pos: Vector2i, elevation: int = 0) -> Vector2`
    - `screen_to_grid(screen_pos: Vector2) -> Vector2i`
    - `get_zone_color(zone_id: String) -> Color`
    - `get_elevation_offset_px(elevation: int) -> float`

### 4.2 Componente: `ZoneOverlay.gd` (`res://scripts/cerco/ZoneOverlay.gd`)
- Herda de `Node2D` (filho de `FortressBoardView`).
- Responsável por todos os efeitos de highlight tático:
  * `highlight_reachable_movement(cells: Array[Vector2i])`: renderiza os diamantes táticos verdes pulsantes com cantoneiras de precisão.
  * `highlight_wall_repairs(wall_ids: Array[String], can_afford: bool)`: destaca muralhas selecionadas para restauração.
  * `highlight_tower_targets(tower_id: String, target_zones: Array[String])`: realça setores sob alcance de disparo das balestras.
  * `draw_breadcrumb_path(path: Array[Vector2i], cost: int)`: desenha a linha de navegação A* com círculos de nós e o badge flutuante de passos.
  * `set_hover_cell(cell: Vector2i)`: desenha a borda iluminada suave na célula ativa.
  * `update_wall_breach(wall_id: String, is_breached: bool)`: atualiza o estado de brecha das muralhas.

### 4.3 Componente: `ResourceScoreboard.gd` (`res://scripts/cerco/ResourceScoreboard.gd`)
- Herda de `Control` (`PanelContainer`).
- Painel superior ou lateral no padrão Dark Fantasy HUD:
  * `ResourceBar`: Mostradores individuais para Madeira, Couro, Metal, Cristais e AP, com ícones temáticos e labels com suporte a animação de pulso ao mudar de valor.
  * `RoundThreatWidget`: Indicador numérico da rodada atual e medidor de ameaça com status dos 4 pontos cardeais de spawn.
  * `SynchronyStepTracker`: Visualizador dos 4 passos sequenciais (Marcha, Trabalho, Escavação, Combate) que reage aos sinais do `CercoSyncRound`.
  * `WallIntegrityMiniBars`: Quatro micro-barras de vida dedicadas às muralhas Norte, Sul, Leste e Oeste, reagindo aos sinais de dano e reparo.
  * `SynergyNotificationBanner`: Banner de exibição de bônus de Sinergia de Equipe e Sincronia Suprema (+2 Cristais).

---

## 5. Verification Method

Para verificar independentemente todas as conclusões e validar os componentes projetados:

1. **Execução Headless da Suíte Canônica GUT**:
   ```bash
   cd /home/anderson/Documents/projeto/RPG-battle/godot_project
   ./bin/godot --headless -s addons/gut/gut_cmdln.gd -gexit
   ```
   - Condição de Sucesso: 100% de aprovação (339 testes atualmente passando, exit code 0, 0 memory leaks).

2. **Verificação de Cobertura das 17 Zonas no Tabuleiro**:
   - Inspecionar `godot_project/scripts/cerco/FortressBoard.gd` e `godot_project/test/unit/test_fortress_board.gd`.
   - Garantir que qualquer nova classe visual (`FortressBoardView.gd`) mantenha paridade exata com as 400 células e as 17 constantes `ZONE_*`.

3. **Verificação da Reatividade da Economia e Sincronia**:
   - Inspecionar `godot_project/scripts/cerco/WorkshopEconomy.gd` e `godot_project/scripts/cerco/CercoSyncRound.gd`.
   - Validar que o `ResourceScoreboard` conecta-se a `resources_updated`, `wall_repaired_with_resources`, `layer_started`, `layer_resolved` e `supreme_synchrony_triggered` sem causar warnings ou referências nulas no modo headless.

4. **Critérios de Invalidação**:
   - Se qualquer cálculo de grade resultar em células sobrepostas ou vazias fora do range 0..19.
   - Se instanciar `FortressBoardView.new()` ou `ResourceScoreboard.new()` em um teste GUT headless causar falha de DisplayServer ou leak no ObjectDB.
