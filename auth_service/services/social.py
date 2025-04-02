from typing import Dict, Any
import httpx
from auth_service.core.config import settings
from auth_service.core.exceptions import AuthException

class SocialAuthService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
    
    async def authenticate_google(self, id_token: str) -> Dict[str, Any]:
        """Authenticate with Google OAuth"""
        data = {
            "id_token": id_token,
            "provider": "google"
        }
        
        url = f"{self.supabase_url}/auth/v1/token?grant_type=id_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data)
            
            if response.status_code >= 400:
                error_data = response.json()
                raise AuthException(
                    status_code=response.status_code,
                    detail=error_data.get("message", "Google authentication error")
                )
            
            result = response.json()
            return result.get("user", {})

