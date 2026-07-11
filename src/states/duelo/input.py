"""
duelo_input.py — Mixin de Input e Controle do Mouse para DueloState
"""
from __future__ import annotations
import pygame


class DueloStateInputMixin:
    """Responsável por gerenciar eventos e cliques do mouse na mesa de cartas."""

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.game.rodando = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._voltar_ao_setup()
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse = pygame.mouse.get_pos()
                self._processar_clique(mouse)

    def _voltar_ao_setup(self):
        """Retorna ao menu anterior (Setup de Castas ou Tabuleiro de Cerco)."""
        # Se veio de um duelo de invasão do Cerco:
        if getattr(self, "modo_retorno_cerco", False) and getattr(self.game, "castas_state_salvo", None):
            # Determina o vencedor
            vencedor = max(self.jogadores, key=lambda p: self.pontos.get(p, 0))
            salvo = self.game.castas_state_salvo
            
            if vencedor == "VOCÊ":
                # Sucesso: Invasor repelido
                salvo._push("SISTEMA", f"⚔️ Vitória no Duelo! Invasor em {self.zona_invasao_origem.upper()} foi repelido com sucesso!")
            else:
                # Fracasso: Invasão bem-sucedida
                from src.cerco_isectum import aplicar_delta
                
                # Aplica penalidade dependendo de onde invadiu
                if self.zona_invasao_origem == "camara_central":
                    dano_ouro = 4
                    salvo.estado = aplicar_delta(salvo.estado, {"tesouro": max(0, salvo.estado.get("tesouro", 10) - dano_ouro)})
                    salvo._push("DERROTA", f"💥 Derrota! Oponente saqueou a Câmara Central (-{dano_ouro} ouro!)")
                else:
                    dano_res = 3
                    salvo.estado = aplicar_delta(salvo.estado, {"reserva": max(0, salvo.estado.get("reserva", 10) - dano_res)})
                    salvo._push("DERROTA", f"💥 Derrota! Fortaleza danificada em {self.zona_invasao_origem.upper()} (-{dano_res} recursos!)")
            
            # Restaura o estado salvo do Cerco
            self.game.castas_state = salvo
            self.game.estado_jogo = "castas"
            self.game.duelo_state = None
            self.game.castas_state_salvo = None
            return

        # Comportamento padrão (Duelo clássico do menu)
        from src.states.castas_setup import CastasSetupState
        self.game.duelo_state = None
        self.game.castas_setup_state = CastasSetupState(self.game)
        self.game.estado_jogo = "castas_setup"

    def _processar_clique(self, mouse):
        # 1. Botão Voltar ao Setup
        if hasattr(self, 'btn_voltar') and self.btn_voltar.collidepoint(mouse):
            self._voltar_ao_setup()
            return

        ativo = self.get_jogador_ativo()
        if self.fase == "FIM":
            return
        # Se o turno for de um Bot IA, impede ações
        if ativo != "VOCÊ" and getattr(self, "controle_filhos", "humano") == "ia":
            return

        # 2. Clique no Deck de Compra
        if hasattr(self, 'deck_rect') and self.deck_rect.collidepoint(mouse):
            self.comprar_do_deck()
            return

        # 3. Clique no Ninho Central (comprar carta aberta)
        if hasattr(self, 'ninho_rects'):
            for idx, r in enumerate(self.ninho_rects):
                if r.collidepoint(mouse):
                    self.comprar_do_ninho(idx)
                    return

        # 4. Clique na Mão de Cartas (Jogador Ativo)
        if hasattr(self, 'mao_jogador_rects'):
            mao_u = self.maos.get(ativo, [])
            for idx, r in enumerate(self.mao_jogador_rects):
                if r.collidepoint(mouse):
                    # Se clicou numa carta já selecionada → convoca!
                    if self.carta_selecionada_idx == idx:
                        self.convocar_carta(idx)
                    else:
                        # Senão, apenas seleciona
                        self.carta_selecionada_idx = idx
                        from src.cerco_isectum import DADOS_INIMIGOS
                        cid = mao_u[idx]
                        dados = DADOS_INIMIGOS.get(cid, {})
                        self._feedback(f"Selecionado: {dados.get('nome', cid)}. Clique novamente para Convocar!", (200, 80, 255))
                    return

            # Clicar fora de uma carta limpa a seleção
            self.carta_selecionada_idx = -1
