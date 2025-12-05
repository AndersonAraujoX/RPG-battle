import random
from src.config import TIME_A, TIME_B, TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE, TERRENO_GELO

class Tabuleiro:
    def __init__(self, largura=20, altura=20):
        self.largura = largura
        self.altura = altura
        self.grid = [[None for _ in range(largura)] for _ in range(altura)]
        self.terrain_grid = [[TERRENO_NORMAL for _ in range(largura)] for _ in range(altura)]
        self.elevation_grid = [[0 for _ in range(largura)] for _ in range(altura)]
        self.itens_no_chao = [[None for _ in range(largura)] for _ in range(altura)]

    def get_item_em(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.itens_no_chao[y][x]
        return None

    def gerar_terreno_aleatorio(self, chance_parede=0.05, chance_floresta=0.1, chance_dificil=0.1):
        """Gera terreno aleatório no tabuleiro, evitando as áreas de spawn."""
        for y in range(4, self.altura - 4):
            for x in range(self.largura):
                if random.random() < chance_parede:
                    self.terrain_grid[y][x] = TERRENO_PAREDE
                elif random.random() < chance_floresta:
                    self.terrain_grid[y][x] = TERRENO_FLORESTA
                elif random.random() < chance_dificil:
                    self.terrain_grid[y][x] = TERRENO_DIFICIL
                
                self.elevation_grid[y][x] = random.randint(0, 2)

    def adicionar_limitadores(self):
        """Adiciona paredes nas bordas do mapa para limitar a área de combate."""
        for x in range(self.largura):
            self.terrain_grid[0][x] = TERRENO_PAREDE
            self.terrain_grid[self.altura - 1][x] = TERRENO_PAREDE
            self.grid[0][x] = None # Remove anyone unlucky enough to be there (though spawn logic should prevent this)
            self.grid[self.altura - 1][x] = None

        for y in range(self.altura):
            self.terrain_grid[y][0] = TERRENO_PAREDE
            self.terrain_grid[y][self.largura - 1] = TERRENO_PAREDE
            self.grid[y][0] = None
            self.grid[y][self.largura - 1] = None

    def get_terrain_em(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.terrain_grid[y][x]
        return None

    def get_elevation_em(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.elevation_grid[y][x]
        return 0


    def adicionar_personagem(self, personagem, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura and self.grid[y][x] is None and self.terrain_grid[y][x] != TERRENO_PAREDE:
            self.grid[y][x] = personagem
            personagem.pos_x = x
            personagem.pos_y = y
            return True
        return False

    def mover_personagem(self, personagem, novo_x, novo_y):
        if self.grid[personagem.pos_y][personagem.pos_x] == personagem:
            self.grid[personagem.pos_y][personagem.pos_x] = None
        self.grid[novo_y][novo_x] = personagem
        personagem.pos_x, personagem.pos_y = novo_x, novo_y

    def adicionar_personagem_na_borda(self, personagem, borda):
        """Adiciona um personagem em uma borda vazia (norte ou sul), espalhando-os."""
        rows = range(0, 4) if borda == 'norte' else range(self.altura - 4, self.altura)
        
        # Tenta espalhar mais, usando colunas alternadas ou aleatórias
        # Começa do centro, mas com espaçamento
        x_inicial = self.largura // 2
        
        # Gera uma lista de posições possíveis nessas linhas
        posicoes_possiveis = []
        for y in rows:
            for x in range(self.largura):
                # Prioriza posições centrais mas com algum espaçamento
                dist_centro = abs(x - x_inicial)
                # Adiciona um peso para ordenar: menor peso = tenta primeiro
                # Peso = distancia do centro + (distancia da borda * 2)
                dist_borda_y = y if borda == 'norte' else (self.altura - 1 - y)
                peso = dist_centro + (dist_borda_y * 5) 
                
                # Verifica se é válido antes de adicionar
                if self.grid[y][x] is None and self.terrain_grid[y][x] != TERRENO_PAREDE:
                    posicoes_possiveis.append((peso, x, y))
        
        # Ordena por peso e tenta colocar
        posicoes_possiveis.sort(key=lambda item: item[0])
        
        for _, x, y in posicoes_possiveis:
             # Verificação extra de espaçamento: tenta não colocar adjacente a outro personagem se possível
            tem_vizinho = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.largura and 0 <= ny < self.altura and self.grid[ny][nx] is not None:
                        tem_vizinho = True
                        break
                if tem_vizinho: break
            
            # Se tiver vizinho, pula essa posição na primeira tentativa (para tentar espaçar)
            # Mas se não tiver opção, vai ter que ser
            if not tem_vizinho:
                if self.adicionar_personagem(personagem, x, y):
                    return True

        # Se não conseguiu com espaçamento, tenta qualquer um livre na ordem
        for _, x, y in posicoes_possiveis:
            if self.adicionar_personagem(personagem, x, y):
                return True
                
        return False

    def get_personagem_em(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.grid[y][x]
        return None

    def get_personagens_em_area(self, x, y, raio):
        personagens_na_area = []
        for r in range(y - raio, y + raio + 1):
            for c in range(x - raio, x + raio + 1):
                if 0 <= c < self.largura and 0 <= r < self.altura:
                    personagem = self.grid[r][c]
                    if personagem:
                        personagens_na_area.append(personagem)
        return personagens_na_area

    def calcular_linha_visao(self, x1, y1, x2, y2, ignorar_personagens=False):
        """
        Verifica se há linha de visão clara entre dois pontos (x1, y1) e (x2, y2).
        Utiliza um algoritmo simplificado de linha para verificar obstáculos.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            # Não verifica o ponto inicial para obstaculos, apenas os pontos entre inicio e fim, e o ponto final
            if (x1 != x2 or y1 != y2) and self.terrain_grid[y1][x1] == TERRENO_PAREDE:
                return False
            
            # Opcionalmente, verifica se há outro personagem bloqueando a visão
            if not ignorar_personagens and self.grid[y1][x1] is not None and \
               not (x1 == x2 and y1 == y2): # Don't block self or target
                return False

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        return True

    def desenhar_tabuleiro(self, combatentes):
        simbolos = {
            ("Guerreiro", TIME_A): "GA", ("Mago", TIME_A): "MA", ("Ladino", TIME_A): "LA",
            ("Arqueiro", TIME_A): "AA", ("Barbaro", TIME_A): "BA", ("Clerigo", TIME_A): "CA",
            ("Guerreiro", TIME_B): "GB", ("Mago", TIME_B): "MB", ("Ladino", TIME_B): "LB",
            ("Arqueiro", TIME_B): "AB", ("Barbaro", TIME_B): "BB", ("Clerigo", TIME_B): "CB",
        }
        simbolos_terreno = {
            TERRENO_NORMAL: " . ",
            TERRENO_FLORESTA: " # ",
            TERRENO_DIFICIL: " ~ ",
            TERRENO_PAREDE: "███",
        }

        print("\n" + "="* (self.largura * 3 + 3))
        for y in range(self.altura):
            linha = ""
            for x in range(self.largura):
                personagem = self.grid[y][x]
                if personagem and personagem.esta_vivo:
                    simbolo = simbolos.get((personagem.__class__.__name__, personagem.time), "??")
                    linha += f" {simbolo}"
                else:
                    linha += simbolos_terreno.get(self.terrain_grid[y][x], " ? ")
            print(linha)
        print("="* (self.largura * 3 + 3))
        
        print("HP dos Times:")
        time_a = sorted([p for p in combatentes if p.time == 'A' and p.esta_vivo], key=lambda p: p.nome)
        time_b = sorted([p for p in combatentes if p.time == 'B' and p.esta_vivo], key=lambda p: p.nome)
        max_len = max(len(time_a), len(time_b))
        
        print(f"{'Time A':<25} | {'Time B':<25}")
        print("-" * 53)
        for i in range(max_len):
            str_a = f"- {time_a[i].nome}: {time_a[i].hp_atual}/{time_a[i].hp_max} HP" if i < len(time_a) else ""
            str_b = f"- {time_b[i].nome}: {time_b[i].hp_atual}/{time_b[i].hp_max} HP" if i < len(time_b) else ""
            print(f"{str_a:<25} | {str_b:<25}")
        print("="* (self.largura * 3 + 3) + "\n")
