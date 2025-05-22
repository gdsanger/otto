from fastapi import APIRouter, Depends, HTTPException, Request, Query
from datetime import datetime, timedelta, time, date
from pydantic import BaseModel
from typing import Optional
from graph import verify_api_key, get_graph_token, utc_to_local
from config import API_KEY, TENANT_ID, CLIENT_ID, CLIENT_SECRET, GRAPH_URL, MAIL_FROM
import httpx
import pytz

router = APIRouter(prefix="/kalender", tags=["Kalender"])

@router.get("/datum", dependencies=[Depends(verify_api_key)])
async def get_termine_fuer_datum(datum: date = Query(...)):
    try:
        events = await get_day_events(datetime.combine(datum, datetime.min.time()))
        for event in events:
            event["start"]["dateTime"] = utc_to_local(event["start"]["dateTime"])
            event["end"]["dateTime"] = utc_to_local(event["end"]["dateTime"])
        return {"datum": datum.isoformat(), "termine": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TerminEintrag(BaseModel):
    titel: str
    datum: date
    von: Optional[str] = "08:00"
    bis: Optional[str] = "17:00"
    ganztag: bool = False

@router.post("/termin", dependencies=[Depends(verify_api_key)])
async def neuen_termin_erstellen(eintrag: TerminEintrag):
    try:
        if eintrag.ganztag:
            start = { "date": eintrag.datum.isoformat() }
            end = { "date": (eintrag.datum + timedelta(days=1)).isoformat() }
            is_all_day = True
        else:
            berlin = pytz.timezone("Europe/Berlin")
            start_dt = berlin.localize(datetime.combine(eintrag.datum, time.fromisoformat(eintrag.von)))
            end_dt = berlin.localize(datetime.combine(eintrag.datum, time.fromisoformat(eintrag.bis)))
            start = { "dateTime": start_dt.isoformat(), "timeZone": "Europe/Berlin" }
            end = { "dateTime": end_dt.isoformat(), "timeZone": "Europe/Berlin" }
            is_all_day = False

        # Hier dein Kalendereintrag auslösen:
        await create_calendar_event(
            title=eintrag.titel,
            start=start,
            end=end,
            all_day=is_all_day
        )

        return { "success": True }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_calendar_event(title, start, end, all_day):
    token = await get_graph_token()
    url = f"{GRAPH_URL}/users/{MAIL_FROM}/events"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",        
    }

    if all_day:
        payload = {
            "subject": title,
            "start": { 
                "dateTime": start['date']+"T00:00:00",
                "timeZone": "UTC"
             },
            "end": { 
                "dateTime": end['date']+"T00:00:00",
                "timeZone": "UTC"
                 },
            "isAllDay": True
        }
    else:
        payload = {
            "subject": title,
            "start": {
                "dateTime": start['dateTime'],
                "timeZone": start['timeZone']
            },
            "end": {
                "dateTime": end['dateTime'],
                "timeZone": end['timeZone']
            },
            "isAllDay": False
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


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

