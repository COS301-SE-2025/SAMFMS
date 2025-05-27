from fastapi import APIRouter
from bson import ObjectId
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from models import UserModel
from motor.motor_asyncio import AsyncIOMotorClient

from database import db

router = APIRouter()

users_collection = db.users

@router.post("/users/", response_model=UserModel)
async def create_user(user: UserModel):
    user_dict = user.model_dump(by_alias=True)
    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return user_dict

@router.get("/users/{id}", response_model=UserModel)
async def get_user(id: str):
    if (user := await users_collection.find_one({"_id": ObjectId(id)})) is not None:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/test-db")
async def test_db_connection():
    try:
        collections = await db.list_collection_names()
        return {"status": "success", "collections": collections}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

