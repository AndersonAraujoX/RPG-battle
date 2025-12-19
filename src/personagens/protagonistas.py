from .personagem_base import Personagem

class Novak(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Novak"
        self.hp_max = 50 # High HP Base
        self.hp_atual = 50
        self.ac_base = 18 # High AC
        self._forca += 4
        self._constituicao += 4
        
    def inicializar_habilidades(self):
        # Tank Agressivo
        self.habilidades['provocar'] = {
            "nome": "Provocar",
            "descricao": "Força inimigos próximos a atacarem Novak.",
            "custo": 0, 
            "cooldown": 3,
            "tipo": "acao",
            "alvo": "area",
            "alcance": 3,
            "raio": 3,
            "efeito": "provocacao"
        }
        self.cooldown_max['provocar'] = 3
        
        self.habilidades['golpe_flamejante'] = {
            "nome": "Golpe Flamejante",
            "descricao": "Ataque com dano de fogo extra.",
            "custo": 0,
            "cooldown": 2,
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 1,
            "dano_extra": 5,
            "tipo_dano": "Fogo"
        }
        self.cooldown_max['golpe_flamejante'] = 2

class Koema(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Koema"
        self.hp_max = 35
        self.hp_atual = 35
        self.mana_atual = 30 
        self.mana_max = 30
        self._destreza += 2
        self._inteligencia += 2

    def inicializar_habilidades(self):
        # Jack-of-all-trades
        self.habilidades['truque_sujo'] = {
            "nome": "Truque Sujo",
            "descricao": "Causa dano e reduz ataque do inimigo.",
            "custo": 5, # Mana? Ou cooldown?
            "custo_recurso": "mana",
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 1,
            "debuff": "reduzir_ataque"
        }
        self.custo_habilidades['truque_sujo'] = 5
        
        self.habilidades['primeiros_socorros'] = {
            "nome": "Primeiros Socorros",
            "descricao": "Cura um aliado próximo.",
            "custo": 5,
            "custo_recurso": "mana",
            "tipo": "acao",
            "alvo": "aliado",
            "alcance": 1,
            "cura": 10
        }
        self.custo_habilidades['primeiros_socorros'] = 5

class Rilem(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Rilem"
        self.energia_atual = 40
        self.energia_max = 40
        self._destreza += 4
        self._inteligencia += 3 # For strategy

    def inicializar_habilidades(self):
        # Support/Strategist
        self.habilidades['comando_tatico'] = {
            "nome": "Comando Tático",
            "descricao": "Aumenta o ataque de todos os aliados.",
            "custo": 10, # Energy
            "custo_recurso": "energia",
            "tipo": "acao",
            "alvo": "todos_aliados",
            "alcance": 99,
            "buff": "aumentar_ataque"
        }
        self.custo_habilidades['comando_tatico'] = 10
        
        self.habilidades['quebrar_defesa'] = {
            "nome": "Quebrar Defesa",
            "descricao": "Reduz a AC de um inimigo.",
            "custo": 10,
            "custo_recurso": "energia",
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 6,
            "debuff": "reduzir_ac"
        }
        self.custo_habilidades['quebrar_defesa'] = 10

class Yukito(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Yukito"
        self.mana_atual = 50
        self.mana_max = 50
        self._inteligencia += 5
        
    def inicializar_habilidades(self):
        # Artillery/AoE Mage
        self.habilidades['tempestade_fogo'] = { 
            "nome": "Tempestade de Fogo", 
            "descricao": "Grande área de fogo (3x3).",
            "custo": 15,
            "custo_recurso": "mana",
            "tipo": "acao",
            "alvo": "area",
            "alcance": 8,
            "raio": 1, # 3x3 effective
            "dano": 10,
            "tipo_dano": "Fogo"
        }
        self.custo_habilidades['tempestade_fogo'] = 15
        
        self.habilidades['explosao_arcana'] = {
            "nome": "Explosão Arcana",
            "descricao": "Dano massivo em alvo único.",
            "custo": 10,
            "custo_recurso": "mana",
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 8,
            "dano": 15,
            "tipo_dano": "Magico"
        }
        self.custo_habilidades['explosao_arcana'] = 10
