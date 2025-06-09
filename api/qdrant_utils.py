import os
import openai
import qdrant_client
from qdrant_client.models import PointStruct, VectorParams, Distance, CollectionStatus
import requests
from controller.context_controller import aufgabe_context
import asyncio
from uuid import uuid4
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger(__name__)
qdrant = qdrant_client.QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "tasks"
MESSAGE_COLLECTION_NAME = "messages"

# Init Collection falls nicht vorhanden
existing = [c.name for c in qdrant.get_collections().collections]
if COLLECTION_NAME not in existing:
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )
if MESSAGE_COLLECTION_NAME not in existing:
    qdrant.recreate_collection(
        collection_name=MESSAGE_COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )


def embed(text: str) -> list[float]:
    """Vektorisiert Text mit OpenAI Embedding."""
    response = openai.embeddings.create(
        input=[text], model="text-embedding-3-large"  # <-- hier gewechselt
    )
    return response.data[0].embedding


import asyncio
from uuid import uuid4


async def upsert_task_to_qdrant(task_id: str):
    """Task-Kontext laden und in Qdrant upserten (async, lokal)."""
    task = await aufgabe_context(task_id)

    vector = await asyncio.to_thread(embed, task["context_text"])
    payload = {
        "mongo_id": str(task["id"]),  # Original Mongo-ID als Referenz
        "tid": task.get("tid"),
        "betreff": task.get("betreff"),
        "projekt": task.get("projekt", {}).get("short"),
        "projekt_name": task.get("projekt", {}).get("name"),
        "bearbeiter": task.get("person", {}).get("name"),
        "status": task.get("status"),
        "prio": task.get("prio"),
        "typ": task.get("typ"),
        "termin": task.get("termin"),
        "sprint": task.get("sprint", {}).get("name"),
        "text": task.get("context_text"),
    }

    await asyncio.to_thread(
        qdrant.upsert,
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=str(uuid4()), vector=vector, payload=payload  # Qdrant-konformer UUID
            )
        ],
    )


def qdrant_similar_tasks(query_text: str, exclude_id: str, limit: int = 5):
    """Sucht ähnliche Tasks in Qdrant basierend auf dem gegebenen Text."""
    query_vector = embed(query_text)
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit + 10,
        with_payload=True,
    )
    similar = []
    for hit in hits:
        logger.debug(f"Treffer Score: {hit.score:.3f}, ID: {hit.id}")
        #if hit.score < 0.7:
        #    continue
        payload = hit.payload
        if payload.get("mongo_id") != exclude_id:
            similar.append({"score": hit.score, "task": payload})
        if len(similar) >= limit:
            break
    return similar


async def upsert_message_to_qdrant(message_id: str):
    """Lädt eine Nachricht und upsertet sie in Qdrant."""
    from bson import ObjectId
    from mongo import db

    msg = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not msg:
        logger.warning(f"Message {message_id} nicht gefunden")
        return

    text = f"{msg.get('subject', '')}\n{msg.get('message', '')}"
    vector = await asyncio.to_thread(embed, text)
    payload = {
        "mongo_id": str(msg["_id"]),
        "betreff": msg.get("subject"),
        "absender": msg.get("sender"),
        "datum": msg.get("datum"),
        "text": msg.get("message"),
        "projekt": msg.get("project_id"),
        "direction": msg.get("direction"),
    }

    await asyncio.to_thread(
        qdrant.upsert,
        collection_name=MESSAGE_COLLECTION_NAME,
        points=[PointStruct(id=str(uuid4()), vector=vector, payload=payload)],
    )


def qdrant_similar_messages(query_text: str, exclude_id: str, limit: int = 5):
    """Sucht ähnliche Nachrichten in Qdrant."""
    query_vector = embed(query_text)
    hits = qdrant.search(
        collection_name=MESSAGE_COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit + 10,
        with_payload=True,
    )

    similar = []
    for hit in hits:
        if hit.score < 0.75:
            continue
        payload = hit.payload
        if payload.get("mongo_id") != exclude_id:
            similar.append({"score": hit.score, "message": payload})
        if len(similar) >= limit:
            break
    return similar
