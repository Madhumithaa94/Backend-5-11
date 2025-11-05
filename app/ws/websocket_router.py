import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from ..api.sessions import MANAGER
from ..core.session_manager import SessionManager

router = APIRouter()

# Each client will connect to /ws/{session_id}?side=A or ?side=B
@router.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str, side: str):
    """
    side must be "A" or "B"
    """
    await websocket.accept()
    try:
        session = await MANAGER.get_session(session_id)
        if not session:
            await websocket.send_text(json.dumps({"error": "Session not found"}))
            await websocket.close()
            return

        direction_in = "AtoB" if side == "A" else "BtoA"  # incoming chunks to be routed
        direction_out = "BtoA" if side == "A" else "AtoB" # outgoing processed chunks for this connection

        # background task that sends processed outputs from the opposite queue to this client
        async def sender_task():
            while True:
                chunk = await MANAGER.pop_chunk(session_id, direction_out, timeout=10)
                if chunk is None:
                    # timeout - send keepalive or continue
                    try:
                        await websocket.send_text(json.dumps({"type": "keepalive"}))
                    except:
                        break
                    continue
                # chunk is expected to have 'chunk_id' and 'payload' (e.g., text or tts audio uri/base64)
                await websocket.send_text(json.dumps({"type": "translated", "chunk": chunk}))

        send_task = asyncio.create_task(sender_task())

        # receive loop: get raw audio chunks from client, forward for processing
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            # expected message shape:
            # {"type": "chunk", "chunk_id": "<id>", "audio_ref": "<base64 or s3uri>", "meta": {...}}
            if msg.get("type") == "chunk":
                chunk_meta = {
                    "chunk_id": msg.get("chunk_id"),
                    "audio_ref": msg.get("audio_ref"),  # could be base64 or S3 URI
                    "meta": msg.get("meta", {})
                }
                # Push into manager queue for processing pipeline (A->B or B->A)
                await MANAGER.push_chunk(session_id, direction_in, chunk_meta)
                # A worker elsewhere should pick this up, run STT->MT->TTS and push result to opposite queue
                await websocket.send_text(json.dumps({"type": "ack", "chunk_id": msg.get("chunk_id")}))
            elif msg.get("type") == "close":
                break

        send_task.cancel()
    except WebSocketDisconnect:
        # cleanup if needed
        pass
