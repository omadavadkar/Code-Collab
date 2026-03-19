from typing import Dict, Set
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# room_id -> set of WebSocket
connections: Dict[str, Set[WebSocket]] = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    room = connections.setdefault(room_id, set())
    room.add(websocket)
    try:
        while True:
            # Only accept text frames; will raise on binary
            data = await websocket.receive_text()

            # Broadcast to all others in the room
            targets = [ws for ws in list(room) if ws is not websocket]
            if not targets:
                continue

            async def send_safe(ws: WebSocket, msg: str):
                try:
                    await ws.send_text(msg)
                except Exception:
                    # If a client is dead, schedule removal
                    try:
                        room.remove(ws)
                    except KeyError:
                        pass

            await asyncio.gather(*(send_safe(ws, data) for ws in targets))
    except WebSocketDisconnect:
        # Client disconnected gracefully
        pass
    except Exception as e:
        # Log unexpected errors if you have logging configured
        # print(f"Unexpected WS error in room {room_id}: {e}")
        pass
    finally:
        # Ensure cleanup
        try:
            room.remove(websocket)
        except KeyError:
            pass
        # Remove the room entry if empty to avoid leaks
        if not room:
            connections.pop(room_id, None)