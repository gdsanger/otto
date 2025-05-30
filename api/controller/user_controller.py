from fastapi import APIRouter, HTTPException, Depends
from helper import verify_api_key, serialize_mongo
from pydantic import BaseModel
import os
from typing import Optional
from datetime import datetime
from bson import ObjectId
from passlib.hash import bcrypt
from mongo import users

router = APIRouter()

class UserIn(BaseModel):
    name: str
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

def serialize(user):
    sanitized = user.copy()
    sanitized["id"] = str(sanitized.get("_id"))
    sanitized.pop("_id", None)
    #sanitized.pop("password", None)
    return sanitized

@router.get("/users", dependencies=[Depends(verify_api_key)], tags=["User"])
async def get_users(username: Optional[str] = None):
    if username:
        user = await users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return serialize(user)
    cursor = users.find()
    return [serialize(u) async for u in cursor]

@router.post("/users", dependencies=[Depends(verify_api_key)], tags=["User"])
async def create_user(user: UserIn):
    existing = await users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail=f"Username bereits vergeben {existing}")

    hashed_pw = bcrypt.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_pw
    user_dict["last_login"] = None
    result = await users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    user_dict.pop("password")
    return serialize(user_dict)

@router.put("/users/{user_id}", dependencies=[Depends(verify_api_key)], tags=["User"])
async def update_user(user_id: str, update: UserUpdate):
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if "password" in update_data:
        update_data["password"] = bcrypt.hash(update_data["password"])

    await users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    return {"ok": True}


class LoginCredentials(BaseModel):
    username: str
    password: str


@router.post("/login", tags=["User"])
async def login(credentials: LoginCredentials):
    user = await users.find_one({"username": credentials.username})
    hash_password = bcrypt.hash(credentials.password)
    if not user or not bcrypt.verify(credentials.password, user.get("password", "")):
        print(f"{credentials.password} / {hash_password}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    return serialize(user)