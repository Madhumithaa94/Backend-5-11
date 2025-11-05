import uuid
import asyncio
from typing import Dict, Optional
from .models import SessionRecord, SpeakerProfile

# Simple in-memory SessionManager; swap Redis for production caching.
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, SessionRecord] = {}
        # Per-session queues for each direction A->B and B->A
        self.queues: Dict[str, Dict[str, asyncio.Queue]] = {}
        self.lock = asyncio.Lock()

    async def create_session(self, speaker_a: SpeakerProfile, speaker_b: SpeakerProfile) -> SessionRecord:
        async with self.lock:
            sid = str(uuid.uuid4())
            record = SessionRecord(session_id=sid, speaker_a=speaker_a, speaker_b=speaker_b)
            self.sessions[sid] = record
            # Initialize queues
            self.queues[sid] = {
                "AtoB": asyncio.Queue(),
                "BtoA": asyncio.Queue()
            }
            return record

    async def get_session(self, session_id: str) -> Optional[SessionRecord]:
        return self.sessions.get(session_id)

    async def push_chunk(self, session_id: str, direction: str, chunk: dict):
        """
        chunk must contain at least: chunk_id, audio_bytes (or reference), metadata
        direction: "AtoB" or "BtoA"
        """
        q = self.queues[session_id][direction]
        await q.put(chunk)

    async def pop_chunk(self, session_id: str, direction: str, timeout: Optional[float] = None):
        q = self.queues[session_id][direction]
        if timeout is None:
            item = await q.get()
            return item
        try:
            item = await asyncio.wait_for(q.get(), timeout=timeout)
            return item
        except asyncio.TimeoutError:
            return None

    async def close_session(self, session_id: str):
        async with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].status = "closed"
                # Optionally drain and remove queues
                self.queues.pop(session_id, None)
                self.sessions.pop(session_id, None)
