from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Wiz Authentication Service",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

# Create handler for Vercel
handler = Mangum(app)

