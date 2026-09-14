"""
src/server/app.py — Aplicação FastAPI e Endpoints WebSockets (RPG-battle Co-op)

Fornece a API REST para consulta e criação de salas, gerenciamento de heróis
e o endpoint WebSocket para sincronização tática autoritativa em tempo real.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.server.protocol import (
    MessageType,
    ServerMessage,
)
from src.server.room_manager import RoomManager
from src.server.session import CLASSES_HEROIS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("coop_server")

app = FastAPI(
    title="RPG-battle Co-op Server",
    description="Servidor Autoritativo de Combate Tático Co-op Online para RPG-battle",
    version="1.0.0",
)

# Configuração de CORS para permitir acesso local ou via rede local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_manager = RoomManager()

# Detalhes informativos dos heróis para o Lobby
HERO_INFO = [
    {
        "nome": "Aquele",
        "classe": "Guerreiro",
        "icone": "🌑",
        "sprite_url": "/assets/images/characters/heroes/Aquele.png",
        "hp_base": 50,
        "ac": 16,
        "descricao": "Guerreiro sombrio implacável com alto poder de absorção e contra-ataques brutais.",
        "especial": "Ataque Furioso & Vanguarda",
    },
    {
        "nome": "Stark",
        "classe": "Paladino",
        "icone": "🛡️",
        "sprite_url": "/assets/images/characters/heroes/paladino.png",
        "hp_base": 60,
        "ac": 18,
        "descricao": "Bastião inabalável da equipe, provê escudos divinos e proteção para aliados adjacentes.",
        "especial": "Aura de Proteção & Cura Sagrada",
    },
    {
        "nome": "Elden",
        "classe": "Mago",
        "icone": "✨",
        "sprite_url": "/assets/images/characters/heroes/mago.png",
        "hp_base": 35,
        "ac": 12,
        "descricao": "Conjurador arcano com alcance devastador de até 8 células no tabuleiro.",
        "especial": "Mísseis Arcanos & Chuva de Fogo",
    },
    {
        "nome": "Doom",
        "classe": "Ladino",
        "icone": "💀",
        "sprite_url": "/assets/images/characters/heroes/ladino.png",
        "hp_base": 42,
        "ac": 15,
        "descricao": "Assassino das sombras focado em golpes críticos e evasão letal.",
        "especial": "Ataque Furtivo & Passo Sombrio",
    },
    {
        "nome": "Gruu",
        "classe": "Bárbaro",
        "icone": "🪓",
        "sprite_url": "/assets/images/characters/heroes/barbaro.png",
        "hp_base": 65,
        "ac": 14,
        "descricao": "Tanque bruto que acumula Fúria ao receber dano para desferir golpes em área.",
        "especial": "Fúria Bárbara & Quebra de Crânios",
    },
    {
        "nome": "Kuro",
        "classe": "Ladino",
        "icone": "🗡️",
        "sprite_url": "/assets/images/characters/heroes/ladino.png",
        "hp_base": 40,
        "ac": 15,
        "descricao": "Especialista ágil em armadilhas, mobilidade extrema e roubo de recursos.",
        "especial": "Truques Ágeis & Facada Rápida",
    },
    {
        "nome": "Darwin",
        "classe": "Druida",
        "icone": "🌿",
        "sprite_url": "/assets/images/characters/heroes/druida.png",
        "hp_base": 48,
        "ac": 14,
        "descricao": "Conexão primal com as matas, escava e manipula terrenos com velocidade inigualável.",
        "especial": "Crescimento Espinhoso & Regeneração",
    },
]


# ── Rotas REST ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Retorna a saúde do servidor e total de salas."""
    return {
        "status": "ok",
        "active_rooms": len(room_manager.rooms),
        "total_heroes": len(CLASSES_HEROIS),
    }


@app.get("/api/heroes")
async def get_heroes():
    """Lista todos os heróis disponíveis com atributos e informações de classe."""
    return HERO_INFO


@app.get("/api/rooms")
async def list_rooms():
    """Lista todas as salas ativas."""
    room_manager.cleanup_empty_rooms()
    return room_manager.list_rooms()


@app.post("/api/rooms")
async def create_room(room_id: Optional[str] = None):
    """Cria uma nova sala de jogo multijogador."""
    room = room_manager.create_room(custom_room_id=room_id)
    return {
        "room_id": room.room_id,
        "fase": room.session.fase,
        "players_count": len(room.session.jogadores),
        "created_at": room.created_at,
    }


