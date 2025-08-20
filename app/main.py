"""Main application entry point with Clean Architecture"""

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging

from shared.config.settings import settings
from infrastructure.logging.config import setup_logging
from infrastructure.database.connection import create_tables, add_indexes
from .dependencies import container

# Import API routes
from interfaces.api.v1.health import router as health_router
from interfaces.api.v1.ingest import router as ingest_router
from interfaces.api.v1.ask import router as ask_router
from interfaces.api.v1.tasks import router as tasks_router
from interfaces.api.v1.status import router as status_router

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

# Add CORS middleware
if settings.debug:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(ingest_router, prefix="/api/v1", tags=["ingest"])
app.include_router(ask_router, prefix="/api/v1", tags=["ask"])
app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
app.include_router(status_router, prefix="/api/v1", tags=["status"])

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

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