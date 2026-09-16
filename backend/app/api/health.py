from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health():
    db_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "provider": settings.MODEL_PROVIDER,
        "model": (
            settings.OLLAMA_MODEL
            if settings.MODEL_PROVIDER.lower() == "ollama"
            else settings.ANTHROPIC_MODEL
        ),
        "database": db_status,
    }