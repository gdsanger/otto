# main.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query
from config import API_KEY
from fastapi.security.api_key import APIKeyHeader
import os
import sys
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

@app.get("/")
async def root():
    return {"message": "KI-Drehkreuz läuft"}


def serialize_mongo(doc):
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc