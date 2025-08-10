from pydantic import BaseModel
from typing import Optional

class AuthRequest(BaseModel):
    request_token: str

class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    status: str
    message: Optional[str] = None

class AuthStatus(BaseModel):
    authenticated: bool
    user_id: Optional[str] = None
    status: str

class LoginUrlResponse(BaseModel):
    login_url: str
    message: str