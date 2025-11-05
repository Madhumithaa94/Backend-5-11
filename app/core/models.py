from typing import Optional, Dict, Any
from pydantic import BaseModel

class SpeakerProfile(BaseModel):
    speaker_id: str
    display_name: Optional[str] = None
    preferred_language: str = "en"
    embedding: Optional[str] = None  # base64 or serialized vector

class SessionRecord(BaseModel):
    session_id: str
    speaker_a: SpeakerProfile
    speaker_b: SpeakerProfile
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}
