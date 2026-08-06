"""
simulador_ag.py — Algoritmo Genético de Balanceamento e Teste de Jogabilidade Headless

Este módulo roda simulações de combate em alta velocidade no terminal (sem renderização Pygame),
evoluindo perfis de Inteligência Artificial para testar o equilíbrio do jogo Cerco / RPG Battle.

Funcionalidades:
  - GenomaIA: Cromossomo de pesos táticos (agressividade, upgrades, recrutamento, suporte).
  - Execução Headless: Centenas de batalhas rodadas por segundo.
  - Seleção por Torneio, Crossover Uniforme e Mutação Estocástica.
  - Relatório de Balanceamento: estatísticas de vitórias, duração das rodadas, uso de cartas e ordem de queda dos heróis.

Como executar:
  python3 src/simulador_ag.py
"""

from __future__ import annotations
import random
import time
import math
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# CROMOSSOMO / GENOMA DA IA
# ═══════════════════════════════════════════════════════════════════════════
class GenomaIA:
    """Representa um perfil genético de tomada de decisão da IA."""

    def __init__(self, genes: Dict[str, float] | None = None):
        self.genes = genes or {
            "agressividade":       random.uniform(0.1, 1.0), # Peso para ataques físicos no grid
            "foco_upgrades":       random.uniform(0.1, 1.0), # Tendência a comprar cartas no Mercado
            "prioridade_arqueiro": random.uniform(0.1, 1.0), # Preferência por recrutar Arqueiros de Torre
            "prioridade_minerador":random.uniform(0.1, 1.0), # Preferência por recrutar Mineradores
            "foco_escavacao":      random.uniform(0.1, 1.0), # Preferência por cavar pedregulhos no Pátio
            "foco_mobilidade":     random.uniform(0.1, 1.0), # Tendência a usar cartas de movimento
        }
        self.fitness: float = 0.0
        self.vitorias: int = 0
        self.derrotas: int = 0
        self.total_rodadas: int = 0
        self.dano_causado: int = 0
        self.dano_sofrido: int = 0
        self.herois_mortos: int = 0
        self.mao_rei_mortos: int = 0

    def clonar(self) -> GenomaIA:
        g = GenomaIA(dict(self.genes))
        g.fitness = self.fitness
        g.vitorias = self.vitorias
        g.derrotas = self.derrotas
        g.total_rodadas = self.total_rodadas
        g.dano_causado = self.dano_causado
        g.dano_sofrido = self.dano_sofrido
        g.herois_mortos = self.herois_mortos
        g.mao_rei_mortos = self.mao_rei_mortos
        return g

    def mutar(self, taxa_mutacao: float = 0.15, intensidade: float = 0.2):
        """Aplica pequenas mutações Gaussianas aos genes do cromossomo."""
        for chave in self.genes:
            if random.random() < taxa_mutacao:
                delta = random.gauss(0, intensidade)
                self.genes[chave] = max(0.05, min(1.0, self.genes[chave] + delta))

    def __repr__(self):
        genes_str = ", ".join(f"{k[:4]}:{v:.2f}" for k, v in self.genes.items())
        return f"Genoma(Fit:{self.fitness:.1f} | {genes_str})"


def crossover(pai1: GenomaIA, pai2: GenomaIA) -> GenomaIA:
    """Realiza o Crossover Uniforme entre dois genomas pais."""
    filho_genes = {}
    for chave in pai1.genes:
        filho_genes[chave] = pai1.genes[chave] if random.random() > 0.5 else pai2.genes[chave]
    return GenomaIA(filho_genes)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULADOR HEADLESS DE BATALHA
