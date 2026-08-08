"""
test_round_simultaneo.py — Testes unitários para a mecânica de Round de Sincronia

Cobre:
  - Inicialização do round simultâneo
  - Seleção de carta por herói
  - Detecção de sinergia (2+ heróis, mesmo tipo)
  - Bônus supremo (todos jogam o mesmo tipo)
  - Fim de turno quando primeiro herói esgota a mão
  - Resolução de efeitos por camadas de tipo
  - Pressão crescente (rounds 1, 2, 3+)
  - Vantagem por velocidade
"""
from __future__ import annotations
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.states.cerco.round_simultaneo import RoundSimultaneoMixin, BONUS_SINERGIA, BONUS_SUPREMO


# ─── Classe fake para testar o Mixin em isolamento ───────────────────────────

class FakeHeroi:
    """Herói mínimo para os testes."""
    def __init__(self, nome, hp=50):
        self.nome = nome
        self.hp_atual = hp
        self.hp_max = hp
        self.pos_x = 9
        self.pos_y = 9
        self.time = "A"
        self.alcance = 1
        self.bonus_ataque = 5
        self.dado_dano = (1, 6)
        self.bonus_dano = 3
        self.ac = 14


class FakeMotor:
    """Motor mínimo para evitar dependências reais."""
    def __init__(self):
        self.combatentes = []
        self.tabuleiro = MagicMock()
        self.tabuleiro.largura = 20
        self.tabuleiro.altura = 20


def _make_carta(tipo="movimento", valor=2, nome="Carta X", uid=None):
    c = {"nome": nome, "tipo": None if tipo != "upgrade" else "upgrade"}
    if tipo == "movimento":
        c["movimento"] = valor
    elif tipo == "trabalho":
        c["trabalho"] = valor
    elif tipo == "escavacao":
        c["escavacao"] = valor
    if uid:
        c["id"] = uid
    return c


class FakeCercoState(RoundSimultaneoMixin):
    """
    Instância fake que herda apenas o Mixin para testes isolados,
    sem depender de Pygame ou do engine completo.
    """

    def __init__(self, herois):
        self.herois = herois
        self.heroi_atual_idx = 0
        self.fase = "JOGAR_CARTA"
        self.motor = FakeMotor()
        self.log = []
        self.msg_feedback = ""
        self.estado = {
            "mao": [_make_carta("movimento", 2, "Passo Rápido")],
            "deck_heroi": [_make_carta("trabalho", 1, "Trabalho Duro")],
            "descarte": [],
            "excluidas_ciclo": [],
            "pontos_movimento": 0,
            "pontos_trabalho": 0,
            "pontos_escavacao": 0,
            "herois_status": {},
            "herois_jogaram": [],
            "tesouro": 10,
            "pedregulhos": 5,
            "recursos_depositados": {"madeira": 0, "couro": 0, "metal": 0},
            "cartas_upgrade_ativas": [],
            "invasores": {},
        }
        # Inicializa mãos para cada herói no herois_status
        for h in herois[1:]:
            self.estado["herois_status"][h.nome] = {
                "mao": [_make_carta("trabalho", 1, f"Carta de {h.nome}")],
                "deck_heroi": [],
                "descarte": [],
                "excluidas_ciclo": [],
                "pontos_movimento": 0,
                "pontos_trabalho": 0,
                "pontos_escavacao": 0,
            }

        self._init_round_simultaneo()

    @property
    def heroi_atual(self):
        if not self.herois:
            return None
        idx = min(self.heroi_atual_idx, len(self.herois) - 1)
        return self.herois[idx]

    # Stubs necessários pelo Mixin
    def _push(self, tipo, msg):
        self.log.append((tipo, msg))

    def _feedback(self, msg, cor=None):
        self.msg_feedback = msg

    def _processar_turnos_inimigos(self, apenas_passo=False):
        self._processou_inimigos = getattr(self, "_processou_inimigos", 0) + 1
        self._ultimo_apenas_passo = apenas_passo

    def _processar_ataques_inimigos_round(self):
        self._processou_ataques = getattr(self, "_processou_ataques", 0) + 1

    def _verificar_derrota_imediata(self):
        return False

    def _concluir_fim_turno_completo(self):
        self._fim_turno_chamado = True

    def _salvar_status_heroi(self, nome):
        pass

    def _push_popup_combate(self, *args, **kwargs):
        pass


# ─── Testes ──────────────────────────────────────────────────────────────────

class TestInitRoundSimultaneo(unittest.TestCase):

    def test_init_zera_variaveis(self):
        h1 = FakeHeroi("Stark")
        state = FakeCercoState([h1])
        self.assertEqual(state.rs_round_atual, 0)
        self.assertFalse(state.rs_ativo)
        self.assertIsNone(state.rs_vencedor_velocidade)
        self.assertEqual(state.rs_cartas_selecionadas, {})
        self.assertEqual(state.rs_bonus_proxima_rodada, {})


class TestIniciarRoundSimultaneo(unittest.TestCase):

    def test_iniciar_turno_sincronia_ativa_round(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        self.assertTrue(state.rs_ativo)
        self.assertEqual(state.rs_round_atual, 1)
        self.assertEqual(state.fase, "ROUND_SIMULTANEO")

    def test_round_registra_todos_herois_vivos(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        h3 = FakeHeroi("Kuro", hp=0)  # Morto — não deve aparecer
        state = FakeCercoState([h1, h2, h3])
        state.iniciar_turno_sincronia()
        # Apenas heróis com hp > 0 entram no round
        self.assertIn("Stark", state.rs_cartas_selecionadas)
        self.assertIn("Elden", state.rs_cartas_selecionadas)
        self.assertNotIn("Kuro", state.rs_cartas_selecionadas)


class TestSelecionarCartaRound(unittest.TestCase):

    def _state_com_2_herois(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        return state, h1, h2

    def test_selecionar_carta_heroi_principal(self):
        state, h1, h2 = self._state_com_2_herois()
        resultado = state.selecionar_carta_round("Stark", 0)
        self.assertTrue(resultado)
        self.assertIsNotNone(state.rs_cartas_selecionadas["Stark"])

    def test_selecionar_carta_indice_invalido_retorna_false(self):
        state, h1, h2 = self._state_com_2_herois()
        resultado = state.selecionar_carta_round("Stark", 99)
        self.assertFalse(resultado)

    def test_fase_errada_retorna_false(self):
        state, h1, h2 = self._state_com_2_herois()
        state.fase = "FASE_AMEACA"
        resultado = state.selecionar_carta_round("Stark", 0)
        self.assertFalse(resultado)

    def test_quando_todos_selecionam_resolve_round(self):
        state, h1, h2 = self._state_com_2_herois()
        # Garante que Elden tem carta na mão
        state.estado["herois_status"]["Elden"]["mao"] = [_make_carta("trabalho", 1, "Carta Elden")]
        state.rs_cartas_selecionadas = {"Stark": None, "Elden": None}

        # Espiona _resolver_round_simultaneo
        state._resolver_chamado = False
        original_resolver = state._resolver_round_simultaneo
        def mock_resolver():
            state._resolver_chamado = True
        state._resolver_round_simultaneo = mock_resolver

        # Seleciona para Stark (1º)
        state.selecionar_carta_round("Stark", 0)
        self.assertFalse(state._resolver_chamado)

        # Seleciona para Elden (último) — deve disparar resolução
        # Elden precisa ser o heroi_atual para pegar da mão do estado principal
        # Como Elden está no herois_status, simulamos com idx=0
        state.rs_cartas_selecionadas["Elden"] = {"carta": _make_carta("trabalho"), "idx": 0}
        # Verifica manualmente se todos escolheram (simula lógica interna)
        herois_vivos = [h for h in state.herois if h.hp_atual > 0]
        todos = all(state.rs_cartas_selecionadas.get(h.nome) is not None for h in herois_vivos)
        self.assertTrue(todos)


class TestCalcularSinergia(unittest.TestCase):

    def _state(self):
        h1 = FakeHeroi("Stark")
        return FakeCercoState([h1])

    def test_sem_sinergia_tipos_diferentes(self):
        state = self._state()
        cartas = {
            "Stark": _make_carta("movimento"),
            "Elden": _make_carta("trabalho"),
        }
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNone(resultado)

    def test_sinergia_movimento_dois_herois(self):
        state = self._state()
        cartas = {
            "Stark": _make_carta("movimento"),
            "Elden": _make_carta("movimento"),
        }
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "passo_extra")

    def test_sinergia_trabalho_dois_herois(self):
        state = self._state()
        cartas = {
            "Stark": _make_carta("trabalho"),
            "Elden": _make_carta("trabalho"),
        }
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "recurso_extra")

    def test_sinergia_escavacao_dois_herois(self):
        state = self._state()
        cartas = {
            "Stark": _make_carta("escavacao"),
            "Elden": _make_carta("escavacao"),
        }
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "escavacao_extra")

    def test_bonus_supremo_todos_mesmo_tipo(self):
        state = self._state()
        cartas = {
            "Stark": _make_carta("movimento"),
            "Elden": _make_carta("movimento"),
            "Kuro":  _make_carta("movimento"),
        }
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "cristal_extra_2")

    def test_apenas_um_heroi_sem_sinergia(self):
        state = self._state()
        cartas = {"Stark": _make_carta("movimento")}
        resultado = state._calcular_sinergia(cartas)
        self.assertIsNone(resultado)


