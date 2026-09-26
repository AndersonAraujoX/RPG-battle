# Relatório Técnico Completo: Entidades, Heróis, Castas Isectum e Modo Cerco

**Data**: 2026-09-26  
**Autor**: `survey_explorer_content`  
**Escopo**: Levantamento técnico, catalogação e arquitetura de dados das entidades, classes de heróis (11 protagonistas), 24 castas de insetos Isectum e mecânicas completas do modo Cerco contra Isectum para migração Godot 4.

---

## 1. Sistema Base de Entidades & Regras D&D 5e

### 1.1 Classe Base `Personagem` (`src/personagens/personagem_base.py`)
A entidade base encapsula a matemática clássica de D&D 5ª Edição:
- **Atributos Principais**:
  - `Força` (For), `Destreza` (Des), `Constituição` (Con), `Inteligência` (Int), `Sabedoria` (Sab), `Carisma` (Car).
  - Modificador de Atributo: `mod = (valor - 10) // 2`.
- **Classe de Armadura (AC)**:
  - Base definida em `dados/personagens.json` ou sobrescrita pela subclasse.
  - Armadura equipada substitui ou adiciona ao AC base (`self.armadura_equipada.bonus_ac`).
  - AC Dinâmica (`calcular_ac_dinamico`):
    - Perk *Muralha de Escudos*: +2 AC se houver aliado adjacente (distância $\le 1.5$).
    - Perk *Mimetismo*: +4 AC se posicionado em terreno com cobertura natural (`TERRENO_FLORESTA`, `TERRENO_ROCHA`, `TERRENO_BARRIL`).
- **Proficiência & Ataque**:
  - Bônus de Proficiência: `1 + math.ceil(nivel / 4)`.
  - Bônus de Ataque (`bonus_ataque`): `bonus_proficiencia + status_efeitos.bonus_ataque_fixo` (ou `_bonus_ataque_override`).
  - Rolagem de Ataque: `1d20 + bonus_ataque` vs AC do alvo. Crítico natural em 20.
  - Vantagem / Desvantagem: 2d20 (pega o maior ou menor).
- **Resoluções de Ação Básica**:
  - `Ação de Disparada (Dash)`: Aplica status `Dash`, dobra movimento no turno.
  - `Desengajar (Disengage)`: Aplica status `Desengajar`, concede imunidade a ataques de oportunidade.
  - `Esquiva (Dodge)`: Aplica status `Esquiva`, atacantes sofrem desvantagem.
  - `Ajuda (Help)`: Concede vantagem ao próximo ataque aliado contra o alvo.
  - `Agarrar (Grapple)`: Teste resistido `d20 + mod_for` vs `d20 + max(mod_for, mod_des)`. Alvo recebe status `Agarrado`.
  - `Derrubar (Shove)`: Teste resistido Atletismo/Acrobacia. Alvo recebe status `Caído (Prone)`.
- **Economia de Turno**:
  - `movimento_realizado`: Booleano para ação de movimento.
  - `acao_realizada`: Booleano para ação padrão.
  - `acao_bonus_realizada`: Booleano para ação bônus.
  - `iniciar_turno()`: Reseta flags, decresce cooldowns (`tick_cooldowns`), regenera +1 Mana/Energia (`tick_recursos`).
- **Testes Contra a Morte (Death Saving Throws)** (`personagem_base.py:769-804`):
  - Quando HP atinge 0, herói entra no estado `INCONSCIENTE`.
  - A cada turno inconsciente, rola 1d20:
    - **20 Natural**: Acorda imediatamente com 1 HP (`NORMAL`), reseta contadores de morte para 0.
    - **1 Natural**: Sofre 2 falhas imediatamente.
    - **$\ge 10$**: 1 Sucesso (com 3 sucessos $\rightarrow$ `ESTABILIZADO`).
    - **$< 10$**: 1 Falha (com 3 falhas $\rightarrow$ `MORTO`).
    - Dano sofrido inconsciente adiciona 1 falha direta (3 falhas $\rightarrow$ `MORTO`).
    - Perk *Última Linha*: Uma vez por batalha, recusa a cair e fixa HP em 1.

---

## 2. Inventário dos 11 Heróis Protagonistas

Fontes: `dados/personagens.json`, `src/personagens/protagonistas.py`, `src/personagens/novos_personagens.py`, `src/config.py`.

| Herói | Papel / Arquétipo | HP / AC / Speed | Recurso Principal | Dano / Alcance | Habilidades & Efeitos | Mapeamento de Asset |
|---|---|---|---|---|---|---|
| **Novak** | Tank Agressivo | 50 HP / 18 AC / 4 Vel | Cooldowns (sem custo) | 1d10 Cortante / Alc. 1 | - `Provocar` (CD 3, Raio 3): Força inimigos a focarem Novak.<br>- `Golpe Flamejante` (CD 2, Alc. 1): +5 Dano extra de Fogo. | `assets/images/characters/heroes/Novak.png` |
| **Koema** | Jack-of-all-trades | 35 HP / 12 AC / 3 Vel | Mana (30 MP) | 1d8 Mágico / Alc. 6 | - `Truque Sujo` (5 MP, Alc. 1): Causa dano e debuff de ataque no alvo.<br>- `Primeiros Socorros` (5 MP, Alc. 1): Cura 10 HP em aliado. | `assets/images/characters/heroes/Koema.png` |
| **Rilem** | Suporte / Estrategista | 38 HP / 16 AC / 5 Vel | Energia (40 EP) | 1d6 Perfurante / Alc. 8 | - `Comando Tático` (10 EP, Alc. Global): Aumenta ataque de todos os aliados.<br>- `Quebrar Defesa` (10 EP, Alc. 6): Reduz a AC do inimigo. | `assets/images/characters/heroes/Rilem.png` |
| **Yukito** | Mago Artilharia / AoE | 42 HP / 18 AC / 3 Vel | Mana (50 MP) | 1d8 Cortante / Alc. 8 | - `Tempestade de Fogo` (15 MP, Alc. 8, Raio 3x3): 10 Dano de Fogo em área.<br>- `Explosão Arcana` (10 MP, Alc. 8): 15 Dano Mágico em alvo único. | `assets/images/characters/heroes/Yukito.png` |
| **Aquele** | Guerreiro Híbrido | 48 HP / 17 AC / 4 Vel | Cooldowns | 1d10 Cortante / Alc. 1 | - `Investida` (CD 2, Alc. 2): Avança causando +4 Dano extra Esmagamento.<br>- `Golpe Preciso` (CD 1, Alc. 1): +6 Dano extra Perfurante com alta precisão. | `assets/images/characters/heroes/Aquele.png` & `assets/images/characters/animation/processed/aquele.png` (256x256, 4x4) |
| **Stark** | Paladino / Tanque Sagrado | 55 HP / 19 AC / 3 Vel | Cooldowns | 1d10 Esmagamento / Alc. 1 | - `Golpe Poderoso` (CD 2, Alc. 1): +8 Dano extra Esmagamento.<br>- `Escudo Sagrado` (CD 3, Self): Concede bônus de AC por 1 turno. | `assets/images/characters/animation/processed/stark.png` (256x256, 4x4) |
| **Elden** | Mago / Clérigo Arcano | 32 HP / 12 AC / 3 Vel | Mana (40 MP) | 1d6 Mágico / Alc. 8 | - `Raio Arcano` (8 MP, Alc. 8): +12 Dano extra Mágico.<br>- `Toque Curativo` (6 MP, Alc. 2): Cura 15 HP em aliado. | `assets/images/characters/animation/processed/elden.png` (256x256, 4x4) |
| **Doom** | Ladino / Assassino | 36 HP / 15 AC / 5 Vel | Energia (40 EP) | 1d8 Necrótico / Alc. 1 | - `Ataque Sombrio` (8 EP, Alc. 1): +10 Dano extra Necrótico furtivo.<br>- `Passos das Sombras` (5 EP, Self): Buff de velocidade e esquiva. | `assets/images/characters/animation/processed/doom.png` (256x256, 4x4) |
| **Gruu** | Bárbaro Furioso | 60 HP / 12 AC / 4 Vel | Cooldowns | 1d12 Esmagamento / Alc. 1 | - `Fúria da Besta` (CD 4, Self): Entra em fúria dobrando o dano causado.<br>- `Esmagar` (CD 2, Alc. 1): +14 Dano extra Esmagamento, ignora armadura. | `assets/images/characters/animation/processed/gruu.png` (256x256, 4x4) |
| **Kuro** | Ninja / Duelista Veloz | 40 HP / 16 AC / 5 Vel | Cooldowns | 1d8 Perfurante / Alc. 1 | - `Golpe Veloz` (CD 1, Alc. 1): Ataque duplo rápido com +6 Dano Perfurante.<br>- `Desviar` (CD 3, Self): Desvia com 100% de certeza do próximo ataque. | `assets/images/characters/animation/processed/kuro.png` (256x256, 4x4) |
| **Darwin** | Druida da Natureza | 44 HP / 14 AC / 4 Vel | Mana (35 MP) | 1d8 Natural / Alc. 6 | - `Chuva de Espinhos` (7 MP, Alc. 6): +10 Dano extra Perfurante à distância.<br>- `Cura Druídica` (10 MP, AoE Aliados): Cura 10 HP em todos aliados na área. | `assets/images/characters/animation/processed/darwin.png` (256x256, 4x4) |

### 2.1 Aliado Especial / NPC de Elite do Cerco
- **Príncipe Lysander (`FilhoDoImperador`)** (`novos_personagens.py:203-277`):
  - HP: 80, AC: 18, Velocidade: 5, Alcance: 2, Mana: 50.
  - Controlado por IA autônoma para defesa tática da fortaleza.
  - Habilidades:
    - `Golpe Imperial` (10 MP, Alc. 2): +20 Dano extra Cortante, penetra armadura.
    - `Escudo Arcano` (8 MP, Self): Projeta barreira mágica com grande buff de AC.
    - `Presença Imperial` (CD 4, Alc. 3 AoE): Concede +2 AC e +4 Ataque a todos os aliados próximos.
    - `Raio Imperial` (15 MP, Alc. 8): +16 Dano extra de Relâmpago e atordoa o alvo.

### 2.2 Classes Genéricas, Mercenários e Monstros do Ecossistema
- **Classes Genéricas**: Guerreiro, Mago, Ladino, Arqueiro, Bárbaro, Clérigo, Paladino, Druida, Bruxo.
- **Mercenários**: Mercenário Melee, Mercenário Arqueiro, Mercenário Minerador.
- **Minions**: Goblin (7 HP, 15 AC), Esqueleto (13 HP, 13 AC, vulnerável a Esmagamento 2.0x), Kobold (5 HP, 12 AC).
- **Chefes**:
  - `ReiGoblin`: 250 HP, 18 AC, Vel 5, 2d6 dano.
  - `LordeLich`: 280 HP, 17 AC, Vel 4, 3d6 Necrótico, Imune a Frio e Veneno.
  - `DragaoAnciao`: 400 HP, 22 AC, Vel 4, 3d10 Fogo, Imune a Paralisia.
  - `Sienna`: 300 HP, 20 AC, Vel 6, 2d6 Elétrico.
  - `SiennaPhoenix`: 200 HP, 22 AC, Vel 8, 3d8 Elétrico/Fogo, Imune a Paralisia e Atordoamento.

---

## 3. As 24 Castas dos Insetos Isectum

Fontes: `src/cerco_isectum.py` (`DADOS_INIMIGOS`), `src/castas_isectum.py` (`aplicar_efeito_inseto`, `INSETOS_BOSS`, `criar_deck_diretor`), e `assets/images/characters/monsters/isectum/`.

Cada casta possui comportamento ofensivo quando jogada pelo Diretor Isectum, arquétipo de combate em campo, e versão invertida (capturada) quando eliminada pelos heróis no caso dos Bosses.

| ID do Inseto | Nome Canônico & Emoji | Classe Base | HP (Boss?) | Comportamento Ativo do Diretor (`aplicar_efeito_inseto`) | Efeito Invertido ao ser Capturado | Arquivo de Asset |
|---|---|---|---|---|---|---|
| `vespa_cacadora` | Vespa-Caçadora 🐝 | Goblin | 1 HP (Boss) | Pede uma carta específica da mão do herói ativo; se possuir, rouba para o Diretor (+1 roubada). | `receber_cartas`: Recebe 1 carta de outro herói à sua escolha. | `vespa_cacadora.png` |
| `louva_deus` | Louva-a-Deus Mimético 🦗 | Kobold | 1 HP | Troca as mãos inteiras de cartas entre dois heróis defensores. | N/A | `louva_deus.png` |
| `viuva_canibal` | Viúva-Canibal 🕷️ | Esqueleto | 2 HP (Boss) | Copia e ativa imediatamente o efeito de outro inseto presente no descarte do Diretor. | `copiar_efeito_aliado`: Copia efeito de carta de Defesa ou Runa usada no turno. | `viuva_canibal.png` |
| `escaravelho_necrofago` | Escaravelho Necrófago 🪲 | Goblin | 1 HP | Pega a carta do topo do descarte do defensor ativo e rouba para si (+1 roubada). | N/A | `escaravelho_necrofago.png` |
| `besouro_unicornio` | Besouro-Unicórnio Negro 🪳 | Kobold | 1 HP | Onda de feromônios: força TODOS os defensores a descartarem 1 carta aleatória da mão. | N/A | `besouro_unicornio.png` |
| `gafanhoto_praga` | Gafanhoto-da-Praga 🦟 | Esqueleto | 1 HP (Boss) | Limpa e destrói todos os recursos alocados em um slot de upgrade aleatório do mercado. | `recuperar_combo`: Recupera um combo destruído do descarte. | `gafanhoto_praga.png` |
| `carrapato_vampiro` | Carrapato-Vampiro 🩸 | Goblin | 1 HP | Rouba 2 cartas diretamente da mão do defensor ativo (+2 roubadas). | N/A | `carrapato_vampiro.png` |
| `libelula_blindada` | Libélula-Blindada 🛡️ | DragaoAnciao | 2 HP (Boss) | Protege a mão do Diretor contra qualquer tentativa de roubo ou anulação por defensores. | `proteger_combo_defensor`: Protege combos de destruição por 1 rodada inteira. | `libelula_blindada.png` |
| `besouro_gorgulho` | Besouro-Gorgulho 🐜 | Kobold | 1 HP | Cava no topo do descarte e no topo do deck do defensor, roubando 1 carta escolhida. | N/A | `besouro_gorgulho.png` |
| `cigarra_ressonante` | Cigarra-Ressonante 🪰 | Esqueleto | 1 HP | Reativa o efeito de qualquer carta de inseto presente na mão do Diretor. | N/A | `cigarra_ressonante.png` |
| `enxame_rainha` | Enxame da Rainha 🐝 | ReiGoblin | 2 HP (Boss) | Completa a mão do Diretor até o limite de mão (`tam_mao_diretor`, ex: 3 cartas) puxando do deck. | `completar_mao_defensor`: Completa a mão do defensor até 7 cartas do deck. | `enxame_rainha.png` |
| `vagalume_sombras` | Vagalumes das Sombras 🦋 | Goblin | 1 HP | Resgata 2 cartas da pilha de descarte dos defensores e rouba-as (+2 roubadas). | N/A | `vagalume_sombras.png` |
| `larva_carniceira` | Larvas Carniceiras 🪱 | Kobold | 1 HP | Rouba 1 carta da mão do herói ou compra 1 carta do deck do Diretor se a mão estiver vazia. | N/A | `larva_carniceira.png` |
| `tarantula_golias` | Tarântula-Golias 🕷️ | Esqueleto | 1 HP | Resgata 1 carta do descarte do defensor e rouba-a (+1 roubada). | N/A | `tarantula_golias.png` |
| `formiga_correicao` | Formigas-Correição 🐜 | Goblin | 1 HP | Investida massiva: rouba 3 cartas distribuídas entre os heróis defensores (+3 roubadas). | N/A | `formiga_correicao.png` |
| `aranha_clepto` | Aranha-Cleptoparasita 🕷️ | Kobold | 1 HP | Troca as mãos de 2 defensores entre si (se jogo solo, rouba 1 carta da mão do herói). | N/A | `aranha_clepto.png` |
| `centopeia_olhos` | Centopeia dos Cem Olhos 🐛 | Esqueleto | 1 HP | Olha fixamente e revela a mão inteira do herói alvo no log/interface. | N/A | `centopeia_olhos.png` |
| `abelha_tecela` | Abelha-Tecelã 🐝 | Goblin | 1 HP | Compra cartas iguais ao número de defensores: Diretor guarda 1 e distribui reveladas aos outros. | N/A | `abelha_tecela.png` |
| `mariposa_esfinge` | Mariposa-Esfinge 🦋 | Kobold | 1 HP | Diretor compra 2 cartas diretamente do seu deck para sua mão. | N/A | `mariposa_esfinge.png` |
| `efemera_mimetica` | Efêmera Mimética 🦟 | Esqueleto | 1 HP | Reativa o efeito de um inseto já jogado que esteja no descarte do Diretor. | N/A | `efemera_mimetica.png` |
| `vespa_joia` | Vespa-Joia Rainha 🐝 | Goblin | 1 HP | Espiona a mão de todos os defensores e rouba 1 carta aleatória do herói com mais cartas. | N/A | `vespa_joia.png` |
| `viuva_negra` | Viúva-Negra Tecelã 🕷️ | Esqueleto | 1 HP | Rouba e zera todos os recursos acumulados na zona/tipo de maior concentração dos defensores. | N/A | `viuva_negra.png` |
| `besouro_rinoceronte` | Besouro-Rinoceronte 🪲 | Troll | 1 HP | Força o herói alvo a descartar 1 carta de sua mão aleatoriamente (+1 roubada). | N/A | `besouro_rinoceronte.png` |
| `mosca_tse_tse` | Mosca-Tsé-Tsé 🪰 | Esqueleto | 1 HP (Boss) | Toxina sonífera: aplica `turno_pulado = True`, fazendo o herói alvo perder seu próximo turno. | `dar_turno_extra`: Ganha 1 ação extra imediata neste turno. | `mosca_tse_tse.png` |

