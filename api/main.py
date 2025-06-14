# main.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query
from config import API_KEY
from fastapi.security.api_key import APIKeyHeader
import os
import sys
import numpy as np

# ----------------------------------------------------------------------------
# Compatibility helpers
# ----------------------------------------------------------------------------
# Some third-party libraries still reference ``np.float_`` which was removed in
# NumPy 2.0. Provide an alias so imports don't fail.
if not hasattr(np, "float_"):
    np.float_ = np.float64
# Ensure project root is on the Python path when running the server from
# within the ``api`` directory so that modules like ``graph`` are available.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from typing import List, Optional
from mongo import projekte_collection, personen_collection
from bson import ObjectId
from fastapi.openapi.utils import get_openapi
from config import GRAPH_URL, SITE_ID, DRIVE_ID, FOLDER
from email import policy
from email.parser import BytesParser
from helper import verify_api_key
import tempfile
from docx import Document
import logging
import httpx
from bson.errors import InvalidId
from openapi_gpt import router as openapi_gpt_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Oder gezielt: ["https://data.isarlabs.de"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dynamisch Router einbinden mit Fehlerbehandlung
try:
    from controller.project_controller import router as project_router
    app.include_router(project_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von project_controller: {e}")

try:
    from controller.personen_controller import router as personen_router
    app.include_router(personen_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von personen_controller: {e}")

try:
    from controller.task_controller import router as task_router
    app.include_router(task_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von task_controller: {e}")

try:
    from controller.context_controller import router as context_router
    app.include_router(context_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von context_controller: {e}")

try:
    from controller.user_controller import router as user_router
    app.include_router(user_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von user_controller: {e}")

try:
    from controller.sharepoint_controller import router as sharepoint_router
    app.include_router(sharepoint_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von sharepoint_router: {e}")

try:
    from controller.message_controller import router as message_router
    app.include_router(message_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von message_controller: {e}")

try:
    from controller.comment_controller import router as comment_router
    app.include_router(comment_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von comment_controller: {e}")

try:
    from controller.sprint_controller import router as sprint_router
    app.include_router(sprint_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von sprint_controller: {e}")

try:
    from controller.ai_controller import router as ai_router
    app.include_router(ai_router)
except Exception as e:
    print(f"⚠️ Fehler beim Einbinden von ai_controller: {e}")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="OttoCore API",
        version="1.0.1",
        description="Die zentrale API für KI-Assistent Otto",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {
            "url": "https://data.isarlabs.de",
            "description": "Produktivserver"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def serialize_mongo(doc):
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc