from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
from model.sprint import Sprint, SprintListe
from mongo import sprints_collection, projekte_collection
from helper import verify_api_key, serialize_mongo

router = APIRouter()

@router.get("/sprints", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def list_sprints():
    cursor = sprints_collection.find()
    return [serialize_mongo(s) async for s in cursor]

@router.get("/sprints/{sprint_id}", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def get_sprint(sprint_id: str):
    try:
        oid = ObjectId(sprint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige ID")

    sprint = await sprints_collection.find_one({"_id": oid})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint nicht gefunden")
    return serialize_mongo(sprint)

@router.post("/sprints", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def create_sprint(sprint: Sprint):
    if not await projekte_collection.find_one({"_id": ObjectId(sprint.projekt_id)}):
        raise HTTPException(status_code=400, detail="Projekt nicht gefunden")
    result = await sprints_collection.insert_one(sprint.dict())
    return {"status": "ok", "id": str(result.inserted_id)}

@router.put("/sprints/{sprint_id}", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def update_sprint(sprint_id: str, sprint: Sprint):
    try:
        oid = ObjectId(sprint_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")
    if not await projekte_collection.find_one({"_id": ObjectId(sprint.projekt_id)}):
        raise HTTPException(status_code=400, detail="Projekt nicht gefunden")
    result = await sprints_collection.replace_one({"_id": oid}, sprint.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sprint nicht gefunden")
    return {"status": "aktualisiert"}

@router.delete("/sprints/{sprint_id}", dependencies=[Depends(verify_api_key)], tags=["Sprint"])
async def delete_sprint(sprint_id: str):
    try:
        oid = ObjectId(sprint_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Ungültige ID")
    result = await sprints_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sprint nicht gefunden")
    return {"status": "gelöscht"}

@router.get("/projekt/{projekt_id}/sprints", dependencies=[Depends(verify_api_key)], tags=["Projekt"])
async def get_sprints_by_project(projekt_id: str):
    cursor = sprints_collection.find({"projekt_id": projekt_id})
    return [serialize_mongo(s) async for s in cursor]
