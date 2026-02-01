from fastapi import APIRouter, HTTPException
from app.core.scam_detector import detect_scam
from app.core.agent import HoneypotAgent
from app.core.extractor import IntelExtractor
from app.core.memory import ConversationMemory
from app.schemas.response import HoneypotRequest, HoneypotResponse

router = APIRouter()

agent = HoneypotAgent()
extractor = IntelExtractor()
memory = ConversationMemory()

@router.post("/honeypot/interact", response_model=HoneypotResponse)
async def interact(body: HoneypotRequest):
    message = body.message

    memory.add("scammer", message)

    detection = detect_scam(message)

    reply = ""
    if detection["is_scam"]:
        try:
            reply = agent.generate_reply(memory.context(), message)
        except Exception as e:
            # Fail gracefully if local LLM errors out
            raise HTTPException(status_code=500, detail=f"Reply generation failed: {str(e)}")
        memory.add("agent", reply)

    intel = extractor.extract(message)

    return HoneypotResponse(
        is_scam=detection["is_scam"],
        confidence=detection["confidence"],
        agent_reply=reply,
        extracted_intel=intel
    )
