import json
from enum import StrEnum, auto
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.rooms import rooms

rooms_router = APIRouter(prefix="/rooms", tags=["Rooms"])


# --- Routes -----------------------------------------------------------------


class Action(StrEnum):
    SET_NAME = auto()
    VOTE = auto()
    REVEAL_ROOM = auto()
    RESET_ROOM = auto()
    RESET_USERS = auto()


class RoomCreateParams(BaseModel):
    id: UUID | None = None


@rooms_router.post("")
def create_room(params: RoomCreateParams) -> dict:
    room = rooms.create(str(params.id) if params.id else None)
    return {"room_id": room.id}


@rooms_router.get("/{room_id}")
def get_room() -> FileResponse:
    return FileResponse("static/index.html")


@rooms_router.websocket("/ws/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in rooms:
        await websocket.close(code=4000, reason="Room not found")
        return

    room = rooms[room_id]

    init_msg = await websocket.receive_text()

    room.connections.append(websocket)
    init_data: dict = json.loads(init_msg)
    user_id = str(init_data.get("userId"))
    user_name = str(init_data.get("userName"))
    room.set_name(user_id, user_name)

    await room.broadcast()

    try:
        while True:
            msg = await websocket.receive_text()
            data: dict = json.loads(msg)

            action = Action(str(data.get("action")))

            match action:
                case Action.SET_NAME:
                    if data["name"]:
                        room.set_name(user_id, data["name"])

                case Action.VOTE:
                    room.set_vote(user_id, data["value"])

                case Action.REVEAL_ROOM:
                    room.revealed = True

                case Action.RESET_ROOM:
                    room.reset()

                case Action.RESET_USERS:
                    room.remove_all_connections()

            await room.broadcast()

    except WebSocketDisconnect:
        await room.remove_connection(websocket, user_id)
