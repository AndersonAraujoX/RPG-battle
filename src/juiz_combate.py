"""
juiz_combate.py — Juiz de Combate e Rolagem de Dados do Cerco contra Isectum

Regras implementadas:
  Dado D6 Customizado:
    - Faces 1-2:  1 Impacto Físico
    - Face  3:    2 Impactos Físicos
    - Face  4:    3 Impactos Físicos
    - Faces 5-6:  1 Disparo de Longa Distância (Balestra)

  Combate Corpo-a-Corpo (Melee):
    - Defensor deve estar na mesma célula/zona do inimigo
    - Usa apenas Impactos Físicos
    - 2 Impactos = 1 Dano (sobras descartadas)

  Combate à Distância (Ranged):
    - Defensor deve estar em uma Torre de Vigilância
    - Alvos válidos: Catapulta, Torre de Assalto, Muralhas
    - Oficinas internas e Câmara Central NÃO são alvos válidos
    - 1 Disparo = 1 Dano

  HP dos Inimigos:
    - Invasor Comum: 1 dano = morto
    - Infiltrador: exige ação especial (entrega recurso / escavação)
    - Brutamonte: múltiplos círculos de HP (ex: 3 círculos, cada um exige N dano/turno)
"""
from __future__ import annotations
import random
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════

# Zonas internas que NÃO podem ser alvo de combate à distância
ZONAS_INTERNAS = {"carpintaria", "curtume", "fundicao", "camara_central", "patio"}

# Zonas que são torres de vigilância (posição válida para atirador)
ZONAS_TORRES = {"torre_nw", "torre_ne", "torre_sw", "torre_se"}

# Zonas válidas como alvo de combate à distância
ZONAS_ALVO_DISTANCIA = {
    "muralha_norte", "muralha_sul", "muralha_oeste", "muralha_leste",
    "campo_norte", "campo_sul", "campo_oeste", "campo_leste"
    # catapulta e torre_assalto são tratados como targets especiais
}

# HP dos Brutamontes
BRUTAMONTE_CIRCULOS_HP  = 3   # total de círculos de vida
BRUTAMONTE_DANO_POR_CIRCULO = 2  # dano necessário em 1 turno para marcar 1 círculo

# Faces do dado D6 customizado → (impactos_fisicos, disparos_distancia)
FACES_D6 = {
    1: (1, 0),  # 1 Impacto Físico
    2: (1, 0),  # 1 Impacto Físico
    3: (2, 0),  # 2 Impactos Físicos
    4: (3, 0),  # 3 Impactos Físicos
    5: (0, 1),  # 1 Disparo de Longa Distância
    6: (0, 1),  # 1 Disparo de Longa Distância
}

ELEVACAO_ZONAS = {
    "camara_central": 3,
    "curtume": 2,
    "carpintaria": 2,
    "fundicao": 2,
    "patio": 2,
    "muralha_norte": 4,
    "muralha_sul": 4,
    "muralha_oeste": 4,
    "muralha_leste": 4,
    "torre_nw": 6,
    "torre_ne": 6,
    "torre_sw": 6,
    "torre_se": 6,
    "campo_norte": 0,
    "campo_sul": 0,
    "campo_oeste": 0,
    "campo_leste": 0
}


# ═══════════════════════════════════════════════════════════════════════════
# ROLAGEM DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

def rolar_d6_customizado(num_dados: int = 1) -> dict:
    """
    Rola N dados D6 customizados e retorna a soma dos resultados.
    
    Retorna dict com:
        "faces": lista das faces obtidas (int),
        "impactos": total de Impactos Físicos,
        "disparos": total de Disparos de Longa Distância,
        "detalhes": texto descritivo dos resultados
    """
    faces = [random.randint(1, 6) for _ in range(num_dados)]
    
    # Roda animação 3D do D6 se a tela estiver ativa
    try:
        import pygame
        tela = pygame.display.get_surface()
        if tela is not None:
            from src.ui.dado_3d import animar_rolagem_dado
            animar_rolagem_dado(tela, tipo_dado="d6", resultado=faces)
    except Exception as e:
        print("Erro ao renderizar dado 3D D6:", e)
    impactos_total = 0
    disparos_total = 0
    detalhes = []

    for face in faces:
        imp, dis = FACES_D6[face]
        impactos_total += imp
        disparos_total += dis
        if imp > 0:
            detalhes.append(f"D6={face} -> {imp}x Impacto")
        else:
            detalhes.append(f"D6={face} -> {dis}x Disparo")

    return {
        "faces": faces,
        "impactos": impactos_total,
        "disparos": disparos_total,
        "detalhes": detalhes,
    }


# ═══════════════════════════════════════════════════════════════════════════
# JUIZ DE COMBATE — CORPO-A-CORPO
# ═══════════════════════════════════════════════════════════════════════════

def resolver_melee(estado: dict, zona_combate: str, num_dados: int = 2, num_aliados_zona: int = 1) -> dict:
    """
    Resolve combate corpo-a-corpo na zona especificada.
    
    Regras:
      - Usa apenas Impactos Físicos (ignorando disparos)
      - 2 Impactos = 1 Dano; sobras descartadas
      - Invasores comuns morrem com 1 Dano
      - Brutamontes acumulam ferimentos por círculo
      - Flanqueamento: se houver >= 2 aliados na zona, adiciona +1 D6!
    
    Retorna dict com delta de estado e logs de combate.
    """
    pos_heroi = estado.get("pos_heroi")
    if pos_heroi != zona_combate:
        return {
            "delta": {},
            "logs": [("SISTEMA", f"INVALIDO: O heroi nao esta em [{zona_combate}] para atacar melee.")],
            "rolagem": None,
        }

    logs = []
    if num_aliados_zona >= 2:
        num_dados += 1
        logs.append(("SISTEMA", f"⚔️ Flanqueamento ativado! (+1 D6 por ter {num_aliados_zona} aliados na zona)"))

    rolagem = rolar_d6_customizado(num_dados)
    impactos = rolagem["impactos"]
    dano = impactos // 2  # 2 impactos = 1 dano, sobras descartadas

    logs.append(("HEROI", f"Melee em [{zona_combate}]: rolou {rolagem['faces']} "
             f"-> {impactos} Impactos -> {dano} Dano"))
    for det in rolagem["detalhes"]:
        logs.append(("SISTEMA", det))

    delta = {}
    invasores_na_zona = estado["invasores"].get(zona_combate, 0)
    dano_restante = dano

    # 1) Mata invasores comuns primeiro
    mortos = min(dano_restante, invasores_na_zona)
    if mortos > 0:
        novos_invasores = dict(estado["invasores"])
        novos_invasores[zona_combate] = invasores_na_zona - mortos
        delta["invasores"] = novos_invasores
        dano_restante -= mortos
        logs.append(("HEROI", f"{mortos} invasor(es) comum(ns) eliminado(s) em [{zona_combate}]!"))

    # 1.5) Mata Goblins (infiltradores) na área do Pátio
    if dano_restante > 0 and zona_combate == "patio" and estado.get("infiltradores", 0) > 0:
        goblins_mortos = min(dano_restante, estado.get("infiltradores", 0))
        delta["infiltradores"] = estado.get("infiltradores", 0) - goblins_mortos
        dano_restante -= goblins_mortos
        logs.append(("HEROI", f"{goblins_mortos} Goblin(s) eliminado(s) no Pátio!"))

    # 2) Aplica dano restante ao Brutamonte (se houver e dano suficiente)
    if dano_restante > 0 and estado.get("brutamontes", 0) > 0:
        resultado_brute = _aplicar_dano_brutamonte(estado, dano_restante)
        delta.update(resultado_brute["delta"])
        logs += resultado_brute["logs"]

    if dano == 0:
        logs.append(("SISTEMA", "Impactos insuficientes para causar dano (mínimo 2)."))

    return {"delta": delta, "logs": logs, "rolagem": rolagem}


# ═══════════════════════════════════════════════════════════════════════════
# JUIZ DE COMBATE — DISTÂNCIA (BALESTRA)
# ═══════════════════════════════════════════════════════════════════════════

def resolver_distancia(estado: dict, zona_defensor: str, zona_alvo: str,
                       num_dados: int = 2) -> dict:
    """
    Resolve combate à distância (Balestra) de uma torre para um alvo externo.
    
    Regras:
      - Defensor deve estar em uma TORRE DE VIGILÂNCIA
      - Alvos válidos: Muralhas, Catapulta (arma especial), Torre de Assalto (arma especial)
      - Oficinas internas e Câmara Central são alvos INVÁLIDOS
      - 1 Disparo = 1 Dano direto
      - Vantagem de Altura: se elev(defensor) > elev(alvo) ganha +1 D6; se menor, perde 1 D6.
    
    Retorna dict com delta de estado e logs de combate.
    """
    logs = []

    # Valida o ataque usando a função centralizada
    ok, msg_val = validar_pode_atacar_distancia(zona_defensor, zona_alvo)
    if not ok:
        return {
            "delta": {},
            "logs": [("SISTEMA", f"INVALIDO: {msg_val}")],
            "rolagem": None,
        }

    # Calcula elevações
    elev_defensor = ELEVACAO_ZONAS.get(zona_defensor, 1)
    elev_alvo = ELEVACAO_ZONAS.get(zona_alvo, 0) # Catapultas/Torre assalto inimigas no chão tem elevação 0

    if elev_defensor > elev_alvo:
        num_dados += 1
        logs.append(("SISTEMA", f"📐 Vantagem de Altura: +1 D6! [{zona_defensor} Elev {elev_defensor} > {zona_alvo} Elev {elev_alvo}]"))
    elif elev_defensor < elev_alvo:
        num_dados = max(1, num_dados - 1)
        logs.append(("SISTEMA", f"📐 Desvantagem de Altura: -1 D6! [{zona_defensor} Elev {elev_defensor} < {zona_alvo} Elev {elev_alvo}]"))

    rolagem = rolar_d6_customizado(num_dados)
    disparos = rolagem["disparos"]
    dano = disparos  # 1 Disparo = 1 Dano

    logs.append(("HEROI", f"Balestra de [{zona_defensor}] -> [{zona_alvo}]: "
                 f"rolou {rolagem['faces']} -> {disparos} Disparos -> {dano} Dano"))
    for det in rolagem["detalhes"]:
        logs.append(("SISTEMA", det))

    delta = {}

    # Alvos especiais: Armas de Cerco
    if zona_alvo in ("catapulta_cerco", "torre_assalto_inimiga"):
        resultado = _danificar_arma_cerco(estado, zona_alvo, dano)
        delta.update(resultado["delta"])
        logs += resultado["logs"]
    else:
        # Alvo é uma Muralha — mata invasores
        invasores_na_zona = estado["invasores"].get(zona_alvo, 0)
        mortos = min(dano, invasores_na_zona)
        if mortos > 0:
            novos_invasores = dict(estado["invasores"])
            novos_invasores[zona_alvo] = invasores_na_zona - mortos
            delta["invasores"] = novos_invasores
            logs.append(("HEROI", f"{mortos} invasor(es) abatido(s) em [{zona_alvo}] pela Balestra!"))
        else:
            logs.append(("SISTEMA", f"Nenhum alvo em [{zona_alvo}] ou sem disparos suficientes."))

    return {"delta": delta, "logs": logs, "rolagem": rolagem}


# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE HP — BRUTAMONTE
# ═══════════════════════════════════════════════════════════════════════════

def _aplicar_dano_brutamonte(estado: dict, dano: int) -> dict:
    """
    Aplica dano ao Brutamonte (múltiplos círculos de HP).
    Cada círculo exige N dano em 1 turno para ser marcado.
    Brutamonte só é removido quando TODOS os círculos forem preenchidos.
    """
    logs = []
    delta = {}
    hp_atual = estado.get("brutamonte_hp", {
        "circulos_total": BRUTAMONTE_CIRCULOS_HP,
        "circulos_marcados": 0,
        "dano_turno_atual": 0,
    })

    # Acumula dano do turno atual
    dano_turno = hp_atual["dano_turno_atual"] + dano
    circulos_marcados = hp_atual["circulos_marcados"]

    # Verifica quantos círculos são marcados com o dano deste turno
    novos_circulos = dano_turno // BRUTAMONTE_DANO_POR_CIRCULO
    circulos_marcados += novos_circulos

    if novos_circulos > 0:
        logs.append(("CERCO", f"Brutamonte sofreu {novos_circulos} ferimento(s)! "
                    f"[{circulos_marcados}/{BRUTAMONTE_CIRCULOS_HP} circulos]"))

    # Reseta o acumulador de dano do turno após ferir
    dano_restante_turno = dano_turno % BRUTAMONTE_DANO_POR_CIRCULO if novos_circulos > 0 else dano_turno

    # Verifica se o Brutamonte foi derrotado
    if circulos_marcados >= BRUTAMONTE_CIRCULOS_HP:
        brutamontes_restantes = max(0, estado.get("brutamontes", 1) - 1)
        delta["brutamontes"] = brutamontes_restantes
        # Reseta HP para o próximo brutamonte
        delta["brutamonte_hp"] = {
            "circulos_total": BRUTAMONTE_CIRCULOS_HP,
            "circulos_marcados": 0,
            "dano_turno_atual": 0,
        }
        logs.append(("VITORIA", "BRUTAMONTE DERROTADO! A criatura cai pesadamente!"))
        if brutamontes_restantes == 0:
            logs.append(("VITORIA", "Nenhum Brutamonte restante!"))
    else:
        # Atualiza o HP parcial
        delta["brutamonte_hp"] = {
            "circulos_total": BRUTAMONTE_CIRCULOS_HP,
            "circulos_marcados": circulos_marcados,
            "dano_turno_atual": dano_restante_turno,
        }
        logs.append(("SISTEMA", f"Brutamonte resiste com {BRUTAMONTE_CIRCULOS_HP - circulos_marcados} "
                    f"circulo(s) de HP restante(s)."))

    return {"delta": delta, "logs": logs}


