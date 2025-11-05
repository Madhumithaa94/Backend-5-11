from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import uuid

app = FastAPI(title="Dual-Lane Conversation Backend", version="1.0")

# Temporary in-memory store (will later move to Redis/DB)
active_sessions = {}
speaker_profiles = {}


@app.get("/")
def root():
    return {"message": "Backend is running successfully ✅"}


# --------------------------
# 1) Speaker Session Handling
# --------------------------
@app.post("/register-speaker/")
def register_speaker(name: str = Form(...)):
    speaker_id = str(uuid.uuid4())
    speaker_profiles[speaker_id] = {"name": name}

    return {
        "status": "registered",
        "speaker_id": speaker_id,
        "name": name
    }


@app.post("/start-session/")
def start_session(speaker_id: str = Form(...)):
    if speaker_id not in speaker_profiles:
        return {"error": "Speaker not found"}

    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {"speaker_id": speaker_id, "chunks": []}

    return {
        "status": "session_started",
        "session_id": session_id,
        "speaker_id": speaker_id
    }


# --------------------------
# 2) Audio Processing (Placeholder)
# --------------------------
@app.post("/process-chunk/")
async def process_chunk(
    session_id: str = Form(...),
    audio: UploadFile = File(...)
):
    if session_id not in active_sessions:
        return {"error": "Invalid session_id"}

    # Store chunk reference (later: run STT → MT → TTS pipeline)
    active_sessions[session_id]["chunks"].append(audio.filename)

    return {
        "status": "chunk_received",
        "session_id": session_id,
        "stored_chunk_count": len(active_sessions[session_id]["chunks"])
    }


# --------------------------
# 3) End Session
# --------------------------
@app.post("/end-session/")
def end_session(session_id: str = Form(...)):
    if session_id not in active_sessions:
        return {"error": "Invalid session_id"}

    del active_sessions[session_id]

    return {"status": "session_ended", "session_id": session_id}
