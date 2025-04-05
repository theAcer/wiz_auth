from typing import Dict, Any, Optional
import httpx
from auth_service.core.config import settings
from auth_service.schemas.user import UserProfile
from auth_service.core.exceptions import AuthException
import logging

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
  
  async def _supabase_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None):
      """Make a request to Supabase API"""
      url = f"{self.supabase_url}/{endpoint}"
      
      logger.debug(f"Making {method} request to {url}")
      
      async with httpx.AsyncClient() as client:
          try:
              if method == "GET":
                  response = await client.get(url, headers=self.headers)
              elif method == "POST":
                  response = await client.post(url, headers=self.headers, json=data)
              elif method == "PUT":
                  response = await client.put(url, headers=self.headers, json=data)
              elif method == "DELETE":
                  response = await client.delete(url, headers=self.headers)
              
              logger.debug(f"Response status: {response.status_code}")
              
              if response.status_code >= 400:
                  try:
                      error_data = response.json()
                      error_message = error_data.get("message", "User service error")
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
  
  async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
      """Get user by ID"""
      try:
          # The correct endpoint for getting a user by ID in Supabase
          # We need to use the auth.users endpoint with the service key
          logger.info(f"Fetching user with ID: {user_id}")
          
          # Add service role key for admin access
          admin_headers = {
              **self.headers,
              "Authorization": f"Bearer {self.supabase_key}"
          }
          
          # First get the user from auth.users
          url = f"{self.supabase_url}/auth/v1/admin/users/{user_id}"
          
          async with httpx.AsyncClient() as client:
              response = await client.get(url, headers=admin_headers)
              
              if response.status_code >= 400:
                  logger.error(f"Error fetching user: {response.status_code} - {response.text}")
                  raise AuthException(
                      status_code=response.status_code,
                      detail=f"Error fetching user: {response.text}"
                  )
              
              user_data = response.json()
              
              # Now get the profile data from profiles table
              profile_url = f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}&select=*"
              profile_response = await client.get(profile_url, headers=admin_headers)
              
              # If profile doesn't exist, create one
              if profile_response.status_code == 200:
                  profiles = profile_response.json()
                  if not profiles:
                      # Create a profile
                      logger.info(f"Creating profile for user {user_id}")
                      create_url = f"{self.supabase_url}/rest/v1/profiles"
                      profile_data = {
                          "id": user_id,
                          "first_name": "",
                          "last_name": "",
                          "phone_number": "",
                          "avatar_url": ""
                      }
                      await client.post(create_url, headers=admin_headers, json=profile_data)
                      profile = profile_data
                  else:
                      profile = profiles[0]
              else:
                  logger.error(f"Error fetching profile: {profile_response.status_code} - {profile_response.text}")
                  profile = {
                      "first_name": "",
                      "last_name": "",
                      "phone_number": "",
                      "avatar_url": ""
                  }
              
              # Combine user and profile data
              return {
                  "id": user_id,
                  "email": user_data.get("email", ""),
                  "first_name": profile.get("first_name", ""),
                  "last_name": profile.get("last_name", ""),
                  "phone_number": profile.get("phone_number", ""),
                  "avatar_url": profile.get("avatar_url", ""),
                  "role": "user",
                  "is_verified": user_data.get("email_confirmed_at") is not None,
                  "created_at": user_data.get("created_at", ""),
                  "updated_at": profile.get("updated_at", ""),
                  "last_login": user_data.get("last_sign_in_at", "")
              }
      except Exception as e:
          logger.error(f"Error getting user by ID: {str(e)}")
          raise
  
  async def update_user(self, user_id: str, profile_data: UserProfile) -> Dict[str, Any]:
      """Update user profile"""
      # Filter out None values
      update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
      
      # Add service role key for admin access
      admin_headers = {
          **self.headers,
          "Authorization": f"Bearer {self.supabase_key}"
      }
      
      try:
          # Update the profile in the profiles table
          url = f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}"
          
          async with httpx.AsyncClient() as client:
              response = await client.patch(url, headers=admin_headers, json=update_data)
              
              if response.status_code >= 400:
                  logger.error(f"Error updating profile: {response.status_code} - {response.text}")
                  raise AuthException(
                      status_code=response.status_code,
                      detail=f"Error updating profile: {response.text}"
                  )
          
          # Get the updated user
          return await self.get_user_by_id(user_id)
      except Exception as e:
          logger.error(f"Error updating user: {str(e)}")
          raise

