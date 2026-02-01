from fastapi import FastAPI, Request, Depends
from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest
from app.core.security import get_api_key
import json
from typing import Dict, Any

app = FastAPI()

app.include_router(router)

@app.get("/")
async def read_root():
    return {"status": "active", "message": "Honeypot API is running. Send POST requests to / or /honeypot/interact"}

@app.post("/", dependencies=[Depends(get_api_key)])
async def handle_root_post(request: Request):
    try:
        # Try to parse as JSON first
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

    # Create schema object (this handles normalization via the validator we added)
    try:
        # Ensure data is a dict
        if not isinstance(data, dict):
             data = {"message": str(data)}
        
        # If data is empty, validator will handle it or we set default
        if not data:
            data = {"message": "Ping"}
        
        # Merge query params if present
        qp = dict(request.query_params)
        for k in ["message", "input", "text", "content", "prompt"]:
            if k in qp and qp[k] and not data.get("message"):
                data["message"] = qp[k]
                break
            
        model = HoneypotRequest(**data)
    except Exception as e:
        # Fallback for any validation error
        print(f"Schema validation failed: {e}")
        model = HoneypotRequest(message="Ping")

    return await interact(model)
