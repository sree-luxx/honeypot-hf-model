import os
from fastapi import FastAPI, Request, Header, HTTPException
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
app = FastAPI(title="Honeypot API", docs_url="/docs")

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

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST", "OPTIONS"])
async def honeypot_interact(
    request: Request,
    x_api_key: str = Header(None)
):
    # ---------- AUTH ----------
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # ---------- MESSAGE EXTRACTION (NO VALIDATION FAILURES) ----------
    message = None

    # 1️⃣ Query params (hackathon UIs love this)
    qp = dict(request.query_params)
    for key in ["message", "SCAMMER", "text", "input", "query", "content", "prompt"]:
        if key in qp and qp[key]:
            message = qp[key]
            break

    # 2️⃣ Try JSON (if present)
    if not message:
        try:
            body = await request.json()
            if isinstance(body, dict):
                for key in ["message", "SCAMMER", "text", "input", "query", "content", "prompt"]:
                    if key in body and body[key]:
                        message = str(body[key])
                        break
        except:
            pass

    # 3️⃣ Try form-data
    if not message:
        try:
            form = await request.form()
            for key in ["message", "SCAMMER", "text", "input", "query", "content", "prompt"]:
                if key in form and form[key]:
                    message = str(form[key])
                    break
        except:
            pass

    # 4️⃣ Raw body fallback
    if not message:
        try:
            raw = await request.body()
            if raw:
                message = raw.decode("utf-8", errors="ignore").strip()
        except:
            pass

    # 5️⃣ Absolute fallback (never fail)
    if not message:
        message = "Hello"

    # ---------- SCAM PIPELINE ----------
    detection = detect_scam(message)

    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except Exception:
        reply = "I didn’t quite catch that—could you clarify?"

    memory.add("agent", reply)

    intel = extractor.extract(message)

    # ---------- RESPONSE ----------
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

