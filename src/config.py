# --- Constantes de Tela e Tabuleiro ---
LARGURA_TELA = 1024
ALTURA_BARRA_INICIATIVA = 60
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
COR_BOTAO_HOVER = (110, 110, 110)
COR_BOTAO_DESABILITADO = (50, 50, 50)
CORES_TIME = {"A": (60, 120, 220), "B": (220, 60, 60)}
COR_HP_BAR_FUNDO = (50, 50, 50)
COR_HP_BAR_FRENTE = (60, 200, 60)
COR_MANA_BAR = (60, 100, 220)
COR_ENERGIA_BAR = (220, 200, 60)

# --- Constantes de Terreno (importadas para uso nas cores) ---
TERRENO_NORMAL = "NORMAL"
TERRENO_FLORESTA = "FLORESTA"
TERRENO_DIFICIL = "DIFICIL"
TERRENO_PAREDE = "PAREDE"
TERRENO_GELO = "GELO"

CORES_TERRENO = {
    TERRENO_NORMAL: (30, 30, 30),
    TERRENO_PAREDE: (100, 100, 100),
    TERRENO_FLORESTA: (20, 80, 20),
    TERRENO_DIFICIL: (110, 90, 70),
    TERRENO_GELO: (180, 200, 255),
}

# --- Constantes de Estado de Jogo ---
ESTADO_JOGO_MENU = "MENU"
ESTADO_JOGO_COMBATE = "COMBATE"

# --- Constantes de Estado de Combate ---
ESTADO_COMBATE_VEZ_IA = "VEZ_IA"
ESTADO_COMBATE_AGUARDANDO_JOGADOR = "AGUARDANDO_JOGADOR"
ESTADO_COMBATE_JOGADOR_SELECIONOU = "JOGADOR_SELECIONOU"

# --- Constantes de Modo de Painel ---
PAINEL_MODO_LOG = "LOG"
PAINEL_MODO_INFO = "INFO"

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
    }
}

# --- Imagens (Placeholders) ---
# ATENÇÃO: Substitua 'caminho/para/imagem.png' pelos caminhos reais das suas imagens.
# Certifique-se de que as imagens existam ou o jogo pode falhar ao carregar.
IMAGE_PERSONAGENS = {
    "Guerreiro": "assets/images/guerreiro.png",
    "Mago": "assets/images/mago.png",
    "Ladino": "assets/images/ladino.png",
    "Arqueiro": "assets/images/arqueiro.png",
    "Barbaro": "assets/images/barbaro.png",
    "Clerigo": "assets/images/clerigo.png",
    "Chefe": "assets/images/chefe.png",
    "Paladino": "assets/images/paladino.png",
    "ReiGoblin": "assets/images/rei_goblin.png",
    "LordeLich": "assets/images/lorde_lich.png",
    "DragaoAnciao": "assets/images/dragao_anciao.png",
    "Druida": "assets/images/druida.png",
    "Bruxo": "assets/images/bruxo.png",
    # Adicione outros personagens conforme necessário
}

IMAGE_TERRENOS = {
    TERRENO_NORMAL: "assets/images/terreno_normal.png",
    TERRENO_FLORESTA: "assets/images/terreno_floresta.png",
    TERRENO_DIFICIL: "assets/images/terreno_dificil.png",
    TERRENO_PAREDE: "assets/images/terreno_parede.png",
    TERRENO_GELO: "assets/images/terreno_gelo.png",
    # Adicione outros terrenos conforme necessário
}