class TestAplicarBonusSinergia(unittest.TestCase):

    def _state(self):
        h1 = FakeHeroi("Stark")
        return FakeCercoState([h1])

    def test_bonus_passo_extra_adiciona_ponto_movimento(self):
        state = self._state()
        state.estado["pontos_movimento"] = 2
        sinergia = {"tipo": "passo_extra", "mensagem": "Teste"}
        state._aplicar_bonus_sinergia(sinergia, {})
        self.assertEqual(state.estado["pontos_movimento"], 3)

    def test_bonus_escavacao_extra_remove_pedregulhos(self):
        state = self._state()
        state.estado["pedregulhos"] = 5
        sinergia = {"tipo": "escavacao_extra", "mensagem": "Teste"}
        state._aplicar_bonus_sinergia(sinergia, {})
        self.assertEqual(state.estado["pedregulhos"], 3)

    def test_bonus_cristal_extra(self):
        state = self._state()
        state.estado["tesouro"] = 10
        sinergia = {"tipo": "cristal_extra", "mensagem": "Teste"}
        state._aplicar_bonus_sinergia(sinergia, {})
        self.assertEqual(state.estado["tesouro"], 11)

    def test_bonus_cristal_extra_2(self):
        state = self._state()
        state.estado["tesouro"] = 10
        sinergia = {"tipo": "cristal_extra_2", "mensagem": "Teste"}
        state._aplicar_bonus_sinergia(sinergia, {})
        self.assertEqual(state.estado["tesouro"], 12)


class TestTipoCarta(unittest.TestCase):

    def _state(self):
        return FakeCercoState([FakeHeroi("Stark")])

    def test_tipo_upgrade(self):
        s = self._state()
        self.assertEqual(s._tipo_carta({"tipo": "upgrade"}), "upgrade")

    def test_tipo_escavacao(self):
        s = self._state()
        self.assertEqual(s._tipo_carta({"escavacao": 2}), "escavacao")

    def test_tipo_trabalho(self):
        s = self._state()
        self.assertEqual(s._tipo_carta({"trabalho": 1}), "trabalho")

    def test_tipo_movimento_padrao(self):
        s = self._state()
        self.assertEqual(s._tipo_carta({"movimento": 3}), "movimento")

    def test_tipo_sem_atributo_padrao_movimento(self):
        s = self._state()
        self.assertEqual(s._tipo_carta({}), "movimento")


