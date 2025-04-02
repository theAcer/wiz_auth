from typing import Dict, Any, Optional
import httpx
from auth_service.core.config import settings
from auth_service.schemas.user import UserProfile
from auth_service.core.exceptions import AuthException

class UserService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
    
    async def _supabase_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None):
        """Make a request to Supabase API"""
        url = f"{self.supabase_url}/{endpoint}"
        
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
                    detail=error_data.get("message", "User service error")
                )
            
            return response.json()
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        result = await self._supabase_request(f"auth/v1/admin/users/{user_id}", "GET")
        return result
    
    async def update_user(self, user_id: str, profile_data: UserProfile) -> Dict[str, Any]:
        """Update user profile"""
        # Filter out None values
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
        
        data = {
            "id": user_id,
            "data": update_data
        }
        
        result = await self._supabase_request("auth/v1/admin/users", "PUT", data)
        return result

