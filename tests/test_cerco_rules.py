import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.resolvedor_acoes import validar_trabalhar, validar_escavar
from src.juiz_combate import resolver_melee, validar_pode_atacar_distancia, resolver_distancia

class TestCercoRules(unittest.TestCase):
    def test_bloqueio_de_oficina(self):
        # 1. Bloqueio de Oficina: Regra que impede a ação de Trabalhar Recursos se houver qualquer Orc presente na oficina correspondente.
        estado = {
            "heroi_x": 6, "heroi_y": 14,  # Carpintaria
            "invasores": {
                "carpintaria": 1,
                "curtume": 0,
                "fundicao": 0
            },
            "pontos_trabalho": 3
        }
        ok, recurso, msg = validar_trabalhar(estado, 3)
        self.assertFalse(ok)
        self.assertIn("Orcs", msg)

        # Sem orcs na oficina correspondente (por exemplo, na fundição)
        estado["heroi_x"] = 5
        estado["heroi_y"] = 10  # Fundição
        ok, recurso, msg = validar_trabalhar(estado, 3)
        self.assertTrue(ok)

    def test_combate_corpo_a_corpo_mesmo_espaco(self):
        # 2. Combate Corpo a Corpo: Resolução baseada no mesmo espaço do inimigo.
        estado = {
            "pos_heroi": "carpintaria",
            "invasores": {"carpintaria": 1, "curtume": 1}
        }
        
        # Ataca a carpintaria (mesma zona)
        res = resolver_melee(estado, "carpintaria", num_dados=2)
        self.assertNotIn("INVALIDO", res["logs"][0][1] if res["logs"] else "")

        # Ataca o curtume (zona diferente)
        res = resolver_melee(estado, "curtume", num_dados=2)
        self.assertIn("INVALIDO", res["logs"][0][1])

    def test_ataque_a_distancia_torres_adjacentes(self):
        # 3. Ataque a Distância (Torres): Restrição de alvejar apenas muralhas adjacentes, espaços externos ou máquinas de cerco a partir das Torres, contando apenas símbolos de Balestra.
        
        # NW targets muralha_norte (adjacent) -> OK
        ok, msg = validar_pode_atacar_distancia("torre_nw", "muralha_norte")
        self.assertTrue(ok)
        
        # NW targets muralha_oeste (adjacent) -> OK
        ok, msg = validar_pode_atacar_distancia("torre_nw", "muralha_oeste")
        self.assertTrue(ok)
        
        # NW targets muralha_sul (non-adjacent) -> False
        ok, msg = validar_pode_atacar_distancia("torre_nw", "muralha_sul")
        self.assertFalse(ok)
        
        # NW targets campo_norte (external space) -> OK
        ok, msg = validar_pode_atacar_distancia("torre_nw", "campo_norte")
        self.assertTrue(ok)
        
        # NW targets catapulta_cerco (siege weapon) -> OK
        ok, msg = validar_pode_atacar_distancia("torre_nw", "catapulta_cerco")
        self.assertTrue(ok)
        
        # NW targets camara_central (internal space) -> False
        ok, msg = validar_pode_atacar_distancia("torre_nw", "camara_central")
        self.assertFalse(ok)

    def test_bloqueio_de_escavacao(self):
        # 4. Bloqueio de Escavação: Regra que proíbe a remoção de pedregulhos se houver Goblins ou Trolls presentes no Pátio de Entrada do Túnel.
        estado = {
            "heroi_x": 13, "heroi_y": 10,  # Pátio
            "brutamontes": 0,
            "infiltradores": 1,
            "pedregulhos": 5,
            "pontos_escavacao": 2
        }
        ok, qty, msg = validar_escavar(estado, 2)
        self.assertFalse(ok)
        self.assertTrue("Bloqueado!" in msg or "Formigas" in msg or "Goblins" in msg)

        # Sem brutamontes e infiltradores -> OK
        estado["infiltradores"] = 0
        ok, qty, msg = validar_escavar(estado, 2)
        self.assertTrue(ok)

if __name__ == '__main__':
    unittest.main()
