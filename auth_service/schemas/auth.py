from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class MagicLinkRequest(BaseModel):
    email: EmailStr
    redirect_to: Optional[str] = None

class PhoneLoginRequest(BaseModel):
    phone: str

class PhoneVerifyRequest(BaseModel):
    phone: str
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

