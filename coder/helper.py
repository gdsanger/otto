# helper.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from fastapi import Header, Depends, HTTPException
from config import API_KEY
from fastapi.security.api_key import APIKeyHeader
import logging

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    logging.basicConfig(level=logging.INFO)
    logging.info(f"API Key received: {api_key}")
    if api_key != API_KEY:
       raise HTTPException(401, "Invalid API Key", status_code=401)

def serialize_mongo(doc):
    doc = dict(doc)  # falls nötig in normales Dict wandeln
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc