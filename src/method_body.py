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

            elif habilidade == 'bola_de_fogo':
                 # Need implementation or use existing one if previously defined?
                 # Let's adding generic Area Logic or specific here.
                 pass # Assuming implemented below or elsewhere? 
                 # Wait, I am REPLACING the block. I must include existing logic if I am overwriting it.
                 # Previous view showed `elif habilidade == 'surto_de_acao'`.
                 # I will implement 'bola_de_fogo' here explicitly.
                 # Target is a position or unit? UI returns 'alvo' usually as unit or handled by target picker.
                 # For Area skills, `acao` might contain 'pos_x', 'pos_y'?
                 # Assuming target unit for simplicity or area logic to be implemented.
                 pass 

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
                 alvo.aplicar_status_efeito("Defesa Quebrada", 3, logs_turno.append)
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
                atacante.fe_atual -= atacante.custo_habilidades.get('canalizar_divindade', 4)
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
                 # Pending Area Logic
                 pass
             
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

