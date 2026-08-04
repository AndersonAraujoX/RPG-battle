"""
mao_rei.py — O Mão Rei: Boss final do modo Cerco.

Aparece quando todas as cartas de ameaça dos inimigos são esgotadas.
É um inseto colossal, membro da casta real do Isectum.
Se derrotado, o modo Cerco termina em VITÓRIA.
"""
import random
from .personagem_base import Personagem


class MaoRei(Personagem):
    """
    Boss final do Cerco Isectum.
    Nome: A Mão Rei — emissário pessoal do Imperador Insectum.
    Derrota-lo encerra o cerco em vitória total.
    """
    NOME_EXIBIDO = "A Mão Rei"
    EMOJI = "👁️"

    def __init__(self, nome="A Mão Rei", time="B", nivel=18, sound_player=None, stats=None):
        super().__init__(nome, time, nivel, sound_player, stats=stats)
        # Atributos de boss: muito mais resistente e forte
        self.hp_max   = max(self.hp_max, 120)
        self.hp_atual = self.hp_max
        self.ac_base   = max(self.ac_base, 18)
        self.threat_level = 8.0
        self.alcance  = 3   # alcance médio

        # Habilidades de boss
        self.cooldowns['mandibula_real'] = 0
        self.cooldown_max['mandibula_real'] = 2
        self.cooldowns['olhar_paralisante'] = 0
        self.cooldown_max['olhar_paralisante'] = 3

        self.imunidades = ["Atordoado", "Envenenado", "Amaldiçoado"]
        self.tipo_inseto = "enxame_rainha"
        self._is_boss = True

    @property
    def bonus_ataque(self):
        return self.mod_for + self.bonus_proficiencia + 3  # +3 bônus de boss

    @property
    def bonus_dano(self):
        return self.mod_for + 2

    def atacar(self, alvo, time_inimigo, time_aliado, tabuleiro, logger=print):
        # Habilidade 1: Mandíbula Real — ataque de alto dano em alvo único
        if self.cooldowns['mandibula_real'] == 0:
            logger(f"👁️ {self.nome} usa MANDÍBULA REAL!")
            self.cooldowns['mandibula_real'] = self.cooldown_max['mandibula_real']
            dano = sum(random.randint(1, 8) for _ in range(4)) + self.bonus_dano
            logger(f"  A mandíbula colossal esmaga {alvo.nome} causando {dano} de dano!")
            if self.sound_player:
                self.sound_player('attack')
            alvo.receber_dano(dano, self, tabuleiro, logger)
            self.eventos_animacao.append({'tipo': 'dano', 'alvo': alvo, 'dano': dano})
            return

        # Habilidade 2: Olhar Paralisante — aplica Atordoado em área
        if self.cooldowns['olhar_paralisante'] == 0:
            logger(f"👁️ {self.nome} usa OLHAR PARALISANTE!")
            self.cooldowns['olhar_paralisante'] = self.cooldown_max['olhar_paralisante']
            self.eventos_animacao.append({'tipo': 'ataque_area', 'atacante': self,
                                          'x': self.pos_x, 'y': self.pos_y, 'raio': 3})
            for p in list(time_inimigo):
                if p.esta_vivo:
                    dist = abs(p.pos_x - self.pos_x) + abs(p.pos_y - self.pos_y)
                    if dist <= 3:
                        from .status_efeito import StatusEfeito
                        p.status_efeitos.append(StatusEfeito("Atordoado", duracao=2))
                        logger(f"  {p.nome} está PARALISADO pelo olhar do Mão Rei!")
            return

        # Ataque normal
        super().atacar(alvo, time_inimigo, time_aliado, tabuleiro, logger)
