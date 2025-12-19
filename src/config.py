import pygame

# --- Constantes de Tela e Tabuleiro ---
LARGURA_TELA = 1024
ALTURA_BARRA_INICIATIVA = 80
ALTURA_TELA = 768 + ALTURA_BARRA_INICIATIVA
TAMANHO_CELULA = 30
LARGURA_TABULEIRO = 20 * TAMANHO_CELULA
ALTURA_TABULEIRO = 20 * TAMANHO_CELULA
LARGURA_LOG = LARGURA_TELA - LARGURA_TABULEIRO

# --- Cores ---
COR_FUNDO = (20, 20, 20)
COR_LINHA = (40, 40, 40)
COR_TEXTO = (220, 220, 220)
COR_BOTAO = (80, 80, 80)
COR_BOTAO_HOVER = (180, 180, 180)
COR_BOTAO_DESABILITADO = (100, 100, 100)
COR_GRID = (50, 50, 50)
CORES_TIME = {"A": (60, 120, 220), "B": (220, 60, 60)}
COR_HP_BAR_FUNDO = (50, 50, 50)
COR_HP_BAR_FRENTE = (60, 200, 60)
COR_CURA = (60, 220, 60)
COR_DANO = (255, 100, 100)
COR_CRITICO = (255, 255, 100)
COR_STATUS = (150, 150, 255)
COR_XP = (200, 200, 200)
COR_LEVEL_UP = (255, 215, 0)
COR_MANA_BAR = (60, 100, 220)
COR_ENERGIA_BAR = (220, 200, 60)
COR_ACCENT = (138, 43, 226) # Roxo
COR_FUNDO_MENU = (10, 10, 15)
COR_BOTAO_MENU = (40, 30, 50)
COR_BOTAO_MENU_HOVER = (60, 50, 80)

# Directions
DIRECAO_CIMA = (0, -1)
DIRECAO_BAIXO = (0, 1)
DIRECAO_ESQUERDA = (-1, 0)
DIRECAO_DIREITA = (1, 0)

# Damage Types (D&D 5e)
DANO_CORTANTE = "cortante"
DANO_PERFURANTE = "perfurante"
DANO_CONTUNDENTE = "contundente"
DANO_FOGO = "fogo"
DANO_GELO = "gelo"
DANO_ELETRICO = "eletrico"
DANO_ACIDO = "acido"
DANO_VENENO = "veneno"
DANO_NECROTICO = "necrotico"
DANO_RADIANTE = "radiante"
DANO_PSIQUICO = "psiquico"
DANO_FORCA = "forca"
DANO_TROVAO = "trovao"
DANO_FISICO = "fisico" # Fallback/Generic

# Colors associated with damage types (Optional for UI)
COR_DANO_FOGO = (255, 69, 0)
COR_DANO_GELO = (0, 191, 255)
COR_DANO_VENENO = (50, 205, 50)

# --- Constantes de Terreno (importadas para uso nas cores) ---
TERRENO_NORMAL = "NORMAL"
TERRENO_FLORESTA = "FLORESTA"
TERRENO_DIFICIL = "DIFICIL"
TERRENO_PAREDE = "PAREDE"
TERRENO_GELO = "GELO"
TERRENO_FOGO = "FOGO"
TERRENO_AGUA = "AGUA"
TERRENO_ROCHA = "ROCHA"
TERRENO_BARRIL = "BARRIL"

CORES_TERRENO = {
    TERRENO_NORMAL: (30, 30, 30),
    TERRENO_PAREDE: (100, 100, 100),
    TERRENO_FLORESTA: (20, 80, 20),
    TERRENO_DIFICIL: (110, 90, 70),
    TERRENO_GELO: (180, 200, 255),
    TERRENO_FOGO: (255, 100, 0),
    TERRENO_AGUA: (0, 100, 255),
    TERRENO_ROCHA: (100, 100, 100),
    TERRENO_BARRIL: (139, 69, 19),
}

# --- Constantes de Estado de Jogo ---
ESTADO_JOGO_MENU_PRINCIPAL = 0
ESTADO_JOGO_SETUP = 1
ESTADO_JOGO_FIM = 3
ESTADO_JOGO_COMBATE = 4
ESTADO_JOGO_EDITOR = 5
ESTADO_JOGO_CUTSCENE = 6
ESTADO_JOGO_MAPA_MUNDO = 8
ESTADO_JOGO_NARRATIVA = 9

# --- Cores do Novo Menu ---
COR_FUNDO_MENU = (5, 5, 5) # Quase preto
COR_ACCENT = (106, 13, 173) # Roxo
COR_BOTAO_MENU = (30, 10, 40) # Roxo escuro
COR_BOTAO_MENU_HOVER = (50, 20, 60)
COR_SUBTITULO = (150, 100, 200)

# --- Constantes de Estado de Combate ---
ESTADO_COMBATE_VEZ_IA = "VEZ_IA"
ESTADO_COMBATE_AGUARDANDO_JOGADOR = "AGUARDANDO_JOGADOR"
ESTADO_COMBATE_JOGADOR_SELECIONOU = "JOGADOR_SELECIONOU"

# --- Constantes de Modo de Painel ---
PAINEL_MODO_LOG = "LOG"
PAINEL_MODO_INFO = "INFO"
PAINEL_MODO_INVENTARIO = "INVENTARIO"

# --- Constantes de Time ---
TIME_A = "A"
TIME_B = "B"

# --- Constantes de Efeitos de Status ---
STATUS_ENVENENADO = "Envenenado"
STATUS_ATURDIDO = "Atordoado"
STATUS_SANGRANDO = "Sangrando"
STATUS_FURIA = "Fúria"
STATUS_AMALDICOADO = "Amaldiçoado"

PROPRIEDADES_STATUS_EFEITO = {
    STATUS_ENVENENADO: {
        "cor": (100, 200, 100),
        "icone": "P", # Placeholder for a visual icon
        "descricao": "Recebe dano de veneno a cada turno.",
        "efeito_por_turno": {"dano_fixo": 2}
    },
    STATUS_ATURDIDO: {
        "cor": (200, 200, 50),
        "icone": "S",
        "descricao": "Não pode realizar ações.",
        "pode_agir": False
    },
    STATUS_SANGRANDO: {
        "cor": (200, 50, 50),
        "icone": "B",
        "descricao": "Recebe dano de sangramento a cada turno.",
        "efeito_por_turno": {"dano_percentual_hp_max": 0.05}
    },
    STATUS_FURIA: {
        "cor": (200, 100, 50),
        "icone": "F",
        "descricao": "Aumenta o dano causado e a resistência a dano, mas pode não conseguir fugir.",
        "bonus_dano_ataque": 2,
        "resistencia_dano_percentual": 0.25,
        "pode_fugir": False
    },
    STATUS_AMALDICOADO: {
        "cor": (100, 0, 100),
        "icone": "C",
        "descricao": "Recebe dano de maldição a cada turno e tem seu ataque reduzido.",
        "efeito_por_turno": {"dano_fixo": 3},
        "bonus_ataque_fixo": -2,
    },
    "Provocado": {
        "cor": (255, 120, 0),
        "icone": "!",
        "descricao": "Forçado a atacar quem provocou.",
        # Mechanic handled in logic
    },
    "Defesa Quebrada": {
        "cor": (150, 150, 150),
        "icone": "D-",
        "descricao": "Classe de Armadura reduzida.",
        "bonus_ac_fixo": -3
    },
    "Ataque Reduzido": {
         "cor": (100, 100, 200),
         "icone": "A-",
         "descricao": "Dano de ataque reduzido.",
         "bonus_dano_ataque": -2
    },
    "Comando Tatico": {
        "cor": (255, 215, 0),
        "icone": "A+",
        "descricao": "Ataque aumentado por comando tático.",
        "bonus_dano_ataque": 2
    }
}


# --- Constantes do Novo Layout (Retro UI) ---
# Dimensões da Tela: 1024 x 768 (Fixa)
LARGURA_TELA = 1024
ALTURA_TELA = 768 # Sem barra extra, tudo contido
ALTURA_BARRA_INICIATIVA = 0 # Integrada ou removida por enquanto? Vamos manter 0 e redesenhar se precisar.
# Layout: Coluna Esquerda (Jogo + Ações), Coluna Direita (Info + Log)

