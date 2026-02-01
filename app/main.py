from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest
from app.core.security import get_api_key

app = FastAPI(title="Honeypot API")

# -------------------- CORS (SAFE DEFAULT) --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTERS --------------------
app.include_router(router)

# -------------------- HEALTH CHECK --------------------
@app.get("/")
async def read_root():
    return {
        "status": "active",
        "message": "Honeypot API is running. Send POST requests to /"
    }

# -------------------- MAIN ENTRY --------------------
@app.post("/", dependencies=[Depends(get_api_key)])
async def handle_root_post(request: Request):
    data = {}

    # 1️⃣ Try JSON
    try:
        data = await request.json()
        if not isinstance(data, dict):
            data = {"message": str(data)}
    except Exception:
        pass

    # 2️⃣ Try form-data
    if not data:
        try:
            form = await request.form()
            for k in ["message", "input", "text", "content", "prompt"]:
                if k in form and form[k]:
                    data = {"message": form[k]}
                    break
        except Exception:
            pass

    # 3️⃣ Try raw body
    if not data:
        body = await request.body()
        text = body.decode("utf-8", errors="ignore").strip()
        if text:
            data = {"message": text}

    # 4️⃣ Query params fallback
    if not data:
        qp = dict(request.query_params)
        for k in ["message", "input", "text", "content", "prompt"]:
            if k in qp and qp[k]:
                data = {"message": qp[k]}
                break

    # 5️⃣ Absolute fallback
    if not data:
        data = {"message": "Ping"}

    # 6️⃣ Schema validation
    model = HoneypotRequest(**data)

    return await interact(model)
