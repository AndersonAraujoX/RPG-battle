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
# Grade 20x20 (coords 0..19), com zona externa de spawn usando coords virtuais -5..-1 e 20..24
ZONAS_GRID = {
    # ── Interior ────────────────────────────────────────────────────────────
    "camara_central": (8,  8,  11, 11),  # OURO   — câmara do tesouro
    "curtume":        (5,  4,  14,  7),  # COURO  — Norte interno
    "carpintaria":    (5, 12,  14, 15),  # MADEIRA — Sul interno
    "fundicao":       (4,  5,   7, 14),  # FERRO  — Oeste interno
    "patio":          (12, 5,  15, 14),  # NEXOS  — Leste interno
    # ── Muralhas (perímetro fechado) ────────────────────────────────────────
    "muralha_norte":  (4,  0,  15,  3),  # muro N (inclui as Torres NO/NE)
    "muralha_sul":    (4, 16,  15, 19),  # muro S
    "muralha_oeste":  (0,  4,   3, 15),  # muro O
    "muralha_leste":  (16, 4,  19, 15),  # muro L
    # ── Torres dos cantos (elevação extra) ──────────────────────────────────
    "torre_nw":       (0,  0,   3,  3),  # Torre Noroeste
    "torre_ne":       (16, 0,  19,  3),  # Torre Nordeste
    "torre_sw":       (0, 16,   3, 19),  # Torre Sudoeste
    "torre_se":       (16,16,  19, 19),  # Torre Sudeste
    # ── Campos Externos (Spawn — borda exterior do grid) ────────────────────
    # As células da borda y=0/y=19 são ocupadas por torres e muralhas.
    # Os campos mapeiam para as 2 primeiras/últimas linhas do grid para efeito de spawn.
    # obter_zona_por_coordenada retorna muralha/torre primeiro (definidas antes), portanto
    # os campos só são usados pelo sistema de spawn com animação de "entrada da borda".
    "campo_norte":    (0,  0, 19,  1),   # 2 linhas top — borda exterior norte
    "campo_sul":      (0, 18, 19, 19),   # 2 linhas bot — borda exterior sul
    "campo_oeste":    (0,  0,  1, 19),   # 2 colunas left — borda exterior oeste
    "campo_leste":    (18, 0, 19, 19),   # 2 colunas right — borda exterior leste
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


CUSTO_ADICIONAL_SLOT = {
    0: {},
    1: {"couro": 1},
    2: {"metal": 1},
    3: {"madeira": 1},
    4: {"madeira": 1, "couro": 1}
}


def validar_alocar_recurso(estado, slot_id: int, pontos: int):
    # Primeiro valida se pode trabalhar e qual o recurso gerado
    ok, recurso, msg = validar_trabalhar(estado, pontos)
    if not ok:
        return False, None, msg

    slots = estado.get("slots_upgrade", [])
    if slot_id < 0 or slot_id >= len(slots):
        return False, None, "Slot inválido."
        
    slot = slots[slot_id]
    if slot.get("bloqueado"):
        return False, None, "Slot destruído!"
    if slot.get("adquirido"):
        return False, None, "Slot já adquirido!"

    # Verifica se o recurso atual da oficina ainda é necessário no custo total do slot
    custo_base = slot.get("custo", {})
    custo_adicional = CUSTO_ADICIONAL_SLOT.get(slot_id, {})
    total_requerido = custo_base.get(recurso, 0) + custo_adicional.get(recurso, 0)
    
    alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
    if alocados.get(recurso, 0) >= total_requerido:
        return False, None, f"Upgrade já tem o máximo necessário de {NOME_RECURSO.get(recurso, recurso)}!"

    return True, recurso, ""


def executar_alocar_recurso(estado, slot_id: int, recurso: str, qtd: int = 1) -> tuple[dict, list]:
    slots = [dict(s) for s in estado.get("slots_upgrade", [])]
    slot = slots[slot_id]
    
    # Inicializa recursos_alocados se não existir
    alocados = dict(slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0}))
    alocados[recurso] = alocados.get(recurso, 0) + qtd
    slot["recursos_alocados"] = alocados
    
    delta = {
        "slots_upgrade": slots,
        "pontos_trabalho": max(0, estado["pontos_trabalho"] - qtd),
    }
    
    logs = [("HEROI", f"+{qtd}x {NOME_RECURSO.get(recurso, recurso)} alocado sobre [{slot['nome']}].")]
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

    # Verifica se os recursos alocados atendem ao custo total (custo_base + custo_adicional_slot)
    custo_base = slot.get("custo", {})
    custo_adicional = CUSTO_ADICIONAL_SLOT.get(slot_id, {})
    
    alocados = slot.get("recursos_alocados", {"madeira": 0, "couro": 0, "metal": 0})
    
    for res in ["madeira", "couro", "metal"]:
        requerido = custo_base.get(res, 0) + custo_adicional.get(res, 0)
        if alocados.get(res, 0) < requerido:
            return False, f"Upgrade incompleto. Falta alocar recursos."

    if idx_carta_queimar < 0 or idx_carta_queimar >= len(mao):
        return False, "Escolha carta para queimar."
    if mao[idx_carta_queimar].get("tipo") == "ameaca":
        return False, "Não pode queimar ameaça."

    return True, ""


def executar_comprar_upgrade(estado, slot_id: int, idx_carta_queimar: int,
                             mao: list, deck_total: int) -> tuple[dict, list, list]:
    slots = [dict(s) for s in estado.get("slots_upgrade", [])]
    slot = slots[slot_id]

    # Zera os recursos alocados e marca como adquirido
    slots[slot_id]["recursos_alocados"] = {"madeira": 0, "couro": 0, "metal": 0}
    slots[slot_id]["adquirido"] = True
    
    # Remove permanentemente da mão
    nova_mao = [c for i, c in enumerate(mao) if i != idx_carta_queimar]

    delta = {
        "slots_upgrade": slots,
    }
    logs = [
        ("HEROI", f"Upgrade comprado: [{slot['nome']}]!"),
        ("HEROI", f"Carta '{mao[idx_carta_queimar]['nome']}' sacrificada permanentemente."),
    ]
    return delta, logs, nova_mao
