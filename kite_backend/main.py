from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from routers import auth, historical_data, metadata, live_data, technical_analysis, gemini_ai
from utils.logger import setup_logger
from utils.config import settings
from services.auth_service import AuthService

logger = setup_logger(__name__)

auth_service_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global auth_service_instance
    logger.info("Starting Kite Backend API")
    
    auth_service_instance = AuthService()
    
    if settings.kite_access_token:
        logger.info("Initializing with existing access token")
        success = auth_service_instance.initialize_with_access_token(settings.kite_access_token)
        if success:
            logger.info("Successfully initialized with access token")
        else:
            logger.warning("Failed to initialize with access token")
    else:
        logger.info("No access token found. Manual authentication required.")
    
    yield
    
    logger.info("Shutting down Kite Backend API")

app = FastAPI(
    title="Kite Connect Backend API",
    description="FastAPI backend for Kite Connect integration with modular design",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(historical_data.router)
app.include_router(metadata.router)
app.include_router(live_data.router)
app.include_router(technical_analysis.router)
app.include_router(gemini_ai.router)

@app.get("/")
async def root():
    return {
        "message": "Kite Connect Backend API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "historical": "/historical",
            "metadata": "/metadata", 
            "live": "/live",
            "technical_analysis": "/technical-analysis",
            "gemini_ai": "/gemini"
        }
    }

@app.get("/health")
async def health_check():
    try:
        if auth_service_instance:
            auth_status = auth_service_instance.get_auth_status()
            return {
                "status": "healthy",
                "authentication": auth_status.authenticated,
                "auth_status": auth_status.status
            }
        else:
            return {
                "status": "healthy",
                "authentication": False,
                "auth_status": "not_initialized"
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )