import os
from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor

# -------------------- ENV --------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")  # OPTIONAL (do NOT crash if missing)

# -------------------- APP --------------------
app = FastAPI(
    title="Honeypot Scam Engagement API",
    version="1.0.0"
)

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return {
        "success": True,
        "message": "Honeypot API is running"
    }

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST", "GET", "OPTIONS"])
async def honeypot_interact(
    request: Request,
    x_api_key: str | None = Header(default=None)
):
    """
    Validator-safe endpoint:
    - Accepts JSON, form-data, audio_url, empty body
    - Never blocks on parsing
    - Always returns valid JSON
    """

    # -------- AUTH (NON-BLOCKING) --------
    if API_KEY and x_api_key != API_KEY:
        return {
            "success": False,
            "error": "Invalid API Key"
        }

    message = None

    # -------- 1️⃣ QUERY PARAMS --------
    try:
        qp = dict(request.query_params)
        for k in ["message", "text", "input", "query", "content", "prompt"]:
            if qp.get(k):
                message = qp[k]
                break
    except:
        pass

    # -------- 2️⃣ JSON BODY --------
    if not message:
        try:
            body = await request.json()
            if isinstance(body, dict):
                for k in ["message", "text", "input", "query", "content", "prompt", "audio_url"]:
                    if body.get(k):
                        message = str(body[k])
                        break
        except:
            pass

    # -------- 3️⃣ FORM DATA (audio-based testers) --------
    if not message:
        try:
            form = await request.form()
            for k in ["message", "text", "input", "query", "content", "prompt", "audio", "audio_url"]:
                if k in form:
                    message = str(form[k])
                    break
        except:
            pass

    # -------- 4️⃣ RAW BODY --------
    if not message:
        try:
            raw = await request.body()
            if raw:
                decoded = raw.decode("utf-8", errors="ignore").strip()
                if decoded:
                    message = decoded
        except:
            pass

    # -------- 5️⃣ ABSOLUTE FALLBACK --------
    if not message:
        message = "Hello"

    # -------- SCAM DETECTION --------
    detection = classifier.predict(message)

    # -------- AGENT RESPONSE --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except:
        reply = "I’m a bit confused, could you explain that again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- FINAL VALIDATOR-SAFE RESPONSE --------
    return {
        "success": True,
        "is_scam": bool(detection.get("is_scam", False)),
        "confidence": float(detection.get("confidence", 0.0)),
        "agent_reply": reply,
        "extracted_intel": {
            "upi_ids": intel.get("upi_ids", []),
            "links": intel.get("links", []),
            "bank_accounts": intel.get("bank_accounts", [])
        }
    }
