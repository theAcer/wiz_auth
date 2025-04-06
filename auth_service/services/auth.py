from typing import Optional, Dict, Any
import httpx
from auth_service.core.config import settings
from auth_service.schemas.auth import (
    UserLogin, UserSignUp, MagicLinkRequest, 
    PasswordResetRequest, PasswordResetConfirm,
    GoogleAuthRequest
)
from auth_service.core.exceptions import AuthException
from fastapi import status
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
    
    async def _supabase_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None):
        """Make a request to Supabase API"""
        url = f"{self.supabase_url}/{endpoint}"
        
        headers = self.headers.copy()
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        logger.debug(f"Making {method} request to {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code >= 400:
                    error_message = f"Error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_message = str(error_data)
                    except:
                        error_message = f"Error: {response.status_code} - {response.text}"
                    
                    logger.error(f"Error in Supabase request: {error_message}")
                    raise AuthException(
                        status_code=response.status_code,
                        detail=error_message
                    )
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                raise AuthException(
                    status_code=500,
                    detail=f"Request error: {str(e)}"
                )
    
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
    
    async def authenticate(self, email, password):
        """Authenticate user with email and password"""
        try:
            auth_data = {
                "email": email,
                "password": password
            }
            
            result = await self._supabase_request("auth/v1/token?grant_type=password", "POST", auth_data)
            
            # Extract user data from the token response
            user = {
                "id": result.get("user", {}).get("id", ""),
                "email": result.get("user", {}).get("email", ""),
                "user_metadata": result.get("user", {}).get("user_metadata", {})
            }
            
            return user
        except Exception as e:
            logger.error(f"Error in authenticate: {str(e)}")
            return None
    
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

    async def get_google_auth_url(self, redirect_uri):
        """Get Google OAuth URL for client-side redirect"""
        try:
            logger.info(f"Getting Google auth URL with redirect: {redirect_uri}")
            
            # Construct the Google OAuth URL using Supabase's OAuth endpoint
            params = {
                "provider": "google",
                "redirect_to": redirect_uri
            }
            
            # Make a request to Supabase's OAuth URL endpoint
            url = f"{self.supabase_url}/auth/v1/authorize"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code >= 400:
                    error_message = f"Error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_message = str(error_data)
                    except:
                        error_message = f"Error: {response.status_code} - {response.text}"
                    
                    logger.error(f"Error getting Google auth URL: {error_message}")
                    raise AuthException(
                        status_code=response.status_code,
                        detail=error_message
                    )
                
                result = response.json()
                return {"url": result.get("url")}
        except Exception as e:
            logger.error(f"Error in get_google_auth_url: {str(e)}")
            raise
    
    async def handle_google_callback(self, code, redirect_uri=None):
        """Handle Google OAuth callback"""
        try:
            logger.info("Processing Google authentication callback")
            
            # Exchange the authorization code for tokens
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "provider": "google"
            }
            
            # Add redirect_uri if provided
            if redirect_uri:
                data["redirect_uri"] = redirect_uri
            
            # Make the token exchange request
            result = await self._supabase_request("auth/v1/token", "POST", data)
            
            logger.info("Google authentication successful")
            return result
        except Exception as e:
            logger.error(f"Error in handle_google_callback: {str(e)}")
            raise
    
    async def logout(self, user_id: str) -> None:
        """Logout user"""
        await self._supabase_request("logout", "POST")

