from typing import Dict, Any, Optional
import httpx
from auth_service.core.config import settings
from auth_service.schemas.user import UserProfile
from auth_service.core.exceptions import AuthException
import logging
import json
from datetime import datetime
from jose import jwt as jose_jwt  # Use jose library which is already installed

# Set up logging
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
        # Use the correct table name from your schema
        self.profile_table = "user_profiles"
    
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
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_message = json.dumps(error_data)
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
    
    def _extract_email_from_token(self, token: str) -> str:
        """Extract email from JWT token"""
        try:
            # Decode the token without verification
            decoded = jose_jwt.decode(token, options={"verify_signature": False})
            
            # Log the token structure for debugging
            logger.debug(f"JWT token payload: {json.dumps(decoded)}")
            
            # Check various possible locations for the email
            # 1. Direct email claim
            if "email" in decoded and decoded["email"]:
                return decoded["email"]
            
            # 2. Check in user metadata
            if "user_metadata" in decoded and isinstance(decoded["user_metadata"], dict):
                user_metadata = decoded["user_metadata"]
                if "email" in user_metadata and user_metadata["email"]:
                    return user_metadata["email"]
            
            # 3. Check in app metadata
            if "app_metadata" in decoded and isinstance(decoded["app_metadata"], dict):
                app_metadata = decoded["app_metadata"]
                if "email" in app_metadata and app_metadata["email"]:
                    return app_metadata["email"]
            
            # 4. Check for Supabase specific claims
            if "user" in decoded and isinstance(decoded["user"], dict):
                user = decoded["user"]
                if "email" in user and user["email"]:
                    return user["email"]
            
            # 5. Try to get email from auth endpoint
            return ""
        except Exception as e:
            logger.error(f"Error extracting email from token: {str(e)}")
            return ""
    
    async def _get_user_email_from_auth(self, auth_token: str) -> str:
        """Get user email from Supabase auth endpoint"""
        try:
            # Try to get user data from Supabase auth endpoint
            user_data = await self._supabase_request("auth/v1/user", "GET", auth_token=auth_token)
            if user_data and "email" in user_data:
                return user_data["email"]
            return ""
        except Exception as e:
            logger.error(f"Error getting user email from auth: {str(e)}")
            return ""
    
    async def get_user_by_id(self, user_id: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            logger.info(f"Fetching user with ID: {user_id}")
            
            # First, get the user's profile from the user_profiles table
            profile_endpoint = f"rest/v1/{self.profile_table}?id=eq.{user_id}&select=*"
            
            try:
                profiles = await self._supabase_request(profile_endpoint, "GET", auth_token=auth_token)
                
                if not profiles or len(profiles) == 0:
                    # Profile doesn't exist, create one
                    logger.info(f"Profile not found for user {user_id}, creating one")
                    now = datetime.utcnow().isoformat()
                    profile_data = {
                        "id": user_id,
                        "first_name": "",
                        "last_name": "",
                        "phone_number": "",
                        "avatar_url": "",
                        "created_at": now,
                        "updated_at": now
                    }
                    await self._supabase_request(f"rest/v1/{self.profile_table}", "POST", data=profile_data, auth_token=auth_token)
                    profile = profile_data
                else:
                    profile = profiles[0]
            except Exception as e:
                logger.error(f"Error fetching profile: {str(e)}")
                now = datetime.utcnow().isoformat()
                profile = {
                    "first_name": "",
                    "last_name": "",
                    "phone_number": "",
                    "avatar_url": "",
                    "created_at": now,
                    "updated_at": now
                }
            
            # For the user's email, try multiple methods
            email = "user@example.com"  # Default valid email
            
            if auth_token:
                # Method 1: Extract from token
                token_email = self._extract_email_from_token(auth_token)
                if token_email:
                    email = token_email
                    logger.info(f"Extracted email from token: {email}")
                else:
                    # Method 2: Get from auth endpoint
                    auth_email = await self._get_user_email_from_auth(auth_token)
                    if auth_email:
                        email = auth_email
                        logger.info(f"Got email from auth endpoint: {email}")
                    else:
                        logger.warning("Could not extract email from token or auth endpoint")
            
            # Ensure we have valid datetime strings
            now = datetime.utcnow().isoformat()
            created_at = profile.get("created_at") or now
            updated_at = profile.get("updated_at") or now
            
            # Combine user and profile data
            return {
                "id": user_id,
                "email": email,
                "first_name": profile.get("first_name", ""),
                "last_name": profile.get("last_name", ""),
                "phone_number": profile.get("phone_number", ""),
                "avatar_url": profile.get("avatar_url", ""),
                "role": "user",
                "is_verified": True,  # Assume verified since they have a token
                "created_at": created_at,
                "updated_at": updated_at,
                "last_login": now
            }
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, profile_data: UserProfile, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Update user profile"""
        try:
            # Filter out None values
            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Update the profile in the user_profiles table
            profile_endpoint = f"rest/v1/{self.profile_table}?id=eq.{user_id}"
            
            await self._supabase_request(profile_endpoint, "PATCH", data=update_data, auth_token=auth_token)
            
            # Get the updated user
            return await self.get_user_by_id(user_id, auth_token)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

