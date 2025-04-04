from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from datetime import timedelta

from auth_service.core.config import settings
from auth_service.core.security import create_access_token
from auth_service.core.exceptions import AuthException
from auth_service.schemas.auth import (
    Token, UserSignUp, MagicLinkRequest, PhoneLoginRequest, 
    PhoneVerifyRequest, PasswordResetRequest, PasswordResetConfirm
)
from auth_service.services.auth import AuthService
from auth_service.dependencies.auth import get_current_user

router = APIRouter()
auth_service = AuthService()

@router.post("/signup", response_model=dict)
async def signup(user_data: UserSignUp) -> Any:
    """
    Register a new user.
    """
    try:
        result = await auth_service.signup(user_data)
        return {"message": "User registered successfully", "user": result}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        user = await auth_service.authenticate(
            email=form_data.username,
            password=form_data.password
        )
        if not user:
            raise AuthException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user["id"], expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except AuthException as e:
        raise e
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/magic-link", response_model=dict)
async def send_magic_link(request: MagicLinkRequest) -> Any:
    """
    Send a magic link to the user's email.
    """
    try:
        await auth_service.send_magic_link(request.email, request.redirect_to)
        return {"message": "Magic link sent to your email"}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/phone/login", response_model=dict)
async def phone_login(request: PhoneLoginRequest) -> Any:
    """
    Start phone number authentication.
    """
    try:
        await auth_service.send_phone_otp(request.phone)
        return {"message": "Verification code sent to your phone"}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/phone/verify", response_model=Token)
async def verify_phone(request: PhoneVerifyRequest) -> Any:
    """
    Verify phone number with token.
    """
    try:
        user = await auth_service.verify_phone_otp(request.phone, request.token)
        
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

@router.post("/reset-password", response_model=dict)
async def reset_password(request: PasswordResetRequest) -> Any:
    """
    Request password reset.
    """
    try:
        await auth_service.request_password_reset(request.email)
        return {"message": "Password reset instructions sent to your email"}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/reset-password-confirm", response_model=dict)
async def reset_password_confirm(request: PasswordResetConfirm) -> Any:
    """
    Confirm password reset with token.
    """
    try:
        await auth_service.confirm_password_reset(request.token, request.password)
        return {"message": "Password has been reset successfully"}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout", response_model=dict)
async def logout(current_user: dict = Depends(get_current_user)) -> Any:
    """
    Logout user.
    """
    try:
        await auth_service.logout(current_user["id"])
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

