from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query
from config import API_KEY
from fastapi.security.api_key import APIKeyHeader
from typing import List, Optional
from fastapi.openapi.utils import get_openapi
from config import GRAPH_URL, SITE_ID, DRIVE_ID, FOLDER
from email import policy
from email.parser import BytesParser
import tempfile
import os
from docx import Document
import logging
import httpx

from controller.calendar import router as calendar_router
from controller.mail import router as mail_router
from controller.sharepoint import router as sharepoint_router

app = FastAPI()

try:
    from controller.calendar import router as calendar_router
    app.include_router(calendar_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von calendar_router: {e}")

try:
    from controller.mail import router as mail_router
    app.include_router(calendar_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von mail_router: {e}")

try:
    from controller.sharepoint import router as sharepoint_router
    app.include_router(sharepoint_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von sharepoint_router: {e}")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="OttoCore API",
        version="1.0.1",
        description="Die Grapg API Kapselung für KI-Assistent Otto",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {
            "url": "https://graph.isarlabs.de",
            "description": "Produktivserver"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi