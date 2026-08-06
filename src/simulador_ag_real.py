"""
simulador_ag_real.py — Algoritmo Genético Integrado ao Código Real do Jogo (Versão Avançada)

Este script roda o Algoritmo Genético de Balanceamento utilizando as CLASSES E ENGINE REAIS DO JOGO:
  - CercoState (Máquina de estados oficial do Modo Cerco)
  - BotHeroi (Controlador de IA com os cromossomos genéticos)
  - MotorCombate, Tabuleiro e Resolvedor de Ações em 2D
  - Personagens reais: Stark, Elden, Kuro, Darwin e Boss A Mão Rei

Como executar com escolha de dificuldade:
  python3 src/simulador_ag_real.py
  python3 src/simulador_ag_real.py --facil
  python3 src/simulador_ag_real.py --medio
  python3 src/simulador_ag_real.py --dificil
"""

from __future__ import annotations
import os
import sys
import time
import random
import copy
from typing import Dict, List, Tuple

# Configura o Pygame para rodar em modo Headless (sem janela visual)
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()
pygame.font.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

# Garante que a pasta raiz do projeto está no sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Bypassa a animação 3D de dados no modo headless (elimina delay de 250ms por ataque)
try:
    import src.ui.dado_3d as dado_3d_mod
    dado_3d_mod.animar_rolagem_dado = lambda tela, tipo_dado="d6", resultado=None: None
except Exception:
    pass

# Importa as classes reais do jogo
from src.states.cerco.state import CercoState
from src.states.cerco.bot_heroi import BotHeroi
from src.personagens.guerreiro import Guerreiro
from src.personagens.mago import Mago
from src.personagens.ladino import Ladino
from src.personagens.arqueiro import Arqueiro

# Configurações de Dificuldade Selecionáveis
DIFICULDADES_DISPONIVEIS = {
    "1": {"id": "facil", "nome": "Fácil", "fator_deck": 0.25, "pedregulhos": 3, "tesouro": 30, "reserva": 20},
    "2": {"id": "normal", "nome": "Normal / Médio", "fator_deck": 0.50, "pedregulhos": 5, "tesouro": 25, "reserva": 15},
    "3": {"id": "dificil", "nome": "Difícil", "fator_deck": 1.00, "pedregulhos": 8, "tesouro": 20, "reserva": 10},
}


class MockGame:
    """Objeto mock simples para satisfazer a dependência do GameState."""
    def __init__(self, diff_preset=None):
        self.tela = pygame.Surface((800, 600))
        self.estado_atual = None
        self.angulo_rotacao = 0.0
        self.delta_time = 0.016
        self.dificuldade_selecionada = diff_preset or DIFICULDADES_DISPONIVEIS["1"]
        self.personagens_selecionados = [
            ("Stark", Guerreiro),
            ("Elden", Mago),
            ("Kuro", Ladino),
            ("Darwin", Arqueiro),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# CROMOSSOMO / GENOMA DA IA REAL COM MÉTRICAS EXPANDIDAS
# ═══════════════════════════════════════════════════════════════════════════
class GenomaIAReal:
    """Representa um perfil genético de tomada de decisão com estatísticas ricas."""

    def __init__(self, genes: Dict[str, float] | None = None):
        self.genes = genes or {
            "agressividade":       random.uniform(0.3, 1.0),
            "prioridade_minerador":random.uniform(0.3, 1.0),
            "prioridade_arqueiro": random.uniform(0.3, 1.0),
            "foco_upgrades":       random.uniform(0.2, 0.9),
            "foco_escavacao":      random.uniform(0.2, 0.9),
            "foco_mobilidade":     random.uniform(0.1, 0.8),
        }
        self.fitness: float = 0.0
        self.vitorias: int = 0
        self.derrotas: int = 0
        self.total_rodadas: int = 0
        self.dano_causado: int = 0
        self.dano_sofrido: int = 0
        self.boss_derrotados: int = 0
        self.boss_spawnou: int = 0
        self.mercenarios_recrutados: int = 0
        self.upgrades_comprados: int = 0
        self.sobreviventes_herois: Dict[str, int] = {"Stark": 0, "Elden": 0, "Kuro": 0, "Darwin": 0}

    def clonar(self) -> GenomaIAReal:
        g = GenomaIAReal(dict(self.genes))
        g.fitness = self.fitness
        g.vitorias = self.vitorias
        g.derrotas = self.derrotas
        g.total_rodadas = self.total_rodadas
        g.dano_causado = self.dano_causado
        g.dano_sofrido = self.dano_sofrido
        g.boss_derrotados = self.boss_derrotados
        g.boss_spawnou = self.boss_spawnou
        g.mercenarios_recrutados = self.mercenarios_recrutados
        g.upgrades_comprados = self.upgrades_comprados
        g.sobreviventes_herois = dict(self.sobreviventes_herois)
        return g

    def mutar(self, taxa_mutacao: float = 0.15, intensidade: float = 0.2):
        for chave in self.genes:
            if random.random() < taxa_mutacao:
                delta = random.gauss(0, intensidade)
                self.genes[chave] = max(0.05, min(1.0, self.genes[chave] + delta))


def crossover_real(pai1: GenomaIAReal, pai2: GenomaIAReal) -> GenomaIAReal:
    filho_genes = {}
    for chave in pai1.genes:
        filho_genes[chave] = pai1.genes[chave] if random.random() > 0.5 else pai2.genes[chave]
    return GenomaIAReal(filho_genes)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULADOR USANDO AS CLASSES E MOTOR REAIS DO JOGO
# ═══════════════════════════════════════════════════════════════════════════
def rodar_partida_real(genoma: GenomaIAReal, diff_preset: Dict = None, max_ticks: int = 1500) -> Dict[str, any]:
    """Instancia um CercoState real e executa o jogo coletando estatísticas detalhadas."""
    mock_game = MockGame(diff_preset=diff_preset)

    config = {
        "dificuldade": mock_game.dificuldade_selecionada,
        "herois": mock_game.personagens_selecionados
    }

    cerco = CercoState(mock_game, config=config)
    cerco.autoplay_ativo = True
    cerco._push = lambda canal, msg: None

    # Garante a mão inicial do primeiro herói ao iniciar o estado
    if not cerco.estado.get("mao"):
        cerco._comprar_mao()

    # Instancia o BotAutoPlay real alimentado pelos genes com velocidade instantânea
    bot = BotHeroi(cerco, velocidade="rapido")
    bot._timer = 0
    bot.genoma = dict(genoma.genes)
    cerco.bot_heroi = bot

    # Acelera a IA do Filho do Imperador (diretor inimigo) para modo headless instantâneo
    if hasattr(cerco, "ia_comandante") and cerco.ia_comandante is not None:
        cerco.ia_comandante.delay = 1
        cerco.ia_comandante.timer = 0

    dano_causado_acumulado = 0
    dano_sofrido_acumulado = 0

    # Rastreia HP em tempo real frame-a-frame
    last_hero_hps = {h.nome: h.hp_atual for h in cerco.herois}
    last_enemy_hps = {}

    ticks = 0
    while ticks < max_ticks:
        ticks += 1
        cerco.update()

        # Zera timers de delay para rotação instantânea em simulação
        if cerco.bot_heroi is not None:
            cerco.bot_heroi._timer = 0
        if hasattr(cerco, "ia_comandante") and cerco.ia_comandante is not None:
            cerco.ia_comandante.timer = 0

        # Rastreia dano sofrido pelos heróis no frame
        for h in cerco.herois:
            prev = last_hero_hps.get(h.nome, h.hp_atual)
            diff = prev - h.hp_atual
            if diff > 0:
                dano_sofrido_acumulado += diff
            last_hero_hps[h.nome] = h.hp_atual

        # Rastreia dano causado aos inimigos/boss no frame
        for c in cerco.motor.combatentes:
            if c not in cerco.herois and not getattr(c, "is_mercenario", False):
                prev_ini = last_enemy_hps.get(id(c), c.hp_atual)
                diff_ini = prev_ini - c.hp_atual
                if diff_ini > 0:
                    dano_causado_acumulado += diff_ini
                last_enemy_hps[id(c)] = c.hp_atual

        if cerco.estado.get("vitoria") or cerco.estado.get("derrota"):
            break

    # Coleta de métricas reais da partida
    vit = cerco.estado.get("vitoria", False)
    if not vit:
        # Se as cartas de ameaça acabaram e os heróis mantiveram a fortaleza viva, considera vitória de resistência
        if not cerco.deck or len(cerco.deck) == 0:
            vit = any(h.hp_atual > 0 for h in cerco.herois)

    boss_spawn = cerco.estado.get("mao_rei_spawnou", False)
    boss_morto = vit and boss_spawn

    # Mercenários e Upgrades
    merc_recrutados = len([c for c in cerco.motor.time_a if getattr(c, "is_mercenario", False)])
    upgrades = len(cerco.estado.get("cartas_upgrade_ativas", []))

    # Sobrevivência por herói
    sobreviventes = {h.nome: 1 if h.hp_atual > 0 else 0 for h in cerco.herois}

    return {
        "vitoria": vit,
        "rodadas": max(1, ticks // 20),
        "boss_spawnou": boss_spawn,
        "boss_morto": boss_morto,
        "dano_causado": dano_causado_acumulado,
        "dano_sofrido": dano_sofrido_acumulado,
        "mercenarios": merc_recrutados,
        "upgrades": upgrades,
        "sobreviventes": sobreviventes
    }


# ═══════════════════════════════════════════════════════════════════════════
# ALGORITMO GENÉTICO SOBRE O JOGO REAL
# ═══════════════════════════════════════════════════════════════════════════
class AlgoritmoGeneticoReal:
    def __init__(self, diff_preset: Dict, tam_populacao: int = 10, simulacoes_por_ind: int = 5):
        self.diff_preset = diff_preset
        self.tam_populacao = tam_populacao
        self.simulacoes_por_ind = simulacoes_por_ind
        self.populacao: List[GenomaIAReal] = [GenomaIAReal() for _ in range(tam_populacao)]
        self.geracao = 0

    def avaliar_populacao(self):
        for ind in self.populacao:
            vitorias = 0
            total_rodadas = 0
            boss_kills = 0
            boss_spawns = 0
            tot_dano_c = 0
            tot_dano_s = 0
            tot_merc = 0
            tot_upg = 0
            tot_sob = {"Stark": 0, "Elden": 0, "Kuro": 0, "Darwin": 0}

            for _ in range(self.simulacoes_por_ind):
                res = rodar_partida_real(ind, diff_preset=self.diff_preset, max_ticks=1500)
                if res["vitoria"]:
                    vitorias += 1
                if res["boss_morto"]:
                    boss_kills += 1
                if res["boss_spawnou"]:
                    boss_spawns += 1

                total_rodadas += res["rodadas"]
                tot_dano_c += res["dano_causado"]
                tot_dano_s += res["dano_sofrido"]
                tot_merc += res["mercenarios"]
                tot_upg += res["upgrades"]

                for h_nome, sob in res["sobreviventes"].items():
                    tot_sob[h_nome] += sob

            ind.vitorias = vitorias
            ind.derrotas = self.simulacoes_por_ind - vitorias
            ind.total_rodadas = total_rodadas // self.simulacoes_por_ind
            ind.boss_derrotados = boss_kills
            ind.boss_spawnou = boss_spawns
            ind.dano_causado = tot_dano_c // self.simulacoes_por_ind
            ind.dano_sofrido = tot_dano_s // self.simulacoes_por_ind
            ind.mercenarios_recrutados = tot_merc // self.simulacoes_por_ind
            ind.upgrades_comprados = tot_upg // self.simulacoes_por_ind
            ind.sobreviventes_herois = tot_sob

            taxa_vit = vitorias / self.simulacoes_por_ind
            ind.fitness = max(1.0, (taxa_vit * 120) + (ind.dano_causado * 0.4) - (ind.dano_sofrido * 0.2) + (boss_kills * 25))

    def evoluir_geracao(self) -> GenomaIAReal:
        self.avaliar_populacao()
        self.populacao.sort(key=lambda ind: ind.fitness, reverse=True)

        campeao = self.populacao[0].clonar()

        nova_pop = [self.populacao[0].clonar(), self.populacao[1].clonar()]
        while len(nova_pop) < self.tam_populacao:
            pai1 = random.choice(self.populacao[:4])
            pai2 = random.choice(self.populacao[:4])
            filho = crossover_real(pai1, pai2)
            filho.mutar(taxa_mutacao=0.2, intensidade=0.15)
            nova_pop.append(filho)

        self.populacao = nova_pop
        self.geracao += 1
        return campeao


# ═══════════════════════════════════════════════════════════════════════════
# EXECUÇÃO E MENU SELETOR DE DIFICULDADE
# ═══════════════════════════════════════════════════════════════════════════
def escolher_dificuldade() -> Dict:
    """Detecta argumento de linha de comando ou exibe menu interativo."""
    if "--facil" in sys.argv:
        return DIFICULDADES_DISPONIVEIS["1"]
    elif "--medio" in sys.argv or "--normal" in sys.argv:
        return DIFICULDADES_DISPONIVEIS["2"]
    elif "--dificil" in sys.argv:
        return DIFICULDADES_DISPONIVEIS["3"]

    print("=" * 80)
    print("🧬 SIMULADOR DE ALGORITMO GENÉTICO NO JOGO REAL — MODO CERCO")
    print("=" * 80)
    print("Escolha o nível de dificuldade para testar o balanceamento:")
    print("  [1] 🟢 FÁCIL           (12 Ameaças | 30 Cristais | Pátio Limpo)")
    print("  [2] 🟡 NORMAL / MÉDIO  (24 Ameaças | 25 Cristais | Pátio Moderado)")
    print("  [3] 🔴 DIFÍCIL         (48 Ameaças | 20 Cristais | Pátio Obstruído)")
    print("=" * 80)

    try:
        opcao = input("Digite a opção desejada [1, 2 ou 3] (Padrão: 1): ").strip()
    except Exception:
        opcao = "1"

    return DIFICULDADES_DISPONIVEIS.get(opcao, DIFICULDADES_DISPONIVEIS["1"])


def executar_simulador_ag_real(geracoes: int = 10):
    diff_preset = escolher_dificuldade()

    print("\n" + "=" * 80)
    print(f"🎮 INICIANDO SIMULAÇÃO NA DIFICULDADE: {diff_preset['nome'].upper()}")
    print("=" * 80)
    print(f"⚙️ Configuração: {geracoes} Gerações | 10 Indivíduos | 5 Partidas Reais por Indivícito")
    print("🚀 Rodando simulação de alto desempenho em modo Headless...\n")

    t_inicio = time.time()
    ag = AlgoritmoGeneticoReal(diff_preset=diff_preset, tam_populacao=10, simulacoes_por_ind=5)
    melhor_absoluto = None

    for g in range(1, geracoes + 1):
        campeao = ag.evoluir_geracao()
        if melhor_absoluto is None or campeao.fitness > melhor_absoluto.fitness:
            melhor_absoluto = campeao.clonar()

        progresso = int((g / geracoes) * 20)
        barra = "█" * progresso + "░" * (20 - progresso)
        print(f"Geração {g:02d}/{geracoes:02d} [{barra}] ── Fitness: {campeao.fitness:.1f} | Vitórias: {campeao.vitorias}/5 ({campeao.vitorias/5*100:.0f}%) | Média Rodadas: {campeao.total_rodadas}")

    t_fim = time.time()
    duracao = t_fim - t_inicio
    total_partidas = geracoes * 10 * 5

    print("\n" + "=" * 80)
    print(f"📊 RELATÓRIO DE ESTATÍSTICAS NO JOGO REAL — DIFICULDADE: {diff_preset['nome'].upper()}")
    print("=" * 80)
    print(f"⏱️ Tempo total de execução: {duracao:.2f} segundos ({total_partidas} partidas reais simuladas)")
    print(f"⚡ Velocidade de processamento: {total_partidas / max(0.001, duracao):.1f} partidas reais/segundo\n")

    print("🏆 GENOMA VENCEDOR DA EVOLUÇÃO (Melhor Perfil Tático):")
    for gene, valor in melhor_absoluto.genes.items():
        bar = "▓" * int(valor * 15)
        print(f"  • {gene.replace('_', ' ').title():<22}: {valor:.2f} [{bar:<15}]")

    print("\n⚔️ ESTATÍSTICAS DETALHADAS DE COMBATE E RECURSOS:")
    print(f"  • Taxa de Vitória das IAs no Jogo Real : {melhor_absoluto.vitorias/5*100:.1f}%")
    print(f"  • Duração Média da Partida Real        : {melhor_absoluto.total_rodadas} rodadas")
    print(f"  • Média Dano Físico Causado / Jogo     : {melhor_absoluto.dano_causado} HP")
    print(f"  • Média Dano Sofrido pelos Heróis      : {melhor_absoluto.dano_sofrido} HP")
    dps_ratio = melhor_absoluto.dano_causado / max(1, melhor_absoluto.dano_sofrido)
    print(f"  • Razão Dano Causado / Sofrido         : {dps_ratio:.2f}x")
    print(f"  • Mercenários Recrutados por Jogo      : {melhor_absoluto.mercenarios_recrutados} unidades")
    print(f"  • Upgrades Comprados no Mercado        : {melhor_absoluto.upgrades_comprados} cartas")
    print(f"  • Abates do Boss A Mão Rei             : {melhor_absoluto.boss_derrotados} de {melhor_absoluto.boss_spawnou} aparições")

    print("\n🛡️ TAXA DE SOBREVOVÊNCIA POR HERÓI:")
    for h_nome, sob in melhor_absoluto.sobreviventes_herois.items():
        pct = (sob / 5) * 100
        bar_h = "█" * int(pct / 10)
        print(f"  • {h_nome:<10}: {pct:5.1f}% [{bar_h:<10}]")

    print("\n⚖️ DIAGNÓSTICO DE BALANCEAMENTO:")
    if melhor_absoluto.vitorias / 5 >= 0.6:
        print(f"  🟢 JOGO BALANCEADO / VANTAGEM DOS HERÓIS: A IA tática conseguiu alta taxa de vitória no nível {diff_preset['nome']}.")
    elif melhor_absoluto.vitorias / 5 >= 0.3:
        print(f"  🟡 JOGO DESAFIADOR: Combate equilibrado no nível {diff_preset['nome']}.")
    else:
        print(f"  🔴 JOGO DIFICIL: A horda de insetos superou os heróis na dificuldade {diff_preset['nome']}.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    executar_simulador_ag_real(geracoes=10)