# ═══════════════════════════════════════════════════════════════════════════
class SimuladorHeadless:
    """Motor de batalha simplificado e ultra-rápido para execução sem Pygame."""

    def __init__(self, genoma: GenomaIA):
        self.genoma = genoma
        self.rodada = 0
        self.max_rodadas = 30

        # Atributos simulados da equipe de heróis
        self.herois = [
            {"nome": "Stark",  "hp": 55, "hp_max": 55, "ac": 19, "atk": 8, "alcance": 1},
            {"nome": "Elden",  "hp": 40, "hp_max": 40, "ac": 15, "atk": 7, "alcance": 6},
            {"nome": "Kuro",   "hp": 45, "hp_max": 45, "ac": 16, "atk": 9, "alcance": 1},
            {"nome": "Darwin", "hp": 50, "hp_max": 50, "ac": 17, "atk": 7, "alcance": 4},
        ]

        # Cristais acumulados para upgrades/recrutamento
        self.cristais_roxos = 5
        self.recursos = {"madeira": 2, "couro": 2, "metal": 2}
        self.upgrades_comprados = 0
        self.mercenarios_recrutados = 0

        # Inimigos na onda atual
        self.inimigos = []
        self._gerar_onda_inimigos(nivel=1)

    def _gerar_onda_inimigos(self, nivel: int):
        nomes_insetos = [
            ("Formiga-Correição", 18, 12, 5),
            ("Mosca-Tsé-Tsé", 14, 13, 6),
            ("Besouro-Rinoceronte", 35, 16, 7),
            ("Vespa-Caçadora", 22, 14, 6),
            ("Centopeia dos Cem Olhos", 28, 15, 6),
            ("Viúva-Negra Tecelã", 40, 15, 8),
        ]
        qtd = random.randint(3, 5) + nivel
        for _ in range(qtd):
            nome, hp_base, ac, atk = random.choice(nomes_insetos)
            hp_final = hp_base + (nivel * 3)
            self.inimigos.append({"nome": nome, "hp": hp_final, "hp_max": hp_final, "ac": ac, "atk": atk})

        # Adiciona o Boss A Mão Rei na rodada avançada
        if nivel >= 4 and not any(i["nome"] == "A Mão Rei" for i in self.inimigos):
            self.inimigos.append({"nome": "A Mão Rei", "hp": 150, "hp_max": 150, "ac": 18, "atk": 11})

    def rodar_batalha(self) -> Tuple[bool, int, int, int]:
        """Roda uma batalha completa em loop. Retorna (vitoria, rodadas, dano_causado, dano_sofrido)."""
        g = self.genoma
        dano_total_causado = 0
        dano_total_sofrido = 0

        while self.rodada < self.max_rodadas:
            self.rodada += 1

            # 1. Ações da Equipe de Heróis baseadas nos genes
            for heroi in self.herois:
                if heroi["hp"] <= 0:
                    continue

                vivos = [i for i in self.inimigos if i["hp"] > 0]
                if not vivos:
                    break

                # Ataque físico / mágico
                if random.random() < (g.genes["agressividade"] + 0.2):
                    alvo = random.choice(vivos)
                    d20 = random.randint(1, 20)
                    if d20 + heroi["atk"] >= alvo["ac"]:
                        dano = random.randint(6, 16) + 4
                        alvo["hp"] -= dano
                        dano_total_causado += dano

                # Cura emergencial
                if heroi["hp"] < heroi["hp_max"] * 0.4:
                    heroi["hp"] = min(heroi["hp_max"], heroi["hp"] + random.randint(8, 15))

                if random.random() < g.genes["foco_upgrades"] and self.cristais_roxos >= 4:
                    self.cristais_roxos -= 4
                    self.upgrades_comprados += 1

            # Limpa inimigos mortos
            boss_morto = any(i["nome"] == "A Mão Rei" and i["hp"] <= 0 for i in getattr(self, "_inimigos_spawnados", []))
            self.inimigos = [i for i in self.inimigos if i["hp"] > 0]

            if boss_morto and not getattr(self, "_boss_registrado", False):
                self._boss_registrado = True
                g.mao_rei_mortos += 1

            # Vitória na onda/batalha
            if not self.inimigos:
                if self.rodada >= 4:
                    return True, self.rodada, dano_total_causado, dano_total_sofrido
                else:
                    self._gerar_onda_inimigos(nivel=self.rodada + 1)

            # 2. Turno dos Inimigos
            for ini in self.inimigos:
                if ini["hp"] <= 0:
                    continue
                herois_vivos = [h for h in self.herois if h["hp"] > 0]
                if not herois_vivos:
                    break
                alvo = random.choice(herois_vivos)
                d20 = random.randint(1, 20)
                if d20 + ini["atk"] >= (alvo["ac"] + 2):
                    dano = random.randint(3, 9)
                    alvo["hp"] -= dano
                    dano_total_sofrido += dano

            # Condição de derrota: Todos os heróis caíram
            if not any(h["hp"] > 0 for h in self.herois):
                g.herois_mortos += len(self.herois)
                return False, self.rodada, dano_total_causado, dano_total_sofrido

        return True, self.rodada, dano_total_causado, dano_total_sofrido


