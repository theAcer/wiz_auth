from fastapi import FastAPI
from mangum import Mangum

# Create a minimal FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is working!"}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI on Vercel!"}

# Create handler for Vercel
handler = Mangum(app)