---

## 4. Modo Cerco contra Isectum & Deckbuilding de Sincronia

Fontes: `src/cerco_isectum.py`, `src/castas_isectum.py`, `src/states/cerco/round_simultaneo.py`, `src/states/cerco/hero.py`, `src/states/cerco/draw_cards.py`, `src/resolvedor_acoes.py`, `src/juiz_combate.py`.

### 4.1 Arquitetura de Cartas
- **Categorias de Cartas**:
  1. `Básica` (`CARTAS_BASICAS`, 12 cartas no deck inicial de cada herói):
     - Trabalho (x2): +3 PT.
     - Marcha (x5): +15 PM.
     - Escavação (x1): +4 PE.
     - Força Anã (x2): +15 PM, +4 PT.
     - Invocador Orc / Portal Inseto (x2): +15 PM +3 PT ou +3 PT +3 PE, com efeito colateral `invocar_inimigo` (gera invasor no campo externo).
  2. `Upgrade` (Mercado de 5 slots alimentado por catálogo Amarelo, Cinza e Vermelho):
     - Gera pontos altos de PM, PT, PE.
     - Efeitos especiais:
       - `aumentar_mao`: +1 vaga permanente de mão por turno (ex: Plano Tático, Guia Tático, Grão Mestre).
       - `draw_1`: Compra 1 carta adicional imediatamente (Mestre Artesão).
       - `dano_area`: Causa dano em área no tabuleiro (Bola de Fogo 25 dano / raio 3; Onda de Choque 20 dano / raio 4; Chuva de Flechas 18 dano / raio 5).
     - Quando ativado em jogo, upgrades permanecem ativos permanentemente (`cartas_upgrade_ativas`).
  3. `Defesa` (`CARTAS_DEFESA`):
     - `Escudo de Quitina` (2 metal): Reação; anula roubo/troca e faz o Diretor perder 1 ação.
     - `Teia Endurecida` (2 couro): Contínua; bloqueia avanço de insetos em uma muralha por 1 turno.
     - `Antídoto Alquímico` (1 metal, 2 couro): Reação; cancela atordoamento da Mosca-Tsé-Tsé.
     - `Amuleto de Resistência` (2 metal, 1 madeira): Passiva; devolve a 1ª carta roubada na rodada.
  4. `Runa` (`CARTAS_RUNA`):
     - `Runa da Haste` (1 madeira, 1 couro): +2 ações extras ao defensor.
     - `Runa da Visão` (1 couro, 1 metal): Revela as 3 cartas do topo do deck do Diretor.
     - `Runa da Fortaleza` (2 madeira, 1 metal): +8 PT e imunidade a destruição de recursos no turno.
     - `Runa de Recuperação` (2 couro): Compra 2 cartas extras do deck.
  5. `Capturada`:
     - Gerada dinamicamente quando um inseto Boss (Libélula, Rainha, Viúva, Vespa, Mosca, Gafanhoto) é eliminado no campo de batalha, inserindo seu efeito invertido no deck do defensor.
- **Badges e Custos**:
  - `M` (Movimento): Badge azul `(80, 180, 255)`.
  - `T` (Trabalho): Badge verde `(100, 220, 120)`.
  - `E` (Escavação): Badge amarelo/âmbar `(255, 215, 80)`.
  - Custos de Aquisição: `madeira`, `couro`, `metal`, `ouro` (cristais).

### 4.2 Apresentação e Mecânica de Mão (Leque / Fan Layout)
- Tamanho base de mão: 3 cartas (`TAM_MAO = 3`), expandido por cartas com `aumentar_mao`.
- Ciclo do baralho: Se deck esvaziar, embaralha descarte (`descarte` $\rightarrow$ `deck_heroi`).
- Matemática do leque de cartas (`_calcular_pos_carta_na_mao` em `draw_cards.py:29-35`):
  $$\text{mid\_idx} = \frac{\text{total\_cartas} - 1}{2.0}$$
  $$\text{offset\_center} = \text{idx} - \text{mid\_idx}$$
  $$\text{fan\_arc\_y} = \text{int}((\text{offset\_center})^2 \times 1.6)$$
  $$\text{cy} = \text{mr.y} + 4 + \text{fan\_arc\_y}$$
- Hover e Elevação:
  - Ao passar o mouse sobre a carta: deslocamento vertical para cima (`deslocamento_y = -30`).
  - Sombra projetada + borda dourada/acento com aura de brilho 3D.

### 4.3 Turno de Sincronia Simultânea Co-op (`round_simultaneo.py`)
No modo co-op simultâneo, não há espera sequencial entre heróis:
1. **Seleção Simultânea**: Cada herói escolhe 1 carta de sua mão para o round (`ROUND_SIMULTANEO`).
2. **Camadas de Resolução**: Quando todos escolhem, os efeitos resolvem em ordem estrita:
   $$\text{Movimento} \longrightarrow \text{Trabalho} \longrightarrow \text{Escavação} \longrightarrow \text{Upgrade}$$
3. **Cálculo de Sinergias (Combos)**:
   - Se 2+ heróis jogarem cartas do mesmo tipo:
     - **Movimento**: +1 passo extra para todos os heróis.
     - **Trabalho**: +1 recurso bônus coletado automaticamente.
     - **Escavação**: -2 pedregulhos extras removidos do túnel.
     - **Upgrade**: +1 Cristal Roxo adicionado ao Tesouro da fortaleza.
   - **Sincronia Suprema / Perfeita**: Se todos os heróis (mínimo de 3) jogarem o mesmo tipo de carta:
     - Mensagem de Sincronia Perfeita +2 Cristais Roxos ao Tesouro.
4. **Pressão Crescente de Inimigos**:
   - Round 1: Insetos avançam 1 passo.
   - Round 2: Insetos avançam 1 passo e desferem ataques aos heróis no alcance.
   - Round 3+: Insetos avançam 2 passos e atacam com pressão máxima.
5. **Vantagem por Velocidade**:
   - O primeiro herói a esgotar completamente sua mão no turno ganha *Vantagem por Velocidade* (+1 carta extra sacada no próximo turno global).

### 4.4 Economia da Fortaleza & Ações Livres no Tabuleiro 20x20
- **Grid e Zonas Lógicas** (`resolvedor_acoes.py:20-48`):
  - `Câmara Central` [coords (8,8) a (11,11)]: Guarda o Tesouro (Cristais Roxos). Derrota se 3+ invasores entrarem ou cristais zerarem.
  - `Oficinas Internas`:
    - `Carpintaria` [(5,12) a (14,15)]: Produz **Madeira** (gasta PT). Bloqueada se houver invasor dentro.
    - `Curtume` [(5,4) a (14,7)]: Produz **Couro** (gasta PT). Bloqueada se houver invasor dentro.
    - `Fundição` [(4,5) a (7,14)]: Produz **Metal / Ferro** (gasta PT). Bloqueada se houver invasor dentro.
  - `Pátio / Área de Escavação` [(12,5) a (15,14)]:
    - Contém pedregulhos que bloqueiam o túnel de fuga.
    - Ação de Escavar: consome Pontos de Escavação (PE). Bloqueada se houver Brutamontes ou Infiltradores no Pátio.
    - Emboscadas: a cada 4 pedregulhos escavados, 2 Infiltradores invadem o Pátio.
    - Conclusão do Túnel: Ao zerar pedregulhos, surge o desafio final (2 Infiltradores de Elite). Derrotá-los garante a vitória.
  - `Muralhas do Perímetro` (Norte, Sul, Leste, Oeste): Elevação 4. Bloqueiam invasores vindos dos campos externos.
  - `Torres dos Cantos` (`torre_nw`, `torre_ne`, `torre_sw`, `torre_se`): Elevação 6. Posições de atirador para ataque de balestra de longo alcance.
  - `Campos Externos` (Norte, Sul, Leste, Oeste): Borda exterior onde os inimigos dão spawn inicial.
