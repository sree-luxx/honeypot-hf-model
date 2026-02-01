from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest

app = FastAPI(title="Honeypot API")

# Dummy dependency if not defined elsewhere
async def get_api_key():
    return "valid-key"

# Mount static files
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

# -------------------- MAIN ENDPOINT --------------------
@app.post("/")
async def honeypot_entry(
    payload: HoneypotRequest,
    _: str = Depends(get_api_key)
):
    return await interact(payload)
