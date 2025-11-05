from fastapi import APIRouter, HTTPException
from ..core.session_manager import SessionManager
from ..core.models import SpeakerProfile

router = APIRouter(prefix="/sessions", tags=["sessions"])

# For simplicity expose a singleton manager; better to instantiate via DI
MANAGER = SessionManager()

@router.post("/create")
async def create_session(speaker_a_id: str, speaker_b_id: str):
    from .speakers import SPEAKER_STORE
    a = SPEAKER_STORE.get(speaker_a_id)
    b = SPEAKER_STORE.get(speaker_b_id)
    if not a or not b:
        raise HTTPException(status_code=404, detail="Speaker(s) not found")
    record = await MANAGER.create_session(a, b)
    return {"session_id": record.session_id}
