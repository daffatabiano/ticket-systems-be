"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.config import get_settings
from app.api import tickets, websocket
from app.database import engine, Base
from app.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting Complaint Triage System API")
    logger.info("=" * 60)
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"AI Model: {settings.AI_MODEL}")
    logger.info("=" * 60)
    
    # Create tables if they don't exist (for development)
    # In production, use Alembic migrations instead
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified/created")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("👋 Shutting down Complaint Triage System API")
    logger.info("=" * 60)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered complaint triage system with async processing",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Complaint Triage System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
        "ai_model": settings.AI_MODEL,
        "endpoints": {
            "tickets": "/api/tickets",
            "websocket": "/ws/tickets",
            "docs": "/docs",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
