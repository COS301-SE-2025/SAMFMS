from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from routes.auth_utils import get_current_user
from pydantic import BaseModel
import uvicorn
import asyncio
import logging
from routes import user
from routes import auth
from routes import vehicle
from routes import driver
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class TokenValidationResponse(BaseModel):
    valid: bool

# Configure CORS
origins = [
    "http://localhost:3000",     # React development server
    "http://127.0.0.1:3000",
    "http://localhost:5000",     # Production build if served differently
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        # Allow all methods including OPTIONS
    allow_headers=["*"],        # Allow all headers
    expose_headers=["*"]
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(driver.router)

@app.get("/auth/validate-token", response_model=TokenValidationResponse)
async def validate_token(current_user: dict = Depends(get_current_user)):
    """
    Validates the current JWT token.
    Returns true if the token is valid (user is authenticated).
    """
    return {"valid": True}

@app.get("/")
async def root():
    return {"message": "SAMFMS API is running"}







#####################################################################################################################
client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
db = client.mcore
users_collection = db.users


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    