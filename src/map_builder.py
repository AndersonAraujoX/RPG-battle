import json

class MapObject:
    """Representa um objeto customizado (imagem/prop) colocado no mapa."""
    def __init__(self, id, image_path, x, y, width=1, height=1, **caracteristicas):
        self.id = id
        self.image_path = image_path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Atributos padrão e os extras fornecidos
        self.caracteristicas = {
            'nome': caracteristicas.get('nome', 'Objeto Customizado'),
            'bloqueia_movimento': caracteristicas.get('bloqueia_movimento', False),
            'cobertura': caracteristicas.get('cobertura', 0), # 0 (nenhuma), 1 (meia), 2 (total)
            'interagivel': caracteristicas.get('interagivel', False),
            'hp': caracteristicas.get('hp', None) # None = indestrutível
        }
        # Adiciona outras características enviadas
        for k, v in caracteristicas.items():
            if k not in self.caracteristicas:
                self.caracteristicas[k] = v

    def overlaps_with(self, x, y):
        """Verifica se uma coordenada x, y está dentro dos limites deste objeto."""
        return (self.x <= x < self.x + self.width) and (self.y <= y < self.y + self.height)
        
    def overlaps_with_rect(self, other_x, other_y, other_width, other_height):
        """Verifica se o bounding box deste objeto colide com outro."""
        return not (self.x >= other_x + other_width or 
                    self.x + self.width <= other_x or 
                    self.y >= other_y + other_height or 
                    self.y + self.height <= other_y)
                    
    def to_dict(self):
        return {
            'id': self.id,
            'image_path': self.image_path,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'caracteristicas': self.caracteristicas
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            image_path=data['image_path'],
            x=data['x'],
            y=data['y'],
            width=data.get('width', 1),
            height=data.get('height', 1),
            **data.get('caracteristicas', {})
        )


class MapBuilder:
    """Gerencia a criação do grid de terrenos e posicionamento de MapObjects sobre ele."""
    def __init__(self, width=20, height=20, default_terrain="Normal"):
        self.width = width
        self.height = height
        self.default_terrain = default_terrain
        self.grid = [[self.default_terrain for _ in range(width)] for _ in range(height)]
        self.objects = {} # id -> MapObject
        self._next_id = 1

    def set_terrain(self, x, y, terrain_type):
        """Altera o terreno de uma célula específica se estiver dentro dos limites."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = terrain_type
            return True
        return False

    def get_terrain(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def add_object(self, image_path, x, y, width=1, height=1, overwrite_overlap=False, **caracteristicas):
        """
        Adiciona um objeto ao mapa.
        Se overwrite_overlap = False, não permite adicionar se colidir com outro existente.
        Retorna o ID do objeto se sucesso, ou None se falhar/colidir.
        """
        # Verifica se está dentro dos limites do tabuleiro
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            raise ValueError(f"Objeto excede os limites do mapa ({self.width}x{self.height}).")

        # Verificar colisões se necessário
        if not overwrite_overlap:
            for obj in self.objects.values():
                if obj.overlaps_with_rect(x, y, width, height):
                    return None

        # Remover colididos se sobrescrever
        if overwrite_overlap:
            to_remove = []
            for obj_id, obj in self.objects.items():
                 if obj.overlaps_with_rect(x, y, width, height):
                     to_remove.append(obj_id)
            for rid in to_remove:
                del self.objects[rid]

        obj_id = f"obj_{self._next_id}"
        self._next_id += 1
        
        new_obj = MapObject(obj_id, image_path, x, y, width, height, **caracteristicas)
        self.objects[obj_id] = new_obj
        return obj_id

    def remove_object(self, obj_id):
        """Remove o objeto pelo ID."""
        if obj_id in self.objects:
            del self.objects[obj_id]
            return True
        return False

    def get_objects_at(self, x, y):
        """Retorna uma lista de objetos presentes na coordenada x,y."""
        found = []
        for obj in self.objects.values():
            if obj.overlaps_with(x, y):
                found.append(obj)
        return found
        
    def collides_with_blocking_object(self, x, y):
        """Verifica se há algum objeto bloqueador de movimento em uma coordenada específica."""
        objs = self.get_objects_at(x, y)
        for obj in objs:
            if obj.caracteristicas.get('bloqueia_movimento', False):
                return True
        return False

    def export_map(self, filepath):
        """Exporta a configuração do grid e dos objetos para um arquivo JSON."""
        data = {
            'width': self.width,
            'height': self.height,
            'grid': self.grid,
            'objects': [obj.to_dict() for obj in self.objects.values()],
            'next_id': self._next_id
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True

    @classmethod
    def import_map(cls, filepath):
        """Instancia um MapBuilder a partir de um arquivo JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        builder = cls(width=data['width'], height=data['height'])
        builder.grid = data['grid']
        builder._next_id = data.get('next_id', 1)
        
        for obj_data in data.get('objects', []):
            obj = MapObject.from_dict(obj_data)
            builder.objects[obj.id] = obj
            
        return builder
