from .personagem_base import Personagem


class Stark(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Stark"
        self.hp_max = 55
        self.hp_atual = 55
        self.ac_base = 19
        self._forca += 5
        self._constituicao += 4
        self._destreza += 2
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['golpe_poderoso'] = {
            "nome": "Golpe Poderoso",
            "descricao": "Ataque devastador com dano adicional.",
            "custo": 0, "cooldown": 2,
            "tipo": "acao", "alvo": "inimigo", "alcance": 1,
            "dano_extra": 8, "tipo_dano": "Esmagamento"
        }
        self.cooldown_max['golpe_poderoso'] = 2
        self.habilidades['escudo_sagrado'] = {
            "nome": "Escudo Sagrado",
            "descricao": "Aumenta propria defesa por um turno.",
            "custo": 0, "cooldown": 3,
            "tipo": "acao", "alvo": "self", "alcance": 0,
            "buff": "aumentar_ac"
        }
        self.cooldown_max['escudo_sagrado'] = 3
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})


class Elden(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Elden"
        self.hp_max = 32
        self.hp_atual = 32
        self.mana_atual = 40
        self.mana_max = 40
        self._inteligencia += 5
        self._sabedoria += 3
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['raio_arcane'] = {
            "nome": "Raio Arcano",
            "descricao": "Dispara um raio de energia arcana.",
            "custo": 8, "custo_recurso": "mana",
            "tipo": "acao", "alvo": "inimigo", "alcance": 8,
            "dano_extra": 12, "tipo_dano": "Magico"
        }
        self.custo_habilidades['raio_arcane'] = 8
        self.habilidades['curandeiro'] = {
            "nome": "Toque Curativo",
            "descricao": "Cura um aliado proximo.",
            "custo": 6, "custo_recurso": "mana",
            "tipo": "acao", "alvo": "aliado", "alcance": 2,
            "cura": 15
        }
        self.custo_habilidades['curandeiro'] = 6
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})


class Doom(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Doom"
        self.hp_max = 36
        self.hp_atual = 36
        self.energia_atual = 40
        self.energia_max = 40
        self._destreza += 5
        self._forca += 2
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['ataque_sombrio'] = {
            "nome": "Ataque Sombrio",
            "descricao": "Ataque furtivo que causa dano extra.",
            "custo": 8, "custo_recurso": "energia",
            "tipo": "acao", "alvo": "inimigo", "alcance": 1,
            "dano_extra": 10, "tipo_dano": "Necrotico"
        }
        self.custo_habilidades['ataque_sombrio'] = 8
        self.habilidades['passos_das_sombras'] = {
            "nome": "Passos das Sombras",
            "descricao": "Aumenta velocidade e esquiva.",
            "custo": 5, "custo_recurso": "energia",
            "tipo": "acao", "alvo": "self", "alcance": 0,
            "buff": "aumentar_velocidade"
        }
        self.custo_habilidades['passos_das_sombras'] = 5
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})


class Gruu(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Gruu"
        self.hp_max = 60
        self.hp_atual = 60
        self.ac_base = 12
        self._forca += 6
        self._constituicao += 5
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['furia_besta'] = {
            "nome": "Furia da Besta",
            "descricao": "Entra em furia causando dano dobrado.",
            "custo": 0, "cooldown": 4,
            "tipo": "acao", "alvo": "self", "alcance": 0,
            "buff": "furia"
        }
        self.cooldown_max['furia_besta'] = 4
        self.habilidades['esmagar'] = {
            "nome": "Esmagar",
            "descricao": "Ataque massivo que ignora armadura.",
            "custo": 0, "cooldown": 2,
            "tipo": "acao", "alvo": "inimigo", "alcance": 1,
            "dano_extra": 14, "tipo_dano": "Esmagamento"
        }
        self.cooldown_max['esmagar'] = 2
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})


class Kuro(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Kuro"
        self.hp_max = 40
        self.hp_atual = 40
        self._destreza += 4
        self._forca += 3
        self._inteligencia += 2
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['golpe_veloz'] = {
            "nome": "Golpe Veloz",
            "descricao": "Ataque rapido que acerta duas vezes.",
            "custo": 0, "cooldown": 1,
            "tipo": "acao", "alvo": "inimigo", "alcance": 1,
            "dano_extra": 6, "tipo_dano": "Perfurante"
        }
        self.cooldown_max['golpe_veloz'] = 1
        self.habilidades['desviar'] = {
            "nome": "Desviar",
            "descricao": "Desvia do proximo ataque recebido.",
            "custo": 0, "cooldown": 3,
            "tipo": "acao", "alvo": "self", "alcance": 0,
            "buff": "esquiva"
        }
        self.cooldown_max['desviar'] = 3
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})


class Darwin(Personagem):
    def __init__(self, nome, time, nivel=5, sound_player=None):
        super().__init__(nome, time, nivel, sound_player)
        self.classe_nome = "Darwin"
        self.hp_max = 44
        self.hp_atual = 44
        self.mana_atual = 35
        self.mana_max = 35
        self._sabedoria += 5
        self._constituicao += 3
        self.inicializar_habilidades()

    def inicializar_habilidades(self):
        self.habilidades['espinhos'] = {
            "nome": "Chuva de Espinhos",
            "descricao": "Ataque a distancia com espinhos naturais.",
            "custo": 7, "custo_recurso": "mana",
            "tipo": "acao", "alvo": "inimigo", "alcance": 6,
            "dano_extra": 10, "tipo_dano": "Perfurante"
        }
        self.custo_habilidades['espinhos'] = 7
        self.habilidades['cura_druidica'] = {
            "nome": "Cura Druidica",
            "descricao": "Cura todos os aliados proximos.",
            "custo": 10, "custo_recurso": "mana",
            "tipo": "acao", "alvo": "area_aliados", "alcance": 0,
            "cura": 10
        }
        self.custo_habilidades['cura_druidica'] = 10
        self.custo_habilidades.update({k: v.get('custo', 0) for k, v in self.habilidades.items()})
        self.cooldown_max.update({k: v.get('cooldown', 0) for k, v in self.habilidades.items()})
        self.cooldowns.update({k: 0 for k, v in self.habilidades.items() if 'cooldown' in v})
