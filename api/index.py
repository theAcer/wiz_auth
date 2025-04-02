from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your FastAPI app
from auth_service.main import app as fastapi_app

# Create a handler for Vercel serverless functions
async def handler(request: Request):
    """
    Handle requests in the Vercel serverless environment
    """
    # Get the path and method from the request
    path = request.url.path
    if path.endswith("/"):
        path = path[:-1]
        
    # Process the request through your FastAPI app
    return await fastapi_app(scope={"type": "http", "path": path, "method": request.method}, receive=request.receive)

# Export the handler for Vercel
app = fastapi_app

