"""Health check endpoints."""

from fastapi import APIRouter
from pathlib import Path

from api.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verify data files exist."""
    data_dir = Path(settings.data_dir)
    parquet_files = list(data_dir.glob("*.parquet"))

    return {
        "status": "ok",
        "data_dir": str(data_dir),
        "instruments": [f.stem for f in parquet_files],
        "ready": len(parquet_files) > 0,
    }
