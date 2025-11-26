import random
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe
from src.config import TIME_A, TIME_B
from .utils import calcular_distancia

class MotorCombate:
    def __init__(self, args_times, gerar_terreno=False, sound_player=None, modo_chefe=False, stats_chefe=None):
        self.tabuleiro = Tabuleiro(20, 20)
        if gerar_terreno:
            self.tabuleiro.gerar_terreno_aleatorio()
        self.sound_player = sound_player
        self.time_a, self.time_b = self._setup_times(args_times, modo_chefe, stats_chefe)
        if not self.time_a or not self.time_b:
            raise ValueError("Ambos os times precisam de pelo menos um personagem.")
        self.combatentes = self.time_a + self.time_b
        for p in self.combatentes: p.rolar_iniciativa()
        self.ordem_de_combate = sorted(self.combatentes, key=lambda x: x.iniciativa, reverse=True)
        self.turno = 1
        self.combatente_atual_idx = 0
        self.vencedor = None

    def _setup_times(self, args, modo_chefe, stats_chefe):
        classes = [Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo]
        time_a = []
        personagens_para_criar_a = []
        for i, classe in enumerate(classes):
            personagens_para_criar_a.extend([classe] * args[i])
        for i, classe_personagem in enumerate(personagens_para_criar_a):
            nome = f"{classe_personagem.__name__}_A{i+1}"
            p = classe_personagem(nome, TIME_A, nivel=1, sound_player=self.sound_player)
            time_a.append(p)
            self.tabuleiro.adicionar_personagem_na_borda(p, 'sul')

        time_b = []
        if modo_chefe:
            chefe = Chefe("Dragão Ancião", TIME_B, sound_player=self.sound_player, stats=stats_chefe)
            time_b.append(chefe)
            self.tabuleiro.adicionar_personagem_na_borda(chefe, 'norte')
        else:
            personagens_para_criar_b = []
            for i, classe in enumerate(classes):
                personagens_para_criar_b.extend([classe] * args[i+6])
            for i, classe_personagem in enumerate(personagens_para_criar_b):
                nome = f"{classe_personagem.__name__}_B{i+1}"
                p = classe_personagem(nome, TIME_B, nivel=1, sound_player=self.sound_player)
                time_b.append(p)
                self.tabuleiro.adicionar_personagem_na_borda(p, 'norte')
        return time_a, time_b

    def proximo_passo(self):
        logs_turno = []
        eventos_turno = []
        if self.vencedor: return {'logs': [], 'eventos': []}

        if self.combatente_atual_idx == 0:
            logs_turno.append(f"--- RODADA {self.turno} ---")
            for p in self.combatentes: p.tick_cooldowns()

        atacante = self.ordem_de_combate[self.combatente_atual_idx]
        atacante.eventos_animacao.clear()

        if atacante.esta_vivo:
            atacante.tick_status_efeitos(logs_turno.append) # Processa efeitos de status no início do turno
            logs_turno.append(f"Vez de {atacante.nome}")
            time_inimigo = [p for p in (self.time_b if atacante.time == TIME_A else self.time_a) if p.esta_vivo]
            time_aliado = [p for p in (self.time_a if atacante.time == TIME_A else self.time_b) if p.esta_vivo]
            
            if not time_inimigo and not time_aliado: # If there are no enemies or allies, the character just passes
                logs_turno.append(f"{atacante.nome} não tem alvos ou aliados.")
                acao = {'acao': 'passar'}
            else:
                acao = atacante.decidir_acao(time_inimigo, time_aliado, self.tabuleiro, logs_turno)

            # Executa a ação decidida pelo personagem
            if acao['acao'] == 'atacar':
                alvo = acao['alvo']
                if calcular_distancia(atacante, alvo) > atacante.alcance: # Should not happen if AI is good, but a safeguard
                    logs_turno.append(f"  {atacante.nome} tenta atacar {alvo.nome} mas está fora de alcance!")
                    self._mover_personagem(atacante, alvo, logs_turno) # Try to move closer
                    if calcular_distancia(atacante, alvo) <= atacante.alcance: # If now in range, attack
                         atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
                else:
                    atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
            elif acao['acao'] == 'mover':
                alvo = acao['alvo']
                self._mover_personagem(atacante, alvo, logs_turno)
            elif acao['acao'] == 'fugir':
                alvos_vivos = [p for p in (self.time_b if atacante.time == TIME_A else self.time_a) if p.esta_vivo]
                self._fugir(atacante, alvos_vivos, logs_turno)
            elif acao['acao'] == 'usar_habilidade':
                habilidade = acao['habilidade']
                if habilidade == 'canalizar_divindade':
                    alvo_cura = acao['alvo']
                    atacante.cooldowns['canalizar_divindade'] = atacante.cooldown_max['canalizar_divindade']
                    cura = sum(random.randint(1, 6) for _ in range(2)) + atacante.mod_sab
                    alvo_cura.receber_cura(cura, logs_turno.append)
                    atacante.eventos_animacao.append({'tipo': 'cura', 'alvo': alvo_cura, 'cura': cura})
                elif habilidade == 'bola_de_fogo':
                    pos_final = acao['pos_conjuracao']
                    alvo_central = acao['alvo_central']

                    if (atacante.pos_x, atacante.pos_y) != pos_final:
                        self.tabuleiro.mover_personagem(atacante, pos_final[0], pos_final[1])
                        logs_turno.append(f"  {atacante.nome} se move para ({pos_final[0]},{pos_final[1]}) para a conjuração.")
                        atacante.eventos_animacao.append({'tipo': 'movimento', 'personagem': atacante, 'start_pos': (atacante.pos_x, atacante.pos_y), 'end_pos': pos_final})
                    
                    logs_turno.append(f"{atacante.nome} conjura BOLA DE FOGO em ({alvo_central.pos_x},{alvo_central.pos_y})!")
                    atacante.cooldowns['bola_de_fogo'] = atacante.cooldown_max['bola_de_fogo']
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
                custo = 2 if self.tabuleiro.get_terrain_em(melhor_passo[0], melhor_passo[1]) == TERRENO_DIFICIL else 1
                if pontos_movimento >= custo:
                    self.tabuleiro.mover_personagem(p, melhor_passo[0], melhor_passo[1])
                    pontos_movimento -= custo
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
            for p in self.combatentes: p.tick_cooldowns()

    def jogador_move_personagem(self, personagem, novo_x, novo_y):
        """Executa um comando de movimento do jogador."""
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