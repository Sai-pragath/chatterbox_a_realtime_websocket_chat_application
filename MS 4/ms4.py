from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
import uvicorn

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # websocket -> { username, room }
        self.connections: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, username: str, room: str):
        self.connections[websocket] = {
            "username": username,
            "room": room
        }
        await self.broadcast(room, {
            "type": "system",
            "message": f"{username} joined {room} 👋"
        })

    def disconnect(self, websocket: WebSocket):
        return self.connections.pop(websocket, None)

    async def broadcast(self, room: str, data: dict):
        for ws, info in self.connections.items():
            if info["room"] == room:
                await ws.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        # Initial join message
        join_data = await websocket.receive_json()
        username = join_data.get("username", "Anonymous")
        room = join_data.get("room", "general")

        await manager.connect(websocket, username, room)

        while True:
            data = await websocket.receive_json()
            event = data.get("type")

            if event == "chat" and data.get("message", "").strip():
                await manager.broadcast(room, {
                    "type": "chat",
                    "username": username,
                    "message": data["message"],
                    "time": datetime.now().strftime("%I:%M %p")
                })

            elif event == "typing":
                await manager.broadcast(room, {
                    "type": "typing",
                    "username": username
                })

            elif event == "stop_typing":
                await manager.broadcast(room, {
                    "type": "stop_typing",
                    "username": username
                })

            elif event == "switch_room":
                old_room = room
                new_room = data.get("room")

                if new_room and new_room != old_room:
                    manager.connections[websocket]["room"] = new_room
                    room = new_room

                    await manager.broadcast(old_room, {
                        "type": "system",
                        "message": f"{username} left the room ❌"
                    })

                    await manager.broadcast(new_room, {
                        "type": "system",
                        "message": f"{username} joined the room 👋"
                    })

    except WebSocketDisconnect:
        user = manager.disconnect(websocket)
        if user:
            await manager.broadcast(user["room"], {
                "type": "system",
                "message": f"{user['username']} left the room ❌"
            })

if __name__ == "__main__":
    uvicorn.run("ms4:app", host="localhost", port=8000, reload=True)