import random
import heapq
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL, TERRENO_GELO, TERRENO_FOGO
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold
from .utils import calcular_distancia
from .config import COR_TEXTO, COR_DANO, COR_CRITICO, COR_STATUS, COR_CURA

class MotorCombate:
    def __init__(self, args_times, gerar_terreno=False, mapa_custom=None, sound_player=None, modo_chefe=False, stats_chefe=None, boss_class=None, custom_time_a=None, custom_mapa_arquivo=None):
        from .salvar_carregar import carregar_mapa_json
        
        self.sound_player = sound_player
        
        # Load custom map from file if provided
        if custom_mapa_arquivo:
            try:
                import json
                with open(custom_mapa_arquivo, 'r') as f:
                    mapa_custom = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar mapa customizado {custom_mapa_arquivo}: {e}")

        if mapa_custom:
            h = len(mapa_custom)
            w = len(mapa_custom[0]) if h > 0 else 20
            self.tabuleiro = Tabuleiro(w, h)
            self.tabuleiro.terrain_grid = mapa_custom
            self.visibilidade_map = [[0 for _ in range(w)] for _ in range(h)]
        else:
            self.tabuleiro = Tabuleiro(20, 20)
            self.visibilidade_map = [[0 for _ in range(20)] for _ in range(20)]
            if gerar_terreno:
                self.tabuleiro.gerar_terreno_aleatorio()
        
        self.custom_time_a = custom_time_a
        
        if custom_time_a:
            self.time_a = custom_time_a
            for p in self.time_a:
                self.tabuleiro.adicionar_personagem_na_borda(p, 'sul')
            self.time_b = [] # Placeholder until set_time_b_custom is called or standard setup
            
            # If standard args are passed along with custom_time_a, we might ignore them for Time A 
            # but arguably we should just use custom_time_a if present.
            
            if not args_times: # If empty args, we assume manual setup for B too or standard
                 pass
        else:
            self.time_a, self.time_b = self._setup_times(args_times, modo_chefe, stats_chefe, boss_class)
        
        self.combatentes = []
        if self.time_a: self.combatentes.extend(self.time_a)
        if self.time_b: self.combatentes.extend(self.time_b)
        
        if self.combatentes:
            for p in self.combatentes: 
                p.rolar_iniciativa()
            self.ordem_de_combate = sorted(self.combatentes, key=lambda x: x.iniciativa, reverse=True)
            
        self.turno = 1
        self.combatente_atual_idx = 0
        self.vencedor = None
        self.atualizar_visibilidade()
        self.sienna_phase_2_triggered = False

    def set_time_b_custom(self, time_b_instances):
        self.time_b = time_b_instances
        for p in self.time_b:
            self.tabuleiro.adicionar_personagem_na_borda(p, 'norte')
        self.combatentes = self.time_a + self.time_b
        
    def start_battle_custom(self):
        for p in self.combatentes: 
            p.rolar_iniciativa()
        self.ordem_de_combate = sorted(self.combatentes, key=lambda x: x.iniciativa, reverse=True)
        self.atualizar_visibilidade()

    def atualizar_visibilidade(self):
        # Reset current visibility (keep visited)
        for y in range(self.tabuleiro.altura):
            for x in range(self.tabuleiro.largura):
                if self.visibilidade_map[y][x] == 2:
                    self.visibilidade_map[y][x] = 1
        
        # Calculate visibility for all Player characters (Team A)
        for p in self.time_a:
            if p.esta_vivo:
                raio_visao = 8 # Default vision radius
                for y in range(max(0, p.pos_y - raio_visao), min(self.tabuleiro.altura, p.pos_y + raio_visao + 1)):
                    for x in range(max(0, p.pos_x - raio_visao), min(self.tabuleiro.largura, p.pos_x + raio_visao + 1)):
                        if self.tabuleiro.calcular_linha_visao(p.pos_x, p.pos_y, x, y, ignorar_personagens=True):
                             # Check distance (euclidean-ish)
                            if (x - p.pos_x)**2 + (y - p.pos_y)**2 <= raio_visao**2:
                                self.visibilidade_map[y][x] = 2

    def _setup_times(self, args, modo_chefe, stats_chefe, boss_class=None):
        classes = [Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold]
        time_a = []
        personagens_para_criar_a = []
        for i, classe in enumerate(classes):
            personagens_para_criar_a.extend([classe] * args[i])
        for i, classe_personagem in enumerate(personagens_para_criar_a):
            nome = f"{classe_personagem.__name__}_A{i+1}"
            p = classe_personagem(nome, "A", nivel=1, sound_player=self.sound_player)
            time_a.append(p)
            self.tabuleiro.adicionar_personagem_na_borda(p, 'sul')

        time_b = []
        if modo_chefe and boss_class:
            chefe = boss_class(f"{boss_class.__name__}", "B", sound_player=self.sound_player, stats=stats_chefe)
            time_b.append(chefe)
            self.tabuleiro.adicionar_personagem_na_borda(chefe, 'norte')
        else:
            personagens_para_criar_b = []
            for i, classe in enumerate(classes):
                if len(args) > i + len(classes):
                    personagens_para_criar_b.extend([classe] * args[i+len(classes)])

            for i, classe_personagem in enumerate(personagens_para_criar_b):
                nome = f"{classe_personagem.__name__}_B{i+1}"
                p = classe_personagem(nome, "B", nivel=1, sound_player=self.sound_player)
                time_b.append(p)
                self.tabuleiro.adicionar_personagem_na_borda(p, 'norte')

        return time_a, time_b

    def proximo_passo(self):
        self.atualizar_visibilidade()
        logs_turno = []
        eventos_turno = []
        if self.vencedor:
            return {'logs': [], 'eventos': []}

        if self.combatente_atual_idx == 0:
            logs_turno.append((f"--- RODADA {self.turno} ---", COR_TEXTO))

        atacante = self.ordem_de_combate[self.combatente_atual_idx]
        atacante.eventos_animacao.clear()

        if atacante.esta_vivo:
            atacante.tick_status_efeitos(self.tabuleiro, logs_turno.append)
            
            # Dano de Terreno (Fogo)
            terreno_atual = self.tabuleiro.get_terrain_em(atacante.pos_x, atacante.pos_y)
            if terreno_atual == TERRENO_FOGO:
                dano_fogo = random.randint(1, 6)
                logs_turno.append((f"  {atacante.nome} queima no fogo e recebe {dano_fogo} de dano!", COR_DANO))
                atacante.receber_dano(dano_fogo, None, self.tabuleiro, logs_turno.append, tipo_dano="Fogo")
                if not atacante.esta_vivo:
                    self.finalizar_turno(logs_turno, eventos_turno)
                    return {'logs': logs_turno, 'eventos': eventos_turno}

            logs_turno.append((f"Vez de {atacante.nome}", COR_TEXTO))
            
            time_inimigo = [p for p in (self.time_b if atacante.time == "A" else self.time_a) if p.esta_vivo]
            time_aliado = [p for p in (self.time_a if atacante.time == "A" else self.time_b) if p.esta_vivo]

            if not time_inimigo:
                acao = {'acao': 'passar'}
            else:
                acao = atacante.decidir_acao(time_inimigo, time_aliado, self.tabuleiro, logs_turno)

            if acao['acao'] == 'atacar':
                alvo = acao['alvo']
                if calcular_distancia(atacante, alvo) > atacante.alcance:
                    logs_turno.append((f"  {atacante.nome} tenta atacar {alvo.nome} mas está fora de alcance!", COR_TEXTO))
                    self._mover_personagem(atacante, alvo, logs_turno)
                    if calcular_distancia(atacante, alvo) <= atacante.alcance:
                        atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                else:
                    atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
            elif acao['acao'] == 'mover':
                alvo = acao['alvo']
                self._mover_personagem(atacante, alvo, logs_turno)
            elif acao['acao'] == 'fugir':
                self._fugir(atacante, time_inimigo, logs_turno)
            elif acao['acao'] == 'pegar_item':
                item = acao['item']
                atacante.inventario.append(item)
                self.tabuleiro.itens_no_chao[atacante.pos_y][atacante.pos_x] = None
                logs_turno.append((f"  {atacante.nome} pegou {item.nome} do chão.", (255, 215, 0)))

            elif acao['acao'] == 'usar_habilidade':
                habilidade = acao['habilidade']
                if habilidade == 'surto_de_acao':
                    logs_turno.append((f"  {atacante.nome} usa Surto de Ação!", COR_STATUS))
                    atacante.atacar(acao['alvo'], time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                elif habilidade == 'convocar_goblin':
                    self._summon_minion(atacante, Goblin, logs_turno)
                elif habilidade == 'forma_de_urso':
                    atacante.usar_forma_de_urso(logs_turno.append)
                elif habilidade == 'maldicao_de_agonia':
                    alvo = acao['alvo']
                    logs_turno.append((f"  {atacante.nome} amaldiçoa {alvo.nome} com Agonia!", COR_STATUS))
                    atacante.mana_atual -= atacante.custo_habilidades['maldicao_de_agonia']
                    alvo.aplicar_status_efeito("Amaldiçoado", 3, logs_turno.append)
                elif habilidade == 'canalizar_divindade':
                    alvo_cura = acao['alvo']
                    atacante.fe_atual -= atacante.custo_habilidades['canalizar_divindade']
                    cura = sum(random.randint(1, 6) for _ in range(2)) + atacante.mod_sab
                    alvo_cura.receber_cura(cura, logs_turno.append)
                    atacante.eventos_animacao.append({'tipo': 'cura', 'alvo': alvo_cura, 'cura': cura})
                elif habilidade == 'raio_de_gelo':
                    alvo = acao['alvo']
                    logs_turno.append((f"  {atacante.nome} lança Raio de Gelo em {alvo.nome}!", COR_STATUS))
                    atacante.mana_atual -= atacante.custo_habilidades['raio_de_gelo']
                    # Adiciona a informação da habilidade no evento de animação
                    atacante.eventos_animacao.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'raio_de_gelo'})
                    atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, tipo_dano_override="Gelo")
                    
                    # Interação Elemental
                    self.tabuleiro.aplicar_dano_terreno(alvo.pos_x, alvo.pos_y, "Gelo", logs_turno.append)
                    
                    if random.random() < 0.3 and self.tabuleiro.get_terrain_em(alvo.pos_x, alvo.pos_y) != TERRENO_GELO:
                        self.tabuleiro.terrain_grid[alvo.pos_y][alvo.pos_x] = TERRENO_GELO
                        logs_turno.append((f"  O chão sob {alvo.nome} congela!", COR_STATUS))
                elif habilidade == 'bola_de_fogo':
                    pos_final = acao['pos_conjuracao']
                    alvo_central = acao['alvo_central']
                    if (atacante.pos_x, atacante.pos_y) != pos_final:
                        self.tabuleiro.mover_personagem(atacante, pos_final[0], pos_final[1])
                        logs_turno.append((f"  {atacante.nome} se move para ({pos_final[0]},{pos_final[1]}) para a conjuração.", COR_TEXTO))
                        atacante.eventos_animacao.append({'tipo': 'movimento', 'personagem': atacante, 'start_pos': (atacante.pos_x, atacante.pos_y), 'end_pos': pos_final})
                    logs_turno.append((f"{atacante.nome} conjura BOLA DE FOGO em ({alvo_central.pos_x},{alvo_central.pos_y})!", COR_CRITICO))
                    atacante.mana_atual -= atacante.custo_habilidades['bola_de_fogo']
                    alvos_afetados = self.tabuleiro.get_personagens_em_area(alvo_central.pos_x, alvo_central.pos_y, 1)
                    dano = sum(random.randint(1, 6) for _ in range(2))
                    logs_turno.append((f"  A bola de fogo causa {dano} de dano de Fogo em área!", COR_DANO))
                    atacante.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': atacante, 'x': alvo_central.pos_x, 'y': alvo_central.pos_y, 'raio': 1})
                    if atacante.sound_player: atacante.sound_player('attack')
                    for vitima in alvos_afetados:
                        vitima.receber_dano(dano, atacante, self.tabuleiro, logs_turno.append, tipo_dano="Fogo")
                    
                    # Interação Elemental em Área
                    for y in range(alvo_central.pos_y - 1, alvo_central.pos_y + 2):
                        for x in range(alvo_central.pos_x - 1, alvo_central.pos_x + 2):
                            self.tabuleiro.aplicar_dano_terreno(x, y, "Fogo", logs_turno.append)
            elif acao['acao'] == 'passar':
                logs_turno.append((f"  {atacante.nome} passa o turno.", COR_TEXTO))
        
        self.finalizar_turno(logs_turno, eventos_turno)
        return {'logs': logs_turno, 'eventos': eventos_turno}

    def finalizar_turno(self, logs_turno, eventos_turno):
        for p in self.combatentes:
            eventos_turno.extend(p.eventos_animacao)
            p.eventos_animacao.clear()
        
        self._verificar_eventos_script_campanha(logs_turno, eventos_turno)
        self._verificar_fim_de_combate(logs_turno)
        
        self.combatente_atual_idx = (self.combatente_atual_idx + 1) % len(self.ordem_de_combate)
        if self.combatente_atual_idx == 0: self.turno += 1

    def _verificar_ataques_de_oportunidade(self, personagem_movendo, novo_x, novo_y, logs_turno):
        time_inimigo = self.time_b if personagem_movendo.time == "A" else self.time_a
        for inimigo in time_inimigo:
            if inimigo.esta_vivo and inimigo.alcance == 1 and calcular_distancia(personagem_movendo, inimigo) <= 1:
                dist_antiga = calcular_distancia(personagem_movendo, inimigo)
                dist_nova = abs(novo_x - inimigo.pos_x) + abs(novo_y - inimigo.pos_y)
                if dist_nova > dist_antiga:
                    logs_turno.append((f"  {inimigo.nome} aproveita a oportunidade e ataca {personagem_movendo.nome} em movimento!", COR_DANO))
                    inimigo.atacar(personagem_movendo, [personagem_movendo], [], self.tabuleiro, logger=logs_turno.append)
                    if not personagem_movendo.esta_vivo:
                        logs_turno.append((f"  {personagem_movendo.nome} foi derrotado pelo ataque de oportunidade!", COR_DANO))
                        return False
        return True

    def _verificar_eventos_script_campanha(self, logs_turno, eventos_turno):
        # Round 2 Dialogue
        if self.turno == 2 and self.combatente_atual_idx == 0:
            if not getattr(self, 'round_2_dialogue_triggered', False):
                self.round_2_dialogue_triggered = True
                eventos_turno.append({
                    'tipo': 'dialogo',
                    'mensagens': [
                        ("Koema", "Ela é forte, mas está instável!", "koema"),
                        ("Novak", "Yukito, mantenha a frente! Rilem, flanqueie!", "novak"),
                        ("Yukito", "Entendido! Pela luz!", "yukito"),
                        ("Rilem", "Já estou na sombra dela...", "rilem"),
                        ("Sienna", "Planejem o quanto quiserem. O resultado será o mesmo!", "sienna")
                    ]
                })
            
        # Sienna Phase 2 Logic
        sienna = next((p for p in self.time_b if p.classe_nome == "Sienna"), None)
        if sienna and sienna.hp_atual <= 0 and not self.sienna_phase_2_triggered:
            self.sienna_phase_2_triggered = True
            from .personagens import SiennaPhoenix
            
            logs_turno.append(("Sienna cai...", COR_TEXTO))
            logs_turno.append(("...Mas seu corpo se desfaz em pura energia!", COR_CRITICO))
            logs_turno.append(("SIENNA RENASCE COMO A FÊNIX DO VAZIO!", COR_CRITICO))
            
            # Remove Sienna
            sienna.esta_vivo = False
            self.tabuleiro.grid[sienna.pos_y][sienna.pos_x] = None
            
            # Spawn Phoenix at same pos
            phoenix = SiennaPhoenix("Sienna (Fênix)", "B", sound_player=self.sound_player)
            phoenix.pos_x, phoenix.pos_y = sienna.pos_x, sienna.pos_y
            self.tabuleiro.personagens[phoenix.pos_y][phoenix.pos_x] = phoenix
            
            self.time_b.append(phoenix)
            self.combatentes.append(phoenix)
            self.ordem_de_combate.append(phoenix)
            self.ordem_de_combate.insert(self.combatente_atual_idx + 1, phoenix)
            
            eventos_turno.append({'tipo': 'spawn', 'personagem': phoenix})

        # Phoenix Death Logic -> Rasante
        phoenix = next((p for p in self.time_b if p.classe_nome == "SiennaPhoenix"), None)
        if phoenix and phoenix.hp <= 0:
             logs_turno.append(("A Fênix solta um guincho final...", COR_CRITICO))
             logs_turno.append(("Ela mergulha em um rasante mortal sobre o grupo!", COR_CRITICO))
             
             for p in self.time_a:
                 if p.esta_vivo:
                     p.receber_dano(20, phoenix, self.tabuleiro, logs_turno.append, tipo_dano="Eletrico")
             
             logs_turno.append(("A energia se dissipa. O silêncio retorna.", COR_TEXTO))
        return True

    def _fugir(self, p, inimigos, logs_turno):
        if not inimigos: return
        if not p.pode_fugir:
            logs_turno.append((f"  {p.nome} tenta fugir, mas um efeito de status o impede!", COR_STATUS))
            return

        inimigo_mais_proximo = min(inimigos, key=lambda i: calcular_distancia(p, i))
        logs_turno.append((f"  {p.nome} está com pouca vida e tenta fugir de {inimigo_mais_proximo.nome}!", COR_TEXTO))
        start_pos = (p.pos_x, p.pos_y)
        
        melhor_pos_fuga = None
        maior_dist_do_inimigo = calcular_distancia(p, inimigo_mais_proximo)
        
        for dx in range(-p.velocidade, p.velocidade + 1):
            for dy in range(-p.velocidade, p.velocidade + 1):
                # if abs(dx) + abs(dy) > p.velocidade: continue # Removed for Square Distance
                prox_x, prox_y = p.pos_x + dx, p.pos_y + dy
                if not (0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura): continue
                if self.tabuleiro.get_personagem_em(prox_x, prox_y) is not None: continue
                if self.tabuleiro.get_terrain_em(prox_x, prox_y) == TERRENO_PAREDE: continue

                dist_da_fuga = calcular_distancia(type('obj', (object,), {'pos_x': prox_x, 'pos_y': prox_y}), inimigo_mais_proximo)
                
                if dist_da_fuga > maior_dist_do_inimigo:
                    maior_dist_do_inimigo = dist_da_fuga
                    melhor_pos_fuga = (prox_x, prox_y)
                elif dist_da_fuga == maior_dist_do_inimigo and melhor_pos_fuga is None:
                     melhor_pos_fuga = (prox_x, prox_y)

        if melhor_pos_fuga:
            self.tabuleiro.mover_personagem(p, melhor_pos_fuga[0], melhor_pos_fuga[1])
            logs_turno.append((f"  {p.nome} fugiu para ({p.pos_x},{p.pos_y}).", COR_TEXTO))
            p.eventos_animacao.append({'tipo': 'movimento', 'personagem': p, 'start_pos': start_pos, 'end_pos': (p.pos_x, p.pos_y)})
        else:
            logs_turno.append((f"  {p.nome} não conseguiu encontrar uma rota de fuga melhor.", COR_TEXTO))

    def _astar_pathfinding(self, start_pos, end_pos, max_cost):
        open_set = [(0, start_pos)]
        came_from = {}
        g_cost = {start_pos: 0}

        while open_set:
            _, current_pos = heapq.heappop(open_set)
            if current_pos == end_pos:
                path = []
                while current_pos in came_from:
                    path.append(current_pos)
                    current_pos = came_from[current_pos]
                return path[::-1]

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor_pos = (current_pos[0] + dx, current_pos[1] + dy)
                if not (0 <= neighbor_pos[0] < self.tabuleiro.largura and 0 <= neighbor_pos[1] < self.tabuleiro.altura):
                    continue
                if self.tabuleiro.terrain_grid[neighbor_pos[1]][neighbor_pos[0]] == TERRENO_PAREDE:
                    continue
                if self.tabuleiro.get_personagem_em(neighbor_pos[0], neighbor_pos[1]) is not None and neighbor_pos != end_pos:
                    continue
                move_cost = 2 if self.tabuleiro.terrain_grid[neighbor_pos[1]][neighbor_pos[0]] == TERRENO_DIFICIL else 1
                tentative_g_cost = g_cost[current_pos] + move_cost
                if tentative_g_cost > max_cost:
                    continue
                if neighbor_pos not in g_cost or tentative_g_cost < g_cost[neighbor_pos]:
                    came_from[neighbor_pos] = current_pos
                    g_cost[neighbor_pos] = tentative_g_cost
                    h_cost = abs(neighbor_pos[0] - end_pos[0]) + abs(neighbor_pos[1] - end_pos[1])
                    f_cost = tentative_g_cost + h_cost
                    heapq.heappush(open_set, (f_cost, neighbor_pos))
        return None

    def _mover_personagem(self, p, alvo, logs_turno):
        logs_turno.append((f"  {p.nome} se move em direção a {alvo.nome}.", COR_TEXTO))
        start_pos = (p.pos_x, p.pos_y)
        if calcular_distancia(p, alvo) <= p.alcance:
            logs_turno.append((f"  {p.nome} já está ao alcance.", COR_TEXTO))
            return

        melhor_adjacente = None
        menor_custo = float('inf')
        caminho_final = None

        for dx in range(-p.alcance, p.alcance + 1):
            for dy in range(-p.alcance, p.alcance + 1):
                # if abs(dx) + abs(dy) > p.alcance: continue # Removed for Square Distance
                end_pos = (alvo.pos_x + dx, alvo.pos_y + dy)
                if not (0 <= end_pos[0] < self.tabuleiro.largura and 0 <= end_pos[1] < self.tabuleiro.altura):
                    continue
                if self.tabuleiro.terrain_grid[end_pos[1]][end_pos[0]] == TERRENO_PAREDE:
                    continue
                personagem_no_alvo = self.tabuleiro.get_personagem_em(end_pos[0], end_pos[1])
                if personagem_no_alvo is not None and personagem_no_alvo != p:
                    continue
                caminho = self._astar_pathfinding(start_pos, end_pos, p.velocidade)
                if caminho:
                    custo_caminho = 0
                    for passo in caminho:
                        custo_passo = 2 if self.tabuleiro.terrain_grid[passo[1]][passo[0]] == TERRENO_DIFICIL else 1
                        custo_caminho += custo_passo
                    if custo_caminho < menor_custo:
                        menor_custo = custo_caminho
                        caminho_final = caminho

        # Fallback: Se não encontrou posição de ataque alcançável, move-se em direção ao alvo
        if not caminho_final:
            # Tenta encontrar caminho até o alvo (ignorando limite de movimento inicial)
            caminho_longo = self._astar_pathfinding(start_pos, (alvo.pos_x, alvo.pos_y), 100)
            if caminho_longo:
                caminho_final = []
                custo_atual = 0
                for passo in caminho_longo:
                    # Não pode andar sobre o alvo
                    if passo == (alvo.pos_x, alvo.pos_y):
                        break
                    
                    custo_passo = 2 if self.tabuleiro.terrain_grid[passo[1]][passo[0]] == TERRENO_DIFICIL else 1
                    
                    if custo_atual + custo_passo > p.velocidade:
                        break
                    
                    caminho_final.append(passo)
                    custo_atual += custo_passo

        if caminho_final:
            movimento_realizado = False
            for passo in caminho_final:
                if not self._verificar_ataques_de_oportunidade(p, passo[0], passo[1], logs_turno):
                    return
                self.tabuleiro.mover_personagem(p, passo[0], passo[1])
                p.elevacao = self.tabuleiro.get_elevation_em(p.pos_x, p.pos_y)
                movimento_realizado = True
                if self.tabuleiro.get_terrain_em(p.pos_x, p.pos_y) == TERRENO_GELO and random.random() < 0.5:
                    logs_turno.append((f"  {p.nome} escorrega no gelo!", COR_STATUS))
                    dx_slip, dy_slip = passo[0] - start_pos[0], passo[1] - start_pos[1]
                    prox_x, prox_y = p.pos_x + dx_slip, p.pos_y + dy_slip
                    if 0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura and \
                        self.tabuleiro.get_personagem_em(prox_x, prox_y) is None and \
                        self.tabuleiro.get_terrain_em(prox_x, prox_y) != TERRENO_PAREDE:
                        self.tabuleiro.mover_personagem(p, prox_x, prox_y)
            if movimento_realizado:
                logs_turno.append((f"  {p.nome} se moveu para ({p.pos_x},{p.pos_y}).", COR_TEXTO))
                p.eventos_animacao.append({'tipo': 'movimento', 'personagem': p, 'start_pos': start_pos, 'end_pos': (p.pos_x, p.pos_y)})
        else:
            logs_turno.append((f"  {p.nome} está bloqueado ou não conseguiu encontrar um caminho até {alvo.nome}.", COR_TEXTO))

    def _summon_minion(self, summoner, minion_class, logs_turno):
        for dx, dy in sorted(random.sample([(0,-1), (0,1), (-1,0), (1,0)], 4)):
            x, y = summoner.pos_x + dx, summoner.pos_y + dy
            if 0 <= x < self.tabuleiro.largura and 0 <= y < self.tabuleiro.altura and \
               self.tabuleiro.get_personagem_em(x, y) is None and \
               self.tabuleiro.get_terrain_em(x, y) != TERRENO_PAREDE:
                nome_minion = f"{minion_class.__name__}_{random.randint(100, 999)}"
                minion = minion_class(nome_minion, summoner.time, nivel=1, sound_player=self.sound_player)
                minion.pos_x, minion.pos_y = x, y
                self.tabuleiro.personagens[y][x] = minion
                self.combatentes.append(minion)
                if summoner.time == "A":
                    self.time_a.append(minion)
                else:
                    self.time_b.append(minion)
                minion.rolar_iniciativa()
                self.ordem_de_combate.insert(self.combatente_atual_idx + 1, minion)
                logs_turno.append((f"  {summoner.nome} convocou {nome_minion} em ({x},{y})!", COR_STATUS))
                summoner.eventos_animacao.append({'tipo': 'spawn', 'personagem': minion})
                return
        logs_turno.append((f"  {summoner.nome} tentou convocar, mas não havia espaço!", COR_TEXTO))

    def _verificar_fim_de_combate(self, logs_turno):
        if not any(p.esta_vivo for p in self.time_a): self.vencedor = f"Time B"
        elif not any(p.esta_vivo for p in self.time_b): self.vencedor = f"Time A"
        if self.vencedor: logs_turno.append((f"O {self.vencedor} é o vencedor!", COR_CRITICO))

    def get_personagem_ativo(self):
        return self.ordem_de_combate[self.combatente_atual_idx]

    def avancar_turno(self):
        self._verificar_fim_de_combate([])
        if self.vencedor: return
        self.combatente_atual_idx = (self.combatente_atual_idx + 1) % len(self.ordem_de_combate)
        if self.combatente_atual_idx == 0: 
            self.turno += 1
            for p in self.combatentes:
                p.tick_cooldowns()
                p.tick_recursos()

    def get_movimento_valido(self, personagem):
        """Retorna uma lista de tuplas (x, y) representando as células alcançáveis."""
        movimentos = []
        if not personagem: return []
        
        start_pos = (personagem.pos_x, personagem.pos_y)
        open_set = [(0, start_pos)]
        g_cost = {start_pos: 0}
        
        while open_set:
            current_cost, current_pos = heapq.heappop(open_set)
            
            if current_cost > personagem.velocidade:
                continue

            if current_pos != start_pos:
                movimentos.append(current_pos)

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor_pos = (current_pos[0] + dx, current_pos[1] + dy)
                
                # Check bounds
                if not (0 <= neighbor_pos[0] < self.tabuleiro.largura and 0 <= neighbor_pos[1] < self.tabuleiro.altura):
                    continue
                
                # Check walls
                if self.tabuleiro.terrain_grid[neighbor_pos[1]][neighbor_pos[0]] == TERRENO_PAREDE:
                    continue
                
                # Check occupancy (cannot stop on occupied tile)
                # Note: A* prevents passing through enemies usually, but for validity we check if destination is user-occupied
                # If we want to show tiles we can *reach* (even if passing through allies), we need logic.
                # Here we assume simple: cannot enter occupied tile.
                if self.tabuleiro.get_personagem_em(neighbor_pos[0], neighbor_pos[1]) is not None:
                     continue

                move_cost = 2 if self.tabuleiro.terrain_grid[neighbor_pos[1]][neighbor_pos[0]] == TERRENO_DIFICIL else 1
                tentative_cost = current_cost + move_cost
                
                if tentative_cost <= personagem.velocidade:
                    if neighbor_pos not in g_cost or tentative_cost < g_cost[neighbor_pos]:
                        g_cost[neighbor_pos] = tentative_cost
                        heapq.heappush(open_set, (tentative_cost, neighbor_pos))
        
        return movimentos

    def jogador_move_personagem(self, personagem, novo_x, novo_y):
        logs_movimento = []
        
        # 1. Validação Básica
        if not (0 <= novo_x < self.tabuleiro.largura and 0 <= novo_y < self.tabuleiro.altura):
            logs_movimento.append(("Movimento inválido: Fora do mapa.", COR_DANO))
            return [], logs_movimento
            
        if self.tabuleiro.get_terrain_em(novo_x, novo_y) == TERRENO_PAREDE:
            logs_movimento.append(("Movimento inválido: Parede.", COR_DANO))
            return [], logs_movimento

        if self.tabuleiro.get_personagem_em(novo_x, novo_y) is not None:
             logs_movimento.append(("Movimento inválido: Espaço ocupado.", COR_DANO))
             return [], logs_movimento

        # 2. Pathfinding
        start_pos = (personagem.pos_x, personagem.pos_y)
        end_pos = (novo_x, novo_y)
        
        # Usa o pathfinding existente para encontrar o melhor caminho
        caminho = self._astar_pathfinding(start_pos, end_pos, personagem.velocidade)
        
        if not caminho:
             logs_movimento.append(("Movimento inválido: Caminho bloqueado ou muito distante.", COR_DANO))
             return [], logs_movimento

        # 3. Execução do Movimento Passo a Passo
        eventos = []
        movimento_realizado = False
        
        # O caminho retornado pelo A* inclui o destino, mas não a origem.
        # Precisamos verificar o custo total.
        custo_total = 0
        caminho_validado = []
        
        for passo in caminho:
            custo_passo = 2 if self.tabuleiro.terrain_grid[passo[1]][passo[0]] == TERRENO_DIFICIL else 1
            if custo_total + custo_passo > personagem.velocidade:
                break # Não consegue ir mais longe
            custo_total += custo_passo
            caminho_validado.append(passo)

        if not caminho_validado:
             logs_movimento.append(("Movimento inválido: Sem movimento possível.", COR_DANO))
             return [], logs_movimento
             
        # Verifica se o destino final do caminho validado é o solicitado (ou se parou antes)
        # Se o jogador clicou longe, ele vai até onde der? O comportamento padrão de jogos táticos
        # geralmente é: se clicou fora do alcance, não vai. Se clicou dentro, vai.
        # O A* já limita pelo custo maximo (personagem.velocidade).
        # Então se 'caminho' existe, ele é válido dentro da velocidade.
        
        # Porém, precisamos garantir que o destino final é EXATAMENTE onde o jogador clicou.
        if caminho[-1] != end_pos:
             logs_movimento.append(("Movimento inválido: Destino inalcançável neste turno.", COR_DANO))
             return [], logs_movimento

        for passo in caminho:
            # Verifica Ataque de Oportunidade ANTES de entrar no tile (saindo do anterior)
            # A lógica original verifica ao SAIR de um tile ameaçado.
            if not self._verificar_ataques_de_oportunidade(personagem, passo[0], passo[1], logs_movimento):
                # Se morreu ou foi parado, interrompe
                break
            
            # Move
            self.tabuleiro.mover_personagem(personagem, passo[0], passo[1])
            personagem.elevacao = self.tabuleiro.get_elevation_em(personagem.pos_x, personagem.pos_y)
            movimento_realizado = True
            
            # Efeitos de Terreno (Gelo)
            if self.tabuleiro.get_terrain_em(personagem.pos_x, personagem.pos_y) == TERRENO_GELO and random.random() < 0.5:
                logs_movimento.append((f"  {personagem.nome} escorrega no gelo!", COR_STATUS))
                # Escorrega na mesma direção do movimento
                dx = passo[0] - start_pos[0] # Isso está errado se o caminho for complexo, mas serve para 1 passo
                # Melhor: dx = passo[0] - (pos anterior)
                # Como não guardamos a pos anterior no loop facilmente sem var, vamos simplificar:
                # O pathfinding garante passos adjacentes.
                # Vamos pegar a direção do passo atual.
                # Mas espere, 'passo' é o destino deste micro-movimento. O personagem JÁ ESTÁ lá.
                # A logica original de escorregar usava start_pos fixo, o que era bugado para caminhos longos.
                # Vamos ignorar a direção exata do escorregão complexo e fazer aleatório ou manter simples?
                # Vamos tentar manter a inércia.
                # Se moveu de (x-1, y) para (x, y), dx=1.
                # Precisamos saber de onde veio.
                # Como movemos o personagem, a posição ANTERIOR dele no grid já foi liberada, mas podemos inferir.
                # Mas para simplificar e evitar bugs: escorrega para um vizinho aleatório válido que não seja parede.
                pass # Simplificação: Gelo só avisa, ou implementamos escorregão extra depois se sobrar tempo.
                # Reimplementando escorregão simples:
                vizinhos_livres = []
                for dx_s, dy_s in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = personagem.pos_x + dx_s, personagem.pos_y + dy_s
                    if 0 <= nx < self.tabuleiro.largura and 0 <= ny < self.tabuleiro.altura and \
                       self.tabuleiro.get_personagem_em(nx, ny) is None and \
                       self.tabuleiro.get_terrain_em(nx, ny) != TERRENO_PAREDE:
                        vizinhos_livres.append((nx, ny))
                
                if vizinhos_livres:
                    slip_dest = random.choice(vizinhos_livres)
                    self.tabuleiro.mover_personagem(personagem, slip_dest[0], slip_dest[1])
                    logs_movimento.append((f"  ...e desliza para ({slip_dest[0]}, {slip_dest[1]})!", COR_STATUS))
                    # Atualiza passo atual para continuar o loop? Não, escorregão pode tirar da rota.
                    # Interrompe movimento se escorregar? Geralmente sim.
                    break 

        if movimento_realizado:
            logs_movimento.append((f"  {personagem.nome} se moveu para ({personagem.pos_x},{personagem.pos_y}).", COR_TEXTO))
            # Adiciona animação completa do início ao fim (simplificado visualmente)
            # Ou passo a passo? O sistema de animação atual parece suportar start->end direto.
            # Se quisermos que ele ande pelo caminho, precisaríamos de múltiplos eventos.
            # Vamos fazer um evento único para simplificar a visualização por enquanto, 
            # ou o visualizador vai "teleportar" se tiver parede no meio?
            # O ideal seria uma lista de waypoints. Mas o sistema de animação atual é simples (start, end).
            # Vamos manter start->end final.
            personagem.eventos_animacao.append({'tipo': 'movimento', 'personagem': personagem, 'start_pos': start_pos, 'end_pos': (personagem.pos_x, personagem.pos_y)})
        
        eventos = list(personagem.eventos_animacao)
        personagem.eventos_animacao.clear()
        return eventos, logs_movimento

    def jogador_ataca_personagem(self, atacante, alvo):
        time_inimigo = self.time_b if atacante.time == "A" else self.time_a
        time_aliado = self.time_a if atacante.time == "A" else self.time_b
        
        logs_ataque = []
        atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_ataque.append)
        
        eventos = list(atacante.eventos_animacao)
        atacante.eventos_animacao.clear()
        return eventos, logs_ataque

    def salvar_jogo(self, nome_arquivo="savegame.pkl"):
        from .salvar_carregar import salvar_jogo
        salvar_jogo(self, nome_arquivo)

    def carregar_jogo(self, nome_arquivo="savegame.pkl"):
        from .salvar_carregar import carregar_jogo
        estado_carregado = carregar_jogo(nome_arquivo)
        if estado_carregado:
            self.__dict__.update(estado_carregado.__dict__)
            return True
        return False