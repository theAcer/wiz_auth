from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    marketing_consent: Optional[bool] = False

class MagicLinkRequest(BaseModel):
    email: EmailStr
    redirect_to: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    password: str

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None

