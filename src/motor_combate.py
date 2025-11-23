import random
from .tabuleiro import Tabuleiro, TERRENO_PAREDE, TERRENO_DIFICIL
from .personagens import Guerreiro, Mago, Ladino, Arqueiro, Barbaro, Clerigo, Chefe

def calcular_distancia(p1, p2):
    return abs(p1.pos_x - p2.pos_x) + abs(p1.pos_y - p2.pos_y)

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
            p = classe_personagem(nome, "A", nivel=1, sound_player=self.sound_player)
            time_a.append(p)
            self.tabuleiro.adicionar_personagem_na_borda(p, 'sul')

        time_b = []
        if modo_chefe:
            chefe = Chefe("Dragão Ancião", "B", sound_player=self.sound_player, stats=stats_chefe)
            time_b.append(chefe)
            self.tabuleiro.adicionar_personagem_na_borda(chefe, 'norte')
        else:
            personagens_para_criar_b = []
            for i, classe in enumerate(classes):
                personagens_para_criar_b.extend([classe] * args[i+6])
            for i, classe_personagem in enumerate(personagens_para_criar_b):
                nome = f"{classe_personagem.__name__}_B{i+1}"
                p = classe_personagem(nome, "B", nivel=1, sound_player=self.sound_player)
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
            logs_turno.append(f"Vez de {atacante.nome}")
            time_inimigo = self.time_b if atacante.time == "A" else self.time_a
            time_aliado = self.time_a if atacante.time == "A" else self.time_b
            alvos_vivos = [p for p in time_inimigo if p.esta_vivo]
            
            if alvos_vivos:
                acao_realizada = False
                # 1. Lógica Específica de Classe
                if isinstance(atacante, Mago) and atacante.cooldowns['bola_de_fogo'] == 0:
                    acao_realizada = self._ia_mago_bola_de_fogo(atacante, time_inimigo, logs_turno)
                elif isinstance(atacante, Clerigo):
                    acao_realizada = self._ia_clerigo_cura(atacante, time_aliado, logs_turno)

                if acao_realizada:
                    self.finalizar_turno(logs_turno, eventos_turno)
                    return {'logs': logs_turno, 'eventos': eventos_turno}

                # 2. Instinto de Sobrevivência
                if atacante.hp_atual / atacante.hp_max < 0.25:
                    logs_turno.append(f"  {atacante.nome} está com pouca vida e tenta fugir!")
                    self._fugir(atacante, alvos_vivos, logs_turno)
                else:
                    # 3. Lógica de Ataque Padrão
                    alvo = max(alvos_vivos, key=lambda p: (p.threat_level, -p.hp_atual))
                    logs_turno.append(f"  ({atacante.nome} identifica {alvo.nome} como a maior ameaça.)")
                    if calcular_distancia(atacante, alvo) > atacante.alcance:
                        self._mover_personagem(atacante, alvo, logs_turno)
                    if calcular_distancia(atacante, alvo) <= atacante.alcance:
                        atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_turno.append)
            else:
                logs_turno.append(f"{atacante.nome} não tem alvos.")
        
        self.finalizar_turno(logs_turno, eventos_turno)
        return {'logs': logs_turno, 'eventos': eventos_turno}

    def _ia_clerigo_cura(self, clerigo, time_aliado, logs_turno):
        if clerigo.cooldowns['canalizar_divindade'] == 0:
            aliados_feridos = [p for p in time_aliado if p.esta_vivo and p.hp_atual < p.hp_max * 0.7 and calcular_distancia(clerigo, p) <= clerigo.alcance_cura]
            if aliados_feridos:
                alvo_cura = min(aliados_feridos, key=lambda p: p.hp_atual / p.hp_max)
                logs_turno.append(f"  {clerigo.nome} prioriza a cura e usa Canalizar Divindade em {alvo_cura.nome}!")
                clerigo.cooldowns['canalizar_divindade'] = clerigo.cooldown_max['canalizar_divindade']
                cura = sum(random.randint(1, 6) for _ in range(2)) + clerigo.mod_sab
                alvo_cura.receber_cura(cura, logs_turno.append)
                return True
        return False

    def _ia_mago_bola_de_fogo(self, mago, time_inimigo, logs_turno):
        melhor_oportunidade = {'alvos_atingidos': 0, 'pos_final': None, 'alvo_central': None}
        pos_inicial = (mago.pos_x, mago.pos_y)

        # Avalia todas as posições alcançáveis
        for r in range(mago.velocidade + 1):
            for dx in range(-r, r + 1):
                dy = r - abs(dx)
                for sign_x, sign_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                    if dx == 0 and dy == 0 and (sign_x != 1 or sign_y != 1): continue
                    nova_pos_x, nova_pos_y = pos_inicial[0] + dx*sign_x, pos_inicial[1] + dy*sign_y
                    
                    if not (0 <= nova_pos_x < self.tabuleiro.largura and 0 <= nova_pos_y < self.tabuleiro.altura): continue
                    if self.tabuleiro.get_personagem_em(nova_pos_x, nova_pos_y) is not None and (nova_pos_x, nova_pos_y) != pos_inicial: continue
                    if self.tabuleiro.get_terrain_em(nova_pos_x, nova_pos_y) == TERRENO_PAREDE: continue

                    mago_simulado_pos = type('obj', (object,), {'pos_x': nova_pos_x, 'pos_y': nova_pos_y})
                    for inimigo in time_inimigo:
                        if calcular_distancia(mago_simulado_pos, inimigo) <= mago.alcance:
                            alvos_na_area = self.tabuleiro.get_personagens_em_area(inimigo.pos_x, inimigo.pos_y, 1)
                            num_inimigos = sum(1 for p in alvos_na_area if p.time != mago.time)
                            if num_inimigos > melhor_oportunidade['alvos_atingidos']:
                                melhor_oportunidade = {'alvos_atingidos': num_inimigos, 'pos_final': (nova_pos_x, nova_pos_y), 'alvo_central': inimigo}
        
        if melhor_oportunidade['alvos_atingidos'] >= 2:
            logs_turno.append(f"  {mago.nome} vê uma oportunidade para a Bola de Fogo!")
            pos_final = melhor_oportunidade['pos_final']
            alvo_central = melhor_oportunidade['alvo_central']
            
            if (mago.pos_x, mago.pos_y) != pos_final:
                self.tabuleiro.mover_personagem(mago, pos_final[0], pos_final[1])
                logs_turno.append(f"  {mago.nome} se move para ({pos_final[0]},{pos_final[1]}) para a conjuração.")
                mago.eventos_animacao.append({'tipo': 'movimento', 'personagem': mago, 'start_pos': pos_inicial, 'end_pos': pos_final})

            logs_turno.append(f"{mago.nome} conjura BOLA DE FOGO em ({alvo_central.pos_x},{alvo_central.pos_y})!")
            mago.cooldowns['bola_de_fogo'] = mago.cooldown_max['bola_de_fogo']
            alvos_afetados = self.tabuleiro.get_personagens_em_area(alvo_central.pos_x, alvo_central.pos_y, 1)
            dano = sum(random.randint(1, 6) for _ in range(2))
            logs_turno.append(f"  A bola de fogo causa {dano} de dano em área!")
            mago.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': mago, 'x': alvo_central.pos_x, 'y': alvo_central.pos_y, 'raio': 1})
            if mago.sound_player: mago.sound_player('attack')
            for vitima in alvos_afetados:
                vitima.receber_dano(dano, mago, logs_turno.append)
                mago.eventos_animacao.append({'tipo': 'dano', 'alvo': vitima, 'dano': dano})
            return True
        return False

    def finalizar_turno(self, logs_turno, eventos_turno):
        for p in self.combatentes:
            eventos_turno.extend(p.eventos_animacao)
            p.eventos_animacao.clear()
        self._verificar_fim_de_combate(logs_turno)
        self.combatente_atual_idx = (self.combatente_atual_idx + 1) % len(self.ordem_de_combate)
        if self.combatente_atual_idx == 0: self.turno += 1

    def _fugir(self, p, inimigos, logs_turno):
        inimigo_mais_proximo = min(inimigos, key=lambda i: calcular_distancia(p, i))
        logs_turno.append(f"  O inimigo mais próximo é {inimigo_mais_proximo.nome}.")
        start_pos = (p.pos_x, p.pos_y)
        pontos_movimento = p.velocidade
        while pontos_movimento > 0:
            melhor_passo, maior_dist = None, calcular_distancia(p, inimigo_mais_proximo)
            for dx, dy in sorted(random.sample([(0,-1), (0,1), (-1,0), (1,0), (-1,-1), (-1,1), (1,-1), (1,1)], 8)):
                prox_x, prox_y = p.pos_x + dx, p.pos_y + dy
                if not (0 <= prox_x < self.tabuleiro.largura and 0 <= prox_y < self.tabuleiro.altura): continue
                if self.tabuleiro.get_personagem_em(prox_x, prox_y) is not None: continue
                if self.tabuleiro.get_terrain_em(prox_x, prox_y) == TERRENO_PAREDE: continue
                dist = abs(prox_x - inimigo_mais_proximo.pos_x) + abs(prox_y - inimigo_mais_proximo.pos_y)
                if dist > maior_dist:
                    maior_dist, melhor_passo = dist, (prox_x, prox_y)
            if melhor_passo:
                custo = 2 if self.tabuleiro.get_terrain_em(melhor_passo[0], melhor_passo[1]) == TERRENO_DIFICIL else 1
                if pontos_movimento >= custo:
                    self.tabuleiro.mover_personagem(p, melhor_passo[0], melhor_passo[1])
                    pontos_movimento -= custo
                else: break 
            else: break 
        if (p.pos_x, p.pos_y) != start_pos:
            logs_turno.append(f"  {p.nome} fugiu para ({p.pos_x},{p.pos_y}).")
            p.eventos_animacao.append({'tipo': 'movimento', 'personagem': p, 'start_pos': start_pos, 'end_pos': (p.pos_x, p.pos_y)})
        else:
            logs_turno.append(f"  {p.nome} não conseguiu encontrar uma rota de fuga.")

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
        if not any(p.esta_vivo for p in self.time_a): self.vencedor = "Time B"
        elif not any(p.esta_vivo for p in self.time_b): self.vencedor = "Time A"
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
        time_inimigo = self.time_b if atacante.time == "A" else self.time_a
        time_aliado = self.time_a if atacante.time == "A" else self.time_b
        
        # Usando uma lista para capturar logs do ataque do jogador
        logs_ataque = []
        atacante.atacar(alvo, time_inimigo, time_aliado, self.tabuleiro, logger=logs_ataque.append)
        # No futuro, podemos passar esses logs para a tela principal se quisermos
        print(logs_ataque) # Por enquanto, apenas printamos no console
        
        eventos = list(atacante.eventos_animacao)
        atacante.eventos_animacao.clear()
        return eventos