# helper.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from fastapi import Header, Depends, HTTPException
from config import API_KEY
from fastapi.security.api_key import APIKeyHeader
import logging
from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, FOLDER, GRAPH_URL, SITE_ID, DRIVE_ID, MESSAGES_FOLDER
import httpx


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

async def ensure_folder_exists(shortname: str):
    print(f"ensure_folder_exists: {shortname}")
    token = await get_graph_token()
    path = f"{FOLDER.rstrip('/')}/{shortname}"
    check_url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        check = await client.get(check_url, headers=headers)

        if check.status_code == 200:
            print(f"✔️ Ordner '{shortname}' existiert bereits.")
            return
        elif check.status_code == 404:
            print(f"➕ Ordner '{shortname}' wird erstellt …")
            create_url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}"
            response = await client.put(
                create_url,
                headers={**headers, "Content-Type": "application/json"},
                json={"folder": {}, "@microsoft.graph.conflictBehavior": "fail"}
            )
            if response.status_code in (200, 201):
                print(f"✅ Ordner '{shortname}' erfolgreich erstellt.")
            else:
                print(f"❌ Fehler bei Ordner '{shortname}': {response.status_code} – {response.text}")
        else:
            print(f"⚠️ Fehler beim Prüfen von '{shortname}': {check.status_code} – {check.text}")


async def ensure_message_folder(message_id: str):
    """Ensure that the SharePoint folder for the given message exists."""
    token = await get_graph_token()
    path = f"{MESSAGES_FOLDER.rstrip('/')}/{message_id}"
    url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        check = await client.get(url, headers=headers)
        if check.status_code == 404:
            await client.put(
                url,
                headers={**headers, "Content-Type": "application/json"},
                json={"folder": {}, "@microsoft.graph.conflictBehavior": "fail"},
            )


async def upload_message_attachment(message_id: str, filename: str, content: bytes) -> str:
    """Upload an attachment file to the SharePoint message folder and return the file URL."""
    token = await get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    path = f"{MESSAGES_FOLDER.rstrip('/')}/{message_id}/{filename}"
    url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}:/content"
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, headers=headers, content=content)
        resp.raise_for_status()
        data = resp.json()
    return data.get("webUrl")
