import os
from typing import Any, Dict, Union

from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.core.scam_detector import detect_scam
from app.core.extractor import IntelExtractor

# -------------------- ENV --------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

# -------------------- APP --------------------
app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CORE --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
extractor = IntelExtractor()

# -------------------- HEALTH --------------------
@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

@app.post("/honeypot/interact")
async def honeypot_interact(
    payload: Union[str, Dict[str, Any]] = Body(...),
    x_api_key: str = Header(None)
):
    # -------- AUTH --------
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # -------- MESSAGE EXTRACTION (HACKATHON-COMPATIBLE) --------
    message = None

    # Case 1: raw string
    if isinstance(payload, str):
        message = payload

    # Case 2: structured JSON
    elif isinstance(payload, dict):
        # Hackathon format
        if isinstance(payload.get("message"), dict):
            message = payload["message"].get("text")

        # Fallbacks (keep your robustness)
        if not message:
            message = (
                payload.get("message")
                or payload.get("text")
                or payload.get("input")
                or payload.get("query")
                or payload.get("prompt")
                or payload.get("content")
            )

        if not message and "data" in payload and isinstance(payload["data"], dict):
            message = payload["data"].get("message")

    if not isinstance(message, str):
        raise HTTPException(status_code=400, detail="Invalid request body")

    message = message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")

    # -------- SCAM DETECTION --------
    detection = detect_scam(message)

    # -------- AGENT LOGIC --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except Exception as e:
        print("Agent error:", e)
        reply = "Sorry, can you explain that again?"

    memory.add("agent", reply)

    # -------- RESPONSE (STRICT HACKATHON FORMAT) --------
    return {
        "status": "success",
        "reply": reply
    }
