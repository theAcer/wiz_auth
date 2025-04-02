from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

# Add the root directory to the path so we can import the auth_service module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your FastAPI app
from auth_service.main import app

# Export the app directly for Vercel

