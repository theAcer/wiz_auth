from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Configure CORS - Update to include Vercel deployment URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["https://*.vercel.app", "https://*.now.sh"],
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

# This is only used when running locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_service.main:app", host="0.0.0.0", port=8000, reload=True)

# This is only used when running in Vercel
# async def handler(request: Request):
#     """
#     Handle requests in the Vercel serverless environment
#     """
#     # Get the path and method from the request
#     path = request.url.path
#     if path.endswith("/"):
#         path = path[:-1]
#
#     # Process the request through your FastAPI app
#     return await fastapi_app(scope={"type": "http", "path": path, "method": request.method}, receive=request.receive)
#
# # Export the handler for Vercel
# app = fastapi_app
#   