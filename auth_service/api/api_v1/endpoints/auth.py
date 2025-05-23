from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from datetime import timedelta

from auth_service.core.config import settings
from auth_service.core.security import create_access_token
from auth_service.core.exceptions import AuthException
from auth_service.schemas.auth import (
    Token, UserSignUp, MagicLinkRequest, PhoneLoginRequest, 
    PhoneVerifyRequest, PasswordResetRequest, PasswordResetConfirm,
    GoogleAuthRequest, GoogleAuthUrlRequest
)
from auth_service.services.auth import AuthService
from auth_service.dependencies.auth import get_current_user
import logging
import jwt

logger = logging.getLogger(__name__)

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
    
@router.get("/google/url", response_model=dict)
async def get_google_auth_url(redirect_uri: str = Query(...)) -> Any:
    """
    Get Google OAuth URL for client-side redirect.
    """
    try:
        logger.info(f"Getting Google auth URL with redirect: {redirect_uri}")
        result = await auth_service.get_google_auth_url(redirect_uri)
        return result
    except AuthException as e:
        logger.error(f"Auth exception in get_google_auth_url: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_google_auth_url: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Google auth URL: {str(e)}"
        )

@router.post("/google/callback", response_model=Token)
async def google_callback(request: GoogleAuthRequest) -> Any:
    """
    Handle Google OAuth callback.
    """
    try:
        logger.info("Processing Google authentication callback")
        logger.info(f"Code received: {request.code[:10]}... (truncated)")
        logger.info(f"Redirect URI: {request.redirect_uri}")
        
        # Exchange the code for tokens
        result = await auth_service.handle_google_callback(request.code, request.redirect_uri)
        
        logger.info("Google authentication successful, returning token")
        
        # Format the response to match your Token model
        return {
            "access_token": result.get("access_token", ""),
            "token_type": result.get("token_type", "bearer"),
            "expires_in": result.get("expires_in"),
            "refresh_token": result.get("refresh_token"),
            "user": result.get("user")
        }
    except Exception as e:
        logger.error(f"Unexpected error in google_callback: {str(e)}")
        # Return a valid response even in case of error to prevent hanging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during Google authentication: {str(e)}"
        )
    
@router.get("/debug-token")
async def debug_token(request: Request):
    """Debug endpoint to analyze token structure"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No Authorization header provided"}
    
    try:
        # Log the raw header
        logger.info(f"Raw Authorization header: {auth_header}")
        
        # Extract token
        if " " in auth_header:
            token_type, token = auth_header.split(" ", 1)
        else:
            token_type = "Unknown"
            token = auth_header
        
        logger.info(f"Token type: {token_type}, Token (first 20 chars): {token[:20]}...")
        
        # Try to decode header without verification
        try:
            header = jwt.get_unverified_header(token)
            logger.info(f"Token header: {header}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {str(e)}")
            header = {"error": str(e)}
        
        # Try to decode payload without verification
        try:
            # The jose library requires a key even when not verifying
            payload = jwt.decode(
                token,
                key="dummy_key_for_unverified_jwt",
                options={"verify_signature": False}
            )
            logger.info(f"Token payload keys: {list(payload.keys())}")
        except Exception as e:
            logger.error(f"Failed to decode token payload: {str(e)}")
            payload = {"error": str(e)}
        
        # Return token info
        return {
            "raw_header": auth_header,
            "token_type": token_type,
            "token_preview": token[:20] + "...",
            "header": header,
            "payload_keys": list(payload.keys()) if isinstance(payload, dict) and "error" not in payload else [],
            "issuer": payload.get("iss") if isinstance(payload, dict) else None,
            "subject": payload.get("sub") if isinstance(payload, dict) else None,
            "audience": payload.get("aud") if isinstance(payload, dict) else None,
            "expiration": payload.get("exp") if isinstance(payload, dict) else None,
            "issued_at": payload.get("iat") if isinstance(payload, dict) else None,
        }
    except Exception as e:
        logger.error(f"Error in debug-token endpoint: {str(e)}")
        return {"error": f"Failed to analyze token: {str(e)}"}
    

@router.get("/direct-token-test")
async def direct_token_test(request: Request):
    """Test endpoint that manually extracts the token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No Authorization header provided"}
    
    try:
        # Extract token
        if " " in auth_header:
            token_type, token = auth_header.split(" ", 1)
        else:
            token = auth_header
        
        # Try to decode without verification
        payload = jwt.decode(
            token,
            key="dummy_key_for_unverified_jwt",
            options={"verify_signature": False}
        )
        
        return {
            "success": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email")
        }
    except Exception as e:
        return {"error": f"Failed to process token: {str(e)}"}
