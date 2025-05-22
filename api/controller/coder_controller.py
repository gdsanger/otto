# coder.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from fastapi import FastAPI, Depends, Header, Request, HTTPException, status, Body, Query, APIRouter
from model.filecontentresponse import FileContentResponse
from bson import ObjectId
from helper import verify_api_key
from typing import List, Optional
import tempfile
import logging
from config import BASE_DIR
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from otto_guard import rotate_backups, validate_before_save

router = APIRouter()

@router.get("/api/files/tree", dependencies=[Depends(verify_api_key)], tags=["Coder"])
def list_files(dir: str = "") -> List[str]:
    excluded = [".venv", "__pycache__"]
    target_dir = (BASE_DIR / dir).resolve()

    if not str(target_dir).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=400, detail="Ungültiges Verzeichnis")

    files = []
    for p in target_dir.rglob("*"):
        if p.is_file() and not any(part in excluded for part in p.parts):
            files.append(str(p.relative_to(BASE_DIR)))
    return files


@router.get("/api/files/content", dependencies=[Depends(verify_api_key)], tags=["Coder"])
def get_file_content(path: str):
    full_path = (BASE_DIR / path).resolve()
    if not full_path.is_file() or not str(full_path).startswith(str(BASE_DIR)):
        return {"path": path, "content": "Invalid file path or file not found."}
    return FileContentResponse(path=path, content=full_path.read_text(encoding="utf-8"))

@router.put("/api/files/content", dependencies=[Depends(verify_api_key)], tags=["Coder"])
def save_file_content(data: FileContentResponse):
    full_path = (BASE_DIR / data.path).resolve()

    if not str(full_path).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=400, detail="Ungültiger Pfad")
    if full_path.is_dir():
        raise HTTPException(status_code=400, detail="Pfad verweist auf ein Verzeichnis")

    # Validierung vor dem Speichern
    is_valid, msg = validate_before_save(data.path, data.content)
    if not is_valid:
        raise HTTPException(status_code=403, detail=f"Speichern abgebrochen: {msg}")

    # Sicherung anlegen (rotierend)
    if full_path.exists():
        rotate_backups(full_path)

    full_path.write_text(data.content, encoding="utf-8")
    return {"status": "gespeichert", "backup": f"{full_path.name}.sic.0"}

@router.post("/api/backup/source", dependencies=[Depends(verify_api_key)], tags=["Coder"])
def create_code_backup(dir: str = ""):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BASE_DIR / "backup"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"source_backup_{timestamp}.tar.gz"

    source_dir = (BASE_DIR / dir).resolve()
    if not str(source_dir).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=400, detail="Ungültiges Verzeichnis")

    def exclude_filter(tarinfo):
        parts = Path(tarinfo.name).parts
        if any(x in parts for x in [".venv", "__pycache__", "backup"]):
            return None
        return tarinfo

    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(source_dir, arcname=".", filter=exclude_filter)

    return {"status": "ok", "file": str(backup_path.relative_to(BASE_DIR))}