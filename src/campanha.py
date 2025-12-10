from .personagens import ReiGoblin, LordeLich, DragaoAnciao, Goblin, Esqueleto, Kobold

# Exemplo de estrutura de campanha
# Cada entrada é uma batalha, com a configuração de inimigos
CAMPAIGN_DATA = [
    {
        "inimigos": [
            (Goblin, 2),
            (Kobold, 1),
        ],
        "mapa": "mapa_floresta.json", # Futuramente, usar mapas específicos
        "mensagem_inicio": "Uma pequena horda de goblins bloqueia o caminho!",
        "dialogo_inicio": [
            ("Guerreiro", "O que é aquilo na estrada?", "guerreiro"),
            ("Goblin", "Kekeke! Comida fresca!", "goblin"),
            ("Mago", "Preparem-se! Eles parecem hostis.", "mago"),
        ]
    },
    {
        "inimigos": [
            (Esqueleto, 3),
            (LordeLich, 1),
        ],
        "mapa": "mapa_cemiterio.json",
        "mensagem_inicio": "Um cemitério amaldiçoado! Um Lorde Lich e seus lacaios se erguem!",
        "dialogo_inicio": [
            ("Clérigo", "Sinto uma presença profana aqui...", "clerigo"),
            ("Lorde Lich", "Mortais tolos... Vocês se juntarão ao meu exército!", "lordelich"),
            ("Paladino", "Pela luz, nós vamos purificar este lugar!", "paladino"),
        ]
    },
    {
        "inimigos": [
            (DragaoAnciao, 1),
        ],
        "mapa": "mapa_montanha.json",
        "mensagem_inicio": "A Batalha Final! Um Dragão Ancião protege o pico da montanha.",
        "dialogo_inicio": [
            ("Dragão Ancião", "QUEM OUSA PERTURBAR MEU SONO?", "dragaoanciao"),
            ("Guerreiro", "Viemos pôr um fim ao seu reinado de terror!", "guerreiro"),
            ("Dragão Ancião", "Então queimem!", "dragaoanciao"),
        ]
    },
]

class CampaignManager:
    def __init__(self):
        self.nivel_atual = 0
        self.progresso_personagens = {} 
        self.posicao_jogador = [100, 400] # Posição inicial (x, y)
        self.destino_movimento = None # Para movimento suave
        
        # Definição dos Locais no Mapa Mundi (Coordenadas baseadas em 1024x768)
        self.locais = [
            {
                "nome": "Floresta do Caos",
                "pos": (150, 400),
                "raio": 40,
                "evento_id": 0, # Index em CAMPAIGN_DATA
                "completado": False,
                "cor": (34, 139, 34) # Forest Green
            },
            {
                "nome": "Pântano de Vendala",
                "pos": (500, 350),
                "raio": 40,
                "evento_id": 1,
                "completado": False,
                "cor": (47, 79, 79) # Dark Slate Gray
            },
            {
                "nome": "Picos Cinzentos",
                "pos": (600, 650),
                "raio": 40,
                "evento_id": 2,
                "completado": False,
                "cor": (105, 105, 105) # Dim Gray
            },
             {
                "nome": "Bosque Nebuloso",
                "pos": (800, 200),
                "raio": 40,
                "evento_id": 0, # Reutilizando evento 0 como placeholder
                "completado": False,
                "cor": (100, 200, 150)
            },
        ]

    def atualizar_movimento(self):
        if self.destino_movimento:
            # Movimento simples linear
            dx = self.destino_movimento[0] - self.posicao_jogador[0]
            dy = self.destino_movimento[1] - self.posicao_jogador[1]
            dist = (dx**2 + dy**2)**0.5
            
            velocidade = 5 # Pixels por frame
            
            if dist < velocidade:
                self.posicao_jogador = list(self.destino_movimento)
                self.destino_movimento = None
            else:
                self.posicao_jogador[0] += (dx / dist) * velocidade
                self.posicao_jogador[1] += (dy / dist) * velocidade

    def get_battle_config(self):
        if self.nivel_atual < len(CAMPAIGN_DATA):
            return CAMPAIGN_DATA[self.nivel_atual]
        return None

    def avancar_nivel(self):
        self.nivel_atual += 1

    def salvar_progresso_personagens(self, time_a):
        self.progresso_personagens = {p.nome: p.to_dict() for p in time_a}

    def carregar_progresso_personagens(self, time_a):
        for p in time_a:
            if p.nome in self.progresso_personagens:
                p.from_dict(self.progresso_personagens[p.nome])

    def reset(self):
        self.nivel_atual = 0
        self.progresso_personagens = {}
