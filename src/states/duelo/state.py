"""
duelo_state.py — Estado Principal do Duelo de Castas (Grimwood Style)
Suporta de 1 a 4 oponentes (Filhos do Imperador) controlados por IA.
"""
from __future__ import annotations
import random
import pygame

from ..state_base import GameState
from .data import (
    C_VERDE, C_PERIGO, C_OURO, C_ACENTO, C_TEXTO,
)
from src.cerco_isectum import DADOS_INIMIGOS


from .draw import DueloStateDrawMixin
from .input import DueloStateInputMixin


class DueloState(
    DueloStateDrawMixin,
    DueloStateInputMixin,
    GameState,
):
    def __init__(self, game):
        super().__init__(game)
        self._setup_fonts()
        self._setup_layout()

        self.num_adversarios = 1
        self.controle_filhos = "humano"
        self.log = []
        
        # Estado do jogo (será inicializado em configurar_duelo_adversarios)
        self.jogadores = []
        self.maos = {}
        self.hordas = {}
        self.pontos = {}
        self.descarte = []
        self.deck = []
        self.ninho = []
        
        self.jogador_atual_idx = 0
        self.acoes_restantes = 2
        self.fase = "JOGAR"
        
        # Feedback e Tooltips
        self.carta_selecionada_idx = -1
        self.carta_hover_idx = -1
        self.msg_feedback = ""
        self.msg_cor = C_VERDE
        self.feedback_timer = 0
        self.timer = 0

    def _setup_fonts(self):
        self.fT  = pygame.font.Font(None, 48)
        self.fG  = pygame.font.Font(None, 32)
        self.fM  = pygame.font.Font(None, 24)
        self.fMi = pygame.font.Font(None, 18)

    def _setup_layout(self):
        self.ninho_rects = []
        self.mao_jogador_rects = []
        self.horda_jogador_rects = []
        self.horda_bot_rects = [] # Será gerado dinamicamente para cada adversário no draw
        self.oponente_horda_rects = {} # nome → rect da área
        self.btn_encerrar = None

    def configurar_duelo_adversarios(self):
        """Inicializa os decks, mãos e filas de acordo com o número de adversários configurados."""
        # Jogadores na partida
        self.jogadores = ["VOCÊ"] + [f"Filho {i+1}" for i in range(self.num_adversarios)]
        
        # Inicializa recipientes
        self.maos = {nome: [] for nome in self.jogadores}
        self.hordas = {nome: [] for nome in self.jogadores}
        self.pontos = {nome: 0 for nome in self.jogadores}
        
        # Cria deck grande proporcional ao número de jogadores
        multiplicador = max(2, (self.num_adversarios + 1) // 2)
        self.deck = list(DADOS_INIMIGOS.keys()) * multiplicador
        random.shuffle(self.deck)
        
        # Mercado Ninho
        self.ninho = []
        for _ in range(3):
            if self.deck:
                self.ninho.append(self.deck.pop())
                
        # Distribui cartas iniciais (3 por jogador)
        for nome in self.jogadores:
            for _ in range(3):
                if self.deck:
                    self.maos[nome].append(self.deck.pop())
                    
        self.jogador_atual_idx = 0
        self.acoes_restantes = 2
        self.fase = "JOGAR"
        
        self._push("SISTEMA", f"⚔ Duelo Iniciado com {self.num_adversarios} Filho(s) do Imperador!")
        self._push("SISTEMA", "Acumule pontos em sua Horda e use cartas para roubar/anular!")

    def _push(self, autor, msg):
        self.log.append((autor, msg))
        if len(self.log) > 60:
            self.log.pop(0)

    def _feedback(self, msg, cor=C_VERDE):
        self.msg_feedback = msg
        self.msg_cor = cor
        self.feedback_timer = 120

    def get_jogador_ativo(self):
        if self.jogador_atual_idx < len(self.jogadores):
            return self.jogadores[self.jogador_atual_idx]
        return "VOCÊ"

    # ── MÉTODOS DE AÇÃO DO JOGADOR ATIVO (HUMANO) ──────────────────────────

    def comprar_do_deck(self):
        ativo = self.get_jogador_ativo()
        # Se for IA e o turno for do bot, impede
        if ativo != "VOCÊ" and getattr(self, "controle_filhos", "humano") == "ia":
            return
            
        if self.acoes_restantes <= 0:
            return
            
        if not self.deck:
            if self.descarte:
                self.deck = list(self.descarte)
                random.shuffle(self.deck)
                self.descarte.clear()
                self._push("SISTEMA", "🎴 O descarte foi rebaralhado ao Deck!")
            else:
                self._feedback("Sem cartas no Deck!", C_PERIGO)
                return

        carta = self.deck.pop()
        self.maos[ativo].append(carta)
        self.acoes_restantes -= 1
        self._push(ativo, "Comprou uma carta do Deck.")
        
        if self.acoes_restantes <= 0:
            self.passar_turno()

    def comprar_do_ninho(self, idx):
        ativo = self.get_jogador_ativo()
        # Se for IA e o turno for do bot, impede
        if ativo != "VOCÊ" and getattr(self, "controle_filhos", "humano") == "ia":
            return
            
        if self.acoes_restantes <= 0:
            return
            
        if idx >= len(self.ninho):
            return
            
        carta = self.ninho.pop(idx)
        self.maos[ativo].append(carta)
        
        if self.deck:
            self.ninho.insert(idx, self.deck.pop())
            
        self.acoes_restantes -= 1
        dados = DADOS_INIMIGOS.get(carta, {})
        self._push(ativo, f"Comprou {dados.get('nome', carta)} do Ninho.")
        
        if self.acoes_restantes <= 0:
            self.passar_turno()

    def convocar_carta(self, idx_mao):
        ativo = self.get_jogador_ativo()
        # Se for IA e o turno for do bot, impede
        if ativo != "VOCÊ" and getattr(self, "controle_filhos", "humano") == "ia":
            return
            
        if self.acoes_restantes <= 0:
            return
            
        mao_u = self.maos[ativo]
        if idx_mao >= len(mao_u):
            return
            
        carta = mao_u.pop(idx_mao)
        self.hordas[ativo].append(carta)
        self.acoes_restantes -= 1
        
        self._aplicar_efeito_carta(carta, atacante=ativo)
        
        self.carta_selecionada_idx = -1
        
        if self.acoes_restantes <= 0:
            self.passar_turno()

    def passar_turno(self):
        self.acoes_restantes = 0
        
        # Avança para o próximo jogador da ordem
        self.jogador_atual_idx = (self.jogador_atual_idx + 1) % len(self.jogadores)
        self.acoes_restantes = 2
        
        ativo = self.get_jogador_ativo()
        if ativo == "VOCÊ":
            self._feedback("Seu Turno!", C_VERDE)
            self._push("SISTEMA", "Seu Turno! 2 ações disponíveis.")
        else:
            self._feedback(f"Turno de {ativo}", C_PERIGO)
            self._push("SISTEMA", f"Turno de {ativo}.")

    # ── IA E PROCESSAMENTO DOS FILHOS DO IMPERADOR (BOTS) ─────────────────

    def processar_turno_bot(self):
        """Simula a ação do Bot atual."""
        ativo = self.get_jogador_ativo()
        if self.fase == "FIM" or ativo == "VOCÊ":
            return
            
        self.timer += 1
        if self.timer < 50: # Atraso para parecer orgânico
            return
        self.timer = 0
        
        if self.acoes_restantes > 0:
            mao_b = self.maos[ativo]
            # Se tiver cartas na mão, prioriza convocar
            if mao_b:
                carta = random.choice(mao_b)
                mao_b.remove(carta)
                self.hordas[ativo].append(carta)
                self._aplicar_efeito_carta(carta, atacante=ativo)
                self.acoes_restantes -= 1
            else:
                # Caso contrário, compra do Ninho ou do Deck
                if self.ninho:
                    idx = random.randint(0, len(self.ninho) - 1)
                    carta = self.ninho.pop(idx)
                    self.maos[ativo].append(carta)
                    if self.deck:
                        self.ninho.insert(idx, self.deck.pop())
                    dados = DADOS_INIMIGOS.get(carta, {})
                    self._push(ativo, f"Comprou {dados.get('nome', carta)} do Ninho.")
                elif self.deck:
                    self.maos[ativo].append(self.deck.pop())
                    self._push(ativo, "Comprou uma carta do Deck.")
                self.acoes_restantes -= 1
        else:
            self.passar_turno()

    # ── RESOLVEDOR DE HABILIDADES MULTI-JOGADOR (GRIMWOOD) ──────────────────

    def _obter_alvo_valido(self, atacante, criterio="pontos"):
        """Retorna o oponente que melhor se encaixa no critério para ser atacado."""
        oponentes = [p for p in self.jogadores if p != atacante]
        if not oponentes:
            return None
            
        if criterio == "pontos":
            # Retorna o oponente com maior pontuação
            return max(oponentes, key=lambda p: self.pontos.get(p, 0))
        elif criterio == "cartas":
            # Retorna o oponente com mais cartas na mão
            return max(oponentes, key=lambda p: len(self.maos.get(p, [])))
        return random.choice(oponentes)

    def _aplicar_efeito_carta(self, inseto_id, atacante):
        dados = DADOS_INIMIGOS.get(inseto_id, {})
        nome = dados.get("nome", inseto_id)
        emoji = dados.get("emoji", "🐛")
        
        self._push(atacante, f"Convocou {emoji} {nome}!")
        
        # Alvos automáticos baseados nos oponentes mais fortes
        alvo_c = self._obter_alvo_valido(atacante, criterio="pontos")
        alvo_m = self._obter_alvo_valido(atacante, criterio="cartas")
        
        if not alvo_c or not alvo_m:
            return

        horda_alvo = self.hordas[alvo_c]
        horda_propria = self.hordas[atacante]
        mao_alvo = self.maos[alvo_m]
        mao_propria = self.maos[atacante]

        # Proteção estática da Libélula-Blindada
        has_protection = any(c == "libelula_blindada" for c in horda_alvo)

        # ── 1. Vespa-Caçadora / Carrapato-Vampiro: Roubo de Mão ────────────
        if inseto_id in ("vespa_cacadora", "carrapato_vampiro"):
            if has_protection:
                self._push("SISTEMA", f"🛡 A Libélula de {alvo_c} bloqueou o roubo de {nome}!")
                return
                
            # Verifica Anulação na mão do oponente
            defesa_ids = ("abelha_tecela", "vespa_joia")
            defesa_cards = [c for c in mao_alvo if c in defesa_ids]
            if defesa_cards:
                c_def = defesa_cards[0]
                mao_alvo.remove(c_def)
                self.descarte.append(c_def)
                self._push("SISTEMA", f"⚡ Anulação! {alvo_m} descartou {c_def} para cancelar o roubo! {atacante} perdeu o turno!")
                self.acoes_restantes = 0
                return

            if mao_alvo:
                roubada = mao_alvo.pop(random.randint(0, len(mao_alvo) - 1))
                mao_propria.append(roubada)
                self._push(atacante, f"Roubou uma carta da mão de {alvo_m}!")
            else:
                self._push("SISTEMA", f"A mão de {alvo_m} está vazia.")

        # ── 2. Louva-Deus: Troca de Mão ─────────────────────────────────────
        elif inseto_id == "louva_deus":
            if has_protection:
                self._push("SISTEMA", f"🛡 {alvo_c} protegido pela Libélula.")
                return
            # Troca de mão com o oponente que tem mais cartas
            self.maos[atacante], self.maos[alvo_m] = self.maos[alvo_m], self.maos[atacante]
            self._push("SISTEMA", f"🔄 As mãos de {atacante} e {alvo_m} foram trocadas!")

        # ── 3. Besouro-Unicórnio / Mosca-Tsé-Tsé: Descarte Forçado ─────────
        elif inseto_id in ("besouro_unicornio", "mosca_tse_tse"):
            if has_protection:
                self._push("SISTEMA", f"🛡 Bloqueado.")
                return
            if mao_alvo:
                descartada = mao_alvo.pop(random.randint(0, len(mao_alvo) - 1))
                self.descarte.append(descartada)
                self._push(atacante, f"Forçou {alvo_m} a descartar 1 carta.")
            else:
                self._push("SISTEMA", f"A mão de {alvo_m} está vazia.")

        # ── 4. Mariposa-Esfinge: Compra Bônus ──────────────────────────────
        elif inseto_id == "mariposa_esfinge":
            for _ in range(2):
                if self.deck:
                    mao_propria.append(self.deck.pop())
            self._push(atacante, "Comprou 2 cartas bônus do Deck.")

        # ── 5. Escaravelho Necrófago: Recuperar Descarte ───────────────────
        elif inseto_id == "escaravelho_necrofago":
            if self.descarte:
                carta_recup = self.descarte.pop()
                mao_propria.append(carta_recup)
                self._push(atacante, f"Recuperou {carta_recup} da pilha de descarte.")
            else:
                self._push("SISTEMA", "Pilha de descarte vazia.")

        # ── 6. Aranha-Cleptoparasita: Rouba Inseto da Horda ────────────────
        elif inseto_id == "aranha_clepto":
            if has_protection:
                self._push("SISTEMA", f"🛡 A Horda de {alvo_c} está protegida.")
                return
            if horda_alvo:
                roubada = horda_alvo.pop(random.randint(0, len(horda_alvo) - 1))
                horda_propria.append(roubada)
                self._push(atacante, f"Roubou a carta {roubada} da Horda de {alvo_c}!")
            else:
                self._push("SISTEMA", f"A Horda de {alvo_c} está vazia.")

        else:
            self._push("SISTEMA", f"Casta {nome} ativou o Enxame.")

        self._calcular_pontos()

    # ── MÉTODOS DE CÁLCULO E FIM DE JOGO ───────────────────────────────────

    def _calcular_pontos(self):
        """Calcula a pontuação de todas as Hordas ativas na mesa."""
        for nome in self.jogadores:
            total = 0
            contagem = {}
            horda = self.hordas[nome]
            
            for c in horda:
                contagem[c] = contagem.get(c, 0) + 1
                total += 2  # Cada inseto base vale 2 pontos

            # Sets do mesmo inseto
            for c, qtd in contagem.items():
                if qtd >= 2:
                    total += 3
                if qtd >= 3:
                    total += 6

            # Combo Cadeia Alimentar: Predador + Presa
            has_predator = any(x in ("tarantula_golias", "viuva_negra", "viuva_canibal") for x in horda)
            has_prey     = any(x in ("cigarra_ressonante", "gafanhoto_praga") for x in horda)
            if has_predator and has_prey:
                total += 5

            # Combo Rainha Suprema + Súdito
            if "enxame_rainha" in horda and "abelha_tecela" in horda:
                total += 8

            self.pontos[nome] = total

        # Verifica se o jogo acabou (deck vazio e todas as mãos vazias)
        jogo_ativo = False
        for nome in self.jogadores:
            if self.maos[nome]:
                jogo_ativo = True
                break
                
        if not self.deck and not jogo_ativo:
            self.fase = "FIM"
            self._push("SISTEMA", "=== FIM DE DUELO ===")
            
            # Determina o vencedor
            vencedor = max(self.jogadores, key=lambda p: self.pontos.get(p, 0))
            max_pts = self.pontos[vencedor]
            
            if vencedor == "VOCÊ":
                self._push("VITORIA", f"Você venceu com {max_pts} pontos!")
            else:
                self._push("DERROTA", f"{vencedor} venceu a partida com {max_pts} pontos!")

    def update(self):
        self.timer += 1
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        ativo = self.get_jogador_ativo()
        if ativo != "VOCÊ" and self.fase != "FIM" and getattr(self, "controle_filhos", "humano") == "ia":
            self.processar_turno_bot()
        else:
            self.timer = 0
