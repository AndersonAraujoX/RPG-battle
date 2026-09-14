"""
tests/test_coop_server.py — Suíte de Testes Unitários e de Integração do Servidor Co-op

Abrange os requisitos arquiteturais:
  1. Gerenciamento de Salas (RoomManager): ciclo de vida, limites de jogadores, descarte de heróis duplicados e cleanup.
  2. Autoridade do Servidor & Segurança: validação de limites de tabuleiro, colisão, pontos de ação e rejeição de ações espúrias.
  3. Mecânica de Sincronia & Sinergia: rodadas simultâneas, bônus de equipe, bônus supremo e avanço da IA inimiga.
  4. Protocolo WebSocket & REST: integração assíncrona ponta-a-ponta via TestClient.

Padrão: Arrange-Act-Assert (AAA).
"""
import unittest
from starlette.testclient import TestClient

from src.server.app import app, room_manager
from src.server.room_manager import Room, RoomManager
from src.server.session import CoopSession, CLASSES_HEROIS
from src.server.protocol import MessageType
from src.config import TERRENO_PAREDE, TERRENO_ROCHA, TERRENO_NORMAL


class TestRoomManagerUnit(unittest.TestCase):
    """Testes unitários para a classe Room e RoomManager."""

    def setUp(self):
        self.rm = RoomManager()

    def test_criar_sala_com_codigo_automatico(self):
        # Arrange
        # Act
        room = self.rm.create_room()

        # Assert
        self.assertIsNotNone(room)
        self.assertEqual(len(room.room_id), 6)
        self.assertIn(room.room_id, self.rm.rooms)
        self.assertEqual(room.session.fase, "LOBBY")

    def test_criar_sala_com_id_customizado(self):
        # Arrange
        custom_id = "SALA99"

        # Act
        room = self.rm.create_room(custom_room_id=custom_id)

        # Assert
        self.assertEqual(room.room_id, "SALA99")
        self.assertIs(self.rm.get_room("sala99"), room)

    def test_limite_maximo_quatro_jogadores(self):
        # Arrange
        room = self.rm.create_room("TEST4P")

        # Act
        p1 = room.session.add_player("p1", "Jogador 1")
        p2 = room.session.add_player("p2", "Jogador 2")
        p3 = room.session.add_player("p3", "Jogador 3")
        p4 = room.session.add_player("p4", "Jogador 4")
        p5 = room.session.add_player("p5", "Jogador 5")  # Excede o limite

        # Assert
        self.assertTrue(p1)
        self.assertTrue(p2)
        self.assertTrue(p3)
        self.assertTrue(p4)
        self.assertFalse(p5)
        self.assertEqual(len(room.session.jogadores), 4)

    def test_remocao_e_limpeza_de_salas_vazias(self):
        # Arrange
        room = self.rm.create_room("INATIVA")
        room.created_at -= 400  # Força idade maior que 300 segundos

        # Act
        self.rm.cleanup_empty_rooms(max_idle_seconds=300)

        # Assert
        self.assertIsNone(self.rm.get_room("INATIVA"))


class TestCoopSessionAuthority(unittest.TestCase):
    """Testes de autoridade de servidor, seleção de heróis e regras de combate."""

    def setUp(self):
        self.session = CoopSession("AUTH_ROOM")
        self.session.add_player("p1", "Alice")
        self.session.add_player("p2", "Bob")

    def test_selecao_heroi_caminho_feliz(self):
        # Arrange & Act
        ok1, _ = self.session.select_hero("p1", "Aquele")
        ok2, _ = self.session.select_hero("p2", "Stark")

        # Assert
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertEqual(self.session.jogadores["p1"]["hero_name"], "Aquele")
        self.assertEqual(self.session.jogadores["p2"]["hero_name"], "Stark")

    def test_prevencao_heroi_duplicado(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")

        # Act: p2 tenta escolher o mesmo herói
        ok, msg = self.session.select_hero("p2", "Aquele")

        # Assert
        self.assertFalse(ok)
        self.assertIn("já foi escolhido", msg)
        self.assertIsNone(self.session.jogadores["p2"]["hero_name"])

    def test_selecao_heroi_invalido_rejeitada(self):
        # Arrange & Act
        ok, msg = self.session.select_hero("p1", "HeroiInexistente")

        # Assert
        self.assertFalse(ok)
        self.assertIn("inválida", msg)

    def test_iniciar_jogo_requer_todos_herois_escolhidos(self):
        # Arrange: apenas p1 escolheu herói
        self.session.select_hero("p1", "Aquele")

        # Act
        ok, msg = self.session.start_game()

        # Assert
        self.assertFalse(ok)
        self.assertIn("Nem todos os jogadores", msg)
        self.assertEqual(self.session.fase, "LOBBY")

        # Act 2: p2 escolhe herói e inicia
        self.session.select_hero("p2", "Elden")
        ok_iniciar, _ = self.session.start_game()

        # Assert 2
        self.assertTrue(ok_iniciar)
        self.assertEqual(self.session.fase, "SELECAO_CARTAS")
        self.assertGreater(len(self.session.inimigos), 0)

    def test_movimento_bloqueado_na_fase_errada(self):
        # Arrange: jogo ainda em fase de SELECAO_CARTAS
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()

        # Act: tentar mover antes de resolver a seleção de cartas
        ok, msg = self.session.move_hero("p1", 9, 11)

        # Assert
        self.assertFalse(ok)
        self.assertIn("Ação Livre", msg)

    def test_movimento_valida_pontos_e_limites(self):
        # Arrange: iniciar partida e forçar fase de ACAO_LIVRE
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()
        self.session.fase = "ACAO_LIVRE"
        h = self.session.jogadores["p1"]["hero"]
        self.session.jogadores["p1"]["pontos_movimento"] = 1

        # Act 1: Movimento para fora do mapa
        ok_out, _ = self.session.move_hero("p1", -1, 5)

        # Act 2: Movimento além dos pontos disponíveis
        ok_longe, _ = self.session.move_hero("p1", h.pos_x + 5, h.pos_y)

        # Act 3: Movimento válido de 1 passo
        destino_x, destino_y = h.pos_x, h.pos_y - 1
        # Garante que destino está livre
        self.session.tabuleiro.grid[destino_y][destino_x] = None
        self.session.tabuleiro.terrain_grid[destino_y][destino_x] = TERRENO_NORMAL
        ok_valido, _ = self.session.move_hero("p1", destino_x, destino_y)

        # Assert
        self.assertFalse(ok_out)
        self.assertFalse(ok_longe)
        self.assertTrue(ok_valido)
        self.assertEqual(h.pos_x, destino_x)
        self.assertEqual(h.pos_y, destino_y)
        self.assertEqual(self.session.jogadores["p1"]["pontos_movimento"], 0)

    def test_jogador_nao_pode_mover_heroi_alheio(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()
        self.session.fase = "ACAO_LIVRE"

        # Act: comando com ID fantasma
        ok, msg = self.session.move_hero("jogador_hacker", 10, 10)

        # Assert
        self.assertFalse(ok)
        self.assertIn("não autorizado", msg)

    def test_ataque_validacao_alcance_e_dano(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")  # Melee (alcance 2)
        self.session.select_hero("p2", "Elden")   # Mago (alcance 8)
        self.session.start_game()
        self.session.fase = "ACAO_LIVRE"
        h1 = self.session.jogadores["p1"]["hero"]
        h2 = self.session.jogadores["p2"]["hero"]

        # Coloca um inimigo a 5 casas de distância
        ini = self.session.inimigos[0]
        ini.pos_x = h1.pos_x + 5
        ini.pos_y = h1.pos_y
        self.session.tabuleiro.grid[ini.pos_y][ini.pos_x] = ini

        # Act 1: Aquele (melee) tenta atacar a 5 casas (deve falhar)
        ok1, msg1 = self.session.attack_target("p1", ini.pos_x, ini.pos_y)

        # Act 2: Elden (mago, alcance 8) ataca a mesma distância
        h2.pos_x = h1.pos_x
        h2.pos_y = h1.pos_y
        ok2, msg2 = self.session.attack_target("p2", ini.pos_x, ini.pos_y)

        # Assert
        self.assertFalse(ok1)
        self.assertIn("fora de alcance", msg1)
        self.assertTrue(ok2)

    def test_mineracao_e_coleta_de_recursos(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()
        self.session.fase = "ACAO_LIVRE"
        h = self.session.jogadores["p1"]["hero"]
        self.session.jogadores["p1"]["pontos_escavacao"] = 2

        # Posiciona rocha adjacente (distância 1)
        rx, ry = h.pos_x + 1, h.pos_y
        self.session.tabuleiro.terrain_grid[ry][rx] = TERRENO_ROCHA
        recursos_antes = self.session.recursos["metal"]

        # Act
        ok, msg = self.session.mine_action("p1", rx, ry)

        # Assert
        self.assertTrue(ok)
        self.assertEqual(self.session.tabuleiro.terrain_grid[ry][rx], TERRENO_NORMAL)
        self.assertEqual(self.session.recursos["metal"], recursos_antes + 1)
        self.assertEqual(self.session.jogadores["p1"]["pontos_escavacao"], 1)

    def test_avanco_de_round_e_compra_de_cartas(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()
        self.session.fase = "ACAO_LIVRE"
        self.session.jogadores["p1"]["pontos_movimento"] = 5
        self.session.jogadores["p1"]["mao"].pop(0)  # Deixa com 3 cartas

        # Act
        ok, msg = self.session.end_player_turn("p1")

        # Assert
        self.assertTrue(ok)
        self.assertEqual(self.session.round_atual, 2)
        self.assertEqual(self.session.fase, "SELECAO_CARTAS")
        self.assertEqual(len(self.session.jogadores["p1"]["mao"]), 4)
        self.assertEqual(self.session.jogadores["p1"]["pontos_movimento"], 0)

    def test_reconexao_jogador_mantem_dados(self):
        # Arrange
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()
        self.session.remove_player("p1")
        self.assertFalse(self.session.jogadores["p1"]["connected"])

        # Act: Reconecta
        ok = self.session.add_player("p1", "Alice Reborn")

        # Assert
        self.assertTrue(ok)
        self.assertTrue(self.session.jogadores["p1"]["connected"])
        self.assertEqual(self.session.jogadores["p1"]["hero_name"], "Aquele")



class TestSimultaneousRoundsAndSynergy(unittest.TestCase):
    """Testes para o cálculo de sinergia e rodadas simultâneas."""

    def setUp(self):
        self.session = CoopSession("SYNC_ROOM")
        self.session.add_player("p1", "Alice")
        self.session.add_player("p2", "Bob")
        self.session.select_hero("p1", "Aquele")
        self.session.select_hero("p2", "Stark")
        self.session.start_game()

    def test_selecao_secreta_e_privacidade_da_mao(self):
        # Arrange & Act
        ok, _ = self.session.select_card("p1", 0)

        # Assert
        self.assertTrue(ok)
        self.assertIsNotNone(self.session.cartas_selecionadas["p1"])

        # Verifica privacidade no payload JSON para p2
        state_para_p2 = self.session.to_dict(for_player_id="p2")
        p1_data = next(h for h in state_para_p2["heroes"] if h["player_id"] == "p1")
        p2_data = next(h for h in state_para_p2["heroes"] if h["player_id"] == "p2")

        self.assertEqual(len(p1_data["hand"]), 0)  # P2 não vê as cartas de P1!
        self.assertGreater(len(p2_data["hand"]), 0)  # P2 vê suas próprias cartas
        self.assertTrue(p1_data["card_locked"])

    def test_sinergia_calculada_corretamente(self):
        # Arrange
        carta_mov1 = {"id": "c1", "movimento": 10, "trabalho": 0, "escavacao": 0}
        carta_mov2 = {"id": "c2", "movimento": 15, "trabalho": 0, "escavacao": 0}
        cartas = {"p1": carta_mov1, "p2": carta_mov2}

        # Act
        sinergia = self.session._calcular_sinergia(cartas)

        # Assert
        self.assertIsNotNone(sinergia)
        self.assertEqual(sinergia["tipo"], "supremo")
        self.assertEqual(sinergia["categoria"], "movimento")

    def test_resolucao_automatica_quando_todos_selecionam(self):
        # Arrange: ambos selecionam suas cartas
        # Act
        self.session.select_card("p1", 0)
        self.session.select_card("p2", 0)

        # Assert: fase muda para ACAO_LIVRE automaticamente
        self.assertEqual(self.session.fase, "ACAO_LIVRE")
        self.assertGreater(self.session.jogadores["p1"]["pontos_movimento"], 0)
        self.assertGreater(self.session.jogadores["p2"]["pontos_movimento"], 0)


class TestCoopIntegrationFastAPI(unittest.TestCase):
    """Testes de integração REST e WebSocket usando TestClient."""

    def setUp(self):
        self.client = TestClient(app)

    def test_rest_health_and_heroes(self):
        # Arrange & Act
        res_health = self.client.get("/api/health")
        res_heroes = self.client.get("/api/heroes")

        # Assert
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")
        self.assertEqual(res_heroes.status_code, 200)
        heroes = res_heroes.json()
        self.assertGreaterEqual(len(heroes), 7)
        nomes = [h["nome"] for h in heroes]
        self.assertIn("Aquele", nomes)
        self.assertIn("Stark", nomes)

    def test_rest_create_and_list_rooms(self):
        # Arrange & Act
        res_create = self.client.post("/api/rooms?room_id=INTEG1")
        res_list = self.client.get("/api/rooms")

        # Assert
        self.assertEqual(res_create.status_code, 200)
        self.assertEqual(res_create.json()["room_id"], "INTEG1")
        self.assertEqual(res_list.status_code, 200)
        rooms = res_list.json()
        ids = [r["room_id"] for r in rooms]
        self.assertIn("INTEG1", ids)

    def test_websocket_coop_flow(self):
        # Arrange: Conectar dois jogadores via WebSocket
        with self.client.websocket_connect("/ws/WSROOM/p1?player_name=GuerreiroAlice") as ws1:
            # Recebe o state update inicial do p1
            data1 = ws1.receive_json()
            self.assertEqual(data1["type"], MessageType.STATE_UPDATE.value)
            self.assertEqual(data1["payload"]["room_id"], "WSROOM")

            with self.client.websocket_connect("/ws/WSROOM/p2?player_name=PaladinoBob") as ws2:
                # Ambos recebem o update com 2 jogadores
                ws1.receive_json()
                data2 = ws2.receive_json()
                self.assertEqual(len(data2["payload"]["heroes"]), 2)
                self.assertIsNone(data2["payload"]["heroes"][0]["hero_name"])
                self.assertIsNone(data2["payload"]["heroes"][1]["hero_name"])

                # Act 1: Alice escolhe Aquele
                ws1.send_json({"type": MessageType.SELECT_HERO.value, "payload": {"hero_name": "Aquele"}})
                upd1 = ws1.receive_json()
                ws2.receive_json()
                self.assertEqual(upd1["payload"]["heroes"][0]["hero_name"], "Aquele")

                # Act 2: Bob tenta escolher Aquele (deve ser rejeitado)
                ws2.send_json({"type": MessageType.SELECT_HERO.value, "payload": {"hero_name": "Aquele"}})
                rej = ws2.receive_json()
                self.assertEqual(rej["type"], MessageType.ACTION_REJECTED.value)

                # Act 3: Bob escolhe Stark (sucesso)
                ws2.send_json({"type": MessageType.SELECT_HERO.value, "payload": {"hero_name": "Stark"}})
                ws1.receive_json()
                upd2 = ws2.receive_json()
                nomes_herois = [h["hero_name"] for h in upd2["payload"]["heroes"]]
                self.assertIn("Aquele", nomes_herois)
                self.assertIn("Stark", nomes_herois)

                # Act 4: Iniciar Partida
                ws1.send_json({"type": MessageType.START_GAME.value, "payload": {}})
                game_upd1 = ws1.receive_json()
                ws2.receive_json()
                self.assertEqual(game_upd1["payload"]["fase"], "SELECAO_CARTAS")

                # Act 5: Ambos selecionam carta
                ws1.send_json({"type": MessageType.SELECT_CARD.value, "payload": {"card_idx": 0}})
                ws1.receive_json()
                ws2.receive_json()

                ws2.send_json({"type": MessageType.SELECT_CARD.value, "payload": {"card_idx": 0}})
                res_round1 = ws1.receive_json()
                ws2.receive_json()
                # Round resolvido!
                self.assertEqual(res_round1["payload"]["fase"], "ACAO_LIVRE")





if __name__ == "__main__":
    unittest.main()
