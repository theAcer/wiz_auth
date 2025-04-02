from typing import Optional, Dict, Any
import httpx
from auth_service.core.config import settings
from auth_service.schemas.auth import UserSignUp
from auth_service.core.exceptions import AuthException
from fastapi import status

class AuthService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
    
    async def _supabase_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None):
        """Make a request to Supabase Auth API"""
        url = f"{self.supabase_url}/auth/v1/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=self.headers)
            elif method == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=self.headers)
            
            if response.status_code >= 400:
                error_data = response.json()
                raise AuthException(
                    status_code=response.status_code,
                    detail=error_data.get("message", "Authentication error")
                )
            
            return response.json()
    
    async def signup(self, user_data: UserSignUp) -> Dict[str, Any]:
        """Register a new user"""
        auth_data = {
            "email": user_data.email,
            "password": user_data.password,
            "data": {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "phone_number": user_data.phone_number
            }
        }
        
        result = await self._supabase_request("signup", "POST", auth_data)
        return result
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        auth_data = {
            "email": email,
            "password": password
        }
        
        try:
            result = await self._supabase_request("token?grant_type=password", "POST", auth_data)
            return result.get("user", None)
        except AuthException as e:
            if e.status_code == status.HTTP_400_BAD_REQUEST:
                return None
            raise e
    
    async def send_magic_link(self, email: str, redirect_to: Optional[str] = None) -> None:
        """Send a magic link to the user's email"""
        data = {
            "email": email,
            "type": "magiclink",
        }
        
        if redirect_to:
            data["redirect_to"] = redirect_to
            
        await self._supabase_request("otp", "POST", data)
    
    async def send_phone_otp(self, phone: str) -> None:
        """Send OTP to phone number"""
        data = {
            "phone": phone,
            "type": "sms"
        }
        
        await self._supabase_request("otp", "POST", data)
    
    async def verify_phone_otp(self, phone: str, token: str) -> Dict[str, Any]:
        """Verify phone OTP"""
        data = {
            "phone": phone,
            "token": token,
            "type": "sms"
        }
        
        result = await self._supabase_request("verify", "POST", data)
        return result.get("user", {})
    
    async def request_password_reset(self, email: str) -> None:
        """Request password reset"""
        data = {
            "email": email
        }
        
        await self._supabase_request("recover", "POST", data)
    
    async def confirm_password_reset(self, token: str, password: str) -> None:
        """Confirm password reset with token"""
        data = {
            "token": token,
            "password": password
        }
        
        await self._supabase_request("recover", "PUT", data)
    
    async def logout(self, user_id: str) -> None:
        """Logout user"""
        await self._supabase_request("logout", "POST")

