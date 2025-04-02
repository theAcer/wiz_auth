from fastapi import APIRouter, Depends, status
from typing import Any

from auth_service.core.exceptions import AuthException
from auth_service.schemas.user import UserProfile, UserResponse
from auth_service.services.user import UserService
from auth_service.dependencies.auth import get_current_user

router = APIRouter()
user_service = UserService()

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)) -> Any:
    """
    Get current user profile.
    """
    try:
        user = await user_service.get_user_by_id(current_user["id"])
        return user
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
        updated_user = await user_service.update_user(current_user["id"], profile)
        return updated_user
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

