from .utils import calcular_distancia

def verificar_condicoes_ataque(atacante, alvo, distancia, vantagem_inicial=False, desvantagem_inicial=False):
    """
    Verifica condições de D&D 5e e retorna flags atualizadas de vantagem/desvantagem
    e uma lista de mensagens de modificadores.
    """
    vantagem = vantagem_inicial
    desvantagem = desvantagem_inicial
    msg_modificadores = []

    # 1. Blinded (Cego)
    if atacante.tem_status("Cego"):
        desvantagem = True
        msg_modificadores.append("Cego (Atacante)")
    if alvo.tem_status("Cego"):
        vantagem = True
        msg_modificadores.append("Cego (Alvo)")

    # 2. Poisoned (Envenenado)
    if atacante.tem_status("Envenenado"):
        desvantagem = True
        msg_modificadores.append("Envenenado")
        
    # 3. Prone (Caído)
    if atacante.tem_status("Caído"):
        desvantagem = True
        msg_modificadores.append("Caído (Atacante)")
    if alvo.tem_status("Caído"):
        if distancia <= 1.5:
            vantagem = True
            msg_modificadores.append("Alvo Caído (Perto)")
        else:
            desvantagem = True
            msg_modificadores.append("Alvo Caído (Longe)")
    
    # 4. Invisible (Invisível)
    if atacante.tem_status("Invisível"):
        vantagem = True
        msg_modificadores.append("Invisível")
    if alvo.tem_status("Invisível") and not atacante.tem_status("Ver o Invisível"):
        desvantagem = True
        msg_modificadores.append("Alvo Invisível")
        
    # 5. Paralyzed / Stunned / Unconscious / Petrified (Auto Advantage)
    if alvo.tem_status("Paralisado") or alvo.tem_status("Atordoado") or alvo.estado == "INCONSCIENTE" or alvo.tem_status("Petrificado"):
        vantagem = True
        msg_modificadores.append("Alvo Incapacitado/Petrificado")

    # 6. Frightened (Assustado)
    if atacante.tem_status("Assustado"):
        desvantagem = True
        msg_modificadores.append("Assustado")
        
    # 7. Restrained (Contido) - Often caused by Entangle or Grappler Pin
    if atacante.tem_status("Contido"):
        desvantagem = True
        msg_modificadores.append("Contido (Atacante)")
    if alvo.tem_status("Contido"):
        vantagem = True
        msg_modificadores.append("Contido (Alvo)")

    # 8. Dodge (Esquiva)
    if alvo.tem_status("Esquiva"):
        desvantagem = True
        msg_modificadores.append("Esquiva (Alvo)")

    # 9. Help Target (Alvo de Ajuda)
    if alvo.tem_status("Alvo de Ajuda"):
        vantagem = True
        msg_modificadores.append("Alvo de Ajuda")  
        # Note: Help usually applies to the next attack only. Character logic should remove this status after being hit or turn end.
        # Status Effect system handles turn duration. Hit duration logic needs addition if specific.
        # For simple implementation, it lasts 1 turn (until start of next turn of helper), granting advantage to everyone?
        # D&D RAW: "First attack roll made against it".
        # We need to remove status after attack?
        # Let's keep it simple: 1 turn advantage. Or try to remove it in Personagem.atacar?
        # Personagem.atacar logic is better place to remove "One Time" buffs on target.

    return vantagem, desvantagem, msg_modificadores

    return vantagem, desvantagem, msg_modificadores

def verificar_critico_automatico(atacante, alvo, distancia, rolagem, total_ataque, ac_alvo):
    """
    Verifica se o ataque é um crítico automático (Ex: Alvo Paralisado a 1.5m).
    """
    is_critico = (rolagem == 20)
    msg = None
    
    if (alvo.tem_status("Paralisado") or alvo.estado == "INCONSCIENTE") and distancia <= 1.5 and total_ataque >= ac_alvo:
        is_critico = True
        msg = "CRÍTICO AUTOMÁTICO (Paralisia)"
        
    return is_critico, msg
