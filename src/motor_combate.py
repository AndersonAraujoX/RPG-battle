import random
import heapq
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL, TERRENO_GELO, TERRENO_FOGO
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Paladino, Druida, Bruxo, Goblin, Esqueleto, Kobold
from .utils import calcular_distancia
from .config import COR_TEXTO, COR_DANO, COR_CRITICO, COR_STATUS, COR_CURA, COR_XP, COR_DANO_FOGO

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

            if atacante.estado == "MORTO":
                # Should rely on remove_dead logic, but if still in list:
                 self.finalizar_turno(logs_turno, eventos_turno)
                 return {'logs': logs_turno, 'eventos': eventos_turno}

            if atacante.estado == "INCONSCIENTE":
                logs_turno.append((f"Vez de {atacante.nome} (INCONSCIENTE)", COR_TEXTO))
                atacante.realizar_teste_morte(logs_turno.append)
                self.finalizar_turno(logs_turno, eventos_turno)
                return {'logs': logs_turno, 'eventos': eventos_turno}
            
            # Check if start of turn
            # Assuming avancar_turno calls iniciar_turno for everyone or current.
            # But here we are polled every frame.
            # State management:
            # We need to know if we just started processing this character's turn to log "Vez de..." once?
            # Existing code logs "Vez de..." every call. That's spammy if we call multiple times per turn.
            # Let's check a flag on MotorCombate or assume the UI handles logs gracefully?
            # Actually, proximo_passo is called ONCE by the Game Loop per "Action Step".
            # The Game Loop waits for animation/input before calling again.
            # So if we return, the game waits.
            # We want to return after ONE action, but NOT end the turn unless it's "passar".
            
            # Logic:
            # 1. Get Action from deciding logic (which now checks flags).
            # 2. If 'passar', finalize turn.
            # 3. Else, execute action, set flag, return (so game can animate).
            # 4. Next call to proximo_passo will see flags set and ask deciding logic again.
            
            if not getattr(atacante, 'turn_started_log', False):
                 logs_turno.append((f"Vez de {atacante.nome}", COR_TEXTO))
                 atacante.turn_started_log = True
                 
                 # --- PERK: Aura de Vitalidade (Koema) ---
                 if atacante.tem_perk("aura_vitalidade"):
                     aliados_proximos = [p for p in (self.time_a if atacante.time == "A" else self.time_b) if p.esta_vivo and p != atacante and calcular_distancia(atacante, p) <= 1.5]
                     if aliados_proximos:
                         logs_turno.append((f"  Aura de Vitalidade de {atacante.nome} cura aliados próximos!", COR_CURA))
                         for aliado in aliados_proximos:
                             aliado.receber_cura(atacante.mod_sab + 2, logs_turno.append)

                 # --- PERK: Inspiração (Rilem) ---
                 if atacante.tem_perk("inspiracao"):
                      # Aplica buff de movimento em todos os aliados
                      aliados = (self.time_a if atacante.time == "A" else self.time_b)
                      for aliado in aliados:
                          if aliado.esta_vivo:
                              aliado.aplicar_status_efeito("Inspirado", 1, logs_turno.append, bonus_velocidade=2)
                      logs_turno.append((f"  {atacante.nome} inspira seus aliados! (+Movimento)", COR_STATUS))

            
            time_inimigo = [p for p in (self.time_b if atacante.time == "A" else self.time_a) if p.esta_vivo and p.estado != "MORTO"]
            time_aliado = [p for p in (self.time_a if atacante.time == "A" else self.time_b) if p.esta_vivo]

            if not time_inimigo:
                acao = {'acao': 'passar'}
            else:
                acao = atacante.decidir_acao(time_inimigo, time_aliado, self.tabuleiro, logs_turno)
            
            # Check for Pass
            if acao['acao'] == 'passar':
                 logs_turno.append((f"  {atacante.nome} encerra o turno.", COR_TEXTO))
                 self.finalizar_turno(logs_turno, eventos_turno)
                 atacante.turn_started_log = False # Reset for next time (though new turn resets flags usually)
                 return {'logs': logs_turno, 'eventos': eventos_turno}

            # Execute other actions and return WITHOUT finalizing turn
            # Note: The following if/elif blocks handle execution.
            # We just need to ensure we don't fall through to `finalizar_turno` at the end of the method.
            # We will return early after execution.


            self._executar_acao(atacante, acao, time_inimigo, time_aliado, logs_turno)
            return {'logs': logs_turno, 'eventos': eventos_turno}



        # End of step: Do NOT finalize turn. Return so game loop can animate/wait.
        # Next loop will ask decidir_acao again.
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
        if personagem_movendo.tem_status("Desengajar"):
            return True # Imune

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
            self.tabuleiro.grid[phoenix.pos_y][phoenix.pos_x] = phoenix
            
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
                self.tabuleiro.grid[y][x] = minion
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
        ativo_a = any(p.esta_vivo and p.estado not in ["INCONSCIENTE", "MORTO"] for p in self.time_a)
        ativo_b = any(p.esta_vivo and p.estado not in ["INCONSCIENTE", "MORTO"] for p in self.time_b)
        
        if not ativo_a: self.vencedor = f"Time B"
        elif not ativo_b: self.vencedor = f"Time A"
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

    def get_alcance_habilidade(self, atacante, habilidade_key):
        """Retorna (lista_de_tiles_validos, tipo_alcance) para visualização"""
        if habilidade_key not in atacante.habilidades: return [], None
        
        dados = atacante.habilidades[habilidade_key]
        alcance = dados['alcance']
        tipo = dados['tipo']
        
        tiles = []
        # Simple radial range for now
        # For 'area' abilities (like Fireball), range is where you can CENTER it.
        # For 'alvo' abilities, range is where you can target.
        
        # Using a simple box range for visualization matching grid logic
        for y in range(max(0, atacante.pos_y - alcance), min(self.tabuleiro.altura, atacante.pos_y + alcance + 1)):
            for x in range(max(0, atacante.pos_x - alcance), min(self.tabuleiro.largura, atacante.pos_x + alcance + 1)):
                if calcular_distancia(atacante, type('obj', (object,), {'pos_x': x, 'pos_y': y})) <= alcance:
                     # For 'area', we might check line of sight to the center point?
                     # For now, just distance
                     tiles.append((x, y))
                     
        return tiles, tipo

    def jogador_usar_habilidade(self, atacante, habilidade_key, alvo=None, pos_alvo=None):
        logs = []
        eventos = []
        
        if habilidade_key not in atacante.habilidades:
             logs.append((f"Erro: Habilidade {habilidade_key} inexistente.", COR_DANO))
             return eventos, logs
             
        dados = atacante.habilidades[habilidade_key]
        # Check Cooldowns
        if habilidade_key in atacante.cooldowns and atacante.cooldowns[habilidade_key] > 0:
             logs.append((f"{dados['nome']} em recarga ({atacante.cooldowns[habilidade_key]} turnos)!", COR_DANO))
             return eventos, logs

        # Check Resources (Mana/Energia/Fe presumed based on class)
        custo = dados.get('custo', 0)
        recurso_tipo = "mana" # Default
        
        # Simple heuristic or explicit type if defined
        if hasattr(atacante, 'energia_atual') and atacante.energia_max > 0 and atacante.mana_max == 0:
            recurso_tipo = "energia"
        
        if recurso_tipo == "mana" and atacante.mana_atual < custo:
             logs.append((f"Mana insuficiente para {dados['nome']}!", COR_DANO))
             return eventos, logs
        elif recurso_tipo == "energia" and atacante.energia_atual < custo:
             logs.append((f"Energia insuficiente para {dados['nome']}!", COR_DANO))
             return eventos, logs
             
        # Consume Resource
        if recurso_tipo == "mana": atacante.mana_atual -= custo
        elif recurso_tipo == "energia": atacante.energia_atual -= custo
        
        nome = dados['nome']
        logs.append((f"{atacante.nome} usa {nome}!", COR_STATUS))
        
        if habilidade_key == 'bola_de_fogo':
             cx, cy = pos_alvo
             raio = dados['area']
             alvos = self.tabuleiro.get_personagens_em_area(cx, cy, raio)
             
             eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': None, 'habilidade': 'bola_de_fogo'}) # Visual only
             
             dano_base = sum(random.randint(1, 6) for _ in range(3)) # 3d6 simplified
             
             logs.append((f"  A Bola de Fogo explode em ({cx}, {cy})!", COR_DANO))
             
             for vitima in alvos:
                  dano = dano_base
                  # Dex save? Simplified: half damage if high dex? No, full damage for now.
                  logs.append((f"  {vitima.nome} é atingido pela explosão!", COR_TEXTO))
                  vitima.receber_dano(dano, atacante, self.tabuleiro, logs.append, tipo_dano="Fogo")
             
             # Interação com Terreno (Cria Fogo)
             for y in range(cy - raio, cy + raio + 1):
                 for x in range(cx - raio, cx + raio + 1):
                     self.tabuleiro.aplicar_dano_terreno(x, y, "Fogo", logger=logs.append)
                  
        elif habilidade_key == 'raio_de_gelo':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'raio_de_gelo'})
                 dano = random.randint(1, 10) + atacante.mod_int
                 alvo.receber_dano(dano, atacante, self.tabuleiro, logs.append, tipo_dano="Gelo")
                 # Slow effect?
                 alvo.aplicar_status_efeito("Lentidão", 2, logs.append, velocidade_reducao=2)

        elif habilidade_key == 'tempestade_fogo':
             cx, cy = pos_alvo
             raio = dados['area']
             alvos = self.tabuleiro.get_personagens_em_area(cx, cy, raio)
             
             eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': None, 'habilidade': 'tempestade_fogo'})
             
             # Dano fixo 10 + mod_int (Assumption) or just 10? Plan said 10. Let's add mod_int for scaling.
             dano_base = 10 + atacante.mod_int 
             
             logs.append((f"  A Tempestade de Fogo engolfe a área em ({cx}, {cy})!", COR_DANO))
             
             for vitima in alvos:
                  logs.append((f"  {vitima.nome} queima na tempestade!", COR_TEXTO))
                  vitima.receber_dano(dano_base, atacante, self.tabuleiro, logs.append, tipo_dano="Fogo")

        elif habilidade_key == 'explosao_arcana':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'explosao_arcana'})
                 dano = 15 + atacante.mod_int
                 alvo.receber_dano(dano, atacante, self.tabuleiro, logs.append, tipo_dano="Magico")

        elif habilidade_key == 'provocar':
             eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': None, 'habilidade': 'provocar'})
             logs.append((f"{atacante.nome} ruge, provocando os inimigos!", COR_STATUS))
             raio = dados.get('area', 2)
             alvos_area = self.tabuleiro.get_personagens_em_area(atacante.pos_x, atacante.pos_y, raio)
             for inimigo in alvos_area:
                 if inimigo.time != atacante.time and inimigo.esta_vivo:
                     inimigo.aplicar_status_efeito("Provocado", 3, logs.append, provocador=atacante)
             atacante.cooldowns['provocar'] = atacante.cooldown_max.get('provocar', 3)

        elif habilidade_key == 'golpe_flamejante':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'golpe_flamejante'})
                 atacante.atacar(alvo, [], [], self.tabuleiro, logger=logs.append, tipo_dano_override="Fogo")
                 atacante.cooldowns['golpe_flamejante'] = atacante.cooldown_max.get('golpe_flamejante', 2)

        elif habilidade_key == 'truque_sujo':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'truque_sujo'})
                 dano = random.randint(1, 6) + atacante.mod_des
                 alvo.receber_dano(dano, atacante, self.tabuleiro, logs.append, tipo_dano="Fisico")
                 alvo.aplicar_status_efeito("Ataque Reduzido", 2, logs.append, bonus_ataque_fixo=-2)

        elif habilidade_key == 'primeiros_socorros':
             if alvo:
                 eventos.append({'tipo': 'cura', 'alvo': alvo, 'cura': dados['cura']})
                 alvo.receber_cura(dados['cura'], logs.append)

        elif habilidade_key == 'comando_tatico':
             eventos.append({'tipo': 'buff_global', 'origem': atacante, 'habilidade': 'comando_tatico'})
             logs.append((f"{atacante.nome} emite ordens táticas!", COR_STATUS))
             time_aliado = self.time_a if atacante.time == "A" else self.time_b
             for aliado in time_aliado:
                 if aliado.esta_vivo:
                     aliado.aplicar_status_efeito("Ataque Aumentado", 3, logs.append, bonus_dano_ataque=2, bonus_ataque_fixo=2)

        elif habilidade_key == 'quebrar_defesa':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'quebrar_defesa'})
                 alvo.aplicar_status_efeito("Defesa Quebrada", 3, logs.append, resistencia_dano_percentual=-0.2)

        elif habilidade_key == 'provocar':
             # Area effect around self
             eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': None, 'habilidade': 'provocar'})
             logs.append((f"{atacante.nome} ruge, provocando os inimigos!", COR_STATUS))
             
             raio = dados['area'] # 3x3 around self = radius 1
             alvos_area = self.tabuleiro.get_personagens_em_area(atacante.pos_x, atacante.pos_y, raio)
             for inimigo in alvos_area:
                 if inimigo.time != atacante.time and inimigo.esta_vivo:
                     inimigo.aplicar_status_efeito("Provocado", 3, logs.append, provocador=atacante)
             
             # Cooldown handling (manual for now since cooldowns dict exists but not auto-ticked or checked fully yet)
             atacante.cooldowns['provocar'] = atacante.cooldown_max.get('provocar', 3)

        elif habilidade_key == 'golpe_flamejante':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'golpe_flamejante'})
                 # Base attack + extra fire damage
                 atacante.atacar(alvo, [], [], self.tabuleiro, logger=logs.append, tipo_dano_override="Fogo")
                 atacante.cooldowns['golpe_flamejante'] = atacante.cooldown_max.get('golpe_flamejante', 2)

        elif habilidade_key == 'truque_sujo':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'truque_sujo'})
                 dano = random.randint(1, 6) + atacante.mod_des
                 alvo.receber_dano(dano, atacante, self.tabuleiro, logs.append, tipo_dano="Fisico")
                 alvo.aplicar_status_efeito("Ataque Reduzido", 2, logs.append, bonus_ataque_fixo=-2)

        elif habilidade_key == 'primeiros_socorros':
             if alvo:
                 eventos.append({'tipo': 'cura', 'alvo': alvo, 'cura': dados['cura']})
                 alvo.receber_cura(dados['cura'], logs.append)

        elif habilidade_key == 'comando_tatico':
             eventos.append({'tipo': 'buff_global', 'origem': atacante, 'habilidade': 'comando_tatico'})
             logs.append((f"{atacante.nome} emite ordens táticas!", COR_STATUS))
             time_aliado = self.time_a if atacante.time == "A" else self.time_b
             for aliado in time_aliado:
                 if aliado.esta_vivo:
                     aliado.aplicar_status_efeito("Ataque Aumentado", 3, logs.append, bonus_dano_ataque=2, bonus_ataque_fixo=2)
                     
             # Resource check was simplistic (mana_atual vs custo). Rilem uses Energy?
             # My generic check used atacante.mana_atual. I need to fix check logic for Energy based chars.
             # See below adjustment.

        elif habilidade_key == 'quebrar_defesa':
             if alvo:
                 eventos.append({'tipo': 'ataque', 'atacante': atacante, 'alvo': alvo, 'habilidade': 'quebrar_defesa'})
                 alvo.aplicar_status_efeito("Defesa Quebrada", 3, logs.append, resistencia_dano_percentual=-0.2) # Takes 20% more damage logic or just AC malus?
                 # My AC logic checks effects manually? No, AC property checks 'bonus_ac' from effects?
                 # Need to implement logic in AC property or status effect tick if I want DebuffAC.
                 # For now, let's use a text log and maybe simple logic.
                 # Actually Personagem.ac doesn't check effects for AC bonus yet in my brief view.
                 # Let's verify Personagem logic later. For now apply effect.
                 pass

        return eventos, logs

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
        
        # --- PERK: Lâmina Incendiária (Novak) ---
        if atacante.tem_perk("lamina_incendiaria") and alvo.esta_vivo is not None: # Check simple attack assumption
             self.tabuleiro.aplicar_dano_terreno(alvo.pos_x, alvo.pos_y, "Fogo", logger=lambda x,y: None) # Silent create text? Or log?
             # aplicar_dano_terreno actually damages if stand, but visual update handles creation?
             # My visual update logic relies on terrain_grid.
             # aplicar_dano_terreno does NOT set terrain.
             self.tabuleiro.terrain_grid[alvo.pos_y][alvo.pos_x] = TERRENO_FOGO
             logs_ataque.append((f"  [Lâmina Incendiária] O chão sob {alvo.nome} pega fogo!", COR_DANO_FOGO))

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
    def _executar_acao(self, atacante, acao, time_inimigo, time_aliado, logs_turno):
        from .personagens import Goblin
        if acao['acao'] == 'atacar':
            alvo = acao['alvo']
            if calcular_distancia(atacante, alvo) > atacante.alcance:
                logs_turno.append((f"  {atacante.nome} tenta atacar {alvo.nome} mas está fora de alcance!", COR_TEXTO))
                # Move logic handled by decidier now? 
                # Existing logic tried to move automatically.
                # With new economy, "atacar" implies in range.
                # If AI returned "atacar" out of range, it's a bug or old logic.
                # Let's keep the fallback for safety but charge movement?
                # Better: Assume decidier handles checking range. 
                # If here and out of range -> Fail action? Or Auto-Move (costing move)?
                # Let's Fail to encourage correct AI logic.
                pass
            else:
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                atacante.acao_realizada = True

        elif acao['acao'] == 'mover':
            alvo = acao['alvo']
            self._mover_personagem(atacante, alvo, logs_turno)
            atacante.movimento_realizado = True

        elif acao['acao'] == 'fugir':
            self._fugir(atacante, time_inimigo, logs_turno)
            atacante.movimento_realizado = True
            atacante.acao_realizada = True # Dash action? Fugir usually implies full turn in old logic.

        elif acao['acao'] == 'pegar_item':
            item = acao['item']
            atacante.inventario.append(item)
            self.tabuleiro.itens_no_chao[atacante.pos_y][atacante.pos_x] = None
            logs_turno.append((f"  {atacante.nome} pegou {item.nome} do chão.", (255, 215, 0)))
            atacante.acao_realizada = True # Standard Interaction is object interaction (free) or action? 
            # Let's say Free Object Interaction (once per turn) or Action. 5e says 1 free.
            # Let's make it Free but limited? Or Action?
            # Code says "acao_realizada". Let's stick to Action for picking up to avoid abuse.

        elif acao['acao'] == 'usar_item':
             # Item usage handled in decidir_acao (method called on item).
             # We just need to mark action used.
             atacante.acao_realizada = True

        elif acao['acao'] == 'usar_habilidade':
            habilidade = acao['habilidade']
            # Determine if Action or Bonus Action
            # Simplified: All abilities are Actions unless specified?
            # Surto de Ação = Free/Special. 
            # Convocar Goblin = Action.
            # Forma de Urso = Bonus Action (Druid).
            # Maldicao = Action/Bonus?
            # Let's assume most are Actions.
            
            is_bonus = habilidade in ['forma_de_urso', 'surto_de_acao'] # Example
            
            if habilidade == 'surto_acao':
                logs_turno.append((f"  {atacante.nome} usa Surto de Ação!", COR_STATUS))
                atacante.acao_realizada = False # Grant extra action
                atacante.cooldowns['surto_acao'] = atacante.habilidades['surto_acao']['cooldown']

            elif habilidade == 'ataque_giratorio':
                 logs_turno.append((f"  {atacante.nome} gira sua arma atingindo todos ao redor!", COR_DANO))
                 atacante.cooldowns['ataque_giratorio'] = atacante.habilidades['ataque_giratorio']['cooldown']
                 adjacentes = [p for p in time_inimigo if p.esta_vivo and calcular_distancia(atacante, p) <= 1]
                 if adjacentes:
                     for alvo_adj in adjacentes:
                         atacante.atacar(alvo_adj, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                 else:
                     logs_turno.append("  Mas não atinge ninguém!", COR_TEXTO)
                 atacante.acao_realizada = True

            elif habilidade == 'furia':
                logs_turno.append((f"  {atacante.nome} entra em FÚRIA!", COR_STATUS))
                atacante.aplicar_status_efeito("Fúria", 10, logs_turno.append) # Furia needs implement definition? Or just buff stats manually?
                # Ideally Furia is a status.
                atacante.cooldowns['furia'] = atacante.habilidades['furia']['cooldown']
                atacante.acao_bonus_realizada = True

            elif habilidade == 'ataque_descuidado':
                logs_turno.append((f"  {atacante.nome} prepara um Ataque Descuidado!", COR_STATUS))
                atacante.cooldowns['ataque_descuidado'] = atacante.habilidades['ataque_descuidado']['cooldown']
                # Attack immediate
                alvo = acao['alvo']
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, vantagem=True) # Needs change in atacar sig?
                # Old logic handled it via cooldown check INSIDE atacar.
                # If we call atacar here, it might DOUBLE apply if logic remains inside.
                # Best to rely on Standard Attack button for Passive/Buff actions?
                # BUT this is an Active Skill Button press.
                # So we execute attack here.
                atacante.acao_realizada = True

            elif habilidade == 'missil_magico':
                alvo = acao['alvo']
                # Guaranteed hit x3
                dano =sum(random.randint(1,4)+1 for _ in range(3))
                logs_turno.append((f"  Mísseis Mágicos atingem {alvo.nome} causando {dano} de dano!", (100, 100, 255)))
                alvo.receber_dano(dano, atacante, self.tabuleiro, logs_turno.append)
                atacante.mana_atual -= atacante.custo_habilidades.get('missil_magico', 5)
                atacante.acao_realizada = True

            elif habilidade == 'curar_ferimentos':
                alvo = acao['alvo']
                cura = random.randint(1,8) + 3
                logs_turno.append((f"  {atacante.nome} cura {alvo.nome} em {cura} PV.", COR_XP))
                alvo.receber_cura(cura, logs_turno.append)
                atacante.fe_atual -= atacante.custo_habilidades.get('curar_ferimentos', 3)
                atacante.acao_realizada = True

            elif habilidade == 'lay_on_hands':
                alvo = acao['alvo']
                cura = atacante.nivel * 5
                logs_turno.append((f"  {atacante.nome} impõe as mãos e cura {alvo.nome} em {cura} PV.", COR_XP))
                alvo.receber_cura(cura, logs_turno.append)
                if hasattr(atacante, 'usos_lay_on_hands'): atacante.usos_lay_on_hands -= 1
                atacante.acao_realizada = True

            elif habilidade == 'smite_evil':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} desfere um Golpe Divino!", (255, 255, 100)))
                atacante.cooldowns['smite_evil'] = 3
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, habilidade='smite_evil')
                atacante.acao_realizada = True

            elif habilidade == 'esconder':
                logs_turno.append((f"  {atacante.nome} tenta se esconder nas sombras.", COR_STATUS))
                atacante.aplicar_status_efeito("Escondido", 2, logs_turno.append) # Need status
                atacante.energia_atual -= atacante.custo_habilidades.get('esconder', 5)
                atacante.acao_bonus_realizada = True

            elif habilidade == 'golpe_sombrio':
                 alvo = acao['alvo']
                 logs_turno.append((f"  {atacante.nome} desfere um Golpe Sombrio!", (100, 0, 100)))
                 atacante.energia_atual -= atacante.custo_habilidades.get('golpe_sombrio', 5)
                 dano_extra = sum(random.randint(1,6) for _ in range(2))
                 atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, bonus_dano_extra=dano_extra)
                 atacante.acao_realizada = True
            
            elif habilidade == 'tiro_duplo':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} dispara duas flechas!", COR_DANO))
                atacante.cooldowns['tiro_duplo'] = 3
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                if alvo.esta_vivo:
                     atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                atacante.acao_realizada = True

            # --- Protagonist Skills ---
            elif habilidade == 'provocar':
                logs_turno.append((f"  {atacante.nome} ruge, provocando os inimigos!", COR_STATUS))
                raio = 3
                afetados = self.tabuleiro.get_personagens_em_area(atacante.pos_x, atacante.pos_y, raio)
                for p in afetados:
                    if p.time != atacante.time and p.esta_vivo:
                         p.aplicar_status_efeito("Provocado", 3, logs_turno.append)
                atacante.cooldowns['provocar'] = atacante.habilidades['provocar']['cooldown']
                atacante.acao_realizada = True

            elif habilidade == 'golpe_flamejante':
                 alvo = acao['alvo']
                 logs_turno.append((f"  {atacante.nome} executa um Golpe Flamejante!", COR_DANO_FOGO))
                 atacante.cooldowns['golpe_flamejante'] = atacante.habilidades['golpe_flamejante']['cooldown']
                 atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, bonus_dano_extra=5, tipo_dano_override="Fogo")
                 
                 # --- PERK: Terra Arrasada (Yukito) ---
                 if atacante.tem_perk("terra_arrasada"):
                      self.tabuleiro.terrain_grid[alvo.pos_y][alvo.pos_x] = TERRENO_FOGO
                      logs_turno.append((f"  [Terra Arrasada] A terra queima!", COR_DANO_FOGO))
                      
                 atacante.acao_realizada = True

            elif habilidade == 'truque_sujo':
                 alvo = acao['alvo']
                 logs_turno.append((f"  {atacante.nome} usa um Truque Sujo!", COR_DANO))
                 atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                 if alvo.esta_vivo:
                     alvo.aplicar_status_efeito("Ataque Reduzido", 3, logs_turno.append)
                 # Cost managed via Action logic or Resource? Config says 'custo': 5 (Mana).
                 if 'truque_sujo' in atacante.custo_habilidades and hasattr(atacante, 'mana_atual'):
                     atacante.mana_atual -= atacante.custo_habilidades['truque_sujo']
                 atacante.acao_realizada = True

            elif habilidade == 'primeiros_socorros':
                alvo = acao['alvo']
                cura = 10
                logs_turno.append((f"  {atacante.nome} aplica Primeiros Socorros em {alvo.nome}.", COR_XP))
                alvo.receber_cura(cura, logs_turno.append)
                if 'primeiros_socorros' in atacante.custo_habilidades and hasattr(atacante, 'mana_atual'):
                     atacante.mana_atual -= atacante.custo_habilidades['primeiros_socorros']
                atacante.acao_realizada = True

            elif habilidade == 'comando_tatico':
                 logs_turno.append((f"  {atacante.nome} emite um Comando Tático!", COR_STATUS))
                 for aliado in time_aliado:
                     if aliado.esta_vivo:
                         aliado.aplicar_status_efeito("Comando Tatico", 3, logs_turno.append) # Buff
                 if 'comando_tatico' in atacante.custo_habilidades and hasattr(atacante, 'energia_atual'):
                     atacante.energia_atual -= atacante.custo_habilidades['comando_tatico']
                 atacante.acao_realizada = True

            elif habilidade == 'quebrar_defesa':
                 alvo = acao['alvo']
                 logs_turno.append((f"  {atacante.nome} tenta Quebrar a Defesa de {alvo.nome}!", COR_STATUS))
                 
                 duracao = 3
                 if atacante.tem_perk("analise_profunda"):
                     duracao = 10 # Permanente na prática para combate
                     logs_turno.append((f"  [Análise Profunda] O debuff durará mais tempo!", COR_STATUS))

                 alvo.aplicar_status_efeito("Defesa Quebrada", duracao, logs_turno.append)
                 if 'quebrar_defesa' in atacante.custo_habilidades and hasattr(atacante, 'energia_atual'):
                     atacante.energia_atual -= atacante.custo_habilidades['quebrar_defesa']
                 atacante.acao_realizada = True

            elif habilidade == 'tempestade_fogo':
                 pos_centro = acao.get('pos_conjuracao')
                 # Fallback if UI sends target
                 if not pos_centro and 'alvo' in acao:
                     pos_centro = (acao['alvo'].pos_x, acao['alvo'].pos_y)
                 
                 if pos_centro:
                     logs_turno.append((f"  {atacante.nome} conjura Tempestade de Fogo!", COR_DANO_FOGO))
                     raio = 1
                     alvos_area = self.tabuleiro.get_personagens_em_area(pos_centro[0], pos_centro[1], raio)
                     dano = 10
                     for p in alvos_area:
                         p.receber_dano(dano, atacante, self.tabuleiro, logs_turno.append, tipo_dano="Fogo")
                     
                     self.tabuleiro.aplicar_dano_terreno(pos_centro[0], pos_centro[1], "Fogo", logs_turno.append) # Only center? Or Area?
                     # Map generic apply terrain area logic? For now center.
                     
                     atacante.mana_atual -= atacante.custo_habilidades.get('tempestade_fogo', 15)
                     atacante.acao_realizada = True

            elif habilidade == 'explosao_arcana':
                 alvo = acao['alvo']
                 dano = 15
                 logs_turno.append((f"  {atacante.nome} dispara uma Explosão Arcana em {alvo.nome}!", (150, 0, 200)))
                 alvo.receber_dano(dano, atacante, self.tabuleiro, logs_turno.append, tipo_dano="Magico")
                 atacante.mana_atual -= atacante.custo_habilidades.get('explosao_arcana', 10)
                 atacante.acao_realizada = True

            elif habilidade == 'habilidade_desconhecida':
                # Fallback
                pass

            # KEEP EXISTING LOGIC FOR: convocar_goblin, forma_de_urso, maldicao_de_agonia, canalizar_divindade, raio_de_gelo
            elif habilidade == 'convocar_goblin':
                self._summon_minion(atacante, Goblin, logs_turno)
                atacante.acao_realizada = True
                
            elif habilidade == 'forma_de_urso':
                atacante.usar_forma_de_urso(logs_turno.append)
                atacante.acao_bonus_realizada = True

            elif habilidade == 'maldicao_de_agonia':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} amaldiçoa {alvo.nome} com Agonia!", COR_STATUS))
                atacante.mana_atual -= atacante.custo_habilidades['maldicao_de_agonia']
                alvo.aplicar_status_efeito("Amaldiçoado", 3, logs_turno.append)
                atacante.acao_realizada = True
                
            elif habilidade == 'canalizar_divindade':
                alvo_cura = acao['alvo']
                # Handle both Ally and Self logic
                custo = atacante.custo_habilidades.get('canalizar_divindade', 4)
                if atacante.tem_perk("maos_rapidas"):
                    custo = max(1, custo - 1)
                
                atacante.fe_atual -= custo
                cura = sum(random.randint(1, 6) for _ in range(2)) + atacante.mod_sab
                alvo_cura.receber_cura(cura, logs_turno.append)
                atacante.acao_realizada = True
                
            elif habilidade == 'raio_de_gelo':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} lança Raio de Gelo em {alvo.nome}!", COR_STATUS))
                atacante.mana_atual -= atacante.custo_habilidades.get('raio_de_gelo', 3)
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, tipo_dano_override="Gelo")
                self.tabuleiro.aplicar_dano_terreno(alvo.pos_x, alvo.pos_y, "Gelo", logs_turno.append)
                atacante.acao_realizada = True

            elif habilidade == 'chuva_flechas':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} dispara uma Chuva de Flechas!", COR_DANO))
                atacante.cooldowns['chuva_flechas'] = 5
                afetados = self.tabuleiro.get_personagens_em_area(alvo.pos_x, alvo.pos_y, 1)
                for vitima in afetados:
                    if vitima.esta_vivo and vitima.time != atacante.time:
                        dano = random.randint(1, 6) + atacante.mod_des
                        vitima.receber_dano(dano, atacante, self.tabuleiro, logs_turno.append, tipo_dano="Perfurante")
                atacante.acao_realizada = True
             
            elif habilidade == 'rajada_mistica':
                alvo = acao['alvo']
                logs_turno.append((f"  {atacante.nome} dispara Rajada Mística!", (150, 0, 150)))
                atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append, tipo_dano_override="Energia")
                atacante.acao_realizada = True
                 

            elif habilidade == 'bola_de_fogo':
                pos_final = acao['pos_conjuracao']
                alvo_central = acao['alvo_central']
                if (atacante.pos_x, atacante.pos_y) != pos_final:
                    self.tabuleiro.mover_personagem(atacante, pos_final[0], pos_final[1])
                    logs_turno.append((f"  {atacante.nome} se move para ({pos_final[0]},{pos_final[1]}) para a conjuração.", COR_TEXTO))
                    atacante.eventos_animacao.append({'tipo': 'movimento', 'personagem': atacante, 'start_pos': (atacante.pos_x, atacante.pos_y), 'end_pos': pos_final})
                    atacante.movimento_realizado = True # Consumes move if needed to adjust pos
                    
                logs_turno.append((f"{atacante.nome} conjura BOLA DE FOGO em ({alvo_central.pos_x},{alvo_central.pos_y})!", COR_CRITICO))
                atacante.mana_atual -= atacante.custo_habilidades['bola_de_fogo']
                alvos_afetados = self.tabuleiro.get_personagens_em_area(alvo_central.pos_x, alvo_central.pos_y, 1)
                
                dc = 8 + atacante.bonus_proficiencia + atacante.mod_int
                logs_turno.append((f"  Dificuldade do Teste (DC): {dc}", (200, 200, 255)))

                atacante.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': atacante, 'x': alvo_central.pos_x, 'y': alvo_central.pos_y, 'raio': 1})
                if atacante.sound_player: atacante.sound_player('attack')
                
                if atacante.sound_player: atacante.sound_player('attack')
                
                # --- PERK: Poço de Gravidade (Yukito) ---
                if atacante.tem_perk("poco_gravidade"):
                    logs_turno.append((f"  [Poço de Gravidade] Inimigos são puxados para o centro!", (150, 0, 200)))
                    for vitima in alvos_afetados:
                         if vitima.pos_x != alvo_central.pos_x or vitima.pos_y != alvo_central.pos_y:
                             # Move towards center
                             self.tabuleiro.mover_personagem(vitima, alvo_central.pos_x, alvo_central.pos_y) 

                for vitima in alvos_afetados:
                     dano_base = sum(random.randint(1, 6) for _ in range(3)) 
                     dano_rolado = sum(random.randint(1, 6) for _ in range(3))
                     
                     sucesso, msg_teste = vitima.fazer_teste_resistencia('destreza', dc, logs_turno.append)
                     
                     dano_final = dano_rolado
                     if sucesso:
                         dano_final = dano_rolado // 2
                         logs_turno.append((f"  Sucesso! Dano reduzido pela metade ({dano_rolado} -> {dano_final}).", (100, 255, 100)))
                     else:
                         logs_turno.append((f"  Falha no teste. Dano completo ({dano_final}).", COR_DANO))
                         
                     vitima.receber_dano(dano_final, atacante, self.tabuleiro, logs_turno.append, tipo_dano="Fogo")
                
                # Interação Elemental em Área
                for y in range(alvo_central.pos_y - 1, alvo_central.pos_y + 2):
                    for x in range(alvo_central.pos_x - 1, alvo_central.pos_x + 2):
                        self.tabuleiro.aplicar_dano_terreno(x, y, "Fogo", logs_turno.append)
                
                atacante.acao_realizada = True

