from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import requirements, models, health

app = FastAPI(title="Business Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(requirements.router, prefix="/api/v1/requirements")
app.include_router(models.router, prefix="/api/v1/models")

@app.get("/")
async def root():
    return {"ok": True}