"""
RM AI Advisory - FastAPI Application
Multi-agent investment advisory platform for Relationship Managers
"""

# Set PYTHONPATH to include backend directory FIRST
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.api import clients, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler for startup and shutdown"""
    # Startup
    print("🚀 Starting RM AI Advisory API...")
    print(f"📊 Database: {os.getenv('DATABASE_URL', 'Not configured')[:50]}...")
    print(f"🤖 LLM Provider: {os.getenv('GROQ_BASE_URL', 'Not configured')}")
    
    # TODO: Initialize database connection pool
    # TODO: Initialize cache
    # TODO: Test Groq API connection
    
    yield
    
    # Shutdown
    print("👋 Shutting down RM AI Advisory API...")
    # TODO: Close database connections


app = FastAPI(
    title="RM AI Advisory API",
    description="Multi-agent investment advisory platform with compliance governance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
# For development, allow all origins. In production, use specific origins from env var.
origins = ["*"]  # Allow all origins for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RM AI Advisory API",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "pending",  # TODO: Check DB connection
        "llm": "pending",       # TODO: Check Groq API
        "cache": "pending"      # TODO: Check cache
    }


# Router registration
app.include_router(clients.router, prefix="/api", tags=["clients"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
# app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
