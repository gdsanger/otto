from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from helper import verify_api_key, serialize_mongo
from mongo import db
from model.message import Message

router = APIRouter()

@router.post("/messages", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def create_message(message: Message):
    result = await db.messages.insert_one(message.dict())
    return {"status": "ok", "id": str(result.inserted_id)}

@router.get("/messages", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def list_messages():
    cursor = db.messages.find()
    return [serialize_mongo(m) async for m in cursor]

@router.get("/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def get_message(message_id: str):
    msg = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return serialize_mongo(msg)

@router.delete("/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def delete_message(message_id: str):
    result = await db.messages.delete_one({"_id": ObjectId(message_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "deleted"}

@router.get("/project/{project_id}/messages", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def get_messages_by_project(project_id: str):
    cursor = db.messages.find({"project_id": project_id}).sort("datum", -1)
    return [serialize_mongo(m) async for m in cursor]
