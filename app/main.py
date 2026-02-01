from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.schemas.response import HoneypotRequest
from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor
from app.config import CONFIDENCE_THRESHOLD
import os

app = FastAPI(title="Honeypot API")

# -------------------- GUVI API KEY --------------------
GUVI_API_KEY = os.getenv("GUVI_API_KEY")

def verify_guvi_api_key(x_api_key: str = Header(...)):
    if not GUVI_API_KEY or x_api_key != GUVI_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# -------------------- STATIC FILES --------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTES --------------------
app.include_router(router)

@app.get("/")
def health_check():
    return {
        "status": "active",
        "message": "Honeypot API running"
    }

# -------------------- CORE COMPONENTS --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- REQUIRED ENDPOINT --------------------
@app.post("/honeypot/interact")
async def honeypot_entry(
    payload: HoneypotRequest,
    _: None = Depends(verify_guvi_api_key)
):
    user_message = payload.message

    # 1️⃣ Scam detection
    scam_result = classifier.predict(user_message)

    # 2️⃣ Maintain conversation memory
    memory.add("scammer", user_message)
    context = memory.context()

    # 3️⃣ Generate honeypot reply
    reply = agent.generate_reply(context, user_message)
    memory.add("agent", reply)

    # 4️⃣ Extract intelligence
    extracted_intel = extractor.extract(user_message)

    # 5️⃣ Structured response (GUVI-compatible)
    return {
        "is_scam": scam_result["is_scam"],
        "confidence": scam_result["confidence"],
        "reply": reply,
        "extracted_intel": extracted_intel
    }
