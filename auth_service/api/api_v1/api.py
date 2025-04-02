from fastapi import APIRouter
from auth_service.api.api_v1.endpoints import auth, users, social

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(social.router, prefix="/social", tags=["social"])

