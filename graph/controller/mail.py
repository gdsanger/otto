# graph_mailer.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

import httpx
from fastapi import APIRouter
from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, MAIL_FROM, MAIL_TO, SITE_ID, DRIVE_ID, FOLDER, GRAPH_URL
from typing import Optional
from datetime import date, datetime
from graph import verify_api_key, get_graph_token

router = APIRouter(prefix="/mail", tags=["Mail"])

async def send_mail_via_graph(subject: str, body: str, to: str, cc: Optional[str] = None):
    token = await get_graph_token()
    url = f"https://graph.microsoft.com/v1.0/users/{MAIL_FROM}/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Empfänger verarbeiten
    recipients = [
        {"emailAddress": {"address": addr.strip()}}
        for addr in to.split(",") if addr.strip()
    ]

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