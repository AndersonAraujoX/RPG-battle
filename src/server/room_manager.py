"""
src/server/room_manager.py — Gerenciador de Salas e Conexões WebSockets (RPG-battle)

Controla o ciclo de vida das salas de jogo, pool de conexões WebSocket por sala,
despacho de mensagens broadcast e personalizadas, e higienização de salas inativas.
"""
from __future__ import annotations

import asyncio
import json
import logging
import secrets
import string
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from fastapi import WebSocket

from src.server.session import CoopSession
from src.server.protocol import MessageType, ServerMessage

logger = logging.getLogger("coop_server.room_manager")


class Room:
    """
    Representa uma sala de jogo multijogador com sua sessão autoritativa e conexões ativas.
    """

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.created_at = time.time()
        self.session = CoopSession(room_id)
        self.connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    @property
    def player_count(self) -> int:
        return len(self.session.jogadores)

    @property
    def is_empty(self) -> bool:
        # Sala está vazia se não há conexões ativas
        return len(self.connections) == 0

    def add_connection(self, player_id: str, websocket: WebSocket):
        self.connections[player_id] = websocket

    def remove_connection(self, player_id: str):
        if player_id in self.connections:
            del self.connections[player_id]
        self.session.remove_player(player_id)

    async def send_personal(self, player_id: str, message: Dict[str, Any] | ServerMessage):
        """Envia mensagem direta para o WebSocket de um jogador específico."""
        ws = self.connections.get(player_id)
        if not ws:
            return
        data = message.to_dict() if isinstance(message, ServerMessage) else message
        try:
            await ws.send_json(data)
        except Exception as err:
            logger.warning(f"Erro ao enviar mensagem para player {player_id} na sala {self.room_id}: {err}")

    async def broadcast(self, message: Dict[str, Any] | ServerMessage, exclude_player_id: Optional[str] = None):
        """Envia mensagem para todos os jogadores conectados na sala."""
        data = message.to_dict() if isinstance(message, ServerMessage) else message
        dead_pids: List[str] = []
        for pid, ws in list(self.connections.items()):
            if exclude_player_id and pid == exclude_player_id:
                continue
            try:
                await ws.send_json(data)
            except Exception as err:
                logger.warning(f"Erro no broadcast para player {pid}: {err}")
                dead_pids.append(pid)

        for pid in dead_pids:
            self.remove_connection(pid)

    async def broadcast_state(self):
        """
        Envia o estado atualizado do jogo para cada jogador individualmente,
        garantindo privacidade de mão de cartas (Server Authority & Anti-Cheat).
        """
        dead_pids: List[str] = []
        for pid, ws in list(self.connections.items()):
            state_data = self.session.to_dict(for_player_id=pid)
            msg = {
                "type": MessageType.STATE_UPDATE.value,
                "payload": state_data,
            }
            try:
                await ws.send_json(msg)
            except Exception as err:
                logger.warning(f"Erro ao enviar state update para {pid}: {err}")
                dead_pids.append(pid)

        for pid in dead_pids:
            self.remove_connection(pid)


class RoomManager:
    """
    Gerencia o conjunto de todas as salas ativas no servidor.
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._lock = asyncio.Lock()

    def generate_room_code(self, length: int = 6) -> str:
        alphabet = string.ascii_uppercase + string.digits
        # Remove caracteres ambíguos (0, O, 1, I)
        filtered = [c for c in alphabet if c not in "0O1I"]
        return "".join(secrets.choice(filtered) for _ in range(length))

    def create_room(self, custom_room_id: Optional[str] = None) -> Room:
        room_id = (custom_room_id or self.generate_room_code()).upper().strip()
        if room_id in self.rooms:
            return self.rooms[room_id]
        room = Room(room_id)
        self.rooms[room_id] = room
        logger.info(f"Nova sala criada: {room_id}")
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id.upper().strip())

    def remove_room(self, room_id: str):
        r_id = room_id.upper().strip()
        if r_id in self.rooms:
            del self.rooms[r_id]
            logger.info(f"Sala removida: {r_id}")

    def cleanup_empty_rooms(self, max_idle_seconds: float = 300.0):
        """Remove salas sem conexões com tempo de criação superior a max_idle_seconds."""
        now = time.time()
        to_remove = [
            r_id for r_id, room in self.rooms.items()
            if room.is_empty and (now - room.created_at) > max_idle_seconds
        ]
        for r_id in to_remove:
            self.remove_room(r_id)

    def list_rooms(self) -> List[Dict[str, Any]]:
        return [
            {
                "room_id": room.room_id,
                "players_count": len(room.session.jogadores),
                "max_players": 4,
                "fase": room.session.fase,
                "created_at": room.created_at,
            }
            for room in self.rooms.values()
        ]
