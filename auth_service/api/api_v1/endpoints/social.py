from fastapi import APIRouter, status
from typing import Any

from auth_service.core.exceptions import AuthException
from auth_service.schemas.auth import Token, GoogleAuthRequest
from auth_service.services.social import SocialAuthService
from datetime import timedelta
from auth_service.core.config import settings
from auth_service.core.security import create_access_token

router = APIRouter()
social_auth_service = SocialAuthService()

@router.post("/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest) -> Any:
    """
    Handle Google OAuth authentication.
    """
    try:
        user = await social_auth_service.authenticate_google(request.id_token)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user["id"], expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

