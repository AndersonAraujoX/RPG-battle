"""
src/server/session.py — Sessão de Jogo Co-op Autoritativa (RPG-battle)

Encapsula o motor de jogo, tabuleiro, controle de heróis por jogador,
validação estrita de autoridade, rodadas simultâneas com sinergia e IA inimiga.
"""
from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from src.tabuleiro import Tabuleiro
from src.config import (
    TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL,
    TERRENO_PAREDE, TERRENO_ROCHA, TERRENO_BARRIL,
    TIME_A, TIME_B,
)
from src.personagens import Stark, Elden, Doom, Gruu, Kuro, Darwin, Aquele
from src.personagens.personagem_base import Personagem
from src.cerco_isectum import CARTAS_BASICAS


class InvasorIsectum(Personagem):
    """Classe base para as forças invasoras do enxame Isectum."""
    def __init__(self, nome: str, time: str = TIME_B, nivel: int = 3, casta: str = "Invasor", emoji: str = "🐛", ac: int = 12, hp: int = 24):
        super().__init__(nome, time, nivel)
        self.classe_nome = casta
        self.emoji = emoji
        self.ac_base = ac
        self.hp_max = hp
        self.hp_atual = hp


class TrabalhadorIsectum(InvasorIsectum):
    def __init__(self, nome: str, time: str = TIME_B, nivel: int = 2):
        super().__init__(nome, time, nivel, casta="Trabalhador", emoji="🐜", ac=11, hp=18)


class GuerreiroIsectum(InvasorIsectum):
    def __init__(self, nome: str, time: str = TIME_B, nivel: int = 3):
        super().__init__(nome, time, nivel, casta="Guerreiro Isectum", emoji="🐝", ac=14, hp=30)


class ExploradorIsectum(InvasorIsectum):
    def __init__(self, nome: str, time: str = TIME_B, nivel: int = 3):
        super().__init__(nome, time, nivel, casta="Explorador", emoji="🦗", ac=13, hp=22)

# Mapa de classes disponíveis para o Co-op
CLASSES_HEROIS = {
    "Aquele": Aquele,
    "Stark": Stark,
    "Elden": Elden,
    "Doom": Doom,
    "Gruu": Gruu,
    "Kuro": Kuro,
    "Darwin": Darwin,
}

POSICOES_INICIAIS = [
    (9, 10),
    (10, 10),
    (9, 11),
    (10, 11),
]


class CoopSession:
    """
    Controla o estado de uma partida Co-op autoritativa no servidor.
    """

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.tabuleiro = Tabuleiro(largura=20, altura=20)
        self.jogadores: Dict[str, Dict[str, Any]] = {}
        self.inimigos: List[Any] = []
        self.fase: str = "LOBBY"  # LOBBY, SELECAO_CARTAS, ACAO_LIVRE, VITORIA, DERROTA
        self.round_atual: int = 0
        self.cartas_selecionadas: Dict[str, Optional[Dict[str, Any]]] = {}
        self.sinergia_ativa: Optional[Dict[str, Any]] = None
        self.combat_log: List[Dict[str, Any]] = []
        self.recursos: Dict[str, int] = {"madeira": 0, "couro": 0, "metal": 0, "cristal": 0}
        self._next_enemy_id: int = 1

    # ── Log de Combate ────────────────────────────────────────────────────────

    def add_log(self, autor: str, texto: str, cor: str = "#cbd5e1"):
        self.combat_log.append({
            "autor": autor,
            "texto": texto,
            "cor": cor,
        })
        if len(self.combat_log) > 50:
            self.combat_log.pop(0)

    # ── Gerenciamento de Jogadores & Heróis ───────────────────────────────────

    def add_player(self, player_id: str, player_name: str) -> bool:
        """Adiciona um jogador ao lobby da sala (máx 4 jogadores)."""
        if len(self.jogadores) >= 4 and player_id not in self.jogadores:
            return False
        if player_id not in self.jogadores:
            self.jogadores[player_id] = {
                "id": player_id,
                "nome": player_name,
                "hero_name": None,
                "hero": None,
                "mao": [],
                "deck": [],
                "descarte": [],
                "pontos_movimento": 0,
                "pontos_trabalho": 0,
                "pontos_escavacao": 0,
                "ready": False,
                "connected": True,
            }
            self.add_log("SALA", f"⚔️ {player_name} entrou na sala.", "#38bdf8")
        else:
            self.jogadores[player_id]["connected"] = True
        return True

    def remove_player(self, player_id: str):
        """Remove o jogador ou marca como desconectado."""
        if player_id in self.jogadores:
            p = self.jogadores[player_id]
            p["connected"] = False
            self.add_log("SALA", f"⚠️ {p['nome']} desconectou-se.", "#f87171")
            if self.fase == "LOBBY":
                del self.jogadores[player_id]

    def select_hero(self, player_id: str, hero_name: str) -> Tuple[bool, str]:
        """Permite que um jogador escolha um herói ainda não selecionado."""
        if player_id not in self.jogadores:
            return False, "Jogador não encontrado."
        if self.fase != "LOBBY":
            return False, "O jogo já começou. Não é possível trocar de herói."
        if hero_name not in CLASSES_HEROIS:
            return False, f"Classe de herói '{hero_name}' inválida."

        # Verifica se outro jogador já escolheu este herói
        for pid, pdata in self.jogadores.items():
            if pid != player_id and pdata.get("hero_name") == hero_name:
                return False, f"O herói {hero_name} já foi escolhido por {pdata['nome']}."

        self.jogadores[player_id]["hero_name"] = hero_name
        self.jogadores[player_id]["ready"] = True
        self.add_log("LOBBY", f"🛡️ {self.jogadores[player_id]['nome']} escolheu {hero_name}.", "#fbbf24")
        return True, f"Herói {hero_name} selecionado com sucesso."

    # ── Inicialização da Partida ─────────────────────────────────────────────

    def start_game(self) -> Tuple[bool, str]:
        """Inicia o combate se todos os jogadores tiverem escolhido heróis."""
        if len(self.jogadores) == 0:
            return False, "A sala está vazia."
        if any(p.get("hero_name") is None for p in self.jogadores.values()):
            return False, "Nem todos os jogadores escolheram seus heróis."

        self.fase = "SELECAO_CARTAS"
        self.round_atual = 1

        # Instancia heróis no tabuleiro
        idx = 0
        for pid, pdata in self.jogadores.items():
            h_name = pdata["hero_name"]
            cls_heroi = CLASSES_HEROIS[h_name]
            hero = cls_heroi(nome=h_name, time=TIME_A, nivel=5)
            px, py = POSICOES_INICIAIS[idx % len(POSICOES_INICIAIS)]
            hero.pos_x = px
            hero.pos_y = py
            self.tabuleiro.grid[py][px] = hero
            pdata["hero"] = hero

            # Prepara baralho inicial e mão de 4 cartas
            deck = copy.deepcopy(CARTAS_BASICAS)
            random.shuffle(deck)
            pdata["deck"] = deck
            pdata["mao"] = [pdata["deck"].pop(0) for _ in range(min(4, len(pdata["deck"])))]
            pdata["descarte"] = []
            idx += 1

        # Spawna onda inicial de Invasores Isectum nas bordas
        self._spawn_wave_inicial()
        self.add_log("CERCO", "🚨 O cerco Isectum começou! Escolham suas cartas para o Round 1.", "#e11d48")
        self._iniciar_round_selecao()
        return True, "Partida iniciada com sucesso."

    def _spawn_wave_inicial(self):
        """Spawna inimigos Isectum nos arredores do tabuleiro."""
        spawn_locs = [(2, 2), (17, 2), (2, 17), (17, 17), (10, 2), (10, 18)]
        classes_inimigos = [TrabalhadorIsectum, GuerreiroIsectum, ExploradorIsectum]

        for i, (sx, sy) in enumerate(spawn_locs):
            if self.tabuleiro.grid[sy][sx] is None:
                cls_ini = classes_inimigos[i % len(classes_inimigos)]
                nome_ini = f"{cls_ini.__name__}_{self._next_enemy_id}"
                self._next_enemy_id += 1
                ini = cls_ini(nome=nome_ini, time=TIME_B, nivel=3)
                ini.pos_x = sx
                ini.pos_y = sy
                self.tabuleiro.grid[sy][sx] = ini
                self.inimigos.append(ini)

    # ── Sistema de Round Simultâneo & Sinergia ───────────────────────────────

    def _iniciar_round_selecao(self):
        """Prepara o estado para a seleção de cartas do round."""
        self.fase = "SELECAO_CARTAS"
        self.cartas_selecionadas = {pid: None for pid, p in self.jogadores.items() if p["hero"] and p["hero"].hp_atual > 0}
        self.sinergia_ativa = None

    def select_card(self, player_id: str, card_idx: int) -> Tuple[bool, str]:
        """Registra a carta selecionada pelo jogador no round de sincronia."""
        if self.fase != "SELECAO_CARTAS":
            return False, "Não estamos na fase de seleção de cartas."
        if player_id not in self.jogadores:
            return False, "Jogador não participa desta partida."

        p = self.jogadores[player_id]
        if not p.get("hero") or p["hero"].hp_atual <= 0:
            return False, "Seu herói está derrotado e não pode agir."
        if card_idx < 0 or card_idx >= len(p["mao"]):
            return False, "Índice de carta inválido."

        carta = p["mao"][card_idx]
        self.cartas_selecionadas[player_id] = {"idx": card_idx, "carta": carta}
        self.add_log("CARTAS", f"🃏 {p['nome']} ({p['hero_name']}) travou uma carta secreta.", "#38bdf8")

        # Se todos os heróis vivos escolheram, resolve automaticamente
        jogadores_vivos = [pid for pid, pdata in self.jogadores.items() if pdata["hero"] and pdata["hero"].hp_atual > 0]
        todos_escolheram = all(self.cartas_selecionadas.get(pid) is not None for pid in jogadores_vivos)
        if todos_escolheram:
            self.resolve_round()

        return True, "Carta confirmada para este round."

    def resolve_round(self) -> Dict[str, Any]:
        """
        Calcula as sinergias, descarta as cartas jogadas,
        atribui os pontos de ação e avança os inimigos 1 passo.
        """
        self.fase = "ACAO_LIVRE"
        cartas_por_jogador: Dict[str, Dict[str, Any]] = {}
        for pid, sel in self.cartas_selecionadas.items():
            if sel:
                cartas_por_jogador[pid] = sel["carta"]

        # Calcula sinergia de equipe
        sinergia = self._calcular_sinergia(cartas_por_jogador)
        self.sinergia_ativa = sinergia

        # Remove cartas da mão e aloca pontos de ação
        for pid, sel in self.cartas_selecionadas.items():
            if not sel:
                continue
            p = self.jogadores[pid]
            idx = sel["idx"]
            carta = sel["carta"]
            if idx < len(p["mao"]):
                c = p["mao"].pop(idx)
                p["descarte"].append(c)

            # Atribui pontos da carta
            mov = carta.get("movimento", 0) // 5 if carta.get("movimento", 0) >= 5 else carta.get("movimento", 2)
            trab = carta.get("trabalho", 0)
            esc = carta.get("escavacao", 0)

            p["pontos_movimento"] = p.get("pontos_movimento", 0) + max(1, mov)
            p["pontos_trabalho"] = p.get("pontos_trabalho", 0) + trab
            p["pontos_escavacao"] = p.get("pontos_escavacao", 0) + esc

        # Aplica bônus de sinergia
        if sinergia:
            self._aplicar_bonus_sinergia(sinergia)

        # Avanço dos inimigos (pressão tática)
        self._avancar_inimigos()

        self.add_log("ROUND", f"⚡ Round {self.round_atual} resolvido! Ações livres liberadas para a equipe.", "#10b981")
        return {"sinergia": self.sinergia_ativa, "round": self.round_atual}

    def _calcular_sinergia(self, cartas_por_jogador: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Identifica se 2+ jogadores jogaram cartas com o mesmo tipo de foco."""
        if len(cartas_por_jogador) < 2:
            return None

        tipos = []
        for c in cartas_por_jogador.values():
            if c.get("tipo") == "upgrade":
                tipos.append("upgrade")
            elif c.get("escavacao", 0) > 0:
                tipos.append("escavacao")
            elif c.get("trabalho", 0) > 0:
                tipos.append("trabalho")
            else:
                tipos.append("movimento")

        contagem = {}
        for t in tipos:
            contagem[t] = contagem.get(t, 0) + 1

        # Sinergia Suprema: todos jogaram o mesmo tipo
        if len(set(tipos)) == 1 and len(tipos) >= 2:
            return {
                "tipo": "supremo",
                "categoria": tipos[0],
                "mensagem": f"🌟 SINCRONIA PERFEITA: Todos jogaram {tipos[0].upper()}! +2 Cristais Bônus!",
            }

        # Sinergia padrão: 2+ cartas com o mesmo tipo
        for tipo_nome, count in contagem.items():
            if count >= 2:
                msg = f"⚡ SINCRONIA DE EQUIPE: {count}x {tipo_nome.upper()} combinados!"
                return {"tipo": "equipe", "categoria": tipo_nome, "mensagem": msg}

        return None

    def _aplicar_bonus_sinergia(self, sinergia: Dict[str, Any]):
        """Concede os efeitos dos bônus calculados para a equipe."""
        cat = sinergia.get("categoria")
        self.add_log("SINERGIA", sinergia["mensagem"], "#fbbf24")

        if sinergia.get("tipo") == "supremo":
            self.recursos["cristal"] += 2

        for p in self.jogadores.values():
            if cat == "movimento":
                p["pontos_movimento"] += 2
            elif cat == "trabalho":
                p["pontos_trabalho"] += 2
                self.recursos["madeira"] += 1
            elif cat == "escavacao":
                p["pontos_escavacao"] += 3

    def _avancar_inimigos(self):
        """Inimigos vivos dão 1 passo em direção ao herói mais próximo ou atacam."""
        for ini in list(self.inimigos):
            if ini.hp_atual <= 0:
                continue

            # Encontra herói vivo mais próximo
            alvo = None
            menor_dist = 999
            for p in self.jogadores.values():
                h = p.get("hero")
                if h and h.hp_atual > 0:
                    d = abs(h.pos_x - ini.pos_x) + abs(h.pos_y - ini.pos_y)
                    if d < menor_dist:
                        menor_dist = d
                        alvo = h

            if not alvo:
                continue

            # Se estiver adjacente (dist == 1), ataca o herói
            if menor_dist == 1:
                dano = random.randint(3, 7)
                alvo.hp_atual = max(0, alvo.hp_atual - dano)
                self.add_log("COMBATE", f"💥 {ini.nome} atacou {alvo.nome} causando {dano} de dano! ({alvo.hp_atual}/{alvo.hp_max})", "#f87171")
                if alvo.hp_atual <= 0:
                    self.add_log("ALERTA", f"💀 {alvo.nome} caiu em combate!", "#ef4444")
            else:
                # Dá 1 passo no caminho até o herói
                caminho = self.tabuleiro.encontrar_caminho(ini.pos_x, ini.pos_y, alvo.pos_x, alvo.pos_y, max_passos=1)
                if caminho:
                    nx, ny = caminho[0]
                    if self.tabuleiro.grid[ny][nx] is None:
                        self.tabuleiro.grid[ini.pos_y][ini.pos_x] = None
                        ini.pos_x = nx
                        ini.pos_y = ny
                        self.tabuleiro.grid[ny][nx] = ini

    # ── Ações Autoritativas do Jogador ───────────────────────────────────────

    def move_hero(self, player_id: str, dest_x: int, dest_y: int) -> Tuple[bool, str]:
        """
        Move o herói para o destino se o jogador tiver autoridade e pontos de movimento.
        """
        if self.fase != "ACAO_LIVRE":
            return False, "Movimento liberado apenas na fase de Ação Livre."
        if player_id not in self.jogadores:
            return False, "Jogador não autorizado."

        p = self.jogadores[player_id]
        h = p.get("hero")
        if not h or h.hp_atual <= 0:
            return False, "Seu herói está abatido e não pode se mover."

        # Validação de limites
        if not (0 <= dest_x < self.tabuleiro.largura and 0 <= dest_y < self.tabuleiro.altura):
            return False, "Coordenadas fora do tabuleiro."

        # Validação de terreno intransponível
        if self.tabuleiro.terrain_grid[dest_y][dest_x] == TERRENO_PAREDE:
            return False, "Destino bloqueado por parede intransponível."

        # Validação de ocupação
        if self.tabuleiro.grid[dest_y][dest_x] is not None:
            return False, "A célula de destino já está ocupada."

        # Validação de passos e pontos de movimento
        caminho = self.tabuleiro.encontrar_caminho(h.pos_x, h.pos_y, dest_x, dest_y)
        passos_necessarios = len(caminho)
        if passos_necessarios == 0:
            return False, "Não há caminho desimpedido até o destino."
        if p["pontos_movimento"] < passos_necessarios:
            return False, f"Pontos de movimento insuficientes ({p['pontos_movimento']} disponíveis, {passos_necessarios} necessários)."

        # Aplica movimento
        self.tabuleiro.grid[h.pos_y][h.pos_x] = None
        h.pos_x = dest_x
        h.pos_y = dest_y
        self.tabuleiro.grid[dest_y][dest_x] = h
        p["pontos_movimento"] -= passos_necessarios

        self.add_log("MOVIMENTO", f"🏃 {h.nome} moveu-se para ({dest_x}, {dest_y}).", "#60a5fa")
        return True, "Movimento concluído com sucesso."

    def attack_target(self, player_id: str, target_x: int, target_y: int) -> Tuple[bool, str]:
        """
        Executa um ataque contra um Invasor no alcance.
        """
        if self.fase != "ACAO_LIVRE":
            return False, "Ataques liberados apenas na fase de Ação Livre."
        if player_id not in self.jogadores:
            return False, "Jogador não autorizado."

        p = self.jogadores[player_id]
        h = p.get("hero")
        if not h or h.hp_atual <= 0:
            return False, "Herói abatido não pode atacar."

        # Verifica se há um inimigo nas coordenadas
        alvo = None
        for ini in self.inimigos:
            if ini.pos_x == target_x and ini.pos_y == target_y and ini.hp_atual > 0:
                alvo = ini
                break

        if not alvo:
            return False, "Não há nenhum invasor vivo no alvo indicado."

        # Distância máxima (Mago = 8, outros = 1 ou 2)
        alcance_max = 8 if getattr(h, "classe_nome", "") == "Elden" else 2
        dist = abs(h.pos_x - target_x) + abs(h.pos_y - target_y)
        if dist > alcance_max:
            return False, f"Alvo fora de alcance (distância {dist} > alcance {alcance_max})."

        # Rolagem de Dano
        d20 = random.randint(1, 20)
        ac_alvo = getattr(alvo, "ac_base", 12) + self.tabuleiro.obter_bonificacao_cobertura(target_x, target_y)
        acerto = (d20 + 4) >= ac_alvo or d20 == 20

        if acerto:
            dano = random.randint(6, 14)
            alvo.hp_atual = max(0, alvo.hp_atual - dano)
            msg = f"⚔️ {h.nome} acertou {alvo.nome} com {dano} de dano! ({alvo.hp_atual}/{alvo.hp_max})"
            self.add_log("ATAQUE", msg, "#fbbf24")

            # Verifica morte do inimigo
            if alvo.hp_atual <= 0:
                self.tabuleiro.grid[target_y][target_x] = None
                self.add_log("VITÓRIA", f"💥 {alvo.nome} foi exterminado por {h.nome}!", "#34d399")
                self.recursos["cristal"] += 1
                # Checa se todos os inimigos foram eliminados
                if all(ini.hp_atual <= 0 for ini in self.inimigos):
                    self.fase = "VITORIA"
                    self.add_log("CONQUISTA", "🏆 TODOS OS INVASORES FORAM DERROTADOS! A EQUIPE VENCEU!", "#10b981")
            return True, msg
        else:
            msg = f"🛡️ {h.nome} atacou {alvo.nome}, mas o golpe errou (d20={d20} vs AC={ac_alvo})."
            self.add_log("ATAQUE", msg, "#94a3b8")
            return True, msg

    def mine_action(self, player_id: str, target_x: int, target_y: int) -> Tuple[bool, str]:
        """Escava rochas ou coleta madeira/recursos adjacentes."""
        if self.fase != "ACAO_LIVRE":
            return False, "Ação liberada apenas na fase de Ação Livre."
        if player_id not in self.jogadores:
            return False, "Jogador não autorizado."

        p = self.jogadores[player_id]
        h = p.get("hero")
        if not h or h.hp_atual <= 0:
            return False, "Herói abatido não pode trabalhar."

        dist = abs(h.pos_x - target_x) + abs(h.pos_y - target_y)
        if dist > 1:
            return False, "Você precisa estar adjacente ao recurso para interagir."

        if p["pontos_escavacao"] <= 0 and p["pontos_trabalho"] <= 0:
            return False, "Sem pontos de trabalho ou escavação disponíveis."

        t = self.tabuleiro.terrain_grid[target_y][target_x]
        if t in (TERRENO_ROCHA, TERRENO_FLORESTA, TERRENO_BARRIL):
            self.tabuleiro.terrain_grid[target_y][target_x] = TERRENO_NORMAL
            if p["pontos_escavacao"] > 0:
                p["pontos_escavacao"] -= 1
            else:
                p["pontos_trabalho"] -= 1

            self.recursos["madeira"] += 1
            self.recursos["metal"] += 1
            msg = f"⛏️ {h.nome} limpou o terreno ({target_x}, {target_y}) e coletou materiais!"
            self.add_log("RECURSO", msg, "#34d399")
            return True, msg

        return False, "Não há obstáculo ou recurso escavável nesta posição."

    def end_player_turn(self, player_id: str) -> Tuple[bool, str]:
        """Avança o round quando os heróis concluem suas ações livres."""
        if self.fase != "ACAO_LIVRE":
            return False, "Não estamos na fase de Ação Livre."
        if player_id not in self.jogadores:
            return False, "Jogador não autorizado."

        # Compra cartas até o limite de mão e zera pontos
        for p in self.jogadores.values():
            p["pontos_movimento"] = 0
            p["pontos_trabalho"] = 0
            p["pontos_escavacao"] = 0
            # Compra cartas
            while len(p["mao"]) < 4 and len(p["deck"]) > 0:
                p["mao"].append(p["deck"].pop(0))
            if len(p["deck"]) == 0 and len(p["descarte"]) > 0:
                p["deck"] = list(p["descarte"])
                p["descarte"] = []
                random.shuffle(p["deck"])

        self.round_atual += 1
        self._iniciar_round_selecao()
        self.add_log("ROUND", f"🔄 Iniciando Round {self.round_atual} — Escolham suas cartas!", "#38bdf8")
        return True, "Próximo round iniciado."

    # ── Serialização de Estado para o Frontend ───────────────────────────────

    def to_dict(self, for_player_id: Optional[str] = None) -> Dict[str, Any]:
        """Serializa o estado do jogo para JSON enviado via WebSocket."""
        SPRITES_HEROIS = {
            "Aquele": "/assets/images/characters/heroes/Aquele.png",
            "Stark": "/assets/images/characters/heroes/paladino.png",
            "Elden": "/assets/images/characters/heroes/mago.png",
            "Doom": "/assets/images/characters/heroes/ladino.png",
            "Gruu": "/assets/images/characters/heroes/barbaro.png",
            "Kuro": "/assets/images/characters/heroes/ladino.png",
            "Darwin": "/assets/images/characters/heroes/druida.png",
        }

        SPRITES_INIMIGOS = {
            "TrabalhadorIsectum": "/assets/images/characters/monsters/isectum/besouro_gorgulho.png",
            "GuerreiroIsectum": "/assets/images/characters/monsters/isectum/vespa_cacadora.png",
            "ExploradorIsectum": "/assets/images/characters/monsters/isectum/louva_deus.png",
        }

        heroes_data = []
        for pid, p in self.jogadores.items():
            h = p.get("hero")
            is_me = (pid == for_player_id)
            h_name = p.get("hero_name")
            heroes_data.append({
                "player_id": pid,
                "player_name": p["nome"],
                "hero_name": h_name,
                "sprite_url": SPRITES_HEROIS.get(h_name, "/assets/images/characters/heroes/Aquele.png") if h_name else None,
                "hp_atual": h.hp_atual if h else 50,
                "hp_max": h.hp_max if h else 50,
                "ac": getattr(h, "ac_base", 15) if h else 15,
                "pos_x": h.pos_x if h else 0,
                "pos_y": h.pos_y if h else 0,
                "pontos_movimento": p.get("pontos_movimento", 0),
                "pontos_trabalho": p.get("pontos_trabalho", 0),
                "pontos_escavacao": p.get("pontos_escavacao", 0),
                "cards_count": len(p.get("mao", [])),
                # A mão secreta só é enviada para o próprio jogador
                "hand": p.get("mao", []) if is_me else [],
                "is_me": is_me,
                "card_locked": self.cartas_selecionadas.get(pid) is not None,
                "ready": p.get("ready", False),
                "connected": p.get("connected", True),
            })

        enemies_data = []
        for ini in self.inimigos:
            if ini.hp_atual > 0:
                c_name = ini.__class__.__name__
                enemies_data.append({
                    "id": ini.nome,
                    "nome": ini.nome,
                    "tipo": c_name,
                    "sprite_url": SPRITES_INIMIGOS.get(c_name, "/assets/images/characters/monsters/isectum/larva_carniceira.png"),
                    "hp_atual": ini.hp_atual,
                    "hp_max": ini.hp_max,
                    "pos_x": ini.pos_x,
                    "pos_y": ini.pos_y,
                })

        return {
            "room_id": self.room_id,
            "fase": self.fase,
            "round": self.round_atual,
            "sinergia_ativa": self.sinergia_ativa,
            "recursos": self.recursos,
            "heroes": heroes_data,
            "enemies": enemies_data,
            "grid_terreno": self.tabuleiro.terrain_grid,
            "combat_log": self.combat_log[-20:],
        }
