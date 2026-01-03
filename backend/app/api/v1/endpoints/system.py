from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@router.get("/version", tags=["System"])
async def get_version() -> dict[str, str]:
    """Get application version and environment."""
    return {
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
