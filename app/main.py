import os
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
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
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- HEALTH --------------------
@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["GET", "POST", "OPTIONS"])
async def honeypot_interact(
    request: Request,
    x_api_key: str = Header(None)
):
    # -------- AUTH --------
    if not API_KEY:
        return {"success": False, "error": "Server misconfigured"}

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # -------- MESSAGE EXTRACTION (SAFE) --------
    message = None

    # 1️⃣ Query params (MOST RELIABLE)
    qp = dict(request.query_params)
    for key in ["message", "text", "input", "query", "content", "prompt"]:
        if key in qp and qp[key]:
            message = qp[key]
            break

    # 2️⃣ Raw body (NO JSON parsing)
    if not message:
        try:
            raw = await request.body()
            if raw:
                message = raw.decode("utf-8", errors="ignore").strip()
        except:
            pass

    # 3️⃣ Absolute fallback
    if not message:
        message = "Hello"

    # -------- SCAM DETECTION --------
    detection = classifier.predict(message)

    # -------- AGENT LOGIC --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except:
        reply = "Could you please explain that again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- FINAL RESPONSE --------
    return {
        "success": True,
        "result": {
            "is_scam": bool(detection.get("is_scam", False)),
            "confidence": float(detection.get("confidence", 0.0)),
            "agent_reply": reply,
            "extracted_intel": {
                "upi_ids": intel.get("upi_ids", []),
                "links": intel.get("links", []),
                "bank_accounts": intel.get("bank_accounts", [])
            }
        }
    }
