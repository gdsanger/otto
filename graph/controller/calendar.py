from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import date, datetime
from pydantic import BaseModel
from graph import verify_api_key, get_graph_token
from config import API_KEY, TENANT_ID, CLIENT_ID, CLIENT_SECRET, GRAPH_URL, MAIL_FROM
import httpx

router = APIRouter(prefix="/kalender", tags=["Kalender"])

@router.get("/heute", dependencies=[Depends(verify_api_key)])
async def get_heutige_termine():
    heute = date.today()
    try:
        events = await get_day_events(datetime.combine(heute, datetime.min.time()))
        return {"datum": heute.isoformat(), "termine": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TerminEintrag(BaseModel):
    titel: str
    von: datetime
    bis: datetime

@router.post("/termin", dependencies=[Depends(verify_api_key)])
async def neuen_termin_erstellen(eintrag: TerminEintrag):
    try:
        result = await add_focus_block(start=eintrag.von, end=eintrag.bis, subject=eintrag.titel)
        return {"status": "ok", "event_id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_day_events(date: datetime) -> list:
    token = await get_graph_token()
    start = date.strftime("%Y-%m-%dT00:00:00")
    end = date.strftime("%Y-%m-%dT23:59:59")
    url = f"{GRAPH_URL}/users/{MAIL_FROM}/calendarView"
    params = {
        "startDateTime": start,
        "endDateTime": end,
        "$orderby": "start/dateTime"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    if response.status_code >= 300:
        raise Exception(f"Graph API Fehler: {response.status_code} – {response.text}")
    return response.json().get("value", [])


async def add_focus_block(start, end, subject="Fokuszeit"):
    token = await get_graph_token()
    url = f"{GRAPH_URL}/users/{MAIL_FROM}/events"

    payload = {
        "subject": subject,
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Berlin"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Berlin"},
        "showAs": "busy",
        "body": {"contentType": "text", "content": "Automatisch eingetragen durch Otto"}
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 300:
        raise Exception(f"Fehler beim Erstellen des Events: {response.status_code} – {response.text}")

    return response.json()