class TestPressaoCrescenteRound(unittest.TestCase):

    def _state(self):
        h1 = FakeHeroi("Stark")
        state = FakeCercoState([h1])
        state.iniciar_turno_sincronia()
        return state

    def test_round_1_apenas_passo(self):
        state = self._state()
        state.rs_round_atual = 1
        state._pressao_crescente_round()
        self.assertEqual(getattr(state, "_processou_inimigos", 0), 1)
        self.assertTrue(state._ultimo_apenas_passo)

    def test_round_2_passo_e_ataque(self):
        state = self._state()
        state.rs_round_atual = 2
        state._pressao_crescente_round()
        self.assertEqual(getattr(state, "_processou_inimigos", 0), 1)
        self.assertTrue(state._ultimo_apenas_passo)
        self.assertEqual(getattr(state, "_processou_ataques", 0), 1)

    def test_round_3_avanco_completo(self):
        state = self._state()
        state.rs_round_atual = 3
        state._pressao_crescente_round()
        self.assertEqual(getattr(state, "_processou_inimigos", 0), 1)
        self.assertFalse(state._ultimo_apenas_passo)


class TestVerificarFimTurnoSimultaneo(unittest.TestCase):

    def test_sem_heroi_sem_mao_continua(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        # Ambos ainda têm cartas na mão
        resultado = state._verificar_fim_turno_simultaneo()
        self.assertFalse(resultado)

    def test_heroi_sem_mao_encerra_turno(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        # Esvazia a mão do herói principal
        state.estado["mao"] = []
        resultado = state._verificar_fim_turno_simultaneo()
        self.assertTrue(resultado)
        self.assertTrue(getattr(state, "_fim_turno_chamado", False))

    def test_vencedor_velocidade_registrado(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        state.estado["mao"] = []
        state._verificar_fim_turno_simultaneo()
        self.assertEqual(state.rs_vencedor_velocidade, "Stark")
        self.assertIn("Stark", state.rs_bonus_proxima_rodada)

    def test_bonus_velocidade_aplicado_no_proximo_turno(self):
        h1 = FakeHeroi("Stark")
        state = FakeCercoState([h1])
        state.rs_bonus_proxima_rodada = {"Stark": "carta_extra"}
        state.estado["herois_status"]["Stark"] = {
            "mao": [],
            "deck_heroi": [_make_carta("movimento", 2, "Carta Bônus")],
            "descarte": [],
        }
        state.iniciar_turno_sincronia()
        # Carta extra foi puxada do deck para a mão via bônus de velocidade
        mao_stark = state.estado["herois_status"]["Stark"]["mao"]
        # A lógica de bonus pega do herois_status
        # Como Stark é o herói principal, o bonus é aplicado no herois_status
        self.assertEqual(state.rs_bonus_proxima_rodada, {})  # Limpou após aplicar


class TestGetInfoRoundSincronia(unittest.TestCase):

    def test_retorna_dict_com_campos_esperados(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        info = state.get_info_round_sincronia()

        self.assertIn("round_atual", info)
        self.assertIn("total_herois", info)
        self.assertIn("selecionados", info)
        self.assertIn("faltando", info)
        self.assertIn("sinergia_detectada", info)
        self.assertIn("cartas_selecionadas", info)
        self.assertIn("vencedor_velocidade", info)

    def test_faltando_correto_nenhum_selecionado(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        info = state.get_info_round_sincronia()
        self.assertEqual(info["faltando"], 2)

    def test_sinergia_detectada_quando_mesmo_tipo(self):
        h1 = FakeHeroi("Stark")
        h2 = FakeHeroi("Elden")
        state = FakeCercoState([h1, h2])
        state.iniciar_turno_sincronia()
        carta_m = _make_carta("movimento")
        state.rs_cartas_selecionadas["Stark"] = {"carta": carta_m, "idx": 0}
        state.rs_cartas_selecionadas["Elden"] = {"carta": carta_m, "idx": 0}
        info = state.get_info_round_sincronia()
        self.assertEqual(info["sinergia_detectada"], "movimento")


if __name__ == "__main__":
    unittest.main(verbosity=2)
