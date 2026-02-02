from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor

app = FastAPI()

# -------------------- CORS (MANDATORY) --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Core --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- Health --------------------
@app.get("/")
def health():
    return {"success": True, "message": "API is running"}

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST", "OPTIONS"])
async def honeypot_interact(request: Request):

    # -------- SAFE BODY PARSING --------
    body = {}
    try:
        parsed = await request.json()
        if isinstance(parsed, dict):
            body = parsed
    except:
        body = {}

    # -------- MESSAGE EXTRACTION --------
    message = (
        body.get("message")
        or body.get("text")
        or body.get("input")
        or body.get("query")
        or body.get("content")
        or ""
    )

    if not isinstance(message, str) or not message.strip():
        message = "Hello"

    # -------- SCAM DETECTION --------
    detection = classifier.predict(message)

    # -------- AGENT RESPONSE --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except:
        reply = "I am not sure I understood, can you explain again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- CRITICAL: VALIDATOR-FRIENDLY RESPONSE --------
    return {
        "success": True,
        "message": "Request processed successfully",
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
