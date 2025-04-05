from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict
import logging
from jose import jwt as jose_jwt

from auth_service.core.exceptions import AuthException
from auth_service.schemas.user import UserProfile, UserResponse
from auth_service.services.user import UserService
from auth_service.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)) -> Any:
    """
    Get current user profile.
    """
    try:
        logger.info(f"Getting profile for user ID: {current_user['id']}")
        user = await user_service.get_user_by_id(current_user["id"], current_user["token"])
        return user
    except AuthException as e:
        logger.error(f"Auth exception in get_user_profile: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile: UserProfile, 
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Update user profile.
    """
    try:
        logger.info(f"Updating profile for user ID: {current_user['id']}")
        updated_user = await user_service.update_user(current_user["id"], profile, current_user["token"])
        return updated_user
    except AuthException as e:
        logger.error(f"Auth exception in update_user_profile: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )

@router.get("/token-debug")
async def debug_token(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Debug endpoint to see the token payload.
    """
    try:
        token = current_user["token"]
        decoded = jose_jwt.decode(token, options={"verify_signature": False})
        return {"token_payload": decoded}
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error decoding token: {str(e)}"
        )

