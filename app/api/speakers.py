from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.status import HTTP_201_CREATED
from ..core.models import SpeakerProfile
from ..services.embeddings import generate_embedding_from_audio_bytes

router = APIRouter(prefix="/speakers", tags=["speakers"])

# In-memory store as example. Replace with DB in production.
SPEAKER_STORE = {}

@router.post("/register", status_code=HTTP_201_CREATED)
async def register_speaker(display_name: str, preferred_language: str = "en", sample_audio: UploadFile = File(None)):
    # 1) if audio sample provided, generate embedding
    embedding = None
    if sample_audio:
        audio_bytes = await sample_audio.read()
        embedding = generate_embedding_from_audio_bytes(audio_bytes)

    speaker_id = f"user_{len(SPEAKER_STORE) + 1}"
    profile = SpeakerProfile(speaker_id=speaker_id, display_name=display_name,
                             preferred_language=preferred_language, embedding=embedding)
    SPEAKER_STORE[speaker_id] = profile
    return {"speaker_id": speaker_id, "profile": profile.dict()}
