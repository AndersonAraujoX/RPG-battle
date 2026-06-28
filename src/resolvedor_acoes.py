"""
resolvedor_acoes.py — Resolvedor de Ações do Cerco contra Isectum (Tático)

Valida se a jogada pretendida pelo jogador é permitida usando coordenadas do tabuleiro de grade.

Zonas Lógicas mapeadas no Tabuleiro 20x20:
  - Câmara Central:  [8..11, 8..11]
  - Carpintaria:     [8..11, 3..7]
  - Curtume:         [8..11, 12..16]
  - Fundição:        [3..7,  8..11]
  - Pátio/Escavação: [12..16, 8..11]
  - Muralha Norte:   [5..14, 0..2]
  - Muralha Sul:     [5..14, 17..19]
  - Muralha Oeste:   [0..2,  5..14]
  - Muralha Leste:   [17..19, 5..14]
"""
from __future__ import annotations
from typing import Optional, Dict, List, Tuple

# Mapeamento de Zonas Lógicas para Retângulos de Células (x_min, y_min, x_max, y_max)
# Conforme imagem: Couro no topo (Norte), Madeira no rodapé (Sul), Ferro à esquerda (Oeste), Nexos à direita (Leste)
ZONAS_GRID = {
    "camara_central": (8, 8, 11, 11),  # OURO (Centro)
    "curtume":        (8, 3, 11, 7),   # COURO (Topo / Norte)
    "carpintaria":    (8, 12, 11, 16), # MADEIRA (Rodapé / Sul)
    "fundicao":       (3, 8, 7, 11),   # FERRO (Esquerda / Oeste)
    "patio":          (12, 8, 16, 11),  # NEXOS (Direita / Leste)
    "muralha_norte":  (5, 0, 14, 2),
    "muralha_sul":    (5, 17, 14, 19),
    "muralha_oeste":  (0, 5, 2, 14),
    "muralha_leste":  (17, 5, 19, 14),
}

# Zonas de Produção e o recurso que geram
OFICINAS = {
    "carpintaria": "madeira",
    "curtume":     "couro",
    "fundicao":    "metal",
}

ZONA_ESCAVACAO = "patio"

NOME_RECURSO = {
    "madeira": "🪵 Madeira",
    "couro":   "🧳 Couro",
    "metal":   "⚙️  Metal",
}


def obter_zona_por_coordenada(x: int, y: int) -> Optional[str]:
    """Retorna qual zona lógica a célula (x, y) pertence."""
    for zona, (x1, y1, x2, y2) in ZONAS_GRID.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return zona
    return None


# ═══════════════════════════════════════════════════════════════════════════
# PATHFINDING NA GRADE TÁTICA (Dijkstra considerando terreno)
# ═══════════════════════════════════════════════════════════════════════════
def custo_minimo_grade(motor_combate, origem: tuple[int, int], destino: tuple[int, int]) -> Optional[int]:
    """Calcula o custo mínimo na grade 20x20 considerando paredes e elevações."""
    tab = motor_combate.tabuleiro
    ox, oy = origem
    dx, dy = destino

    if not (0 <= dx < tab.largura and 0 <= dy < tab.altura):
        return None
    # Evita paredes
    if tab.get_terrain_em(dx, dy) == "parede":
        return None

    dist = {origem: 0}
    fila = [(0, origem)]

    while fila:
        fila.sort(key=lambda x: x[0])
        custo, (cx, cy) = fila.pop(0)

        if (cx, cy) == destino:
            return custo

        for dx2, dy2 in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx2, cy + dy2
            if 0 <= nx < tab.largura and 0 <= ny < tab.altura:
                terr = tab.get_terrain_em(nx, ny)
                if terr == "parede":
                    continue

                # Custo padrão de terreno
                peso = 1
                if terr == "dificil":
                    peso = 2

                # Custo por diferença de elevação (subir custa mais)
                el_curr = tab.get_elevation_em(cx, cy)
                el_next = tab.get_elevation_em(nx, ny)
                if el_next > el_curr:
                    peso += (el_next - el_curr)

                nc = custo + peso
                if nc < dist.get((nx, ny), 10**9):
                    dist[(nx, ny)] = nc
                    fila.append((nc, (nx, ny)))

    return None


def obter_celulas_alcancaveis(motor_combate, origem: tuple[int, int], pontos: int) -> dict[tuple[int, int], int]:
    """Retorna todas as células alcançáveis a partir de origem com os pontos disponíveis."""
    tab = motor_combate.tabuleiro
    dist = {origem: 0}
    fila = [(0, origem)]
    resultado = {}

    while fila:
        fila.sort(key=lambda x: x[0])
        custo, (cx, cy) = fila.pop(0)

        if custo > pontos:
            continue
        if (cx, cy) != origem:
            resultado[(cx, cy)] = custo

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < tab.largura and 0 <= ny < tab.altura:
                terr = tab.get_terrain_em(nx, ny)
                if terr == "parede":
                    continue

                peso = 1
                if terr == "dificil":
                    peso = 2

                el_curr = tab.get_elevation_em(cx, cy)
                el_next = tab.get_elevation_em(nx, ny)
                if el_next > el_curr:
                    peso += (el_next - el_curr)

                nc = custo + peso
                if nc <= pontos and nc < dist.get((nx, ny), 10**9):
                    dist[(nx, ny)] = nc
                    fila.append((nc, (nx, ny)))

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# VALIDAR AÇÕES NA GRADE
# ═══════════════════════════════════════════════════════════════════════════
def validar_mover(estado, dest_x: int, dest_y: int, pontos: int, motor_combate):
    """Valida o movimento do herói até uma célula específica."""
    pos_x = estado.get("heroi_x", 9)
    pos_y = estado.get("heroi_y", 9)

    if pos_x == dest_x and pos_y == dest_y:
        return False, 0, "Herói já está nesta célula!"

    custo = custo_minimo_grade(motor_combate, (pos_x, pos_y), (dest_x, dest_y))
    if custo is None:
        return False, 0, "Destino inacessível (obstáculo ou parede)."
    if custo > pontos:
        return False, custo, f"Caminho exige {custo} PM, mas restam {pontos}."

    return True, custo, ""


def executar_mover(estado, dest_x: int, dest_y: int, custo: int) -> tuple[dict, list]:
    delta = {
        "heroi_x":          dest_x,
        "heroi_y":          dest_y,
        "pos_heroi":       obter_zona_por_coordenada(dest_x, dest_y) or "camara_central",
        "pontos_movimento": max(0, estado["pontos_movimento"] - custo),
    }
    logs = [("HEROI", f"Herói moveu para ({dest_x}, {dest_y})  (−{custo} PM)")]
    return delta, logs


def validar_trabalhar(estado, pontos: int):
    """Valida o trabalho na oficina."""
    pos_x = estado.get("heroi_x", 9)
    pos_y = estado.get("heroi_y", 9)
    zona = obter_zona_por_coordenada(pos_x, pos_y)

    if zona not in OFICINAS:
        return False, None, "Você precisa estar fisicamente na Carpintaria, Curtume ou Fundição!"
    if estado["invasores"].get(zona, 0) > 0:
        return False, None, f"Bloqueado! Há invasores atacando esta oficina."
    if pontos <= 0:
        return False, None, "Sem pontos de trabalho."

    return True, OFICINAS[zona], ""


def executar_trabalhar(estado, recurso: str, qtd: int = 1) -> tuple[dict, list]:
    dep = dict(estado.get("recursos_depositados", {"madeira": 0, "couro": 0, "metal": 0}))
    dep[recurso] = dep.get(recurso, 0) + qtd
    delta = {
        "recursos_depositados": dep,
        "pontos_trabalho": max(0, estado["pontos_trabalho"] - qtd),
    }
    logs = [("HEROI", f"+{qtd}x {NOME_RECURSO[recurso]} produzido e alocado.")]
    return delta, logs


def validar_escavar(estado, pontos: int):
    """Valida escavação no Pátio."""
    pos_x = estado.get("heroi_x", 9)
    pos_y = estado.get("heroi_y", 9)
    zona = obter_zona_por_coordenada(pos_x, pos_y)

    if zona != ZONA_ESCAVACAO:
        return False, 0, "Vá até o Pátio / Área de Escavação para cavar!"
    if estado["brutamontes"] > 0 or estado.get("infiltradores", 0) > 0:
        return False, 0, "Bloqueado! Limpe o Pátio de inimigos primeiro."
    if estado["pedregulhos"] <= 0:
        return False, 0, "Sem pedregulhos."
    if pontos <= 0:
        return False, 0, "Sem pontos de escavação."

    qtd = min(pontos, estado["pedregulhos"])
    return True, qtd, ""


def executar_escavar(estado, qtd: int) -> tuple[dict, list]:
    novo = estado["pedregulhos"] - qtd
    delta = {
        "pedregulhos":      novo,
        "pontos_escavacao": max(0, estado["pontos_escavacao"] - qtd),
    }
    logs = [("HEROI", f"⛏️ Escavou {qtd}x pedregulho no Pátio.")]

    if novo <= 0:
        delta["vitoria"] = True
        delta["msg_vitoria"] = "Túnel finalizado! Os anões escaparam!"
        logs.append(("VITORIA", "VITÓRIA! Túnel concluído!"))
    elif novo % 4 == 0 and novo < estado["pedregulhos_max"]:
        delta["infiltradores"] = estado.get("infiltradores", 0) + 2
        logs.append(("CERCO", "2 Infiltradores invadiram a escavação!"))

    return delta, logs


def validar_subornar(estado, recurso: str):
    inf = estado.get("infiltradores", 0)
    if inf <= 0:
        return False, "Nenhum infiltrador para subornar."
    dep = estado.get("recursos_depositados", {})
    if dep.get(recurso, 0) <= 0:
        return False, f"Sem {NOME_RECURSO.get(recurso, recurso)}."
    return True, ""


def executar_subornar(estado, recurso: str) -> tuple[dict, list]:
    dep = dict(estado.get("recursos_depositados", {}))
    dep[recurso] = max(0, dep.get(recurso, 0) - 1)
    delta = {
        "infiltradores":        max(0, estado.get("infiltradores", 0) - 1),
        "recursos_depositados": dep,
    }
    logs = [("HEROI", f"Infiltrador removido via suborno com {NOME_RECURSO.get(recurso, recurso)}.")]
    return delta, logs


def validar_comprar_upgrade(estado, slot_id: int, idx_carta_queimar: int, mao: list):
    slots = estado.get("slots_upgrade", [])
    if slot_id < 0 or slot_id >= len(slots):
        return False, "Slot inválido."
    slot = slots[slot_id]
    if slot.get("bloqueado"):
        return False, "Slot destruído!"
    if slot.get("adquirido"):
        return False, "Já comprado."

    dep = estado.get("recursos_depositados", {})
    for res, qtd in slot.get("custo", {}).items():
        if dep.get(res, 0) < qtd:
            return False, f"Falta {NOME_RECURSO.get(res, res)}."

    if idx_carta_queimar < 0 or idx_carta_queimar >= len(mao):
        return False, "Escolha carta para queimar."
    if mao[idx_carta_queimar].get("tipo") == "ameaca":
        return False, "Não pode queimar ameaça."

    return True, ""


def executar_comprar_upgrade(estado, slot_id: int, idx_carta_queimar: int,
                             mao: list, deck_total: int) -> tuple[dict, list, list]:
    slots = [dict(s) for s in estado.get("slots_upgrade", [])]
    slot = slots[slot_id]

    dep = dict(estado.get("recursos_depositados", {}))
    for res, qtd in slot.get("custo", {}).items():
        dep[res] = max(0, dep.get(res, 0) - qtd)

    slots[slot_id]["adquirido"] = True
    nova_mao = [c for i, c in enumerate(mao) if i != idx_carta_queimar]

    delta = {
        "slots_upgrade":        slots,
        "recursos_depositados": dep,
    }
    logs = [
        ("HEROI", f"Upgrade comprado: [{slot['nome']}]!"),
        ("HEROI", f"Queimou '{mao[idx_carta_queimar]['nome']}'. Deck total: {deck_total - 1}."),
    ]
    return delta, logs, nova_mao
