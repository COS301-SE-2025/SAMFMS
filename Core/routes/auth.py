from fastapi import APIRouter
from models import UserModel
from bson import ObjectId
from fastapi import APIRouter
from fastapi import HTTPException
from models import UserModel
import user
import json

from database import db

router = APIRouter()
users_collection = db.users

@router.post("/signup/")
async def create_user(user: str):
    try:
        user_data = json.loads(user)

        required_fields = ["fullname", "email", "password"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )


        user_model = UserModel(
                full_name=user_data["full_name"],
                email=user_data["email"],
                password=user_data["password"]
            )
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    response = user.create_user(user_model)
    return {"id": str(response.inserted_id), "message": "User created successfully"}


    

#create sighnup endpoint
#get info and make user model
#send user model to /users/