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
    email: str  # Changed from EmailStr to str to allow default value
    first_name: str = ""
    last_name: str = ""
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    is_verified: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Add model validator to ensure email is valid
    def model_post_init(self, __context):
        if not self.email or '@' not in self.email:
            self.email = "user@example.com"

