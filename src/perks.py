
# Dicionário de Perks por Classe/Personagem
# Cada perk tem:
# - nome: Display name
# - descricao: Display description
# - tipo: 'passiva', 'habilidade_mod' (modifica habilidade existente), 'gatilho' (ativa em evento)
# - codigo: Identificador único para lógica

PERKS = {
    "Novak": [
        {
            "id": "muralha_escudos",
            "nome": "Muralha de Escudos",
            "descricao": "+2 AC se tiver aliados adjacentes.",
            "tipo": "passiva",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (0, 0)
        },
        {
            "id": "ultima_linha",
            "nome": "Última Linha",
            "descricao": "Resiste a 1 golpe fatal por batalha (Fica com 1 HP).",
            "tipo": "gatilho",
            "nivel_req": 3,
            "req_perk": "muralha_escudos",
            "pos": (0, 1)
        },
        {
            "id": "lamina_incendiaria",
            "nome": "Lâmina Incendiária",
            "descricao": "Golpe Flamejante cria terreno de fogo.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "golpe_flamejante",
            "nivel_req": 5,
            "req_perk": None,
            "pos": (1, 0)
        },
         {
            "id": "sede_sangue",
            "nome": "Sede de Sangue",
            "descricao": "Recupera 5 HP ao matar um inimigo.",
            "tipo": "gatilho",
            "nivel_req": 5,
            "req_perk": "lamina_incendiaria",
            "pos": (1, 1)
        }
    ],
    "Koema": [
        {
            "id": "aura_vitalidade",
            "nome": "Aura de Vitalidade",
            "descricao": "Aliados adjacentes curam 2 HP no início do turno.",
            "tipo": "passiva",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (0, 0)
        },
        {
            "id": "mimetismo",
            "nome": "Mimetismo",
            "descricao": "+4 AC se estiver em terreno de Floresta ou Cobertura.",
            "tipo": "passiva",
            "nivel_req": 5,
            "req_perk": "aura_vitalidade",
            "pos": (0, 1)
        },
        {
            "id": "maos_rapidas",
            "nome": "Mãos Rápidas",
            "descricao": "Habilidades de cura custam menos.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "primeiros_socorros",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (1, 0)
        },
        {
            "id": "golpe_baixo_stunning",
            "nome": "Golpe Baixo Atordoante",
            "descricao": "Truque Sujo atordoa se alvo já tiver debuff.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "truque_sujo",
            "nivel_req": 5,
            "req_perk": "maos_rapidas",
            "pos": (1, 1)
        }
    ],
    "Rilem": [
        {
            "id": "analise_fraqueza_perma",
            "nome": "Análise Profunda",
            "descricao": "Quebrar Defesa dura até o fim do combate.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "quebrar_defesa",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (0, 0)
        },
        {
             "id": "ataque_coordenado",
             "nome": "Ataque Coordenado",
             "descricao": "Bônus de flanqueamento comandado por Rilem é dobrado (+4).",
             "tipo": "passiva",
             "nivel_req": 5,
             "req_perk": "analise_fraqueza_perma",
             "pos": (0, 1)
        },
        {
            "id": "inspiracao_movimento",
            "nome": "Inspiração de Movimento",
            "descricao": "Comando Tático também aumenta movimento dos aliados.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "comando_tatico",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (1, 0)
        }
    ],
    "Yukito": [
        {
            "id": "ressonancia_arcana",
            "nome": "Ressonância Arcana",
            "descricao": "Matar inimigo com magia restaura 10 Mana.",
            "tipo": "gatilho",
            "nivel_req": 3,
            "req_perk": None,
            "pos": (0, 0)
        },
         {
            "id": "poco_gravidade",
            "nome": "Poço de Gravidade",
            "descricao": "Explosão Arcana puxa inimigos próximos.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "explosao_arcana",
            "nivel_req": 5,
            "req_perk": "ressonancia_arcana",
            "pos": (0, 1)
        },
        {
            "id": "terra_arrasada",
            "nome": "Terra Arrasada",
            "descricao": "Tempestade de Fogo converte terreno em Lava.",
            "tipo": "habilidade_mod",
            "habilidade_alvo": "tempestade_fogo",
            "nivel_req": 5,
            "req_perk": None,
            "pos": (1, 0)
        }
    ]
}
