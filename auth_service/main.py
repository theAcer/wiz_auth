from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from auth_service.core.config import settings
from auth_service.api.api_v1.api import api_router
from auth_service.core.exceptions import add_exception_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Authentication microservice for Wiz platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get the PORT from environment variable (Render sets this)
port = os.environ.get("PORT", 8000)

# Configure CORS - Add Render domains and your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + [
        "https://*.onrender.com",
        # Add your frontend domain here
        "https://elecmate-exchange.lovable.app",
        # During development
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add exception handlers
add_exception_handlers(app)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Wiz Authentication Service",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy"}

# This is only used when running locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_service.main:app", host="0.0.0.0", port=int(port), reload=True)

