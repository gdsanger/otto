from fastapi import APIRouter, Depends, HTTPException
from typing import List, Tuple, Dict
import asyncio
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
from qdrant_utils import upsert_message_to_qdrant, qdrant_similar_messages, qdrant_similar_tasks
import os
import httpx
from datetime import datetime
from config import API_KEY as INTERNAL_API_KEY, GRAPH_API_URL

import base64

router = APIRouter()

# Versucht, falsch dekodierte Strings wieder in korrektes UTF-8 zu wandeln
def fix_encoding(text: str) -> str:
    if "\ufffd" in text:
        try:
            return text.encode("latin1").decode("utf-8")
        except Exception:
            return text
    return text


@router.post("/messages", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def create_message(message: Message):
    result = await db.messages.insert_one(message.dict())
    message_id = str(result.inserted_id)
    asyncio.create_task(upsert_message_to_qdrant(message_id))
    return {"status": "ok", "id": message_id}


@router.get("/messages", dependencies=[Depends(verify_api_key)], tags=["Message"])
async def list_messages():
    cursor = db.messages.find()
    return [serialize_mongo(m) async for m in cursor]


@router.get(
    "/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"]
)
async def get_message(message_id: str):
    msg = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return serialize_mongo(msg)


@router.get(
    "/project/{project_id}/messages",
    dependencies=[Depends(verify_api_key)],
    tags=["Projekt"],
)
async def get_messages_by_project(project_id: str):
    cursor = db.messages.find({"project_id": project_id}).sort("datum", -1)
    return [serialize_mongo(m) async for m in cursor]


async def _fetch_and_store_attachments(
    client: httpx.AsyncClient, headers: dict, message_id: str
) -> Tuple[List[str], Dict[str, str]]:
    """Retrieve attachments of a message and store them on SharePoint.

    Returns a tuple containing the list of uploaded attachment URLs and a
    mapping of cid/contentId values to those URLs for inline images.
    """
    att_resp = await client.get(
        f"{GRAPH_API_URL}/mail/{message_id}/attachments", headers=headers
    )
    # Some messages may not have an attachments endpoint and return 404.
    # Treat this case as having no attachments instead of raising an error.
    try:
        att_resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        raise
    attachments = att_resp.json()
    urls: List[str] = []
    cid_map: Dict[str, str] = {}
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
                    cid = att.get("contentId")
                    if att.get("isInline") and cid:
                        cid_map[cid.strip("<>")] = url
    return urls, cid_map


@router.post(
    "/messages/fetch", dependencies=[Depends(verify_api_key)], tags=["Message"]
)
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
                "datum": (
                    datetime.fromisoformat(dt_str) if dt_str else datetime.utcnow()
                ),
                "subject": fix_encoding(m.get("subject", "")),
                "sender": m.get("from", {}).get("emailAddress", {}).get("address"),
                "to": [r["emailAddress"]["address"] for r in m.get("toRecipients", [])],
                "cc": [r["emailAddress"]["address"] for r in m.get("ccRecipients", [])]
                or None,
                "message": fix_encoding(m.get("body", {}).get("content", "")),
                "direction": "in",
                "status": "gesendet",
                "message_id": m.get("id"),
                "conversation_id": m.get("conversationId"),
            }

            result = await db.messages.insert_one(doc)
            message_id = str(result.inserted_id)
            inserted.append(message_id)

            # Fetch and store attachments
            att_urls, cid_map = await _fetch_and_store_attachments(
                client, headers, m.get("id")
            )
            update_fields = {}
            if att_urls:
                update_fields["attachments"] = att_urls
            if cid_map:
                html = doc["message"]
                for cid, url in cid_map.items():
                    html = html.replace(f"cid:{cid}", url)
                    html = html.replace(f"cid:%3C{cid}%3E", url)
                update_fields["message"] = html
            if update_fields:
                await db.messages.update_one(
                    {"_id": result.inserted_id}, {"$set": update_fields}
                )

            await client.post(
                f"{GRAPH_API_URL}/mail/{m.get('id')}/archive", headers=headers
            )

            asyncio.create_task(upsert_message_to_qdrant(message_id))

    return {"inserted": inserted}


@router.put(
    "/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"]
)
async def update_message(message_id: str, message: Message):
    try:
        oid = ObjectId(message_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await db.messages.replace_one({"_id": oid}, message.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    asyncio.create_task(upsert_message_to_qdrant(message_id))
    return {"status": "aktualisiert"}


@router.delete(
    "/messages/{message_id}", dependencies=[Depends(verify_api_key)], tags=["Message"]
)
async def delete_message(message_id: str):
    """Delete a message by its MongoDB identifier."""
    try:
        oid = ObjectId(message_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    result = await db.messages.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "deleted"}


@router.get(
    "/messages/{message_id}/similar",
    dependencies=[Depends(verify_api_key)],
    tags=["Message"],
)
async def get_similar_messages(message_id: str, limit: int = 5):
    msg = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    text = f"{msg.get('subject', '')}"
    similar = qdrant_similar_messages(text, message_id, limit)
    return similar


@router.get(
    "/messages/{message_id}/similar_tasks",
    dependencies=[Depends(verify_api_key)],
    tags=["Message"],
)
async def get_similar_tasks_for_message(message_id: str, limit: int = 5):
    """Gibt Aufgaben zurück, die semantisch zu dieser Nachricht passen."""
    msg = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    text = f"{msg.get('subject', '')}"
    similar = qdrant_similar_tasks(text, None, limit)
    return similar


@router.post(
    "/messages/qdrant/reindex", dependencies=[Depends(verify_api_key)], tags=["Qdrant"]
)
async def reindex_all_messages():
    message_ids = await db.messages.distinct("_id")
    count = 0
    for mid in message_ids:
        await upsert_message_to_qdrant(str(mid))
        count += 1
    return {"status": "ok", "indexed_messages": count}
