import random
import heapq
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL, TERRENO_GELO
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold
from .utils import calcular_distancia
from .config import COR_TEXTO, COR_DANO, COR_CRITICO, COR_STATUS, COR_CURA

class MotorCombate:
    def __init__(self, args_times, gerar_terreno=False, mapa_custom=None, sound_player=None, modo_chefe=False, stats_chefe=None, boss_class=None):
        self.tabuleiro = Tabuleiro(20, 20)
        if mapa_custom:
            self.tabuleiro.terrain_grid = mapa_custom
        elif gerar_terreno:
            self.tabuleiro.gerar_terreno_aleatorio()
        
        self.sound_player = sound_player
        self.time_a, self.time_b = self._setup_times(args_times, modo_chefe, stats_chefe, boss_class)
        
        if not self.time_a or not self.time_b:
            raise ValueError("Ambos os times precisam de pelo menos um personagem.")
            
        self.combatentes = self.time_a + self.time_b
        for p in self.combatentes: 
            p.rolar_iniciativa()
            
        self.ordem_de_combate = sorted(self.combatentes, key=lambda x: x.iniciativa, reverse=True)
        self.turno = 1
        self.combatente_atual_idx = 0
        self.vencedor = None

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
                    if random.random() < 0.3:
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
            elif acao['acao'] == 'passar':
                logs_turno.append((f"  {atacante.nome} passa o turno.", COR_TEXTO))
        
        self.finalizar_turno(logs_turno, eventos_turno)
        return {'logs': logs_turno, 'eventos': eventos_turno}

    def finalizar_turno(self, logs_turno, eventos_turno):
        for p in self.combatentes:
            eventos_turno.extend(p.eventos_animacao)
            p.eventos_animacao.clear()
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
                if abs(dx) + abs(dy) > p.velocidade: continue
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
                if abs(dx) + abs(dy) > p.alcance: continue
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

    def jogador_move_personagem(self, personagem, novo_x, novo_y):
        logs_movimento = []
        if not self._verificar_ataques_de_oportunidade(personagem, novo_x, novo_y, logs_movimento):
            eventos = list(personagem.eventos_animacao)
            personagem.eventos_animacao.clear()
            return eventos, logs_movimento

        start_pos = (personagem.pos_x, personagem.pos_y)
        self.tabuleiro.mover_personagem(personagem, novo_x, novo_y)
        personagem.eventos_animacao.append({'tipo': 'movimento', 'personagem': personagem, 'start_pos': start_pos, 'end_pos': (novo_x, novo_y)})
        
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