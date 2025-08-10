import os
from kiteconnect import KiteConnect
from typing import Optional
from utils.logger import setup_logger
from utils.config import settings
from models.auth import AuthResponse, AuthStatus, LoginUrlResponse

class AuthService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.api_key = settings.kite_api_key
        self.api_secret = settings.kite_api_secret
        self.kite: Optional[KiteConnect] = None
        self.access_token: Optional[str] = None
        
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            self.logger.info("KiteConnect instance created")
        else:
            self.logger.warning("API key not found in environment variables")
    
    def generate_session(self, request_token: str) -> AuthResponse:
        try:
            if not self.kite:
                raise ValueError("KiteConnect not initialized. Check API key.")
            
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            self.logger.info(f"Authentication successful for user: {data['user_id']}")
            
            return AuthResponse(
                access_token=data["access_token"],
                user_id=data["user_id"],
                status="success"
            )
        
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return AuthResponse(
                access_token="",
                user_id="",
                status="failed",
                message=str(e)
            )
    
    def get_auth_status(self) -> AuthStatus:
        if not self.kite or not self.access_token:
            return AuthStatus(
                authenticated=False,
                status="not_authenticated"
            )
        
        try:
            profile = self.kite.profile()
            return AuthStatus(
                authenticated=True,
                user_id=profile.get("user_id", ""),
                status="authenticated"
            )
        except Exception as e:
            self.logger.error(f"Auth status check failed: {str(e)}")
            return AuthStatus(
                authenticated=False,
                status="authentication_expired"
            )
    
    def initialize_with_access_token(self, access_token: str) -> bool:
        try:
            if not self.kite:
                self.kite = KiteConnect(api_key=self.api_key)
            
            self.kite.set_access_token(access_token)
            self.access_token = access_token
            
            profile = self.kite.profile()
            self.logger.info(f"Initialized with access token for user: {profile.get('user_id', 'unknown')}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to initialize with access token: {str(e)}")
            return False
    
    def get_login_url(self) -> LoginUrlResponse:
        try:
            if not self.kite:
                raise ValueError("KiteConnect not initialized. Check API key in .env file.")
            
            login_url = self.kite.login_url()
            self.logger.info("Login URL generated successfully")
            
            return LoginUrlResponse(
                login_url=login_url,
                message="Please visit this URL to authenticate and get the request token"
            )
        
        except Exception as e:
            self.logger.error(f"Failed to generate login URL: {str(e)}")
            raise e
    
    def get_kite_instance(self) -> Optional[KiteConnect]:
        return self.kite if self.access_token else None