# ── WebSocket Endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    player_id: str,
    player_name: str = Query("Aventureiro"),
):
    """
    Canal de comunicação bidirecional em tempo real para a partida Co-op.
    """
    await websocket.accept()
    room_id_upper = room_id.upper().strip()

    # Obtém ou cria a sala automaticamente ao conectar
    room = room_manager.get_room(room_id_upper)
    if not room:
        room = room_manager.create_room(custom_room_id=room_id_upper)

    # Adiciona conexão e jogador
    added = room.session.add_player(player_id=player_id, player_name=player_name)
    if not added:
        await websocket.send_json({
            "type": MessageType.ERROR.value,
            "payload": {"mensagem": "A sala atingiu o limite de 4 jogadores."},
        })
        await websocket.close()
        return

    room.add_connection(player_id, websocket)
    logger.info(f"Player {player_name} ({player_id}) conectado na sala {room.room_id}")

    # Notifica todos os jogadores com o estado atualizado
    await room.broadcast_state()

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            # ── SELECT_HERO ──
            if msg_type == MessageType.SELECT_HERO.value:
                hero_name = payload.get("hero_name")
                sucesso, motivo = room.session.select_hero(player_id, hero_name)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "SELECT_HERO", "motivo": motivo},
                    })

            # ── START_GAME ──
            elif msg_type == MessageType.START_GAME.value:
                sucesso, motivo = room.session.start_game()
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "START_GAME", "motivo": motivo},
                    })

            # ── SELECT_CARD ──
            elif msg_type == MessageType.SELECT_CARD.value:
                card_idx = payload.get("card_idx", -1)
                sucesso, motivo = room.session.select_card(player_id, card_idx)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "SELECT_CARD", "motivo": motivo},
                    })

            # ── MOVE_HERO ──
            elif msg_type == MessageType.MOVE_HERO.value:
                dx = payload.get("dest_x")
                dy = payload.get("dest_y")
                sucesso, motivo = room.session.move_hero(player_id, dx, dy)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "MOVE_HERO", "motivo": motivo},
                    })

            # ── ATTACK_TARGET ──
            elif msg_type == MessageType.ATTACK_TARGET.value:
                tx = payload.get("target_x")
                ty = payload.get("target_y")
                sucesso, motivo = room.session.attack_target(player_id, tx, ty)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "ATTACK_TARGET", "motivo": motivo},
                    })

            # ── WORK_ACTION (Minerar / Limpar) ──
            elif msg_type == MessageType.WORK_ACTION.value:
                tx = payload.get("target_x")
                ty = payload.get("target_y")
                sucesso, motivo = room.session.mine_action(player_id, tx, ty)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "WORK_ACTION", "motivo": motivo},
                    })

            # ── END_ROUND ──
            elif msg_type == MessageType.END_ROUND.value:
                sucesso, motivo = room.session.end_player_turn(player_id)
                if sucesso:
                    await room.broadcast_state()
                else:
                    await room.send_personal(player_id, {
                        "type": MessageType.ACTION_REJECTED.value,
                        "payload": {"acao": "END_ROUND", "motivo": motivo},
                    })

            # ── CHAT_MESSAGE ──
            elif msg_type == MessageType.CHAT_MESSAGE.value:
                texto = payload.get("text", "").strip()
                if texto:
                    pname = room.session.jogadores.get(player_id, {}).get("nome", player_name)
                    hname = room.session.jogadores.get(player_id, {}).get("hero_name")
                    prefix = f"💬 {pname}" if not hname else f"💬 {pname} ({hname})"
                    room.session.add_log(prefix, texto, "#c084fc")
                    await room.broadcast_state()

    except WebSocketDisconnect:
        logger.info(f"Player {player_id} desconectou da sala {room.room_id}")
    except Exception as exc:
        logger.warning(f"Exceção no WebSocket de {player_id}: {exc}")
    finally:
        room.remove_connection(player_id)
        await room.broadcast_state()
        room_manager.cleanup_empty_rooms()


# ── Frontend Static Files & Redirecionamento ─────────────────────────────────

assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

web_dir = Path(__file__).resolve().parent.parent.parent / "web" / "coop"
if web_dir.exists():
    app.mount("/coop", StaticFiles(directory=str(web_dir), html=True), name="coop")

    @app.get("/")
    async def index_redirect():
        return RedirectResponse(url="/coop/")
