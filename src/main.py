from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import create_tables
from .config import settings
from .routes import health, ingest, ask, tasks, status

# Create tables on startup
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="AI Work OS",
    description="Minimal AI Work OS for document ingestion, task extraction, and Q&A",
    version="0.1.0"
)

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