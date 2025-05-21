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