import random
from src.config import TIME_A, TIME_B, TERRENO_NORMAL, TERRENO_FLORESTA, TERRENO_DIFICIL, TERRENO_PAREDE

class Tabuleiro:
    def __init__(self, largura=20, altura=20):
        self.largura = largura
        self.altura = altura
        self.grid = [[None for _ in range(largura)] for _ in range(altura)]
        self.terrain_grid = [[TERRENO_NORMAL for _ in range(largura)] for _ in range(altura)]

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

    def get_terrain_em(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.terrain_grid[y][x]
        return None

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
        """Adiciona um personagem em uma borda vazia (norte ou sul)."""
        y = 1 if borda == 'norte' else self.altura - 2
        
        x_inicial = self.largura // 2
        for offset in range(self.largura // 2):
            for x_op in [x_inicial + offset, x_inicial - offset]:
                if 0 <= x_op < self.largura:
                    if self.adicionar_personagem(personagem, x_op, y):
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
