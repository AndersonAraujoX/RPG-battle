import unittest
import os
from src.map_builder import MapBuilder

class TestMapBuilder(unittest.TestCase):

    def setUp(self):
        """Configura um mapa fresco de 10x10 para cada teste."""
        self.builder = MapBuilder(width=10, height=10, default_terrain="Normal")
        self.test_json_path = "test_temp_map.json"

    def tearDown(self):
        """Remove arquivos temporários criados pelos testes."""
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)

    def test_initialization(self):
        self.assertEqual(self.builder.width, 10)
        self.assertEqual(self.builder.height, 10)
        self.assertEqual(self.builder.get_terrain(0, 0), "Normal")
        self.assertEqual(len(self.builder.objects), 0)

    def test_set_terrain(self):
        self.assertTrue(self.builder.set_terrain(5, 5, "Água"))
        self.assertEqual(self.builder.get_terrain(5, 5), "Água")
        self.assertFalse(self.builder.set_terrain(10, 10, "Água")) # Fora do grid
        self.assertFalse(self.builder.set_terrain(-1, 0, "Água"))

    def test_add_object_success(self):
        obj_id = self.builder.add_object("assets/tree.png", 2, 2, width=2, height=2, nome="Árvore Grande", bloqueia_movimento=True, cobertura=2)
        self.assertIsNotNone(obj_id)
        self.assertEqual(len(self.builder.objects), 1)

        obj = self.builder.objects[obj_id]
        self.assertEqual(obj.image_path, "assets/tree.png")
        self.assertEqual(obj.width, 2)
        self.assertEqual(obj.height, 2)
        self.assertTrue(obj.caracteristicas['bloqueia_movimento'])
        self.assertEqual(obj.caracteristicas['cobertura'], 2)
        self.assertEqual(obj.caracteristicas['nome'], "Árvore Grande")

    def test_add_object_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.builder.add_object("assets/rock.png", 9, 9, width=2, height=2)
            
        with self.assertRaises(ValueError):
             self.builder.add_object("assets/rock.png", -1, 0)

    def test_overlap_no_overwrite(self):
        obj_id_1 = self.builder.add_object("img.png", 0, 0, width=2, height=2)
        self.assertIsNotNone(obj_id_1)
        
        # Tentando colocar exatamente no mesmo lugar
        obj_id_2 = self.builder.add_object("img2.png", 0, 0, overwrite_overlap=False)
        self.assertIsNone(obj_id_2)
        
        # Tentando colidir parcialmente
        obj_id_3 = self.builder.add_object("img3.png", 1, 1, overwrite_overlap=False)
        self.assertIsNone(obj_id_3)

        self.assertEqual(len(self.builder.objects), 1)

    def test_overlap_with_overwrite(self):
        obj_id_1 = self.builder.add_object("img.png", 0, 0, width=2, height=2)
        self.assertIsNotNone(obj_id_1)
        
        # Colocando com overwrite por cima, deve apagar o anterior
        obj_id_2 = self.builder.add_object("img2.png", 1, 1, overwrite_overlap=True)
        self.assertIsNotNone(obj_id_2)

        self.assertEqual(len(self.builder.objects), 1)
        self.assertIn(obj_id_2, self.builder.objects)
        self.assertNotIn(obj_id_1, self.builder.objects)

    def test_get_objects_at(self):
        self.builder.add_object("img.png", x=5, y=5, width=2, height=2)
        
        objs = self.builder.get_objects_at(5, 5)
        self.assertEqual(len(objs), 1)
        
        objs = self.builder.get_objects_at(6, 6)
        self.assertEqual(len(objs), 1)
        
        objs = self.builder.get_objects_at(4, 5)
        self.assertEqual(len(objs), 0)

    def test_collides_with_blocking_object(self):
        self.builder.add_object("tenda.png", 2, 2, bloqueia_movimento=True)
        self.builder.add_object("grama.png", 4, 4, bloqueia_movimento=False)

        self.assertTrue(self.builder.collides_with_blocking_object(2, 2))
        self.assertFalse(self.builder.collides_with_blocking_object(4, 4))
        self.assertFalse(self.builder.collides_with_blocking_object(0, 0))

    def test_export_and_import_json(self):
        self.builder.set_terrain(3, 3, "Fogo")
        self.builder.add_object("rocha.png", 1, 1, bloqueia_movimento=True, hp=50)

        # Exporta
        success = self.builder.export_map(self.test_json_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.test_json_path))

        # Importa em uma nova instância
        new_builder = MapBuilder.import_map(self.test_json_path)

        # Verifica consistência do grid
        self.assertEqual(new_builder.width, 10)
        self.assertEqual(new_builder.height, 10)
        self.assertEqual(new_builder.get_terrain(3, 3), "Fogo")

        # Verifica consistência dos objetos
        self.assertEqual(len(new_builder.objects), 1)
        loaded_obj = list(new_builder.objects.values())[0]
        self.assertEqual(loaded_obj.image_path, "rocha.png")
        self.assertEqual(loaded_obj.x, 1)
        self.assertEqual(loaded_obj.y, 1)
        self.assertTrue(loaded_obj.caracteristicas['bloqueia_movimento'])
        self.assertEqual(loaded_obj.caracteristicas['hp'], 50)

if __name__ == '__main__':
    unittest.main()
