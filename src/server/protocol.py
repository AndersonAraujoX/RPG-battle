"""
src/server/protocol.py — Protocolo de Comunicação Co-op Online (RPG-battle)

Define os tipos de eventos, esquemas de dados e mensagens trocadas
entre clientes e o servidor autoritativo via WebSocket e REST.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    # Cliente -> Servidor
    JOIN_ROOM = "JOIN_ROOM"
    SELECT_HERO = "SELECT_HERO"
    START_GAME = "START_GAME"
    SELECT_CARD = "SELECT_CARD"
    MOVE_HERO = "MOVE_HERO"
    ATTACK_TARGET = "ATTACK_TARGET"
    WORK_ACTION = "WORK_ACTION"
    END_ROUND = "END_ROUND"
    CHAT_MESSAGE = "CHAT_MESSAGE"

    # Servidor -> Cliente
    ROOM_STATE = "ROOM_STATE"
    GAME_STARTED = "GAME_STARTED"
    CARD_LOCKED = "CARD_LOCKED"
    ROUND_RESOLVED = "ROUND_RESOLVED"
    STATE_UPDATE = "STATE_UPDATE"
    COMBAT_LOG = "COMBAT_LOG"
    ACTION_REJECTED = "ACTION_REJECTED"
    ERROR = "ERROR"


# ── Schemas de Entrada (Client -> Server) ────────────────────────────────────

class ClientMessage(BaseModel):
    type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)


class SelectHeroPayload(BaseModel):
    hero_name: str


class SelectCardPayload(BaseModel):
    card_idx: int


class MoveHeroPayload(BaseModel):
    dest_x: int
    dest_y: int


class AttackTargetPayload(BaseModel):
    target_x: int
    target_y: int
    habilidade: Optional[str] = None


class WorkActionPayload(BaseModel):
    target_x: int
    target_y: int
    tipo: str = "minerar"  # minerar, reparar, coletar


# ── Schemas de Saída (Server -> Client) ───────────────────────────────────

class ServerMessage(BaseModel):
    type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "payload": self.payload}