- **Fluxo de Avanço dos Invasores**:
  $$\text{Campos Externos} \xrightarrow{\text{Escalada}} \text{Muralhas} \longrightarrow \text{Oficinas} \longrightarrow \text{Câmara Central (Roubo de Cristais)}$$
- **Mercado de Upgrades**:
  - 5 slots no mercado. Heróis alocam Madeira, Couro e Metal produzidos nas oficinas.
  - Ao completar o custo, o herói gasta uma ação e deve sacrificar/queimar permanentemente uma carta não-penalidade da mão para integrar a nova carta de Upgrade ao seu baralho.
- **Sistema de Combate Cerco (D6 Customizado)** (`juiz_combate.py`):
  - Faces 1-2: 1 Impacto Físico.
  - Face 3: 2 Impactos Físicos.
  - Face 4: 3 Impactos Físicos.
  - Faces 5-6: 1 Disparo de Longa Distância (Balestra).
  - Melee: Requer mesma zona/célula; 2 Impactos = 1 Dano; Flanqueamento com 2+ aliados dá +1 D6.
  - Distância: Requer posição em Torre; 1 Disparo = 1 Dano; atinge apenas muralhas adjacentes, campos externos ou armas de cerco (Catapulta e Torre de Assalto).

---

## 5. Mapeamento de Assets Visuais

| Categoria | Caminho Canônico | Formato / Resolução | Uso Recomendado em Godot 4 |
|---|---|---|---|
| **Heróis (Protagonistas)** | `assets/images/characters/heroes/` | PNG estático (Novak, Koema, Rilem, Yukito, Aquele) | `Texture2D` para HUD / Portraits / UI |
| **Heróis (Spritesheets)** | `assets/images/characters/animation/processed/` | PNG Spritesheet 1024x1024 (256x256 por quadro, 4 colunas x 4 linhas) | `Sprite2D` / `AnimatedSprite2D` no grid tático |
| **Classes Genéricas** | `assets/images/characters/silver_roses/` | PNG Spritesheet (sword_isnet_clean.png, archer_sem_halo.png, mine_sem_halo.png, 3x4 col/lin) | `Sprite2D` com `hframes=3, vframes=4` |
| **Castas Isectum (24 Insetos)**| `assets/images/characters/monsters/isectum/` | PNG individual com transparência (24 arquivos nomeados por casta) | `Sprite2D` de inimigo e ícone de carta |
| **Monstros & Bosses** | `assets/images/characters/monsters/` & `bosses/` | PNG estáticos (goblin, esqueleto, lorde_lich, dragao_anciao, Sienna.png, chefe.png) | Sprites de chefes e minions |
| **Terrenos do Tabuleiro** | `assets/images/environment/` | PNG tiles (`terreno_normal`, `terreno_muralha_lo`, `terreno_subsolo`, etc.) | `TileSet` / `TileMapLayer` do Godot 4 |
| **UI & Badges** | `assets/images/ui/` | PNGs de painéis, botões e ícones | `TextureRect` e temas de `Control` |

---

## 6. Conclusão & Prontidão para Migração
A integridade dos dados e regras do projeto Python original está 100% catalogada e mapeada:
1. Todos os 11 heróis e suas classes possuem atributos, recursos, habilidades e assets prontos para conversão em `CharacterData.gd` (`Custom Resource`).
2. Todas as 24 castas Isectum possuem mapeamento 1:1 de efeitos ofensivos, defensivos, de captura e sprites.
3. A lógica do Cerco (deckbuilding, leque de cartas, sincronia de combos, economia de oficinas e escavação) está plenamente especificada para implementação em GDScript desacoplado.
