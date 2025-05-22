# helper.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from fastapi import Header, Depends, HTTPException
from config import API_KEY, TENANT_ID, CLIENT_ID, CLIENT_SECRET, GRAPH_URL
from fastapi.security.api_key import APIKeyHeader
from datetime import datetime
import pytz
import logging
import httpx

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    logging.basicConfig(level=logging.INFO)
    logging.info(f"API Key received: {api_key}")
    if api_key != API_KEY:
       raise HTTPException(401, "Invalid API Key", status_code=401)

async def get_graph_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]

def utc_to_local(utc_string: str, target_tz: str = "Europe/Berlin") -> datetime:
    utc = pytz.UTC
    local_tz = pytz.timezone(target_tz)
    dt = datetime.fromisoformat(utc_string)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=utc)
    return dt.astimezone(local_tz)