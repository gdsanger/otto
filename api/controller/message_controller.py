from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from helper import (
    verify_api_key,
    serialize_mongo,
    ensure_message_folder,
    upload_message_attachment,
)
from bson.errors import InvalidId
from mongo import db
from model.message import Message
import os
import httpx
from datetime import datetime
from config import API_KEY as INTERNAL_API_KEY, GRAPH_API_URL

import base64

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


async def _fetch_and_store_attachments(client: httpx.AsyncClient, headers: dict, message_id: str) -> List[str]:
    """Retrieve attachments of a message and store them on SharePoint."""
    att_resp = await client.get(f"{GRAPH_API_URL}/mail/{message_id}/attachments", headers=headers)
    att_resp.raise_for_status()
    attachments = att_resp.json()
    urls: List[str] = []
    if attachments:
        await ensure_message_folder(message_id)
        for att in attachments:
            name = att.get("name")
            if not name:
                continue
            content = None
            if att.get("contentBytes"):
                content = base64.b64decode(att["contentBytes"])
            elif att.get("@microsoft.graph.downloadUrl"):
                resp = await client.get(att["@microsoft.graph.downloadUrl"])
                resp.raise_for_status()
                content = resp.content
            if content is not None:
                url = await upload_message_attachment(message_id, name, content)
                if url:
                    urls.append(url)
    return urls


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

            dt_str = m.get("receivedDateTime")
            if dt_str:
                dt_str = dt_str.replace("Z", "+00:00")
            doc = {
                "datum": datetime.fromisoformat(dt_str) if dt_str else datetime.utcnow(),
                "subject": m.get("subject", ""),
                "sender": m.get("from", {}).get("emailAddress", {}).get("address"),
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

            # Fetch and store attachments
            att_urls = await _fetch_and_store_attachments(client, headers, m.get("id"))
            if att_urls:
                await db.messages.update_one({"_id": result.inserted_id}, {"$set": {"attachments": att_urls}})

            await client.post(f"{GRAPH_API_URL}/mail/{m.get('id')}/archive", headers=headers)

    return {"inserted": inserted}


@router.put("/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def update_message(message_id: str, message: Message):
    try:
        oid = ObjectId(message_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await db.messages.replace_one({"_id": oid}, message.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "aktualisiert"}

