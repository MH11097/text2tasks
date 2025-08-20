"""Main entry point for Text2Tasks application"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Simple app without clean architecture for now - let's get it working first
app = FastAPI(
    title="Text2Tasks - AI Work OS",
    description="Transform unstructured text into actionable tasks using AI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve the main HTML page"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Text2Tasks API is running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "clean (in progress)"
    }

# Basic API endpoints to test
@app.get("/api/v1/health")
async def api_health():
    """API health check"""
    return {"status": "ok", "message": "API is working"}

@app.post("/api/v1/test")
async def test_endpoint():
    """Test endpoint"""
    return {"message": "Clean architecture migration in progress"}

if __name__ == "__main__":
    print("🚀 Starting Text2Tasks with Clean Architecture...")
    print("📂 Project structure has been migrated to clean architecture")
    print("🔧 Some imports may need fixing - this is the basic startup version")
    print("🌐 Access the app at: http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )