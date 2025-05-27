from fastapi import APIRouter, HTTPException
from fastapi import APIRouter
<<<<<<< Updated upstream
from Core.models import UserModel
from routes import user
=======
from models import UserModel
from bson import ObjectId
from fastapi import HTTPException
>>>>>>> Stashed changes
import json

from database import db

router = APIRouter()
users_collection = db.users

@router.post("/signup/")
async def create_user(user: str):
    try:
        user_data = json.loads(user)
        required_fields = ["name", "email", "password", "ID", "role"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        user_model = UserModel(
            ID=user_data["ID"],
            name=user_data["name"],
            email=user_data["email"],
            password=user_data["password"],
            role=user_data["role"]
        )
        
        # Insert user directly into database
        user_dict = user_model.model_dump(by_alias=True)
        result = await users_collection.insert_one(user_dict)
        return {"id": str(result.inserted_id), "message": "User created successfully"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")


    

#create sighnup endpoint
#get info and make user model
#send user model to /users/