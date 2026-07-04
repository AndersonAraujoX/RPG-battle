import pygame
import math
import random

# Configurações de cores neon e premium
C_FACE_D20 = (30, 20, 60, 160)     # Roxo profundo translúcido
C_ARESTA_D20 = (180, 120, 255, 255) # Roxo neon
C_TEXTO_D20 = (255, 220, 100)      # Ouro brilhante

C_FACE_D6 = (80, 15, 15, 160)       # Vermelho translúcido profundo (Pedida pelo usuário)
C_ARESTA_D6 = (255, 60, 60, 255)   # Vermelho neon vibrante (Pedida pelo usuário)
C_TEXTO_D6 = (255, 220, 220)       # Vermelho claro brilhante

def rotacionar_x(x, y, z, angulo):
    rad = math.radians(angulo)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return x, y * cos_a - z * sin_a, y * sin_a + z * cos_a

def rotacionar_y(x, y, z, angulo):
    rad = math.radians(angulo)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a

def rotacionar_z(x, y, z, angulo):
    rad = math.radians(angulo)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return x * cos_a - y * sin_a, x * sin_a + y * cos_a, z

def animar_rolagem_dado(tela, tipo_dado="d20", resultado=None):
    """
    Roda uma animação 3D de um ou mais dados (d6 ou d20) no centro da tela.
    Gera um congelamento dramático de ~700ms.
    Se resultado for uma lista ou tupla, desenha múltiplos dados ao mesmo tempo.
    """
    largura, altura = tela.get_size()
    
    # Salva a tela atual para usar como fundo
    fundo = tela.copy()
    
    # Normaliza o resultado para uma lista de números
    if isinstance(resultado, (list, tuple)):
        resultados = list(resultado)
    else:
        if resultado is None:
            resultados = [random.randint(1, 20 if tipo_dado == "d20" else 6)]
        else:
            resultados = [resultado]
            
    num_dados = len(resultados)
    
    # Definição dos vértices e faces padrão
    if tipo_dado == "d6":
        vertices_base = [
            [-0.7, -0.7, -0.7],
            [ 0.7, -0.7, -0.7],
            [ 0.7,  0.7, -0.7],
            [-0.7,  0.7, -0.7],
            [-0.7, -0.7,  0.7],
            [ 0.7, -0.7,  0.7],
            [ 0.7,  0.7,  0.7],
            [-0.7,  0.7,  0.7]
        ]
        faces = [
            [0, 1, 2, 3], # Frente
            [1, 5, 6, 2], # Direita
            [5, 4, 7, 6], # Trás
            [4, 0, 3, 7], # Esquerda
            [3, 2, 6, 7], # Topo
            [4, 5, 1, 0]  # Base
        ]
        cor_face = C_FACE_D6
        cor_aresta = C_ARESTA_D6
        cor_texto = C_TEXTO_D6
    else:
        phi = (1 + math.sqrt(5)) / 2
        vertices_base = [
            [-1,  phi,  0],
            [ 1,  phi,  0],
            [-1, -phi,  0],
            [ 1, -phi,  0],
            [ 0, -1,  phi],
            [ 0,  1,  phi],
            [ 0, -1, -phi],
            [ 0,  1, -phi],
            [ phi, 0, -1],
            [ phi, 0,  1],
            [-phi, 0, -1],
            [-phi, 0,  1]
        ]
        for v in vertices_base:
            scale = 0.8
            v[0] *= scale
            v[1] *= scale
            v[2] *= scale
            
        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 1], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ]
        cor_face = C_FACE_D20
        cor_aresta = C_ARESTA_D20
        cor_texto = C_TEXTO_D20

    # Sons de rolagem de dados
    try:
        som_rolar = pygame.mixer.Sound("sons/dado_rolar.wav")
        som_fim = pygame.mixer.Sound("sons/dado_fim.wav")
    except:
        som_rolar = None
        som_fim = None

    if som_rolar:
        som_rolar.play()

    # Fontes
    fonte_num = pygame.font.SysFont("Impact", 80)
    fonte_num_borda = pygame.font.SysFont("Impact", 84)

    # Inicializa estados de rotação e velocidades independentes para cada dado
    dados_estado = []
    espacamento = 180
    
    # Distribuição dos centros horizontais dos dados
    centros_x = []
    if num_dados == 1:
        centros_x = [largura // 2]
    elif num_dados == 2:
        centros_x = [largura // 2 - espacamento // 2, largura // 2 + espacamento // 2]
    else:
        start_x = largura // 2 - (num_dados - 1) * espacamento // 2
        centros_x = [start_x + i * espacamento for i in range(num_dados)]

    for i in range(num_dados):
        dados_estado.append({
            "cx": centros_x[i],
            "cy": altura // 2,
            "ax": random.randint(0, 360),
            "ay": random.randint(0, 360),
            "az": random.randint(0, 360),
            "vx": random.uniform(15, 30),
            "vy": random.uniform(15, 30),
            "vz": random.uniform(15, 30),
            "resultado": resultados[i]
        })
    
    clock = pygame.time.Clock()
    total_frames = 45
    
    # Superfície para desenho translúcido
    overlay_3d = pygame.Surface((largura, altura), pygame.SRCALPHA)

    for frame in range(total_frames):
        # 1. Desenha o fundo e escurece levemente
        tela.blit(fundo, (0, 0))
        
        escurecer = pygame.Surface((largura, altura), pygame.SRCALPHA)
        alpha_escurecer = min(150, 50 + frame * 3)
        escurecer.fill((8, 10, 20, alpha_escurecer))
        tela.blit(escurecer, (0, 0))
        
        # Limpa overlay
        overlay_3d.fill((0, 0, 0, 0))
        
        # 2. Renderiza cada dado
        for dado in dados_estado:
            cx, cy = dado["cx"], dado["cy"]
            
            # Atualiza ângulos
            if frame < 30:
                dado["ax"] += dado["vx"]
                dado["ay"] += dado["vy"]
                dado["az"] += dado["vz"]
                dado["vx"] *= 0.95
                dado["vy"] *= 0.95
                dado["vz"] *= 0.95
            else:
                # Estabiliza suavemente
                dado["ax"] = dado["ax"] * 0.7 + 0.0 * 0.3
                dado["ay"] = dado["ay"] * 0.7 + 0.0 * 0.3
                dado["az"] = dado["az"] * 0.7 + 0.0 * 0.3

            # Escala do dado (efeito quique)
            escala = 100
            if frame < 15:
                escala = 180 - (frame * 5)
            elif frame < 30:
                escala = 105
            else:
                prog = (frame - 30) / 15
                escala = 105 + int(math.sin(prog * math.pi * 2.5) * 8 * (1 - prog))

            # Rotaciona vértices
            vertices_rotacionados = []
            for vx, vy, vz in vertices_base:
                vx, vy, vz = rotacionar_x(vx, vy, vz, dado["ax"])
                vx, vy, vz = rotacionar_y(vx, vy, vz, dado["ay"])
                vx, vy, vz = rotacionar_z(vx, vy, vz, dado["az"])
                vertices_rotacionados.append((vx, vy, vz))

            # Ordena faces (Painter's Algorithm)
            faces_ordenadas = []
            for face in faces:
                z_medio = sum(vertices_rotacionados[idx][2] for idx in face) / len(face)
                faces_ordenadas.append((z_medio, face))
            faces_ordenadas.sort(key=lambda item: item[0], reverse=True)

            # Desenha faces e arestas
            for z_val, face in faces_ordenadas:
                pontos_proj = []
                for idx in face:
                    px, py, pz = vertices_rotacionados[idx]
                    factor = 280 / (pz + 3.5)
                    x_proj = int(cx + px * factor * (escala / 100))
                    y_proj = int(cy - py * factor * (escala / 100))
                    pontos_proj.append((x_proj, y_proj))

                pygame.draw.polygon(overlay_3d, cor_face, pontos_proj)
                pygame.draw.polygon(overlay_3d, cor_aresta, pontos_proj, 3)

        # Blita todos os dados na tela
        tela.blit(overlay_3d, (0, 0))

        # 3. Desenha os números finais de cada dado (fade-in)
        if frame >= 25:
            alpha_texto = min(255, (frame - 25) * 15)
            
            for dado in dados_estado:
                cx, cy = dado["cx"], dado["cy"]
                txt = str(dado["resultado"])
                t_surface = fonte_num.render(txt, True, cor_texto)
                t_borda = fonte_num_borda.render(txt, True, (0, 0, 0))
                
                t_surface.set_alpha(alpha_texto)
                t_borda.set_alpha(alpha_texto)
                
                tela.blit(t_borda, (cx - t_borda.get_width() // 2, cy - t_borda.get_height() // 2))
                tela.blit(t_surface, (cx - t_surface.get_width() // 2, cy - t_surface.get_height() // 2))
            
            if frame == 25 and som_fim:
                som_fim.play()

        pygame.display.flip()
        clock.tick(60)

    # Pausa final
    pygame.time.wait(250)