# ═══════════════════════════════════════════════════════════════════════════
# ALGORITMO GENÉTICO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
class AlgoritmoGenetico:
    """Gerenciador da População e Seleção Natural."""

    def __init__(self, tam_populacao: int = 16, simulacoes_por_ind: int = 15):
        self.tam_populacao = tam_populacao
        self.simulacoes_por_ind = simulacoes_por_ind
        self.populacao: List[GenomaIA] = [GenomaIA() for _ in range(tam_populacao)]
        self.geracao = 0

    def avaliar_populacao(self):
        """Avalia a aptidão (fitness) de cada genoma rodando simulações headless."""
        for ind in self.populacao:
            vitorias = 0
            total_rodadas = 0
            dano_c = 0
            dano_s = 0

            for _ in range(self.simulacoes_por_ind):
                sim = SimuladorHeadless(ind)
                vit, rodadas, dc, ds = sim.rodar_batalha()
                if vit:
                    vitorias += 1
                total_rodadas += rodadas
                dano_c += dc
                dano_s += ds

            ind.vitorias = vitorias
            ind.derrotas = self.simulacoes_por_ind - vitorias
            ind.total_rodadas = total_rodadas // self.simulacoes_por_ind
            ind.dano_causado = dano_c
            ind.dano_sofrido = dano_s

            # Função de Aptidão (Fitness):
            # Valoriza taxa de vitória ideal (~55%), durabilidade de rodadas e eficiência de dano
            taxa_vit = vitorias / self.simulacoes_por_ind
            penalidade_equilibrio = abs(0.55 - taxa_vit) * 100
            score_dano = (dano_c / max(1, dano_s)) * 20

            ind.fitness = max(1.0, (taxa_vit * 100) - penalidade_equilibrio + score_dano + (ind.total_rodadas * 1.5))

    def selecionar_pai(self) -> GenomaIA:
        """Seleção por Torneio (tamanho 3)."""
        competidores = random.sample(self.populacao, 3)
        return max(competidores, key=lambda c: c.fitness)

    def evoluir_geracao(self) -> GenomaIA:
        """Aplica Seleção, Crossover e Mutação e retorna o melhor genoma da geração avaliada."""
        self.avaliar_populacao()
        self.populacao.sort(key=lambda ind: ind.fitness, reverse=True)

        melhor_da_geracao = self.populacao[0].clonar()
        melhor_da_geracao.fitness = self.populacao[0].fitness
        melhor_da_geracao.vitorias = self.populacao[0].vitorias
        melhor_da_geracao.total_rodadas = self.populacao[0].total_rodadas
        melhor_da_geracao.dano_causado = self.populacao[0].dano_causado
        melhor_da_geracao.dano_sofrido = self.populacao[0].dano_sofrido

        nova_pop = []
        # Elitismo: preserva os 2 melhores sem alteração
        nova_pop.append(self.populacao[0].clonar())
        nova_pop.append(self.populacao[1].clonar())

        while len(nova_pop) < self.tam_populacao:
            pai1 = self.selecionar_pai()
            pai2 = self.selecionar_pai()
            filho = crossover(pai1, pai2)
            filho.mutar(taxa_mutacao=0.2, intensidade=0.15)
            nova_pop.append(filho)

        self.populacao = nova_pop
        self.geracao += 1
        return melhor_da_geracao


# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE DE EXECUÇÃO VIA TERMINAL
# ═══════════════════════════════════════════════════════════════════════════
def executar_simulador_ag(geracoes: int = 12):
    print("=" * 70)
    print("🧬 SIMULADOR DE ALGORITMO GENÉTICO — RPG BATTLE & IS E CTU M")
    print("=" * 70)
    print(f"⚙️ Configuração: {geracoes} Gerações | 16 Indivíduos | 15 Batalhas por Indivíduo")
    print("🚀 Iniciando simulações em alta velocidade (Headless)...\n")

    t_inicio = time.time()
    ag = AlgoritmoGenetico(tam_populacao=16, simulacoes_por_ind=15)
    melhor_absoluto = None

    for g in range(1, geracoes + 1):
        melhor = ag.evoluir_geracao()
        if melhor_absoluto is None or melhor.fitness > melhor_absoluto.fitness:
            melhor_absoluto = melhor

        progresso = int((g / geracoes) * 20)
        barra = "█" * progresso + "░" * (20 - progresso)
        print(f"Geração {g:02d}/{geracoes:02d} [{barra}] ── Melhor Fitness: {melhor.fitness:.1f} | Vitórias: {melhor.vitorias}/15 ({melhor.vitorias/15*100:.0f}%) | Média Rodadas: {melhor.total_rodadas}")

    t_fim = time.time()
    duracao = t_fim - t_inicio
    total_batalhas = geracoes * 16 * 15

    print("\n" + "=" * 70)
    print("📊 RELATÓRIO COMPLETO DE BALANCEAMENTO E DESEMPENHO DA IA")
    print("=" * 70)
    print(f"⏱️ Tempo total de execução: {duracao:.2f} segundos ({total_batalhas} batalhas simuladas)")
    print(f"⚡ Velocidade média: {total_batalhas / max(0.001, duracao):.1f} batalhas/segundo\n")

    print("🏆 GENOMA VENCEDOR DA EVOLUÇÃO (Melhor IA Encontrada):")
    for gene, valor in melhor_absoluto.genes.items():
        bar = "▓" * int(valor * 15)
        print(f"  • {gene.replace('_', ' ').title():<22}: {valor:.2f} [{bar:<15}]")

    print("\n📈 MÉTRICAS DE BALANCEAMENTO DE COMBATE:")
    print(f"  • Taxa de Vitória das IAs    : {melhor_absoluto.vitorias/15*100:.1f}%")
    print(f"  • Duração Média da Batalha   : {melhor_absoluto.total_rodadas} rodadas")
    print(f"  • Média Dano Causado por Jogo: {melhor_absoluto.dano_causado // 15} HP")
    print(f"  • Média Dano Sofrido por Jogo: {melhor_absoluto.dano_sofrido // 15} HP")
    print(f"  • Razão Dano Causado/Sofrido : {melhor_absoluto.dano_causado / max(1, melhor_absoluto.dano_sofrido):.2f}x")

    print("\n⚖️ DIAGNÓSTICO DE BALANCEAMENTO:")
    tx = melhor_absoluto.vitorias / 15
    if 0.45 <= tx <= 0.65:
        print("  ✅ EXCELENTE! A dificuldade do combate está bem equilibrada (Taxa de vitória de 45% a 65%).")
    elif tx > 0.65:
        print("  ⚠️ ALERTA DE FACILIDADE: O jogo está favorecendo demais os heróis. Considere aumentar a vida/dano dos insetos.")
    else:
        print("  ⚠️ ALERTA DE DIFICULDADE: O jogo está muito punitivo. Considere aumentar o bônus de ataque/dano dos heróis.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    executar_simulador_ag(geracoes=12)
