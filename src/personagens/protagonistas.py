from .personagem_base import Personagem

class Novak(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Novak"
        self.hp_max = 50 # High HP Base
        self.hp_atual = 50
        self.ac_base = 18 # High AC
        self._forca += 4
        self._forca += 4
        self._constituicao += 4
        
        self.inicializar_habilidades()
        
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
        
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

class Koema(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Koema"
        self.hp_max = 35
        self.hp_atual = 35
        self.mana_atual = 30 
        self.mana_max = 30
        self._destreza += 2
        self._destreza += 2
        self._inteligencia += 2
        
        self.inicializar_habilidades()

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
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

class Rilem(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Rilem"
        self.energia_atual = 40
        self.energia_max = 40
        self._destreza += 4
        self._inteligencia += 3 # For strategy
        
        self.inicializar_habilidades()

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
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

class Yukito(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Yukito"
        self.mana_atual = 50
        self.mana_max = 50
        self._inteligencia += 5
        self.inicializar_habilidades()
        
    def inicializar_habilidades(self):
        # Artillery/AoE Mage
        self.habilidades['tempestade_fogo'] = { 
            "nome": "Tempestade de Fogo", 
            "descricao": "Grande área de fogo (3x3).",
            "custo": 15,
            "tipo": "area", # Standardized from "acao"/"alvo"
            "alcance": 8,
            "area": 1, # Standardized from "raio"
            "dano": "10", # String for display, int for logic
            "tipo_dano": "Fogo"
        }
        self.habilidades['explosao_arcana'] = {
            "nome": "Explosão Arcana",
            "descricao": "Dano massivo em alvo único.",
            "custo": 10,
            "tipo": "alvo",
            "alcance": 8,
            "area": 0,
            "dano": "15",
            "tipo_dano": "Magico"
        }
        self.custo_habilidades = {k: v['custo'] for k, v in self.habilidades.items()}
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})

class Aquele(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Aquele"
        self.hp_max = 48
        self.hp_atual = 48
        self._forca += 3
        self._destreza += 2
        self._constituicao += 2
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['investida'] = {
            "nome": "Investida",
            "descricao": "Avança sobre o inimigo causando dano extra.",
            "custo": 0,
            "cooldown": 2,
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 2,
            "dano_extra": 4,
            "tipo_dano": "Esmagamento"
        }
        self.cooldown_max['investida'] = 2

        self.habilidades['golpe_preciso'] = {
            "nome": "Golpe Preciso",
            "descricao": "Ataque com bônus de acerto e dano adicional.",
            "custo": 0,
            "cooldown": 1,
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 1,
            "dano_extra": 6,
            "tipo_dano": "Perfurante"
        }
        self.cooldown_max['golpe_preciso'] = 1

        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})