# Esquerda (Total 600px largura)
RECT_TABULEIRO = pygame.Rect(0, 0, 600, 600) # 20x30 = 600
RECT_BARRA_ACOES = pygame.Rect(0, 600, 600, 168) # 768 - 600 = 168

# Direita (Total 424px largura -> 1024 - 600)
X_DIREITA = 600
LARGURA_DIREITA = 424
RECT_PAINEL_INFO = pygame.Rect(X_DIREITA, 0, LARGURA_DIREITA, 120)       # Cabecalho / Info Unidade
RECT_LOG = pygame.Rect(X_DIREITA, 120, LARGURA_DIREITA, 300)             # Log de Combate
RECT_INVENTARIO = pygame.Rect(X_DIREITA, 420, LARGURA_DIREITA, 150)      # Inventario
RECT_TUTORIAL = pygame.Rect(X_DIREITA, 570, LARGURA_DIREITA, 198)        # Tutorial / Extra

# Cores Retro
COR_BORDA_DOURADA = (184, 134, 11)   # DarkGoldenrod
COR_FUNDO_PEDRA = (45, 40, 35)       # Dark Stone/Wood
COR_FUNDO_RETRO = (30, 25, 20)       # Darker background for panels
COR_TEXTO_RETRO = (240, 230, 200)    # Cream
COR_TITULO_RETRO = (255, 215, 0)     # Gold

# --- Imagens (Placeholders) ---
image_path_heroes = "assets/images/characters/heroes/"
image_path_monsters = "assets/images/characters/monsters/"
image_path_bosses = "assets/images/characters/bosses/"
image_path_env = "assets/images/environment/"
image_path_ui = "assets/images/ui/"

IMAGE_PERSONAGENS = {
    # Protagonists (Specific)
    "Novak": image_path_heroes + "Novak.png",
    "Koema": image_path_heroes + "Koema.png",
    "Rilem": image_path_heroes + "Rilem.png",
    "Yukito": image_path_heroes + "Yukito.png",

    # Generic Classes
    "Guerreiro": image_path_heroes + "guerreiro.png",
    "Mago": image_path_heroes + "mago.png",
    "Ladino": image_path_heroes + "ladino.png",
    "Arqueiro": image_path_heroes + "arqueiro.png",
    "Barbaro": image_path_heroes + "barbaro.png",
    "Clerigo": image_path_heroes + "clerigo.png",
    "Paladino": image_path_heroes + "paladino.png",
    "Druida": image_path_heroes + "druida.png",
    "Bruxo": image_path_heroes + "bruxo.png",
    
    # Bosses
    "Chefe": image_path_bosses + "chefe.png",
    "Sienna": image_path_bosses + "Sienna.png",
    "SiennaPhoenix": image_path_bosses + "Sienna.png",

    # Monsters
    "Goblin": image_path_monsters + "goblin.png",
    "Esqueleto": image_path_monsters + "esqueleto.png",
    "Kobold": image_path_monsters + "kobold.png",
    "ReiGoblin": image_path_monsters + "rei_goblin.png",
    "LordeLich": image_path_monsters + "lorde_lich.png",
    "DragaoAnciao": image_path_monsters + "dragao_anciao.png",
}

IMAGE_TERRENOS = {
    TERRENO_NORMAL: image_path_env + "terreno_normal.png",
    TERRENO_FLORESTA: image_path_env + "terreno_floresta.png",
    TERRENO_DIFICIL: image_path_env + "terreno_dificil.png",
    TERRENO_PAREDE: image_path_env + "terreno_parede.png",
    TERRENO_GELO: image_path_env + "terreno_gelo.png",
    TERRENO_FOGO: image_path_env + "terreno_fogo.png",
    TERRENO_AGUA: image_path_env + "terreno_agua.png",
    TERRENO_ROCHA: image_path_env + "terreno_rocha.png",
    TERRENO_BARRIL: image_path_env + "terreno_barril.png",
}