from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict
import uuid
import os
from pathlib import Path

app = FastAPI(title="Dual-Lane Conversation Backend", version="1.0")

# Temporary in-memory store (will later move to Redis/DB)
active_sessions: Dict[str, dict] = {}
speaker_profiles: Dict[str, dict] = {}

# directory to save uploaded chunks (optional)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

    return {"status": "registered", "speaker_id": speaker_id, "name": name}


@app.post("/start-session/")
def start_session(speaker_id: str = Form(...)):
    if speaker_id not in speaker_profiles:
        raise HTTPException(status_code=404, detail="Speaker not found")

    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {"speaker_id": speaker_id, "chunks": []}

    return {"status": "session_started", "session_id": session_id, "speaker_id": speaker_id}


# --------------------------
# 2) Audio Processing (Placeholder)
# --------------------------
@app.post("/process-chunk/")
async def process_chunk(session_id: str = Form(...), audio: UploadFile = File(...)):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    # save the uploaded file to disk (safe consumption of UploadFile)
    filename = f"{session_id}_{uuid.uuid4().hex}_{audio.filename}"
    out_path = UPLOAD_DIR / filename

    try:
        with out_path.open("wb") as f:
            content = await audio.read()   # read the upload
            f.write(content)
    finally:
        await audio.close()

    # store reference to saved chunk path (or store metadata)
    active_sessions[session_id]["chunks"].append(str(out_path))

    return {
        "status": "chunk_received",
        "session_id": session_id,
        "stored_chunk_count": len(active_sessions[session_id]["chunks"]),
        "saved_path": str(out_path)
    }


# --------------------------
# 3) End Session
# --------------------------
@app.post("/end-session/")
def end_session(session_id: str = Form(...)):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    # optional: cleanup files associated with session
    chunks = active_sessions[session_id].get("chunks", [])
    for p in chunks:
        try:
            os.remove(p)
        except Exception:
            # ignore remove errors for now
            pass

    del active_sessions[session_id]

    return {"status": "session_ended", "session_id": session_id}
