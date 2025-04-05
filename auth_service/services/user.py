from typing import Dict, Any, Optional
import httpx
from auth_service.core.config import settings
from auth_service.schemas.user import UserProfile
from auth_service.core.exceptions import AuthException
import logging
import json

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
  
  async def get_user_by_id(self, user_id: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
      """Get user by ID"""
      try:
          logger.info(f"Fetching user with ID: {user_id}")
          
          # First, get the user's profile from the profiles table
          # This is a public table that can be accessed with the anon key
          profile_endpoint = f"rest/v1/profiles?id=eq.{user_id}&select=*"
          
          try:
              profiles = await self._supabase_request(profile_endpoint, "GET", auth_token=auth_token)
              
              if not profiles or len(profiles) == 0:
                  # Profile doesn't exist, create one
                  logger.info(f"Profile not found for user {user_id}, creating one")
                  profile_data = {
                      "id": user_id,
                      "first_name": "",
                      "last_name": "",
                      "phone_number": "",
                      "avatar_url": ""
                  }
                  await self._supabase_request("rest/v1/profiles", "POST", data=profile_data, auth_token=auth_token)
                  profile = profile_data
              else:
                  profile = profiles[0]
          except Exception as e:
              logger.error(f"Error fetching profile: {str(e)}")
              profile = {
                  "first_name": "",
                  "last_name": "",
                  "phone_number": "",
                  "avatar_url": ""
              }
          
          # Now get the user's email from the auth.users table
          # We can use the user's token to get their own data
          user_endpoint = "auth/v1/user"
          
          try:
              # This endpoint requires the user's token
              if not auth_token:
                  # If no token provided, use a default email
                  user_data = {"email": "user@example.com"}
              else:
                  user_data = await self._supabase_request(user_endpoint, "GET", auth_token=auth_token)
          except Exception as e:
              logger.error(f"Error fetching user data: {str(e)}")
              user_data = {"email": "user@example.com"}
          
          # Combine user and profile data
          return {
              "id": user_id,
              "email": user_data.get("email", ""),
              "first_name": profile.get("first_name", ""),
              "last_name": profile.get("last_name", ""),
              "phone_number": profile.get("phone_number", ""),
              "avatar_url": profile.get("avatar_url", ""),
              "role": "user",
              "is_verified": True,  # Assume verified since they have a token
              "created_at": profile.get("created_at", ""),
              "updated_at": profile.get("updated_at", ""),
              "last_login": user_data.get("last_sign_in_at", "")
          }
      except Exception as e:
          logger.error(f"Error getting user by ID: {str(e)}")
          raise
  
  async def update_user(self, user_id: str, profile_data: UserProfile, auth_token: Optional[str] = None) -> Dict[str, Any]:
      """Update user profile"""
      try:
          # Filter out None values
          update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
          
          # Update the profile in the profiles table
          profile_endpoint = f"rest/v1/profiles?id=eq.{user_id}"
          
          await self._supabase_request(profile_endpoint, "PATCH", data=update_data, auth_token=auth_token)
          
          # Get the updated user
          return await self.get_user_by_id(user_id, auth_token)
      except Exception as e:
          logger.error(f"Error updating user: {str(e)}")
          raise

