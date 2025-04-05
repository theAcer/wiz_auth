from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
  email: EmailStr
  first_name: str
  last_name: str
  phone_number: Optional[str] = None

class UserProfile(BaseModel):
  first_name: Optional[str] = None
  last_name: Optional[str] = None
  phone_number: Optional[str] = None
  avatar_url: Optional[str] = None

class UserResponse(BaseModel):
  id: UUID
  email: EmailStr
  first_name: str = ""
  last_name: str = ""
  phone_number: Optional[str] = None
  avatar_url: Optional[str] = None
  role: str = "user"
  is_verified: bool = True
  created_at: datetime = Field(default_factory=datetime.utcnow)
  updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
  last_login: Optional[datetime] = Field(default_factory=datetime.utcnow)

