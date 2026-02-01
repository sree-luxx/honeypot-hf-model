from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest
from app.core.security import get_api_key

app = FastAPI()

app.include_router(router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")

@app.post("/", dependencies=[Depends(get_api_key)])
async def handle_root_post(body: HoneypotRequest):
    return await interact(body)
