"""BKS Verse API — FastAPI app principale."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import verse, lineage, leaderboard, reel
from verse_engine.db import init_db

app = FastAPI(
    title="BKS Verse API",
    version="1.0.0",
    description="Dalla Poesia all'Oggetto — motore operativo",
)

@app.on_event("startup")
async def startup_event():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bakabo.club", "https://bakabo.myshopify.com", "https://verse.bakabo.club", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verse.router,       prefix="/verse",       tags=["verse"])
app.include_router(lineage.router,     prefix="/lineage",     tags=["lineage"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(reel.router,        prefix="/reel",        tags=["reel"])


@app.get("/health")
def health():
    return {"status": "ok", "system": "BKS Verse", "version": "1.0.0"}
