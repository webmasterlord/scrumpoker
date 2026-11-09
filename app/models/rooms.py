import json
from typing import Dict, Self
from uuid import uuid4

from fastapi import WebSocket


class Room:
    """Single object managing state and WebSocket connections."""

    def __init__(self: Self, room_id: str):
        self.id = room_id
        self.votes: dict[str, dict] = {}
        self.revealed: bool = False
        self.connections: list[WebSocket] = []

    def json_state(self: Self) -> dict:
        """Return a JSON-serializable representation."""
        return {
            "votes": [
                {"name": v["name"], "vote": v["vote"] if self.revealed else ("😌" if v["vote"] is not None else "-")}
                for v in sorted(list(self.votes.values()), key=lambda v: v["name"])
            ],
            "revealed": self.revealed,
        }

    def set_name(self: Self, user_id: str, name: str):
        """Register or update user's name."""
        if user_id not in self.votes:
            self.votes[user_id] = {"name": name, "vote": None}
        else:
            self.votes[user_id]["name"] = name

    def set_vote(self: Self, user_id: str, value: str):
        """Record a user's vote."""
        if user_id not in self.votes:
            self.votes[user_id] = {"name": f"User-{user_id[:4]}", "vote": value}
        else:
            self.votes[user_id]["vote"] = value

    def remove_user(self: Self, user_id: str):
        self.votes.pop(user_id, None)

    def reset(self: Self) -> None:
        """Reset votes and hide results, keeping names."""
        for user in self.votes.values():
            user["vote"] = None
        self.revealed = False

    async def broadcast(self: Self):
        """Send the current state to all connected clients."""
        message = json.dumps(self.json_state())
        for conn in list(self.connections):
            try:
                await conn.send_text(message)
            except Exception:
                self.connections.remove(conn)

    async def remove_connection(self: Self, websocket: WebSocket, user_id: str):
        """Handle user disconnect."""
        if websocket in self.connections:
            self.connections.remove(websocket)
        self.remove_user(user_id)
        await self.broadcast()

    def remove_all_connections(self: Self) -> None:
        for websocket in self.connections:
            self.connections.remove(websocket)
        self.votes = {}


class Rooms:
    """Global room registry."""

    def __init__(self: Self) -> None:
        self._rooms: Dict[str, Room] = {}

    def create(self: Self, room_id: str | None = None) -> Room:
        room = Room(room_id or str(uuid4()))
        self._rooms[room.id] = room
        return room

    def __getitem__(self: Self, room_id: str) -> Room:
        return self._rooms[room_id]

    def __contains__(self, room_id: str) -> bool:
        return room_id in self._rooms


# Init global rooms var! Everything is done in memory.
rooms = Rooms()
