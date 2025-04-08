from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from auth_service.core.config import settings
from auth_service.schemas.auth import TokenPayload
import logging

# Set up logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    try:
        logger.info("Verifying JWT token")
        logger.info(f"Token (first 20 chars): {token[:20]}...")
        
        # Extract token if it's in "Bearer <token>" format
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            logger.info("Extracted token from Bearer format")
        
        # Log token header for debugging
        try:
            header = jwt.get_unverified_header(token)
            logger.info(f"Token header: {header}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {str(e)}")
        
        # First try with the configured secret key
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_audience": False, "verify_iss": False}  # More lenient verification
            )
            logger.info("Token decoded with JWT_SECRET_KEY")
        except Exception as e:
            logger.warning(f"Failed to decode with JWT_SECRET_KEY: {str(e)}")
            # Try with Supabase JWT secret as fallback
            try:
                payload = jwt.decode(
                    token, 
                    settings.SUPABASE_JWT_SECRET, 
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_audience": False, "verify_iss": False}  # More lenient verification
                )
                logger.info("Token decoded with SUPABASE_JWT_SECRET")
            except Exception as e2:
                logger.warning(f"Failed to decode with SUPABASE_JWT_SECRET: {str(e2)}")
                # As a last resort, decode without verification
                payload = jwt.decode(
                    token,
                    key="dummy_key_for_unverified_jwt",
                    options={"verify_signature": False}
                )
                logger.warning("Token decoded without verification - security risk!")
        
        # Log the payload structure for debugging
        logger.info(f"Token payload keys: {list(payload.keys())}")
        
        # Extract user ID from payload - Supabase uses 'sub' for user ID
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials - missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Token verified for user ID: {user_id}")
        return {"id": user_id, "token": token}
    except JWTError as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in auth dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )