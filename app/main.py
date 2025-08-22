"""Main application entry point with Clean Architecture"""

from fastapi import FastAPI, Depends, HTTPException, status, Header
from contextlib import asynccontextmanager
import logging

from shared.config.settings import settings
from infrastructure.logging.config import setup_logging
from infrastructure.logging.middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from infrastructure.database.connection import create_tables, add_indexes
from .dependencies import container

# Import API routes
from interfaces.api.v1.health import router as health_router
from interfaces.api.v1.ingest import router as ingest_router
from interfaces.api.v1.ask import router as ask_router
from interfaces.api.v1.tasks import router as tasks_router
from interfaces.api.v1.status import router as status_router
from interfaces.api.v1.documents import router as documents_router
from interfaces.api.v1.ai import router as ai_router
from interfaces.api.v1.export import router as export_router
from interfaces.api.v1.search import router as search_router
from interfaces.api.v1.dependencies import router as dependencies_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Text2Tasks application...")
    create_tables()
    add_indexes()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down Text2Tasks application...")

# Create FastAPI app
app = FastAPI(
    title="Text2Tasks - AI Work OS",
    description="Transform unstructured text into actionable tasks using AI",
    version="2.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add middleware
from fastapi.middleware.cors import CORSMiddleware

# Error logging middleware (first)
app.add_middleware(ErrorLoggingMiddleware)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware (last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5174"] if settings.debug else ["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(ingest_router, prefix="/api/v1", tags=["ingest"])
app.include_router(ask_router, prefix="/api/v1", tags=["ask"])
app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
app.include_router(documents_router, prefix="/api/v1", tags=["documents"])
app.include_router(ai_router, prefix="/api/v1", tags=["ai"])
app.include_router(export_router, prefix="/api/v1", tags=["export"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])
app.include_router(dependencies_router, prefix="/api/v1", tags=["dependencies"])
app.include_router(status_router, prefix="/api/v1", tags=["status"])

# API-only backend - no static file serving

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "clean"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )