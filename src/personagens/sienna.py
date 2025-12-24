from .chefe import Chefe
import random

class Sienna(Chefe):
    def __init__(self, nome, time, nivel=1, sound_player=None, stats=None):
        super().__init__(nome, time, sound_player=sound_player, stats=stats)
        self.classe_nome = "Sienna"
        self.hp_max = 80 # Reduzido de valores mais altos
        self.hp_atual = self.hp_max
        self.mana_atual = 50
        self.mana_max = 50
        self.inicializar_habilidades()
    
    def inicializar_habilidades(self):
        self.habilidades['raio_carmesim'] = {
            "nome": "Raio Carmesim",
            "descricao": "Dispara um raio de energia vermelha.",
            "custo": 5, # Mana
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 8
        }
        self.custo_habilidades['raio_carmesim'] = 5

    def decidir_acao(self, inimigos, aliados, tabuleiro, logger):
        # Simple AI for Sienna
        # 1. Use Raio Carmesim if mana permits and target in range
        if self.mana_atual >= self.custo_habilidades['raio_carmesim']:
            alvos_no_alcance = [i for i in inimigos if self.pode_atacar(i, tabuleiro)]
            if alvos_no_alcance:
                alvo = max(alvos_no_alcance, key=lambda i: 100 if i.hp < i.hp_max * 0.3 else 1) # Prefer weak targets
                return {'acao': 'usar_habilidade', 'habilidade': 'raio_carmesim', 'alvo': alvo}
        
        # 2. Attack normally
        return super().decidir_acao(inimigos, aliados, tabuleiro, logger)

    def executar_habilidade_especifica(self, habilidade, alvo, logger, **kwargs):
        if habilidade == 'raio_carmesim':
            logger.append((f"{self.nome} dispara RAIO CARMESIM em {alvo.nome}!", (255, 50, 50)))
            dano = sum(random.randint(1, 10) for _ in range(2)) # 2d10
            alvo.receber_dano(dano, self, None, logger, tipo_dano="Magico")
            self.mana_atual -= self.custo_habilidades['raio_carmesim']
            # Animation event logic would go here if we had access to the list from here, 
            # but usually this method is called inside MotorCombate which handles basic animations.
            # We will rely on MotorCombate improvements to handle custom skill animations properly 
            # or return animation data.
            # For now, base class doesn't return events easily, but we can hook into MotorCombate.
            pass

class SiennaPhoenix(Chefe):
    def __init__(self, nome, time, nivel=1, sound_player=None, stats=None):
        super().__init__(nome, time, sound_player=sound_player, stats=stats)
        self.classe_nome = "SiennaPhoenix"
        self.mana_atual = 100
        self.mana_max = 100
        self.inicializar_habilidades()
    
    def inicializar_habilidades(self):
        self.habilidades['tempestade_raios'] = {
            "nome": "Tempestade de Raios",
            "descricao": "Atinge múltiplos alvos com raios.",
            "custo": 10,
            "tipo": "acao",
            "alvo": "inimigo",
            "alcance": 10
        }
        self.custo_habilidades['tempestade_raios'] = 10

    def decidir_acao(self, inimigos, aliados, tabuleiro, logger):
        if self.mana_atual >= self.custo_habilidades['tempestade_raios']:
            return {'acao': 'usar_habilidade', 'habilidade': 'tempestade_raios', 'alvo': inimigos[0]} # Target logic handled in execution
        return super().decidir_acao(inimigos, aliados, tabuleiro, logger)
