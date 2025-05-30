from fastapi import APIRouter, Depends, HTTPException
from model.meeting import Meeting
from typing import List
from datetime import date, datetime
from helper import verify_api_key
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["otto"]
meetings_collection = db["meetings"]
tasks_collection = db["tasks"]

@router.post("/meetings", dependencies=[Depends(verify_api_key)], tags=["Meeting"])
async def create_meeting(meeting: Meeting):
    meeting_dict = meeting.dict()
    if isinstance(meeting_dict["datum"], date):
        meeting_dict["datum"] = datetime.combine(meeting_dict["datum"], datetime.min.time())
    await meetings_collection.insert_one(meeting_dict)
    return {"message": "Meeting erstellt", "meeting": meeting}

@router.get("/meetings", dependencies=[Depends(verify_api_key)], tags=["Meeting"])
async def list_meetings():
    cursor = meetings_collection.find({}, {"_id": 0})
    return [doc async for doc in cursor]

@router.get("/meetings/{meeting_id}", dependencies=[Depends(verify_api_key)], tags=["Meeting"])
async def get_meeting(meeting_id: str):
    meeting = await meetings_collection.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting nicht gefunden")

    tasks_cursor = tasks_collection.find({"meeting_id": meeting_id}, {"_id": 0})
    meeting["tasks"] = [task async for task in tasks_cursor]
    return meeting

@router.put("/meetings/{meeting_id}", dependencies=[Depends(verify_api_key)], tags=["Meeting"])
async def update_meeting(meeting_id: str, updated: Meeting):
    update_dict = updated.dict()
    if isinstance(update_dict["datum"], date):
        update_dict["datum"] = datetime.combine(update_dict["datum"], datetime.min.time())
    result = await meetings_collection.replace_one({"id": meeting_id}, update_dict)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Meeting nicht gefunden")
    return {"message": "Meeting aktualisiert"}

@router.delete("/meetings/{meeting_id}", dependencies=[Depends(verify_api_key)], tags=["Meeting"])
async def delete_meeting(meeting_id: str):
    result = await meetings_collection.delete_one({"id": meeting_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meeting nicht gefunden")
    return {"message": "Meeting gelöscht"}