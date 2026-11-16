from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.config import settings
from app.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    # Check database connectivity
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok",
        app="SaarthiFlow API",
        version="1.0.0",
        database=db_status,
        nemotronConfigured=bool(settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY != "your_nvidia_api_key_here"),
        port=settings.PORT,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SaarthiFlow API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }