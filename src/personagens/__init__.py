from .personagem_base import Personagem, calcular_distancia
from .guerreiro import Guerreiro
from .mago import Mago
from .ladino import Ladino
from .arqueiro import Arqueiro
from .barbaro import Barbaro
from .clerigo import Clerigo
from .chefe import Chefe
from .paladino import Paladino
from .rei_goblin import ReiGoblin
from .lorde_lich import LordeLich
from .dragao_anciao import DragaoAnciao
from .druida import Druida
from .bruxo import Bruxo
from .minions import Goblin, Esqueleto, Kobold
from .protagonistas import Novak, Koema, Rilem, Yukito, Aquele
from .sienna import Sienna, SiennaPhoenix
from .novos_personagens import Stark, Elden, Doom, Gruu, Kuro, Darwin
from .mao_rei import MaoRei

def get_class_by_name(name):
    cls_map = {
        "Guerreiro": Guerreiro,
        "Mago": Mago,
        "Ladino": Ladino,
        "Arqueiro": Arqueiro,
        "Bárbaro": Barbaro,
        "Clérigo": Clerigo,
        "Paladino": Paladino,
        "Druida": Druida,
        "Bruxo": Bruxo,
        "ReiGoblin": ReiGoblin,
        "LordeLich": LordeLich,
        "DragaoAnciao": DragaoAnciao,
        "Goblin": Goblin,
        "Esqueleto": Esqueleto,
        "Kobold": Kobold,
        "Novak": Novak,
        "Koema": Koema,
        "Rilem": Rilem,
        "Yukito": Yukito,
        "Aquele": Aquele,
        "Sienna": Sienna,
        "SiennaPhoenix": SiennaPhoenix,
        "Stark": Stark,
        "Elden": Elden,
        "Doom": Doom,
        "Gruu": Gruu,
        "Kuro": Kuro,
        "Darwin": Darwin
    }
    return cls_map.get(name)
