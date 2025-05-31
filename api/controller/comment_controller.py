from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from bson import ObjectId

from model.comment import Comment
from mongo import db, comments_collection, personen_collection, messages_collection
from helper import verify_api_key, serialize_mongo
from model.message import Message

router = APIRouter()

@router.get("/tasks/{task_id}/comments", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def list_comments(task_id: str) -> List[Comment]:
    cursor = comments_collection.find({"task_id": task_id}).sort("datum", 1)
    return [serialize_mongo(c) async for c in cursor]

@router.post("/tasks/{task_id}/comments", dependencies=[Depends(verify_api_key)], tags=["Task"])
async def create_comment(task_id: str, comment: Comment, send_email: bool = False):
    comment_dict = comment.dict()
    comment_dict["task_id"] = task_id
    if comment_dict.get("datum") is None:
        comment_dict["datum"] = datetime.utcnow()

    # Optionally send an email to the requester and store as message
    message_id = None
    if send_email:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        requester_id = task.get("requester_id")
        if not requester_id:
            raise HTTPException(status_code=400, detail="Task has no requester")
        requester = await personen_collection.find_one({"_id": ObjectId(requester_id)})
        if not requester:
            raise HTTPException(status_code=404, detail="Requester not found")
        mail = Message(
            datum=datetime.utcnow(),
            subject=task.get("betreff", "Task"),
            sender=None,
            to=[requester.get("email")],
            cc=None,
            message=comment_dict.get("text"),
            direction="out",
            status="gesendet",
            project_id=task.get("project_id"),
            task_id=task_id,
        )
        msg_result = await messages_collection.insert_one(mail.dict())
        message_id = str(msg_result.inserted_id)
        comment_dict["type"] = "email_out"
        comment_dict["message_id"] = message_id

    result = await comments_collection.insert_one(comment_dict)
    return {"status": "ok", "id": str(result.inserted_id), "message_id": message_id}
