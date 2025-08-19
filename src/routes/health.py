from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import time
from datetime import datetime
from typing import Dict, Any

from ..database import get_db_session
from ..config import settings
from ..logging_config import get_logger
from ..rate_limiting import health_endpoint_limit

router = APIRouter()
logger = get_logger(__name__)

@router.get("/healthz")
@health_endpoint_limit()
async def health_check(request: Request):
    """Basic health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "ok"}

@router.get("/health/detailed")
@health_endpoint_limit()
async def detailed_health_check(request: Request, db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Detailed health check with database and LLM connectivity"""
    logger.info("Detailed health check requested")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database connectivity check
    try:
        # Simple query to check DB connection
        result = db.execute(text("SELECT 1")).fetchone()
        if result and result[0] == 1:
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
            logger.debug("Database health check passed")
        else:
            raise Exception("Unexpected query result")
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
        logger.error("Database health check failed", extra={"error": str(e)})
    
    # LLM API connectivity check
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test API endpoint availability
            response = await client.get(
                f"{settings.openai_base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"}
            )
            
            if response.status_code == 200:
                health_status["checks"]["llm_api"] = {
                    "status": "healthy",
                    "message": "LLM API connection successful",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
                logger.debug("LLM API health check passed")
            else:
                health_status["checks"]["llm_api"] = {
                    "status": "unhealthy",
                    "message": f"LLM API returned status {response.status_code}"
                }
                health_status["status"] = "degraded"
                logger.warning("LLM API health check degraded", extra={"status_code": response.status_code})
                
    except Exception as e:
        health_status["checks"]["llm_api"] = {
            "status": "unhealthy",
            "message": f"LLM API connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"
        logger.error("LLM API health check failed", extra={"error": str(e)})
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/health/ready")
@health_endpoint_limit()
async def readiness_check(request: Request, db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint"""
    try:
        # Quick database check
        db.execute(text("SELECT 1")).fetchone()
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception as e:
        logger.error("Readiness check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail={"status": "not_ready", "error": str(e)})

@router.get("/health/live")
@health_endpoint_limit()
async def liveness_check(request: Request) -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": time.time()
    }