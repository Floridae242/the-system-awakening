"""The System — Awakening API entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="The System — Awakening API",
    version="0.1.0",
    description="Real-life RPG: Auth → Quest → Proof → Verify → Reward → Chest → Inventory → Growth",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "the-system-awakening-api", "version": "0.1.0"}
