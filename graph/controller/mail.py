# graph_mailer.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

import httpx
from fastapi import APIRouter, Depends
from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, MAIL_FROM, MAIL_TO, SITE_ID, DRIVE_ID, FOLDER, GRAPH_URL, MAIL_INBOX
from typing import Optional
from datetime import date, datetime
from graph import verify_api_key, get_graph_token

router = APIRouter(tags=["Mail"])

@router.post("/mail", dependencies=[Depends(verify_api_key)])
async def send_mail_via_graph(subject: str, body: str, to: str, cc: Optional[str] = None):
    try:
        # Token besorgen
        token = await get_graph_token()
        if not token:
            return {"success": False, "error": "Konnte kein Authentifizierungstoken erhalten"}

        url = f"https://graph.microsoft.com/v1.0/users/{MAIL_FROM}/sendMail"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Empfänger verarbeiten und validieren
        if not to or not to.strip():
            return {"success": False, "error": "Keine Empfänger angegeben"}
        
        recipients = [
            {"emailAddress": {"address": addr.strip()}}
            for addr in to.split(",") if addr.strip()
        ]
        
        if not recipients:
            return {"success": False, "error": "Keine gültigen Empfänger gefunden"}
        
        # CC-Empfänger verarbeiten, falls vorhanden
        cc_recipients = None
        if cc:
            cc_recipients = [
                {"emailAddress": {"address": addr.strip()}}
                for addr in cc.split(",") if addr.strip()
            ]

        # E-Mail-Daten vorbereiten
        mail_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": recipients
            },
            "saveToSentItems": "true"
        }
        
        # CC-Empfänger hinzufügen, falls vorhanden
        if cc_recipients:
            mail_data["message"]["ccRecipients"] = cc_recipients

        # E-Mail senden mit Timeout und Fehlerbehandlung
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=mail_data)
                response.raise_for_status()  # Fehler werfen, wenn Status-Code >= 400
                
                # Erfolgreiche Antwort
                return {
                    "success": True,
                    "message": "E-Mail erfolgreich gesendet",
                    "status_code": response.status_code
                }
                
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "error": "Zeitüberschreitung bei der Anfrage an Microsoft Graph API"
                }
            except httpx.HTTPStatusError as e:
                # Detaillierte Fehlerinformationen aus der API-Antwort extrahieren
                error_info = "Unbekannter Fehler"
                try:
                    error_detail = e.response.json()
                    if "error" in error_detail:
                        error_info = f"{error_detail['error'].get('code', '')}: {error_detail['error'].get('message', '')}"
                except:
                    error_info = f"HTTP-Fehler {e.response.status_code}"
                
                return {
                    "success": False,
                    "error": f"Microsoft Graph API-Fehler: {error_info}",
                    "status_code": e.response.status_code
                }
            except httpx.RequestError as e:
                return {
                    "success": False, 
                    "error": f"Verbindungsproblem: {str(e)}"
                }
    
    except Exception as e:
        # Allgemeine Fehlerbehandlung für unerwartete Fehler
        import traceback
        error_trace = traceback.format_exc()
        print(f"Fehler beim E-Mail-Versand: {str(e)}\n{error_trace}")
        return {
            "success": False,
            "error": f"Unerwarteter Fehler beim E-Mail-Versand: {str(e)}"
        }


@router.get("/mail/inbox", dependencies=[Depends(verify_api_key)])
async def fetch_inbox_messages():
    """Retrieve all messages from the configured inbox."""
    token = await get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_URL}/users/{MAIL_INBOX}/mailFolders/inbox/messages"
    params = {
        "$top": 50,
        "$select": "id,conversationId,subject,body,toRecipients,ccRecipients,from,receivedDateTime"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        base_messages = resp.json().get("value", [])

        detailed = []
        for m in base_messages:
            mid = m.get("id")
            detail = await client.get(
                f"{GRAPH_URL}/users/{MAIL_INBOX}/messages/{mid}",
                headers=headers
            )
            detail.raise_for_status()
            detailed.append(detail.json())

    return detailed


@router.post("/mail/{message_id}/archive", dependencies=[Depends(verify_api_key)])
async def archive_message(message_id: str):
    """Move the specified message to the Archive folder."""
    token = await get_graph_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{GRAPH_URL}/users/{MAIL_INBOX}/messages/{message_id}/move"
    payload = {"destinationId": "Archive"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()

    return {"status": "archived"}


@router.get("/mail/{message_id}/attachments", dependencies=[Depends(verify_api_key)])
async def get_message_attachments(message_id: str):
    """Return all attachments for the given message."""
    token = await get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_URL}/users/{MAIL_INBOX}/messages/{message_id}/attachments"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()

    return data.get("value", [])
