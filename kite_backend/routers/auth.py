from fastapi import APIRouter, HTTPException, Depends
from models.auth import AuthRequest, AuthResponse, AuthStatus, LoginUrlResponse
from services.auth_service import AuthService
from utils.logger import setup_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = setup_logger(__name__)

# Use the same auth service instance as main.py
def get_global_auth_service():
    import main
    return main.auth_service_instance

auth_service = None

@router.get("/login-url", response_model=LoginUrlResponse)
async def get_login_url():
    try:
        logger.info("Login URL request")
        auth_svc = get_global_auth_service()
        if not auth_svc:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        response = auth_svc.get_login_url()
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate login URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=AuthResponse)
async def login(auth_request: AuthRequest):
    try:
        logger.info(f"Authentication attempt with request token")
        auth_svc = get_global_auth_service()
        if not auth_svc:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        response = auth_svc.generate_session(auth_request.request_token)
        
        if response.status == "failed":
            raise HTTPException(status_code=401, detail=response.message or "Authentication failed")
        
        return response
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    try:
        auth_svc = get_global_auth_service()
        if not auth_svc:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        status = auth_svc.get_auth_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting auth status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_with_token(access_token: str):
    try:
        auth_svc = get_global_auth_service()
        if not auth_svc:
            raise HTTPException(status_code=500, detail="Auth service not initialized")
        success = auth_svc.initialize_with_access_token(access_token)
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        return {"status": "success", "message": "Initialized successfully"}
        
    except Exception as e:
        logger.error(f"Token initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_auth_service() -> AuthService:
    return get_global_auth_service()