from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from helper import verify_api_key, serialize_mongo
from mongo import db
from model.message import Message
import os
import httpx
from datetime import datetime
from config import API_KEY as INTERNAL_API_KEY, GRAPH_API_URL

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

@router.get("/project/{project_id}/messages", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def get_messages_by_project(project_id: str):
    cursor = db.messages.find({"project_id": project_id}).sort("datum", -1)
    return [serialize_mongo(m) async for m in cursor]


@router.post("/messages/fetch", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def fetch_inbox():
    """Fetch messages from the external inbox and store them."""
    headers = {"x-api-key": INTERNAL_API_KEY}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{GRAPH_API_URL}/mail/inbox", headers=headers)
        resp.raise_for_status()
        msgs = resp.json()

        inserted = []
        for m in msgs:
            if await db.messages.find_one({"message_id": m.get("id")}):
                continue

            doc = {
                "datum": datetime.fromisoformat(m.get("receivedDateTime")),
                "subject": m.get("subject", ""),
                "to": [r["emailAddress"]["address"] for r in m.get("toRecipients", [])],
                "cc": [r["emailAddress"]["address"] for r in m.get("ccRecipients", [])] or None,
                "message": m.get("body", {}).get("content", ""),
                "direction": "in",
                "status": "gesendet",
                "message_id": m.get("id"),
                "conversation_id": m.get("conversationId"),
            }

            result = await db.messages.insert_one(doc)
            inserted.append(str(result.inserted_id))

            await client.post(f"{GRAPH_API_URL}/mail/{m.get('id')}/archive", headers=headers)

    return {"inserted": inserted}

