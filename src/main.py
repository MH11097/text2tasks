from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid
import time

from .database import create_tables
from .config import settings
from .logging_config import setup_logging, get_logger
from .rate_limiting import limiter, custom_rate_limit_handler
from .security import SecurityHeadersMiddleware, RequestSizeMiddleware
from .routes import health, ingest, ask, tasks, status, task_hierarchy, resources, contextual_ask

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Create tables on startup
create_tables()
logger.info("Database tables created successfully")

# Initialize FastAPI app
app = FastAPI(
    title="AI Work OS",
    description="Minimal AI Work OS for document ingestion, task extraction, and Q&A",
    version="0.1.0"
)

# Setup rate limiting
app.state.limiter = limiter
app.add_exception_handler(429, custom_rate_limit_handler)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeMiddleware, max_size=1024 * 1024)  # 1MB limit

# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Log request start
    start_time = time.time()
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log request completion
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, tags=["ingestion"])
app.include_router(ask.router, tags=["qa"])
app.include_router(tasks.router, tags=["tasks"])
app.include_router(status.router, tags=["status"])
app.include_router(task_hierarchy.router, tags=["task-hierarchy"])
app.include_router(resources.router, tags=["resource-management"])
app.include_router(contextual_ask.router, tags=["contextual-qa"])

# Serve static files (UI)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serve the main UI page"""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    index_file = os.path.join(static_dir, "index.html")
    
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {
            "message": "AI Work OS API",
            "version": "0.1.0",
            "endpoints": {
                "health": "/healthz",
                "ingest": "/ingest",
                "ask": "/ask", 
                "tasks": "/tasks",
                "status": "/status"
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)