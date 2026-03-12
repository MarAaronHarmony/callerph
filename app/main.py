import logging
import time

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.config import settings
from app.db.database import create_db_and_tables
from app.voice.handler import router as voice_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="CallerPH", version="0.1.0")

start_time = time.time()

# Include routers
app.include_router(voice_router)
app.include_router(api_router)


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()


@app.get("/health")
async def health_check():
    from sqlmodel import Session, text

    from app.db.database import get_engine

    try:
        with Session(get_engine()) as session:
            result = session.exec(
                text("SELECT COUNT(*) FROM clients WHERE is_active = 1")
            ).scalar()
            active_clients = int(result) if result else 0
    except Exception:
        active_clients = 0

    return {
        "status": "ok",
        "version": "0.1.0",
        "active_clients": active_clients,
        "uptime_seconds": int(time.time() - start_time),
        "debug": settings.debug,
    }