def resetar_dano_turno_brutamonte(estado: dict) -> dict:
    """
    Deve ser chamado no início de cada novo turno para resetar o acumulador
    de dano do Brutamonte (sobras não acumulam entre turnos).
    """
    hp_atual = estado.get("brutamonte_hp", None)
    if hp_atual:
        novo_hp = dict(hp_atual)
        novo_hp["dano_turno_atual"] = 0
        return {"brutamonte_hp": novo_hp}
    return {}


# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE COMBATE — ARMAS DE CERCO INIMIGAS
# ═══════════════════════════════════════════════════════════════════════════

def _danificar_arma_cerco(estado: dict, alvo: str, dano: int) -> dict:
    """Aplica dano a uma arma de cerco inimiga (Catapulta ou Torre de Assalto)."""
    logs = []
    delta = {}

    if alvo == "torre_assalto_inimiga":
        torre = estado.get("torre_assalto", {})
        if torre.get("estado") in ("preparando", "ativa"):
            delta["torre_assalto"] = {"estado": "reserva", "ciclo": 0}
            logs.append(("VITORIA", f"Torre de Assalto DESTRUIDA com {dano} de dano!"))
        else:
            logs.append(("SISTEMA", "Torre de Assalto nao esta ativa/preparando."))

    elif alvo == "catapulta_cerco":
        catapulta = estado.get("catapulta", {})
        if catapulta.get("estado") in ("preparando", "ativa"):
            delta["catapulta"] = {"estado": "reserva", "ciclo": 0}
            logs.append(("VITORIA", f"Catapulta DESTRUIDA com {dano} de dano!"))
        else:
            logs.append(("SISTEMA", "Catapulta nao esta ativa/preparando."))

    return {"delta": delta, "logs": logs}


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS DE CONVENIÊNCIA
# ═══════════════════════════════════════════════════════════════════════════

def calcular_dano_melee(num_dados: int = 2) -> tuple[int, list]:
    """Rola dados e retorna (dano_calculado, detalhes_rolagem) para combate melee."""
    rolagem = rolar_d6_customizado(num_dados)
    dano = rolagem["impactos"] // 2
    return dano, rolagem["detalhes"]


def calcular_dano_distancia(num_dados: int = 2) -> tuple[int, list]:
    """Rola dados e retorna (dano_calculado, detalhes_rolagem) para combate à distância."""
    rolagem = rolar_d6_customizado(num_dados)
    dano = rolagem["disparos"]
    return dano, rolagem["detalhes"]


def validar_pode_atacar_distancia(zona_defensor: str, zona_alvo: str) -> tuple[bool, str]:
    """Verifica se o ataque à distância é válido retornando (ok, mensagem)."""
    if zona_defensor not in ZONAS_TORRES:
        return False, f"[{zona_defensor}] nao e uma Torre de Vigilancia."
    if zona_alvo in ZONAS_INTERNAS:
        return False, f"[{zona_alvo}] e uma zona interna — nao pode ser alvo de Balestra."

    # Restrição de alvejar apenas muralhas adjacentes, espaços externos ou máquinas de cerco
    TORRE_MURALHAS_ADJACENTES = {
        "torre_nw": {"muralha_norte", "muralha_oeste"},
        "torre_ne": {"muralha_norte", "muralha_leste"},
        "torre_sw": {"muralha_sul", "muralha_oeste"},
        "torre_se": {"muralha_sul", "muralha_leste"},
    }

    if "muralha" in zona_alvo:
        muralhas_permitidas = TORRE_MURALHAS_ADJACENTES.get(zona_defensor, set())
        if zona_alvo not in muralhas_permitidas:
            return False, f"A partir de [{zona_defensor}], voce so pode alvejar as muralhas adjacentes."
    elif not (zona_alvo.startswith("campo_") or "catapulta" in zona_alvo or "torre_assalto" in zona_alvo):
        return False, "Alvo invalido! A partir das Torres, voce so pode alvejar muralhas adjacentes, espaços externos ou maquinas de cerco."

    return True, "Alvo valido para ataque de Balestra."
