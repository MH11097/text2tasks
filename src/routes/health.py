from fastapi import APIRouter
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/healthz")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "ok"}