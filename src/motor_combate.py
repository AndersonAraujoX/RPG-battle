import random
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL, TERRENO_GELO
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe, Druida, Bruxo, Goblin
# ...
                elif habilidade == 'convocar_goblin':
                    self._summon_minion(atacante, Goblin, logs_turno)
                elif habilidade == 'forma_de_urso':
                    atacante.usar_forma_de_urso(logs_turno.append)
                elif habilidade == 'maldicao_de_agonia':
                    alvo = acao['alvo']
                    logs_turno.append(f"  {atacante.nome} amaldiçoa {alvo.nome} com Agonia!")
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
                    logs_turno.append(f"  {atacante.nome} lança Raio de Gelo em {alvo.nome}!")
                    atacante.mana_atual -= atacante.custo_habilidades['raio_de_gelo']
                    
                    # Perform the attack
                    atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)

                    # Chance to freeze the ground
                    if random.random() < 0.3: # 30% chance
                        self.tabuleiro.terreno[alvo.pos_y][alvo.pos_x] = TERRENO_GELO
                        logs_turno.append(f"  O chão sob {alvo.nome} congela!")

                elif habilidade == 'bola_de_fogo':
                    pos_final = acao['pos_conjuracao']
                    alvo_central = acao['alvo_central']

                    if (atacante.pos_x, atacante.pos_y) != pos_final:
                        self.tabuleiro.mover_personagem(atacante, pos_final[0], pos_final[1])
                        logs_turno.append(f"  {atacante.nome} se move para ({pos_final[0]},{pos_final[1]}) para a conjuração.")
                        atacante.eventos_animacao.append({'tipo': 'movimento', 'personagem': atacante, 'start_pos': (atacante.pos_x, atacante.pos_y), 'end_pos': pos_final})
                    
                    logs_turno.append(f"{atacante.nome} conjura BOLA DE FOGO em ({alvo_central.pos_x},{alvo_central.pos_y})!")
                    atacante.mana_atual -= atacante.custo_habilidades['bola_de_fogo']
                    alvos_afetados = self.tabuleiro.get_personagens_em_area(alvo_central.pos_x, alvo_central.pos_y, 1)
                    dano = sum(random.randint(1, 6) for _ in range(2))
                    logs_turno.append(f"  A bola de fogo causa {dano} de dano em área!")
                    atacante.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': atacante, 'x': alvo_central.pos_x, 'y': alvo_central.pos_y, 'raio': 1})
                    if atacante.sound_player: atacante.sound_player('attack')
                    for vitima in alvos_afetados:
                        vitima.receber_dano(dano, atacante, logs_turno.append)
                        atacante.eventos_animacao.append({'tipo': 'dano', 'alvo': vitima, 'dano': dano})
            elif acao['acao'] == 'passar':
                logs_turno.append(f"  {atacante.nome} passa o turno.")
        
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
        time_inimigo = self.time_b if personagem_movendo.time == TIME_A else self.time_a
        for inimigo in time_inimigo:
            if inimigo.esta_vivo and inimigo.alcance == 1 and calcular_distancia(personagem_movendo, inimigo) <= 1:
                # Check if the move is away from the enemy
                dist_antiga = calcular_distancia(personagem_movendo, inimigo)
                dist_nova = abs(novo_x - inimigo.pos_x) + abs(novo_y - inimigo.pos_y)
                if dist_nova > dist_antiga:
                    logs_turno.append(f"  {inimigo.nome} aproveita a oportunidade e ataca {personagem_movendo.nome} em movimento!")
                    inimigo.atacar(personagem_movendo, [personagem_movendo], [], self.tabuleiro, logger=logs_turno.append)
                    if not personagem_movendo.esta_vivo:
                        logs_turno.append(f"  {personagem_movendo.nome} foi derrotado pelo ataque de oportunidade!")
                        return False # Stop the move
        return True # Continue the move

    def _fugir(self, p, inimigos, logs_turno):
        if not inimigos: return # No one to flee from
        
        # Verifica se o personagem pode fugir devido a efeitos de status
        if not p.pode_fugir:
            logs_turno.append(f"  {p.nome} tenta fugir, mas um efeito de status o impede!")
            return

        inimigo_mais_proximo = min(inimigos, key=lambda i: calcular_distancia(p, i))
        logs_turno.append(f"  {p.nome} está com pouca vida e tenta fugir de {inimigo_mais_proximo.nome}!")
        start_pos = (p.pos_x, p.pos_y)
        
        melhor_pos_fuga = None
        maior_dist_do_inimigo = calcular_distancia(p, inimigo_mais_proximo) # Current distance
        
        # Iterar sobre todas as posições possíveis dentro do alcance de movimento do personagem
        for dx in range(-p.velocidade, p.velocidade + 1):
            for dy in range(-p.velocidade, p.velocidade + 1):
                if abs(dx) + abs(dy) > p.velocidade: continue # Manhathan distance within speed

                prox_x, prox_y = p.pos_x + dx, p.pos_y + dy

                # Verificar se a nova posição é válida
                if not (0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura): continue
                if self.tabuleiro.get_personagem_em(prox_x, prox_y) is not None: continue # Não pode mover para célula ocupada
                if self.tabuleiro.get_terrain_em(prox_x, prox_y) == TERRENO_PAREDE: continue # Não pode mover para parede

                dist_da_fuga = calcular_distancia(type('obj', (object,), {'pos_x': prox_x, 'pos_y': prox_y}), inimigo_mais_proximo)
                
                # Se encontrou uma posição mais distante do inimigo
                if dist_da_fuga > maior_dist_do_inimigo:
                    maior_dist_do_inimigo = dist_da_fuga
                    melhor_pos_fuga = (prox_x, prox_y)
                # Se a distância é igual, prioriza posições que custam menos movimento ou são mais centrais
                elif dist_da_fuga == maior_dist_do_inimigo and melhor_pos_fuga is None:
                     melhor_pos_fuga = (prox_x, prox_y)

        if melhor_pos_fuga:
            self.tabuleiro.mover_personagem(p, melhor_pos_fuga[0], melhor_pos_fuga[1])
            logs_turno.append(f"  {p.nome} fugiu para ({p.pos_x},{p.pos_y}).")
            p.eventos_animacao.append({'tipo': 'movimento', 'personagem': p, 'start_pos': start_pos, 'end_pos': (p.pos_x, p.pos_y)})
        else:
            logs_turno.append(f"  {p.nome} não conseguiu encontrar uma rota de fuga melhor.")

    def _mover_personagem(self, p, alvo, logs_turno):
        logs_turno.append(f"  {p.nome} se move em direção a {alvo.nome}.")
        start_pos = (p.pos_x, p.pos_y)
        pontos_movimento = p.velocidade
        while pontos_movimento > 0:
            if calcular_distancia(p, alvo) <= p.alcance:
                logs_turno.append(f"  {p.nome} já está ao alcance.")
                break
            melhor_passo, menor_dist = None, calcular_distancia(p, alvo)
            for dx, dy in sorted(random.sample([(0,-1), (0,1), (-1,0), (1,0), (-1,-1), (-1,1), (1,-1), (1,1)], 8)):
                prox_x, prox_y = p.pos_x + dx, p.pos_y + dy
                if not (0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura): continue
                if self.tabuleiro.get_personagem_em(prox_x, prox_y) is not None: continue
                terreno_passo = self.tabuleiro.get_terrain_em(prox_x, prox_y)
                if terreno_passo == TERRENO_PAREDE: continue
                dist = abs(prox_x - alvo.pos_x) + abs(prox_y - alvo.pos_y)
                if dist < menor_dist:
                    menor_dist, melhor_passo = dist, (prox_x, prox_y)
            if melhor_passo:
                if not self._verificar_ataques_de_oportunidade(p, melhor_passo[0], melhor_passo[1], logs_turno):
                    break
                
                custo = 2 if self.tabuleiro.get_terrain_em(melhor_passo[0], melhor_passo[1]) == TERRENO_DIFICIL else 1
                if pontos_movimento >= custo:
                    # Store direction of movement
                    dx = melhor_passo[0] - p.pos_x
                    dy = melhor_passo[1] - p.pos_y

                    self.tabuleiro.mover_personagem(p, melhor_passo[0], melhor_passo[1])
                    p.elevacao = self.tabuleiro.get_elevation_em(p.pos_x, p.pos_y)

                    pontos_movimento -= custo

                    # Check for ice terrain slip
                    if self.tabuleiro.get_terrain_em(p.pos_x, p.pos_y) == TERRENO_GELO:
                        if random.random() < 0.5: # 50% chance to slip
                            prox_x, prox_y = p.pos_x + dx, p.pos_y + dy
                            if 0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura and \
                               self.tabuleiro.get_personagem_em(prox_x, prox_y) is None and \
                               self.tabuleiro.get_terrain_em(prox_x, prox_y) != TERRENO_PAREDE:
                                
                                logs_turno.append(f"  {p.nome} escorrega no gelo!")
                                self.tabuleiro.mover_personagem(p, prox_x, prox_y)

                    if custo > 1: logs_turno.append(f"  (Terreno difícil custou {custo} de movimento)")
                else:
                    logs_turno.append(f"  {p.nome} não tem movimento suficiente para o próximo passo.")
                    break
            else:
                logs_turno.append(f"  {p.nome} está bloqueado e não pode se mover.")
                break
        if (p.pos_x, p.pos_y) != start_pos:
            logs_turno.append(f"  {p.nome} se moveu para ({p.pos_x},{p.pos_y}).")
            p.eventos_animacao.append({'tipo': 'movimento', 'personagem': p, 'start_pos': start_pos, 'end_pos': (p.pos_x, p.pos_y)})
        else:
            logs_turno.append(f"  {p.nome} não se moveu nesta rodada.")

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
                if summoner.time == TIME_A:
                    self.time_a.append(minion)
                else:
                    self.time_b.append(minion)

                # Add to initiative order
                minion.rolar_iniciativa()
                # Insert after the current combatant
                self.ordem_de_combate.insert(self.combatente_atual_idx + 1, minion)
                
                logs_turno.append(f"  {summoner.nome} convocou {nome_minion} em ({x},{y})!")
                summoner.eventos_animacao.append({'tipo': 'spawn', 'personagem': minion})
                return
        logs_turno.append(f"  {summoner.nome} tentou convocar, mas não havia espaço!")

    def _verificar_fim_de_combate(self, logs_turno):
        if not any(p.esta_vivo for p in self.time_a): self.vencedor = f"Time {TIME_B}"
        elif not any(p.esta_vivo for p in self.time_b): self.vencedor = f"Time {TIME_A}"
        if self.vencedor: logs_turno.append(f"O {self.vencedor} é o vencedor!")

    def get_personagem_ativo(self):
        return self.ordem_de_combate[self.combatente_atual_idx]

    def avancar_turno(self):
        """Avança o índice de combate para o próximo personagem."""
        self._verificar_fim_de_combate([]) # Apenas para setar o vencedor se necessário
        if self.vencedor: return

        self.combatente_atual_idx = (self.combatente_atual_idx + 1) % len(self.ordem_de_combate)
        if self.combatente_atual_idx == 0: 
            self.turno += 1
            for p in self.combatentes:
                p.tick_cooldowns()
                p.tick_recursos()

    def jogador_move_personagem(self, personagem, novo_x, novo_y):
        """Executa um comando de movimento do jogador."""
        # Check for attacks of opportunity before moving
        if not self._verificar_ataques_de_oportunidade(personagem, novo_x, novo_y, []):
            # The character was killed, no move happens, but animation events for the attack have been added.
            eventos = list(personagem.eventos_animacao)
            personagem.eventos_animacao.clear()
            return eventos

        start_pos = (personagem.pos_x, personagem.pos_y)
        self.tabuleiro.mover_personagem(personagem, novo_x, novo_y)
        personagem.eventos_animacao.append({'tipo': 'movimento', 'personagem': personagem, 'start_pos': start_pos, 'end_pos': (novo_x, novo_y)})
        
        eventos = list(personagem.eventos_animacao)
        personagem.eventos_animacao.clear()
        return eventos

    def jogador_ataca_personagem(self, atacante, alvo):
        """Executa um comando de ataque do jogador."""
        time_inimigo = self.time_b if atacante.time == TIME_A else self.time_a
        time_aliado = self.time_a if atacante.time == TIME_A else self.time_b
        
        # Usando uma lista para capturar logs do ataque do jogador
        logs_ataque = []
        atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_ataque.append)
        # No futuro, podemos passar esses logs para a tela principal se quisermos
        print(logs_ataque) # Por enquanto, apenas printamos no console
        
        eventos = list(atacante.eventos_animacao)
        atacante.eventos_animacao.clear()
        return eventos