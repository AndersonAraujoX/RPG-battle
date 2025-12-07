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
        self.progresso_personagens = {} # Salvará o estado dos personagens do jogador

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
