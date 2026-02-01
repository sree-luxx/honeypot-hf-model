from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.scam_detector import detect_scam
from app.core.agent import HoneypotAgent
from app.core.extractor import IntelExtractor
from app.core.memory import ConversationMemory
from app.schemas.response import HoneypotRequest, HoneypotResponse
from app.core.security import get_api_key

router = APIRouter()

agent = HoneypotAgent()
extractor = IntelExtractor()
memory = ConversationMemory()

async def interact(body: HoneypotRequest):
    # Core logic extracted to be reusable
    message = body.message or "Ping"

    memory.add("scammer", message)

    detection = detect_scam(message)

    reply = ""
    try:
        # Always generate a reply to keep the conversation going, even if not explicitly a scam
        reply = await agent.generate_reply(memory.context(), message)
        memory.add("agent", reply)
    except Exception as e:
        # Fail gracefully if local LLM errors out
        print(f"Reply generation failed: {str(e)}")
        
    intel = extractor.extract(message)

    return HoneypotResponse(
        is_scam=detection["is_scam"],
        confidence=detection["confidence"],
        agent_reply=reply,
        extracted_intel=intel
    )

@router.post("/honeypot/interact", response_model=HoneypotResponse, dependencies=[Depends(get_api_key)])
async def handle_interact_post(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
        try:
            form = await request.form()
            candidate = None
            for k in ["message", "input", "text", "content", "prompt"]:
                if k in form and form[k]:
                    candidate = form[k]
                    break
            if candidate is not None:
                data = {"message": candidate}
            else:
                body_bytes = await request.body()
                text = body_bytes.decode("utf-8", errors="ignore")
                data = {"message": text} if text else {}
        except Exception:
            body_bytes = await request.body()
            text = body_bytes.decode("utf-8", errors="ignore")
            data = {"message": text} if text else {}

    try:
        if not isinstance(data, dict):
             data = {"message": str(data)}
        if not data:
             data = {"message": "Ping"}
        qp = dict(request.query_params)
        for k in ["message", "input", "text", "content", "prompt"]:
            if k in qp and qp[k] and not data.get("message"):
                data["message"] = qp[k]
                break
        model = HoneypotRequest(**data)
    except Exception:
        model = HoneypotRequest(message="Ping")

    return await interact(model)
