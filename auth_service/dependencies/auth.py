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
        logger.debug("Verifying JWT token")
        
        # First try with the configured secret key
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_audience": False}  # Skip audience verification
            )
        except Exception as e:
            logger.warning(f"Failed to decode with JWT_SECRET_KEY: {str(e)}")
            # Try with Supabase JWT secret as fallback
            payload = jwt.decode(
                token, 
                settings.SUPABASE_JWT_SECRET, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_audience": False}  # Skip audience verification
            )
        
        # Extract user ID from payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Token verified for user ID: {user_id}")
        return {"id": user_id, "token": token}
    except JWTError as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in auth dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )

