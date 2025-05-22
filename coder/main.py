from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query
from config import API_KEY, BASE_DIR
from fastapi.security.api_key import APIKeyHeader
from typing import List, Optional
from fastapi.openapi.utils import get_openapi

app = FastAPI()

import socket
print("🔍 Hostname:", socket.gethostname())
print("🔍 BASE_DIR:", BASE_DIR)

import logging
logging.basicConfig(level=logging.DEBUG)

try:
    from controller.coder_controller import router as coder_router
    app.include_router(coder_router)
except Exception:
    print("⚠️ Fehler beim Einbinden von coder_controller:")
    

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Otto Coder API",
        version="1.0.1",
        description="Die API für Coding KI-Assistent Otto",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {
            "url": "https://coder.isarlabs.de",
            "description": "Produktivserver"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi